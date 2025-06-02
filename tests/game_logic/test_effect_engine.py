# tests/game_logic/test_effect_engine.py
# Unit tests for effect_engine.py

import pytest
from typing import Tuple, List, Dict, Any
from unittest.mock import MagicMock, call # Added call

from tuck_in_terrors_sim.game_logic.game_state import GameState, CardInPlay
from tuck_in_terrors_sim.game_logic.effect_engine import EffectEngine
from tuck_in_terrors_sim.game_elements.card import Card, EffectLogic, Toy # Added Toy
from tuck_in_terrors_sim.game_elements.objective import ObjectiveCard
from tuck_in_terrors_sim.game_elements.enums import (
    EffectConditionType, EffectActionType, CardType, Zone, EffectTriggerType
)

# Fixture 'initialized_game_environment' is defined in tests/conftest.py
# Fixture 'ee_and_gs' (below) is more tailored for direct EffectEngine tests.

@pytest.fixture
def base_toy_card_def() -> Toy: # Changed to Toy for more specific testing
    """Provides a basic Toy card definition."""
    return Toy(card_id="T_BASE001", name="Base Test Toy", cost=1, card_type=CardType.TOY, quantity_in_deck=1)

@pytest.fixture
def another_toy_card_def() -> Toy:
    """Provides another basic Toy card definition for multi-card tests."""
    return Toy(card_id="T_OTHER001", name="Other Test Toy", cost=1, card_type=CardType.TOY, quantity_in_deck=1)


@pytest.fixture
def ee_and_gs(initialized_game_environment: Tuple[GameState, Any, EffectEngine, Any, Any], 
              base_toy_card_def: Toy, another_toy_card_def: Toy) -> Tuple[EffectEngine, GameState]: # Added card defs
    """Extracts EffectEngine and GameState, clears/preps for focused tests."""
    game_state, _, effect_engine, _, _ = initialized_game_environment
    
    # Clear and reset relevant parts of game_state for fresh tests
    game_state.hand = []
    game_state.deck = [ # Populate with concrete Card instances
        base_toy_card_def, # Use the new fixture
        another_toy_card_def, # Use the new fixture
        Toy(card_id="DECK_T3", name="Deck Toy 3", cost=1, card_type=CardType.TOY),
        Toy(card_id="DECK_T4", name="Deck Toy 4", cost=1, card_type=CardType.TOY),
    ]
    game_state.cards_in_play.clear()
    game_state.discard_pile = []
    game_state.spirit_tokens = 0
    game_state.memory_tokens = 0
    game_state.mana_pool = 10 # Default mana for tests
    game_state.objective_progress = game_state.initialize_objective_progress() # Reset progress
    game_state.game_log = [] 
    
    # Mock the trigger_effects method for easier assertion of subsequent triggers
    effect_engine.trigger_effects = MagicMock()
    
    return effect_engine, game_state

