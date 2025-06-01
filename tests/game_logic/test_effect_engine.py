# tests/game_logic/test_effect_engine.py
# Unit tests for effect_engine.py

import pytest
from typing import Tuple, List, Dict, Any
from unittest.mock import MagicMock

from tuck_in_terrors_sim.game_logic.game_state import GameState, CardInPlay
from tuck_in_terrors_sim.game_logic.effect_engine import EffectEngine
from tuck_in_terrors_sim.game_elements.card import Card, EffectLogic, Toy
from tuck_in_terrors_sim.game_elements.objective import ObjectiveCard
from tuck_in_terrors_sim.game_elements.enums import (
    EffectConditionType, EffectActionType, CardType, Zone, EffectTriggerType
)

# Fixture 'initialized_game_environment' is defined in tests/conftest.py

@pytest.fixture
def ee_and_gs(initialized_game_environment: Tuple[GameState, Any, EffectEngine, Any, Any]) -> Tuple[EffectEngine, GameState]:
    """Extracts EffectEngine and GameState from the larger fixture."""
    game_state, _, effect_engine, _, _ = initialized_game_environment
    # Ensure a clean hand and deck for some tests
    game_state.hand = []
    game_state.deck = [ 
        Toy(card_id="DECK_T1", name="Deck Toy 1", cost=1, card_type=CardType.TOY),
        Toy(card_id="DECK_T2", name="Deck Toy 2", cost=1, card_type=CardType.TOY),
        Toy(card_id="DECK_T3", name="Deck Toy 3", cost=1, card_type=CardType.TOY),
        Toy(card_id="DECK_T4", name="Deck Toy 4", cost=1, card_type=CardType.TOY),
    ]
    game_state.spirit_tokens = 0
    game_state.memory_tokens = 0
    game_state.mana_pool = 0
    game_state.game_log = [] # Clear log for fresh test section
    return effect_engine, game_state

class TestEffectEngineConditions:

    def test_check_conditions_is_first_memory_true(self, ee_and_gs: Tuple[EffectEngine, GameState]):
        effect_engine, game_state = ee_and_gs
        fm_card_def = Toy(card_id="FM_TOY", name="First Memory Toy", cost=1, card_type=CardType.TOY)
        game_state.first_memory_card_definition = fm_card_def
        conditions = [{"condition_type": EffectConditionType.IS_FIRST_MEMORY.name, "params": {}}]
        assert effect_engine._check_conditions(conditions, None, fm_card_def, None) is True

    def test_check_conditions_is_first_memory_false(self, ee_and_gs: Tuple[EffectEngine, GameState]):
        effect_engine, game_state = ee_and_gs
        fm_card_def = Toy(card_id="FM_TOY", name="First Memory Toy", cost=1, card_type=CardType.TOY)
        other_card_def = Toy(card_id="OTHER_TOY", name="Other Toy", cost=1, card_type=CardType.TOY)
        game_state.first_memory_card_definition = fm_card_def
        conditions = [{"condition_type": EffectConditionType.IS_FIRST_MEMORY.name, "params": {}}]
        assert effect_engine._check_conditions(conditions, None, other_card_def, None) is False

    def test_check_conditions_is_first_memory_in_play_true(self, ee_and_gs: Tuple[EffectEngine, GameState]):
        effect_engine, game_state = ee_and_gs
        fm_card_def = Toy(card_id="FM_TOY_IN_PLAY", name="FM In Play", cost=1, card_type=CardType.TOY)
        game_state.first_memory_card_definition = fm_card_def
        game_state.first_memory_current_zone = Zone.IN_PLAY
        game_state.first_memory_instance_id = "fm_instance_123" 
        conditions = [{"condition_type": EffectConditionType.IS_FIRST_MEMORY_IN_PLAY.name, "params": {}}]
        assert effect_engine._check_conditions(conditions, None, None, None) is True

    def test_check_conditions_is_first_memory_in_play_false_not_in_play(self, ee_and_gs: Tuple[EffectEngine, GameState]):
        effect_engine, game_state = ee_and_gs
        fm_card_def = Toy(card_id="FM_TOY_NOT_IN_PLAY", name="FM Not In Play", cost=1, card_type=CardType.TOY)
        game_state.first_memory_card_definition = fm_card_def
        game_state.first_memory_current_zone = Zone.HAND 
        game_state.first_memory_instance_id = None
        conditions = [{"condition_type": EffectConditionType.IS_FIRST_MEMORY_IN_PLAY.name, "params": {}}]
        assert effect_engine._check_conditions(conditions, None, None, None) is False

    def test_check_conditions_no_conditions(self, ee_and_gs: Tuple[EffectEngine, GameState]):
        effect_engine, _ = ee_and_gs
        assert effect_engine._check_conditions([], None, None, None) is True

    def test_check_conditions_unimplemented(self, ee_and_gs: Tuple[EffectEngine, GameState]):
        effect_engine, game_state = ee_and_gs
        conditions = [{"condition_type": "NON_EXISTENT_CONDITION", "params": {}}] # String that won't match enum
        game_state.game_log.clear() # Clear log for this specific check
        assert effect_engine._check_conditions(conditions, None, None, None) is False
        assert "Unknown condition type 'NON_EXISTENT_CONDITION'" in game_state.game_log[-1]


