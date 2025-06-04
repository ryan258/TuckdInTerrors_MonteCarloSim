# src/tuck_in_terrors_sim/game_elements/data_loaders.py
import json
import os
from typing import List, Dict, Any, Optional

# Assuming card.py, objective.py, and enums.py are now the corrected versions
from .card import Card, Effect, EffectAction, Cost, Toy, Ritual, Spell 
from .objective import ObjectiveCard, ObjectiveLogicComponent 
from .enums import (CardType, EffectTriggerType, EffectActionType, ResourceType,
                    EffectConditionType, Zone, CardSubType, EffectActivationCostType,
                    PlayerChoiceType)

# --- Configuration ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_CARDS_FILE = os.path.join(BASE_DIR, "..", "..", "..", "data", "cards.json")
DEFAULT_OBJECTIVES_FILE = os.path.join(BASE_DIR, "..", "..", "..", "data", "objectives.json")

# --- Helper Functions for Parsing ---

def _parse_cost(cost_data: Optional[Dict[str, Any]]) -> Optional[Cost]:
    # This uses Cost.from_dict which should handle parsing from string keys
    return Cost.from_dict(cost_data)


def _parse_effect_action(action_data: Dict[str, Any]) -> EffectAction:
    action_type_str = action_data.get("action_type")
    if not action_type_str:
        raise ValueError("Effect action data must have an 'action_type'.")
    try:
        # Ensure action_type_str is uppercase before enum lookup
        effect_action_type = EffectActionType[action_type_str.upper()]
    except KeyError:
        raise ValueError(f"Unknown EffectActionType: {action_type_str}")

    params = action_data.get("params", {}).copy()

    sub_action_keys = [
        "on_true_actions", "on_false_actions",
        "on_yes_actions", "on_no_actions",
        "on_selection_actions", "sub_actions"
    ]

    # Recursively parse sub-actions for relevant action types
    if effect_action_type in [EffectActionType.CONDITIONAL_EFFECT, EffectActionType.PLAYER_CHOICE]:
        for key in sub_action_keys:
            if key in params and isinstance(params[key], list):
                try:
                    # Ensure each item in the list is a dict before parsing
                    params[key] = [_parse_effect_action(sa_data) for sa_data in params[key] if isinstance(sa_data, dict)]
                except ValueError as e:
                    raise ValueError(f"Error parsing sub-action under '{key}' for '{action_type_str}': {e}")
        
        # Handle actions_map if its values are lists of actions
        if "actions_map" in params and isinstance(params["actions_map"], dict):
            parsed_actions_map = {}
            for map_key, map_value in params["actions_map"].items():
                if isinstance(map_value, list):
                    try:
                        parsed_actions_map[map_key] = [_parse_effect_action(sa_data) for sa_data in map_value if isinstance(sa_data, dict)]
                    except ValueError as e:
                         raise ValueError(f"Error parsing sub-action in 'actions_map' under key '{map_key}' for '{action_type_str}': {e}")
                else:
                    # If map values are not lists of actions, keep them as is
                    parsed_actions_map[map_key] = map_value 
            params["actions_map"] = parsed_actions_map

    # Helper to resolve enum strings within params, robustly handling non-string values or KeyErrors
    def _resolve_param_enum(param_value: Any, enum_class: type) -> Any:
        if isinstance(param_value, str):
            try:
                return enum_class[param_value.upper()]
            except KeyError:
                # If it's a string but not a valid enum member, keep it as string.
                # The consuming logic in EffectEngine might handle specific string values
                # or raise a more specific error if an enum is strictly required there.
                # print(f"Warning: Invalid enum string '{param_value}' for {enum_class.__name__} in action params. Kept as string.")
                pass 
        return param_value # Return original value if not string or if string is not a matching enum key

    # Parse enums within params where applicable
    for param_key, param_value in params.items():
        if param_key in ["zone", "from_zone", "to_zone"]:
            params[param_key] = _resolve_param_enum(param_value, Zone)
        elif param_key == "card_type" and "target_card_filter" not in params : # Avoid double parsing if in target_card_filter
            params[param_key] = _resolve_param_enum(param_value, CardType)
        elif param_key == "resource_type":
            params[param_key] = _resolve_param_enum(param_value, ResourceType)
        elif param_key == "choice_type": # For PLAYER_CHOICE
            params[param_key] = _resolve_param_enum(param_value, PlayerChoiceType)
        elif param_key == "trigger_type": # For effects that might specify a sub-trigger
             params[param_key] = _resolve_param_enum(param_value, EffectTriggerType)


    # Parse target_card_filter specifically
    target_card_filter = params.get("target_card_filter")
    if target_card_filter and isinstance(target_card_filter, dict):
        parsed_filter = {}
        for k, v_val in target_card_filter.items(): # Renamed v_str to v_val as it might not be string
            if k == "card_type":
                parsed_filter[k] = _resolve_param_enum(v_val, CardType)
            elif k == "zone":
                parsed_filter[k] = _resolve_param_enum(v_val, Zone)
            elif k == "subtype": 
                parsed_filter[k] = _resolve_param_enum(v_val, CardSubType)
            else: # For other filter keys like 'name', 'is_tapped', 'controller' etc.
                parsed_filter[k] = v_val
        params["target_card_filter"] = parsed_filter
        
    return EffectAction(
        action_type=effect_action_type,
        params=params,
        description=action_data.get("description", "")
    )

