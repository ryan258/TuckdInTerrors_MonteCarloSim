# Tuck'd-In Terrors Monte Carlo Simulator

A Python-based Monte Carlo simulator for the solo card game ""Tuck'd-In Terrors"".

## Setup

1.  Ensure you have uv installed.
2.  Navigate to the project root directory (\$ProjectRootName\).
3.  Create and activate the virtual environment:
    \\\ash
    uv venv
    # On Windows (PowerShell):
    .\.venv\Scripts\Activate.ps1
    # On Linux/macOS:
    # source .venv/bin/activate
    \\\
4.  Install dependencies:
    \\\ash
    uv pip sync pyproject.toml
    # To install dev dependencies as well:
    # uv pip sync pyproject.toml --all-extras
    \\\

## Running Simulations

(Example, assuming main.py is in the root of the project)
\\\ash
python main.py --objective <objective_id> --simulations <number> --ai <ai_profile>
\\\
(Command-line arguments to be implemented)