class TestEffectEngineActions:

    def test_execute_action_draw_cards(self, ee_and_gs: Tuple[EffectEngine, GameState]):
        effect_engine, game_state = ee_and_gs
        initial_deck_size = len(game_state.deck)
        initial_hand_size = len(game_state.hand)
        action_data = {"action_type": EffectActionType.DRAW_CARDS.name, "params": {"amount": 2}}
        effect_engine._execute_action(action_data, None, None, None)
        assert len(game_state.hand) == initial_hand_size + 2
        assert len(game_state.deck) == initial_deck_size - 2

    def test_execute_action_draw_cards_empty_deck(self, ee_and_gs: Tuple[EffectEngine, GameState]):
        effect_engine, game_state = ee_and_gs
        game_state.deck = [] 
        initial_hand_size = len(game_state.hand)
        game_state.game_log.clear() # Clear log for specific check of this action's logs
        
        action_data = {"action_type": EffectActionType.DRAW_CARDS.name, "params": {"amount": 1}}
        effect_engine._execute_action(action_data, None, None, None)
        
        assert len(game_state.hand) == initial_hand_size 
        
        # Check that the relevant log messages were made by this action
        logs_from_action = [entry for entry in game_state.game_log if "DRAW_CARDS" in entry or "Deck is empty" in entry or "Hand size now" in entry]
        assert any("Cannot draw card: Deck is empty." in entry for entry in logs_from_action)
        assert any(f"Hand size now: {initial_hand_size}" in entry for entry in logs_from_action)


    def test_execute_action_create_spirit_tokens(self, ee_and_gs: Tuple[EffectEngine, GameState]):
        effect_engine, game_state = ee_and_gs
        initial_spirits = game_state.spirit_tokens
        action_data = {"action_type": EffectActionType.CREATE_SPIRIT_TOKENS.name, "params": {"amount": 3}}
        effect_engine._execute_action(action_data, None, None, None)
        assert game_state.spirit_tokens == initial_spirits + 3

    def test_execute_action_create_memory_tokens(self, ee_and_gs: Tuple[EffectEngine, GameState]):
        effect_engine, game_state = ee_and_gs
        initial_memory = game_state.memory_tokens
        action_data = {"action_type": EffectActionType.CREATE_MEMORY_TOKENS.name, "params": {"amount": 1}}
        effect_engine._execute_action(action_data, None, None, None)
        assert game_state.memory_tokens == initial_memory + 1

    def test_execute_action_add_mana(self, ee_and_gs: Tuple[EffectEngine, GameState]):
        effect_engine, game_state = ee_and_gs
        initial_mana = game_state.mana_pool
        action_data = {"action_type": EffectActionType.ADD_MANA.name, "params": {"amount": 5}}
        effect_engine._execute_action(action_data, None, None, None)
        assert game_state.mana_pool == initial_mana + 5

    def test_execute_action_browse_deck(self, ee_and_gs: Tuple[EffectEngine, GameState]):
        effect_engine, game_state = ee_and_gs
        initial_deck_order = list(game_state.deck) 
        game_state.game_log.clear()
        action_data = {"action_type": EffectActionType.BROWSE_DECK.name, "params": {"count": 2}}
        effect_engine._execute_action(action_data, None, None, None)
        
        assert any("Browse top 2 card(s)" in entry for entry in game_state.game_log)
        assert any("Placeholder: AI would choose order" in entry for entry in game_state.game_log)
        assert game_state.deck == initial_deck_order 

    def test_execute_action_unimplemented(self, ee_and_gs: Tuple[EffectEngine, GameState]):
        effect_engine, game_state = ee_and_gs
        action_data = {"action_type": "NON_EXISTENT_ACTION", "params": {}} # String that won't match enum
        game_state.game_log.clear()
        effect_engine._execute_action(action_data, None, None, None)
        assert "Unknown action type 'NON_EXISTENT_ACTION'" in game_state.game_log[-1]


