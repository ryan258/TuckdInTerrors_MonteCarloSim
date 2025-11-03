# src/tuck_in_terrors_sim/simulation/balance_analyzer.py
"""
Game Balance Analysis Tools for Tuck'd-In Terrors

Provides advanced analysis capabilities for evaluating game balance across:
- Objectives (win rates, difficulty curves)
- AI strategies (performance comparison)
- Card impact (win rate correlation)
- Game length distribution
"""

from typing import List, Dict, Any, Optional, Tuple
from collections import defaultdict, Counter
import statistics


class BalanceAnalyzer:
    """
    Analyzes simulation results to provide insights into game balance.
    """

    def __init__(self):
        self.results: List[Dict[str, Any]] = []

    def add_results(self, results: List[Dict[str, Any]]):
        """Add simulation results for analysis."""
        self.results.extend(results)

    def clear_results(self):
        """Clear all stored results."""
        self.results = []

    def analyze_objective_difficulty(self, objective_id: str) -> Dict[str, Any]:
        """
        Analyze the difficulty of a specific objective.

        Returns:
            Dictionary with:
            - win_rate: Overall win rate
            - avg_turns_to_win: Average turns when winning
            - avg_turns_to_loss: Average turns when losing
            - primary_win_rate: Rate of primary win condition
            - alternative_win_rate: Rate of alternative win condition
            - loss_breakdown: Distribution of loss reasons
        """
        obj_results = [r for r in self.results if r.get("objective_id") == objective_id]

        if not obj_results:
            return {"error": f"No results found for objective {objective_id}"}

        total_games = len(obj_results)
        wins = [r for r in obj_results if r.get("win_status", "").startswith("PRIMARY_WIN") or r.get("win_status", "").startswith("ALTERNATIVE_WIN")]
        losses = [r for r in obj_results if r.get("win_status", "").startswith("LOSS")]

        win_rate = len(wins) / total_games if total_games > 0 else 0

        # Win condition breakdown
        primary_wins = len([r for r in obj_results if r.get("win_status") == "PRIMARY_WIN"])
        alt_wins = len([r for r in obj_results if r.get("win_status") == "ALTERNATIVE_WIN"])

        # Turn counts
        win_turns = [r.get("turns_taken", 0) for r in wins if r.get("turns_taken")]
        loss_turns = [r.get("turns_taken", 0) for r in losses if r.get("turns_taken")]

        avg_turns_win = statistics.mean(win_turns) if win_turns else 0
        avg_turns_loss = statistics.mean(loss_turns) if loss_turns else 0

        # Loss breakdown
        loss_reasons = Counter(r.get("win_status", "UNKNOWN") for r in losses)

        return {
            "objective_id": objective_id,
            "total_games": total_games,
            "win_rate": round(win_rate, 4),
            "wins": len(wins),
            "losses": len(losses),
            "primary_win_rate": round(primary_wins / total_games, 4) if total_games > 0 else 0,
            "alternative_win_rate": round(alt_wins / total_games, 4) if total_games > 0 else 0,
            "avg_turns_to_win": round(avg_turns_win, 2),
            "avg_turns_to_loss": round(avg_turns_loss, 2),
            "median_turns_to_win": statistics.median(win_turns) if win_turns else 0,
            "median_turns_to_loss": statistics.median(loss_turns) if loss_turns else 0,
            "loss_breakdown": dict(loss_reasons),
        }

    def compare_ai_performance(self, objective_id: Optional[str] = None) -> Dict[str, Dict[str, Any]]:
        """
        Compare performance of different AI profiles.

        Args:
            objective_id: Optional - filter by specific objective

        Returns:
            Dictionary mapping AI profile names to their performance metrics
        """
        results_to_analyze = self.results
        if objective_id:
            results_to_analyze = [r for r in self.results if r.get("objective_id") == objective_id]

        # Group by AI profile
        ai_groups = defaultdict(list)
        for result in results_to_analyze:
            ai_profile = result.get("ai_profile", "unknown")
            ai_groups[ai_profile].append(result)

        comparison = {}
        for ai_profile, ai_results in ai_groups.items():
            total = len(ai_results)
            wins = [r for r in ai_results if r.get("win_status", "").startswith("PRIMARY") or r.get("win_status", "").startswith("ALTERNATIVE")]

            win_turns = [r.get("turns_taken", 0) for r in wins if r.get("turns_taken")]
            all_turns = [r.get("turns_taken", 0) for r in ai_results if r.get("turns_taken")]

            comparison[ai_profile] = {
                "total_games": total,
                "wins": len(wins),
                "win_rate": round(len(wins) / total, 4) if total > 0 else 0,
                "avg_turns_overall": round(statistics.mean(all_turns), 2) if all_turns else 0,
                "avg_turns_to_win": round(statistics.mean(win_turns), 2) if win_turns else 0,
                "fastest_win": min(win_turns) if win_turns else None,
                "slowest_win": max(win_turns) if win_turns else None,
            }

        return comparison

    def analyze_win_rate_by_turn(self, objective_id: Optional[str] = None, max_turn: int = 20) -> Dict[int, float]:
        """
        Calculate cumulative win rate by turn number.

        Args:
            objective_id: Optional - filter by specific objective
            max_turn: Maximum turn to analyze

        Returns:
            Dictionary mapping turn number to cumulative win rate
        """
        results_to_analyze = self.results
        if objective_id:
            results_to_analyze = [r for r in self.results if r.get("objective_id") == objective_id]

        wins_by_turn = defaultdict(int)
        total_games = len(results_to_analyze)

        for result in results_to_analyze:
            if result.get("win_status", "").startswith("PRIMARY") or result.get("win_status", "").startswith("ALTERNATIVE"):
                turn = result.get("turns_taken", 0)
                if turn <= max_turn:
                    wins_by_turn[turn] += 1

        # Calculate cumulative win rates
        cumulative_wins = 0
        win_rate_by_turn = {}

        for turn in range(1, max_turn + 1):
            cumulative_wins += wins_by_turn.get(turn, 0)
            win_rate_by_turn[turn] = round(cumulative_wins / total_games, 4) if total_games > 0 else 0

        return win_rate_by_turn

    def identify_outliers(self, objective_id: Optional[str] = None, threshold: float = 2.0) -> Dict[str, List[Dict[str, Any]]]:
        """
        Identify outlier games (unusually fast or slow wins/losses).

        Args:
            objective_id: Optional - filter by specific objective
            threshold: Standard deviations from mean to consider outlier

        Returns:
            Dictionary with 'fast_wins', 'slow_wins', 'fast_losses', 'slow_losses'
        """
        results_to_analyze = self.results
        if objective_id:
            results_to_analyze = [r for r in self.results if r.get("objective_id") == objective_id]

        wins = [r for r in results_to_analyze if r.get("win_status", "").startswith("PRIMARY") or r.get("win_status", "").startswith("ALTERNATIVE")]
        losses = [r for r in results_to_analyze if r.get("win_status", "").startswith("LOSS")]

        def find_outliers(games: List[Dict], label: str) -> Tuple[List[Dict], List[Dict]]:
            if not games:
                return [], []

            turns = [g.get("turns_taken", 0) for g in games if g.get("turns_taken")]
            if len(turns) < 3:
                return [], []

            mean_turns = statistics.mean(turns)
            stdev_turns = statistics.stdev(turns)

            fast = [g for g in games if g.get("turns_taken") and g["turns_taken"] < (mean_turns - threshold * stdev_turns)]
            slow = [g for g in games if g.get("turns_taken") and g["turns_taken"] > (mean_turns + threshold * stdev_turns)]

            return fast, slow

        fast_wins, slow_wins = find_outliers(wins, "wins")
        fast_losses, slow_losses = find_outliers(losses, "losses")

        return {
            "fast_wins": fast_wins,
            "slow_wins": slow_wins,
            "fast_losses": fast_losses,
            "slow_losses": slow_losses,
        }

    def generate_balance_report(self, objective_id: Optional[str] = None) -> str:
        """
        Generate a comprehensive text report on game balance.

        Args:
            objective_id: Optional - focus on specific objective

        Returns:
            Formatted string report
        """
        results_to_analyze = self.results
        if objective_id:
            results_to_analyze = [r for r in self.results if r.get("objective_id") == objective_id]

        if not results_to_analyze:
            return "No results available for analysis."

        report_lines = []
        report_lines.append("=" * 80)
        report_lines.append("GAME BALANCE ANALYSIS REPORT")
        report_lines.append("=" * 80)
        report_lines.append("")

        # Overall statistics
        total = len(results_to_analyze)
        wins = len([r for r in results_to_analyze if r.get("win_status", "").startswith("PRIMARY") or r.get("win_status", "").startswith("ALTERNATIVE")])
        win_rate = wins / total if total > 0 else 0

        report_lines.append(f"Total Games Analyzed: {total}")
        report_lines.append(f"Overall Win Rate: {win_rate:.2%}")
        report_lines.append("")

        # Objective difficulty (if analyzing multiple objectives)
        objectives = set(r.get("objective_id") for r in results_to_analyze if r.get("objective_id"))
        if len(objectives) > 1:
            report_lines.append("OBJECTIVE DIFFICULTY COMPARISON")
            report_lines.append("-" * 80)
            for obj_id in sorted(objectives):
                obj_analysis = self.analyze_objective_difficulty(obj_id)
                report_lines.append(f"\n{obj_id}:")
                report_lines.append(f"  Win Rate: {obj_analysis['win_rate']:.2%} ({obj_analysis['wins']} wins / {obj_analysis['total_games']} games)")
                report_lines.append(f"  Avg Turns to Win: {obj_analysis['avg_turns_to_win']:.1f}")
                report_lines.append(f"  Avg Turns to Loss: {obj_analysis['avg_turns_to_loss']:.1f}")
                report_lines.append(f"  Primary Win Rate: {obj_analysis['primary_win_rate']:.2%}")
                report_lines.append(f"  Alternative Win Rate: {obj_analysis['alternative_win_rate']:.2%}")
            report_lines.append("")

        # AI Performance Comparison
        ai_comparison = self.compare_ai_performance(objective_id)
        if len(ai_comparison) > 1:
            report_lines.append("AI PERFORMANCE COMPARISON")
            report_lines.append("-" * 80)
            for ai_name, metrics in sorted(ai_comparison.items(), key=lambda x: x[1]['win_rate'], reverse=True):
                report_lines.append(f"\n{ai_name}:")
                report_lines.append(f"  Win Rate: {metrics['win_rate']:.2%} ({metrics['wins']} / {metrics['total_games']})")
                report_lines.append(f"  Avg Turns to Win: {metrics['avg_turns_to_win']:.1f}")
                if metrics['fastest_win']:
                    report_lines.append(f"  Fastest Win: Turn {metrics['fastest_win']}")
                    report_lines.append(f"  Slowest Win: Turn {metrics['slowest_win']}")
            report_lines.append("")

        # Turn distribution
        report_lines.append("WIN RATE BY TURN (Cumulative)")
        report_lines.append("-" * 80)
        win_rate_by_turn = self.analyze_win_rate_by_turn(objective_id, max_turn=15)
        for turn in sorted(win_rate_by_turn.keys())[:10]:
            rate = win_rate_by_turn[turn]
            bar = "█" * int(rate * 50)
            report_lines.append(f"  Turn {turn:2d}: {rate:6.2%} {bar}")
        report_lines.append("")

        # Outliers
        outliers = self.identify_outliers(objective_id)
        if outliers["fast_wins"] or outliers["slow_wins"]:
            report_lines.append("NOTABLE OUTLIERS")
            report_lines.append("-" * 80)
            if outliers["fast_wins"]:
                report_lines.append(f"  Unusually Fast Wins: {len(outliers['fast_wins'])} games")
                fastest = min(outliers['fast_wins'], key=lambda x: x.get('turns_taken', 999))
                report_lines.append(f"    Fastest: Turn {fastest.get('turns_taken')} ({fastest.get('ai_profile', 'unknown')} AI)")
            if outliers["slow_wins"]:
                report_lines.append(f"  Unusually Slow Wins: {len(outliers['slow_wins'])} games")
                slowest = max(outliers['slow_wins'], key=lambda x: x.get('turns_taken', 0))
                report_lines.append(f"    Slowest: Turn {slowest.get('turns_taken')} ({slowest.get('ai_profile', 'unknown')} AI)")
            report_lines.append("")

        report_lines.append("=" * 80)
        report_lines.append("END OF REPORT")
        report_lines.append("=" * 80)

        return "\n".join(report_lines)

    def export_balance_data(self, objective_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Export all balance analysis data in structured format for external tools.

        Returns:
            Dictionary with all analysis results
        """
        return {
            "objectives": {obj_id: self.analyze_objective_difficulty(obj_id)
                          for obj_id in set(r.get("objective_id") for r in self.results if r.get("objective_id"))},
            "ai_comparison": self.compare_ai_performance(objective_id),
            "win_rate_by_turn": self.analyze_win_rate_by_turn(objective_id),
            "outliers": self.identify_outliers(objective_id),
            "total_games_analyzed": len(self.results),
        }


if __name__ == '__main__':
    print("BalanceAnalyzer module: Advanced game balance analysis tools.")
    print("Usage:")
    print("  analyzer = BalanceAnalyzer()")
    print("  analyzer.add_results(simulation_results)")
    print("  print(analyzer.generate_balance_report())")
