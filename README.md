# Tuck'd-In Terrors: Monte Carlo Simulator

This repository contains a high-performance Monte Carlo simulation platform for the solo card game "Tuck'd-In Terrors." The simulator is designed for deep strategic analysis, AI development, and game balance testing. It allows users to run thousands of game simulations with configurable parameters and receive detailed statistical analysis and visualizations of the results.

## Key Features

- **High-Speed Simulation:** The engine is optimized to run thousands of game simulations per minute, allowing for rapid generation of large datasets.
- **Multiple AI Profiles:** Test and compare different strategies with built-in AI profiles:
  - `random_ai`: Makes completely random valid moves.
  - `greedy_ai`: Prioritizes a single aspect of the win condition.
  - `scoring_ai`: Uses a weighted scoring system to make more balanced, intelligent decisions.
- **Statistical Analysis:** Automatically calculates and displays key metrics after each batch run, including win rates, outcome breakdowns, average game length, and objective-specific progress.
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
