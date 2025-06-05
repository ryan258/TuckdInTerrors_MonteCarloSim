# src/tuck_in_terrors_sim/game_logic/action_resolver.py
# Handles resolving player actions like playing cards, activating abilities

from typing import Dict, Optional, Any, List 

from .game_state import GameState, PlayerState # Use PlayerState
from tuck_in_terrors_sim.game_elements.card import Card, Toy, Spell, Ritual, Effect, CardInstance
from ..game_elements.enums import CardType, Zone, EffectTriggerType, EffectActivationCostType, ResourceType
from .effect_engine import EffectEngine 

class ActionResolver:
    def __init__(self, game_state: GameState, effect_engine: EffectEngine):
        self.game_state = game_state
        self.effect_engine = effect_engine 

    def _get_active_player(self) -> Optional[PlayerState]:
        """Helper to get the active player's state."""
        return self.game_state.get_active_player_state()

    def play_card(self, card_instance_id_in_hand: str, is_free_toy_play: bool = False, targets: Optional[List[Any]] = None) -> bool:
        gs = self.game_state
        active_player = self._get_active_player()

        if not active_player:
            gs.add_log_entry("Action Error: No active player found to play card.", level="ERROR")
            return False

        card_to_play_instance: Optional[CardInstance] = None
        card_hand_idx = -1
        for idx, inst in enumerate(active_player.zones[Zone.HAND]):
            if inst.instance_id == card_instance_id_in_hand:
                card_to_play_instance = inst
                card_hand_idx = idx
                break
        
        if not card_to_play_instance:
            gs.add_log_entry(f"Action Error: Card instance '{card_instance_id_in_hand}' not in P{active_player.player_id}'s hand.", level="ERROR")
            return False

        card_def = card_to_play_instance.definition

        if is_free_toy_play:
            if active_player.has_played_free_toy_this_turn:
                gs.add_log_entry(f"Action Error: Free Toy already played this turn. Cannot play '{card_def.name}'.", level="ERROR")
                return False
            if card_def.type != CardType.TOY:
                gs.add_log_entry(f"Action Error: '{card_def.name}' ({card_def.type.name}) is not a Toy for Free Toy Play.", level="ERROR")
                return False
            gs.add_log_entry(f"P{active_player.player_id} attempts Free Toy Play: '{card_def.name}'.")
        else: 
            if active_player.mana < card_def.cost_mana:
                gs.add_log_entry(f"Action Error: P{active_player.player_id} needs {card_def.cost_mana} mana for '{card_def.name}', has {active_player.mana}.", level="ERROR")
                return False
            gs.add_log_entry(f"P{active_player.player_id} attempts to play '{card_def.name}' for {card_def.cost_mana} mana.")
            active_player.mana -= card_def.cost_mana 
            gs.add_log_entry(f"P{active_player.player_id} spent {card_def.cost_mana} mana. Mana: {active_player.mana}.")

        # Card is being played
        original_hand_card = active_player.zones[Zone.HAND].pop(card_hand_idx)
        # Ensure we're using the exact instance popped from hand.
        # card_to_play_instance should be original_hand_card

        if card_def.type == CardType.TOY or card_def.type == CardType.RITUAL:
            gs.move_card_zone(card_to_play_instance, Zone.IN_PLAY, active_player.player_id)
            card_to_play_instance.turn_entered_play = gs.current_turn
            
            gs.add_log_entry(f"P{active_player.player_id} played {card_def.type.name} '{card_def.name}' ({card_to_play_instance.instance_id}) to play area.")
            
            for effect_obj in card_to_play_instance.definition.effects:
                if effect_obj.trigger == EffectTriggerType.ON_PLAY:
                    self.effect_engine.resolve_effect(
                        effect=effect_obj,
                        game_state=gs,
                        player=active_player,
                        source_card_instance=card_to_play_instance,
                        triggering_event_context={'played_card_instance_id': card_to_play_instance.instance_id, 'targets': targets}
                    )

        elif card_def.type == CardType.SPELL:
            gs.add_log_entry(f"P{active_player.player_id} plays Spell '{card_def.name}'. Resolving...")
            
            # Storm effects will read gs.storm_count_this_turn for spells cast *before* this one.
            for effect_obj in card_to_play_instance.definition.effects:
                 if effect_obj.trigger == EffectTriggerType.ON_PLAY:
                    self.effect_engine.resolve_effect(
                        effect=effect_obj,
                        game_state=gs,
                        player=active_player, 
                        source_card_instance=card_to_play_instance, 
                        triggering_event_context={'played_spell_instance_id': card_to_play_instance.instance_id, 'targets': targets}
                    )
            
            # Increment storm count *after* this spell's ON_PLAY effects are resolved,
            # so it counts for subsequent spells this turn.
            gs.storm_count_this_turn += 1 # MODIFIED: Increment storm count
            gs.add_log_entry(f"Spell '{card_def.name}' cast. Storm count for this turn now: {gs.storm_count_this_turn}.")
            
            gs.move_card_zone(card_to_play_instance, Zone.DISCARD, active_player.player_id)
            gs.add_log_entry(f"Spell '{card_def.name}' ({card_to_play_instance.instance_id}) moved to P{active_player.player_id}'s discard pile.")

        if is_free_toy_play:
            active_player.has_played_free_toy_this_turn = True
            gs.add_log_entry(f"Free Toy play for P{active_player.player_id} used this turn.")
            
        return True

    def activate_ability(self, card_instance_id: str, effect_index: int, targets: Optional[List[Any]] = None) -> bool:
        gs = self.game_state
        active_player = self._get_active_player()
        card_instance = gs.get_card_instance(card_instance_id) # Fetches from any zone if needed, but usually IN_PLAY

        if not active_player:
            gs.add_log_entry("Action Error: No active player to activate ability.", level="ERROR"); return False
        if not card_instance:
            gs.add_log_entry(f"Action Error: Card instance '{card_instance_id}' not found.", level="ERROR"); return False
        if card_instance.controller_id != active_player.player_id:
            gs.add_log_entry(f"Action Error: P{active_player.player_id} cannot activate ability of card '{card_instance.definition.name}' controlled by P{card_instance.controller_id}.", level="ERROR"); return False


        card_def = card_instance.definition
        if not (0 <= effect_index < len(card_def.effects)):
            gs.add_log_entry(f"Action Error: Invalid effect_index {effect_index} for '{card_def.name}'.", level="ERROR"); return False

        ability_effect_obj = card_def.effects[effect_index] # This is an Effect object
        
        if ability_effect_obj.trigger not in [EffectTriggerType.ACTIVATED_ABILITY, EffectTriggerType.TAP_ABILITY]:
            gs.add_log_entry(f"Action Error: Effect {effect_index} ('{ability_effect_obj.description}') on '{card_def.name}' is not an activatable type (Trigger: {ability_effect_obj.trigger.name}).", level="ERROR"); return False

        # Check once-per-turn for this specific instance's effect
        # Requires CardInstance to track used effects, e.g., card_instance.effects_used_this_turn : Set[str]
        # effect_signature = ability_effect_obj.effect_id 
        # if effect_signature in card_instance.effects_used_this_turn:
        #    gs.add_log_entry(f"Ability '{ability_effect_obj.description}' on '{card_def.name}' already used this turn.", level="ERROR"); return False

        # Check costs (including tap for TAP_ABILITY)
        # TODO: Detailed cost checking and payment (Phase 4)
        # This needs to use ability_effect_obj.cost (which is a Cost object)
        # For now, simplified:
        if ability_effect_obj.trigger == EffectTriggerType.TAP_ABILITY:
            if card_instance.is_tapped:
                gs.add_log_entry(f"Action Error: Cannot activate tap ability of '{card_def.name}', already tapped.", level="ERROR"); return False
            card_instance.tap()
            gs.add_log_entry(f"Card '{card_def.name}' tapped for ability.")
        
        # Placeholder for other costs from ability_effect_obj.cost
        if ability_effect_obj.cost:
            can_pay = True # Assume true for now
            # Actual logic: iterate ability_effect_obj.cost.cost_details
            # Check mana, spirits, sacrifices, etc. against active_player's resources
            # If not can_pay, return False. Then, pay costs.
            gs.add_log_entry(f"Placeholder: Checking/paying costs for ability: {ability_effect_obj.cost}", "TODO")
            if not can_pay:
                 gs.add_log_entry(f"Action Error: Cannot pay costs for ability on '{card_def.name}'.", "ERROR"); return False


        gs.add_log_entry(f"P{active_player.player_id} activating ability '{ability_effect_obj.description or effect_index}' of '{card_def.name}'.")

        # Resolve the ability's Effect object
        self.effect_engine.resolve_effect(
            effect=ability_effect_obj,
            game_state=gs,
            player=active_player, # Player activating the ability
            source_card_instance=card_instance, # The card whose ability is being activated
            triggering_event_context={'activated_ability_on_instance_id': card_instance.instance_id, 'targets': targets}
        )
        
        # Mark as used if once per turn
        # if once_per_turn_flag_on_effect_obj: card_instance.effects_used_this_turn.add(effect_signature)
        
        return True

if __name__ == '__main__':
    print("ActionResolver module: Handles player/AI actions and interfaces with EffectEngine.")