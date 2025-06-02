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
    EffectTriggerType, CardType 
)
# Import Card class for type hinting if not fully covered by TYPE_CHECKING
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
            
            elif condition_type == EffectConditionType.IS_FIRST_MEMORY_IN_DISCARD:
                if gs.first_memory_card_definition and gs.first_memory_current_zone == Zone.DISCARD:
                    if gs.first_memory_card_definition in gs.discard_pile:
                        condition_met = True
                gs.add_log_entry(f"Condition Check IS_FIRST_MEMORY_IN_DISCARD: FM is '{gs.first_memory_card_definition.name if gs.first_memory_card_definition else 'None'}' and zone is {gs.first_memory_current_zone}. In discard pile: {gs.first_memory_card_definition in gs.discard_pile if gs.first_memory_card_definition else False}. Met: {condition_met}", level="DEBUG")

            elif condition_type == EffectConditionType.DECK_SIZE_LE:
                max_cards = params.get("count", 0)
                if len(gs.deck) <= max_cards:
                    condition_met = True
                gs.add_log_entry(f"Condition Check DECK_SIZE_LE: Deck size {len(gs.deck)} <= {max_cards}. Met: {condition_met}", level="DEBUG")

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
                                             source_card_definition_for_trigger=drawn_card, 
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
            elif target_instance_id: 
                 if isinstance(target_instance_id, str):
                    target_instance = gs.get_card_in_play_by_instance_id(target_instance_id)

            if target_instance and counter_type and isinstance(amount, int) and amount > 0:
                target_instance.add_counter(counter_type, amount)
                gs.add_log_entry(f"Placed {amount} '{counter_type}' counter(s) on '{target_instance.card_definition.name}'. Now has: {target_instance.counters.get(counter_type)}.")
                
                self.trigger_effects(
                    EffectTriggerType.WHEN_COUNTER_REACHES_THRESHOLD,
                    source_card_instance_for_trigger=target_instance, 
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
            target_id_to_sacrifice = params.get("target_card_instance_id") 
            card_to_sacrifice_instance: Optional['CardInPlay'] = None

            if target_id_to_sacrifice == "SELF" and source_card_instance:
                card_to_sacrifice_instance = source_card_instance
            elif isinstance(target_id_to_sacrifice, str):
                 card_to_sacrifice_instance = gs.get_card_in_play_by_instance_id(target_id_to_sacrifice)
            
            if card_to_sacrifice_instance and card_to_sacrifice_instance.instance_id in gs.cards_in_play: 
                card_def = card_to_sacrifice_instance.card_definition
                instance_id = card_to_sacrifice_instance.instance_id
                
                sacrifice_event_ctx = {
                    'sacrificed_card_instance': card_to_sacrifice_instance, 
                    'sacrificed_card_definition': card_def,
                    'destination_zone': Zone.DISCARD, 
                    'action_source_instance': source_card_instance, 
                    'action_source_definition': source_card_definition
                }

                self.trigger_effects(EffectTriggerType.BEFORE_THIS_CARD_LEAVES_PLAY, source_card_instance_for_trigger=card_to_sacrifice_instance, event_context=sacrifice_event_ctx)

                if card_to_sacrifice_instance.instance_id in gs.cards_in_play:
                    del gs.cards_in_play[instance_id]
                    gs.discard_pile.append(card_def) 
                    gs.add_log_entry(f"Sacrificed '{card_def.name}' (Instance: {instance_id}). Moved to discard pile.")
                    
                    self.trigger_effects(EffectTriggerType.ON_LEAVE_PLAY, source_card_instance_for_trigger=card_to_sacrifice_instance, event_context=sacrifice_event_ctx)
                    self.trigger_effects(EffectTriggerType.ON_SACRIFICE_THIS_CARD, source_card_instance_for_trigger=card_to_sacrifice_instance, event_context=sacrifice_event_ctx)
                    
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
                    'action_source_instance': source_card_instance, 
                    'action_source_definition': source_card_definition 
                }

                self.trigger_effects(EffectTriggerType.BEFORE_THIS_CARD_LEAVES_PLAY, source_card_instance_for_trigger=source_card_instance, event_context=return_event_ctx)

                if source_card_instance.instance_id in gs.cards_in_play: 
                    del gs.cards_in_play[instance_id_to_return]
                    gs.hand.append(card_def_to_return)
                    gs.add_log_entry(f"Returned '{card_def_to_return.name}' (Instance: {instance_id_to_return}) from play to hand.")

                    self.trigger_effects(EffectTriggerType.ON_LEAVE_PLAY, source_card_instance_for_trigger=source_card_instance, event_context=return_event_ctx)
                    self.trigger_effects(EffectTriggerType.WHEN_OTHER_CARD_LEAVES_PLAY, event_context=return_event_ctx)
                else:
                    gs.add_log_entry(f"Return to hand of '{card_def_to_return.name}' was replaced or modified.", level="INFO")

            elif params.get("from_zone_override") == Zone.DISCARD.name and source_card_definition: 
                card_to_save: Optional[Card] = None
                if event_context and isinstance(event_context.get('moving_card_definition'), Card):
                    card_to_save = event_context.get('moving_card_definition')
                elif source_card_definition: 
                    card_to_save = source_card_definition
                
                if card_to_save and card_to_save in gs.discard_pile:
                    gs.discard_pile.remove(card_to_save)
                    gs.hand.append(card_to_save)
                    gs.add_log_entry(f"Returned '{card_to_save.name}' from discard to hand (special replacement action).")
                else:
                    gs.add_log_entry(f"Action RETURN_THIS_CARD_TO_HAND (from discard special): '{source_card_definition.name if source_card_definition else 'Card'}' not found in discard or invalid params.", level="WARNING")
            else:
                gs.add_log_entry(f"Action RETURN_THIS_CARD_TO_HAND failed: Source card instance not in play or invalid parameters. Source: {source_card_instance.card_definition.name if source_card_instance else 'None'}", level="WARNING")

        elif action_type == EffectActionType.MILL_DECK:
            amount = params.get("amount", 0)
            if isinstance(amount, int) and amount > 0:
                milled_cards_names = []
                for _ in range(amount):
                    if gs.deck:
                        milled_card = gs.deck.pop(0)
                        gs.discard_pile.append(milled_card)
                        milled_cards_names.append(milled_card.name)
                    else:
                        gs.add_log_entry("Cannot mill card: Deck is empty.", level="WARNING")
                        break
                if milled_cards_names:
                    gs.add_log_entry(f"Milled {len(milled_cards_names)} card(s): {', '.join(milled_cards_names)}. Moved to discard.")
            else:
                gs.add_log_entry(f"Action MILL_DECK: Invalid amount {amount}.", level="WARNING")

        elif action_type == EffectActionType.EXILE_CARD_FROM_ZONE:
            from_zone_name = params.get("zone", "DECK").upper() 
            count = params.get("count", 1)
            card_id_to_exile = params.get("card_id") 

            from_zone_list: Optional[List[Card]] = None
            zone_enum_member = None
            try:
                zone_enum_member = Zone[from_zone_name]
                if zone_enum_member == Zone.DECK: from_zone_list = gs.deck
                elif zone_enum_member == Zone.HAND: from_zone_list = gs.hand
                elif zone_enum_member == Zone.DISCARD: from_zone_list = gs.discard_pile
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
                        found_card = None
                        for i, card in enumerate(from_zone_list):
                            if card.card_id == card_id_to_exile:
                                found_card = from_zone_list.pop(i)
                                break
                        if found_card:
                            card_to_exile = found_card
                        else:
                            gs.add_log_entry(f"Card ID '{card_id_to_exile}' not found in {from_zone_name} to exile.", level="WARNING")
                            break 
                    else: 
                        if zone_enum_member == Zone.DECK: 
                            card_to_exile = from_zone_list.pop(0)
                        elif zone_enum_member == Zone.HAND: 
                            card_to_exile = from_zone_list.pop(random.randrange(len(from_zone_list)))
                    
                    if card_to_exile:
                        gs.exile_zone.append(card_to_exile)
                        exiled_card_names.append(card_to_exile.name)
                        exiled_count +=1
                        if zone_enum_member == Zone.HAND:
                            self.trigger_effects(EffectTriggerType.WHEN_CARD_EXILED_FROM_HAND, source_card_definition_for_trigger=card_to_exile, event_context={'exiled_card_definition': card_to_exile})

                if exiled_count > 0:
                    gs.add_log_entry(f"Exiled {exiled_count} card(s) from {from_zone_name}: {', '.join(exiled_card_names)}.")
            else:
                 gs.add_log_entry(f"Action EXILE_CARD_FROM_ZONE: Zone '{from_zone_name}' not supported for this simple exile.", level="WARNING")
        
        elif action_type == EffectActionType.RETURN_CARD_FROM_ZONE_TO_ZONE:
            card_id_to_return = params.get("card_to_return_id") 
            from_zone_name = params.get("from_zone", "DISCARD").upper()
            to_zone_name = params.get("to_zone", "HAND").upper() # String from params
            
            card_to_move: Optional[Card] = None
            
            if card_id_to_return == "FIRST_MEMORY":
                card_to_move = gs.first_memory_card_definition
            elif card_id_to_return: 
                if event_context and isinstance(event_context.get('chosen_card_definition'), Card): 
                    chosen_card = event_context.get('chosen_card_definition')
                    if chosen_card.card_id == card_id_to_return:
                        card_to_move = chosen_card 
                if not card_to_move: 
                    temp_source_list_for_search: List[Card] = []
                    try: 
                        if Zone[from_zone_name] == Zone.DISCARD: temp_source_list_for_search = gs.discard_pile
                        elif Zone[from_zone_name] == Zone.EXILE: temp_source_list_for_search = gs.exile_zone
                    except KeyError: pass
                    for card_in_src_zone in temp_source_list_for_search:
                        if card_in_src_zone.card_id == card_id_to_return:
                            card_to_move = card_in_src_zone
                            break 
                    if not card_to_move:
                        gs.add_log_entry(f"RETURN_CARD_FROM_ZONE_TO_ZONE: Card ID '{card_id_to_return}' not found through event_context or direct search of {from_zone_name}.", level="WARNING")
            
            source_list: Optional[List[Card]] = None
            try:
                from_zone_enum = Zone[from_zone_name] 
                if from_zone_enum == Zone.DISCARD: source_list = gs.discard_pile
                elif from_zone_enum == Zone.EXILE: source_list = gs.exile_zone
            except KeyError:
                gs.add_log_entry(f"RETURN_CARD_FROM_ZONE_TO_ZONE: Invalid from_zone name '{from_zone_name}'.", level="ERROR")
                return

            if card_to_move and source_list is not None:
                if card_to_move in source_list:
                    try:
                        source_list.remove(card_to_move) 
                        
                        fm_updated_zone: Optional[Zone] = None
                        log_destination_name = to_zone_name # Use the original string for logging "DECK_TOP"

                        if to_zone_name == "HAND":
                            gs.hand.append(card_to_move)
                            fm_updated_zone = Zone.HAND
                        elif to_zone_name == "DECK_TOP":
                            gs.deck.insert(0, card_to_move)
                            fm_updated_zone = Zone.DECK 
                        elif to_zone_name == "DISCARD":
                            gs.discard_pile.append(card_to_move)
                            fm_updated_zone = Zone.DISCARD
                        elif to_zone_name == "EXILE":
                            gs.exile_zone.append(card_to_move)
                            fm_updated_zone = Zone.EXILE
                        # TODO: Add "IN_PLAY"
                        else:
                            gs.add_log_entry(f"RETURN_CARD_FROM_ZONE_TO_ZONE: Destination zone string '{to_zone_name}' not supported. Card '{card_to_move.name}' removed from source but not placed.", level="WARNING")
                            # Card is effectively lost if destination is not recognized after removal.
                            # Consider re-adding to source_list or a default 'lost' zone if this is undesirable.
                        
                        if fm_updated_zone: # Log successful move only if a known destination type was handled
                             gs.add_log_entry(f"Moved '{card_to_move.name}' from {from_zone_name} to {log_destination_name}.", level="INFO")
                             if card_to_move == gs.first_memory_card_definition:
                                gs.first_memory_current_zone = fm_updated_zone
                        
                    except ValueError:
                         gs.add_log_entry(f"RETURN_CARD_FROM_ZONE_TO_ZONE: ValueError during remove of '{card_to_move.name}' from {from_zone_name} even after 'in' check. This is unexpected.", level="ERROR")
                else:
                    gs.add_log_entry(f"RETURN_CARD_FROM_ZONE_TO_ZONE: Card '{card_to_move.name}' (ID: {card_to_move.card_id}) identified, but Python's 'in' operator reported it as NOT in the source_list ({from_zone_name}). Contents: {[c.name + ' (' + c.card_id + ')' for c in source_list]}", level="ERROR")
            
            elif not card_to_move: 
                gs.add_log_entry(f"RETURN_CARD_FROM_ZONE_TO_ZONE: No card was identified to move based on params: card_id_to_return='{card_id_to_return}', event_context='{event_context}'.", level="WARNING")
            elif source_list is None: 
                # This should have been caught by from_zone_enum KeyError already if from_zone_name was invalid
                gs.add_log_entry(f"RETURN_CARD_FROM_ZONE_TO_ZONE: Source list for '{from_zone_name}' could not be determined (is None).", level="WARNING")
        
        else:
            gs.add_log_entry(f"EffectEngine: Action type '{action_type.name}' execution not yet implemented. Action skipped.", level="WARNING")

    def trigger_effects(self,
                        trigger_type: EffectTriggerType,
                        source_card_instance_for_trigger: Optional['CardInPlay'] = None, 
                        source_card_definition_for_trigger: Optional['Card'] = None,  
                        event_context: Optional[Dict[str, Any]] = None):
        gs = self.game_state
        
        candidate_effects_to_resolve: List[Tuple[EffectLogic, Optional[CardInPlay], Optional[Card]]] = []
        processed_effect_ids_for_this_trigger = set() 

        card_directly_involved_instance = source_card_instance_for_trigger
        card_directly_involved_definition = source_card_definition_for_trigger

        if not card_directly_involved_instance and event_context: 
            card_directly_involved_instance = event_context.get('sacrificed_card_instance') or \
                                              event_context.get('entered_card_instance') or \
                                              event_context.get('left_play_card_instance') or \
                                              event_context.get('target_card_instance') 
        if not card_directly_involved_definition and event_context:
            if isinstance(event_context.get('drawn_card_definition'), Card):
                card_directly_involved_definition = event_context.get('drawn_card_definition')
            elif isinstance(event_context.get('exiled_card_definition'), Card):
                card_directly_involved_definition = event_context.get('exiled_card_definition')
            elif isinstance(event_context.get('sacrificed_card_definition'), Card): 
                card_directly_involved_definition = event_context.get('sacrificed_card_definition')


        if card_directly_involved_instance:
            for i, el in enumerate(card_directly_involved_instance.card_definition.effect_logic_list):
                effect_unique_id = f"{card_directly_involved_instance.instance_id}_effect_{i}"
                if el.trigger == trigger_type.name and effect_unique_id not in processed_effect_ids_for_this_trigger:
                    candidate_effects_to_resolve.append(
                        (el, card_directly_involved_instance, None)
                    )
                    processed_effect_ids_for_this_trigger.add(effect_unique_id)
        elif card_directly_involved_definition: 
             for i, el in enumerate(card_directly_involved_definition.effect_logic_list):
                effect_unique_id = f"{card_directly_involved_definition.card_id}_effect_{i}" 
                if el.trigger == trigger_type.name and effect_unique_id not in processed_effect_ids_for_this_trigger:
                    candidate_effects_to_resolve.append(
                        (el, None, card_directly_involved_definition)
                    )
                    processed_effect_ids_for_this_trigger.add(effect_unique_id)
        
        event_card_instance_from_context: Optional['CardInPlay'] = None
        event_card_definition_from_context: Optional['Card'] = None

        if event_context: 
            event_card_instance_from_context = event_context.get('entered_card_instance') or \
                                               event_context.get('left_play_card_instance') or \
                                               event_context.get('sacrificed_card_instance') or \
                                               event_context.get('target_card_instance')
            if not event_card_instance_from_context: 
                 event_card_definition_from_context = event_context.get('drawn_card_definition') or \
                                                      event_context.get('exiled_card_definition') or \
                                                      event_context.get('sacrificed_card_definition')


        for listener_card_in_play in list(gs.cards_in_play.values()):
            if listener_card_in_play == card_directly_involved_instance and trigger_type in [
                EffectTriggerType.ON_PLAY, EffectTriggerType.ON_LEAVE_PLAY, 
                EffectTriggerType.ON_SACRIFICE_THIS_CARD, EffectTriggerType.ON_ENTER_PLAY_FROM_DISCARD,
                EffectTriggerType.WHEN_COUNTER_REACHES_THRESHOLD 
            ]:
                continue

            for i, el in enumerate(listener_card_in_play.card_definition.effect_logic_list):
                effect_unique_id = f"{listener_card_in_play.instance_id}_effect_{i}"
                if el.trigger == trigger_type.name and effect_unique_id not in processed_effect_ids_for_this_trigger:
                    is_other_card_event = trigger_type in [
                        EffectTriggerType.WHEN_OTHER_CARD_ENTERS_PLAY, 
                        EffectTriggerType.WHEN_OTHER_CARD_LEAVES_PLAY
                    ]
                    if is_other_card_event:
                        if (event_card_instance_from_context and listener_card_in_play == event_card_instance_from_context) or \
                           (event_card_definition_from_context and listener_card_in_play.card_definition == event_card_definition_from_context):
                            continue 

                    if trigger_type == EffectTriggerType.WHEN_YOU_SACRIFICE_TOY:
                        sacrificed_instance = event_context.get('sacrificed_toy_instance') or event_context.get('sacrificed_card_instance') if event_context else None
                        if sacrificed_instance and listener_card_in_play == sacrificed_instance:
                            continue 

                    candidate_effects_to_resolve.append((el, listener_card_in_play, None))
                    processed_effect_ids_for_this_trigger.add(effect_unique_id)
        
        if not candidate_effects_to_resolve:
            return

        gs.add_log_entry(f"EffectEngine: Found {len(candidate_effects_to_resolve)} candidate effect(s) for trigger '{trigger_type.name}'. Processing...", level="DEBUG")
        
        for effect_logic_to_resolve, src_instance, src_definition in candidate_effects_to_resolve:
            if gs.game_over: break 
            self.resolve_effect_logic(effect_logic_to_resolve, src_instance, src_definition, 
                                      targets=event_context.get('targets') if event_context else None, 
                                      event_context=event_context) 

if __name__ == '__main__':
    print("EffectEngine module: Contains logic for resolving card and game effects.")