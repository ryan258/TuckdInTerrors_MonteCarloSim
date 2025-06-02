# tests/game_logic/test_effect_engine.py
# Unit tests for effect_engine.py

import pytest
from typing import Tuple, List, Dict, Any
from unittest.mock import MagicMock, call 

from tuck_in_terrors_sim.game_logic.game_state import GameState, CardInPlay
from tuck_in_terrors_sim.game_logic.effect_engine import EffectEngine
from tuck_in_terrors_sim.game_elements.card import Card, EffectLogic, Toy, Spell 
from tuck_in_terrors_sim.game_elements.objective import ObjectiveCard
from tuck_in_terrors_sim.game_elements.enums import (
    EffectConditionType, EffectActionType, CardType, Zone, EffectTriggerType, PlayerChoiceType
)
from tuck_in_terrors_sim.ai.ai_profiles.random_ai import RandomAI 

@pytest.fixture
def base_toy_card_def() -> Toy: 
    return Toy(card_id="T_BASE001", name="Base Test Toy", cost=1, card_type=CardType.TOY, quantity_in_deck=1)

@pytest.fixture
def another_toy_card_def() -> Toy:
    return Toy(card_id="T_OTHER001", name="Other Test Toy", cost=1, card_type=CardType.TOY, quantity_in_deck=1)

@pytest.fixture
def spell_card_def() -> Spell:
    """Provides a basic Spell card definition."""
    return Spell(card_id="S_BASE001", name="Base Test Spell", cost=1, card_type=CardType.SPELL, quantity_in_deck=1)


@pytest.fixture
def ee_and_gs(initialized_game_environment: Tuple[GameState, Any, EffectEngine, Any, Any], 
              base_toy_card_def: Toy, another_toy_card_def: Toy, spell_card_def: Spell) -> Tuple[EffectEngine, GameState]:
    game_state, _, effect_engine, _, _ = initialized_game_environment
    
    game_state.hand = []
    game_state.deck = [ 
        base_toy_card_def, 
        another_toy_card_def, 
        Toy(card_id="DECK_T3", name="Deck Toy 3", cost=1, card_type=CardType.TOY),
        spell_card_def, 
        Toy(card_id="DECK_T4", name="Deck Toy 4", cost=1, card_type=CardType.TOY),
    ]
    game_state.cards_in_play.clear()
    game_state.discard_pile = []
    game_state.exile_zone = [] 
    game_state.spirit_tokens = 0
    game_state.memory_tokens = 0
    game_state.mana_pool = 10 
    game_state.objective_progress = game_state.initialize_objective_progress() 
    game_state.game_log = [] 
    game_state.first_memory_card_definition = None 
    game_state.first_memory_instance_id = None
    game_state.first_memory_current_zone = None
    
    effect_engine.trigger_effects = MagicMock() 
    
    return effect_engine, game_state