class TestEffectEngineConditions:

    def test_check_conditions_is_first_memory_true(self, ee_and_gs: Tuple[EffectEngine, GameState], base_toy_card_def: Toy):
        effect_engine, game_state = ee_and_gs
        game_state.first_memory_card_definition = base_toy_card_def
        conditions = [{"condition_type": EffectConditionType.IS_FIRST_MEMORY.name, "params": {}}]
        assert effect_engine._check_conditions(conditions, None, base_toy_card_def, None, None) is True

    def test_check_conditions_is_first_memory_false(self, ee_and_gs: Tuple[EffectEngine, GameState], base_toy_card_def: Toy, another_toy_card_def: Toy):
        effect_engine, game_state = ee_and_gs
        game_state.first_memory_card_definition = base_toy_card_def 
        conditions = [{"condition_type": EffectConditionType.IS_FIRST_MEMORY.name, "params": {}}]
        assert effect_engine._check_conditions(conditions, None, another_toy_card_def, None, None) is False

    def test_check_conditions_is_first_memory_in_play_true(self, ee_and_gs: Tuple[EffectEngine, GameState], base_toy_card_def: Toy):
        effect_engine, game_state = ee_and_gs
        game_state.first_memory_card_definition = base_toy_card_def
        game_state.first_memory_current_zone = Zone.IN_PLAY
        game_state.first_memory_instance_id = "fm_instance_123" 
        conditions = [{"condition_type": EffectConditionType.IS_FIRST_MEMORY_IN_PLAY.name, "params": {}}]
        assert effect_engine._check_conditions(conditions, None, None, None, None) is True

    def test_check_conditions_is_first_memory_in_play_false_not_in_play(self, ee_and_gs: Tuple[EffectEngine, GameState], base_toy_card_def: Toy):
        effect_engine, game_state = ee_and_gs
        game_state.first_memory_card_definition = base_toy_card_def
        game_state.first_memory_current_zone = Zone.HAND 
        game_state.first_memory_instance_id = None
        conditions = [{"condition_type": EffectConditionType.IS_FIRST_MEMORY_IN_PLAY.name, "params": {}}]
        assert effect_engine._check_conditions(conditions, None, None, None, None) is False

    def test_check_conditions_no_conditions(self, ee_and_gs: Tuple[EffectEngine, GameState]):
        effect_engine, _ = ee_and_gs
        assert effect_engine._check_conditions([], None, None, None, None) is True

    def test_check_conditions_unimplemented(self, ee_and_gs: Tuple[EffectEngine, GameState]):
        effect_engine, game_state = ee_and_gs
        conditions = [{"condition_type": "NON_EXISTENT_CONDITION", "params": {}}]
        game_state.game_log.clear() 
        assert effect_engine._check_conditions(conditions, None, None, None, None) is False
        assert any("Unknown condition type 'NON_EXISTENT_CONDITION'" in entry for entry in game_state.game_log if "ERROR" in entry)

    def test_check_condition_has_counter_type_value_ge_true(self, ee_and_gs: Tuple[EffectEngine, GameState], base_toy_card_def: Toy):
        effect_engine, game_state = ee_and_gs
        card_in_play = CardInPlay(base_toy_card_def)
        game_state.cards_in_play[card_in_play.instance_id] = card_in_play
        card_in_play.add_counter("power", 3)

        conditions = [{
            "condition_type": EffectConditionType.HAS_COUNTER_TYPE_VALUE_GE.name,
            "params": {"target_card_instance_id": card_in_play.instance_id, "counter_type": "power", "amount": 3}
        }]
        assert effect_engine._check_conditions(conditions, card_in_play, None, None, None) is True

        conditions_self = [{ 
            "condition_type": EffectConditionType.HAS_COUNTER_TYPE_VALUE_GE.name,
            "params": {"target_card_instance_id": "SELF", "counter_type": "power", "amount": 2}
        }]
        assert effect_engine._check_conditions(conditions_self, card_in_play, None, None, None) is True


    def test_check_condition_has_counter_type_value_ge_false(self, ee_and_gs: Tuple[EffectEngine, GameState], base_toy_card_def: Toy):
        effect_engine, game_state = ee_and_gs
        card_in_play = CardInPlay(base_toy_card_def)
        game_state.cards_in_play[card_in_play.instance_id] = card_in_play
        card_in_play.add_counter("power", 1)

        conditions_less = [{
            "condition_type": EffectConditionType.HAS_COUNTER_TYPE_VALUE_GE.name,
            "params": {"target_card_instance_id": card_in_play.instance_id, "counter_type": "power", "amount": 3}
        }]
        assert effect_engine._check_conditions(conditions_less, card_in_play, None, None, None) is False

        conditions_wrong_type = [{
            "condition_type": EffectConditionType.HAS_COUNTER_TYPE_VALUE_GE.name,
            "params": {"target_card_instance_id": card_in_play.instance_id, "counter_type": "charge", "amount": 1}
        }]
        assert effect_engine._check_conditions(conditions_wrong_type, card_in_play, None, None, None) is False
        
        conditions_no_target = [{
            "condition_type": EffectConditionType.HAS_COUNTER_TYPE_VALUE_GE.name,
            "params": {"target_card_instance_id": "NON_EXISTENT_ID", "counter_type": "power", "amount": 1}
        }]
        assert effect_engine._check_conditions(conditions_no_target, card_in_play, None, None, None) is False