class TestEffectEngineResolveEffectLogic:

    def test_resolve_effect_logic_conditions_met(self, ee_and_gs: Tuple[EffectEngine, GameState]):
        effect_engine, game_state = ee_and_gs
        test_effect = EffectLogic(
            trigger=EffectTriggerType.ON_PLAY.name, 
            conditions=[{"condition_type": EffectConditionType.IS_FIRST_MEMORY_IN_PLAY.name, "params": {}}],
            actions=[{"action_type": EffectActionType.CREATE_SPIRIT_TOKENS.name, "params": {"amount": 1}}]
        )
        game_state.first_memory_card_definition = Toy(card_id="FM001", name="FM Toy", cost=1, card_type=CardType.TOY)
        game_state.first_memory_current_zone = Zone.IN_PLAY
        game_state.first_memory_instance_id = "fm_instance_active"
        initial_spirits = game_state.spirit_tokens
        
        effect_engine.resolve_effect_logic(test_effect)
        assert game_state.spirit_tokens == initial_spirits + 1

    def test_resolve_effect_logic_conditions_not_met(self, ee_and_gs: Tuple[EffectEngine, GameState]):
        effect_engine, game_state = ee_and_gs
        test_effect = EffectLogic(
            trigger=EffectTriggerType.ON_PLAY.name,
            conditions=[{"condition_type": EffectConditionType.IS_FIRST_MEMORY_IN_PLAY.name, "params": {}}],
            actions=[{"action_type": EffectActionType.CREATE_SPIRIT_TOKENS.name, "params": {"amount": 1}}]
        )
        game_state.first_memory_card_definition = Toy(card_id="FM001", name="FM Toy", cost=1, card_type=CardType.TOY)
        game_state.first_memory_current_zone = Zone.HAND 
        initial_spirits = game_state.spirit_tokens
        game_state.game_log.clear()

        effect_engine.resolve_effect_logic(test_effect)
        assert game_state.spirit_tokens == initial_spirits 
        assert "Conditions not met" in game_state.game_log[-1]

    def test_resolve_effect_logic_no_conditions_action_runs(self, ee_and_gs: Tuple[EffectEngine, GameState]):
        effect_engine, game_state = ee_and_gs
        test_effect = EffectLogic(
            trigger=EffectTriggerType.ON_PLAY.name,
            conditions=[], 
            actions=[{"action_type": EffectActionType.ADD_MANA.name, "params": {"amount": 10}}]
        )
        initial_mana = game_state.mana_pool
        effect_engine.resolve_effect_logic(test_effect)
        assert game_state.mana_pool == initial_mana + 10