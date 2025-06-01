# src/tuck_in_terrors_sim/game_logic/effect_engine.py
# Core engine to parse and execute card effect_logic

from typing import List, Dict, Any, Optional, Tuple, TYPE_CHECKING
import random # For BROWSE_DECK if we just shuffle back for now

if TYPE_CHECKING: # To avoid circular imports for type hinting
    from .game_state import GameState, CardInPlay
    from ..game_elements.card import Card, EffectLogic
    # from .action_resolver import ActionResolver # If effects can trigger new actions

# Import enums
from ..game_elements.enums import (
    EffectConditionType, EffectActionType, ResourceType, Zone,
    EffectTriggerType
)
# Import Card class for type hinting if not fully covered by TYPE_CHECKING
from ..game_elements.card import Card, EffectLogic # Ensure EffectLogic is imported


class EffectEngine:
    def __init__(self, game_state: 'GameState'): #, action_resolver: Optional['ActionResolver'] = None):
        self.game_state = game_state
        # self.action_resolver = action_resolver # For effects that might trigger player choices

    def resolve_effect_logic(self,
                             effect_logic: 'EffectLogic', # Type hint EffectLogic
                             source_card_instance: Optional['CardInPlay'] = None,
                             source_card_definition: Optional['Card'] = None,
                             targets: Optional[List[Any]] = None): # targets here refers to any pre-selected targets for the effect
        """
        Resolves a single EffectLogic object: checks conditions and executes actions.
        """
        gs = self.game_state
        source_name = ""
        if source_card_instance:
            source_name = source_card_instance.card_definition.name
        elif source_card_definition:
            source_name = source_card_definition.name
        else:
            source_name = "Unknown Source (e.g., Game Rule, Objective)"
        
        effect_desc = effect_logic.description or effect_logic.trigger
        gs.add_log_entry(f"EffectEngine: Evaluating effect '{effect_desc}' from '{source_name}'.")

        if not self._check_conditions(effect_logic.conditions, source_card_instance, source_card_definition, targets):
            gs.add_log_entry(f"EffectEngine: Conditions not met for effect '{effect_desc}'. Effect does not resolve.")
            return

        # Activation costs for ACTIVATED_ABILITY should be handled by ActionResolver before calling this.
        # This method assumes costs (if any for this type of trigger) have been met.

        gs.add_log_entry(f"EffectEngine: Conditions met. Executing actions for '{effect_desc}'.")
        for action_data in effect_logic.actions:
            if gs.game_over:
                gs.add_log_entry(f"EffectEngine: Game ended during action execution of '{effect_desc}'. Halting further actions.", level="INFO")
                break
            self._execute_action(action_data, source_card_instance, source_card_definition, targets)


    def _check_conditions(self,
                          conditions_data: List[Dict[str, Any]],
                          source_card_instance: Optional['CardInPlay'],
                          source_card_definition: Optional['Card'],
                          targets: Optional[List[Any]]) -> bool:
        gs = self.game_state
        if not conditions_data:
            return True # No conditions means an effect always attempts to resolve if triggered

        for cond_data in conditions_data:
            condition_type_str = cond_data.get("condition_type")
            params = cond_data.get("params", {})
            
            try:
                condition_type = EffectConditionType[condition_type_str]
            except KeyError:
                gs.add_log_entry(f"EffectEngine: Unknown condition type '{condition_type_str}'. Assuming condition FALSE.", level="ERROR")
                return False

            condition_met = False
            # --- Initial Condition Implementations ---
            if condition_type == EffectConditionType.IS_FIRST_MEMORY:
                # This condition applies if the *source card itself* is the First Memory
                card_def_to_check = source_card_definition or (source_card_instance.card_definition if source_card_instance else None)
                if card_def_to_check and gs.first_memory_card_definition and \
                   card_def_to_check.card_id == gs.first_memory_card_definition.card_id:
                    condition_met = True
            
            elif condition_type == EffectConditionType.IS_FIRST_MEMORY_IN_PLAY:
                if gs.first_memory_card_definition and \
                   gs.first_memory_current_zone == Zone.IN_PLAY and \
                   gs.first_memory_instance_id is not None: 
                    condition_met = True
            
            # TODO: Add more condition checks here (Phase 4)
            # E.g., PLAYER_HAS_RESOURCE, CARD_IN_ZONE, etc.
            else:
                gs.add_log_entry(f"EffectEngine: Condition type '{condition_type.name}' check not yet implemented. Assuming FALSE for safety.", level="WARNING")
                return False # Default to false for unimplemented conditions

            if not condition_met:
                gs.add_log_entry(f"EffectEngine: Condition '{condition_type.name}' with params {params} NOT MET.")
                return False # If any condition is not met, the whole set fails
            else:
                gs.add_log_entry(f"EffectEngine: Condition '{condition_type.name}' with params {params} MET.", level="DEBUG")
        
        return True # All conditions passed

    def _execute_action(self,
                        action_data: Dict[str, Any],
                        source_card_instance: Optional['CardInPlay'],
                        source_card_definition: Optional['Card'],
                        targets: Optional[List[Any]]): # `targets` here are those passed to resolve_effect_logic
        gs = self.game_state
        action_type_str = action_data.get("action_type")
        params = action_data.get("params", {})

        try:
            action_type = EffectActionType[action_type_str]
        except KeyError:
            gs.add_log_entry(f"EffectEngine: Unknown action type '{action_type_str}'. Action skipped.", level="ERROR")
            return

        gs.add_log_entry(f"EffectEngine: Executing action '{action_type.name}' with params {params}.", level="DEBUG")

        # --- Initial Action Implementations ---
        if action_type == EffectActionType.DRAW_CARDS:
            amount = params.get("amount", 0)
            if isinstance(amount, int) and amount > 0:
                for _ in range(amount):
                    if gs.deck:
                        drawn_card = gs.deck.pop(0)
                        gs.hand.append(drawn_card)
                        gs.add_log_entry(f"Drew card: {drawn_card.name}.")
                    else:
                        gs.add_log_entry("Cannot draw card: Deck is empty.", level="WARNING")
                        break
                gs.add_log_entry(f"Hand size now: {len(gs.hand)}.")
        
        elif action_type == EffectActionType.CREATE_SPIRIT_TOKENS:
            amount = params.get("amount", 0)
            if isinstance(amount, int) and amount > 0:
                gs.spirit_tokens += amount
                gs.add_log_entry(f"Created {amount} Spirit token(s). Total Spirits: {gs.spirit_tokens}.")

        elif action_type == EffectActionType.CREATE_MEMORY_TOKENS:
            amount = params.get("amount", 0)
            if isinstance(amount, int) and amount > 0:
                gs.memory_tokens += amount
                gs.add_log_entry(f"Created {amount} Memory token(s). Total Memory: {gs.memory_tokens}.")
        
        elif action_type == EffectActionType.ADD_MANA:
            amount = params.get("amount", 0)
            if isinstance(amount, int) and amount > 0:
                gs.mana_pool += amount
                gs.add_log_entry(f"Gained {amount} mana. Total mana: {gs.mana_pool}.")

        elif action_type == EffectActionType.BROWSE_DECK:
            count = params.get("count", 0)
            if isinstance(count, int) and count > 0 and gs.deck:
                num_to_browse = min(count, len(gs.deck))
                browsed_cards = gs.deck[:num_to_browse] 
                gs.add_log_entry(f"Browse top {num_to_browse} card(s): {[c.name for c in browsed_cards]}.")
                gs.add_log_entry(f"Placeholder: AI would choose order/destination for browsed cards. For now, no change to deck order.", level="INFO")
            elif not gs.deck:
                 gs.add_log_entry("Cannot browse deck: Deck is empty.", level="WARNING")
            else:
                 gs.add_log_entry(f"Browse deck called with invalid count {count}. No action taken.", level="INFO")
        
        else:
            gs.add_log_entry(f"EffectEngine: Action type '{action_type.name}' execution not yet implemented. Action skipped.", level="WARNING")

    def trigger_effects(self,
                        trigger_type: EffectTriggerType,
                        source_card_instance_for_trigger: Optional['CardInPlay'] = None,
                        source_card_definition_for_trigger: Optional['Card'] = None,
                        event_context: Optional[Dict[str, Any]] = None):
        gs = self.game_state
        gs.add_log_entry(f"EffectEngine: System event - Evaluating triggers for '{trigger_type.name}'. Context: {event_context}", level="DEBUG")

        candidate_effects_to_resolve: List[Tuple[EffectLogic, Optional[CardInPlay], Optional[Card]]] = []

        if source_card_instance_for_trigger:
            for el in source_card_instance_for_trigger.card_definition.effect_logic_list:
                if el.trigger == trigger_type.name: # Assumes trigger in EffectLogic is stored as enum name string
                    candidate_effects_to_resolve.append(
                        (el, source_card_instance_for_trigger, None)
                    )
        elif source_card_definition_for_trigger: 
            for el in source_card_definition_for_trigger.effect_logic_list:
                 if el.trigger == trigger_type.name:
                    candidate_effects_to_resolve.append(
                        (el, None, source_card_definition_for_trigger)
                    )
        
        for card_in_play in list(gs.cards_in_play.values()): 
            is_self_event_source = False
            if event_context:
                # Check common keys used in event_context that might point to the card_in_play instance
                if event_context.get('entered_card_instance') == card_in_play or \
                   event_context.get('left_play_card_instance') == card_in_play or \
                   event_context.get('source_card_instance') == card_in_play : # If the event itself originated from this card
                    is_self_event_source = True

            for el in card_in_play.card_definition.effect_logic_list:
                if el.trigger == trigger_type.name: # Assumes trigger in EffectLogic is stored as enum name string
                    # For "other card" triggers, don't let a card trigger on its own event.
                    if trigger_type in [EffectTriggerType.WHEN_OTHER_CARD_ENTERS_PLAY, EffectTriggerType.WHEN_OTHER_CARD_LEAVES_PLAY] and is_self_event_source:
                        # This check needs refinement: if 'entered_card_instance' is 'card_in_play', then it's NOT an "other" card.
                        # This logic is tricky. Let's re-evaluate "is_self_event_source"
                        # The `source_card_instance_for_trigger` is for the effect *being resolved*.
                        # The `card_in_play` is the potential *listener*.
                        # If the event is about card_in_play itself, it shouldn't trigger its own "other card" listener.
                        # This part of trigger_effects needs careful thought for WHEN_OTHER_... triggers
                        pass # Revisit self-triggering for "other" types later
                    
                    candidate_effects_to_resolve.append((el, card_in_play, None))
        
        if not candidate_effects_to_resolve:
            gs.add_log_entry(f"EffectEngine: No effects found to process for trigger '{trigger_type.name}'.", level="DEBUG")
            return

        gs.add_log_entry(f"EffectEngine: Found {len(candidate_effects_to_resolve)} candidate effect(s) for trigger '{trigger_type.name}'. Processing...", level="DEBUG")
        
        for effect_logic_to_resolve, src_instance, src_definition in candidate_effects_to_resolve:
            if gs.game_over: break 
            self.resolve_effect_logic(effect_logic_to_resolve, src_instance, src_definition, targets=event_context)


if __name__ == '__main__':
    print("EffectEngine module: Contains logic for resolving card and game effects.")