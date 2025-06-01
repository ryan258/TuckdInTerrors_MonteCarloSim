# tests/game_logic/test_turn_manager.py
# Unit tests for turn_manager.py

import pytest
from typing import Tuple, List
from unittest.mock import MagicMock, patch

from tuck_in_terrors_sim.game_logic.game_state import GameState, CardInPlay
from tuck_in_terrors_sim.game_logic.turn_manager import TurnManager, STANDARD_MANA_GAIN_PER_TURN_BASE, STANDARD_CARDS_TO_DRAW_PER_TURN, STANDARD_MAX_HAND_SIZE
from tuck_in_terrors_sim.game_logic.effect_engine import EffectEngine
from tuck_in_terrors_sim.game_logic.nightmare_creep import NightmareCreepModule
from tuck_in_terrors_sim.game_logic.win_loss_checker import WinLossChecker
from tuck_in_terrors_sim.game_elements.enums import TurnPhase, EffectTriggerType, CardType 
from tuck_in_terrors_sim.game_elements.card import Card, Toy # Import Toy if used, Card is base for instantiation
from tuck_in_terrors_sim.game_elements.objective import ObjectiveCard

# Fixture 'initialized_game_environment' is defined in tests/conftest.py

class TestTurnManager:

    def test_begin_turn_phase_basic_rules(self, initialized_game_environment: Tuple[GameState, TurnManager, EffectEngine, NightmareCreepModule, WinLossChecker]):
        game_state, turn_manager, effect_engine, nightmare_module, _ = initialized_game_environment
        
        game_state.current_turn = 1 
        initial_mana = game_state.mana_pool 
        initial_deck_size = len(game_state.deck)
        initial_hand_size = len(game_state.hand)

        nightmare_module.apply_nightmare_creep_for_current_turn = MagicMock(return_value=False)
        effect_engine.trigger_effects = MagicMock()

        test_card_def_for_untap = None
        if game_state.all_card_definitions: 
            test_card_def_for_untap = game_state.all_card_definitions.get("TCTOY001") or list(game_state.all_card_definitions.values())[0]
        
        card_in_play_to_untap = None
        if test_card_def_for_untap:
            card_in_play_to_untap = CardInPlay(test_card_def_for_untap) 
            card_in_play_to_untap.tap()
            card_in_play_to_untap.effects_active_this_turn["test_effect"] = True
            card_in_play_to_untap.turns_in_play = 0 
            game_state.cards_in_play[card_in_play_to_untap.instance_id] = card_in_play_to_untap
        
        turn_manager._begin_turn_phase()

        assert game_state.current_phase == TurnPhase.BEGIN_TURN
        assert game_state.free_toy_played_this_turn is False
        assert game_state.storm_count_this_turn == 0

        if game_state.current_turn == 1 and \
           game_state.current_objective.setup_instructions and \
           game_state.current_objective.setup_instructions.params.get("first_turn_mana_override") == 1:
            assert game_state.mana_pool == initial_mana, "Mana should be pre-set for Turn 1 of OBJ01"
        else: 
             assert game_state.mana_pool == initial_mana + game_state.current_turn + STANDARD_MANA_GAIN_PER_TURN_BASE

        if initial_deck_size >= STANDARD_CARDS_TO_DRAW_PER_TURN:
            assert len(game_state.hand) == initial_hand_size + STANDARD_CARDS_TO_DRAW_PER_TURN
            assert len(game_state.deck) == initial_deck_size - STANDARD_CARDS_TO_DRAW_PER_TURN
            # Check if WHEN_CARD_DRAWN was called for each drawn card
            draw_trigger_calls = [
                call for call in effect_engine.trigger_effects.call_args_list 
                if call[1].get('trigger_type') == EffectTriggerType.WHEN_CARD_DRAWN or (call[0] and call[0][0] == EffectTriggerType.WHEN_CARD_DRAWN)
            ]
            assert len(draw_trigger_calls) == STANDARD_CARDS_TO_DRAW_PER_TURN
        else: 
            assert len(game_state.hand) == initial_hand_size + initial_deck_size
            assert len(game_state.deck) == 0
        
        if card_in_play_to_untap:
            assert not card_in_play_to_untap.is_tapped
            assert card_in_play_to_untap.turns_in_play == 1 
            assert not card_in_play_to_untap.effects_active_this_turn

        nightmare_module.apply_nightmare_creep_for_current_turn.assert_called_once()
        effect_engine.trigger_effects.assert_any_call(EffectTriggerType.BEGIN_PLAYER_TURN)


    def test_main_phase_placeholder(self, initialized_game_environment: Tuple[GameState, TurnManager, EffectEngine, NightmareCreepModule, WinLossChecker]):
        game_state, turn_manager, _, _, _ = initialized_game_environment
        mock_ai_player = MagicMock() 

        turn_manager._main_phase(mock_ai_player)
        assert game_state.current_phase == TurnPhase.MAIN_PHASE
        assert any("AI Player taking actions..." in entry for entry in game_state.game_log)


    def test_end_turn_phase_basic_rules(self, initialized_game_environment: Tuple[GameState, TurnManager, EffectEngine, NightmareCreepModule, WinLossChecker]):
        game_state, turn_manager, effect_engine, _, win_loss_checker = initialized_game_environment
        
        game_state.mana_pool = 5
        game_state.hand = [Card(card_id=f"C{i}", name=f"Card {i}", card_type=CardType.TOY, cost=0) for i in range(STANDARD_MAX_HAND_SIZE + 2)] 
        initial_hand_size = len(game_state.hand)
        
        effect_engine.trigger_effects = MagicMock()
        win_loss_checker.check_all_conditions = MagicMock()

        turn_manager._end_turn_phase()

        assert game_state.current_phase == TurnPhase.END_TURN
        assert game_state.mana_pool == 0, "Mana should be lost at end of turn."
        
        assert len(game_state.hand) == STANDARD_MAX_HAND_SIZE
        assert len(game_state.discard_pile) == initial_hand_size - STANDARD_MAX_HAND_SIZE
        
        expected_discard_triggers = initial_hand_size - STANDARD_MAX_HAND_SIZE
        actual_discard_triggers = 0
        for call_obj in effect_engine.trigger_effects.call_args_list:
            args, kwargs = call_obj 
            # trigger_type is the first positional argument to effect_engine.trigger_effects
            if args and isinstance(args[0], EffectTriggerType) and args[0] == EffectTriggerType.ON_DISCARD_THIS_CARD:
                actual_discard_triggers +=1
        
        assert actual_discard_triggers == expected_discard_triggers
        effect_engine.trigger_effects.assert_any_call(EffectTriggerType.END_PLAYER_TURN)
        win_loss_checker.check_all_conditions.assert_called_once()

    def test_execute_full_turn_flow(self, initialized_game_environment: Tuple[GameState, TurnManager, EffectEngine, NightmareCreepModule, WinLossChecker]):
        game_state, turn_manager, _, _, _ = initialized_game_environment
        mock_ai_player = MagicMock()
        
        with patch.object(turn_manager, '_begin_turn_phase', wraps=turn_manager._begin_turn_phase) as mock_begin, \
             patch.object(turn_manager, '_main_phase', wraps=turn_manager._main_phase) as mock_main, \
             patch.object(turn_manager, '_end_turn_phase', wraps=turn_manager._end_turn_phase) as mock_end:
            
            turn_manager.execute_full_turn(mock_ai_player)
            
            mock_begin.assert_called_once()
            mock_main.assert_called_once_with(mock_ai_player)
            mock_end.assert_called_once()
            
        assert not game_state.game_over 
        assert any(f"Turn {game_state.current_turn} concluded." in entry for entry in game_state.game_log)

    def test_execute_full_turn_ends_game_mid_phase(self, initialized_game_environment: Tuple[GameState, TurnManager, EffectEngine, NightmareCreepModule, WinLossChecker]):
        game_state, turn_manager, _, _, _ = initialized_game_environment
        mock_ai_player = MagicMock()

        original_main_phase_method = turn_manager._main_phase # Store reference to original

        def main_phase_ends_game_side_effect(ai_player_arg):
            # This function is the side_effect, it does NOT call the original _main_phase unless we want it to.
            # Here, we just set the game_over state and perhaps minimal logging.
            game_state.add_log_entry("Mocked _main_phase: Setting game_over = True")
            game_state.game_over = True
            game_state.win_status = "TEST_WIN_MAIN_PHASE"
            # Do not call original_main_phase_method(ai_player_arg) to avoid recursion with this patch setup.

        with patch.object(turn_manager, '_begin_turn_phase', wraps=turn_manager._begin_turn_phase) as mock_begin, \
             patch.object(turn_manager, '_main_phase', side_effect=main_phase_ends_game_side_effect) as mock_main_custom, \
             patch.object(turn_manager, '_end_turn_phase') as mock_end: # mock_end does not wrap
            
            turn_manager.execute_full_turn(mock_ai_player)
            
            mock_begin.assert_called_once()
            mock_main_custom.assert_called_once_with(mock_ai_player)
            mock_end.assert_not_called() 
            assert game_state.game_over
            assert game_state.win_status == "TEST_WIN_MAIN_PHASE"