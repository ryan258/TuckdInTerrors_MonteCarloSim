# tests/game_logic/test_nightmare_creep.py
# Unit tests for nightmare_creep.py

import pytest
from typing import Tuple, List, Dict, Any
from unittest.mock import MagicMock, patch

from tuck_in_terrors_sim.game_logic.game_state import GameState
from tuck_in_terrors_sim.game_logic.effect_engine import EffectEngine
from tuck_in_terrors_sim.game_logic.nightmare_creep import NightmareCreepModule
from tuck_in_terrors_sim.game_elements.objective import ObjectiveCard, ObjectiveLogicComponent
from tuck_in_terrors_sim.game_elements.card import EffectLogic 
from tuck_in_terrors_sim.game_elements.enums import EffectTriggerType, EffectActionType

# Fixture 'initialized_game_environment' provides GameState, EffectEngine, NightmareCreepModule
# It's defined in tests/conftest.py

class TestNightmareCreepModule:

    def test_apply_nightmare_creep_not_active_turn_too_early(
        self, 
        initialized_game_environment: Tuple[GameState, Any, EffectEngine, NightmareCreepModule, Any]
    ):
        game_state, _, effect_engine, nightmare_module, _ = initialized_game_environment
        
        game_state.current_turn = 1 
        game_state.game_log.clear() 
        
        effect_engine.resolve_effect_logic = MagicMock()
        
        applied = nightmare_module.apply_nightmare_creep_for_current_turn()
        
        assert applied is False, "NC should not apply if turn is too early"
        assert game_state.nightmare_creep_effect_applied_this_turn is False
        effect_engine.resolve_effect_logic.assert_not_called()
        assert not any("Applying objective's NC effects" in entry for entry in game_state.game_log)

    def test_apply_nightmare_creep_active_applies_effect(
        self, 
        initialized_game_environment: Tuple[GameState, Any, EffectEngine, NightmareCreepModule, Any]
    ):
        game_state, _, effect_engine, nightmare_module, _ = initialized_game_environment
        
        game_state.current_turn = 5 
        game_state.game_log.clear()
        
        effect_engine.resolve_effect_logic = MagicMock()
        
        applied = nightmare_module.apply_nightmare_creep_for_current_turn()
        
        assert applied is True, "NC should indicate it was processed as it's the correct turn"
        assert game_state.nightmare_creep_effect_applied_this_turn is True
        
        effect_engine.resolve_effect_logic.assert_called_once()
        
        assert effect_engine.resolve_effect_logic.call_args is not None, "resolve_effect_logic should have been called"
        
        _pos_args, kw_args = effect_engine.resolve_effect_logic.call_args 
        
        assert "effect_logic" in kw_args, "effect_logic should be a keyword argument"
        resolved_effect_logic: EffectLogic = kw_args["effect_logic"]

        assert isinstance(resolved_effect_logic, EffectLogic)
        assert resolved_effect_logic.trigger == EffectTriggerType.ON_NIGHTMARE_CREEP_RESOLUTION_FOR_TURN.name
        
        # Specific check for OBJ01_THE_FIRST_NIGHT's NC effect from objectives.json
        # This assumes OBJ01 is the default loaded by initialized_game_environment
        assert len(resolved_effect_logic.actions) >= 1 
        first_action = resolved_effect_logic.actions[0]
        assert first_action.get("action_type") == EffectActionType.PLAYER_CHOICE.name
        assert first_action.get("params", {}).get("choice_id") == "NC_FIRST_NIGHT_CHOICE"
        
        assert any("Applying objective's NC effects" in entry for entry in game_state.game_log)

    def test_apply_nightmare_creep_no_nc_defined_in_objective(
        self,
        initialized_game_environment: Tuple[GameState, Any, EffectEngine, NightmareCreepModule, Any]
    ):
        game_state, _, effect_engine, nightmare_module, _ = initialized_game_environment
        
        game_state.current_objective.nightmare_creep_effect = [] 
        game_state.current_turn = 5 
        game_state.game_log.clear()
        
        effect_engine.resolve_effect_logic = MagicMock()
        
        applied = nightmare_module.apply_nightmare_creep_for_current_turn()
        
        assert applied is False, "NC should not apply if not defined in objective"
        assert game_state.nightmare_creep_effect_applied_this_turn is False
        effect_engine.resolve_effect_logic.assert_not_called()
        assert not any("Applying objective's NC effects" in entry for entry in game_state.game_log)


    def test_apply_nightmare_creep_malformed_effect_data(
        self,
        initialized_game_environment: Tuple[GameState, Any, EffectEngine, NightmareCreepModule, Any]
    ):
        game_state, _, effect_engine, nightmare_module, _ = initialized_game_environment
        game_state.current_turn = 5
        game_state.game_log.clear()
        
        if game_state.current_objective.nightmare_creep_effect:
            if not game_state.current_objective.nightmare_creep_effect[0].params:
                 game_state.current_objective.nightmare_creep_effect[0].params = {}
            game_state.current_objective.nightmare_creep_effect[0].params["effect_to_apply"] = "not_a_dict"
        else: 
            dummy_nc_component = ObjectiveLogicComponent(
                component_type="NIGHTMARE_CREEP_PHASED_EFFECT",
                params={"effective_on_turn": 5, "effect_to_apply": "not_a_dict"}
            )
            game_state.current_objective.nightmare_creep_effect = [dummy_nc_component]

        effect_engine.resolve_effect_logic = MagicMock()
        
        applied = nightmare_module.apply_nightmare_creep_for_current_turn()
        
        assert applied is True, "NC should be considered active for the turn even if its data is malformed"
        assert game_state.nightmare_creep_effect_applied_this_turn is True 
        effect_engine.resolve_effect_logic.assert_not_called() 
        assert any("effect_to_apply data is missing or malformed" in entry for entry in game_state.game_log)