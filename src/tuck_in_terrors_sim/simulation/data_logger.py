# src/tuck_in_terrors_sim/simulation/data_logger.py
from typing import List, Dict, Any
from ..game_logic.game_state import GameState

class DataLogger:
    """Collects and stores key data points from completed simulation runs."""

    def __init__(self):
        self.simulation_results: List[Dict[str, Any]] = []
# In src/tuck_in_terrors_sim/simulation/data_logger.py, inside the DataLogger class

    def log_simulation_result(self, final_state: GameState):
        """
        Records the outcome of a single game simulation.
        Args:
            final_state: The GameState object at the end of the game.
        """
        if not final_state:
            return

        player_state = final_state.get_active_player_state()
        
        # Extract specific progress metrics for easier analysis
        progress = final_state.objective_progress
        distinct_toys_played = len(progress.get("distinct_toys_played_ids", set()))
        spirits_created = progress.get("spirits_created_total_game", 0)
        mana_from_effects = progress.get("mana_from_card_effects_total_game", 0)

        result = {
            "objective_id": final_state.current_objective.objective_id, # <-- This line is corrected
            "win_status": final_state.win_status,
            "final_turn": final_state.current_turn,
            "memory_tokens": player_state.memory_tokens if player_state else 0,
            "spirit_tokens": player_state.spirit_tokens if player_state else 0,
            "distinct_toys_played": distinct_toys_played,
            "spirits_created": spirits_created,
            "mana_from_effects": mana_from_effects,
        }
        self.simulation_results.append(result)

    def get_results(self) -> List[Dict[str, Any]]:
        """Returns all collected simulation results."""
        return self.simulation_results