class TestEffectEngineActions:

    def test_execute_action_draw_cards(self, ee_and_gs: Tuple[EffectEngine, GameState]):
        effect_engine, game_state = ee_and_gs
        initial_deck_size = len(game_state.deck)
        initial_hand_size = len(game_state.hand)
        action_data = {"action_type": EffectActionType.DRAW_CARDS.name, "params": {"amount": 2}}
        
        effect_engine._execute_action(action_data, None, None, None, None)
        
        assert len(game_state.hand) == initial_hand_size + 2
        assert len(game_state.deck) == initial_deck_size - 2
        assert effect_engine.trigger_effects.call_count == 2
        for i in range(2):
            args, kwargs = effect_engine.trigger_effects.call_args_list[i]
            assert args[0] == EffectTriggerType.WHEN_CARD_DRAWN
            assert 'drawn_card_definition' in kwargs['event_context']


    def test_execute_action_draw_cards_empty_deck(self, ee_and_gs: Tuple[EffectEngine, GameState]):
        effect_engine, game_state = ee_and_gs
        game_state.deck = [] 
        initial_hand_size = len(game_state.hand)
        game_state.game_log.clear()
        
        action_data = {"action_type": EffectActionType.DRAW_CARDS.name, "params": {"amount": 1}}
        effect_engine._execute_action(action_data, None, None, None, None)
        
        assert len(game_state.hand) == initial_hand_size 
        assert any("Cannot draw card: Deck is empty." in entry for entry in game_state.game_log if "WARNING" in entry)
        effect_engine.trigger_effects.assert_not_called() 

    def test_execute_action_create_spirit_tokens(self, ee_and_gs: Tuple[EffectEngine, GameState]):
        effect_engine, game_state = ee_and_gs
        initial_spirits = game_state.spirit_tokens
        initial_objective_spirits = game_state.objective_progress.get("spirits_created_total_game", 0)
        action_data = {"action_type": EffectActionType.CREATE_SPIRIT_TOKENS.name, "params": {"amount": 3}}
        
        effect_engine._execute_action(action_data, None, None, None, None)
        
        assert game_state.spirit_tokens == initial_spirits + 3
        assert game_state.objective_progress["spirits_created_total_game"] == initial_objective_spirits + 3
        effect_engine.trigger_effects.assert_called_once_with(
            EffectTriggerType.WHEN_SPIRIT_CREATED, 
            event_context={'amount': 3, 'action_source_instance': None, 'action_source_definition': None}
        )

    def test_execute_action_create_memory_tokens(self, ee_and_gs: Tuple[EffectEngine, GameState]):
        effect_engine, game_state = ee_and_gs
        initial_memory = game_state.memory_tokens
        action_data = {"action_type": EffectActionType.CREATE_MEMORY_TOKENS.name, "params": {"amount": 1}}
        
        effect_engine._execute_action(action_data, None, None, None, None)
        
        assert game_state.memory_tokens == initial_memory + 1
        effect_engine.trigger_effects.assert_called_once_with(
            EffectTriggerType.WHEN_MEMORY_TOKEN_CREATED, 
            event_context={'amount': 1, 'action_source_instance': None, 'action_source_definition': None}
        )

    def test_execute_action_add_mana_from_card_effect(self, ee_and_gs: Tuple[EffectEngine, GameState], base_toy_card_def: Toy):
        effect_engine, game_state = ee_and_gs
        initial_mana = game_state.mana_pool
        initial_objective_mana = game_state.objective_progress.get("mana_from_card_effects_total_game", 0)
        action_data = {"action_type": EffectActionType.ADD_MANA.name, "params": {"amount": 5}}
        
        source_card_in_play = CardInPlay(base_toy_card_def)
        game_state.cards_in_play[source_card_in_play.instance_id] = source_card_in_play
        
        effect_engine._execute_action(action_data, source_card_in_play, None, None, None)
        
        assert game_state.mana_pool == initial_mana + 5
        assert game_state.objective_progress["mana_from_card_effects_total_game"] == initial_objective_mana + 5

    def test_execute_action_add_mana_not_from_card_effect(self, ee_and_gs: Tuple[EffectEngine, GameState]):
        effect_engine, game_state = ee_and_gs
        initial_mana = game_state.mana_pool
        initial_objective_mana = game_state.objective_progress.get("mana_from_card_effects_total_game", 0)
        action_data = {"action_type": EffectActionType.ADD_MANA.name, "params": {"amount": 5}}
                
        effect_engine._execute_action(action_data, None, None, None, None) 
        
        assert game_state.mana_pool == initial_mana + 5
        assert game_state.objective_progress.get("mana_from_card_effects_total_game", 0) == initial_objective_mana


    def test_execute_action_browse_deck(self, ee_and_gs: Tuple[EffectEngine, GameState]):
        effect_engine, game_state = ee_and_gs
        initial_deck_order = list(game_state.deck) 
        game_state.game_log.clear()
        action_data = {"action_type": EffectActionType.BROWSE_DECK.name, "params": {"count": 2}}
        effect_engine._execute_action(action_data, None, None, None, None)
        
        assert any("Browse top 2 card(s)" in entry for entry in game_state.game_log)
        assert any("Placeholder: AI would choose order" in entry for entry in game_state.game_log)
        assert game_state.deck == initial_deck_order 

    def test_execute_action_unimplemented(self, ee_and_gs: Tuple[EffectEngine, GameState]):
        effect_engine, game_state = ee_and_gs
        action_data = {"action_type": "NON_EXISTENT_ACTION", "params": {}}
        game_state.game_log.clear()
        effect_engine._execute_action(action_data, None, None, None, None)
        assert any("Unknown action type 'NON_EXISTENT_ACTION'" in entry for entry in game_state.game_log if "ERROR" in entry)

    def test_execute_action_place_counter_on_card_self(self, ee_and_gs: Tuple[EffectEngine, GameState], base_toy_card_def: Toy):
        effect_engine, game_state = ee_and_gs
        card_in_play = CardInPlay(base_toy_card_def)
        game_state.cards_in_play[card_in_play.instance_id] = card_in_play
        
        action_data = {
            "action_type": EffectActionType.PLACE_COUNTER_ON_CARD.name,
            "params": {"target_card_instance_id": "SELF", "counter_type": "test_counter", "amount": 2}
        }
        effect_engine._execute_action(action_data, card_in_play, None, None, None)
        
        assert card_in_play.counters.get("test_counter") == 2
        effect_engine.trigger_effects.assert_called_once_with(
            EffectTriggerType.WHEN_COUNTER_REACHES_THRESHOLD,
            source_card_instance_for_trigger=card_in_play,
            event_context={
                'counter_type': "test_counter", 
                'total_amount': 2, 
                'placed_amount': 2,
                'target_card_instance': card_in_play,
                'action_source_instance': card_in_play, 
                'action_source_definition': None
            }
        )

    def test_execute_action_place_counter_on_card_other(self, ee_and_gs: Tuple[EffectEngine, GameState], base_toy_card_def: Toy, another_toy_card_def: Toy):
        effect_engine, game_state = ee_and_gs
        source_card = CardInPlay(base_toy_card_def) 
        target_card = CardInPlay(another_toy_card_def) 
        game_state.cards_in_play[source_card.instance_id] = source_card
        game_state.cards_in_play[target_card.instance_id] = target_card
        
        action_data = {
            "action_type": EffectActionType.PLACE_COUNTER_ON_CARD.name,
            "params": {"target_card_instance_id": target_card.instance_id, "counter_type": "charge", "amount": 1}
        }
        effect_engine._execute_action(action_data, source_card, None, None, None)
        
        assert target_card.counters.get("charge") == 1
        assert source_card.counters == {} 
        effect_engine.trigger_effects.assert_called_once_with(
            EffectTriggerType.WHEN_COUNTER_REACHES_THRESHOLD,
            source_card_instance_for_trigger=target_card,
            event_context={
                'counter_type': "charge", 
                'total_amount': 1, 
                'placed_amount': 1,
                'target_card_instance': target_card,
                'action_source_instance': source_card, 
                'action_source_definition': None
            }
        )

    def test_execute_action_sacrifice_card_in_play_self(self, ee_and_gs: Tuple[EffectEngine, GameState], base_toy_card_def: Toy):
        effect_engine, game_state = ee_and_gs
        card_to_sacrifice = CardInPlay(base_toy_card_def)
        game_state.cards_in_play[card_to_sacrifice.instance_id] = card_to_sacrifice
        
        action_data = {
            "action_type": EffectActionType.SACRIFICE_CARD_IN_PLAY.name,
            "params": {"target_card_instance_id": "SELF"}
        }
        effect_engine._execute_action(action_data, card_to_sacrifice, None, None, None)
        
        assert card_to_sacrifice.instance_id not in game_state.cards_in_play
        assert base_toy_card_def in game_state.discard_pile
        
        actual_trigger_calls = [c[0][0] for c in effect_engine.trigger_effects.call_args_list]
        assert EffectTriggerType.BEFORE_THIS_CARD_LEAVES_PLAY in actual_trigger_calls
        assert EffectTriggerType.ON_LEAVE_PLAY in actual_trigger_calls
        assert EffectTriggerType.ON_SACRIFICE_THIS_CARD in actual_trigger_calls
        assert EffectTriggerType.WHEN_OTHER_CARD_LEAVES_PLAY in actual_trigger_calls
        assert EffectTriggerType.WHEN_YOU_SACRIFICE_TOY in actual_trigger_calls


    def test_execute_action_return_this_card_to_hand(self, ee_and_gs: Tuple[EffectEngine, GameState], base_toy_card_def: Toy):
        effect_engine, game_state = ee_and_gs
        card_to_return = CardInPlay(base_toy_card_def)
        game_state.cards_in_play[card_to_return.instance_id] = card_to_return
        initial_hand_size = len(game_state.hand)

        action_data = {"action_type": EffectActionType.RETURN_THIS_CARD_TO_HAND.name, "params": {}}
        effect_engine._execute_action(action_data, card_to_return, None, None, None)

        assert card_to_return.instance_id not in game_state.cards_in_play
        assert base_toy_card_def in game_state.hand
        assert len(game_state.hand) == initial_hand_size + 1

        actual_trigger_calls = [c[0][0] for c in effect_engine.trigger_effects.call_args_list]
        assert EffectTriggerType.BEFORE_THIS_CARD_LEAVES_PLAY in actual_trigger_calls
        assert EffectTriggerType.ON_LEAVE_PLAY in actual_trigger_calls
        assert EffectTriggerType.WHEN_OTHER_CARD_LEAVES_PLAY in actual_trigger_calls