def _parse_condition(condition_data: Optional[Dict[str, Any]]) -> Optional[Dict[EffectConditionType, Any]]:
    if not condition_data:
        return None
    
    parsed_condition_dict = {}
    condition_type_str = condition_data.get("condition_type")
    if not condition_type_str:
        raise ValueError("Condition data must have a 'condition_type'.")
    try:
        # Ensure condition_type_str is uppercase for enum lookup
        condition_type_enum = EffectConditionType[condition_type_str.upper()]
    except KeyError:
        raise ValueError(f"Unknown EffectConditionType: {condition_type_str}")

    params = condition_data.get("params", {}).copy()

    def _resolve_param_enum(param_value: Any, enum_class: type) -> Any:
        if isinstance(param_value, str):
            try:
                return enum_class[param_value.upper()]
            except KeyError:
                # print(f"Warning: Invalid enum string '{param_value}' for {enum_class.__name__} in condition params. Kept as string.")
                pass
        return param_value
        
    # Parse specific enum values within params if needed
    if "resource_type" in params:
        params["resource_type"] = _resolve_param_enum(params["resource_type"], ResourceType)
    if "card_type" in params: # For conditions like EVENT_CARD_IS_TYPE
        params["card_type"] = _resolve_param_enum(params["card_type"], CardType)
    if "zone" in params: # For conditions like IS_MOVING_FROM_ZONE/TO_ZONE
        params["zone"] = _resolve_param_enum(params["zone"], Zone)

    parsed_condition_dict[condition_type_enum] = params
    return parsed_condition_dict


def _parse_effect(effect_data: Dict[str, Any], card_name_context: str, card_id_context: str) -> Effect:
    trigger_str = effect_data.get("trigger")
    if not trigger_str:
        raise ValueError(f"Effect for card '{card_name_context}' must have a 'trigger'.")
    try:
        trigger_enum = EffectTriggerType[trigger_str.upper()]
    except KeyError:
        raise ValueError(f"Unknown EffectTriggerType: {trigger_str} for card '{card_name_context}'.")

    raw_actions_list = effect_data.get("actions", [])
    if not isinstance(raw_actions_list, list):
        raise ValueError(f"Actions for effect '{trigger_str}' on card '{card_name_context}' must be a list.")
        
    parsed_actions: List[EffectAction] = []
    for i, action_dict in enumerate(raw_actions_list):
        if not isinstance(action_dict, dict):
            raise ValueError(f"Action data (idx {i}) for '{trigger_str}' on '{card_name_context}' must be a dictionary.")
        try:
            parsed_actions.append(_parse_effect_action(action_dict))
        except ValueError as e: # Catch potential errors from _parse_effect_action
            raise ValueError(f"Error parsing action (idx {i}) for effect '{trigger_str}' on card '{card_name_context}': {e}")

    # Parse condition and cost
    parsed_condition = _parse_condition(effect_data.get("condition")) # Returns Optional[Dict]
    parsed_cost = _parse_cost(effect_data.get("cost")) # Returns Optional[Cost]
    
    # Generate a somewhat unique effect_id if not provided.
    # Hash of actions can be unstable if action dict order changes, but better than just index.
    effect_id_str = effect_data.get("effect_id", f"{card_id_context}_{trigger_enum.name}_{len(parsed_actions)}_{sum(ord(c) for c in json.dumps(raw_actions_list)) % 10000}")


    return Effect(
        effect_id=effect_id_str,
        trigger=trigger_enum,
        actions=parsed_actions,
        condition=parsed_condition,
        description=effect_data.get("description", ""),
        cost=parsed_cost,
        is_replacement_effect=effect_data.get("is_replacement_effect", False),
        temporary_effect_data=effect_data.get("temporary_effect_data"), # Pass as is
        source_card_id=card_id_context
    )

