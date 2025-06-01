# src/tuck_in_terrors_sim/game_logic/nightmare_creep.py
# Manages application of Nightmare Creep effects per objective

from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING: # To avoid circular imports for type hinting
    from .game_state import GameState
    from .effect_engine import EffectEngine
    from ..game_elements.objective import ObjectiveLogicComponent

# We need EffectLogic to parse the "effect_to_apply" structure from the objective's JSON
from ..game_elements.card import EffectLogic
from ..game_elements.enums import EffectTriggerType # For the conceptual trigger of NC effects

class NightmareCreepModule:
    def __init__(self, game_state: 'GameState', effect_engine: 'EffectEngine'):
        self.game_state = game_state
        self.effect_engine = effect_engine

    def apply_nightmare_creep_for_current_turn(self):
        """
        Checks if Nightmare Creep should apply on the current turn based on the objective's
        definition and, if so, applies its effects using the EffectEngine.
        This function will be called by the TurnManager.
        """
        gs = self.game_state
        objective = gs.current_objective
        current_turn = gs.current_turn

        if not objective.nightmare_creep_effect:
            # gs.add_log_entry("No Nightmare Creep defined for this objective.", level="DEBUG") # Handled by TurnManager check
            return False # Indicate NC didn't apply

        active_nc_component: Optional['ObjectiveLogicComponent'] = None
        for nc_component in objective.nightmare_creep_effect:
            effective_turn = nc_component.params.get("effective_on_turn")
            if effective_turn is not None and current_turn >= effective_turn:
                active_nc_component = nc_component
                # Assuming the list in objectives.json is ordered, or the last match for current turn is taken.
                # For more complex escalation (e.g. different effect on turn 5 vs turn 7), this logic might need adjustment.
                # For now, if multiple are valid, the last one in the list that meets turn condition will be used.
                # This is fine if each component defines a new phase replacing previous ones.
                
        if not active_nc_component:
            # gs.add_log_entry(f"Nightmare Creep not active on Turn {current_turn} for this objective phase.", level="DEBUG") # Handled by TurnManager check
            return False # Indicate NC didn't apply

        gs.add_log_entry(f"Nightmare Creep is active for Turn {current_turn}. Applying objective's NC effects.", level="INFO")
        gs.nightmare_creep_effect_applied_this_turn = True # Mark that the NC process for the objective has started

        effect_to_apply_data = active_nc_component.params.get("effect_to_apply")

        if not effect_to_apply_data or not isinstance(effect_to_apply_data, dict):
            gs.add_log_entry("Nightmare Creep effect_to_apply data is missing or malformed in objective definition.", level="ERROR")
            return True # NC was active, but effect could not be applied due to data error

        # Ensure a trigger is present for EffectLogic.from_dict if it's mandatory.
        # The implicit trigger for the NC effect is the NC event itself.
        if "trigger" not in effect_to_apply_data:
            effect_to_apply_data["trigger"] = EffectTriggerType.ON_NIGHTMARE_CREEP_RESOLUTION_FOR_TURN.name
        
        try:
            nc_effect_logic = EffectLogic.from_dict(effect_to_apply_data)
            gs.add_log_entry(f"Resolving Nightmare Creep effect: {nc_effect_logic.description or nc_effect_logic.trigger}", level="DEBUG")
            
            # The "source" of a Nightmare Creep effect is the Objective/Game itself.
            self.effect_engine.resolve_effect_logic(
                effect_logic=nc_effect_logic,
                source_card_definition=None, 
                source_card_instance=None
                # `targets` would be relevant if NC effects had explicit targets beyond the player/game state
            )
            return True # NC applied
        except Exception as e:
            gs.add_log_entry(f"Error creating or resolving Nightmare Creep EffectLogic: {e}", level="ERROR")
            return True # NC was active, but effect resolution failed

if __name__ == '__main__':
    print("NightmareCreepModule: Applies objective-specific Nightmare Creep effects.")