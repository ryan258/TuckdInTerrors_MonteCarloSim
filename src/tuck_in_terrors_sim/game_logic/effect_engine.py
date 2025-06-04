# src/tuck_in_terrors_sim/game_logic/effect_engine.py
from typing import TYPE_CHECKING, List, Dict, Any, Optional

from ..game_elements.card import Card, Effect, EffectAction, CardInstance 
# CardType is now added to this import list:
from ..game_elements.enums import (EffectActionType, EffectConditionType, Zone, ResourceType,
                                   PlayerChoiceType, CardType) 
from .game_state import PlayerState 
from ..ai.ai_player_base import AIPlayerBase


if TYPE_CHECKING:
    from .game_state import GameState


class EffectEngine:
    def __init__(self, game_state_ref: 'GameState'): 
        self.game_state_ref = game_state_ref 

    def check_condition(self, 
                        condition_data: Optional[Dict[EffectConditionType, Any]], 
                        player: PlayerState, 
                        card_instance: Optional[CardInstance], 
                        game_state: 'GameState', # Explicitly pass game_state
                        event_context: Optional[Dict[str, Any]] = None
                        ) -> bool:
        if condition_data is None:
            return True 

        if not condition_data or not isinstance(condition_data, dict) or not list(condition_data.items()):
             game_state.add_log_entry(f"Warning: Malformed condition_data: {condition_data}", "ENGINE_DEBUG")
             return False 

        condition_type, params = list(condition_data.items())[0]
        
        if event_context is None:
            event_context = {}

        # Ensure enums from params are resolved if they are strings
        # This is important if data_loaders didn't fully parse enums deep in params dicts
        def _resolve_param_enum(param_value: Any, enum_class: type) -> Any:
            if isinstance(param_value, str):
                try:
                    return enum_class[param_value.upper()]
                except KeyError:
                    game_state.add_log_entry(f"Invalid enum string '{param_value}' for {enum_class.__name__} in condition params.", "WARNING")
                    return None # Or raise error, or return original string
            return param_value # Assume already correct type or not an enum string

        if condition_type == EffectConditionType.PLAYER_HAS_RESOURCE:
            resource_type_param = params.get("resource_type")
            resource_type = _resolve_param_enum(resource_type_param, ResourceType)
            required_amount = params.get("amount", 1)
            if not isinstance(resource_type, ResourceType):
                game_state.add_log_entry(f"Invalid resource_type '{resource_type_param}' in PLAYER_HAS_RESOURCE condition.", "ERROR")
                return False
            if resource_type == ResourceType.MANA: return player.mana >= required_amount
            if resource_type == ResourceType.SPIRIT: return player.spirit_tokens >= required_amount
            if resource_type == ResourceType.MEMORY: return player.memory_tokens >= required_amount
            return False
        
        elif condition_type == EffectConditionType.DECK_SIZE_LE:
            required_size = params.get("count", 0)
            return len(player.zones[Zone.DECK]) <= required_size

        elif condition_type == EffectConditionType.IS_FIRST_MEMORY_IN_PLAY:
            fm_instance = game_state.get_first_memory_instance()
            return fm_instance is not None and fm_instance.current_zone == Zone.IN_PLAY
        
        elif condition_type == EffectConditionType.IS_FIRST_MEMORY_IN_DISCARD:
            fm_instance = game_state.get_first_memory_instance()
            if fm_instance and fm_instance.current_zone == Zone.DISCARD:
                 owner_player_state = game_state.get_player_state(fm_instance.owner_id)
                 if owner_player_state and fm_instance in owner_player_state.zones[Zone.DISCARD]:
                     return True
            return False

        elif condition_type == EffectConditionType.CARD_IS_TAPPED:
            return card_instance.is_tapped if card_instance else False
            
        elif condition_type == EffectConditionType.EVENT_CARD_IS_TYPE: # Line 75 is likely around here
            event_card_inst = event_context.get("card_instance") 
            target_type_param = params.get("card_type")
            target_type_enum = _resolve_param_enum(target_type_param, CardType) # Use CardType here
            if isinstance(event_card_inst, CardInstance) and isinstance(target_type_enum, CardType):
                return event_card_inst.definition.type == target_type_enum
            return False
        
        elif condition_type == EffectConditionType.IS_MOVING_FROM_ZONE:
            target_zone_param = params.get("zone") 
            target_zone_enum = _resolve_param_enum(target_zone_param, Zone)
            moving_card_origin_zone_param = event_context.get("from_zone")
            moving_card_origin_zone_enum = _resolve_param_enum(moving_card_origin_zone_param, Zone)
            if isinstance(target_zone_enum, Zone) and isinstance(moving_card_origin_zone_enum, Zone):
                return moving_card_origin_zone_enum == target_zone_enum
            return False

        elif condition_type == EffectConditionType.IS_MOVING_TO_ZONE:
            target_zone_param = params.get("zone")
            target_zone_enum = _resolve_param_enum(target_zone_param, Zone)
            moving_card_destination_zone_param = event_context.get("to_zone")
            moving_card_destination_zone_enum = _resolve_param_enum(moving_card_destination_zone_param, Zone)
            if isinstance(target_zone_enum, Zone) and isinstance(moving_card_destination_zone_enum, Zone):
                return moving_card_destination_zone_enum == target_zone_enum
            return False
            
        # elif condition_type == EffectConditionType.CARD_HAS_BEEN_IN_PLAY_FOR_X_TURNS_GE:
        #     if not card_instance or card_instance.turn_entered_play is None: return False
        #     turns_in_play_required = params.get("turns", 0)
        #     return (game_state.current_turn - card_instance.turn_entered_play) >= turns_in_play_required

        elif condition_type == EffectConditionType.HAS_COUNTER_TYPE_VALUE_GE:
            if not card_instance: return False
            counter_type_str = params.get("counter_type")
            threshold = params.get("value", 1)
            return card_instance.get_counter(str(counter_type_str)) >= threshold if counter_type_str else False

        game_state.add_log_entry(f"Warning: Condition type {condition_type.name} not fully implemented. Defaulting to False.", "ENGINE_DEBUG")
        return False

    def resolve_effect(self, 
                       effect: Effect, 
                       game_state: 'GameState', 
                       player: PlayerState, 
                       source_card_instance: Optional[CardInstance] = None,
                       triggering_event_context: Optional[Dict[str, Any]] = None
                       ) -> List[EffectAction]:
        all_generated_actions: List[EffectAction] = []

        if not self.check_condition(effect.condition, player, source_card_instance, game_state, triggering_event_context):
            game_state.add_log_entry(f"Condition for E'{effect.effect_id}'({effect.source_card_id or 'N/A'}) not met for P{player.player_id}.", "EFFECT_DEBUG")
            return all_generated_actions

        game_state.add_log_entry(f"Resolving E'{effect.effect_id}'({effect.description or 'No desc.'}) for P{player.player_id}.", "EFFECT_INFO")

        controller_id_for_context = source_card_instance.controller_id if source_card_instance else player.player_id

        effect_context = {
            "player_id": controller_id_for_context, 
            "target_player_id": player.player_id, 
            "source_card_instance_id": source_card_instance.instance_id if source_card_instance else None,
            "source_card_definition_id": source_card_instance.definition.card_id if source_card_instance else effect.source_card_id,
            "effect_id": effect.effect_id,
            "trigger_type": effect.trigger,
            "triggering_event_context": triggering_event_context or {}
        }

        for action in effect.actions:
            target_player_for_action = game_state.get_player_state(effect_context["target_player_id"])
            if not target_player_for_action: 
                game_state.add_log_entry(f"Error: Target player for action not found: {effect_context['target_player_id']}", "ERROR")
                continue

            generated_actions = self._execute_action(
                action=action, game_state=game_state, player=target_player_for_action,
                effect_context=effect_context, card_instance=source_card_instance
            )
            all_generated_actions.extend(generated_actions)
        
        return all_generated_actions

    def _execute_action(self, 
                        action: EffectAction, 
                        game_state: 'GameState', 
                        player: PlayerState, 
                        effect_context: Dict[str, Any], 
                        card_instance: Optional[CardInstance] = None
                        ) -> List[EffectAction]: 
        action_type = action.action_type
        params = action.params # These params should have enums resolved by data_loaders or EffectAction creation
        pending_actions: List[EffectAction] = [] 
        
        game_state.add_log_entry(f"Exec: {action_type.name} for P{player.player_id}, Params: {params}", "ACTION_DETAIL")

        if action_type == EffectActionType.DRAW_CARDS:
            count = params.get("count", 1)
            player.draw_cards(count, game_state)
        
        elif action_type == EffectActionType.ADD_MANA:
            amount = params.get("amount", 1)
            player.mana += amount
            game_state.add_log_entry(f"P{player.player_id} gains {amount} mana. Total: {player.mana}")

        elif action_type == EffectActionType.CREATE_SPIRIT_TOKENS:
            count = params.get("count", 1)
            player.spirit_tokens += count
            game_state.add_log_entry(f"P{player.player_id} creates {count} Spirit(s). Total: {player.spirit_tokens}")

        elif action_type == EffectActionType.CREATE_MEMORY_TOKENS:
            count = params.get("count", 1)
            player.memory_tokens += count
            game_state.add_log_entry(f"P{player.player_id} creates {count} Memory(s). Total: {player.memory_tokens}")
            
        elif action_type == EffectActionType.MILL_CARDS:
            count = params.get("count", 1)
            player.mill_deck(count, game_state)

        elif action_type == EffectActionType.PLACE_COUNTER_ON_CARD:
            target_card_id_val = params.get("target_card_id", effect_context.get("chosen_target_id")) 
            if not target_card_id_val and card_instance:
                 target_card_id_val = card_instance.instance_id
            
            target_card_inst = game_state.get_card_instance(str(target_card_id_val)) if target_card_id_val else None

            if target_card_inst:
                counter_type = params.get("counter_type", "generic")
                amount = params.get("amount", 1)
                target_card_inst.add_counter(str(counter_type), amount) # Ensure counter_type is string
                game_state.add_log_entry(f"Placed {amount} '{counter_type}' on {target_card_inst.definition.name} ({target_card_inst.instance_id}).")
            else:
                game_state.add_log_entry(f"PLACE_COUNTER_ON_CARD: Target card ({target_card_id_val}) not found.", "WARNING")
        
        elif action_type == EffectActionType.RETURN_THIS_CARD_TO_HAND:
            if card_instance:
                game_state.move_card_zone(card_instance, Zone.HAND, card_instance.owner_id)
            else:
                game_state.add_log_entry("RETURN_THIS_CARD_TO_HAND failed: no source card_instance.", "ERROR")
        
        elif action_type == EffectActionType.RETURN_CARD_FROM_ZONE_TO_ZONE:
            card_to_move_id = params.get("card_id", effect_context.get("chosen_target_id"))
            card_to_move_instance = None
            if str(card_to_move_id).lower() in ["self", "this"] and card_instance:
                card_to_move_instance = card_instance
            elif card_to_move_id:
                card_to_move_instance = game_state.get_card_instance(str(card_to_move_id))

            if card_to_move_instance:
                from_zone_enum = params.get("from_zone") 
                to_zone_enum = params.get("to_zone")     
                target_player_id_for_zone_param = params.get("target_player_id")
                # Ensure target_player_id is int if provided, else default to owner.
                target_player_id_for_zone = int(target_player_id_for_zone_param) if target_player_id_for_zone_param is not None else card_to_move_instance.owner_id


                if not isinstance(from_zone_enum, Zone) or not isinstance(to_zone_enum, Zone):
                    game_state.add_log_entry(f"Invalid zones for RETURN_CARD_FROM_ZONE_TO_ZONE: {from_zone_enum} to {to_zone_enum}", "ERROR")
                    return pending_actions

                if card_to_move_instance.current_zone == from_zone_enum:
                    game_state.move_card_zone(card_to_move_instance, to_zone_enum, target_player_id_for_zone)
                else:
                    game_state.add_log_entry(f"Card {card_to_move_instance.definition.name} not in {from_zone_enum.name}. Actual: {card_to_move_instance.current_zone.name}", "WARNING")
            else:
                game_state.add_log_entry(f"Could not find card '{card_to_move_id}' for RETURN_CARD_FROM_ZONE_TO_ZONE.", "WARNING")
        
        elif action_type == EffectActionType.EXILE_CARD_FROM_ZONE:
            card_to_exile_id = params.get("card_id", effect_context.get("chosen_target_id"))
            from_zone_enum = params.get("from_zone") # Should be pre-parsed Zone enum
            
            if not isinstance(from_zone_enum, Zone):
                game_state.add_log_entry(f"Invalid from_zone for EXILE_CARD_FROM_ZONE: {from_zone_enum}", "ERROR")
                return pending_actions

            card_to_exile_instance = game_state.get_card_instance(str(card_to_exile_id)) if card_to_exile_id else None

            if card_to_exile_instance:
                if card_to_exile_instance.current_zone == from_zone_enum:
                    game_state.move_card_zone(card_to_exile_instance, Zone.EXILE, card_to_exile_instance.owner_id)
                else:
                    game_state.add_log_entry(f"Card {card_to_exile_instance.definition.name} not in {from_zone_enum.name} to be exiled.", "WARNING")
            else: 
                count_to_exile = params.get("count", 1)
                if from_zone_enum == Zone.DECK and player: 
                    for _ in range(count_to_exile):
                        if player.zones[Zone.DECK]: # Check if deck has cards
                            exiled_instance = player.zones[Zone.DECK].pop(0) # Remove from PlayerState's deck
                            game_state.move_card_zone(exiled_instance, Zone.EXILE, exiled_instance.owner_id) # GameState handles global logic
                        else:
                            game_state.add_log_entry(f"P{player.player_id} deck empty, cannot exile from deck.", "INFO")
                            break
                else:
                    game_state.add_log_entry(f"EXILE_CARD_FROM_ZONE needs target or better filter. CardID: {card_to_exile_id}, Zone: {from_zone_enum}", "WARNING")

        elif action_type == EffectActionType.SACRIFICE_RESOURCE:
            resource_param = params.get("resource_type")
            amount = params.get("count", 1)
            resource_type_enum = resource_param
            if isinstance(resource_param, str): 
                try: resource_type_enum = ResourceType[resource_param.upper()]
                except KeyError: game_state.add_log_entry(f"Invalid resource_type str '{resource_param}' for SACRIFICE_RESOURCE", "ERROR"); return pending_actions
            
            if not isinstance(resource_type_enum, ResourceType):
                 game_state.add_log_entry(f"Invalid resource_type obj '{resource_type_enum}' for SACRIFICE_RESOURCE", "ERROR"); return pending_actions

            if resource_type_enum == ResourceType.SPIRIT:
                if player.spirit_tokens >= amount: player.spirit_tokens -= amount; game_state.add_log_entry(f"P{player.player_id} sacrificed {amount} Spirit(s). Left: {player.spirit_tokens}")
                else: game_state.add_log_entry(f"P{player.player_id} lacks {amount} Spirit(s) to sacrifice (has {player.spirit_tokens}).", "WARNING")
            else: game_state.add_log_entry(f"Cannot sacrifice unimplemented resource: {resource_type_enum.name}", "WARNING")

        elif action_type == EffectActionType.CONDITIONAL_EFFECT:
            condition_data = params.get("condition") 
            condition_met = self.check_condition(condition_data, player, card_instance, game_state, effect_context.get("triggering_event_context"))
            actions_to_run: List[EffectAction] = params.get("on_true_actions", []) if condition_met else params.get("on_false_actions", [])
            
            for sub_action in actions_to_run: 
                pending_actions.extend(self._execute_action(
                    sub_action, game_state, player, effect_context, card_instance))
            return pending_actions 

        elif action_type == EffectActionType.PLAYER_CHOICE:
            choice_type_param = params.get("choice_type")
            choice_type_enum = choice_type_param
            if isinstance(choice_type_param, str): 
                 try: choice_type_enum = PlayerChoiceType[choice_type_param.upper()]
                 except KeyError: game_state.add_log_entry(f"Invalid PlayerChoiceType str '{choice_type_param}'", "ERROR"); return []
            
            if not isinstance(choice_type_enum, PlayerChoiceType):
                game_state.add_log_entry(f"Error: Invalid PlayerChoiceType obj '{choice_type_enum}'", "ERROR"); return []

            choice_player_id = effect_context.get("player_id", game_state.active_player_id) 
            choice_player_agent = game_state.get_player_agent(choice_player_id)
            
            if not choice_player_agent:
                game_state.add_log_entry(f"Error: No AI agent for P{choice_player_id} for choice.", "ERROR"); return []

            ai_params_for_choice = {k: v for k, v in params.items() if k not in ["on_yes_actions", "on_no_actions", "on_selection_actions", "actions_map", "choice_type", "on_discard_actions", "on_sacrifice_actions"]} # Added more keys to exclude
            
            choice_context_for_ai = {
                "choice_type": choice_type_enum,
                "prompt_text": params.get("prompt_text", "Make a choice:"),
                "source_card_instance_id": card_instance.instance_id if card_instance else None,
                "effect_id": effect_context.get("effect_id"),
                "options": params.get("options"), 
                **ai_params_for_choice 
            }
            
            chosen_value = choice_player_agent.make_choice(game_state, choice_context_for_ai)
            game_state.add_log_entry(f"P{choice_player_id} chose '{chosen_value}' for {choice_type_enum.name}.", "CHOICE_DEBUG")

            sub_actions_to_run: List[EffectAction] = []
            current_effect_context = effect_context.copy() 

            if choice_type_enum == PlayerChoiceType.CHOOSE_YES_NO:
                sub_actions_to_run = params.get("on_yes_actions", []) if chosen_value else params.get("on_no_actions", [])
            
            elif choice_type_enum == PlayerChoiceType.DISCARD_CARD_OR_SACRIFICE_SPIRIT:
                # RandomAI returns True for "discard" (first option like "yes"), False for "sacrifice" (second option like "no")
                # This needs alignment with how options are presented to AI and how AI returns choice.
                # For now, assuming `on_yes_actions` = discard, `on_no_actions` = sacrifice
                if chosen_value == "discard" or chosen_value is True: # Accommodate AI returning string or bool
                     sub_actions_to_run = params.get("on_discard_actions", params.get("on_yes_actions", [])) 
                elif chosen_value == "sacrifice" or chosen_value is False:
                     sub_actions_to_run = params.get("on_sacrifice_actions", params.get("on_no_actions", []))
                else:
                     game_state.add_log_entry(f"Unhandled choice val '{chosen_value}' for DISCARD_CARD_OR_SACRIFICE_SPIRIT.", "WARNING")

            else:
                game_state.add_log_entry(f"Warning: PlayerChoiceType {choice_type_enum.name} outcome not fully implemented.", "WARNING")

            for sub_action in sub_actions_to_run: 
                pending_actions.extend(self._execute_action(
                    sub_action, game_state, player, current_effect_context, card_instance))
            return pending_actions 
            
        else:
            game_state.add_log_entry(f"Warning: Action type {action_type.name} not implemented in _execute_action.", "WARNING")

        return pending_actions