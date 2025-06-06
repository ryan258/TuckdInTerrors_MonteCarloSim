# src/tuck_in_terrors_sim/simulation/simulation_runner.py

import copy
from typing import Optional, Tuple, List

# Game data and elements
from ..game_elements.data_loaders import GameData
from ..game_elements.enums import Zone, EffectTriggerType

# Game logic components
from ..game_logic.game_state import GameState
from ..game_logic.game_setup import initialize_new_game, DEFAULT_PLAYER_ID
from ..game_logic.win_loss_checker import WinLossChecker
from ..game_logic.effect_engine import EffectEngine
from ..game_logic.action_resolver import ActionResolver
from ..game_logic.nightmare_creep import NightmareCreepModule
from ..game_logic.turn_manager import TurnManager

# AI
from ..ai.ai_player_base import AIPlayerBase
from ..ai.ai_profiles.random_ai import RandomAI
from ..ai.ai_profiles.greedy_ai import GreedyAI
from ..ai.ai_profiles.scoring_ai import ScoringAI


class SimulationRunner:
    """Orchestrates running one or more game simulations."""

    def __init__(self, game_data: GameData):
        self.game_data = game_data

    def _get_ai_profile(self, ai_profile_name: str, player_id: int) -> Optional[AIPlayerBase]:
        """Factory function to get an AI player instance by name."""
        if ai_profile_name == "random_ai":
            return RandomAI(player_id=player_id)
        elif ai_profile_name == "greedy_ai":
            return GreedyAI(player_id=player_id)
        elif ai_profile_name == "scoring_ai":
            return ScoringAI(player_id=player_id)
        else:
            print(f"Warning: Unknown AI profile '{ai_profile_name}'.")
            return None

    def run_one_game(self, objective_id: str, ai_profile_name: str, detailed_logging: bool = False) -> Tuple[Optional[GameState], List[GameState]]:
        """
        Runs a single complete game simulation from setup to a win/loss condition.
        """
        objective = self.game_data.get_objective_by_id(objective_id)
        if not objective:
            return None, []

        game_state = initialize_new_game(objective, self.game_data.cards_by_id)
        game_snapshots: List[GameState] = []

        ai_player = self._get_ai_profile(ai_profile_name, DEFAULT_PLAYER_ID)
        if not ai_player:
            return None, []
        game_state.ai_agents[DEFAULT_PLAYER_ID] = ai_player

        win_loss_checker = WinLossChecker(game_state)
        effect_engine = EffectEngine(game_state, win_loss_checker)
        action_resolver = ActionResolver(game_state, effect_engine, win_loss_checker)
        nightmare_module = NightmareCreepModule(game_state, effect_engine)
        turn_manager = TurnManager(
            game_state=game_state,
            action_resolver=action_resolver,
            effect_engine=effect_engine,
            nightmare_module=nightmare_module,
            win_loss_checker=win_loss_checker
        )

        active_player_state = game_state.get_active_player_state()
        if active_player_state:
            cards_starting_in_play = list(active_player_state.zones[Zone.IN_PLAY])
            for card_instance in cards_starting_in_play:
                for effect in card_instance.definition.effects:
                    if effect.trigger == EffectTriggerType.ON_PLAY:
                        effect_engine.resolve_effect(
                            effect=effect, game_state=game_state, player=active_player_state,
                            source_card_instance=card_instance
                        )
        if win_loss_checker.check_all_conditions():
            game_state.game_over = True

        if detailed_logging:
            game_snapshots.append(copy.deepcopy(game_state))

        max_turns = 100
        while not game_state.game_over and game_state.current_turn <= max_turns:
            turn_manager.execute_full_turn()
            if detailed_logging:
                game_snapshots.append(copy.deepcopy(game_state))

        if game_state.current_turn > max_turns and not game_state.game_over:
            game_state.add_log_entry(f"Simulation ended: Exceeded max turns ({max_turns}).", "SIM_WARNING")
            game_state.game_over = True
            game_state.win_status = "LOSS_MAX_TURNS"

        return game_state, game_snapshots