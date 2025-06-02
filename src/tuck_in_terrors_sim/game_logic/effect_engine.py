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
    EffectTriggerType, CardType # Added CardType for SACRIFICE_CARD_IN_PLAY
)
# Import Card class for type hinting if not fully covered by TYPE_CHECKING
from ..game_elements.card import Card, EffectLogic # Ensure EffectLogic is imported


class EffectEngine:
    def __init__(self, game_state: 'GameState'):
        self.game_state = game_state

    def resolve_effect_logic(self,
                             effect_logic: 'EffectLogic', 
                             source_card_instance: Optional['CardInPlay'] = None,
                             source_card_definition: Optional['Card'] = None,
                             targets: Optional[List[Any]] = None, # targets for the effect if pre-selected
                             event_context: Optional[Dict[str, Any]] = None): # context of the event that triggered this
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

        if not self._check_conditions(effect_logic.conditions, source_card_instance, source_card_definition, targets, event_context):
            gs.add_log_entry(f"EffectEngine: Conditions not met for effect '{effect_desc}'. Effect does not resolve.")
            return

        gs.add_log_entry(f"EffectEngine: Conditions met. Executing actions for '{effect_desc}'.")
        for action_data in effect_logic.actions:
            if gs.game_over:
                gs.add_log_entry(f"EffectEngine: Game ended during action execution of '{effect_desc}'. Halting further actions.", level="INFO")
                break
            self._execute_action(action_data, source_card_instance, source_card_definition, targets, event_context)


    def _check_conditions(self,
                          conditions_data: List[Dict[str, Any]],
                          source_card_instance: Optional['CardInPlay'],
                          source_card_definition: Optional['Card'],
                          targets: Optional[List[Any]],
                          event_context: Optional[Dict[str, Any]] = None) -> bool:
        gs = self.game_state
        if not conditions_data:
            return True 

        for cond_data in conditions_data:
            condition_type_str = cond_data.get("condition_type")
            params = cond_data.get("params", {})
            
            try:
                condition_type = EffectConditionType[condition_type_str]
            except KeyError:
                gs.add_log_entry(f"EffectEngine: Unknown condition type '{condition_type_str}'. Assuming condition FALSE.", level="ERROR")
                return False

            condition_met = False
            
            if condition_type == EffectConditionType.IS_FIRST_MEMORY:
                card_def_to_check = source_card_definition or (source_card_instance.card_definition if source_card_instance else None)
                if card_def_to_check and gs.first_memory_card_definition and \
                   card_def_to_check.card_id == gs.first_memory_card_definition.card_id:
                    condition_met = True
            
            elif condition_type == EffectConditionType.IS_FIRST_MEMORY_IN_PLAY:
                if gs.first_memory_card_definition and \
                   gs.first_memory_current_zone == Zone.IN_PLAY and \
                   gs.first_memory_instance_id is not None: 
                    condition_met = True
            
            elif condition_type == EffectConditionType.HAS_COUNTER_TYPE_VALUE_GE:
                target_instance_id = params.get("target_card_instance_id", "SELF" if source_card_instance else None)
                counter_type_to_check = params.get("counter_type")
                min_amount = params.get("amount", 1)
                
                target_instance = None
                if target_instance_id == "SELF" and source_card_instance:
                    target_instance = source_card_instance
                elif target_instance_id:
                    target_instance = gs.get_card_in_play_by_instance_id(target_instance_id)

                if target_instance and counter_type_to_check:
                    current_amount = target_instance.counters.get(counter_type_to_check, 0)
                    if current_amount >= min_amount:
                        condition_met = True
                    gs.add_log_entry(f"Condition Check HAS_COUNTER_TYPE_VALUE_GE: Target '{target_instance.card_definition.name}' has {current_amount} of '{counter_type_to_check}' (needs >={min_amount}). Met: {condition_met}", level="DEBUG")
                else:
                    gs.add_log_entry(f"Condition Check HAS_COUNTER_TYPE_VALUE_GE: Invalid target or counter_type. Target ID: {target_instance_id}, Counter Type: {counter_type_to_check}", level="WARNING")
            
            else:
                gs.add_log_entry(f"EffectEngine: Condition type '{condition_type.name}' check not yet implemented. Assuming FALSE for safety.", level="WARNING")
                return False

            if not condition_met:
                gs.add_log_entry(f"EffectEngine: Condition '{condition_type.name}' with params {params} NOT MET.")
                return False 
            else:
                gs.add_log_entry(f"EffectEngine: Condition '{condition_type.name}' with params {params} MET.", level="DEBUG")
        
        return True

    def _execute_action(self,
                        action_data: Dict[str, Any],
                        source_card_instance: Optional['CardInPlay'],
                        source_card_definition: Optional['Card'],
                        targets: Optional[List[Any]],
                        event_context: Optional[Dict[str, Any]] = None):
        gs = self.game_state
        action_type_str = action_data.get("action_type")
        params = action_data.get("params", {})

        try:
            action_type = EffectActionType[action_type_str]
        except KeyError:
            gs.add_log_entry(f"EffectEngine: Unknown action type '{action_type_str}'. Action skipped.", level="ERROR")
            return

        gs.add_log_entry(f"EffectEngine: Executing action '{action_type.name}' with params {params}.", level="DEBUG")

        if action_type == EffectActionType.DRAW_CARDS:
            amount = params.get("amount", 0)
            if isinstance(amount, int) and amount > 0:
                for i in range(amount):
                    if gs.deck:
                        drawn_card = gs.deck.pop(0)
                        gs.hand.append(drawn_card)
                        gs.add_log_entry(f"Drew card: {drawn_card.name}.")
                        self.trigger_effects(EffectTriggerType.WHEN_CARD_DRAWN, 
                                             source_card_definition_for_trigger=drawn_card, # The card being drawn
                                             event_context={'drawn_card_definition': drawn_card, 'action_source_instance': source_card_instance, 'action_source_definition': source_card_definition})
                    else:
                        gs.add_log_entry("Cannot draw card: Deck is empty.", level="WARNING")
                        break
                gs.add_log_entry(f"Hand size now: {len(gs.hand)}.")
        
        elif action_type == EffectActionType.CREATE_SPIRIT_TOKENS:
            amount = params.get("amount", 0)
            if isinstance(amount, int) and amount > 0:
                gs.spirit_tokens += amount
                gs.objective_progress["spirits_created_total_game"] = gs.objective_progress.get("spirits_created_total_game", 0) + amount
                gs.add_log_entry(f"Created {amount} Spirit token(s). Total Spirits: {gs.spirit_tokens}.")
                self.trigger_effects(EffectTriggerType.WHEN_SPIRIT_CREATED, 
                                     event_context={'amount': amount, 'action_source_instance': source_card_instance, 'action_source_definition': source_card_definition})
        
        elif action_type == EffectActionType.CREATE_MEMORY_TOKENS:
            amount = params.get("amount", 0)
            if isinstance(amount, int) and amount > 0:
                gs.memory_tokens += amount
                gs.add_log_entry(f"Created {amount} Memory token(s). Total Memory: {gs.memory_tokens}.")
                self.trigger_effects(EffectTriggerType.WHEN_MEMORY_TOKEN_CREATED, 
                                     event_context={'amount': amount, 'action_source_instance': source_card_instance, 'action_source_definition': source_card_definition})
        
        elif action_type == EffectActionType.ADD_MANA:
            amount = params.get("amount", 0)
            source_is_card_effect = bool(source_card_instance or source_card_definition)
            if isinstance(amount, int) and amount > 0:
                gs.mana_pool += amount
                if source_is_card_effect:
                     gs.objective_progress["mana_from_card_effects_total_game"] = gs.objective_progress.get("mana_from_card_effects_total_game", 0) + amount
                     gs.add_log_entry(f"Gained {amount} mana from card effect. Total mana: {gs.mana_pool}. Mana from effects this game: {gs.objective_progress['mana_from_card_effects_total_game']}.")
                else:
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
        
        elif action_type == EffectActionType.PLACE_COUNTER_ON_CARD:
            target_instance_id = params.get("target_card_instance_id", "SELF" if source_card_instance else None)
            counter_type = params.get("counter_type")
            amount = params.get("amount", 1)

            target_instance = None
            if target_instance_id == "SELF" and source_card_instance:
                target_instance = source_card_instance
            elif target_instance_id: # Check if target_instance_id is a string, then fetch
                 if isinstance(target_instance_id, str):
                    target_instance = gs.get_card_in_play_by_instance_id(target_instance_id)
                 # TODO: Add handling if target_instance_id is a CardInPlay object passed directly (e.g. from PLAYER_CHOICE)

            if target_instance and counter_type and isinstance(amount, int) and amount > 0:
                target_instance.add_counter(counter_type, amount)
                gs.add_log_entry(f"Placed {amount} '{counter_type}' counter(s) on '{target_instance.card_definition.name}'. Now has: {target_instance.counters.get(counter_type)}.")
                
                # Check for WHEN_COUNTER_REACHES_THRESHOLD
                # This check is reactive. It means any card that has such a trigger needs to list it.
                self.trigger_effects(
                    EffectTriggerType.WHEN_COUNTER_REACHES_THRESHOLD,
                    source_card_instance_for_trigger=target_instance, # The card that received the counter
                    event_context={
                        'counter_type': counter_type, 
                        'total_amount': target_instance.counters.get(counter_type),
                        'placed_amount': amount,
                        'target_card_instance': target_instance,
                        'action_source_instance': source_card_instance, 
                        'action_source_definition': source_card_definition
                        }
                )
            else:
                gs.add_log_entry(f"Action PLACE_COUNTER_ON_CARD failed: Invalid target, counter_type, or amount. TargetID: {target_instance_id}, Counter: {counter_type}, Amount: {amount}", level="WARNING")

        elif action_type == EffectActionType.SACRIFICE_CARD_IN_PLAY:
            target_id_to_sacrifice = params.get("target_card_instance_id") # Could be "SELF" or an actual ID string
            # Future: could also be a CardInPlay object if a PLAYER_CHOICE resolved to it.
            card_to_sacrifice_instance: Optional['CardInPlay'] = None

            if target_id_to_sacrifice == "SELF" and source_card_instance:
                card_to_sacrifice_instance = source_card_instance
            elif isinstance(target_id_to_sacrifice, str):
                 card_to_sacrifice_instance = gs.get_card_in_play_by_instance_id(target_id_to_sacrifice)
            # elif isinstance(target_id_to_sacrifice, CardInPlay): # Future support if PLAYER_CHOICE passes object
            #    card_to_sacrifice_instance = target_id_to_sacrifice
            
            # TODO: Add logic for "player chooses a Toy to sacrifice" - this will need PLAYER_CHOICE action type first

            if card_to_sacrifice_instance and card_to_sacrifice_instance.instance_id in gs.cards_in_play: # Ensure it's still in play
                card_def = card_to_sacrifice_instance.card_definition
                instance_id = card_to_sacrifice_instance.instance_id
                
                # Create event context for this sacrifice
                sacrifice_event_ctx = {
                    'sacrificed_card_instance': card_to_sacrifice_instance, 
                    'sacrificed_card_definition': card_def,
                    'destination_zone': Zone.DISCARD, # Standard sacrifice destination
                    'action_source_instance': source_card_instance, # Card/effect causing the sacrifice
                    'action_source_definition': source_card_definition
                }

                # Trigger BEFORE_THIS_CARD_LEAVES_PLAY for replacement effects on the card being sacrificed
                self.trigger_effects(EffectTriggerType.BEFORE_THIS_CARD_LEAVES_PLAY, source_card_instance_for_trigger=card_to_sacrifice_instance, event_context=sacrifice_event_ctx)

                # If card is still in play (not replaced by its own effect, e.g. Echo Bear save)
                if card_to_sacrifice_instance.instance_id in gs.cards_in_play:
                    del gs.cards_in_play[instance_id]
                    gs.discard_pile.append(card_def) 
                    gs.add_log_entry(f"Sacrificed '{card_def.name}' (Instance: {instance_id}). Moved to discard pile.")
                    
                    # Trigger ON_LEAVE_PLAY for the sacrificed card
                    self.trigger_effects(EffectTriggerType.ON_LEAVE_PLAY, source_card_instance_for_trigger=card_to_sacrifice_instance, event_context=sacrifice_event_ctx)
                    # Trigger ON_SACRIFICE_THIS_CARD for the sacrificed card
                    self.trigger_effects(EffectTriggerType.ON_SACRIFICE_THIS_CARD, source_card_instance_for_trigger=card_to_sacrifice_instance, event_context=sacrifice_event_ctx)
                    
                    # Trigger "other card" type listeners
                    self.trigger_effects(EffectTriggerType.WHEN_OTHER_CARD_LEAVES_PLAY, event_context=sacrifice_event_ctx)
                    if card_def.card_type == CardType.TOY:
                        self.trigger_effects(EffectTriggerType.WHEN_YOU_SACRIFICE_TOY, event_context=sacrifice_event_ctx)
                else:
                    gs.add_log_entry(f"Sacrifice of '{card_def.name}' was replaced or modified. It's no longer in play as originally intended for standard sacrifice.", level="INFO")

            else:
                gs.add_log_entry(f"Action SACRIFICE_CARD_IN_PLAY: No valid target specified or found in play. Target: {target_id_to_sacrifice}", level="WARNING")
        
        elif action_type == EffectActionType.RETURN_THIS_CARD_TO_HAND:
            if source_card_instance and source_card_instance.instance_id in gs.cards_in_play:
                card_def_to_return = source_card_instance.card_definition
                instance_id_to_return = source_card_instance.instance_id
                
                return_event_ctx = {
                    'returned_card_instance': source_card_instance,
                    'returned_card_definition': card_def_to_return,
                    'destination_zone': Zone.HAND,
                    'action_source_instance': source_card_instance, # Self-return
                    'action_source_definition': source_card_definition 
                }

                self.trigger_effects(EffectTriggerType.BEFORE_THIS_CARD_LEAVES_PLAY, source_card_instance_for_trigger=source_card_instance, event_context=return_event_ctx)

                if source_card_instance.instance_id in gs.cards_in_play: # Check if still in play
                    del gs.cards_in_play[instance_id_to_return]
                    gs.hand.append(card_def_to_return)
                    gs.add_log_entry(f"Returned '{card_def_to_return.name}' (Instance: {instance_id_to_return}) from play to hand.")

                    self.trigger_effects(EffectTriggerType.ON_LEAVE_PLAY, source_card_instance_for_trigger=source_card_instance, event_context=return_event_ctx)
                    self.trigger_effects(EffectTriggerType.WHEN_OTHER_CARD_LEAVES_PLAY, event_context=return_event_ctx)
                else:
                    gs.add_log_entry(f"Return to hand of '{card_def_to_return.name}' was replaced or modified.", level="INFO")


            elif params.get("from_zone_override") == Zone.DISCARD.name and source_card_definition: 
                # This is specific for "Ghost Doll" type effect where it saves itself FROM discard TO hand
                # This should be triggered by BEFORE_THIS_CARD_MOVES_ZONES (from discard to exile)
                # The 'source_card_definition' here is the Ghost Doll itself.
                # The 'event_context' should contain the card trying to move.
                card_to_save: Optional[Card] = None
                if event_context and isinstance(event_context.get('moving_card_definition'), Card):
                    card_to_save = event_context.get('moving_card_definition')
                elif source_card_definition: # Fallback if context is not perfectly set up
                    card_to_save = source_card_definition
                
                if card_to_save and card_to_save in gs.discard_pile:
                    gs.discard_pile.remove(card_to_save)
                    gs.hand.append(card_to_save)
                    gs.add_log_entry(f"Returned '{card_to_save.name}' from discard to hand (special replacement action).")
                else:
                    gs.add_log_entry(f"Action RETURN_THIS_CARD_TO_HAND (from discard special): '{source_card_definition.name if source_card_definition else 'Card'}' not found in discard or invalid params.", level="WARNING")
            else:
                gs.add_log_entry(f"Action RETURN_THIS_CARD_TO_HAND failed: Source card instance not in play or invalid parameters. Source: {source_card_instance.card_definition.name if source_card_instance else 'None'}", level="WARNING")
        
        else:
            gs.add_log_entry(f"EffectEngine: Action type '{action_type.name}' execution not yet implemented. Action skipped.", level="WARNING")

    def trigger_effects(self,
                        trigger_type: EffectTriggerType,
                        source_card_instance_for_trigger: Optional['CardInPlay'] = None, 
                        source_card_definition_for_trigger: Optional['Card'] = None,  
                        event_context: Optional[Dict[str, Any]] = None):
        gs = self.game_state
        
        candidate_effects_to_resolve: List[Tuple[EffectLogic, Optional[CardInPlay], Optional[Card]]] = []
        processed_effect_ids_for_this_trigger = set() # To avoid duplicate processing if an effect lists multiple identical triggers

        # 1. Effects from the card directly causing or experiencing the trigger event
        card_directly_involved_instance = source_card_instance_for_trigger
        card_directly_involved_definition = source_card_definition_for_trigger

        if not card_directly_involved_instance and event_context: # Try to find the card from event context if not passed directly
            card_directly_involved_instance = event_context.get('sacrificed_card_instance') or \
                                              event_context.get('entered_card_instance') or \
                                              event_context.get('left_play_card_instance') or \
                                              event_context.get('target_card_instance') # card that got a counter

        if card_directly_involved_instance:
            for i, el in enumerate(card_directly_involved_instance.card_definition.effect_logic_list):
                effect_unique_id = f"{card_directly_involved_instance.instance_id}_effect_{i}"
                if el.trigger == trigger_type.name and effect_unique_id not in processed_effect_ids_for_this_trigger:
                    candidate_effects_to_resolve.append(
                        (el, card_directly_involved_instance, None)
                    )
                    processed_effect_ids_for_this_trigger.add(effect_unique_id)
        elif card_directly_involved_definition: # E.g. a spell from hand, or a drawn card definition
             for i, el in enumerate(card_directly_involved_definition.effect_logic_list):
                effect_unique_id = f"{card_directly_involved_definition.card_id}_effect_{i}" # card_id for defs
                if el.trigger == trigger_type.name and effect_unique_id not in processed_effect_ids_for_this_trigger:
                    candidate_effects_to_resolve.append(
                        (el, None, card_directly_involved_definition)
                    )
                    processed_effect_ids_for_this_trigger.add(effect_unique_id)
        
        # 2. Effects from other cards in play that are "listening" for this trigger type
        event_card_instance_from_context: Optional['CardInPlay'] = None
        event_card_definition_from_context: Optional['Card'] = None

        if event_context: # Get the card the event is *about*
            event_card_instance_from_context = event_context.get('entered_card_instance') or \
                                               event_context.get('left_play_card_instance') or \
                                               event_context.get('sacrificed_card_instance') or \
                                               event_context.get('target_card_instance')
            if not event_card_instance_from_context:
                 event_card_definition_from_context = event_context.get('drawn_card_definition')


        for listener_card_in_play in list(gs.cards_in_play.values()):
            # Avoid re-processing the same effect on the same card if it was already added as a direct source
            if listener_card_in_play == card_directly_involved_instance and trigger_type in [
                EffectTriggerType.ON_PLAY, EffectTriggerType.ON_LEAVE_PLAY, 
                EffectTriggerType.ON_SACRIFICE_THIS_CARD, EffectTriggerType.ON_ENTER_PLAY_FROM_DISCARD,
                EffectTriggerType.WHEN_COUNTER_REACHES_THRESHOLD # These are typically self-referential
            ]:
                continue

            for i, el in enumerate(listener_card_in_play.card_definition.effect_logic_list):
                effect_unique_id = f"{listener_card_in_play.instance_id}_effect_{i}"
                if el.trigger == trigger_type.name and effect_unique_id not in processed_effect_ids_for_this_trigger:
                    # Handle "WHEN_OTHER_CARD..." triggers
                    is_other_card_event = trigger_type in [
                        EffectTriggerType.WHEN_OTHER_CARD_ENTERS_PLAY, 
                        EffectTriggerType.WHEN_OTHER_CARD_LEAVES_PLAY
                    ]
                    if is_other_card_event:
                        # The listener should not be the card the event is about
                        if (event_card_instance_from_context and listener_card_in_play == event_card_instance_from_context) or \
                           (event_card_definition_from_context and listener_card_in_play.card_definition == event_card_definition_from_context):
                            continue # Skip if listener is the card featured in the "other card" event

                    # WHEN_YOU_SACRIFICE_TOY is also an "other card" style trigger
                    if trigger_type == EffectTriggerType.WHEN_YOU_SACRIFICE_TOY:
                        sacrificed_instance = event_context.get('sacrificed_toy_instance') if event_context else None
                        if sacrificed_instance and listener_card_in_play == sacrificed_instance:
                            continue # The card itself being sacrificed doesn't trigger its own "when you sacrifice a toy"

                    candidate_effects_to_resolve.append((el, listener_card_in_play, None))
                    processed_effect_ids_for_this_trigger.add(effect_unique_id)
        
        if not candidate_effects_to_resolve:
            return

        gs.add_log_entry(f"EffectEngine: Found {len(candidate_effects_to_resolve)} candidate effect(s) for trigger '{trigger_type.name}'. Processing...", level="DEBUG")
        
        # TODO: Ordering of effects (e.g. active player, then other player; or timestamp order)
        # For now, just resolve in the order found.
        for effect_logic_to_resolve, src_instance, src_definition in candidate_effects_to_resolve:
            if gs.game_over: break 
            self.resolve_effect_logic(effect_logic_to_resolve, src_instance, src_definition, 
                                      targets=event_context.get('targets'), # Pass along any pre-selected targets from original action
                                      event_context=event_context) # Pass the full event context

if __name__ == '__main__':
    print("EffectEngine module: Contains logic for resolving card and game effects.")