def load_cards(file_path: str = DEFAULT_CARDS_FILE) -> List[Card]:
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Card data file not found: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        try:
            all_card_data_list = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Error decoding JSON from {file_path}: {e}")

    if not isinstance(all_card_data_list, list):
        raise ValueError(f"Card data in {file_path} is not a list.")

    cards_list: List[Card] = []
    for card_data_dict in all_card_data_list:
        if not isinstance(card_data_dict, dict):
            raise ValueError("Each card entry in the JSON file must be a dictionary.")

        card_name = card_data_dict.get("name")
        if not card_name:
            raise ValueError("Card data must have a 'name'.")
        
        # *** UPDATED TO READ "card_type" and "cost" from JSON ***
        card_type_json_val = card_data_dict.get("card_type") 
        if not card_type_json_val: # Check if the key exists and has a non-empty value
            raise ValueError(f"Card '{card_name}' must have a 'card_type' field in JSON with a non-empty value.")
        
        # Handle potential composite types like "TOY — ↻ ✦" by taking the first part
        main_type_str = str(card_type_json_val).split("—")[0].strip()
        try:
            card_type_enum_val = CardType[main_type_str.upper()]
        except KeyError:
            # If it's not in CardType enum, it's an invalid type
            raise ValueError(f"Unknown CardType derived: '{main_type_str}' (from JSON value: '{card_type_json_val}') for card '{card_name}'.")

        cost_from_json = card_data_dict.get("cost", 0) 
        if not isinstance(cost_from_json, int):
            # Attempt to convert if it's a string representing an int
            try:
                cost_from_json = int(cost_from_json)
            except (ValueError, TypeError):
                print(f"Warning: 'cost' for card '{card_name}' is not a valid integer ('{cost_from_json}'). Defaulting to 0.")
                cost_from_json = 0
            
        card_id_val = card_data_dict.get("card_id", card_name.lower().replace(" ", "_").replace("'", ""))
            
        effects_json_list = card_data_dict.get("effects", [])
        parsed_effects_list = []
        if isinstance(effects_json_list, list):
            for effect_data_dict in effects_json_list:
                if not isinstance(effect_data_dict, dict):
                     raise ValueError(f"Effect entry for card '{card_name}' must be a dictionary.")
                try:
                    # Pass card_name and card_id_val for context
                    parsed_effects_list.append(_parse_effect(effect_data_dict, card_name, card_id_val))
                except ValueError as e: # Catch errors from _parse_effect
                    raise ValueError(f"Error parsing effect for card '{card_name}': {e}")
        elif effects_json_list is not None : 
            raise ValueError(f"Effects for '{card_name}' must be a list if provided.")
        
        subtypes_str_list = card_data_dict.get("subtypes", [])
        parsed_subtypes_list = []
        if isinstance(subtypes_str_list, list):
            for st_str in subtypes_str_list:
                try:
                    if isinstance(st_str, str) and st_str: # Ensure it's a non-empty string
                        parsed_subtypes_list.append(CardSubType[st_str.upper()])
                    elif st_str: # If not string but not None/empty, warn
                        print(f"Warning: Non-string or empty subtype value '{st_str}' for card '{card_name}'. Will be ignored.")
                except KeyError:
                    print(f"Warning: Unknown subtype '{st_str}' for card '{card_name}'. Will be ignored.")
        elif isinstance(subtypes_str_list, str) and subtypes_str_list: 
             try:
                parsed_subtypes_list.append(CardSubType[subtypes_str_list.upper()])
             except KeyError:
                print(f"Warning: Unknown subtype '{subtypes_str_list}' for card '{card_name}'. Will be ignored.")
        
        # Card class expects 'type' and 'cost_mana' as keyword arguments
        card_constructor_args = {
            "card_id": card_id_val,
            "name": card_name,
            "type": card_type_enum_val,      
            "cost_mana": cost_from_json,     
            "text": card_data_dict.get("text", ""),
            "flavor_text": card_data_dict.get("flavor_text", ""),
            "subtypes": parsed_subtypes_list,
            "effects": parsed_effects_list,
            "power": card_data_dict.get("power"), 
            "is_first_memory_potential": card_data_dict.get("is_first_memory_potential", card_type_enum_val == CardType.TOY),
            "art_elements": card_data_dict.get("art_elements")
        }
        
        # Instantiate the correct Card subclass
        if card_type_enum_val == CardType.TOY:
            cards_list.append(Toy(**card_constructor_args))
        elif card_type_enum_val == CardType.RITUAL:
            cards_list.append(Ritual(**card_constructor_args))
        elif card_type_enum_val == CardType.SPELL:
            cards_list.append(Spell(**card_constructor_args))
        else: 
            # This case should ideally not be reached if card_type_enum_val is validated against CardType enum
            # However, if CardType enum is extended and this logic isn't, it might fall here.
            print(f"Warning: Card '{card_name}' has unhandled CardType '{card_type_enum_val.name}'. Creating generic Card object.")
            cards_list.append(Card(**card_constructor_args)) 
            
    return cards_list

