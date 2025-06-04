# src/tuck_in_terrors_sim/game_logic/nightmare_creep.py
# Manages application of Nightmare Creep effects per objective

from typing import TYPE_CHECKING, Optional, List, Dict, Any

if TYPE_CHECKING: # To avoid circular imports for type hinting
    from .game_state import GameState, PlayerState
    from .effect_engine import EffectEngine
    from ..game_elements.objective import ObjectiveLogicComponent

from ..game_elements.card import Effect, EffectAction # Use Effect and EffectAction
from ..game_elements.enums import EffectTriggerType, EffectActionType # For parsing and defaults
# Import helper functions from data_loaders to parse components of an Effect
from ..game_elements.data_loaders import _parse_effect_action, _parse_condition, _parse_cost

class NightmareCreepModule:
    def __init__(self, game_state: 'GameState', effect_engine: 'EffectEngine'):
        self.game_state = game_state
        self.effect_engine = effect_engine

    def _parse_json_data_to_effect_object(self, effect_json_data: Dict[str, Any], turn_number: int) -> Optional[Effect]:
        """
        Converts a dictionary (expected to be structured like an Effect definition from JSON)
        into a fully parsed Effect object.
        This mirrors part of the logic in data_loaders._parse_effect.
        """
        gs = self.game_state # For logging
        if not isinstance(effect_json_data, dict):
            gs.add_log_entry("Nightmare Creep 'effect_to_apply' data is not a dictionary.", level="ERROR")
            return None

        # Determine Trigger
        trigger_str = effect_json_data.get("trigger", EffectTriggerType.WHEN_NIGHTMARE_CREEP_APPLIES_TO_PLAYER.name)
        try:
            trigger_enum = EffectTriggerType[trigger_str.upper()]
        except KeyError:
            gs.add_log_entry(f"Invalid trigger type '{trigger_str}' in NC effect data. Defaulting.", level="WARNING")
            trigger_enum = EffectTriggerType.ON_NIGHTMARE_CREEP_RESOLUTION_FOR_TURN
        
        # Parse Actions
        actions_json_list = effect_json_data.get("actions", [])
        parsed_actions_list: List[EffectAction] = []
        if isinstance(actions_json_list, list):
            for i, action_data_dict in enumerate(actions_json_list):
                try:
                    # _parse_effect_action expects a dict and returns an EffectAction object
                    parsed_actions_list.append(_parse_effect_action(action_data_dict))
                except ValueError as e:
                    gs.add_log_entry(f"Error parsing action {i} in NC effect: {e}", level="ERROR")
                    return None 
        else:
            gs.add_log_entry(f"NC effect 'actions' data is not a list: {actions_json_list}", level="ERROR")
            return None

        # Parse Condition
        condition_json_dict = effect_json_data.get("condition")
        parsed_condition_obj = _parse_condition(condition_json_dict) if condition_json_dict else None
        
        # Parse Cost (though NC effects usually don't have player-paid costs)
        cost_json_dict = effect_json_data.get("cost")
        parsed_cost_obj = _parse_cost(cost_json_dict) if cost_json_dict else None

        # Generate other Effect fields
        effect_id_str = effect_json_data.get("effect_id", f"NC_Effect_T{turn_number}_{trigger_enum.name}")
        description_str = effect_json_data.get("description", "Nightmare Creep custom effect.")
        source_card_id_str = "OBJECTIVE_NIGHTMARE_CREEP" # Generic source identifier

        return Effect(
            effect_id=effect_id_str,
            trigger=trigger_enum,
            actions=parsed_actions_list,
            condition=parsed_condition_obj,
            cost=parsed_cost_obj,
            description=description_str,
            source_card_id=source_card_id_str
            # is_replacement_effect and temporary_effect_data default to False/None
        )

    def apply_nightmare_creep_for_current_turn(self) -> bool:
        gs = self.game_state
        objective = gs.current_objective
        current_turn = gs.current_turn
        active_player = gs.get_active_player_state()

        if not active_player:
            gs.add_log_entry("Cannot apply Nightmare Creep: No active player.", level="ERROR")
            return False

        if gs.nightmare_creep_skipped_this_turn:
            gs.add_log_entry(f"Nightmare Creep skipped for Turn {current_turn} due to a card effect.", level="INFO")
            gs.nightmare_creep_skipped_this_turn = False 
            return False

        if not objective.nightmare_creep_effect: # This is List[ObjectiveLogicComponent]
            return False 

        active_nc_logic_component: Optional['ObjectiveLogicComponent'] = None
        for nc_comp in objective.nightmare_creep_effect:
            effective_turn = nc_comp.params.get("effective_on_turn")
            if effective_turn is not None and isinstance(effective_turn, int) and current_turn >= effective_turn:
                active_nc_logic_component = nc_comp 
        
        if not active_nc_logic_component:
            return False 

        gs.add_log_entry(f"Nightmare Creep active for Turn {current_turn}. Objective Component: {active_nc_logic_component.component_type}", level="INFO")
        gs.nightmare_creep_effect_applied_this_turn = True

        # This is the dictionary that defines the actual Effect (trigger, actions, etc.)
        effect_definition_data = active_nc_logic_component.params.get("effect_to_apply")
        if not effect_definition_data:
            gs.add_log_entry(f"No 'effect_to_apply' data in NC component: {active_nc_logic_component.component_type}", level="WARNING")
            return True 

        # Parse the effect_definition_data dictionary into a full Effect object
        parsed_effect_object = self._parse_json_data_to_effect_object(effect_definition_data, current_turn)

        if parsed_effect_object:
            gs.add_log_entry(f"Resolving Nightmare Creep effect: {parsed_effect_object.description or parsed_effect_object.effect_id}", level="DEBUG")
            
            self.effect_engine.resolve_effect( # Calling the new method in EffectEngine
                effect=parsed_effect_object,
                game_state=gs,
                player=active_player, 
                source_card_instance=None, 
                triggering_event_context={"source": "NIGHTMARE_CREEP", "turn": current_turn}
            )
            return True 
        else:
            gs.add_log_entry(f"Failed to parse NC effect data for component {active_nc_logic_component.component_type}.", level="ERROR")
            return True 

if __name__ == '__main__':
    print("NightmareCreepModule: Applies objective-specific Nightmare Creep effects.")