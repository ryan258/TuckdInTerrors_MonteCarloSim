# src/tuck_in_terrors_sim/simulation/scorecard_generator.py
"""
Scorecard Generator for Tuck'd-In Terrors Simulator

Generates concise, visual scorecards with insights after each simulation run.
"""

from typing import List, Dict, Any, Optional
from collections import Counter
import statistics


class ScorecardGenerator:
    """
    Generates executive-summary style scorecards from simulation results.
    """

    # Difficulty thresholds for insights
    DIFFICULTY_TARGETS = {
        "Easy": (0.40, 0.60),
        "EASY": (0.40, 0.60),
        "Moderate": (0.25, 0.40),
        "MODERATE": (0.25, 0.40),
        "Hard": (0.10, 0.25),
        "HARD": (0.10, 0.25),
    }

    def __init__(self):
        pass

    def generate_scorecard(self, results: List[Dict[str, Any]],
                          objective_id: str,
                          ai_profile: str,
                          objective_difficulty: Optional[str] = None) -> str:
        """
        Generate a comprehensive scorecard from simulation results.

        Args:
            results: List of simulation result dictionaries
            objective_id: The objective being tested
            ai_profile: AI profile used
            objective_difficulty: Expected difficulty level (Easy/Moderate/Hard)

        Returns:
            Formatted scorecard string
        """
        if not results:
            return "No results to generate scorecard."

        # Calculate statistics
        stats = self._calculate_statistics(results)

        # Generate scorecard sections
        scorecard = []
        scorecard.append(self._generate_header(objective_id, ai_profile, len(results)))
        scorecard.append(self._generate_performance_summary(stats))
        scorecard.append(self._generate_visual_metrics(stats))
        scorecard.append(self._generate_insights(stats, objective_difficulty, ai_profile))
        scorecard.append(self._generate_recommendations(stats, objective_difficulty))
        scorecard.append(self._generate_footer())

        return "\n".join(scorecard)

    def _calculate_statistics(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate all necessary statistics from results."""
        total_games = len(results)

        # Win/Loss counts
        wins = [r for r in results if r.get("win_status", "").startswith("PRIMARY_WIN") or
                r.get("win_status", "").startswith("ALTERNATIVE_WIN")]
        losses = [r for r in results if r.get("win_status", "").startswith("LOSS")]

        win_count = len(wins)
        loss_count = len(losses)
        win_rate = win_count / total_games if total_games > 0 else 0

        # Primary vs Alternative wins
        primary_wins = len([r for r in results if r.get("win_status") == "PRIMARY_WIN"])
        alt_wins = len([r for r in results if r.get("win_status") == "ALTERNATIVE_WIN"])

        # Turn statistics
        win_turns = [r.get("turns_taken", 0) for r in wins if r.get("turns_taken")]
        loss_turns = [r.get("turns_taken", 0) for r in losses if r.get("turns_taken")]
        all_turns = [r.get("turns_taken", 0) for r in results if r.get("turns_taken")]

        avg_win_turns = statistics.mean(win_turns) if win_turns else 0
        avg_loss_turns = statistics.mean(loss_turns) if loss_turns else 0
        median_win_turns = statistics.median(win_turns) if win_turns else 0

        fastest_win = min(win_turns) if win_turns else None
        slowest_win = max(win_turns) if win_turns else None

        # Loss reasons
        loss_reasons = Counter(r.get("win_status", "UNKNOWN") for r in losses)

        # Resource statistics
        avg_mana_wins = statistics.mean([r.get("final_mana", 0) for r in wins]) if wins else 0
        avg_spirits_wins = statistics.mean([r.get("final_spirits", 0) for r in wins]) if wins else 0
        avg_toys_wins = statistics.mean([r.get("toys_played", 0) for r in wins]) if wins else 0

        # Consistency (standard deviation of win turns)
        win_turn_stdev = statistics.stdev(win_turns) if len(win_turns) > 1 else 0

        return {
            "total_games": total_games,
            "win_count": win_count,
            "loss_count": loss_count,
            "win_rate": win_rate,
            "primary_wins": primary_wins,
            "alt_wins": alt_wins,
            "avg_win_turns": avg_win_turns,
            "avg_loss_turns": avg_loss_turns,
            "median_win_turns": median_win_turns,
            "fastest_win": fastest_win,
            "slowest_win": slowest_win,
            "loss_reasons": dict(loss_reasons),
            "avg_mana_wins": avg_mana_wins,
            "avg_spirits_wins": avg_spirits_wins,
            "avg_toys_wins": avg_toys_wins,
            "win_turn_stdev": win_turn_stdev,
            "all_turns": all_turns,
        }

    def _generate_header(self, objective_id: str, ai_profile: str, total_games: int) -> str:
        """Generate scorecard header."""
        return f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                          SIMULATION SCORECARD                                ║
╚══════════════════════════════════════════════════════════════════════════════╝

Objective: {objective_id}
AI Profile: {ai_profile}
Games Simulated: {total_games:,}
"""

    def _generate_performance_summary(self, stats: Dict[str, Any]) -> str:
        """Generate performance summary section."""
        win_rate_pct = stats["win_rate"] * 100

        # Grade the win rate
        if win_rate_pct >= 50:
            grade = "A"
            grade_color = "★★★★★"
        elif win_rate_pct >= 40:
            grade = "B"
            grade_color = "★★★★☆"
        elif win_rate_pct >= 30:
            grade = "C"
            grade_color = "★★★☆☆"
        elif win_rate_pct >= 20:
            grade = "D"
            grade_color = "★★☆☆☆"
        else:
            grade = "F"
            grade_color = "★☆☆☆☆"

        return f"""
┌──────────────────────────────────────────────────────────────────────────────┐
│ PERFORMANCE SUMMARY                                                          │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Overall Win Rate:  {win_rate_pct:>6.2f}%   [{self._generate_bar(stats["win_rate"], 40)}]  │
│  Performance Grade: {grade:>6}     {grade_color}                                │
│                                                                              │
│  Wins:              {stats["win_count"]:>6,}   ({stats["win_count"]/stats["total_games"]*100:>5.1f}%)                                 │
│    ├─ Primary:      {stats["primary_wins"]:>6,}   ({stats["primary_wins"]/stats["total_games"]*100:>5.1f}%)                                 │
│    └─ Alternative:  {stats["alt_wins"]:>6,}   ({stats["alt_wins"]/stats["total_games"]*100:>5.1f}%)                                 │
│                                                                              │
│  Losses:            {stats["loss_count"]:>6,}   ({stats["loss_count"]/stats["total_games"]*100:>5.1f}%)                                 │
└──────────────────────────────────────────────────────────────────────────────┘
"""

    def _generate_visual_metrics(self, stats: Dict[str, Any]) -> str:
        """Generate visual metrics section."""
        # Create turn distribution visualization
        turn_viz = self._create_turn_distribution(stats["all_turns"])

        # Loss reason breakdown
        loss_breakdown = ""
        for reason, count in sorted(stats["loss_reasons"].items(), key=lambda x: x[1], reverse=True):
            pct = count / stats["total_games"] * 100
            bar = self._generate_bar(pct / 100, 30)
            loss_breakdown += f"│    {reason:<25} {count:>4} ({pct:>5.1f}%) [{bar}] │\n"

        return f"""
┌──────────────────────────────────────────────────────────────────────────────┐
│ GAME METRICS                                                                 │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Average Turns:                                                              │
│    ├─ Wins:       {stats["avg_win_turns"]:>5.1f} turns  (fastest: {stats["fastest_win"] or 0}, slowest: {stats["slowest_win"] or 0})      │
│    └─ Losses:     {stats["avg_loss_turns"]:>5.1f} turns                                             │
│                                                                              │
│  Win Consistency:  {self._assess_consistency(stats["win_turn_stdev"]):<20}  (σ = {stats["win_turn_stdev"]:.1f})              │
│                                                                              │
│  Average Resources at Win:                                                   │
│    ├─ Mana:       {stats["avg_mana_wins"]:>5.1f}                                                     │
│    ├─ Spirits:    {stats["avg_spirits_wins"]:>5.1f}                                                     │
│    └─ Toys:       {stats["avg_toys_wins"]:>5.1f}                                                     │
│                                                                              │
│  Loss Breakdown:                                                             │
{loss_breakdown}│                                                                              │
│  Turn Distribution:                                                          │
{turn_viz}└──────────────────────────────────────────────────────────────────────────────┘
"""

    def _generate_insights(self, stats: Dict[str, Any],
                          difficulty: Optional[str],
                          ai_profile: str) -> str:
        """Generate insights section."""
        insights = []

        # Win rate insight
        win_rate = stats["win_rate"]
        if difficulty and difficulty in self.DIFFICULTY_TARGETS:
            target_min, target_max = self.DIFFICULTY_TARGETS[difficulty]
            if win_rate < target_min:
                insights.append(f"⚠️  Win rate is BELOW target for {difficulty} difficulty ({target_min*100:.0f}-{target_max*100:.0f}%)")
            elif win_rate > target_max:
                insights.append(f"⚠️  Win rate is ABOVE target for {difficulty} difficulty ({target_min*100:.0f}-{target_max*100:.0f}%)")
            else:
                insights.append(f"✓  Win rate is WITHIN target range for {difficulty} difficulty")

        # Turn efficiency insight
        if stats["avg_win_turns"] > 0 and stats["avg_loss_turns"] > 0:
            if stats["avg_win_turns"] < stats["avg_loss_turns"]:
                insights.append("✓  Wins occur faster than losses (efficient strategy)")
            else:
                insights.append("⚠️  Wins take longer than losses (struggling to meet conditions)")

        # Primary vs Alternative insight
        if stats["alt_wins"] > stats["primary_wins"]:
            insights.append("🔄 Alternative win condition is MORE successful than primary")
        elif stats["alt_wins"] > 0:
            insights.append("✓  Both win conditions viable (good objective design)")
        elif stats["primary_wins"] > 0 and stats["alt_wins"] == 0:
            insights.append("⚠️  Only primary win condition being achieved")

        # Consistency insight
        if stats["win_turn_stdev"] < 1.5:
            insights.append("✓  Very consistent win timing (low variance)")
        elif stats["win_turn_stdev"] > 3.0:
            insights.append("⚠️  High variance in win timing (inconsistent strategy)")

        # AI-specific insights
        if ai_profile == "random_ai" and win_rate > 0.4:
            insights.append("⚠️  Random AI winning >40% suggests objective may be too easy")
        elif ai_profile == "scoring_ai" and win_rate < 0.15:
            insights.append("⚠️  Smart AI winning <15% suggests objective may be too hard")

        # Loss reason insight
        most_common_loss = max(stats["loss_reasons"].items(), key=lambda x: x[1])[0] if stats["loss_reasons"] else None
        if most_common_loss == "LOSS_NIGHTFALL":
            insights.append("⏰ Most losses due to Nightfall (time pressure is main challenge)")
        elif most_common_loss == "LOSS_MAX_TURNS":
            insights.append("⚠️  Games hitting max turn limit (possible infinite loop)")

        # Speed insight
        if stats["fastest_win"] and stats["fastest_win"] <= 3:
            insights.append(f"⚡ Fastest win on turn {stats['fastest_win']} (possible rushed strategy)")

        insights_text = "\n".join(f"│  {insight:<76} │" for insight in insights)

        return f"""
┌──────────────────────────────────────────────────────────────────────────────┐
│ KEY INSIGHTS                                                                 │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
{insights_text}
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
"""

    def _generate_recommendations(self, stats: Dict[str, Any],
                                  difficulty: Optional[str]) -> str:
        """Generate recommendations section."""
        recommendations = []

        win_rate = stats["win_rate"]

        # Win rate recommendations
        if difficulty:
            target_min, target_max = self.DIFFICULTY_TARGETS.get(difficulty, (0.25, 0.40))

            if win_rate < target_min * 0.8:  # Significantly below target
                recommendations.append("Consider making objective easier:")
                recommendations.append("  • Extend Nightfall turn by 1-2")
                recommendations.append("  • Reduce win condition requirements")
                recommendations.append("  • Add starting resources (spirits, mana)")
            elif win_rate > target_max * 1.2:  # Significantly above target
                recommendations.append("Consider making objective harder:")
                recommendations.append("  • Reduce Nightfall turn by 1-2")
                recommendations.append("  • Increase win condition requirements")
                recommendations.append("  • Add restrictive special rules")

        # Consistency recommendations
        if stats["win_turn_stdev"] > 3.0:
            recommendations.append("High variance detected:")
            recommendations.append("  • Review card draw mechanics")
            recommendations.append("  • Consider guaranteed starting cards")
            recommendations.append("  • Test with different AI profiles")

        # Alternative win condition recommendations
        if stats["primary_wins"] > 0 and stats["alt_wins"] == 0:
            recommendations.append("Alternative win condition unused:")
            recommendations.append("  • May be too difficult or unclear")
            recommendations.append("  • Consider making it more accessible")

        # Speed recommendations
        if stats["avg_win_turns"] > 10:
            recommendations.append("Games taking many turns to win:")
            recommendations.append("  • Consider more mana generation")
            recommendations.append("  • Review card costs")
            recommendations.append("  • Add card draw effects")

        if not recommendations:
            recommendations.append("No immediate concerns detected!")
            recommendations.append("Objective appears well-balanced for current difficulty.")

        rec_text = "\n".join(f"│  {rec:<76} │" for rec in recommendations)

        return f"""
┌──────────────────────────────────────────────────────────────────────────────┐
│ RECOMMENDATIONS                                                              │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
{rec_text}
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
"""

    def _generate_footer(self) -> str:
        """Generate scorecard footer."""
        return """
╔══════════════════════════════════════════════════════════════════════════════╗
║  Run with --balance-report for detailed statistical analysis                ║
║  Run with --visualize to generate charts                                    ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

    def _generate_bar(self, ratio: float, width: int = 40) -> str:
        """Generate a visual progress bar."""
        filled = int(ratio * width)
        empty = width - filled
        return "█" * filled + "░" * empty

    def _assess_consistency(self, stdev: float) -> str:
        """Assess consistency based on standard deviation."""
        if stdev < 1.5:
            return "Very Consistent"
        elif stdev < 2.5:
            return "Consistent"
        elif stdev < 3.5:
            return "Moderate Variance"
        else:
            return "High Variance"

    def _create_turn_distribution(self, turns: List[int]) -> str:
        """Create a simple turn distribution visualization."""
        if not turns:
            return "│      No data available                                                       │\n"

        # Create bins
        max_turn = max(turns)
        bins = [0] * (max_turn + 1)
        for turn in turns:
            bins[turn] += 1

        max_count = max(bins) if bins else 1

        # Show first 10 turns
        lines = []
        for turn in range(1, min(11, len(bins))):
            count = bins[turn]
            pct = count / len(turns) * 100 if turns else 0
            bar_width = int((count / max_count) * 40) if max_count > 0 else 0
            bar = "█" * bar_width
            lines.append(f"│      Turn {turn:2d}: {pct:5.1f}% [{bar:<40}] │")

        return "\n".join(lines) + "\n"

    def save_scorecard(self, scorecard: str, filename: str):
        """Save scorecard to file."""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(scorecard)
        except Exception as e:
            print(f"Error saving scorecard: {e}")


if __name__ == '__main__':
    print("ScorecardGenerator module: Generate executive summary scorecards.")
