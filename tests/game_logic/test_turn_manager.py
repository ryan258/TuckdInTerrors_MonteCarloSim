# tests/game_logic/test_turn_manager.py
import pytest
from unittest.mock import MagicMock, patch
from typing import Tuple, Any, List, Dict

from tuck_in_terrors_sim.game_logic.turn_manager import TurnManager, STANDARD_CARDS_TO_DRAW_PER_TURN, STANDARD_MAX_HAND_SIZE
from tuck_in_terrors_sim.game_logic.game_state import GameState, PlayerState
from tuck_in_terrors_sim.game_logic.effect_engine import EffectEngine
from tuck_in_terrors_sim.game_logic.nightmare_creep import NightmareCreepModule
from tuck_in_terrors_sim.game_logic.win_loss_checker import WinLossChecker
from tuck_in_terrors_sim.game_logic.action_resolver import ActionResolver
from tuck_in_terrors_sim.game_elements.enums import TurnPhase, Zone
from tuck_in_terrors_sim.game_elements.card import Card, CardInstance, Toy # For creating test cards
from tuck_in_terrors_sim.game_elements.objective import ObjectiveCard # For objective setup
from tuck_in_terrors_sim.ai.ai_player_base import AIPlayerBase # For AI mock
from tuck_in_terrors_sim.game_logic.game_setup import DEFAULT_PLAYER_ID

# Assuming initialized_game_environment is defined in conftest.py
# It returns: Tuple[GameState, ActionResolver, EffectEngine, TurnManager, NightmareCreepModule, WinLossChecker]

class TestTurnManager:

    def test_begin_turn_phase_basic_rules(self, initialized_game_environment: Tuple[GameState, ActionResolver, EffectEngine, TurnManager, NightmareCreepModule, WinLossChecker]):
        game_state, _, _, turn_manager, _, _ = initialized_game_environment # Correct unpacking
        player = game_state.get_active_player_state()
        assert player is not None

        # Setup: Card in play tapped, card in hand, mana at 0, some cards in deck
        card_def = game_state.all_card_definitions.get("T_BASE001") or Toy(card_id="TAPPY", name="Tappy", type=CardType.TOY, cost_mana=1)
        tapped_card = CardInstance(definition=card_def, owner_id=player.player_id, current_zone=Zone.IN_PLAY)
        tapped_card.tap()
        game_state.cards_in_play[tapped_card.instance_id] = tapped_card
        player.zones[Zone.IN_PLAY].append(tapped_card)
        
        initial_deck_size = len(player.zones[Zone.DECK])
        if initial_deck_size == 0: # Ensure there's a card to draw
            player.zones[Zone.DECK].append(CardInstance(card_def, player.player_id, Zone.DECK))
            initial_deck_size = 1
            
        initial_hand_size = len(player.zones[Zone.HAND])
        player.mana = 0
        game_state.current_turn = 0 # So it increments to 1

        turn_manager.execute_full_turn() # This will call _begin_turn_phase

        assert game_state.current_phase == TurnPhase.END_TURN # After full turn
        assert tapped_card.is_tapped is False
        assert player.mana >= 1 # Should gain at least 1 mana (current_turn)
        assert len(player.zones[Zone.HAND]) == initial_hand_size + STANDARD_CARDS_TO_DRAW_PER_TURN
        assert len(player.zones[Zone.DECK]) == initial_deck_size - STANDARD_CARDS_TO_DRAW_PER_TURN


    def test_main_phase_ai_passes(self, initialized_game_environment: Tuple[GameState, ActionResolver, EffectEngine, TurnManager, NightmareCreepModule, WinLossChecker]):
        game_state, _, _, turn_manager, _, _ = initialized_game_environment
        active_player_state = game_state.get_active_player_state()
        mock_ai = MagicMock(spec=AIPlayerBase)
        
        # AI's decide_action will return a PASS_TURN GameAction
        pass_action = MagicMock()
        pass_action.type = "PASS_TURN"
        mock_ai.decide_action.return_value = pass_action
        game_state.ai_agents[active_player_state.player_id] = mock_ai # type: ignore

        # Directly call _main_phase (normally called by execute_full_turn)
        turn_manager._main_phase() 
        
        mock_ai.decide_action.assert_called_once() # AI was asked for an action
        assert game_state.current_phase == TurnPhase.MAIN_PHASE # Stays in main until pass is processed by loop
                                                              # or test ends


    def test_end_turn_phase_discard_down(self, initialized_game_environment: Tuple[GameState, ActionResolver, EffectEngine, TurnManager, NightmareCreepModule, WinLossChecker]):
        game_state, _, _, turn_manager, _, _ = initialized_game_environment
        player = game_state.get_active_player_state()
        assert player is not None
        
        card_def = game_state.all_card_definitions.get("T_BASE001") or Toy(card_id="T_DISCARD", name="Discard Fodder", type=CardType.TOY, cost_mana=1)
        # Give player more cards than max hand size
        player.zones[Zone.HAND] = [CardInstance(card_def, player.player_id, Zone.HAND) for _ in range(STANDARD_MAX_HAND_SIZE + 2)]
        initial_mana = player.mana = 5 # Some mana to lose

        turn_manager._end_turn_phase()

        assert player.mana == 0 # Mana lost
        assert len(player.zones[Zone.HAND]) == STANDARD_MAX_HAND_SIZE
        assert game_state.win_loss_checker.check_all_conditions.called # Win/loss checked

    def test_execute_full_turn_flow(self, initialized_game_environment: Tuple[GameState, ActionResolver, EffectEngine, TurnManager, NightmareCreepModule, WinLossChecker]):
        game_state, _, _, turn_manager, _, _ = initialized_game_environment
        mock_ai = game_state.get_active_player_agent() # Get the mock AI from GameState
        assert mock_ai is not None

        # AI passes immediately in main phase
        pass_action = MagicMock()
        pass_action.type = "PASS_TURN"
        mock_ai.decide_action.return_value = pass_action
        
        initial_turn = game_state.current_turn # Should be 0 if fresh from fixture
        
        turn_manager.execute_full_turn()
        
        assert game_state.current_turn == initial_turn + 1
        # Check if all phases were logged (simplified check)
        log_str = "".join(game_state.game_log)
        assert f"Starting Turn {game_state.current_turn}" in log_str
        assert "Begin Phase" in log_str
        assert "Main Phase" in log_str
        assert "End Phase" in log_str