class TestEffectEngineConditions:

    def test_check_conditions_is_first_memory_true(self, ee_and_gs: Tuple[EffectEngine, GameState], base_toy_card_def: Toy):
        effect_engine, game_state = ee_and_gs
        game_state.first_memory_card_definition = base_toy_card_def
        conditions = [{"condition_type": EffectConditionType.IS_FIRST_MEMORY.name, "params": {}}]
        assert effect_engine._check_conditions(conditions, None, base_toy_card_def, None, {}) is True

    def test_check_conditions_is_first_memory_false(self, ee_and_gs: Tuple[EffectEngine, GameState], base_toy_card_def: Toy, another_toy_card_def: Toy):
        effect_engine, game_state = ee_and_gs
        game_state.first_memory_card_definition = base_toy_card_def 
        conditions = [{"condition_type": EffectConditionType.IS_FIRST_MEMORY.name, "params": {}}]
        assert effect_engine._check_conditions(conditions, None, another_toy_card_def, None, {}) is False

    def test_check_conditions_is_first_memory_in_play_true(self, ee_and_gs: Tuple[EffectEngine, GameState], base_toy_card_def: Toy):
        effect_engine, game_state = ee_and_gs
        game_state.first_memory_card_definition = base_toy_card_def
        game_state.first_memory_current_zone = Zone.IN_PLAY
        game_state.first_memory_instance_id = "fm_instance_123" 
        conditions = [{"condition_type": EffectConditionType.IS_FIRST_MEMORY_IN_PLAY.name, "params": {}}]
        assert effect_engine._check_conditions(conditions, None, None, None, {}) is True

    def test_check_conditions_is_first_memory_in_play_false_not_in_play(self, ee_and_gs: Tuple[EffectEngine, GameState], base_toy_card_def: Toy):
        effect_engine, game_state = ee_and_gs
        game_state.first_memory_card_definition = base_toy_card_def
        game_state.first_memory_current_zone = Zone.HAND 
        game_state.first_memory_instance_id = None
        conditions = [{"condition_type": EffectConditionType.IS_FIRST_MEMORY_IN_PLAY.name, "params": {}}]
        assert effect_engine._check_conditions(conditions, None, None, None, {}) is False

    def test_check_conditions_no_conditions(self, ee_and_gs: Tuple[EffectEngine, GameState]):
        effect_engine, _ = ee_and_gs
        assert effect_engine._check_conditions([], None, None, None, {}) is True

    def test_check_conditions_unimplemented(self, ee_and_gs: Tuple[EffectEngine, GameState]):
        effect_engine, game_state = ee_and_gs
        conditions = [{"condition_type": "NON_EXISTENT_CONDITION", "params": {}}]
        game_state.game_log.clear() 
        assert effect_engine._check_conditions(conditions, None, None, None, {}) is False
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
        assert effect_engine._check_conditions(conditions, card_in_play, None, None, {}) is True

        conditions_self = [{ 
            "condition_type": EffectConditionType.HAS_COUNTER_TYPE_VALUE_GE.name,
            "params": {"target_card_instance_id": "SELF", "counter_type": "power", "amount": 2}
        }]
        assert effect_engine._check_conditions(conditions_self, card_in_play, None, None, {}) is True


    def test_check_condition_has_counter_type_value_ge_false(self, ee_and_gs: Tuple[EffectEngine, GameState], base_toy_card_def: Toy):
        effect_engine, game_state = ee_and_gs
        card_in_play = CardInPlay(base_toy_card_def)
        game_state.cards_in_play[card_in_play.instance_id] = card_in_play
        card_in_play.add_counter("power", 1)

        conditions_less = [{
            "condition_type": EffectConditionType.HAS_COUNTER_TYPE_VALUE_GE.name,
            "params": {"target_card_instance_id": card_in_play.instance_id, "counter_type": "power", "amount": 3}
        }]
        assert effect_engine._check_conditions(conditions_less, card_in_play, None, None, {}) is False

        conditions_wrong_type = [{
            "condition_type": EffectConditionType.HAS_COUNTER_TYPE_VALUE_GE.name,
            "params": {"target_card_instance_id": card_in_play.instance_id, "counter_type": "charge", "amount": 1}
        }]
        assert effect_engine._check_conditions(conditions_wrong_type, card_in_play, None, None, {}) is False
        
        conditions_no_target = [{
            "condition_type": EffectConditionType.HAS_COUNTER_TYPE_VALUE_GE.name,
            "params": {"target_card_instance_id": "NON_EXISTENT_ID", "counter_type": "power", "amount": 1}
        }]
        assert effect_engine._check_conditions(conditions_no_target, card_in_play, None, None, {}) is False

    def test_check_condition_is_first_memory_in_discard_true(self, ee_and_gs: Tuple[EffectEngine, GameState], base_toy_card_def: Toy):
        effect_engine, game_state = ee_and_gs
        game_state.first_memory_card_definition = base_toy_card_def
        game_state.discard_pile.append(base_toy_card_def)
        game_state.first_memory_current_zone = Zone.DISCARD 

        conditions = [{"condition_type": EffectConditionType.IS_FIRST_MEMORY_IN_DISCARD.name, "params": {}}]
        assert effect_engine._check_conditions(conditions, None, None, None, {}) is True

    def test_check_condition_is_first_memory_in_discard_false(self, ee_and_gs: Tuple[EffectEngine, GameState], base_toy_card_def: Toy, another_toy_card_def: Toy):
        effect_engine, game_state = ee_and_gs
        
        game_state.first_memory_card_definition = base_toy_card_def
        game_state.hand.append(base_toy_card_def) 
        game_state.first_memory_current_zone = Zone.HAND
        conditions = [{"condition_type": EffectConditionType.IS_FIRST_MEMORY_IN_DISCARD.name, "params": {}}]
        assert effect_engine._check_conditions(conditions, None, None, None, {}) is False
        
        game_state.discard_pile.append(another_toy_card_def)
        assert effect_engine._check_conditions(conditions, None, None, None, {}) is False 

        game_state.discard_pile.append(base_toy_card_def) 
        assert effect_engine._check_conditions(conditions, None, None, None, {}) is False 

        game_state.first_memory_current_zone = Zone.DISCARD 
        assert effect_engine._check_conditions(conditions, None, None, None, {}) is True


    def test_check_condition_deck_size_le_true(self, ee_and_gs: Tuple[EffectEngine, GameState], base_toy_card_def: Toy):
        effect_engine, game_state = ee_and_gs
        game_state.deck = [base_toy_card_def for _ in range(5)] 
        conditions = [{"condition_type": EffectConditionType.DECK_SIZE_LE.name, "params": {"count": 5}}]
        assert effect_engine._check_conditions(conditions, None, None, None, {}) is True
        conditions_lower = [{"condition_type": EffectConditionType.DECK_SIZE_LE.name, "params": {"count": 10}}]
        assert effect_engine._check_conditions(conditions_lower, None, None, None, {}) is True

    def test_check_condition_deck_size_le_false(self, ee_and_gs: Tuple[EffectEngine, GameState], base_toy_card_def: Toy):
        effect_engine, game_state = ee_and_gs
        game_state.deck = [base_toy_card_def for _ in range(5)] 
        conditions = [{"condition_type": EffectConditionType.DECK_SIZE_LE.name, "params": {"count": 4}}]
        assert effect_engine._check_conditions(conditions, None, None, None, {}) is False