class TestEffectEngineResolveEffectLogic:

    def test_resolve_effect_logic_conditions_met(self, ee_and_gs: Tuple[EffectEngine, GameState], base_toy_card_def: Toy):
        effect_engine, game_state = ee_and_gs
        test_effect = EffectLogic(
            trigger=EffectTriggerType.ON_PLAY.name, 
            conditions=[{"condition_type": EffectConditionType.IS_FIRST_MEMORY_IN_PLAY.name, "params": {}}],
            actions=[{"action_type": EffectActionType.CREATE_SPIRIT_TOKENS.name, "params": {"amount": 1}}]
        )
        game_state.first_memory_card_definition = base_toy_card_def
        game_state.first_memory_current_zone = Zone.IN_PLAY
        game_state.first_memory_instance_id = "fm_instance_active" 
        
        initial_spirits = game_state.spirit_tokens
        
        # When resolve_effect_logic calls _execute_action for CREATE_SPIRIT_TOKENS,
        # source_card_instance will be None, and source_card_definition will be base_toy_card_def.
        effect_engine.resolve_effect_logic(test_effect, source_card_instance=None, source_card_definition=base_toy_card_def)
        assert game_state.spirit_tokens == initial_spirits + 1
        
        # The _execute_action for CREATE_SPIRIT_TOKENS calls trigger_effects.
        # In this scenario, source_card_instance within _execute_action is None,
        # and source_card_definition is base_toy_card_def.
        effect_engine.trigger_effects.assert_called_with(
            EffectTriggerType.WHEN_SPIRIT_CREATED, 
            event_context={'amount': 1, 'action_source_instance': None, 'action_source_definition': base_toy_card_def}
        )


    def test_resolve_effect_logic_conditions_not_met(self, ee_and_gs: Tuple[EffectEngine, GameState], base_toy_card_def: Toy):
        effect_engine, game_state = ee_and_gs
        test_effect = EffectLogic(
            trigger=EffectTriggerType.ON_PLAY.name,
            conditions=[{"condition_type": EffectConditionType.IS_FIRST_MEMORY_IN_PLAY.name, "params": {}}],
            actions=[{"action_type": EffectActionType.CREATE_SPIRIT_TOKENS.name, "params": {"amount": 1}}]
        )
        game_state.first_memory_card_definition = base_toy_card_def
        game_state.first_memory_current_zone = Zone.HAND 
        initial_spirits = game_state.spirit_tokens
        game_state.game_log.clear()

        effect_engine.resolve_effect_logic(test_effect, source_card_definition=base_toy_card_def)
        assert game_state.spirit_tokens == initial_spirits 
        assert any("Conditions not met" in entry for entry in game_state.game_log)
        effect_engine.trigger_effects.assert_not_called()


    def test_resolve_effect_logic_no_conditions_action_runs(self, ee_and_gs: Tuple[EffectEngine, GameState]):
        effect_engine, game_state = ee_and_gs
        test_effect = EffectLogic(
            trigger=EffectTriggerType.ON_PLAY.name,
            conditions=[], 
            actions=[{"action_type": EffectActionType.ADD_MANA.name, "params": {"amount": 10}}]
        )
        initial_mana = game_state.mana_pool
        effect_engine.resolve_effect_logic(test_effect) # source_card_instance and source_card_definition are None here
        assert game_state.mana_pool == initial_mana + 10
        # ADD_MANA doesn't call trigger_effects itself, so no assertion needed here on trigger_effects mock.