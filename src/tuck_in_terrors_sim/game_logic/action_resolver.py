# src/tuck_in_terrors_sim/game_logic/action_resolver.py
# Handles resolving player actions like playing cards, activating abilities

from typing import Dict, Optional, Any, List 

from .game_state import GameState, CardInPlay
from ..game_elements.card import Card, EffectLogic 
from ..game_elements.enums import CardType, Zone, EffectTriggerType, EffectActivationCostType, ResourceType
from .effect_engine import EffectEngine # Import the EffectEngine

class ActionResolver:
    def __init__(self, game_state: 'GameState', effect_engine: 'EffectEngine'):
        self.game_state = game_state
        self.effect_engine = effect_engine # Store and use the EffectEngine

    def play_card_from_hand(self, card_to_play: Card, is_free_toy_play: bool = False, targets: Optional[List[Any]] = None) -> bool:
        gs = self.game_state

        if card_to_play not in gs.hand:
            gs.add_log_entry(f"Action Error: Card '{card_to_play.name}' (ID: {card_to_play.card_id}) not in hand.", level="ERROR")
            return False

        if is_free_toy_play:
            if gs.free_toy_played_this_turn:
                gs.add_log_entry(f"Action Error: Free Toy already played this turn. Cannot play '{card_to_play.name}' as free.", level="ERROR")
                return False
            if card_to_play.card_type != CardType.TOY:
                gs.add_log_entry(f"Action Error: Cannot play '{card_to_play.name}' ({card_to_play.card_type.name}) as free Toy. Only Toys allowed.", level="ERROR")
                return False
            gs.add_log_entry(f"Attempting to play '{card_to_play.name}' as Free Toy.")
        else: 
            if gs.mana_pool < card_to_play.cost:
                gs.add_log_entry(f"Action Error: Not enough mana to play '{card_to_play.name}'. Has {gs.mana_pool}, needs {card_to_play.cost}.", level="ERROR")
                return False
            gs.add_log_entry(f"Attempting to play '{card_to_play.name}' for {card_to_play.cost} mana.")
            # Pay cost BEFORE attempting to move card and trigger effects
            gs.mana_pool -= card_to_play.cost 
            gs.add_log_entry(f"Spent {card_to_play.cost} mana for '{card_to_play.name}'. Mana remaining: {gs.mana_pool}.")

        # Move Card from Hand
        gs.hand.remove(card_to_play)
        card_instance_just_played: Optional[CardInPlay] = None # To hold the CardInPlay instance if created

        if card_to_play.card_type == CardType.TOY or card_to_play.card_type == CardType.RITUAL:
            card_instance = CardInPlay(base_card=card_to_play)
            gs.cards_in_play[card_instance.instance_id] = card_instance
            card_instance_just_played = card_instance 
            gs.add_log_entry(f"Played {card_to_play.card_type.name} '{card_to_play.name}' (Instance: {card_instance.instance_id}) to play area.")
            
            # Trigger ON_PLAY effects for this card instance
            self.effect_engine.trigger_effects(
                trigger_type=EffectTriggerType.ON_PLAY,
                source_card_instance_for_trigger=card_instance,
                event_context={'played_card_instance': card_instance, 'targets': targets}
            )
            # Also trigger WHEN_OTHER_CARD_ENTERS_PLAY for other cards that might be listening
            self.effect_engine.trigger_effects(
                trigger_type=EffectTriggerType.WHEN_OTHER_CARD_ENTERS_PLAY,
                event_context={'entered_card_instance': card_instance} 
            )

        elif card_to_play.card_type == CardType.SPELL:
            gs.add_log_entry(f"Played Spell '{card_to_play.name}'. Resolving ON_PLAY effects...")
            # Trigger ON_PLAY effects for this spell
            # For spells, the source_card_definition is the Card object from hand
            self.effect_engine.trigger_effects(
                trigger_type=EffectTriggerType.ON_PLAY,
                source_card_definition_for_trigger=card_to_play,
                event_context={'played_card_definition': card_to_play, 'targets': targets}
            )
            # After ON_PLAY effects are resolved (which might modify game state), move spell to discard
            gs.discard_pile.append(card_to_play)
            gs.add_log_entry(f"Spell '{card_to_play.name}' moved to discard pile after resolution.")

        # Update Game State Flags
        if is_free_toy_play:
            gs.free_toy_played_this_turn = True
            gs.add_log_entry("Free Toy play for the turn has been used.")
            
        if card_to_play.card_type == CardType.SPELL: # Storm typically counts spells
            gs.storm_count_this_turn +=1 
            gs.add_log_entry(f"Spell played. Storm count this turn now: {gs.storm_count_this_turn}.")

        return True

    def activate_ability(self, card_in_play_instance_id: str, effect_logic_index: int, targets: Optional[List[Any]] = None) -> bool:
        gs = self.game_state
        card_instance = gs.get_card_in_play_by_instance_id(card_in_play_instance_id)

        if not card_instance:
            gs.add_log_entry(f"Action Error: Card instance '{card_in_play_instance_id}' not found in play.", level="ERROR")
            return False

        if not (0 <= effect_logic_index < len(card_instance.card_definition.effect_logic_list)):
            gs.add_log_entry(f"Action Error: Invalid effect_logic_index {effect_logic_index} for card '{card_instance.card_definition.name}'.", level="ERROR")
            return False

        ability_logic = card_instance.card_definition.effect_logic_list[effect_logic_index]
        
        # Convert trigger string from EffectLogic to EffectTriggerType enum member
        trigger_as_enum = None
        try:
            trigger_as_enum = EffectTriggerType[ability_logic.trigger] # Assumes trigger string matches enum member name
        except KeyError:
             gs.add_log_entry(f"Action Error: Unknown trigger type string '{ability_logic.trigger}' for ability on '{card_instance.card_definition.name}'.", level="ERROR")
             return False


        if trigger_as_enum not in [EffectTriggerType.ACTIVATED_ABILITY, EffectTriggerType.TAP_ABILITY]:
            gs.add_log_entry(f"Action Error: Effect '{ability_logic.description or effect_logic_index}' on '{card_instance.card_definition.name}' is not an activatable type (Trigger: {ability_logic.trigger}).", level="ERROR")
            return False

        # Check once-per-turn
        effect_signature = f"effect_{effect_logic_index}" # Unique signature for this ability on this card instance
        if ability_logic.is_once_per_turn and card_instance.effects_active_this_turn.get(effect_signature):
            gs.add_log_entry(f"Action Error: Ability '{ability_logic.description or effect_logic_index}' on '{card_instance.card_definition.name}' already used this turn.", level="ERROR")
            return False

        # Check tap requirement for TAP_ABILITY
        if trigger_as_enum == EffectTriggerType.TAP_ABILITY and card_instance.is_tapped:
            gs.add_log_entry(f"Action Error: Cannot activate tap ability of '{card_instance.card_definition.name}' because it is already tapped.", level="ERROR")
            return False

        # Placeholder: Check and Pay Activation Costs
        can_pay_all_costs = True 
        if ability_logic.activation_costs:
            gs.add_log_entry(f"Placeholder: Checking and paying activation costs for ability '{ability_logic.description}' on '{card_instance.card_definition.name}'...")
            # TODO: Implement cost checking and payment logic here (Phase 4)
            # This involves iterating ability_logic.activation_costs
            # For each cost_data in ability_logic.activation_costs:
            #   cost_type_str = cost_data.get("cost_type")
            #   cost_type = EffectActivationCostType[cost_type_str]
            #   cost_params = cost_data.get("params")
            #   if not self._can_pay_specific_cost(gs, card_instance, cost_type, cost_params): # New helper
            #       can_pay_all_costs = False; break
            # If all can_pay_all_costs:
            #   For each cost_data:
            #       self._pay_specific_cost(gs, card_instance, cost_type, cost_params) # New helper
            pass # Actual cost payment logic will be complex and added in EffectEngine or here.

        if not can_pay_all_costs:
            # Error message would ideally be logged by the cost payment logic
            gs.add_log_entry(f"Action Error: Cannot pay activation costs for ability on '{card_instance.card_definition.name}'.", level="ERROR") # Generic if specific fails
            return False
        
        gs.add_log_entry(f"Activating ability '{ability_logic.description or effect_logic_index}' of '{card_instance.card_definition.name}'.")

        # Tap the card if it's a TAP_ABILITY (and not already tapped as part of costs)
        if trigger_as_enum == EffectTriggerType.TAP_ABILITY: 
             if not card_instance.is_tapped: # Defensive check
                card_instance.tap()
                gs.add_log_entry(f"Card '{card_instance.card_definition.name}' tapped for ability.")

        # Resolve the ability's actual effects using EffectEngine
        # For an activated ability, the source is the card instance itself.
        self.effect_engine.resolve_effect_logic(ability_logic, source_card_instance=card_instance, targets=targets)
        
        if ability_logic.is_once_per_turn:
            card_instance.effects_active_this_turn[effect_signature] = True
            gs.add_log_entry(f"Ability '{ability_logic.description or effect_logic_index}' on '{card_instance.card_definition.name}' marked as used this turn.")
        
        return True

if __name__ == '__main__':
    print("ActionResolver module: Handles player/AI actions and interfaces with EffectEngine.")