class TestEffectEngineActions:

    def test_execute_action_draw_cards(self, ee_and_gs: Tuple[EffectEngine, GameState]):
        effect_engine, game_state = ee_and_gs
        effect_engine.trigger_effects = MagicMock() 

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
            assert 'action_source_instance' in kwargs['event_context'] # Now expecting these
            assert 'action_source_definition' in kwargs['event_context'] # Now expecting these


    def test_execute_action_draw_cards_empty_deck(self, ee_and_gs: Tuple[EffectEngine, GameState]):
        effect_engine, game_state = ee_and_gs
        effect_engine.trigger_effects = MagicMock() 
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
        effect_engine.trigger_effects = MagicMock() 
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
        effect_engine.trigger_effects = MagicMock() 
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
        count_param = 2
        action_data = {"action_type": EffectActionType.BROWSE_DECK.name, "params": {"count": count_param}}
        effect_engine._execute_action(action_data, None, None, None, None)
        
        assert any(f"Placeholder: AI would browse deck (count: {count_param})" in entry for entry in game_state.game_log)
        assert game_state.deck == initial_deck_order 

    def test_execute_action_unimplemented(self, ee_and_gs: Tuple[EffectEngine, GameState]):
        effect_engine, game_state = ee_and_gs
        action_data = {"action_type": "NON_EXISTENT_ACTION", "params": {}}
        game_state.game_log.clear()
        effect_engine._execute_action(action_data, None, None, None, None)
        assert any("Unknown action type 'NON_EXISTENT_ACTION'" in entry for entry in game_state.game_log if "ERROR" in entry)

    def test_execute_action_place_counter_on_card_self(self, ee_and_gs: Tuple[EffectEngine, GameState], base_toy_card_def: Toy):
        effect_engine, game_state = ee_and_gs
        effect_engine.trigger_effects = MagicMock()
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
        effect_engine.trigger_effects = MagicMock()
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
        _fixture_ee, game_state = ee_and_gs 
        effect_engine = EffectEngine(game_state) 

        card_to_sacrifice = CardInPlay(base_toy_card_def)
        game_state.cards_in_play[card_to_sacrifice.instance_id] = card_to_sacrifice
        
        action_data = {
            "action_type": EffectActionType.SACRIFICE_CARD_IN_PLAY.name,
            "params": {"target_card_instance_id": "SELF"}
        }
        
        effect_engine.trigger_effects = MagicMock()
        effect_engine._execute_action(action_data, card_to_sacrifice, base_toy_card_def, None, {}) 
        
        assert card_to_sacrifice.instance_id not in game_state.cards_in_play
        assert base_toy_card_def in game_state.discard_pile
        
        calls = effect_engine.trigger_effects.call_args_list
        
        expected_before_leave_ctx = {
            'card_instance_leaving_play': card_to_sacrifice, 
            'destination_zone': Zone.DISCARD, 
            'cancel_leave_play': False, 
            'original_zone': Zone.IN_PLAY, 
            'action_source_instance': card_to_sacrifice, 
            'action_source_definition': base_toy_card_def
        }
        assert call(EffectTriggerType.BEFORE_THIS_CARD_LEAVES_PLAY, source_card_instance_for_trigger=card_to_sacrifice, event_context=expected_before_leave_ctx) in calls
        
        expected_after_triggers_ctx = {
            'sacrificed_card_definition': base_toy_card_def, 
            'original_instance_id': card_to_sacrifice.instance_id,
            'destination_zone': Zone.DISCARD,
            'action_source_instance': card_to_sacrifice,
            'action_source_definition': base_toy_card_def
        }
        assert any(c == call(EffectTriggerType.ON_LEAVE_PLAY, source_card_definition_for_trigger=base_toy_card_def, event_context=expected_after_triggers_ctx) for c in calls)
        assert any(c == call(EffectTriggerType.ON_SACRIFICE_THIS_CARD, source_card_definition_for_trigger=base_toy_card_def, event_context=expected_after_triggers_ctx) for c in calls)
        
        expected_other_leaves_ctx = {'left_play_card_definition': base_toy_card_def, 'original_instance_id': card_to_sacrifice.instance_id, 'destination_zone': Zone.DISCARD}
        assert any(c == call(EffectTriggerType.WHEN_OTHER_CARD_LEAVES_PLAY, event_context=expected_other_leaves_ctx) for c in calls)
        
        if base_toy_card_def.card_type == CardType.TOY:
             assert any(c == call(EffectTriggerType.WHEN_YOU_SACRIFICE_TOY, event_context=expected_after_triggers_ctx) for c in calls)


    def test_execute_action_return_this_card_to_hand(self, ee_and_gs: Tuple[EffectEngine, GameState], base_toy_card_def: Toy):
        _fixture_ee, game_state = ee_and_gs
        effect_engine = EffectEngine(game_state) 

        card_to_return = CardInPlay(base_toy_card_def)
        game_state.cards_in_play[card_to_return.instance_id] = card_to_return
        initial_hand_size = len(game_state.hand)

        action_data = {"action_type": EffectActionType.RETURN_THIS_CARD_TO_HAND.name, "params": {}}
        
        effect_engine.trigger_effects = MagicMock() 
        effect_engine._execute_action(action_data, card_to_return, base_toy_card_def, None, {})

        assert card_to_return.instance_id not in game_state.cards_in_play
        assert base_toy_card_def in game_state.hand
        assert len(game_state.hand) == initial_hand_size + 1

        calls = effect_engine.trigger_effects.call_args_list
        
        expected_before_leave_ctx = {
            'card_instance_leaving_play': card_to_return, 
            'destination_zone': Zone.HAND, 
            'cancel_leave_play': False, 
            'original_zone': Zone.IN_PLAY, 
            'action_source_instance': card_to_return, 
            'action_source_definition': base_toy_card_def 
        }
        assert call(EffectTriggerType.BEFORE_THIS_CARD_LEAVES_PLAY, source_card_instance_for_trigger=card_to_return, event_context=expected_before_leave_ctx) in calls
        
        expected_on_leave_ctx = { # Corrected expected context
            'returned_card_definition': base_toy_card_def, 
            'original_instance_id': card_to_return.instance_id, 
            'destination_zone': Zone.HAND,
            'action_source_instance': card_to_return, # Now included by engine
            'action_source_definition': base_toy_card_def # Now included by engine
        }
        assert any(c == call(EffectTriggerType.ON_LEAVE_PLAY, source_card_definition_for_trigger=base_toy_card_def, event_context=expected_on_leave_ctx) for c in calls)
        
        expected_other_leave_ctx = {'left_play_card_definition': base_toy_card_def, 'original_instance_id': card_to_return.instance_id, 'destination_zone': Zone.HAND}
        assert any(c == call(EffectTriggerType.WHEN_OTHER_CARD_LEAVES_PLAY, event_context=expected_other_leave_ctx) for c in calls)


    def test_execute_action_mill_deck(self, ee_and_gs: Tuple[EffectEngine, GameState]):
        _fixture_ee, game_state = ee_and_gs
        effect_engine = EffectEngine(game_state) 

        initial_deck_size = len(game_state.deck)
        initial_discard_size = len(game_state.discard_pile)
        if initial_deck_size < 2: game_state.deck.extend([Toy(card_id="TEMP_MILL1", name="Mill Fodder 1", cost=0), Toy(card_id="TEMP_MILL2", name="Mill Fodder 2", cost=0)])
        initial_deck_size = len(game_state.deck) 
            
        cards_to_mill_defs = game_state.deck[:2]


        action_data = {"action_type": EffectActionType.MILL_DECK.name, "params": {"amount": 2}}
        effect_engine._execute_action(action_data, None, None, None, None)

        assert len(game_state.deck) == initial_deck_size - 2
        assert len(game_state.discard_pile) == initial_discard_size + 2
        for card_def in cards_to_mill_defs: 
            assert card_def in game_state.discard_pile
        
    def test_execute_action_exile_card_from_deck(self, ee_and_gs: Tuple[EffectEngine, GameState]):
        _fixture_ee, game_state = ee_and_gs 
        effect_engine = EffectEngine(game_state) 
        effect_engine.trigger_effects = MagicMock() 

        initial_deck_size = len(game_state.deck)
        initial_exile_size = len(game_state.exile_zone)
        card_to_be_exiled = game_state.deck[0]

        action_data = {"action_type": EffectActionType.EXILE_CARD_FROM_ZONE.name, "params": {"zone": "DECK", "count": 1}}
        effect_engine._execute_action(action_data, None, None, None, None) # source_card_instance and def are None

        assert len(game_state.deck) == initial_deck_size - 1
        assert len(game_state.exile_zone) == initial_exile_size + 1
        assert card_to_be_exiled in game_state.exile_zone
        
        expected_event_context_on_exile = { # Corrected expected context
            'exiled_card_definition': card_to_be_exiled,
            'from_zone': Zone.DECK,
            'action_source_instance': None, # Was None in the call to _execute_action
            'action_source_definition': None # Was None in the call to _execute_action
        }
        effect_engine.trigger_effects.assert_any_call(
            EffectTriggerType.ON_EXILE_THIS_CARD,
            source_card_definition_for_trigger=card_to_be_exiled,
            event_context=expected_event_context_on_exile
        )
        
    def test_execute_action_exile_card_from_hand_random(self, ee_and_gs: Tuple[EffectEngine, GameState], base_toy_card_def: Toy, another_toy_card_def: Toy):
        _fixture_ee, game_state = ee_and_gs 
        effect_engine = EffectEngine(game_state) 
        effect_engine.trigger_effects = MagicMock() 

        card1_in_hand = base_toy_card_def 
        card2_in_hand = another_toy_card_def
        game_state.hand = [card1_in_hand, card2_in_hand] 
        initial_hand_size = len(game_state.hand)
        initial_exile_size = len(game_state.exile_zone)

        action_data = {"action_type": EffectActionType.EXILE_CARD_FROM_ZONE.name, "params": {"zone": "HAND", "count": 1}}
        effect_engine._execute_action(action_data, None, None, None, None) # source_card_instance and def are None

        assert len(game_state.hand) == initial_hand_size - 1
        assert len(game_state.exile_zone) == initial_exile_size + 1
        
        exiled_card = game_state.exile_zone[0]
        assert exiled_card == card1_in_hand or exiled_card == card2_in_hand 
        
        calls = effect_engine.trigger_effects.call_args_list
        expected_event_context_exile_hand = { # Corrected expected context
            'exiled_card_definition': exiled_card,
            'from_zone': Zone.HAND,
            'action_source_instance': None, # Was None in the call to _execute_action
            'action_source_definition': None # Was None in the call to _execute_action
        }
        assert call(EffectTriggerType.WHEN_CARD_EXILED_FROM_HAND, source_card_definition_for_trigger=exiled_card, event_context=expected_event_context_exile_hand) in calls
        assert call(EffectTriggerType.ON_EXILE_THIS_CARD, source_card_definition_for_trigger=exiled_card, event_context=expected_event_context_exile_hand) in calls

    
    def test_execute_action_return_card_from_discard_to_hand_first_memory(self, ee_and_gs: Tuple[EffectEngine, GameState], base_toy_card_def: Toy):
        _fixture_ee, game_state = ee_and_gs
        effect_engine = EffectEngine(game_state) 

        fm_card = base_toy_card_def
        game_state.first_memory_card_definition = fm_card
        game_state.discard_pile.append(fm_card)
        game_state.first_memory_current_zone = Zone.DISCARD
        
        initial_discard_size = len(game_state.discard_pile)
        initial_hand_size = len(game_state.hand)

        action_data = {
            "action_type": EffectActionType.RETURN_CARD_FROM_ZONE_TO_ZONE.name,
            "params": {"card_to_return_id": "FIRST_MEMORY", "from_zone": "DISCARD", "to_zone": "HAND"}
        }
        effect_engine._execute_action(action_data, None, None, None, None)

        assert len(game_state.discard_pile) == initial_discard_size - 1
        assert len(game_state.hand) == initial_hand_size + 1
        assert fm_card in game_state.hand
        assert game_state.first_memory_current_zone == Zone.HAND

    def test_execute_action_return_card_from_discard_to_deck_top(self, ee_and_gs: Tuple[EffectEngine, GameState], base_toy_card_def: Toy):
        _fixture_ee, game_state = ee_and_gs
        effect_engine = EffectEngine(game_state) 

        card_to_move = base_toy_card_def
        if card_to_move not in game_state.discard_pile:
            game_state.discard_pile.append(card_to_move)
        
        initial_discard_size = len(game_state.discard_pile)
        initial_deck_size = len(game_state.deck)
        game_state.game_log = [] 

        action_data = {
            "action_type": EffectActionType.RETURN_CARD_FROM_ZONE_TO_ZONE.name,
            "params": {"card_to_return_id": card_to_move.card_id, "from_zone": "DISCARD", "to_zone": "DECK_TOP"}
        }
        event_ctx_for_action = {'chosen_card_definition': card_to_move} 

        effect_engine._execute_action(action_data, None, None, None, event_context=event_ctx_for_action)
        
        assert len(game_state.discard_pile) == initial_discard_size - 1, \
            f"Discard pile size incorrect. Discard: {[c.name for c in game_state.discard_pile]}"
        assert len(game_state.deck) == initial_deck_size + 1
        assert game_state.deck[0] == card_to_move
        assert any(f"Moved '{card_to_move.name}' from DISCARD to DECK_TOP" in entry for entry in game_state.game_log), \
            "Log message for moving card not found."


    def test_player_choice_yes_no_ai_chooses_yes_cancels_sacrifice(self, ee_and_gs: Tuple[EffectEngine, GameState]):
        _fixture_ee, game_state = ee_and_gs  
        effect_engine = EffectEngine(game_state)  

        ai_player = RandomAI() 
        ai_player.make_choice = MagicMock(return_value=True) 
        game_state.ai_player = ai_player

        echo_bear_card_name = "Echo Bear"
        echo_bear_choice_id = "ECHO_BEAR_SAVE_CHOICE"

        echo_bear_effect = EffectLogic(
            trigger=EffectTriggerType.BEFORE_THIS_CARD_LEAVES_PLAY.name,
            conditions=[],
            actions=[
                {
                    "action_type": EffectActionType.PLAYER_CHOICE.name,
                    "params": {
                        "choice_id": echo_bear_choice_id,
                        "choice_type": PlayerChoiceType.CHOOSE_YES_NO.name,
                        "prompt_text": "Echo Bear would leave play. Create a Memory Token and keep it in play instead?",
                        "on_yes_actions": [
                            {"action_type": EffectActionType.CREATE_MEMORY_TOKENS.name, "params": {"amount": 1}},
                            {"action_type": EffectActionType.CANCEL_IMPENDING_LEAVE_PLAY.name, "params": {}}
                        ],
                        "on_no_actions": [] 
                    }
                }
            ],
            description="When this would leave play, you may create a Memory Token and keep this card in play instead."
        )
        echo_bear_card_def = Toy(card_id="T_ECHO_BEAR", name=echo_bear_card_name, cost=3, card_type=CardType.TOY, quantity_in_deck=1, effect_logic_list=[echo_bear_effect])
        
        echo_bear_instance = CardInPlay(echo_bear_card_def)
        game_state.cards_in_play[echo_bear_instance.instance_id] = echo_bear_instance
        
        initial_memory_tokens = game_state.memory_tokens
        initial_discard_size = len(game_state.discard_pile)
        game_state.game_log.clear()

        sacrifice_action_data = {
            "action_type": EffectActionType.SACRIFICE_CARD_IN_PLAY.name,
            "params": {"target_card_instance_id": echo_bear_instance.instance_id}
        }

        effect_engine._execute_action(sacrifice_action_data, source_card_instance=echo_bear_instance, source_card_definition=echo_bear_card_def, targets=None, event_context={})

        ai_player.make_choice.assert_called_once()
        call_args_list = ai_player.make_choice.call_args_list
        assert len(call_args_list) == 1
        actual_call_args, actual_call_kwargs = call_args_list[0]
        
        assert len(actual_call_args) == 2 
        choice_context_arg = actual_call_args[1]
        assert choice_context_arg['choice_id'] == echo_bear_choice_id
        assert choice_context_arg['choice_type'] == PlayerChoiceType.CHOOSE_YES_NO.name
        assert choice_context_arg['prompt_text'] == "Echo Bear would leave play. Create a Memory Token and keep it in play instead?"

        assert game_state.memory_tokens == initial_memory_tokens + 1, "Memory token should be created"
        assert echo_bear_instance.instance_id in game_state.cards_in_play, "Echo Bear should still be in play"
        assert echo_bear_card_def not in game_state.discard_pile, "Echo Bear should not be in discard pile"
        assert len(game_state.discard_pile) == initial_discard_size, "Discard pile size should not change"

        # Corrected log checks
        assert any(f"EffectEngine: AI for '{echo_bear_choice_id}' chose: True" in log for log in game_state.game_log), "Log for AI choice missing or wrong"
        assert any(f"Action CANCEL_IMPENDING_LEAVE_PLAY for '{echo_bear_card_name}' recorded" in log for log in game_state.game_log), "Log for cancel action missing"
        assert any(f"Sacrifice of '{echo_bear_card_name}'" in log and "was cancelled by an effect" in log for log in game_state.game_log), "Log for sacrifice cancelled missing"
    
    def test_player_choice_yes_no_ai_chooses_no_sacrifices_card(self, ee_and_gs: Tuple[EffectEngine, GameState]):
        _fixture_ee, game_state = ee_and_gs  
        effect_engine = EffectEngine(game_state)  

        ai_player = RandomAI() 
        # Mock the AI to choose NO
        ai_player.make_choice = MagicMock(return_value=False) 
        game_state.ai_player = ai_player

        echo_bear_card_name = "Echo Bear"
        echo_bear_choice_id = "ECHO_BEAR_SAVE_CHOICE_NO" # Unique choice ID for clarity if needed

        echo_bear_effect = EffectLogic(
            trigger=EffectTriggerType.BEFORE_THIS_CARD_LEAVES_PLAY.name,
            conditions=[],
            actions=[
                {
                    "action_type": EffectActionType.PLAYER_CHOICE.name,
                    "params": {
                        "choice_id": echo_bear_choice_id,
                        "choice_type": PlayerChoiceType.CHOOSE_YES_NO.name,
                        "prompt_text": "Echo Bear would leave play. Create a Memory Token and keep it in play instead?",
                        "on_yes_actions": [
                            {"action_type": EffectActionType.CREATE_MEMORY_TOKENS.name, "params": {"amount": 1}},
                            {"action_type": EffectActionType.CANCEL_IMPENDING_LEAVE_PLAY.name, "params": {}}
                        ],
                        "on_no_actions": [ # Example: could add a log action here if desired for "NO" path
                            # {"action_type": EffectActionType.LOG_MESSAGE.name, "params": {"message": "Player chose not to save Echo Bear."}}
                        ] 
                    }
                }
            ],
            description="When this would leave play, you may save it. If not, it is sacrificed."
        )
        echo_bear_card_def = Toy(card_id="T_ECHO_BEAR_NO", name=echo_bear_card_name, cost=3, card_type=CardType.TOY, quantity_in_deck=1, effect_logic_list=[echo_bear_effect])
        
        echo_bear_instance = CardInPlay(echo_bear_card_def)
        game_state.cards_in_play[echo_bear_instance.instance_id] = echo_bear_instance
        
        initial_memory_tokens = game_state.memory_tokens
        initial_discard_size = len(game_state.discard_pile)
        initial_play_size = len(game_state.cards_in_play)
        game_state.game_log.clear()

        sacrifice_action_data = {
            "action_type": EffectActionType.SACRIFICE_CARD_IN_PLAY.name,
            "params": {"target_card_instance_id": echo_bear_instance.instance_id}
        }

        # For this sacrifice, assume the card's own effect is triggering the choice,
        # so source_card_instance for SACRIFICE_CARD_IN_PLAY is the Echo Bear.
        effect_engine._execute_action(sacrifice_action_data, source_card_instance=echo_bear_instance, source_card_definition=echo_bear_card_def, targets=None, event_context={})

        # Assertions
        ai_player.make_choice.assert_called_once()
        call_args_list = ai_player.make_choice.call_args_list
        assert len(call_args_list) == 1
        actual_call_args, actual_call_kwargs = call_args_list[0]
        
        assert len(actual_call_args) == 2 
        choice_context_arg = actual_call_args[1]
        assert choice_context_arg['choice_id'] == echo_bear_choice_id
        assert choice_context_arg['choice_type'] == PlayerChoiceType.CHOOSE_YES_NO.name

        assert game_state.memory_tokens == initial_memory_tokens, "Memory tokens should NOT change"
        assert echo_bear_instance.instance_id not in game_state.cards_in_play, "Echo Bear should NOT be in play"
        assert echo_bear_card_def in game_state.discard_pile, "Echo Bear should be in the discard pile"
        assert len(game_state.cards_in_play) == initial_play_size - 1, "One card should leave play"
        assert len(game_state.discard_pile) == initial_discard_size + 1, "Discard pile should increase by one"

        # Check log for key events
        assert any(f"EffectEngine: AI for '{echo_bear_choice_id}' chose: False" in log for log in game_state.game_log), "Log for AI 'NO' choice missing or wrong"
        assert not any("Action CANCEL_IMPENDING_LEAVE_PLAY for 'Echo Bear' recorded" in log for log in game_state.game_log), "CANCEL action should NOT be logged"
        assert any(f"Sacrificed '{echo_bear_card_name}' (Instance: {echo_bear_instance.instance_id}). Moved to discard pile." in log for log in game_state.game_log), "Log for actual sacrifice missing"
        assert not any(f"Sacrifice of '{echo_bear_card_name}'" in log and "was cancelled by an effect" in log for log in game_state.game_log), "Log for sacrifice CANCELLED should NOT be present"

    def test_player_choice_discard_or_sacrifice_ai_chooses_discard(self, ee_and_gs: Tuple[EffectEngine, GameState], base_toy_card_def: Toy, another_toy_card_def: Toy):
        _fixture_ee, game_state = ee_and_gs
        effect_engine = EffectEngine(game_state) # Fresh engine for real trigger processing

        # --- Setup GameState ---
        card_to_keep_in_hand = base_toy_card_def
        card_to_be_discarded = another_toy_card_def
        game_state.hand = [card_to_keep_in_hand, card_to_be_discarded]
        game_state.spirit_tokens = 2 # Initial spirits
        initial_hand_size = len(game_state.hand)
        initial_discard_size = len(game_state.discard_pile)
        initial_spirits = game_state.spirit_tokens
        game_state.game_log.clear()

        # --- Setup AI ---
        ai_player = RandomAI()
        # Mock AI's make_choice to return "DISCARD" first, then the specific card to discard
        ai_player.make_choice = MagicMock(side_effect=[
            "DISCARD",  # For DISCARD_CARD_OR_SACRIFICE_SPIRIT
            card_to_be_discarded  # For CHOOSE_CARD_FROM_HAND
        ])
        game_state.ai_player = ai_player
        
        # --- Mock trigger_effects on this engine instance to check for ON_DISCARD_THIS_CARD ---
        # This allows us to verify triggers without letting them run wild if they have complex effects
        effect_engine.trigger_effects = MagicMock()

        # --- Define the PLAYER_CHOICE effect (e.g., from Nightmare Creep) ---
        choice_id_main = "NC_DISCARD_OR_SAC_TEST"
        discard_choice_effect = EffectLogic(
            trigger="MANUAL_TEST_TRIGGER", # Not using a real trigger, just resolving this effect directly
            conditions=[],
            actions=[
                {
                    "action_type": EffectActionType.PLAYER_CHOICE.name,
                    "params": {
                        "choice_id": choice_id_main,
                        "choice_type": PlayerChoiceType.DISCARD_CARD_OR_SACRIFICE_SPIRIT.name,
                        "prompt_text": "Nightmare Creep: Discard a card or sacrifice a Spirit.",
                        "options": ["DISCARD", "SACRIFICE_SPIRIT"] # Options for AI if it uses generic list choice
                    }
                }
            ]
        )
        
        # --- Execute the effect ---
        # For this test, we simulate an effect (like Nightmare Creep) that isn't tied to a specific source card's effect list.
        # We pass None for source_card_instance and source_card_definition.
        effect_engine.resolve_effect_logic(discard_choice_effect, source_card_instance=None, source_card_definition=None, event_context={})

        # --- Assertions ---
        # 1. AI's make_choice was called twice
        assert ai_player.make_choice.call_count == 2
        
        # 2. Verify context of the first AI choice (DISCARD_CARD_OR_SACRIFICE_SPIRIT)
        first_call_args = ai_player.make_choice.call_args_list[0][0] # Positional args of first call
        assert len(first_call_args) == 2
        first_choice_context = first_call_args[1]
        assert first_choice_context['choice_id'] == choice_id_main
        assert first_choice_context['choice_type'] == PlayerChoiceType.DISCARD_CARD_OR_SACRIFICE_SPIRIT.name
        assert first_choice_context['options'] == ["DISCARD", "SACRIFICE_SPIRIT"]

        # 3. Verify context of the second AI choice (CHOOSE_CARD_FROM_HAND)
        second_call_args = ai_player.make_choice.call_args_list[1][0] # Positional args of second call
        assert len(second_call_args) == 2
        second_choice_context = second_call_args[1]
        assert second_choice_context['choice_id'] == "discard_card_from_hand_choice" # Default ID from DISCARD_CARDS_CHOSEN_FROM_HAND
        assert second_choice_context['choice_type'] == PlayerChoiceType.CHOOSE_CARD_FROM_HAND.name
        # Options for CHOOSE_CARD_FROM_HAND should have been the state of the hand *before* discard
        # In this test, it's [card_to_keep_in_hand, card_to_be_discarded]
        assert len(second_choice_context['options']) == 2 
        assert card_to_keep_in_hand in second_choice_context['options']
        assert card_to_be_discarded in second_choice_context['options']

        # 4. Card was discarded
        assert card_to_be_discarded not in game_state.hand, "Chosen card should be discarded from hand"
        assert card_to_be_discarded in game_state.discard_pile, "Chosen card should be in discard pile"
        assert len(game_state.hand) == initial_hand_size - 1, "Hand size should decrease by one"
        assert len(game_state.discard_pile) == initial_discard_size + 1, "Discard pile size should increase by one"
        assert card_to_keep_in_hand in game_state.hand, "Other card should remain in hand"

        # 5. Spirit tokens unchanged
        assert game_state.spirit_tokens == initial_spirits, "Spirit tokens should not change"

        # 6. ON_DISCARD_THIS_CARD trigger
        expected_discard_event_ctx = {
            'discarded_card_definition': card_to_be_discarded,
            'reason': 'EFFECT_CHOICE', # As set by DISCARD_CARDS_CHOSEN_FROM_HAND
            'action_source_instance': None, # Since original resolve_effect_logic call had None
            'action_source_definition': None # Since original resolve_effect_logic call had None
        }
        effect_engine.trigger_effects.assert_any_call(
            EffectTriggerType.ON_DISCARD_THIS_CARD,
            source_card_definition_for_trigger=card_to_be_discarded,
            event_context=expected_discard_event_ctx
        )

        # 7. Check relevant log messages (optional, but good for debugging)
        assert any(f"EffectEngine: AI for '{choice_id_main}' chose: DISCARD" in log for log in game_state.game_log)
        assert any(f"EffectEngine: AI chose to discard '{card_to_be_discarded.name}'" in log for log in game_state.game_log)

    def test_player_choice_discard_or_sacrifice_ai_chooses_sacrifice_has_spirits(self, ee_and_gs: Tuple[EffectEngine, GameState], base_toy_card_def: Toy):
        _fixture_ee, game_state = ee_and_gs
        effect_engine = EffectEngine(game_state) # Fresh engine

        # --- Setup GameState ---
        game_state.hand = [base_toy_card_def] # Hand content doesn't matter as much here
        game_state.spirit_tokens = 2 # Player has spirits to sacrifice
        initial_hand_size = len(game_state.hand)
        initial_spirits = game_state.spirit_tokens
        game_state.game_log.clear()

        # --- Setup AI ---
        ai_player = RandomAI()
        # Mock AI's make_choice to return "SACRIFICE_SPIRIT"
        ai_player.make_choice = MagicMock(return_value="SACRIFICE_SPIRIT")
        game_state.ai_player = ai_player
        
        # (Optional) Mock trigger_effects if we wanted to check for a WHEN_SPIRIT_SACRIFICED trigger
        # For this test, we'll focus on the direct outcome of resource sacrifice.
        # effect_engine.trigger_effects = MagicMock() 

        # --- Define the PLAYER_CHOICE effect ---
        choice_id_main = "NC_DISCARD_OR_SAC_TEST_SAC"
        sacrifice_choice_effect = EffectLogic(
            trigger="MANUAL_TEST_TRIGGER_SAC",
            conditions=[],
            actions=[
                {
                    "action_type": EffectActionType.PLAYER_CHOICE.name,
                    "params": {
                        "choice_id": choice_id_main,
                        "choice_type": PlayerChoiceType.DISCARD_CARD_OR_SACRIFICE_SPIRIT.name,
                        "prompt_text": "Nightmare Creep: Discard a card or sacrifice a Spirit.",
                        "options": ["DISCARD", "SACRIFICE_SPIRIT"]
                    }
                }
            ]
        )
        
        # --- Execute the effect ---
        effect_engine.resolve_effect_logic(sacrifice_choice_effect, source_card_instance=None, source_card_definition=None, event_context={})

        # --- Assertions ---
        # 1. AI's make_choice was called once
        ai_player.make_choice.assert_called_once()
        
        # 2. Verify context of the AI choice
        first_call_args = ai_player.make_choice.call_args_list[0][0]
        assert len(first_call_args) == 2
        first_choice_context = first_call_args[1]
        assert first_choice_context['choice_id'] == choice_id_main
        assert first_choice_context['choice_type'] == PlayerChoiceType.DISCARD_CARD_OR_SACRIFICE_SPIRIT.name

        # 3. Spirit tokens decreased
        assert game_state.spirit_tokens == initial_spirits - 1, "Spirit tokens should decrease by one"

        # 4. Hand remains unchanged
        assert len(game_state.hand) == initial_hand_size, "Hand size should not change"
        assert base_toy_card_def in game_state.hand, "Hand content should not change"
        
        # 5. Check relevant log messages
        assert any(f"EffectEngine: AI for '{choice_id_main}' chose: SACRIFICE_SPIRIT" in log for log in game_state.game_log)
        assert any(f"EffectEngine: Sacrificed 1 Spirit token(s)." in log for log in game_state.game_log)

    def test_player_choice_discard_or_sacrifice_ai_chooses_sacrifice_no_spirits(self, ee_and_gs: Tuple[EffectEngine, GameState], base_toy_card_def: Toy):
        _fixture_ee, game_state = ee_and_gs
        effect_engine = EffectEngine(game_state) # Fresh engine

        # --- Setup GameState ---
        game_state.hand = [base_toy_card_def] 
        game_state.spirit_tokens = 0 # Player has NO spirits
        initial_spirits = game_state.spirit_tokens
        game_state.game_log.clear()

        # --- Setup AI ---
        ai_player = RandomAI()
        ai_player.make_choice = MagicMock(return_value="SACRIFICE_SPIRIT")
        game_state.ai_player = ai_player
        
        # --- Define the PLAYER_CHOICE effect ---
        choice_id_main = "NC_DISCARD_OR_SAC_NO_SPIRITS_TEST"
        no_spirits_choice_effect = EffectLogic(
            trigger="MANUAL_TEST_TRIGGER_NO_SPIRITS",
            conditions=[],
            actions=[
                {
                    "action_type": EffectActionType.PLAYER_CHOICE.name,
                    "params": {
                        "choice_id": choice_id_main,
                        "choice_type": PlayerChoiceType.DISCARD_CARD_OR_SACRIFICE_SPIRIT.name,
                        "prompt_text": "Nightmare Creep: Discard a card or sacrifice a Spirit.",
                        "options": ["DISCARD", "SACRIFICE_SPIRIT"]
                    }
                }
            ]
        )
        
        # --- Execute the effect ---
        effect_engine.resolve_effect_logic(no_spirits_choice_effect, source_card_instance=None, source_card_definition=None, event_context={})

        # --- Assertions ---
        # 1. AI's make_choice was called once
        ai_player.make_choice.assert_called_once()
        
        # 2. Verify context of the AI choice
        call_args = ai_player.make_choice.call_args_list[0][0]
        assert len(call_args) == 2
        choice_context_arg = call_args[1]
        assert choice_context_arg['choice_id'] == choice_id_main
        assert choice_context_arg['choice_type'] == PlayerChoiceType.DISCARD_CARD_OR_SACRIFICE_SPIRIT.name

        # 3. Spirit tokens remain 0
        assert game_state.spirit_tokens == 0, "Spirit tokens should remain 0"
        assert game_state.spirit_tokens == initial_spirits, "Spirit tokens should be unchanged from initial 0"
        
        # 4. Check relevant log messages
        assert any(f"EffectEngine: AI for '{choice_id_main}' chose: SACRIFICE_SPIRIT" in log for log in game_state.game_log)
        assert any(f"EffectEngine: No Spirit tokens to sacrifice (needed 1, has 0)." in log for log in game_state.game_log), "Log for no spirits to sacrifice missing"