def _parse_objective_logic_component_from_data(data: Optional[Dict[str, Any]]) -> Optional[ObjectiveLogicComponent]:
    if not data or not isinstance(data, dict):
        return None
    component_data = data.copy() 
    if "action_type" in component_data and "component_type" not in component_data:
        component_data["component_type"] = component_data.pop("action_type")
    # Further parsing of component_data["params"] for enums might be needed here
    # if ObjectiveLogicComponent is used for complex game rule definitions.
    # For now, ObjectiveLogicComponent.from_dict handles basic structure.
    return ObjectiveLogicComponent.from_dict(component_data)

def load_objectives(file_path: str = DEFAULT_OBJECTIVES_FILE) -> List[ObjectiveCard]:
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Objective data file not found: {file_path}")

    with open(file_path, 'r', encoding='utf-8') as f:
        try:
            all_objective_data_list = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Error decoding JSON from {file_path}: {e}")

    if not isinstance(all_objective_data_list, list):
        raise ValueError(f"Objective data in {file_path} is not a list.")

    objectives_list: List[ObjectiveCard] = []
    for obj_data_dict in all_objective_data_list:
        if not isinstance(obj_data_dict, dict):
            raise ValueError("Each objective entry in JSON must be a dictionary.")

        # Use "title" if present, fallback to "name", then to "Unnamed Objective"
        title_val = obj_data_dict.get("title", obj_data_dict.get("name", "Unnamed Objective")) 
        obj_id_val = obj_data_dict.get("objective_id", title_val.lower().replace(" ", "_").replace("'", ""))

        nc_effects_raw_list = obj_data_dict.get("nightmare_creep_effects", [])
        parsed_nc_components: List[ObjectiveLogicComponent] = []
        if isinstance(nc_effects_raw_list, list):
            for i, nc_item_dict in enumerate(nc_effects_raw_list):
                if isinstance(nc_item_dict, dict):
                    parsed_comp = _parse_objective_logic_component_from_data(nc_item_dict)
                    if parsed_comp:
                        parsed_nc_components.append(parsed_comp)
                    else:
                        # Log warning if a component could not be parsed
                        print(f"Warning: Could not parse nightmare_creep_effect item {i} for objective '{title_val}'. Data: {nc_item_dict}")
                else: # If item in list is not a dictionary
                    raise ValueError(f"Nightmare Creep effect item {i} for objective '{title_val}' is not a dictionary.")
        elif nc_effects_raw_list is not None: 
             raise ValueError(f"Nightmare Creep effects for objective '{title_val}' must be a list if provided.")
            
        primary_wc_obj = _parse_objective_logic_component_from_data(obj_data_dict.get("primary_win_condition"))
        alt_wc_obj = _parse_objective_logic_component_from_data(obj_data_dict.get("alternative_win_condition"))
        fm_setup_obj = _parse_objective_logic_component_from_data(obj_data_dict.get("first_memory_setup"))
        setup_instr_obj = _parse_objective_logic_component_from_data(obj_data_dict.get("setup_instructions"))
        
        # first_memory_ongoing_effects is expected to be List[Dict[str, Any]] by ObjectiveCard.
        # If these dicts represent Effect definitions, they would need parsing via _parse_effect.
        # For now, pass as is, assuming consuming logic handles raw dicts or it's purely descriptive.
        fm_ongoing_effects_list = obj_data_dict.get("first_memory_ongoing_effects", [])


        objective_instance = ObjectiveCard(
            objective_id=obj_id_val,
            title=title_val, 
            difficulty=obj_data_dict.get("difficulty", "Normal"), 
            flavor_text=obj_data_dict.get("flavor_text", obj_data_dict.get("description", "")), 
            primary_win_condition=primary_wc_obj,
            alternative_win_condition=alt_wc_obj,
            first_memory_setup=fm_setup_obj,
            first_memory_ongoing_effects=fm_ongoing_effects_list, 
            nightmare_creep_effect=parsed_nc_components, 
            setup_instructions=setup_instr_obj,
            nightfall_turn=obj_data_dict.get("nightfall_turn", 10), 
            card_rotation=obj_data_dict.get("card_rotation", {"banned": [], "featured": []}),
            special_rules_text=obj_data_dict.get("special_rules_text", [])
        )
        objectives_list.append(objective_instance)
    return objectives_list


