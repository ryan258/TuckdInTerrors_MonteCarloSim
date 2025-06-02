# src/tuck_in_terrors_sim/game_logic/effect_engine.py
# Core engine to parse and execute card effect_logic

from typing import List, Dict, Any, Optional, Tuple, TYPE_CHECKING
import random 

if TYPE_CHECKING: 
    from .game_state import GameState, CardInPlay
    from ..game_elements.card import Card, EffectLogic

from ..game_elements.enums import (
    EffectConditionType, EffectActionType, ResourceType, Zone,
    EffectTriggerType, CardType, PlayerChoiceType 
)
from ..game_elements.card import Card, EffectLogic 


class EffectEngine:
    def __init__(self, game_state: 'GameState'):
        self.game_state = game_state

    def resolve_effect_logic(self,
                             effect_logic: 'EffectLogic', 
                             source_card_instance: Optional['CardInPlay'] = None,
                             source_card_definition: Optional['Card'] = None,
                             targets: Optional[List[Any]] = None, 
                             event_context: Optional[Dict[str, Any]] = None):
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

        # Ensure event_context is a dict for condition checking if it needs it
        current_event_context = event_context or {}

        if not self._check_conditions(effect_logic.conditions, source_card_instance, source_card_definition, targets, current_event_context):
            gs.add_log_entry(f"EffectEngine: Conditions not met for effect '{effect_desc}'. Effect does not resolve.")
            return

        gs.add_log_entry(f"EffectEngine: Conditions met. Executing actions for '{effect_desc}'.")
        for action_data in effect_logic.actions:
            if gs.game_over:
                gs.add_log_entry(f"EffectEngine: Game ended during action execution of '{effect_desc}'. Halting further actions.", level="INFO")
                break
            # Pass the potentially modified event_context through to sub-actions
            self._execute_action(action_data, source_card_instance, source_card_definition, targets, current_event_context)


    def _check_conditions(self,
                          conditions_data: List[Dict[str, Any]],
                          source_card_instance: Optional['CardInPlay'],
                          source_card_definition: Optional['Card'],
                          targets: Optional[List[Any]],
                          event_context: Dict[str, Any]) -> bool: # event_context is now expected to be a dict
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
                if target_instance_id == "SELF" and source_card_instance: target_instance = source_card_instance
                elif target_instance_id and isinstance(target_instance_id, str): target_instance = gs.get_card_in_play_by_instance_id(target_instance_id)
                if target_instance and counter_type_to_check and target_instance.counters.get(counter_type_to_check, 0) >= min_amount:
                    condition_met = True
            
            elif condition_type == EffectConditionType.IS_FIRST_MEMORY_IN_DISCARD:
                if gs.first_memory_card_definition and gs.first_memory_current_zone == Zone.DISCARD and \
                   gs.first_memory_card_definition in gs.discard_pile:
                    condition_met = True

            elif condition_type == EffectConditionType.DECK_SIZE_LE:
                if len(gs.deck) <= params.get("count", 0):
                    condition_met = True
            
            elif condition_type == EffectConditionType.IS_MOVING_FROM_ZONE:
                zone_str = params.get("zone")
                # event_context is guaranteed to be a dict here
                if event_context.get('original_zone') and zone_str:
                    try:
                        if event_context.get('original_zone') == Zone[zone_str.upper()]: condition_met = True
                    except KeyError: gs.add_log_entry(f"EffectEngine: Condition IS_MOVING_FROM_ZONE invalid zone '{zone_str}'.", level="ERROR")

            elif condition_type == EffectConditionType.IS_MOVING_TO_ZONE:
                zone_str = params.get("zone")
                if event_context.get('destination_zone') and zone_str:
                    try:
                        if event_context.get('destination_zone') == Zone[zone_str.upper()]: condition_met = True
                    except KeyError: gs.add_log_entry(f"EffectEngine: Condition IS_MOVING_TO_ZONE invalid zone '{zone_str}'.", level="ERROR")
            else:
                gs.add_log_entry(f"EffectEngine: Condition type '{condition_type_str}' check not implemented. Assuming FALSE.", level="WARNING")
                return False

            if not condition_met: return False 
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
        
        current_event_context = event_context if event_context is not None else {}

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
                                             source_card_definition_for_trigger=drawn_card, 
                                             event_context={'drawn_card_definition': drawn_card, 
                                                            'action_source_instance': source_card_instance, 
                                                            'action_source_definition': source_card_definition})
                    else:
                        gs.add_log_entry("Cannot draw card: Deck is empty.", level="WARNING") # Corrected log
                        break
        
        elif action_type == EffectActionType.CREATE_SPIRIT_TOKENS:
            amount = params.get("amount", 0)
            if isinstance(amount, int) and amount > 0:
                gs.spirit_tokens += amount
                gs.objective_progress["spirits_created_total_game"] = gs.objective_progress.get("spirits_created_total_game", 0) + amount
                gs.add_log_entry(f"Created {amount} Spirit(s). Total Spirits: {gs.spirit_tokens}.")
                self.trigger_effects(EffectTriggerType.WHEN_SPIRIT_CREATED, 
                                     event_context={'amount': amount, 
                                                    'action_source_instance': source_card_instance, 
                                                    'action_source_definition': source_card_definition})
        
        elif action_type == EffectActionType.CREATE_MEMORY_TOKENS:
            amount = params.get("amount", 0)
            if isinstance(amount, int) and amount > 0:
                gs.memory_tokens += amount
                gs.add_log_entry(f"Created {amount} Memory token(s). Total Memory: {gs.memory_tokens}.")
                self.trigger_effects(EffectTriggerType.WHEN_MEMORY_TOKEN_CREATED, 
                                     event_context={'amount': amount, 
                                                    'action_source_instance': source_card_instance, 
                                                    'action_source_definition': source_card_definition})
        
        elif action_type == EffectActionType.ADD_MANA:
            amount = params.get("amount", 0)
            source_is_card_effect = bool(source_card_instance or source_card_definition)
            if isinstance(amount, int) and amount > 0:
                gs.mana_pool += amount
                if source_is_card_effect:
                     gs.objective_progress["mana_from_card_effects_total_game"] = gs.objective_progress.get("mana_from_card_effects_total_game", 0) + amount
                gs.add_log_entry(f"Gained {amount} mana. Total mana: {gs.mana_pool}.")


        elif action_type == EffectActionType.BROWSE_DECK: # Simplified
            count = params.get("count", 0)
            gs.add_log_entry(f"Placeholder: AI would browse deck (count: {count}). No change.", level="DEBUG")


        elif action_type == EffectActionType.PLACE_COUNTER_ON_CARD:
            target_instance_id = params.get("target_card_instance_id", "SELF" if source_card_instance else None)
            counter_type = params.get("counter_type")
            amount_to_place = params.get("amount", 1)

            target_instance: Optional[CardInPlay] = None
            if target_instance_id == "SELF" and source_card_instance:
                target_instance = source_card_instance
            elif target_instance_id and isinstance(target_instance_id, str): 
                 target_instance = gs.get_card_in_play_by_instance_id(target_instance_id)

            if target_instance and counter_type and isinstance(amount_to_place, int) and amount_to_place > 0:
                target_instance.add_counter(counter_type, amount_to_place)
                gs.add_log_entry(f"Placed {amount_to_place} '{counter_type}' counter(s) on '{target_instance.card_definition.name}'. Now has: {target_instance.counters.get(counter_type)}.")
                
                self.trigger_effects(
                    EffectTriggerType.WHEN_COUNTER_REACHES_THRESHOLD,
                    source_card_instance_for_trigger=target_instance, 
                    event_context={
                        'counter_type': counter_type, 
                        'total_amount': target_instance.counters.get(counter_type),
                        'placed_amount': amount_to_place, # Corrected key based on test
                        'target_card_instance': target_instance,
                        'action_source_instance': source_card_instance, 
                        'action_source_definition': source_card_definition
                        }
                )
            else:
                gs.add_log_entry(f"Action PLACE_COUNTER_ON_CARD failed: Invalid params. TargetID:{target_instance_id}, Counter:{counter_type}, Amount:{amount_to_place}", level="WARNING")

        elif action_type == EffectActionType.SACRIFICE_CARD_IN_PLAY:
            target_id_to_sacrifice = params.get("target_card_instance_id")
            card_to_sacrifice_instance: Optional['CardInPlay'] = None

            if target_id_to_sacrifice == "SELF" and source_card_instance:
                card_to_sacrifice_instance = source_card_instance
            elif isinstance(target_id_to_sacrifice, str):
                 card_to_sacrifice_instance = gs.get_card_in_play_by_instance_id(target_id_to_sacrifice)
            
            if card_to_sacrifice_instance and card_to_sacrifice_instance.instance_id in gs.cards_in_play: 
                card_def = card_to_sacrifice_instance.card_definition
                instance_id = card_to_sacrifice_instance.instance_id
                
                # Build context for BEFORE_THIS_CARD_LEAVES_PLAY
                # source_card_instance and source_card_definition are the source of THIS sacrifice action
                before_leave_ctx = {
                    'card_instance_leaving_play': card_to_sacrifice_instance,
                    'original_zone': Zone.IN_PLAY, 
                    'destination_zone': Zone.DISCARD, 
                    'cancel_leave_play': False, 
                    'action_source_instance': source_card_instance, 
                    'action_source_definition': source_card_definition,
                    **current_event_context # Spread any incoming context
                }
                
                self.trigger_effects(EffectTriggerType.BEFORE_THIS_CARD_LEAVES_PLAY, 
                                     source_card_instance_for_trigger=card_to_sacrifice_instance, 
                                     event_context=before_leave_ctx)

                if before_leave_ctx.get('cancel_leave_play', False):
                    gs.add_log_entry(f"Sacrifice of '{card_def.name}' (Instance: {instance_id}) was cancelled by an effect.", level="INFO")
                elif card_to_sacrifice_instance.instance_id in gs.cards_in_play: # Check again it wasn't removed by a BEFORE trigger
                    del gs.cards_in_play[instance_id]
                    gs.discard_pile.append(card_def) 
                    gs.add_log_entry(f"Sacrificed '{card_def.name}' (Instance: {instance_id}). Moved to discard pile.")
                    
                    if card_def == gs.first_memory_card_definition:
                        gs.first_memory_current_zone = Zone.DISCARD
                        gs.first_memory_instance_id = None

                    after_triggers_ctx = {
                        'sacrificed_card_definition': card_def, 
                        'original_instance_id': instance_id, 
                        'destination_zone': Zone.DISCARD, # For clarity in this context
                        'action_source_instance': source_card_instance, 
                        'action_source_definition': source_card_definition
                    }
                    self.trigger_effects(EffectTriggerType.ON_LEAVE_PLAY, source_card_definition_for_trigger=card_def, event_context=after_triggers_ctx)
                    self.trigger_effects(EffectTriggerType.ON_SACRIFICE_THIS_CARD, source_card_definition_for_trigger=card_def, event_context=after_triggers_ctx)
                    
                    # Context for WHEN_OTHER_CARD_LEAVES_PLAY should clearly identify the card that left
                    other_card_leaves_ctx = {'left_play_card_definition': card_def, 'original_instance_id': instance_id, 'destination_zone': Zone.DISCARD}
                    self.trigger_effects(EffectTriggerType.WHEN_OTHER_CARD_LEAVES_PLAY, event_context=other_card_leaves_ctx) 
                    if card_def.card_type == CardType.TOY:
                        self.trigger_effects(EffectTriggerType.WHEN_YOU_SACRIFICE_TOY, event_context=after_triggers_ctx) # Reuses richer context
                else:
                    gs.add_log_entry(f"'{card_def.name}' (Instance: {instance_id}) was already removed from play during its sacrifice sequence (e.g. by a BEFORE_THIS_CARD_LEAVES_PLAY effect).", level="DEBUG")
            else:
                gs.add_log_entry(f"Action SACRIFICE_CARD_IN_PLAY: No valid target found or target not in play. Target: {target_id_to_sacrifice}", level="WARNING")
        
        elif action_type == EffectActionType.RETURN_THIS_CARD_TO_HAND:
            # This action is primarily for effects on the card itself that cause it to return.
            # source_card_instance is the card being returned.
            if source_card_instance and source_card_instance.instance_id in gs.cards_in_play:
                card_to_return_def = source_card_instance.card_definition
                instance_id_to_return = source_card_instance.instance_id
                
                before_leave_ctx = {
                    'card_instance_leaving_play': source_card_instance,
                    'original_zone': Zone.IN_PLAY,
                    'destination_zone': Zone.HAND,
                    'cancel_leave_play': False,
                    'action_source_instance': source_card_instance, # The card itself is the source of the action
                    'action_source_definition': source_card_definition, # Could be None if no separate def
                    **current_event_context
                }

                self.trigger_effects(EffectTriggerType.BEFORE_THIS_CARD_LEAVES_PLAY, 
                                     source_card_instance_for_trigger=source_card_instance, 
                                     event_context=before_leave_ctx)

                if before_leave_ctx.get('cancel_leave_play', False):
                    gs.add_log_entry(f"Return to hand of '{card_to_return_def.name}' (Instance: {instance_id_to_return}) was cancelled.", level="INFO")
                elif source_card_instance.instance_id in gs.cards_in_play: 
                    del gs.cards_in_play[instance_id_to_return]
                    gs.hand.append(card_to_return_def)
                    gs.add_log_entry(f"Returned '{card_to_return_def.name}' (Instance: {instance_id_to_return}) from play to hand.")

                    if card_to_return_def == gs.first_memory_card_definition:
                        gs.first_memory_current_zone = Zone.HAND
                        gs.first_memory_instance_id = None
                    
                    after_triggers_ctx = {
                        'returned_card_definition': card_to_return_def, # More specific than 'left_play_card_definition'
                        'original_instance_id': instance_id_to_return,
                        'destination_zone': Zone.HAND,
                        'action_source_instance': source_card_instance,
                        'action_source_definition': source_card_definition
                    }
                    self.trigger_effects(EffectTriggerType.ON_LEAVE_PLAY, source_card_definition_for_trigger=card_to_return_def, event_context=after_triggers_ctx)
                    
                    other_card_leaves_ctx = {'left_play_card_definition': card_to_return_def, 'original_instance_id': instance_id_to_return, 'destination_zone': Zone.HAND}
                    self.trigger_effects(EffectTriggerType.WHEN_OTHER_CARD_LEAVES_PLAY, event_context=other_card_leaves_ctx)
                else:
                    gs.add_log_entry(f"'{card_to_return_def.name}' (Instance: {instance_id_to_return}) was already removed during its return to hand sequence.", level="DEBUG")

            elif params.get("from_zone_override") == Zone.DISCARD.name and source_card_definition: 
                # This case is for effects like "instead of exiling from discard, return to hand"
                # source_card_definition is the card in discard.
                if source_card_definition in gs.discard_pile:
                    gs.discard_pile.remove(source_card_definition)
                    gs.hand.append(source_card_definition)
                    gs.add_log_entry(f"Returned '{source_card_definition.name}' from discard to hand (special replacement action).")
                    if source_card_definition == gs.first_memory_card_definition:
                        gs.first_memory_current_zone = Zone.HAND 
                else:
                    gs.add_log_entry(f"Action RETURN_THIS_CARD_TO_HAND (from discard special): '{source_card_definition.name}' not found in discard.", level="WARNING")
            else:
                gs.add_log_entry(f"Action RETURN_THIS_CARD_TO_HAND failed: Source card instance not in play or invalid context. Source: {source_card_instance.card_definition.name if source_card_instance else 'None'}", level="WARNING")
        
        elif action_type == EffectActionType.MILL_DECK: # Restored
            amount = params.get("amount", 0)
            if isinstance(amount, int) and amount > 0:
                milled_cards_names = []
                for _ in range(amount):
                    if gs.deck:
                        milled_card = gs.deck.pop(0)
                        gs.discard_pile.append(milled_card)
                        milled_cards_names.append(milled_card.name)
                        # TODO: Trigger "ON_MILL_THIS_CARD" if such a trigger exists
                    else:
                        gs.add_log_entry("Cannot mill card: Deck is empty.", level="WARNING")
                        break
                if milled_cards_names:
                    gs.add_log_entry(f"Milled {len(milled_cards_names)} card(s): {', '.join(milled_cards_names)}. Moved to discard.")
            else:
                gs.add_log_entry(f"Action MILL_DECK: Invalid amount {amount}.", level="WARNING")

        elif action_type == EffectActionType.EXILE_CARD_FROM_ZONE: # Restored
            from_zone_name = params.get("zone", "DECK").upper() 
            count = params.get("count", 1)
            card_id_to_exile = params.get("card_id") 
            # face_down = params.get("face_down", False) # Not yet fully supported in exile zone state

            from_zone_list: Optional[List[Card]] = None
            zone_enum_member = None
            try:
                zone_enum_member = Zone[from_zone_name]
                if zone_enum_member == Zone.DECK: from_zone_list = gs.deck
                elif zone_enum_member == Zone.HAND: from_zone_list = gs.hand
                elif zone_enum_member == Zone.DISCARD: from_zone_list = gs.discard_pile
                # Other zones like IN_PLAY would need instance handling, not simple list pop.
            except KeyError:
                gs.add_log_entry(f"Action EXILE_CARD_FROM_ZONE: Invalid zone name '{from_zone_name}'.", level="ERROR")
                return

            if from_zone_list is not None:
                exiled_count = 0
                exiled_card_names = []
                for _ in range(count):
                    if not from_zone_list:
                        gs.add_log_entry(f"Cannot exile card: Zone '{from_zone_name}' is empty.", level="WARNING")
                        break
                    
                    card_to_exile: Optional[Card] = None
                    if card_id_to_exile: 
                        found_card_idx = -1
                        for i, card_in_zone in enumerate(from_zone_list):
                            if card_in_zone.card_id == card_id_to_exile:
                                found_card_idx = i
                                break
                        if found_card_idx != -1:
                            card_to_exile = from_zone_list.pop(found_card_idx)
                        else:
                            gs.add_log_entry(f"Card ID '{card_id_to_exile}' not found in {from_zone_name} to exile.", level="WARNING")
                            break 
                    else: # No specific card_id, default logic (top of deck, random from hand)
                        if zone_enum_member == Zone.DECK: 
                            card_to_exile = from_zone_list.pop(0)
                        elif zone_enum_member == Zone.HAND and from_zone_list: 
                            card_to_exile = from_zone_list.pop(random.randrange(len(from_zone_list)))
                        # Add DISCARD logic if needed (e.g. top of discard, or chosen)
                        else:
                            gs.add_log_entry(f"EXILE_CARD_FROM_ZONE: Default exile not implemented for {from_zone_name} or zone empty.", level="WARNING")
                            break
                    
                    if card_to_exile:
                        gs.exile_zone.append(card_to_exile)
                        exiled_card_names.append(card_to_exile.name)
                        exiled_count +=1
                        if card_to_exile == gs.first_memory_card_definition:
                            gs.first_memory_current_zone = Zone.EXILE
                        
                        exile_event_ctx = {'exiled_card_definition': card_to_exile, 'from_zone': zone_enum_member, 'action_source_instance': source_card_instance, 'action_source_definition': source_card_definition}
                        if zone_enum_member == Zone.HAND:
                            self.trigger_effects(EffectTriggerType.WHEN_CARD_EXILED_FROM_HAND, source_card_definition_for_trigger=card_to_exile, event_context=exile_event_ctx)
                        self.trigger_effects(EffectTriggerType.ON_EXILE_THIS_CARD, source_card_definition_for_trigger=card_to_exile, event_context=exile_event_ctx)

                if exiled_count > 0:
                    gs.add_log_entry(f"Exiled {exiled_count} card(s) from {from_zone_name}: {', '.join(exiled_card_names)}.")
            else:
                 gs.add_log_entry(f"Action EXILE_CARD_FROM_ZONE: Zone '{from_zone_name}' not supported for exile from simple list.", level="WARNING")
        
        elif action_type == EffectActionType.RETURN_CARD_FROM_ZONE_TO_ZONE: # Restored
            card_id_to_return = params.get("card_to_return_id") 
            from_zone_name = params.get("from_zone", "DISCARD").upper()
            to_zone_name = params.get("to_zone", "HAND").upper()
            
            card_to_move: Optional[Card] = None
            
            if card_id_to_return == "FIRST_MEMORY":
                card_to_move = gs.first_memory_card_definition
            elif card_id_to_return: 
                # Try to get from event_context if it was "chosen"
                if current_event_context and isinstance(current_event_context.get('chosen_card_definition'), Card): 
                    chosen_card = current_event_context.get('chosen_card_definition')
                    if chosen_card.card_id == card_id_to_return:
                        card_to_move = chosen_card
                # If not in event_context, search the specified from_zone
                if not card_to_move:
                    temp_search_list: List[Card] = []
                    try: 
                        if Zone[from_zone_name] == Zone.DISCARD: temp_search_list = gs.discard_pile
                        elif Zone[from_zone_name] == Zone.EXILE: temp_search_list = gs.exile_zone
                        # Add other zones if searchable by ID
                    except KeyError: pass # Invalid from_zone_name, will be caught later
                    for card_in_src_zone in temp_search_list:
                        if card_in_src_zone.card_id == card_id_to_return:
                            card_to_move = card_in_src_zone
                            break
            
            if not card_to_move and not (card_id_to_return == "FIRST_MEMORY" and not gs.first_memory_card_definition) : # Avoid warning if FIRST_MEMORY chosen but not set
                gs.add_log_entry(f"RETURN_CARD_FROM_ZONE_TO_ZONE: Card ID '{card_id_to_return}' not resolved from event_context or direct search of {from_zone_name}.", level="WARNING")
                return

            source_list: Optional[List[Card]] = None
            from_zone_enum: Optional[Zone] = None
            try:
                from_zone_enum = Zone[from_zone_name] 
                if from_zone_enum == Zone.DISCARD: source_list = gs.discard_pile
                elif from_zone_enum == Zone.EXILE: source_list = gs.exile_zone
                # Add HAND, DECK if cards can be returned from them by ID this way
            except KeyError:
                gs.add_log_entry(f"RETURN_CARD_FROM_ZONE_TO_ZONE: Invalid from_zone name '{from_zone_name}'.", level="ERROR")
                return

            if card_to_move and source_list is not None:
                if card_to_move in source_list:
                    try:
                        source_list.remove(card_to_move) 
                        
                        fm_updated_zone: Optional[Zone] = None
                        log_destination_name = to_zone_name 

                        to_zone_enum_successful = False
                        if to_zone_name == "HAND":
                            gs.hand.append(card_to_move); fm_updated_zone = Zone.HAND; to_zone_enum_successful=True
                        elif to_zone_name == "DECK_TOP":
                            gs.deck.insert(0, card_to_move); fm_updated_zone = Zone.DECK; to_zone_enum_successful=True
                        elif to_zone_name == "DISCARD": # e.g. moving from Exile to Discard
                            gs.discard_pile.append(card_to_move); fm_updated_zone = Zone.DISCARD; to_zone_enum_successful=True
                        elif to_zone_name == "EXILE": # e.g. moving from Discard to Exile
                            gs.exile_zone.append(card_to_move); fm_updated_zone = Zone.EXILE; to_zone_enum_successful=True
                        else:
                            gs.add_log_entry(f"RETURN_CARD_FROM_ZONE_TO_ZONE: Dest zone '{to_zone_name}' not supported. Card '{card_to_move.name}' removed from source.", level="WARNING")
                            # Consider re-adding to source_list or a 'lost' zone if this is critical
                        
                        if to_zone_enum_successful:
                             gs.add_log_entry(f"Moved '{card_to_move.name}' from {from_zone_name} to {log_destination_name}.", level="INFO")
                             if card_to_move == gs.first_memory_card_definition and fm_updated_zone:
                                gs.first_memory_current_zone = fm_updated_zone
                                if fm_updated_zone != Zone.IN_PLAY: gs.first_memory_instance_id = None
                        
                    except ValueError: # Should not happen if 'in' check passed
                         gs.add_log_entry(f"RETURN_CARD_FROM_ZONE_TO_ZONE: Error removing '{card_to_move.name}' from {from_zone_name}.", level="ERROR")
                else:
                    gs.add_log_entry(f"RETURN_CARD_FROM_ZONE_TO_ZONE: Card '{card_to_move.name}' not in source_list {from_zone_name}.", level="WARNING")
            
            elif not card_to_move and card_id_to_return == "FIRST_MEMORY" and not gs.first_memory_card_definition:
                 gs.add_log_entry(f"RETURN_CARD_FROM_ZONE_TO_ZONE: FIRST_MEMORY chosen but no First Memory set in game.", level="INFO")
            elif not card_to_move: # Already logged if card_id was not resolved
                pass
            elif source_list is None: 
                gs.add_log_entry(f"RETURN_CARD_FROM_ZONE_TO_ZONE: Source list for '{from_zone_name}' could not be determined.", level="WARNING")


        elif action_type == EffectActionType.PLAYER_CHOICE:
            choice_id = params.get('choice_id', 'generic_choice')
            choice_type_str = params.get('choice_type')
            prompt_text = params.get('prompt_text', 'Make a choice.')
            options_from_params = params.get('options') 

            if not choice_type_str:
                gs.add_log_entry(f"EffectEngine: PLAYER_CHOICE for '{choice_id}' missing 'choice_type'. Skipped.", level="ERROR"); return
            if not gs.ai_player: 
                gs.add_log_entry(f"EffectEngine: PLAYER_CHOICE for '{choice_id}' but no AI player. Skipped.", level="ERROR"); return

            choice_context_for_ai = {
                'choice_id': choice_id, 'choice_type': choice_type_str, 'prompt_text': prompt_text,
                'options': options_from_params, **params 
            }
            gs.add_log_entry(f"EffectEngine: Presenting choice '{prompt_text}' (ID: {choice_id}, Type: {choice_type_str}) to AI.", level="INFO")
            ai_decision = gs.ai_player.make_choice(gs, choice_context_for_ai)
            gs.add_log_entry(f"EffectEngine: AI for '{choice_id}' chose: {ai_decision}", level="INFO")

            try: actual_choice_type = PlayerChoiceType[choice_type_str]
            except KeyError: gs.add_log_entry(f"EffectEngine: PLAYER_CHOICE '{choice_id}' had unknown type '{choice_type_str}'.", level="ERROR"); return

            if actual_choice_type == PlayerChoiceType.CHOOSE_YES_NO:
                actions_list = params.get('on_yes_actions', []) if ai_decision is True else (params.get('on_no_actions', []) if ai_decision is False else [])
                for sub_action_data in actions_list:
                    if gs.game_over: break
                    self._execute_action(sub_action_data, source_card_instance, source_card_definition, targets, current_event_context) # Pass original event_context
            
            elif actual_choice_type == PlayerChoiceType.DISCARD_CARD_OR_SACRIFICE_SPIRIT:
                if ai_decision == "DISCARD":
                    discard_action_params = {"amount": 1, "prompt_text": f"Choose card to discard for {choice_id}."}
                    # Allow original PLAYER_CHOICE to specify amount to discard.
                    if "amount_to_discard" in params: discard_action_params["amount"] = params["amount_to_discard"]

                    self._execute_action({"action_type": EffectActionType.DISCARD_CARDS_CHOSEN_FROM_HAND.name, "params": discard_action_params}, 
                                         source_card_instance, source_card_definition, targets, current_event_context)
                elif ai_decision == "SACRIFICE_SPIRIT":
                    sacrifice_action_params = {"resource_type": ResourceType.SPIRIT.name, "amount": 1}
                    # Allow original PLAYER_CHOICE to specify amount to sacrifice.
                    if "amount_to_sacrifice" in params: sacrifice_action_params["amount"] = params["amount_to_sacrifice"]
                    self._execute_action({"action_type": EffectActionType.SACRIFICE_RESOURCE.name, "params": sacrifice_action_params}, 
                                         source_card_instance, source_card_definition, targets, current_event_context)
                else:
                    gs.add_log_entry(f"EffectEngine: AI decision for '{choice_id}' was '{ai_decision}', expected 'DISCARD' or 'SACRIFICE_SPIRIT'. No action taken.", level="WARNING")
            else:
                gs.add_log_entry(f"EffectEngine: AI decision processing for choice_type '{actual_choice_type.name}' (ID: {choice_id}) not yet implemented.", level="WARNING")
        
        elif action_type == EffectActionType.DISCARD_CARDS_CHOSEN_FROM_HAND:
            amount_to_discard = params.get("amount", 1)
            prompt_text = params.get("prompt_text", "Choose card(s) to discard.")
            
            if not gs.ai_player: gs.add_log_entry("DISCARD_CHOSEN: No AI player.", level="ERROR"); return
            if not gs.hand: gs.add_log_entry("DISCARD_CHOSEN: Hand empty.", level="INFO"); return

            for _ in range(amount_to_discard):
                if not gs.hand: gs.add_log_entry("DISCARD_CHOSEN: Hand became empty mid-discard.", level="INFO"); break
                
                choice_context_for_ai = {'choice_id': 'discard_card_from_hand_choice', 
                                 'choice_type': PlayerChoiceType.CHOOSE_CARD_FROM_HAND.name, 
                                 'prompt_text': prompt_text, 'options': list(gs.hand) }
                card_to_discard_obj = gs.ai_player.make_choice(gs, choice_context_for_ai)

                if card_to_discard_obj and isinstance(card_to_discard_obj, Card) and card_to_discard_obj in gs.hand:
                    gs.hand.remove(card_to_discard_obj)
                    gs.discard_pile.append(card_to_discard_obj)
                    gs.add_log_entry(f"EffectEngine: AI chose to discard '{card_to_discard_obj.name}'. Moved to discard pile.", level="INFO")
                    # Trigger ON_DISCARD_THIS_CARD effects
                    self.trigger_effects(EffectTriggerType.ON_DISCARD_THIS_CARD, 
                                         source_card_definition_for_trigger=card_to_discard_obj,
                                         event_context={'discarded_card_definition': card_to_discard_obj, 'reason': 'EFFECT_CHOICE',
                                                        'action_source_instance': source_card_instance, 
                                                        'action_source_definition': source_card_definition})
                else:
                    gs.add_log_entry(f"EffectEngine: AI failed to choose a valid card to discard or chose None. Stopping discard.", level="WARNING")
                    break 
        
        elif action_type == EffectActionType.SACRIFICE_RESOURCE:
            resource_type_str = params.get("resource_type")
            amount = params.get("amount", 1)
            try:
                resource_type = ResourceType[resource_type_str.upper()]
                if resource_type == ResourceType.SPIRIT:
                    actual_sacrificed = min(gs.spirit_tokens, amount)
                    if actual_sacrificed > 0:
                        gs.spirit_tokens -= actual_sacrificed
                        gs.add_log_entry(f"EffectEngine: Sacrificed {actual_sacrificed} Spirit token(s). Remaining: {gs.spirit_tokens}.", level="INFO")
                    else:
                         gs.add_log_entry(f"EffectEngine: No Spirit tokens to sacrifice (needed {amount}, has {gs.spirit_tokens}).", level="INFO")
                else:
                    gs.add_log_entry(f"EffectEngine: SACRIFICE_RESOURCE for type '{resource_type.name}' not fully implemented.", level="WARNING")
            except KeyError:
                gs.add_log_entry(f"EffectEngine: SACRIFICE_RESOURCE unknown resource_type '{resource_type_str}'.", level="ERROR")

        elif action_type == EffectActionType.CANCEL_IMPENDING_LEAVE_PLAY:
            current_event_context['cancel_leave_play'] = True 
            card_name = "Unknown Card"
            # Determine card being saved for logging more accurately
            if 'card_instance_leaving_play' in current_event_context and current_event_context['card_instance_leaving_play']:
                 card_name = current_event_context['card_instance_leaving_play'].card_definition.name
            elif source_card_instance: card_name = source_card_instance.card_definition.name
            elif source_card_definition: card_name = source_card_definition.name
            gs.add_log_entry(f"EffectEngine: Action CANCEL_IMPENDING_LEAVE_PLAY for '{card_name}' recorded.", level="DEBUG")
            
        elif action_type == EffectActionType.CANCEL_IMPENDING_MOVE: # More general cancel
             current_event_context['cancel_move'] = True # Note: This flag isn't used by current actions yet
             gs.add_log_entry(f"EffectEngine: Action CANCEL_IMPENDING_MOVE recorded in event_context.", level="DEBUG")

        else:
            gs.add_log_entry(f"EffectEngine: Action type '{action_type.name}' execution not yet implemented. Action skipped.", level="WARNING")

    def trigger_effects(self,
                        trigger_type: EffectTriggerType,
                        source_card_instance_for_trigger: Optional['CardInPlay'] = None, 
                        source_card_definition_for_trigger: Optional['Card'] = None,  
                        event_context: Optional[Dict[str, Any]] = None):
        gs = self.game_state
        
        candidate_effects_to_resolve: List[Tuple[EffectLogic, Optional[CardInPlay], Optional[Card]]] = []
        # Using set of (card_id/instance_id, effect_index_in_list) to track processed effects for THIS trigger event
        processed_effect_identifiers_this_event = set() 

        current_event_context = event_context or {}

        # Card instance or definition that is the primary subject of the trigger
        # (e.g., the card whose own "ON_PLAY" or "BEFORE_THIS_CARD_LEAVES_PLAY" is firing)
        subject_card_inst = source_card_instance_for_trigger
        subject_card_def = source_card_definition_for_trigger

        # If not provided directly, try to infer from event_context
        if not subject_card_inst and not subject_card_def and current_event_context:
            subject_card_inst = current_event_context.get('card_instance_leaving_play') or \
                                current_event_context.get('entered_card_instance') or \
                                current_event_context.get('sacrificed_card_instance') or \
                                current_event_context.get('target_card_instance') # For counter triggers
            if not subject_card_inst:
                 subject_card_def = current_event_context.get('drawn_card_definition') or \
                                    current_event_context.get('exiled_card_definition') or \
                                    current_event_context.get('sacrificed_card_definition') or \
                                    current_event_context.get('returned_card_definition')


        # 1. Effects on the subject card itself (if applicable)
        if subject_card_inst:
            for i, el in enumerate(subject_card_inst.card_definition.effect_logic_list):
                effect_unique_id = (subject_card_inst.instance_id, i)
                if el.trigger == trigger_type.name and effect_unique_id not in processed_effect_identifiers_this_event:
                    candidate_effects_to_resolve.append((el, subject_card_inst, None))
                    processed_effect_identifiers_this_event.add(effect_unique_id)
        elif subject_card_def: # For cards not in play (spells, or cards that just left)
            for i, el in enumerate(subject_card_def.effect_logic_list):
                effect_unique_id = (subject_card_def.card_id, i) # Use card_id for non-instances
                if el.trigger == trigger_type.name and effect_unique_id not in processed_effect_identifiers_this_event:
                    candidate_effects_to_resolve.append((el, None, subject_card_def))
                    processed_effect_identifiers_this_event.add(effect_unique_id)
        
        # 2. Effects on all cards currently in play (listening effects)
        #    This also covers global triggers that aren't tied to a specific source_card_instance_for_trigger
        for listener_card_in_play in list(gs.cards_in_play.values()): # Iterate on a copy
            # Skip re-adding subject_card_inst's effects if they were already added above
            if listener_card_in_play == subject_card_inst and subject_card_inst is not None:
                 # Check if its effects for this trigger were already processed via the subject_card_inst block
                 # This check assumes that if subject_card_inst was processed, all its relevant effects for this trigger_type are in.
                 # This is a simplification; a more robust approach would check if a specific effect_unique_id was added.
                 # For now, if it's the subject_card_inst, we assume its direct effects handled above.
                 # This is mainly to avoid double-adding for triggers like ON_PLAY for the card itself.
                 # For "WHEN_OTHER..." triggers, the subject_card_inst IS the "other" card from listener's perspective.
                 pass # Handled above, or needs specific logic for "OTHER"


            for i, el in enumerate(listener_card_in_play.card_definition.effect_logic_list):
                effect_unique_id = (listener_card_in_play.instance_id, i)
                if el.trigger == trigger_type.name and effect_unique_id not in processed_effect_identifiers_this_event:
                    # Check for "OTHER" card triggers to ensure the listener is not the event's subject
                    is_other_card_trigger = trigger_type in [
                        EffectTriggerType.WHEN_OTHER_CARD_ENTERS_PLAY, 
                        EffectTriggerType.WHEN_OTHER_CARD_LEAVES_PLAY
                    ]
                    if is_other_card_trigger:
                        card_that_moved_inst = current_event_context.get('entered_card_instance') or current_event_context.get('left_play_card_instance') # Or other relevant keys
                        card_that_moved_def = current_event_context.get('left_play_card_definition') # if instance is gone
                        
                        if listener_card_in_play == card_that_moved_inst:
                            continue # Listener IS the card that moved, not an "other"
                        if card_that_moved_def and listener_card_in_play.card_definition.card_id == card_that_moved_def.card_id and listener_card_in_play.instance_id == current_event_context.get('original_instance_id'):
                            continue # Listener was the card that moved (matched by original_instance_id)


                    candidate_effects_to_resolve.append((el, listener_card_in_play, None))
                    processed_effect_identifiers_this_event.add(effect_unique_id)
        
        if not candidate_effects_to_resolve:
            return

        gs.add_log_entry(f"EffectEngine: Found {len(candidate_effects_to_resolve)} candidate effect(s) for trigger '{trigger_type.name}'. Processing...", level="DEBUG")
        
        for effect_logic_to_resolve, src_instance, src_definition in candidate_effects_to_resolve:
            if gs.game_over: break 
            # Pass a copy of the event_context for each resolution to avoid cross-contamination if an effect modifies it
            # (e.g. a PLAYER_CHOICE setting a 'cancel_leave_play' flag that only applies to its own chain)
            # However, if sub-actions within resolve_effect_logic need to see modifications from prior actions
            # in the *same effect_logic.actions list*, then event_context should be the same dict instance.
            # The current resolve_effect_logic -> _execute_action loop already passes the same event_context.
            self.resolve_effect_logic(effect_logic_to_resolve, src_instance, src_definition, 
                                      targets=current_event_context.get('targets'), 
                                      event_context=current_event_context) # Pass the shared context for this effect's actions