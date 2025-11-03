# Tuck'd-In Terrors: Monte Carlo Simulator

This repository contains a high-performance Monte Carlo simulation platform for the solo card game "Tuck'd-In Terrors." The simulator is designed for deep strategic analysis, AI development, and game balance testing. It allows users to run thousands of game simulations with configurable parameters and receive detailed statistical analysis and visualizations of the results.

## Key Features

- **High-Speed Simulation:** The engine is optimized to run thousands of game simulations per minute, allowing for rapid generation of large datasets.
- **Multiple AI Profiles:** Test and compare different strategies with built-in AI profiles:
  - `random_ai`: Makes completely random valid moves.
  - `greedy_ai`: Prioritizes a single aspect of the win condition.
  - `scoring_ai`: Uses a weighted scoring system to make more balanced, intelligent decisions.
- **All 8 Objectives Implemented:** Complete support for all game objectives with fully functional win condition tracking.
- **31-Card Library:** Comprehensive card collection including Toys, Spells, and Rituals supporting all strategies.
- **Statistical Analysis:** Automatically calculates and displays key metrics after each batch run, including win rates, outcome breakdowns, average game length, and objective-specific progress.
- **Automatic Scorecards:** Every simulation generates an executive-summary scorecard with performance grades, visual metrics, key insights, and actionable recommendations.
- **Game Balance Analysis:** Advanced balance analyzer with objective difficulty comparison, AI performance metrics, win rate curves, and outlier detection.
- **Data Export:** Save the detailed results of every game in a simulation batch to a structured JSON file for external analysis.
- **Result Visualization:** Automatically generate and save plots, including win/loss pie charts and game length histograms, to visually interpret the results.
- **Deep Dive Logging:** Isolate and analyze AI behavior with a detailed, turn-by-turn "play-by-play" report for a specified number of games.

## Installation

This project uses `uv` for package and environment management.

1.  **Install `uv`:**
    If you don't have `uv` installed, follow the official installation instructions for your operating system. For example:

    ```bash
    # macOS / Linux
    curl -LsSf [https://astral.sh/uv/install.sh](https://astral.sh/uv/install.sh) | sh

    # Windows (Powershell)
    irm [https://astral.sh/uv/install.ps1](https://astral.sh/uv/install.ps1) | iex
    ```

2.  **Clone the repository:**

    ```bash
    git clone [https://github.com/ryan258/tuckdinterrors_montecarlosim.git](https://github.com/ryan258/tuckdinterrors_montecarlosim.git)
    cd tuckdinterrors_montecarlosim
    ```

3.  **Create the virtual environment and install dependencies:**
    `uv` handles creating the environment and installing packages from `requirements.txt` in a single, fast command.
    ```bash
    uv venv
    uv pip install -r requirements.txt
    ```
    To activate the environment, run:
    ```bash
    source .venv/bin/activate # On Windows use `.venv\Scripts\activate`
    ```

## How to Run Simulations

All simulations are run from the command line using `main.py`. Ensure your virtual environment is activated first.

### Basic Run

To run a standard batch of 1000 simulations with the `scoring_ai`:

```bash
python main.py --objective OBJ01_THE_FIRST_NIGHT --simulations 1000 --ai scoring_ai
```

### Game Balance Analysis

Generate a comprehensive balance analysis report:

```bash
python main.py --objective OBJ01_THE_FIRST_NIGHT --simulations 1000 --ai scoring_ai --balance-report
```

This will produce a detailed report including:
- Objective difficulty metrics
- AI performance comparison
- Win rate progression by turn
- Outlier detection (unusually fast/slow games)
- Statistical summaries

The report is displayed in the console and saved to `results/balance_report_<objective>_<ai>.txt`.

### Understanding Your Scorecard

Every simulation automatically generates a scorecard with:
- **Performance Grade** (A-F) based on win rate
- **Visual metrics** with progress bars and turn distributions
- **Key Insights** identifying strengths and concerns
- **Recommendations** for improving objective balance

Example output:
```
╔══════════════════════════════════════════════════════════════════════════════╗
║                          SIMULATION SCORECARD                                ║
╚══════════════════════════════════════════════════════════════════════════════╝

Objective: OBJ01_THE_FIRST_NIGHT
AI Profile: scoring_ai
Games Simulated: 1,000

┌──────────────────────────────────────────────────────────────────────────────┐
│ PERFORMANCE SUMMARY                                                          │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Overall Win Rate:  45.30%   [██████████████████░░░░░░░░░░░░░░░░░░░░░░░░░]  │
│  Performance Grade:      B     ★★★★☆                                         │
│                                                                              │
│  Wins:                453   (45.3%)                                          │
│    ├─ Primary:        420   (42.0%)                                          │
│    └─ Alternative:     33   ( 3.3%)                                          │
│                                                                              │
│  Losses:              547   (54.7%)                                          │
└──────────────────────────────────────────────────────────────────────────────┘

KEY INSIGHTS:
  ✓  Win rate is WITHIN target range for Easy difficulty
  ✓  Wins occur faster than losses (efficient strategy)
  ⏰ Most losses due to Nightfall (time pressure is main challenge)

RECOMMENDATIONS:
  No immediate concerns detected!
  Objective appears well-balanced for current difficulty.
```

To disable the scorecard, use `--no-scorecard` flag.
Scorecards are automatically saved to `results/scorecard_<objective>_<ai>.txt`.
