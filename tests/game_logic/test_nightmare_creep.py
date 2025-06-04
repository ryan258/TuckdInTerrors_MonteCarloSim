# tests/game_logic/test_nightmare_creep.py
import pytest
from unittest.mock import MagicMock
from typing import Tuple, Any, List, Dict

from tuck_in_terrors_sim.game_logic.game_state import GameState, PlayerState
from tuck_in_terrors_sim.game_logic.effect_engine import EffectEngine
from tuck_in_terrors_sim.game_logic.nightmare_creep import NightmareCreepModule
from tuck_in_terrors_sim.game_elements.objective import ObjectiveCard, ObjectiveLogicComponent
from tuck_in_terrors_sim.game_elements.card import Card # For all_card_definitions type hint
from tuck_in_terrors_sim.game_logic.action_resolver import ActionResolver # For fixture typing
from tuck_in_terrors_sim.game_logic.turn_manager import TurnManager # For fixture typing
from tuck_in_terrors_sim.game_logic.win_loss_checker import WinLossChecker # For fixture typing
from tuck_in_terrors_sim.game_logic.game_setup import DEFAULT_PLAYER_ID


# Assuming initialized_game_environment is defined in conftest.py and returns 6 items now
# Tuple[GameState, ActionResolver, EffectEngine, TurnManager, NightmareCreepModule, WinLossChecker]

class TestNightmareCreepModule:

    def test_apply_nightmare_creep_not_active_turn_too_early(
        self,
        initialized_game_environment: Tuple[GameState, ActionResolver, EffectEngine, TurnManager, NightmareCreepModule, WinLossChecker]
    ):
        game_state, _, _, _, nightmare_module, _ = initialized_game_environment
        game_state.current_turn = 1 # Objective "The First Night" NC starts turn 4 (as per objectives.json)
        
        # Make sure the objective has NC configured to start later
        if game_state.current_objective.nightmare_creep_effect:
            # This assumes the first NC component has the earliest effective_on_turn
            first_nc_comp = game_state.current_objective.nightmare_creep_effect[0]
            if isinstance(first_nc_comp.params.get("effective_on_turn"), int) and first_nc_comp.params.get("effective_on_turn", 0) > 1:
                applied = nightmare_module.apply_nightmare_creep_for_current_turn()
                assert applied is False
                assert game_state.nightmare_creep_effect_applied_this_turn is False
            else:
                pytest.skip("Skipping test: Objective's NC effect is active on turn 1 or not configured as expected for this test.")
        else:
            pytest.skip("Skipping test: Objective has no Nightmare Creep effects defined.")


    def test_apply_nightmare_creep_active_applies_effect(
        self,
        initialized_game_environment: Tuple[GameState, ActionResolver, EffectEngine, TurnManager, NightmareCreepModule, WinLossChecker]
    ):
        game_state, _, effect_engine, _, nightmare_module, _ = initialized_game_environment
        player = game_state.get_active_player_state()
        assert player is not None

        game_state.current_turn = 4 # Assuming NC effect is active on turn 4 for "The First Night"
        
        # Mock the effect engine's resolve_effect to check it's called
        effect_engine.resolve_effect = MagicMock()
        
        # Ensure the objective has an NC effect for turn 4
        nc_effect_data_found = False
        if game_state.current_objective.nightmare_creep_effect:
            for comp in game_state.current_objective.nightmare_creep_effect:
                if comp.params.get("effective_on_turn") == 4 and comp.params.get("effect_to_apply"):
                    nc_effect_data_found = True
                    break
        if not nc_effect_data_found:
            pytest.skip("Skipping test: Objective does not have an NC effect defined for turn 4 with 'effect_to_apply'.")

        applied = nightmare_module.apply_nightmare_creep_for_current_turn()
        
        assert applied is True
        assert game_state.nightmare_creep_effect_applied_this_turn is True
        effect_engine.resolve_effect.assert_called_once()
        # Further assertions could check the arguments passed to resolve_effect

    def test_apply_nightmare_creep_no_nc_defined_in_objective(
        self,
        initialized_game_environment: Tuple[GameState, ActionResolver, EffectEngine, TurnManager, NightmareCreepModule, WinLossChecker]
    ):
        game_state, _, _, _, nightmare_module, _ = initialized_game_environment
        game_state.current_objective.nightmare_creep_effect = [] # Ensure no NC effects
        
        applied = nightmare_module.apply_nightmare_creep_for_current_turn()
        assert applied is False
        assert game_state.nightmare_creep_effect_applied_this_turn is False

    def test_apply_nightmare_creep_malformed_effect_data(
        self,
        initialized_game_environment: Tuple[GameState, ActionResolver, EffectEngine, TurnManager, NightmareCreepModule, WinLossChecker]
    ):
        game_state, _, effect_engine, _, nightmare_module, _ = initialized_game_environment
        game_state.current_turn = 4
        
        # Create a malformed NC component
        malformed_nc_component = ObjectiveLogicComponent(
            component_type="STANDARD_NC_PENALTY",
            params={"effective_on_turn": 4, "effect_to_apply": "not_a_dict"} # Malformed part
        )
        game_state.current_objective.nightmare_creep_effect = [malformed_nc_component]
        effect_engine.resolve_effect = MagicMock() # Mock to ensure it's not called if parsing fails

        applied = nightmare_module.apply_nightmare_creep_for_current_turn()
        
        assert applied is True # Module considers NC "applied" even if parsing within fails, to set flag
        assert game_state.nightmare_creep_effect_applied_this_turn is True
        effect_engine.resolve_effect.assert_not_called()
        assert any("Failed to parse Nightmare Creep effect data" in log for log in game_state.game_log if "ERROR" in log)