class GameData:
    """Container for all loaded game data."""
    def __init__(self, cards: List[Card], objectives: List[ObjectiveCard]):
        self.cards = cards
        self.objectives = objectives
        self.cards_by_id: Dict[str, Card] = {card.card_id: card for card in cards}
        self.objectives_by_id: Dict[str, ObjectiveCard] = {obj.objective_id: obj for obj in objectives}

    def get_card_by_id(self, card_id: str) -> Optional[Card]:
        return self.cards_by_id.get(card_id)

    def get_objective_by_id(self, objective_id: str) -> Optional[ObjectiveCard]:
        return self.objectives_by_id.get(objective_id)

def load_all_game_data(cards_file_path: str = DEFAULT_CARDS_FILE, 
                         objectives_file_path: str = DEFAULT_OBJECTIVES_FILE) -> GameData:
    cards = load_cards(cards_file_path)
    objectives = load_objectives(objectives_file_path)
    return GameData(cards, objectives)


if __name__ == '__main__':
    try:
        print("Attempting to load game data from default JSON file locations...")
        # For direct testing, ensure paths are correct relative to this script if not using project root
        # Example: explicit paths if data folder is sibling to src
        # project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        # cards_json = os.path.join(project_root, "data", "cards.json")
        # objectives_json = os.path.join(project_root, "data", "objectives.json")
        # game_data = load_all_game_data(cards_json, objectives_json)
        
        game_data = load_all_game_data() # Uses DEFAULT paths based on this file's location
        print(f"Successfully loaded {len(game_data.cards)} cards and {len(game_data.objectives)} objectives.")
        
        # Example: Print details of the first loaded card if any
        if game_data.cards:
            print("\nSample Card:")
            sample_card = game_data.cards[0]
            print(f"  Name: {sample_card.name} (ID: {sample_card.card_id})")
            print(f"  Type: {sample_card.type.name}, Cost: {sample_card.cost_mana}")
            print(f"  Text: {sample_card.text}")
            if sample_card.effects:
                print(f"  Effects ({len(sample_card.effects)}):")
                for i, effect_obj in enumerate(sample_card.effects): # Changed variable name to effect_obj
                    print(f"    Effect {i+1}: Trigger: {effect_obj.trigger.name}, ID: {effect_obj.effect_id}")

        # Example: Print details of the first loaded objective if any
        if game_data.objectives:
            print("\nSample Objective:")
            sample_obj = game_data.objectives[0]
            print(f"  Title: {sample_obj.title} (ID: {sample_obj.objective_id})")
            print(f"  Difficulty: {sample_obj.difficulty}")
            print(f"  Nightfall: Turn {sample_obj.nightfall_turn}")
            if sample_obj.primary_win_condition:
                 print(f"  Primary Win Con: {sample_obj.primary_win_condition.component_type} - {sample_obj.primary_win_condition.description}")

    except FileNotFoundError as e:
        print(f"Error: Data file not found. {e}")
        print("Please ensure 'data/cards.json' and 'data/objectives.json' exist relative to the project structure.")
    except ValueError as e:
        print(f"Error: Problem parsing data. {e}")
    except Exception as e: # Catch any other unexpected errors during loading
        import traceback
        print(f"An unexpected error occurred during data loading: {e}")
        traceback.print_exc()