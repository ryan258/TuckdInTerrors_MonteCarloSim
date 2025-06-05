# In main.py

import argparse
import json
import os
from tqdm import tqdm

from src.tuck_in_terrors_sim.simulation.simulation_runner import SimulationRunner
from src.tuck_in_terrors_sim.simulation.data_logger import DataLogger
from src.tuck_in_terrors_sim.simulation.analysis_engine import AnalysisEngine
from src.tuck_in_terrors_sim.simulation.visualizer import Visualizer
from src.tuck_in_terrors_sim.game_elements.data_loaders import load_all_game_data

def main_cli():
    parser = argparse.ArgumentParser(description="Run Tuck'd-In Terrors Monte Carlo Simulations.")
    parser.add_argument("--objective", type=str, required=True, help="ID of the objective to simulate (e.g., OBJ01_THE_FIRST_NIGHT).")
    parser.add_argument("--simulations", type=int, default=100, help="Number of simulations to run.")
    parser.add_argument("--ai", type=str, default="random_ai", help="AI profile to use (e.g., random_ai).")
    parser.add_argument("--cards-file", type=str, default="data/cards.json", help="Path to the cards data file.")
    parser.add_argument("--objectives-file", type=str, default="data/objectives.json", help="Path to the objectives data file.")
    parser.add_argument("--verbose", action="store_true", help="Print the full game log of the LAST simulation.")
    parser.add_argument("--output-file", type=str, default=None, help="Filename to save the simulation results as a JSON file.")
    parser.add_argument("--visualize", action="store_true", help="Generate and save plots of the simulation results.")
    parser.add_argument("--output-dir", type=str, default="results", help="Directory to save output files (JSON, plots).")

    args = parser.parse_args()

    if args.output_file or args.visualize:
        if not os.path.exists(args.output_dir):
            os.makedirs(args.output_dir)

    print("Initializing Tuck'd-In Terrors Monte Carlo Simulator...")
    print(f"Objective: {args.objective}, AI: {args.ai}, Simulations: {args.simulations}")

    try:
        game_data = load_all_game_data(args.cards_file, args.objectives_file)
        runner = SimulationRunner(game_data)
        logger = DataLogger()
        analyzer = AnalysisEngine()

        print(f"\n--- Running {args.simulations} simulations ---")
        final_game_state = None 
        for _ in tqdm(range(args.simulations), desc="Simulating Games"):
            final_game_state = runner.run_one_game(args.objective, args.ai)
            logger.log_simulation_result(final_game_state)

        results_data = logger.get_results()
        analyzer.calculate_and_print_summary(results_data)

        if args.output_file:
            # *** FIX IS HERE: Use os.path.basename to handle file paths robustly ***
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

        if args.verbose and final_game_state:
            print("\n--- Full Game Log (Last Simulation) ---")
            for log_entry in final_game_state.game_log:
                print(log_entry)

    except Exception as e:
        import traceback
        print(f"An unexpected error occurred: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    main_cli()