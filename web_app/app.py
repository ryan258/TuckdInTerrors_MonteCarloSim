"""
Flask Web Interface for Tuck'd-In Terrors Monte Carlo Simulator
"""
import sys
import os
import json
import time
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_file
from threading import Thread

# Add parent directory to path to import simulation modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.tuck_in_terrors_sim.game_elements.data_loaders import load_all_game_data
from src.tuck_in_terrors_sim.simulation.simulation_runner import SimulationRunner
from src.tuck_in_terrors_sim.simulation.analysis_engine import AnalysisEngine
from src.tuck_in_terrors_sim.simulation.scorecard_generator import ScorecardGenerator
from src.tuck_in_terrors_sim.simulation.visualizer import Visualizer

app = Flask(__name__)

# Load game data once at startup
print("Loading game data...")
game_data = load_all_game_data()
print(f"Loaded {len(game_data.objectives_by_id)} objectives and {len(game_data.cards)} cards")

# Store simulation results temporarily (in-memory for MVP)
simulation_results = {}
simulation_status = {}

def run_simulation_background(sim_id, objective_id, ai_profile, num_sims, generate_viz):
    """Run simulation in background thread"""
    try:
        simulation_status[sim_id] = {
            'status': 'running',
            'progress': 0,
            'message': 'Initializing simulation...'
        }

        runner = SimulationRunner(game_data)
        all_results = []

        # Run simulations in batches to update progress
        batch_size = max(1, num_sims // 20)  # 20 updates

        for i in range(0, num_sims, batch_size):
            current_batch = min(batch_size, num_sims - i)

            for _ in range(current_batch):
                final_state, game_log = runner.run_one_game(objective_id, ai_profile)

                result_summary = {
                    'objective_id': objective_id,
                    'ai_profile': ai_profile,
                    'win_status': final_state.win_status,
                    'turns_taken': final_state.current_turn,
                    'final_mana': final_state.player_states[0].mana,
                    'final_spirits': final_state.player_states[0].spirit_tokens,
                    'final_memory': final_state.player_states[0].memory_tokens,
                }

                # Add objective-specific progress
                for key, value in final_state.objective_progress.items():
                    if isinstance(value, (int, float, str, bool)):
                        result_summary[key] = value

                all_results.append(result_summary)

            progress = int(((i + current_batch) / num_sims) * 100)
            simulation_status[sim_id] = {
                'status': 'running',
                'progress': progress,
                'message': f'Running simulations: {i + current_batch}/{num_sims}'
            }

        # Generate analysis
        simulation_status[sim_id]['message'] = 'Analyzing results...'

        analysis_engine = AnalysisEngine()
        summary = analysis_engine.generate_summary(all_results)

        # Generate scorecard
        scorecard_gen = ScorecardGenerator()
        objective = game_data.get_objective_by_id(objective_id)
        scorecard = scorecard_gen.generate_scorecard(
            all_results,
            objective,
            ai_profile
        )

        # Generate visualizations if requested
        chart_paths = {}
        if generate_viz:
            simulation_status[sim_id]['message'] = 'Generating visualizations...'
            viz = Visualizer()

            # Ensure results directory exists
            results_dir = Path(__file__).parent.parent / "results"
            results_dir.mkdir(exist_ok=True)

            # Generate charts
            pie_path = viz.generate_win_loss_pie_chart(
                all_results,
                ai_profile,
                str(results_dir / f"web_pie_{sim_id}.png")
            )
            hist_path = viz.generate_turn_distribution_histogram(
                all_results,
                ai_profile,
                str(results_dir / f"web_hist_{sim_id}.png")
            )

            chart_paths = {
                'pie_chart': pie_path,
                'histogram': hist_path
            }

        # Store results
        simulation_results[sim_id] = {
            'raw_results': all_results,
            'summary': summary,
            'scorecard': scorecard,
            'chart_paths': chart_paths,
            'objective_id': objective_id,
            'ai_profile': ai_profile,
            'num_simulations': num_sims
        }

        simulation_status[sim_id] = {
            'status': 'completed',
            'progress': 100,
            'message': 'Simulation completed successfully!'
        }

    except Exception as e:
        simulation_status[sim_id] = {
            'status': 'error',
            'progress': 0,
            'message': f'Error: {str(e)}'
        }
        print(f"Simulation error: {e}")
        import traceback
        traceback.print_exc()


@app.route('/')
def index():
    """Home page with simulation form"""
    objectives = [
        {
            'id': obj_id,
            'name': obj.title,
            'difficulty': obj.difficulty,
            'nightfall': obj.nightfall_turn
        }
        for obj_id, obj in game_data.objectives_by_id.items()
    ]

    ai_profiles = [
        {
            'id': 'random_ai',
            'name': 'Random AI',
            'description': 'Makes random valid moves - baseline for comparison'
        },
        {
            'id': 'greedy_ai',
            'name': 'Greedy AI',
            'description': 'Maximizes immediate win condition value'
        },
        {
            'id': 'scoring_ai',
            'name': 'Scoring AI',
            'description': 'Intelligent weighted scoring - recommended for analysis'
        }
    ]

    return render_template('index.html',
                          objectives=objectives,
                          ai_profiles=ai_profiles)


@app.route('/simulate', methods=['POST'])
def simulate():
    """Start a new simulation"""
    data = request.get_json()

    objective_id = data.get('objective_id')
    ai_profile = data.get('ai_profile', 'random_ai')
    num_simulations = int(data.get('num_simulations', 100))
    generate_viz = data.get('generate_visualizations', False)

    # Validate inputs
    if not objective_id or objective_id not in game_data.objectives_by_id:
        return jsonify({'error': 'Invalid objective ID'}), 400

    if num_simulations < 1 or num_simulations > 10000:
        return jsonify({'error': 'Number of simulations must be between 1 and 10,000'}), 400

    # Generate unique simulation ID
    sim_id = f"sim_{int(time.time() * 1000)}"

    # Start simulation in background thread
    thread = Thread(target=run_simulation_background,
                   args=(sim_id, objective_id, ai_profile, num_simulations, generate_viz))
    thread.daemon = True
    thread.start()

    return jsonify({'simulation_id': sim_id})


@app.route('/status/<sim_id>')
def get_status(sim_id):
    """Get simulation status"""
    if sim_id not in simulation_status:
        return jsonify({'error': 'Simulation not found'}), 404

    return jsonify(simulation_status[sim_id])


@app.route('/results/<sim_id>')
def get_results(sim_id):
    """Get simulation results"""
    if sim_id not in simulation_results:
        return jsonify({'error': 'Results not found'}), 404

    results = simulation_results[sim_id]

    # Return results without raw data for initial load
    return jsonify({
        'summary': results['summary'],
        'scorecard': results['scorecard'],
        'has_charts': len(results['chart_paths']) > 0,
        'objective_id': results['objective_id'],
        'ai_profile': results['ai_profile'],
        'num_simulations': results['num_simulations']
    })


@app.route('/results/<sim_id>/view')
def view_results(sim_id):
    """View results page"""
    if sim_id not in simulation_results:
        return "Results not found", 404

    results = simulation_results[sim_id]
    objective = game_data.get_objective_by_id(results['objective_id'])

    return render_template('results.html',
                          sim_id=sim_id,
                          objective_name=objective.title,
                          objective_difficulty=objective.difficulty,
                          ai_profile=results['ai_profile'],
                          num_simulations=results['num_simulations'])


@app.route('/chart/<sim_id>/<chart_type>')
def get_chart(sim_id, chart_type):
    """Serve chart image"""
    if sim_id not in simulation_results:
        return "Results not found", 404

    results = simulation_results[sim_id]
    chart_paths = results.get('chart_paths', {})

    if chart_type == 'pie' and 'pie_chart' in chart_paths:
        return send_file(chart_paths['pie_chart'], mimetype='image/png')
    elif chart_type == 'histogram' and 'histogram' in chart_paths:
        return send_file(chart_paths['histogram'], mimetype='image/png')

    return "Chart not found", 404


@app.route('/download/<sim_id>')
def download_results(sim_id):
    """Download raw results as JSON"""
    if sim_id not in simulation_results:
        return "Results not found", 404

    results = simulation_results[sim_id]

    # Create temporary file
    results_dir = Path(__file__).parent.parent / "results"
    results_dir.mkdir(exist_ok=True)

    json_path = results_dir / f"web_results_{sim_id}.json"

    with open(json_path, 'w') as f:
        json.dump(results['raw_results'], f, indent=2, default=str)

    return send_file(json_path,
                    mimetype='application/json',
                    as_attachment=True,
                    download_name=f"simulation_results_{results['objective_id']}_{results['ai_profile']}.json")


if __name__ == '__main__':
    print("\n" + "="*80)
    print("Starting Tuck'd-In Terrors Monte Carlo Simulator Web Interface")
    print("="*80)
    print("\nAccess the application at: http://127.0.0.1:5000")
    print("\nPress Ctrl+C to stop the server\n")

    app.run(debug=True, host='127.0.0.1', port=5000)
