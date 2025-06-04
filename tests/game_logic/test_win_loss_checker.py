# tests/game_logic/test_win_loss_checker.py
import pytest
from typing import Tuple, Dict, Any, List 

from tuck_in_terrors_sim.game_logic.game_state import GameState, PlayerState
from tuck_in_terrors_sim.game_logic.win_loss_checker import WinLossChecker
from tuck_in_terrors_sim.game_elements.objective import ObjectiveCard, ObjectiveLogicComponent
from tuck_in_terrors_sim.game_elements.data_loaders import GameData 
from tuck_in_terrors_sim.game_elements.card import Card, CardInstance, Toy 
from tuck_in_terrors_sim.game_elements.enums import Zone, CardType, CardSubType 
from tuck_in_terrors_sim.game_logic.action_resolver import ActionResolver 
from tuck_in_terrors_sim.game_logic.effect_engine import EffectEngine 
from tuck_in_terrors_sim.game_logic.turn_manager import TurnManager 
from tuck_in_terrors_sim.game_logic.nightmare_creep import NightmareCreepModule
from tuck_in_terrors_sim.game_logic.game_setup import DEFAULT_PLAYER_ID


# Assuming initialized_game_environment is defined in conftest.py and returns 6 items:
# GameState, ActionResolver, EffectEngine, TurnManager, NightmareCreepModule, WinLossChecker

