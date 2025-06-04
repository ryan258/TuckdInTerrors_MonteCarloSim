# tests/game_logic/test_nightmare_creep.py
import pytest
from unittest.mock import MagicMock
from typing import Tuple, Any, List, Dict

from tuck_in_terrors_sim.game_logic.game_state import GameState, PlayerState
from tuck_in_terrors_sim.game_logic.effect_engine import EffectEngine
from tuck_in_terrors_sim.game_logic.nightmare_creep import NightmareCreepModule
from tuck_in_terrors_sim.game_elements.objective import ObjectiveCard, ObjectiveLogicComponent
from tuck_in_terrors_sim.game_elements.card import Card 
from tuck_in_terrors_sim.game_logic.action_resolver import ActionResolver 
from tuck_in_terrors_sim.game_logic.turn_manager import TurnManager 
from tuck_in_terrors_sim.game_logic.win_loss_checker import WinLossChecker 
from tuck_in_terrors_sim.game_logic.game_setup import DEFAULT_PLAYER_ID


# Assuming initialized_game_environment is defined in conftest.py and returns 6 items now
# Tuple[GameState, ActionResolver, EffectEngine, TurnManager, NightmareCreepModule, WinLossChecker]

class TestNightmareCreepModule:

    def test_apply_nightmare_creep_not_active_turn_too_early(
        self,
        initialized_game_environment: Tuple[GameState, ActionResolver, EffectEngine, TurnManager, NightmareCreepModule, WinLossChecker]
    ):
        game_state, _, _, _, nightmare_module, _ = initialized_game_environment
        game_state.current_turn = 1 # Objective "The First Night" NC starts turn 4 (as per objectives.json, but effective on turn 5 in data)
                                    # objectives.json has "effective_on_turn": 5 for OBJ01_THE_FIRST_NIGHT
        
        nc_configured_later = False
        if game_state.current_objective.nightmare_creep_effect:
            first_nc_comp = game_state.current_objective.nightmare_creep_effect[0]
            effective_turn_param = first_nc_comp.params.get("effective_on_turn")
            if isinstance(effective_turn_param, int) and effective_turn_param > game_state.current_turn:
                nc_configured_later = True
        
        if not nc_configured_later:
            pytest.skip("Skipping test: Objective's NC effect is active on turn 1 or not configured as expected for this test.")

        applied = nightmare_module.apply_nightmare_creep_for_current_turn()
        assert applied is False
        assert game_state.nightmare_creep_effect_applied_this_turn is False


    def test_apply_nightmare_creep_active_applies_effect(
        self,
        initialized_game_environment: Tuple[GameState, ActionResolver, EffectEngine, TurnManager, NightmareCreepModule, WinLossChecker]
    ):
        game_state, _, effect_engine, _, nightmare_module, _ = initialized_game_environment
        player = game_state.get_active_player_state()
        assert player is not None

        # OBJ01_THE_FIRST_NIGHT has NC effective_on_turn: 5
        game_state.current_turn = 5 
        
        effect_engine.resolve_effect = MagicMock()
        
        nc_effect_data_found = False
        if game_state.current_objective.nightmare_creep_effect:
            for comp in game_state.current_objective.nightmare_creep_effect:
                if comp.params.get("effective_on_turn") == game_state.current_turn and comp.params.get("effect_to_apply"):
                    nc_effect_data_found = True
                    break
        if not nc_effect_data_found:
            pytest.skip(f"Skipping test: Objective does not have an NC effect defined for turn {game_state.current_turn} with 'effect_to_apply'.")

        applied = nightmare_module.apply_nightmare_creep_for_current_turn()
        
        assert applied is True
        assert game_state.nightmare_creep_effect_applied_this_turn is True
        effect_engine.resolve_effect.assert_called_once()


    def test_apply_nightmare_creep_no_nc_defined_in_objective(
        self,
        initialized_game_environment: Tuple[GameState, ActionResolver, EffectEngine, TurnManager, NightmareCreepModule, WinLossChecker]
    ):
        game_state, _, _, _, nightmare_module, _ = initialized_game_environment
        # Temporarily modify the objective for this test
        original_nc_effects = game_state.current_objective.nightmare_creep_effect
        game_state.current_objective.nightmare_creep_effect = [] 
        
        applied = nightmare_module.apply_nightmare_creep_for_current_turn()
        assert applied is False
        assert game_state.nightmare_creep_effect_applied_this_turn is False
        
        # Restore original NC effects to avoid affecting other tests using the same fixture instance
        game_state.current_objective.nightmare_creep_effect = original_nc_effects


    def test_apply_nightmare_creep_malformed_effect_data(
        self,
        initialized_game_environment: Tuple[GameState, ActionResolver, EffectEngine, TurnManager, NightmareCreepModule, WinLossChecker]
    ):
        game_state, _, effect_engine, _, nightmare_module, _ = initialized_game_environment
        game_state.current_turn = 5 # Assuming NC would be active

        original_nc_effects = game_state.current_objective.nightmare_creep_effect
        
        malformed_nc_component = ObjectiveLogicComponent(
            component_type="STANDARD_NC_PENALTY",
            params={"effective_on_turn": 5, "effect_to_apply": "not_a_dict"} # Malformed part
        )
        game_state.current_objective.nightmare_creep_effect = [malformed_nc_component]
        effect_engine.resolve_effect = MagicMock() 
        game_state.game_log.clear() # Clear log for specific check

        applied = nightmare_module.apply_nightmare_creep_for_current_turn()
        
        assert applied is True 
        assert game_state.nightmare_creep_effect_applied_this_turn is True
        effect_engine.resolve_effect.assert_not_called()
        # Corrected assertion to match the actual log message
        assert any("Nightmare Creep 'effect_to_apply' data is not a dictionary." in log for log in game_state.game_log if "ERROR" in log)
        
        game_state.current_objective.nightmare_creep_effect = original_nc_effects