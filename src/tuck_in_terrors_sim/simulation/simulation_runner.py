# src/tuck_in_terrors_sim/simulation/simulation_runner.py
# Orchestrates running multiple game simulations

from typing import Dict, Any, Optional

# Game data and elements
from ..game_elements.data_loaders import GameData
from ..game_elements.objective import ObjectiveCard

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
# Add other AI profiles here as they are created
# from ..ai.ai_profiles.greedy_ai import GreedyAI

class SimulationRunner:
    """Orchestrates running one or more game simulations."""

    def __init__(self, game_data: GameData):
        """
        Initializes the SimulationRunner with all necessary static game data.
        Args:
            game_data: A GameData object containing all card and objective definitions.
        """
        self.game_data = game_data

    def _get_ai_profile(self, ai_profile_name: str, player_id: int) -> Optional[AIPlayerBase]:
        """Factory function to get an AI player instance by name."""
        if ai_profile_name == "random_ai":
            return RandomAI(player_id=player_id)
        # Add other profiles here
        # elif ai_profile_name == "greedy_ai":
        #     return GreedyAI(player_id=player_id)
        else:
            print(f"Warning: Unknown AI profile '{ai_profile_name}'.")
            return None

    def run_one_game(self, objective_id: str, ai_profile_name: str) -> Optional[GameState]:
        """
        Runs a single complete game simulation from setup to a win/loss condition.
        Args:
            objective_id: The ID of the objective to simulate.
            ai_profile_name: The name of the AI profile to use for the player.
        Returns:
            The final GameState object after the game has concluded, or None if setup fails.
        """
        objective = self.game_data.get_objective_by_id(objective_id)
        if not objective:
            print(f"Error: Objective '{objective_id}' not found.")
            return None

        # 1. Initialize GameState
        game_state = initialize_new_game(objective, self.game_data.cards_by_id)

        # 2. Initialize AI
        ai_player = self._get_ai_profile(ai_profile_name, DEFAULT_PLAYER_ID)
        if not ai_player:
            print(f"Error: Could not create AI profile '{ai_profile_name}'.")
            return None
        game_state.ai_agents[DEFAULT_PLAYER_ID] = ai_player

        # 3. Initialize Game Logic Modules
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

        # 4. Main Game Loop
        game_state.add_log_entry(f"--- Simulation Start: Objective '{objective.title}', AI '{ai_profile_name}' ---", "SIM_INFO")
        max_turns = 100 # Safety break
        while not game_state.game_over and game_state.current_turn <= max_turns:
            turn_manager.execute_full_turn()

        if game_state.current_turn > max_turns:
            game_state.add_log_entry(f"Simulation ended: Exceeded max turns ({max_turns}).", "SIM_WARNING")
            game_state.game_over = True
            game_state.win_status = "LOSS_MAX_TURNS"

        game_state.add_log_entry(f"--- Simulation End: {game_state.win_status} on Turn {game_state.current_turn} ---", "SIM_INFO")
        return game_state