class TestWinLossChecker:

    def test_nightfall_loss_condition(
        self, 
        initialized_game_environment: Tuple[GameState, ActionResolver, EffectEngine, TurnManager, NightmareCreepModule, WinLossChecker]
    ):
        game_state, _, _, _, _, win_loss_checker = initialized_game_environment 
        # For OBJ01_THE_FIRST_NIGHT, nightfall_turn is 4.
        # So, turn 5 should be a loss.
        game_state.current_turn = game_state.current_objective.nightfall_turn + 1 
        
        assert win_loss_checker.check_all_conditions() is True
        assert game_state.game_over is True
        assert game_state.win_status == "LOSS_NIGHTFALL"

    def test_game_already_over(
        self, 
        initialized_game_environment: Tuple[GameState, ActionResolver, EffectEngine, TurnManager, NightmareCreepModule, WinLossChecker]
    ):
        game_state, _, _, _, _, win_loss_checker = initialized_game_environment 
        game_state.game_over = True
        game_state.win_status = "PRIMARY_WIN" 
        
        assert win_loss_checker.check_all_conditions() is True 
        assert game_state.win_status == "PRIMARY_WIN" 

    def test_first_night_primary_win_met(
        self, 
        initialized_game_environment: Tuple[GameState, ActionResolver, EffectEngine, TurnManager, NightmareCreepModule, WinLossChecker]
    ):
        game_state, _, _, _, _, win_loss_checker = initialized_game_environment 
        player = game_state.get_active_player_state()
        assert player is not None
        
        # Ensure "The First Night" (OBJ01_THE_FIRST_NIGHT) is the active objective.
        # Primary win con for OBJ01: PLAY_X_DIFFERENT_TOYS_AND_CREATE_Y_SPIRITS (4 toys, 4 spirits)
        
        game_state.objective_progress["distinct_toys_played_ids"] = {"T1", "T2", "T3", "T4"}
        game_state.objective_progress["spirits_created_total_game"] = 4
        
        assert win_loss_checker.check_all_conditions() is True
        assert game_state.game_over is True
        assert game_state.win_status == "PRIMARY_WIN"

    @pytest.fixture
    def whisper_wake_game_env(self, game_data: GameData) -> Tuple[GameState, WinLossChecker]:
        """Sets up a GameState with OBJ02_WHISPER_WAKE for WinLossChecker tests."""
        from tuck_in_terrors_sim.game_logic.game_setup import initialize_new_game 

        objective = game_data.get_objective_by_id("OBJ02_WHISPER_WAKE")
        if not objective:
            pytest.fail("Objective OBJ02_WHISPER_WAKE not found for test setup.")
        
        gs = initialize_new_game(objective, game_data.cards_by_id) 
        checker = WinLossChecker(gs)
        return gs, checker

    def test_whisper_wake_primary_win_met(self, whisper_wake_game_env: Tuple[GameState, WinLossChecker]):
        game_state, win_loss_checker = whisper_wake_game_env
        player = game_state.get_active_player_state()
        assert player is not None
        
        # For "The Whisper Before Wake" (OBJ02_WHISPER_WAKE):
        # Primary win con in objectives.json is CAST_SPELL_WITH_STORM_COUNT
        # "spell_card_id_or_name": "TCSPL_FLUFFSTORM_PLACEHOLDER",
        # "min_storm_count": 5,
        
        assert game_state.current_objective.objective_id == "OBJ02_WHISPER_WAKE"
        primary_win_con = game_state.current_objective.primary_win_condition
        assert primary_win_con is not None
        assert primary_win_con.component_type == "CAST_SPELL_WITH_STORM_COUNT"
        
        spell_id = primary_win_con.params.get("spell_card_id_or_name")
        min_storm = primary_win_con.params.get("min_storm_count")
        
        # Set the objective progress flag that WinLossChecker looks for
        event_key = f"CAST_SPELL_EVENT_MET_{spell_id}_STORM_{min_storm}"
        game_state.objective_progress[event_key] = True
        
        # The old setup for Haunt toys is no longer relevant for this win condition
        # as defined in objectives.json.

        game_state.add_log_entry(f"Test manually set objective progress: {event_key} = True", "DEBUG")

        assert win_loss_checker.check_all_conditions() is True
        assert game_state.game_over is True
        assert game_state.win_status == "PRIMARY_WIN"

    def test_first_night_no_win_no_loss(
        self, 
        initialized_game_environment: Tuple[GameState, ActionResolver, EffectEngine, TurnManager, NightmareCreepModule, WinLossChecker]
    ):
        game_state, _, _, _, _, win_loss_checker = initialized_game_environment 
        # OBJ01_THE_FIRST_NIGHT has nightfall_turn: 4
        game_state.current_turn = 3 # Changed from 5 to be before nightfall
        
        # Ensure win conditions are NOT met
        game_state.objective_progress["distinct_toys_played_ids"] = {"T1"} # Only 1 toy
        game_state.objective_progress["spirits_created_total_game"] = 1 # Only 1 spirit
        
        assert win_loss_checker.check_all_conditions() is False
        assert game_state.game_over is False
        assert game_state.win_status is None

    def test_win_condition_unknown_type(
        self, 
        initialized_game_environment: Tuple[GameState, ActionResolver, EffectEngine, TurnManager, NightmareCreepModule, WinLossChecker]
    ):
        game_state, _, _, _, _, win_loss_checker = initialized_game_environment 
        
        original_primary_win_condition = game_state.current_objective.primary_win_condition
        
        # Modify current objective to have an unknown win condition component type
        # Ensure a primary_win_condition object exists before modifying it
        if game_state.current_objective.primary_win_condition is None:
             game_state.current_objective.primary_win_condition = ObjectiveLogicComponent(component_type="TEMP", params={})

        game_state.current_objective.primary_win_condition.component_type = "UNKNOWN_WIN_TYPE"
        
        game_state.game_log.clear() # Clear log to specifically check for the warning from this action
        assert win_loss_checker.check_all_conditions() is False 
        assert game_state.game_over is False
        
        # Check log for warning about unknown win type
        expected_log_message = "Win condition type 'UNKNOWN_WIN_TYPE' not yet implemented in WinLossChecker."
        assert any(expected_log_message in log for log in game_state.game_log if "WARNING" in log)

        # Restore original primary win condition
        game_state.current_objective.primary_win_condition = original_primary_win_condition