class TestEffectEngineResolveEffectLogic:

    def test_resolve_effect_logic_conditions_met(self, ee_and_gs: Tuple[EffectEngine, GameState], base_toy_card_def: Toy):
        effect_engine, game_state = ee_and_gs
        effect_engine.trigger_effects = MagicMock()
        test_effect = EffectLogic(
            trigger=EffectTriggerType.ON_PLAY.name, 
            conditions=[{"condition_type": EffectConditionType.IS_FIRST_MEMORY_IN_PLAY.name, "params": {}}],
            actions=[{"action_type": EffectActionType.CREATE_SPIRIT_TOKENS.name, "params": {"amount": 1}}]
        )
        game_state.first_memory_card_definition = base_toy_card_def
        game_state.first_memory_current_zone = Zone.IN_PLAY
        game_state.first_memory_instance_id = "fm_instance_active" 
        
        initial_spirits = game_state.spirit_tokens
        
        effect_engine.resolve_effect_logic(test_effect, source_card_instance=None, source_card_definition=base_toy_card_def, event_context={}) 
        assert game_state.spirit_tokens == initial_spirits + 1
        
        effect_engine.trigger_effects.assert_called_with( 
            EffectTriggerType.WHEN_SPIRIT_CREATED, 
            event_context={'amount': 1, 'action_source_instance': None, 'action_source_definition': base_toy_card_def}
        )


    def test_resolve_effect_logic_conditions_not_met(self, ee_and_gs: Tuple[EffectEngine, GameState], base_toy_card_def: Toy):
        effect_engine, game_state = ee_and_gs
        effect_engine.trigger_effects = MagicMock()
        test_effect = EffectLogic(
            trigger=EffectTriggerType.ON_PLAY.name,
            conditions=[{"condition_type": EffectConditionType.IS_FIRST_MEMORY_IN_PLAY.name, "params": {}}],
            actions=[{"action_type": EffectActionType.CREATE_SPIRIT_TOKENS.name, "params": {"amount": 1}}]
        )
        game_state.first_memory_card_definition = base_toy_card_def
        game_state.first_memory_current_zone = Zone.HAND 
        initial_spirits = game_state.spirit_tokens
        game_state.game_log.clear()

        effect_engine.resolve_effect_logic(test_effect, source_card_definition=base_toy_card_def, event_context={}) 
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
        effect_engine.resolve_effect_logic(test_effect, event_context={}) 
        assert game_state.mana_pool == initial_mana + 10