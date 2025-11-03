# main.py

import argparse
import json
import os
import copy
from typing import List
from tqdm import tqdm

from src.tuck_in_terrors_sim.game_elements.enums import Zone
from src.tuck_in_terrors_sim.game_logic.game_state import GameState
from src.tuck_in_terrors_sim.simulation.simulation_runner import SimulationRunner
from src.tuck_in_terrors_sim.simulation.data_logger import DataLogger
from src.tuck_in_terrors_sim.simulation.analysis_engine import AnalysisEngine
from src.tuck_in_terrors_sim.simulation.visualizer import Visualizer
from src.tuck_in_terrors_sim.simulation.balance_analyzer import BalanceAnalyzer
from src.tuck_in_terrors_sim.game_elements.data_loaders import load_all_game_data


def _print_deep_dive_report(game_number: int, snapshots: List[GameState]):
    """Prints a formatted turn-by-turn report for a single simulation."""
    if not snapshots:
        return

    print("\n" + "="*80)
    print(f" DEEP DIVE REPORT: SIMULATION #{game_number}")
    print("="*80)

    last_turn_reported = -1
    for state in snapshots:
        # Don't print the same turn summary multiple times if many things happened
        if state.current_turn == last_turn_reported:
            continue
        last_turn_reported = state.current_turn

        player_state = state.get_active_player_state()
        print(f"\n--- Turn {state.current_turn} (Phase: {state.current_phase.name}) ---")
        if player_state:
            hand_str = ", ".join(sorted([c.definition.name for c in player_state.zones[Zone.HAND]]))
            play_str = ", ".join(sorted([f"{c.definition.name}{' (T)' if c.is_tapped else ''}" for c in player_state.zones[Zone.IN_PLAY]]))

            print(f"  Player: Mana={player_state.mana}, Spirits={player_state.spirit_tokens}, Memory={player_state.memory_tokens}")
            print(f"  Hand ({len(player_state.zones[Zone.HAND])}): [{hand_str}]")
            print(f"  In Play ({len(player_state.zones[Zone.IN_PLAY])}): [{play_str}]")
        print(f"  Objective Progress: {state.objective_progress}")
        print("-" * 40)
        
        # Find logs for the current turn
        turn_logs = [log.split("] ", 1)[1] for log in state.game_log if log.startswith(f"[T{state.current_turn}:")]
        for log_line in turn_logs:
            print(f"    - {log_line}")

    final_state = snapshots[-1]
    print(f"\n--- FINAL OUTCOME: {final_state.win_status} on Turn {final_state.current_turn} ---")
    print("="*80 + "\n")


def main_cli():
    parser = argparse.ArgumentParser(description="Run Tuck'd-In Terrors Monte Carlo Simulations.")
    parser.add_argument("--objective", type=str, required=True, help="ID of the objective to simulate (e.g., OBJ01_THE_FIRST_NIGHT).")
    parser.add_argument("--simulations", type=int, default=1000, help="Number of simulations to run for statistical analysis.")
    parser.add_argument("--ai", type=str, default="random_ai", help="AI profile to use (e.g., random_ai, greedy_ai, scoring_ai).")
    parser.add_argument("--cards-file", type=str, default="data/cards.json", help="Path to the cards data file.")
    parser.add_argument("--objectives-file", type=str, default="data/objectives.json", help="Path to the objectives data file.")
    parser.add_argument("--verbose", action="store_true", help="Print the full game log of the LAST simulation.")
    parser.add_argument("--output-file", type=str, default=None, help="Filename to save the simulation results as a JSON file (e.g., 'results.json').")
    parser.add_argument("--visualize", action="store_true", help="Generate and save plots of the simulation results.")
    parser.add_argument("--output-dir", type=str, default="results", help="Directory to save output files (JSON, plots).")
    parser.add_argument("--deep-dive", type=int, metavar='N', default=0, help="Run N simulations with detailed turn-by-turn logging before the main batch.")
    parser.add_argument("--balance-report", action="store_true", help="Generate a comprehensive game balance analysis report.")

    args = parser.parse_args()

    if args.output_file or args.visualize:
        if not os.path.exists(args.output_dir):
            os.makedirs(args.output_dir)

    print("Initializing Tuck'd-In Terrors Monte Carlo Simulator...")
    print(f"Objective: {args.objective}, AI: {args.ai}, Simulations: {args.simulations}, Deep Dive: {args.deep_dive}")

    try:
        game_data = load_all_game_data(args.cards_file, args.objectives_file)
        runner = SimulationRunner(game_data)
        logger = DataLogger()
        analyzer = AnalysisEngine()

        total_sims_to_run = args.deep_dive + args.simulations

        with tqdm(total=total_sims_to_run, desc="Simulating Games") as pbar:
            if args.deep_dive > 0:
                pbar.set_description(f"Deep Dive (1/{args.deep_dive})")
                for i in range(args.deep_dive):
                    final_state, snapshots = runner.run_one_game(args.objective, args.ai, detailed_logging=True)
                    if final_state:
                        logger.log_simulation_result(final_state)
                    if snapshots:
                        _print_deep_dive_report(i + 1, snapshots)
                    pbar.update(1)
                    if i + 1 < args.deep_dive:
                        pbar.set_description(f"Deep Dive ({i+2}/{args.deep_dive})")

            if args.simulations > 0:
                pbar.set_description("Standard Sims")
                for _ in range(args.simulations):
                    final_state, _ = runner.run_one_game(args.objective, args.ai, detailed_logging=False)
                    if final_state:
                        logger.log_simulation_result(final_state)
                    pbar.update(1)

        results_data = logger.get_results()
        if results_data:
            analyzer.calculate_and_print_summary(results_data)

            # Generate balance report if requested
            if args.balance_report:
                print("\n" + "="*80)
                print("GENERATING GAME BALANCE ANALYSIS REPORT")
                print("="*80 + "\n")
                balance_analyzer = BalanceAnalyzer()
                balance_analyzer.add_results(results_data)
                balance_report = balance_analyzer.generate_balance_report(args.objective)
                print(balance_report)

                # Save balance report to file
                if args.output_dir:
                    balance_file = os.path.join(args.output_dir, f"balance_report_{args.objective}_{args.ai}.txt")
                    try:
                        with open(balance_file, 'w', encoding='utf-8') as f:
                            f.write(balance_report)
                        print(f"\nBalance report saved to: {balance_file}")
                    except Exception as e:
                        print(f"Error saving balance report: {e}")

            if args.output_file:
                filename = os.path.basename(args.output_file)
                file_path = os.path.join(args.output_dir, filename)
                print(f"\nSaving {len(results_data)} simulation results to {file_path}...")
                try:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump(results_data, f, indent=2)
                    print("Save complete.")
                except Exception as e:
                    print(f"Error saving results to file: {e}")

            if args.visualize:
                print("\n--- Generating Visualizations ---")
                visualizer = Visualizer(output_dir=args.output_dir)
                visualizer.plot_win_loss_pie(results_data, args.ai)
                visualizer.plot_turn_distribution_hist(results_data, args.ai)
        else:
            print("\nNo simulations were run to analyze.")

    except Exception as e:
        import traceback
        print(f"\nAn unexpected error occurred: {e}")
        traceback.print_exc()


if __name__ == "__main__":
    main_cli()