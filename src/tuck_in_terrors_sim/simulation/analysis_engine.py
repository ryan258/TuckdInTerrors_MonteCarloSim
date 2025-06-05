# src/tuck_in_terrors_sim/simulation/analysis_engine.py
from typing import List, Dict, Any
from collections import Counter

class AnalysisEngine:
    """Analyzes a collection of simulation results and prints a summary."""

    def _calculate_average(self, data: List[float]) -> float:
        """Helper to safely calculate an average."""
        return sum(data) / len(data) if data else 0

    def calculate_and_print_summary(self, results: List[Dict[str, Any]]):
        """
        Calculates and prints summary statistics from simulation data.
        Args:
            results: A list of simulation result dictionaries from DataLogger.
        """
        total_simulations = len(results)
        if total_simulations == 0:
            print("No simulation results to analyze.")
            return

        print("\n--- Simulation Analysis ---")
        print(f"Total Simulations Run: {total_simulations}")

        # Win/Loss statistics
        win_statuses = [r["win_status"] for r in results]
        status_counts = Counter(win_statuses)

        total_wins = sum(1 for s in win_statuses if "WIN" in s)
        total_losses = total_simulations - total_wins
        win_rate = (total_wins / total_simulations) * 100 if total_simulations > 0 else 0

        print(f"\nWin Rate: {win_rate:.2f}% ({total_wins} Wins / {total_losses} Losses)")

        print("\nOutcome Breakdown:")
        for status, count in sorted(status_counts.items()):
            percentage = (count / total_simulations) * 100
            print(f"- {status}: {count} ({percentage:.2f}%)")

        # Separate results for wins and losses for more detailed analysis
        win_results = [r for r in results if "WIN" in r.get("win_status", "")]
        loss_results = [r for r in results if "LOSS" in r.get("win_status", "")]

        avg_win_turn = self._calculate_average([r["final_turn"] for r in win_results])
        avg_loss_turn = self._calculate_average([r["final_turn"] for r in loss_results])

        print("\nAverage Final Turn:")
        print(f"- For Wins: {avg_win_turn:.2f}")
        print(f"- For Losses: {avg_loss_turn:.2f}")

        # Resource and Progress Analysis
        print("\nAverage Final Resources (for Wins):")
        avg_spirits_win = self._calculate_average([r.get("spirit_tokens", 0) for r in win_results])
        avg_memory_win = self._calculate_average([r.get("memory_tokens", 0) for r in win_results])
        print(f"- Spirit Tokens: {avg_spirits_win:.2f}")
        print(f"- Memory Tokens: {avg_memory_win:.2f}")

        print("\nAverage Objective Progress (at end of all games):")
        avg_toys_played = self._calculate_average([r.get("distinct_toys_played", 0) for r in results])
        avg_spirits_created = self._calculate_average([r.get("spirits_created", 0) for r in results])
        avg_mana_effects = self._calculate_average([r.get("mana_from_effects", 0) for r in results])
        print(f"- Distinct Toys Played: {avg_toys_played:.2f}")
        print(f"- Spirits Created: {avg_spirits_created:.2f}")
        print(f"- Mana from Effects: {avg_mana_effects:.2f}")
        print("-------------------------")