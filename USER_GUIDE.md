# Tuck'd-In Terrors Monte Carlo Simulator: Comprehensive User Guide

**Version:** 0.3.0
**Last Updated:** November 3, 2025

---

## Table of Contents

1. [Introduction](#introduction)
2. [What is Monte Carlo Simulation?](#what-is-monte-carlo-simulation)
3. [Installation](#installation)
4. [Quick Start](#quick-start)
5. [Understanding the Game](#understanding-the-game)
6. [Basic Usage](#basic-usage)
7. [Advanced Features](#advanced-features)
8. [Interpreting Results](#interpreting-results)
9. [Game Balance Analysis](#game-balance-analysis)
10. [AI Strategies](#ai-strategies)
11. [Example Workflows](#example-workflows)
12. [Troubleshooting](#troubleshooting)
13. [Tips and Best Practices](#tips-and-best-practices)
14. [Frequently Asked Questions](#frequently-asked-questions)

---

## Introduction

### What is This?

The **Tuck'd-In Terrors Monte Carlo Simulator** is a high-performance game analysis tool that simulates thousands of games of "Tuck'd-In Terrors" (a solo card game) to provide statistical insights into game balance, strategy effectiveness, and win rates.

### Who is This For?

- **Game Designers:** Analyze balance and difficulty across objectives
- **Strategy Enthusiasts:** Discover optimal play patterns and deck compositions
- **AI Researchers:** Test and develop game-playing algorithms
- **Players:** Understand win conditions and improve your gameplay

### What Can You Do With It?

- Run 1000+ game simulations per minute
- Test all 8 game objectives with different AI strategies
- Generate comprehensive balance reports
- Visualize win rates and game length distributions
- Export detailed data for external analysis
- Deep-dive into specific games with turn-by-turn analysis

---

## What is Monte Carlo Simulation?

### The Concept

Monte Carlo simulation is a computational technique that uses repeated random sampling to obtain numerical results. Instead of playing one game manually, the simulator plays thousands of games automatically and analyzes the outcomes.

### Why Use It?

**Manual Play Problems:**
- Time-consuming (one game takes 10-30 minutes)
- Human bias affects strategy testing
- Small sample sizes lead to unreliable statistics
- Difficult to test edge cases

**Monte Carlo Simulation Benefits:**
- Play 1000+ games in minutes
- Remove human bias with automated AI
- Large sample sizes for reliable statistics
- Systematically explore all game states

### How It Works (Tuck'd-In Terrors Example)

```
1. Setup Game
   ↓
   - Load Objective (e.g., "The First Night")
   - Shuffle 30-card deck
   - Draw starting hand
   - Place First Memory card

2. Simulate Turn
   ↓
   - Begin Turn Phase (untap, draw, gain mana)
   - Main Phase (AI decides actions)
   - End Turn Phase (check win/loss)

3. Repeat Until Game Ends
   ↓
   - Win condition met (Primary/Alternative)
   - Loss condition met (Nightfall)
   - Max turns reached (safety limit)

4. Record Results
   ↓
   - Win/Loss status
   - Number of turns
   - Resources used
   - Objective progress

5. Run 1000 Times
   ↓
   - Aggregate statistics
   - Calculate win rates
   - Analyze patterns
```

---

## Installation

### Prerequisites

- **Python 3.8 or higher**
- **uv** package manager (recommended) or pip

### Step 1: Install uv (if not already installed)

**macOS / Linux:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Windows (PowerShell):**
```powershell
irm https://astral.sh/uv/install.ps1 | iex
```

### Step 2: Clone the Repository

```bash
git clone https://github.com/ryan258/tuckdinterrors_montecarlosim.git
cd tuckdinterrors_montecarlosim
```

### Step 3: Create Virtual Environment and Install Dependencies

**Using uv (recommended):**
```bash
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -r requirements.txt
```

**Using pip:**
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Step 4: Verify Installation

```bash
python main.py --help
```

You should see the help message with all available options.

---

## Quick Start

### Your First Simulation (30 seconds)

Run 100 simulations of "The First Night" objective:

```bash
python main.py --objective OBJ01_THE_FIRST_NIGHT --simulations 100 --ai scoring_ai
```

**Expected Output:**
```
Initializing Tuck'd-In Terrors Monte Carlo Simulator...
Objective: OBJ01_THE_FIRST_NIGHT, AI: scoring_ai, Simulations: 100, Deep Dive: 0
Simulating Games: 100%|████████████████| 100/100 [00:06<00:00, 15.67it/s]

--- Simulation Summary ---
Total Games: 100
Wins: 45 (45.00%)
Losses: 55 (55.00%)

Win Status Breakdown:
  PRIMARY_WIN: 42 (42.00%)
  ALTERNATIVE_WIN: 3 (3.00%)
  LOSS_NIGHTFALL: 55 (55.00%)

Average Turns (Wins): 5.8
Average Turns (Losses): 4.2
```

**What Just Happened?**
- The simulator played 100 complete games
- Used "scoring_ai" to make decisions
- Achieved a 45% win rate
- Primary win condition was met 42 times
- Most losses were due to Nightfall (running out of time)

---

## Understanding the Game

### Tuck'd-In Terrors Basics

**Game Type:** Solo card game
**Theme:** Defending against nightmares using toys, spells, and rituals
**Win Condition:** Varies by objective (8 total objectives)
**Loss Condition:** Nightfall (time runs out)

### Core Mechanics

#### 1. Resources

- **Mana:** Used to play cards (gain 1 per turn, starting at 1)
- **Spirit Tokens:** Created by card effects, used for various abilities
- **Memory Tokens:** Special currency for powerful effects

#### 2. Card Types

- **Toys (13 cards):** Permanent cards with ongoing effects
  - Example: "Toy Cow With Bell That Never Rings"
- **Spells (11 cards):** One-time effects, discarded after use
  - Example: "Fluffstorm of Forgotten Names"
- **Rituals (7 cards):** Permanents with activated abilities
  - Example: "Recurring Cuddles That Leave Bruises"

#### 3. Zones

- **Deck:** Cards waiting to be drawn
- **Hand:** Cards available to play
- **In Play:** Active cards on the battlefield
- **Discard:** Cards that have been used/destroyed
- **Exile:** Removed from game (special zone)

#### 4. Turn Structure

```
┌─────────────────────────────────────┐
│ BEGIN TURN                          │
│ - Untap all cards                   │
│ - Draw 1 card                       │
│ - Gain mana (turn number + 1)      │
│ - Apply Nightmare Creep (if active) │
└─────────────────────────────────────┘
                ↓
┌─────────────────────────────────────┐
│ MAIN PHASE                          │
│ - Play cards (cost mana)            │
│ - Activate abilities                │
│ - AI makes all decisions            │
│ - Pass turn when done               │
└─────────────────────────────────────┘
                ↓
┌─────────────────────────────────────┐
│ END TURN                            │
│ - Discard to hand size (if needed)  │
│ - Check win/loss conditions         │
│ - Advance to next turn              │
└─────────────────────────────────────┘
```

### The 8 Objectives

Each objective has unique win conditions and challenges:

| ID | Name | Difficulty | Nightfall Turn | Key Mechanic |
|----|------|------------|----------------|--------------|
| OBJ01 | The First Night | Easy | 4 | Play toys & create spirits |
| OBJ02 | The Whisper Before Wake | Easy | 6 | Storm mechanic, spell-focused |
| OBJ03 | Choir of Forgotten Things | Moderate | 7 | Spirit control & generation |
| OBJ04 | The Loop That Loved Too Much | Moderate | 5 | Loop mechanics, recursion |
| OBJ05 | Threadbare Moon | Hard | 8 | Reanimation from discard |
| OBJ06 | The Creaking Choirbox | Moderate | 6 | Spell combo chains |
| OBJ07 | Stitched Infinity | Hard | ∞ | Deck depletion strategy |
| OBJ08 | Wild Night | Hard | 9 | Dice rolling & exile play |

#### Example: OBJ01 - The First Night

**Primary Win Condition:**
- Play 3 different Toys
- Create 3 Spirit tokens

**Alternative Win Condition:**
- Generate 5 mana from card effects (not turn mana)

**Loss Condition:**
- Turn 4 ends (Nightfall)

**Starting Setup:**
- Start with "Toy Cow With Bell That Never Rings" in hand
- First Memory already in play
- 1 mana on turn 1

**Nightmare Creep:**
- After turn 4, discard a card or sacrifice a Spirit each turn

---

## Basic Usage

### Command Structure

```bash
python main.py [OPTIONS]
```

### Required Options

- `--objective OBJECTIVE_ID`: Which objective to simulate
  - Example: `OBJ01_THE_FIRST_NIGHT`
  - See all objectives: OBJ01 through OBJ08

### Common Options

| Option | Description | Default | Example |
|--------|-------------|---------|---------|
| `--simulations N` | Number of games to run | 1000 | `--simulations 500` |
| `--ai PROFILE` | AI strategy to use | random_ai | `--ai scoring_ai` |
| `--visualize` | Generate charts | No | `--visualize` |
| `--output-file FILE` | Save results to JSON | None | `--output-file results.json` |
| `--output-dir DIR` | Output directory | results | `--output-dir data` |
| `--deep-dive N` | Detailed logs for N games | 0 | `--deep-dive 3` |
| `--balance-report` | Generate balance analysis | No | `--balance-report` |

### Example Commands

#### 1. Basic Simulation (Default Settings)
```bash
python main.py --objective OBJ01_THE_FIRST_NIGHT --simulations 1000 --ai random_ai
```

#### 2. High-Performance Run (Smart AI)
```bash
python main.py --objective OBJ02_WHISPER_WAKE --simulations 5000 --ai scoring_ai
```

#### 3. Full Analysis with Visualization
```bash
python main.py --objective OBJ03_CHOIR_FORGOTTEN \
    --simulations 1000 \
    --ai scoring_ai \
    --visualize \
    --output-file obj03_analysis.json \
    --balance-report
```

#### 4. Deep Dive Debug Session
```bash
python main.py --objective OBJ04_LOOP_TOO_MUCH \
    --simulations 10 \
    --ai scoring_ai \
    --deep-dive 3 \
    --verbose
```

---

## Advanced Features

### 1. Deep Dive Logging

**Purpose:** See exactly what happens turn-by-turn in specific games.

**Usage:**
```bash
python main.py --objective OBJ01_THE_FIRST_NIGHT \
    --simulations 100 \
    --deep-dive 2 \
    --ai scoring_ai
```

**Output Example:**
```
================================================================================
 DEEP DIVE REPORT: SIMULATION #1
================================================================================

--- Turn 1 (Phase: BEGIN_TURN) ---
  Player: Mana=1, Spirits=0, Memory=0
  Hand (2): [Toy Cow With Bell That Never Rings, Ghost Doll With Hollow Eyes]
  In Play (1): [Echo Bear Who Remembers Your Name]
  Objective Progress: {'distinct_toys_played_ids': set(), 'spirits_created_total_game': 0}
----------------------------------------
    - Player 1 drew 1 card from deck. Cards remaining: 28
    - Player 1 gains 1 mana. Total: 1
    - ACTION: Play Card 'Toy Cow With Bell That Never Rings' for 2 mana
    - ERROR: Insufficient mana (have 1, need 2)
    - ACTION: Pass Turn

--- Turn 2 (Phase: BEGIN_TURN) ---
  Player: Mana=3, Spirits=0, Memory=0
  Hand (3): [Toy Cow, Ghost Doll, Echoes of Bedtime Stories]
  In Play (1): [Echo Bear]
  Objective Progress: {'distinct_toys_played_ids': {1}, 'spirits_created_total_game': 1}
----------------------------------------
    - Player 1 gains 2 mana. Total: 3
    - ACTION: Play Card 'Toy Cow With Bell That Never Rings' for 2 mana
    - Toy enters play, Echo effect triggers
    - Created 1 Spirit token
    - ACTION: Pass Turn
...
```

**When to Use:**
- Debugging unexpected results
- Understanding AI decision-making
- Verifying card interactions work correctly
- Learning game mechanics

### 2. Visualization

**Purpose:** Generate charts showing win rates and game length distributions.

**Usage:**
```bash
python main.py --objective OBJ01_THE_FIRST_NIGHT \
    --simulations 1000 \
    --ai scoring_ai \
    --visualize
```

**Generated Files:**
- `results/win_loss_pie_scoring_ai.png` - Pie chart of outcomes
- `results/turn_distribution_scoring_ai.png` - Histogram of game lengths

**Example Pie Chart:**
```
         Win/Loss Distribution
    ┌─────────────────────────┐
    │                         │
    │   PRIMARY_WIN (42%)     │
    │   ████████████          │
    │                         │
    │   ALT_WIN (3%)          │
    │   █                     │
    │                         │
    │   LOSS_NIGHTFALL (55%)  │
    │   ███████████████       │
    └─────────────────────────┘
```

### 3. Data Export

**Purpose:** Save raw simulation data for external analysis (Excel, Python, R, etc.).

**Usage:**
```bash
python main.py --objective OBJ01_THE_FIRST_NIGHT \
    --simulations 1000 \
    --ai scoring_ai \
    --output-file obj01_data.json
```

**Output Format (JSON):**
```json
[
  {
    "objective_id": "OBJ01_THE_FIRST_NIGHT",
    "ai_profile": "scoring_ai",
    "win_status": "PRIMARY_WIN",
    "turns_taken": 6,
    "final_mana": 7,
    "final_spirits": 4,
    "final_memory": 1,
    "toys_played": 4,
    "spirits_created": 5,
    "game_log": ["Turn 1: ...", "Turn 2: ..."]
  },
  ...
]
```

**Use Cases:**
- Import into Excel for custom charts
- Analyze with Pandas in Python
- Statistical analysis in R
- Machine learning training data

### 4. Automatic Scorecard (NEW!)

**Purpose:** Get an instant executive summary with insights after every simulation.

**Features:**
- **Enabled by default** - runs automatically after each simulation
- **Performance Grade** (A-F) based on win rate
- **Visual Metrics** with progress bars and distributions
- **Key Insights** - automatic identification of patterns and concerns
- **Recommendations** - actionable suggestions for improvement
- **Auto-saved** to `results/scorecard_<objective>_<ai>.txt`

**Disable if needed:**
```bash
python main.py --objective OBJ01_THE_FIRST_NIGHT \
    --simulations 1000 \
    --ai scoring_ai \
    --no-scorecard  # Disable scorecard
```

**Example Scorecard Output:**

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

┌──────────────────────────────────────────────────────────────────────────────┐
│ GAME METRICS                                                                 │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Average Turns:                                                              │
│    ├─ Wins:        5.8 turns  (fastest: 3, slowest: 12)                     │
│    └─ Losses:      4.2 turns                                                 │
│                                                                              │
│  Win Consistency:  Consistent            (σ = 2.1)                           │
│                                                                              │
│  Average Resources at Win:                                                   │
│    ├─ Mana:        7.2                                                       │
│    ├─ Spirits:     4.5                                                       │
│    └─ Toys:        3.8                                                       │
│                                                                              │
│  Loss Breakdown:                                                             │
│    LOSS_NIGHTFALL              547 (54.7%) [██████████████████████████████] │
└──────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────────┐
│ KEY INSIGHTS                                                                 │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ✓  Win rate is WITHIN target range for Easy difficulty                     │
│  ✓  Wins occur faster than losses (efficient strategy)                      │
│  ✓  Both win conditions viable (good objective design)                      │
│  ⏰ Most losses due to Nightfall (time pressure is main challenge)          │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────────┐
│ RECOMMENDATIONS                                                              │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  No immediate concerns detected!                                             │
│  Objective appears well-balanced for current difficulty.                     │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘

╔══════════════════════════════════════════════════════════════════════════════╗
║  Run with --balance-report for detailed statistical analysis                ║
║  Run with --visualize to generate charts                                    ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

**Understanding Scorecard Sections:**

1. **Performance Summary**
   - Win rate with visual bar
   - Letter grade (A=50%+, B=40%+, C=30%+, D=20%+, F=<20%)
   - Primary vs alternative win breakdown

2. **Game Metrics**
   - Turn statistics (average, fastest, slowest)
   - Win consistency rating
   - Resource usage patterns
   - Loss reason breakdown
   - Turn distribution visualization

3. **Key Insights**
   - ✓ = Positive observation
   - ⚠️ = Warning or concern
   - 🔄 = Interesting pattern
   - ⏰ = Time-related observation
   - ⚡ = Speed observation

4. **Recommendations**
   - Specific suggestions based on data
   - Balance adjustment ideas
   - Next steps for testing

### 5. Game Balance Analysis

**Purpose:** Deep analysis of objective difficulty and AI performance.

**Usage:**
```bash
python main.py --objective OBJ01_THE_FIRST_NIGHT \
    --simulations 1000 \
    --ai scoring_ai \
    --balance-report
```

**Output Sections:**

1. **Overall Statistics**
   - Total games analyzed
   - Win rate percentage
   - Average game length

2. **Objective Difficulty**
   - Primary vs Alternative win rates
   - Average turns to win/loss
   - Median game length
   - Loss reason breakdown

3. **AI Performance Comparison** (if multiple AI runs)
   - Side-by-side win rates
   - Efficiency metrics
   - Fastest/slowest wins

4. **Win Rate Progression**
   - Cumulative win rate by turn
   - Visual bar chart in terminal

5. **Outlier Detection**
   - Unusually fast wins
   - Unusually slow wins
   - Statistical anomalies

**Example Output:**
```
================================================================================
GAME BALANCE ANALYSIS REPORT
================================================================================

Total Games Analyzed: 1000
Overall Win Rate: 45.30%

OBJECTIVE DIFFICULTY COMPARISON
--------------------------------------------------------------------------------

OBJ01_THE_FIRST_NIGHT:
  Win Rate: 45.30% (453 wins / 1000 games)
  Avg Turns to Win: 5.8
  Avg Turns to Loss: 4.2
  Primary Win Rate: 42.00%
  Alternative Win Rate: 3.30%

AI PERFORMANCE COMPARISON
--------------------------------------------------------------------------------

scoring_ai:
  Win Rate: 45.30% (453 / 1000)
  Avg Turns to Win: 5.8
  Fastest Win: Turn 3
  Slowest Win: Turn 12

WIN RATE BY TURN (Cumulative)
--------------------------------------------------------------------------------
  Turn  1:  0.00%
  Turn  2:  0.30% ███
  Turn  3:  5.80% ██████████████
  Turn  4: 18.20% ████████████████████████████████████
  Turn  5: 32.10% ████████████████████████████████████████████████████████████
  Turn  6: 40.50% ████████████████████████████████████████████████████████████████████████████
  Turn  7: 44.20% ███████████████████████████████████████████████████████████████████████████████████████
  Turn  8: 45.10% ████████████████████████████████████████████████████████████████████████████████████████████
  Turn  9: 45.30% █████████████████████████████████████████████████████████████████████████████████████████████

NOTABLE OUTLIERS
--------------------------------------------------------------------------------
  Unusually Fast Wins: 12 games
    Fastest: Turn 2 (scoring_ai AI)
  Unusually Slow Wins: 8 games
    Slowest: Turn 15 (scoring_ai AI)

================================================================================
END OF REPORT
================================================================================
```

---

## Interpreting Results

### Understanding Win Rates

**What is a "Good" Win Rate?**

| Difficulty | Expected Win Rate | Interpretation |
|------------|-------------------|----------------|
| Easy | 40-60% | Balanced, accessible |
| Moderate | 25-40% | Challenging, strategic |
| Hard | 10-25% | Expert-level, puzzle-like |

**OBJ01 Example:**
- Win Rate: 45.30%
- Difficulty: Easy
- **Interpretation:** Well-balanced for an easy objective

### Reading Loss Reasons

Common loss reasons and what they mean:

1. **LOSS_NIGHTFALL** (most common)
   - Ran out of time
   - Didn't meet win condition fast enough
   - **Action:** Need faster strategy or better cards

2. **LOSS_MAX_TURNS** (rare)
   - Safety limit hit (100 turns)
   - Game state loop or stalemate
   - **Action:** Check for infinite loops or bugs

3. **LOSS_DECK_OUT** (objective-specific)
   - Ran out of cards to draw
   - Only relevant for some objectives
   - **Action:** More efficient card usage

### Analyzing Average Turns

**Wins:**
- Lower = More efficient strategy
- OBJ01 Example: 5.8 turns average
- **Interpretation:** Typically win mid-game

**Losses:**
- Lower = Failing early
- OBJ01 Example: 4.2 turns average
- **Interpretation:** Nightfall at turn 4 is common

**Comparison:**
- If Win turns > Loss turns: You're winning by barely beating the clock
- If Win turns < Loss turns: You're either winning fast or losing late

### Statistical Significance

**Sample Sizes:**
- **< 100 games:** Not statistically significant, use for testing only
- **100-500 games:** Good for initial analysis
- **1000+ games:** Reliable statistics
- **5000+ games:** High confidence results

**Variance:**
- Card games have high variance due to shuffling
- A single game tells you almost nothing
- 1000 games gives you ~3% margin of error

---

## Game Balance Analysis

### Comparing Objectives

Run the same AI on multiple objectives to compare difficulty:

```bash
# Run all 8 objectives with scoring_ai
for obj in OBJ01 OBJ02 OBJ03 OBJ04 OBJ05 OBJ06 OBJ07 OBJ08; do
    python main.py --objective ${obj}_* \
        --simulations 1000 \
        --ai scoring_ai \
        --output-file ${obj}_results.json \
        --balance-report
done
```

**Create Summary Table:**

| Objective | Win Rate | Avg Win Turn | Difficulty Rating |
|-----------|----------|--------------|-------------------|
| OBJ01 | 45.3% | 5.8 | ★★☆☆☆ (Easy) |
| OBJ02 | 38.7% | 7.2 | ★★★☆☆ (Moderate) |
| OBJ03 | 31.2% | 8.5 | ★★★☆☆ (Moderate) |
| OBJ04 | 28.9% | 6.1 | ★★★☆☆ (Moderate) |
| OBJ05 | 15.4% | 10.2 | ★★★★☆ (Hard) |
| OBJ06 | 33.5% | 7.8 | ★★★☆☆ (Moderate) |
| OBJ07 | 12.1% | 12.7 | ★★★★★ (Very Hard) |
| OBJ08 | 18.6% | 11.3 | ★★★★☆ (Hard) |

### Identifying Balance Issues

**Red Flags:**

1. **Win Rate Too High (>70%)**
   - Objective may be too easy
   - Consider: Shorter Nightfall turn, harder win conditions

2. **Win Rate Too Low (<10%)**
   - Objective may be impossible or too hard
   - Consider: Longer Nightfall turn, easier win conditions

3. **Huge AI Differences**
   - If random_ai: 5%, scoring_ai: 60%
   - Suggests objective rewards skill heavily (good!)
   - If all AIs similar: Outcome is luck-based (bad!)

4. **Bimodal Turn Distribution**
   - Games end at turn 3 OR turn 15 (nothing in between)
   - Suggests "all-or-nothing" design
   - Consider: More gradual difficulty curve

---

## AI Strategies

The simulator includes 3 built-in AI profiles:

### 1. Random AI (`random_ai`)

**Strategy:** Makes completely random valid moves.

**When to Use:**
- Baseline comparison
- Testing minimum viable win rate
- Identifying broken objectives (if random wins >50%, too easy!)

**Performance:**
- OBJ01: ~20-30% win rate
- Generally 10-20% lower than smart AI

**Command:**
```bash
python main.py --objective OBJ01_THE_FIRST_NIGHT --simulations 1000 --ai random_ai
```

### 2. Greedy AI (`greedy_ai`)

**Strategy:** Maximizes immediate value toward a single win condition aspect.

**Characteristics:**
- Prioritizes primary win condition exclusively
- Makes locally optimal decisions
- Doesn't plan ahead
- Ignores alternative win conditions

**When to Use:**
- Testing single-minded strategies
- Comparing to more sophisticated AI
- Analyzing greedy vs. balanced approaches

**Performance:**
- OBJ01: ~35-40% win rate
- Better than random, worse than scoring

**Command:**
```bash
python main.py --objective OBJ01_THE_FIRST_NIGHT --simulations 1000 --ai greedy_ai
```

### 3. Scoring AI (`scoring_ai`) **[Recommended]**

**Strategy:** Weighted scoring system that balances multiple objectives.

**Characteristics:**
- Considers both primary and alternative win conditions
- Scores each possible action (playing cards, activating abilities)
- Makes intelligent choices during Nightmare Creep
- Adjusts priorities based on game state

**Scoring Example (OBJ01):**
```python
Base score: 1.0

If action plays a TOY and we need more toys:
    score += 10.0

If action creates SPIRITS and we need more spirits:
    score += 10.0

If action is ACTIVATE_ABILITY:
    score += 2.0

Choose highest scoring action
```

**When to Use:**
- Default choice for most analysis
- Represents "decent player" skill level
- Good for balance testing

**Performance:**
- OBJ01: ~40-50% win rate
- Consistently outperforms other AIs

**Command:**
```bash
python main.py --objective OBJ01_THE_FIRST_NIGHT --simulations 1000 --ai scoring_ai
```

### AI Comparison Example

```bash
# Run all 3 AIs on same objective
python main.py --objective OBJ01_THE_FIRST_NIGHT --simulations 1000 --ai random_ai --output-file random.json
python main.py --objective OBJ01_THE_FIRST_NIGHT --simulations 1000 --ai greedy_ai --output-file greedy.json
python main.py --objective OBJ01_THE_FIRST_NIGHT --simulations 1000 --ai scoring_ai --output-file scoring.json

# Compare results manually or use balance analyzer
```

**Expected Results:**

| AI | Win Rate | Avg Turns | Strategy Quality |
|----|----------|-----------|------------------|
| random_ai | 25% | 6.2 | Baseline |
| greedy_ai | 38% | 5.5 | Moderate |
| scoring_ai | 45% | 5.8 | Good |

---

## Example Workflows

### Workflow 1: Testing a New Objective

**Goal:** Determine if a new objective is properly balanced.

**Steps:**

1. **Initial Test (Quick Check)**
   ```bash
   python main.py --objective OBJ05_THREADBARE_MOON \
       --simulations 100 \
       --ai scoring_ai
   ```
   - Quick feedback (30 seconds)
   - Ballpark win rate

2. **Full Analysis**
   ```bash
   python main.py --objective OBJ05_THREADBARE_MOON \
       --simulations 2000 \
       --ai scoring_ai \
       --balance-report \
       --visualize
   ```
   - Reliable statistics (3-4 minutes)
   - Comprehensive report

3. **AI Comparison**
   ```bash
   python main.py --objective OBJ05_THREADBARE_MOON --simulations 1000 --ai random_ai --balance-report
   python main.py --objective OBJ05_THREADBARE_MOON --simulations 1000 --ai scoring_ai --balance-report
   ```
   - See skill impact

4. **Review Results**
   - Is win rate in target range for difficulty?
   - Is there a significant difference between AIs?
   - Are games ending at appropriate turn numbers?
   - Any unexpected loss reasons?

5. **Deep Dive (If Issues Found)**
   ```bash
   python main.py --objective OBJ05_THREADBARE_MOON \
       --simulations 10 \
       --deep-dive 5 \
       --ai scoring_ai \
       --verbose
   ```
   - Identify specific problems
   - Watch AI decision-making

### Workflow 2: Comparing Strategies

**Goal:** Determine which AI performs best on a specific objective.

```bash
# Create a comparison script
cat > compare_ai.sh << 'EOF'
#!/bin/bash
OBJECTIVE="OBJ03_CHOIR_FORGOTTEN"
SIMS=1000

echo "Testing Random AI..."
python main.py --objective $OBJECTIVE --simulations $SIMS --ai random_ai \
    --output-file random_results.json --balance-report > random_report.txt

echo "Testing Greedy AI..."
python main.py --objective $OBJECTIVE --simulations $SIMS --ai greedy_ai \
    --output-file greedy_results.json --balance-report > greedy_report.txt

echo "Testing Scoring AI..."
python main.py --objective $OBJECTIVE --simulations $SIMS --ai scoring_ai \
    --output-file scoring_results.json --balance-report > scoring_report.txt

echo "Comparison complete! Check *_report.txt files."
EOF

chmod +x compare_ai.sh
./compare_ai.sh
```

### Workflow 3: Finding Optimal Play Patterns

**Goal:** Understand what leads to wins vs losses.

1. **Run Large Simulation**
   ```bash
   python main.py --objective OBJ04_LOOP_TOO_MUCH \
       --simulations 5000 \
       --ai scoring_ai \
       --output-file loop_data.json
   ```

2. **Analyze with Python/Pandas**
   ```python
   import json
   import pandas as pd

   # Load data
   with open('results/loop_data.json') as f:
       data = json.load(f)

   df = pd.DataFrame(data)

   # Compare wins vs losses
   wins = df[df['win_status'].str.contains('WIN')]
   losses = df[df['win_status'].str.contains('LOSS')]

   print("Average resources at game end:")
   print("Wins:")
   print(f"  Mana: {wins['final_mana'].mean():.1f}")
   print(f"  Spirits: {wins['final_spirits'].mean():.1f}")
   print(f"  Toys Played: {wins['toys_played'].mean():.1f}")

   print("\nLosses:")
   print(f"  Mana: {losses['final_mana'].mean():.1f}")
   print(f"  Spirits: {losses['final_spirits'].mean():.1f}")
   print(f"  Toys Played: {losses['toys_played'].mean():.1f}")

   # Find patterns
   print("\nKey differences:")
   print(f"Winners played {wins['toys_played'].mean() - losses['toys_played'].mean():.1f} more toys")
   print(f"Winners created {wins['spirits_created'].mean() - losses['spirits_created'].mean():.1f} more spirits")
   ```

3. **Identify Success Factors**
   - What resources do winners have more of?
   - What turn do most wins occur on?
   - Are there common patterns in winning games?

### Workflow 4: Exhaustive Objective Analysis

**Goal:** Complete analysis of all objectives for a balance report.

```bash
#!/bin/bash
# comprehensive_analysis.sh

OBJECTIVES=(
    "OBJ01_THE_FIRST_NIGHT"
    "OBJ02_WHISPER_WAKE"
    "OBJ03_CHOIR_FORGOTTEN"
    "OBJ04_LOOP_TOO_MUCH"
    "OBJ05_THREADBARE_MOON"
    "OBJ06_CREAKING_CHOIRBOX"
    "OBJ07_STITCHED_INFINITY"
    "OBJ08_WILD_NIGHT"
)

AI="scoring_ai"
SIMS=2000

for obj in "${OBJECTIVES[@]}"; do
    echo "========================================="
    echo "Analyzing: $obj"
    echo "========================================="

    python main.py \
        --objective $obj \
        --simulations $SIMS \
        --ai $AI \
        --visualize \
        --balance-report \
        --output-file "${obj}_${AI}.json" \
        > "${obj}_${AI}_report.txt"

    echo "Complete!"
    echo ""
done

echo "All objectives analyzed!"
echo "Check *_report.txt files for detailed results."
```

---

## Troubleshooting

### Common Issues

#### Issue: "No module named 'src'"

**Problem:** Python can't find the simulator modules.

**Solutions:**
```bash
# Solution 1: Run from project root
cd /path/to/tuckdinterrors_montecarlosim
python main.py --objective OBJ01_THE_FIRST_NIGHT --simulations 100 --ai scoring_ai

# Solution 2: Activate virtual environment
source .venv/bin/activate
python main.py ...

# Solution 3: Add to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
python main.py ...
```

#### Issue: "Unknown objective 'OBJ01'"

**Problem:** Objective ID not found in objectives.json.

**Solutions:**
```bash
# Check available objectives
cat data/objectives.json | python3 -c "import sys, json; objs = json.load(sys.stdin); print('\n'.join([o['objective_id'] for o in objs]))"

# Use full objective ID
python main.py --objective OBJ01_THE_FIRST_NIGHT --simulations 100 --ai scoring_ai
```

#### Issue: Simulation is Very Slow

**Problem:** Performance lower than expected.

**Diagnostics:**
```bash
# Run small test
time python main.py --objective OBJ01_THE_FIRST_NIGHT --simulations 100 --ai scoring_ai

# Expected: ~10-20 seconds for 100 games
# If slower: Check CPU usage, close other programs
```

**Solutions:**
- Use scoring_ai (faster than random_ai with fewer random choices)
- Reduce simulation count for testing
- Close resource-intensive programs
- Run on more powerful hardware

#### Issue: "Game stuck in infinite loop"

**Problem:** Max turns limit reached (100 turns).

**What it means:**
- Safety mechanism triggered
- Likely a bug in game logic or AI
- Or objective has no viable win path

**Solutions:**
```bash
# Run deep-dive to see what's happening
python main.py --objective PROBLEMATIC_OBJ \
    --simulations 5 \
    --deep-dive 5 \
    --verbose
```

Look for:
- Repeated actions without progress
- Resources not being generated
- Win conditions that can never be met

#### Issue: Win Rate is 0%

**Problem:** No wins in any simulations.

**Possible Causes:**
1. **Objective too difficult**
   - Win conditions impossible with current cards
   - Nightfall turn too early

2. **Bug in win condition logic**
   - Win condition never triggers
   - Check win_loss_checker.py

3. **AI not playing optimally**
   - Try different AI profile
   - Use deep-dive to watch gameplay

**Debugging:**
```bash
# Test with verbose output
python main.py --objective ZERO_WIN_OBJ \
    --simulations 10 \
    --deep-dive 10 \
    --ai scoring_ai \
    --verbose
```

Look for:
- Are win conditions being checked?
- Is progress being tracked?
- Is AI making reasonable moves?

---

## Tips and Best Practices

### General Tips

1. **Start Small, Scale Up**
   - Run 100 games first for quick feedback
   - If results look good, scale to 1000+
   - Don't run 10,000 games on first try

2. **Use Scoring AI by Default**
   - Best representation of skilled play
   - Much better than random for meaningful results
   - Only use random_ai for baseline comparison

3. **Save Your Results**
   - Always use `--output-file` for important runs
   - Results are deterministic (same seed = same results)
   - You can re-analyze without re-simulating

4. **Balance Reports are Your Friend**
   - Use `--balance-report` frequently
   - Provides insights beyond basic win rate
   - Helps identify issues quickly

5. **Visualizations Aid Understanding**
   - Charts make patterns obvious
   - Win rate curves show difficulty progression
   - Histograms reveal bimodal distributions

### Performance Optimization

1. **Batch Large Runs**
   ```bash
   # Instead of multiple small runs:
   python main.py --objective OBJ01 --simulations 100 --ai scoring_ai
   python main.py --objective OBJ01 --simulations 100 --ai scoring_ai
   python main.py --objective OBJ01 --simulations 100 --ai scoring_ai

   # Do one large run:
   python main.py --objective OBJ01 --simulations 300 --ai scoring_ai
   ```

2. **Minimize Deep-Dive**
   - Deep-dive logging is SLOW (10x slower)
   - Only use for debugging specific issues
   - Run regular simulations for statistics

3. **Disable Visualization for Speed**
   - Generating charts takes time
   - Run simulations without --visualize
   - Generate charts separately if needed

### Data Analysis Tips

1. **Export to CSV for Excel**
   ```python
   import json
   import pandas as pd

   with open('results/data.json') as f:
       data = json.load(f)

   df = pd.DataFrame(data)
   df.to_csv('results/data.csv', index=False)
   ```

2. **Calculate Custom Metrics**
   ```python
   # Efficiency: Resources used per turn
   df['mana_per_turn'] = df['final_mana'] / df['turns_taken']
   df['spirits_per_turn'] = df['final_spirits'] / df['turns_taken']

   # Win rate by turn range
   early_wins = df[(df['win_status'].str.contains('WIN')) & (df['turns_taken'] <= 5)]
   print(f"Early wins (<= turn 5): {len(early_wins) / len(df) * 100:.1f}%")
   ```

3. **Visualize Custom Charts**
   ```python
   import matplotlib.pyplot as plt

   # Scatter plot: Mana vs Spirits (colored by win/loss)
   wins = df[df['win_status'].str.contains('WIN')]
   losses = df[df['win_status'].str.contains('LOSS')]

   plt.scatter(wins['final_mana'], wins['final_spirits'], c='green', label='Wins', alpha=0.5)
   plt.scatter(losses['final_mana'], losses['final_spirits'], c='red', label='Losses', alpha=0.5)
   plt.xlabel('Final Mana')
   plt.ylabel('Final Spirits')
   plt.legend()
   plt.title('Resource Distribution: Wins vs Losses')
   plt.savefig('mana_spirits_scatter.png')
   ```

### Reproducibility

1. **Document Your Commands**
   - Keep a log of commands used
   - Include date, version, and parameters
   - Makes results reproducible

2. **Version Control Results**
   ```bash
   # Save results with metadata
   echo "Date: $(date)" > results/metadata.txt
   echo "Version: $(grep version pyproject.toml)" >> results/metadata.txt
   echo "Command: python main.py --objective OBJ01 --simulations 1000 --ai scoring_ai" >> results/metadata.txt
   ```

3. **Compare Across Versions**
   ```bash
   # Tag results with version
   python main.py --objective OBJ01 --simulations 1000 --ai scoring_ai \
       --output-file v0.3.0_obj01_results.json
   ```

---

## Frequently Asked Questions

### General Questions

**Q: How long does it take to run 1000 simulations?**

A: Typically 30-60 seconds with scoring_ai. Performance depends on:
- Objective complexity
- AI profile (random_ai is actually slower)
- Computer specs
- Whether deep-dive logging is enabled

**Q: Can I run multiple simulations in parallel?**

A: Not out of the box, but you can run multiple terminals:
```bash
# Terminal 1
python main.py --objective OBJ01_THE_FIRST_NIGHT --simulations 1000 --ai scoring_ai &

# Terminal 2
python main.py --objective OBJ02_WHISPER_WAKE --simulations 1000 --ai scoring_ai &
```

**Q: Are results deterministic?**

A: No, each run uses a different random seed. Results will vary slightly. For deterministic results, you'd need to modify the code to set a fixed seed.

**Q: How much disk space do results take?**

A: JSON output is ~500KB - 2MB per 1000 games, depending on objective complexity and logging detail.

### Technical Questions

**Q: Can I modify the card definitions?**

A: Yes! Edit `data/cards.json`:
```json
{
  "card_id": "TCTOY001",
  "name": "Toy Cow With Bell That Never Rings",
  "card_type": "TOY",
  "cost": 2,  // <-- Change this
  "effect_logic_list": [...]
}
```

Then run simulations to see the impact.

**Q: Can I create custom objectives?**

A: Yes! Add to `data/objectives.json`:
```json
{
  "objective_id": "OBJ_CUSTOM_01",
  "title": "My Custom Objective",
  "difficulty": "Moderate",
  "primary_win_condition": {
    "component_type": "EXISTING_WIN_TYPE",
    "params": {...}
  },
  ...
}
```

You may need to implement new win condition logic in `win_loss_checker.py` if using custom types.

**Q: Can I create a custom AI?**

A: Yes! Create a new file in `src/tuck_in_terrors_sim/ai/ai_profiles/`:

```python
# custom_ai.py
from .random_ai import RandomAI

class CustomAI(RandomAI):
    def decide_action(self, game_state, possible_actions):
        # Your custom logic here
        # Return the chosen GameAction
        pass
```

Then add it to `simulation_runner.py`:
```python
elif ai_profile_name == "custom_ai":
    return CustomAI(player_id=player_id)
```

**Q: Why do some objectives have Nightfall turn 0?**

A: Nightfall turn 0 means "no time limit" (infinite turns). Example: OBJ07 (Stitched Infinity) focuses on deck depletion, so time isn't the limiting factor.

### Balance Questions

**Q: What's a good win rate for testing?**

A: Depends on your goal:
- **Development**: 30-70% (ensures both outcomes occur frequently)
- **Easy objectives**: 40-60%
- **Hard objectives**: 10-25%
- **Playtesting**: Whatever matches desired difficulty

**Q: How many simulations do I need for reliable results?**

A:
- **Quick check**: 100 games (±10% accuracy)
- **Good confidence**: 1000 games (±3% accuracy)
- **High confidence**: 5000 games (±1.4% accuracy)
- **Publication-quality**: 10,000+ games (<1% accuracy)

**Q: My objective has a 5% win rate. Is it broken?**

A: Not necessarily! Check:
1. Is it marked as "Hard"? (10-25% is expected)
2. Does random_ai also get 5%? (If yes, might be too hard)
3. Does scoring_ai get much higher? (If yes, skill-based)

If scoring_ai gets <10% on a "Moderate" objective, rebalancing may be needed.

**Q: How do I make an objective easier/harder?**

Easier:
- Extend Nightfall turn (+2 turns)
- Reduce win condition requirements (-1 toy needed)
- Start with more resources (+1 Spirit token)
- Remove restrictive special rules

Harder:
- Reduce Nightfall turn (-1 turn)
- Increase win condition requirements (+1 toy needed)
- Add Nightmare Creep effects earlier
- Add restrictive special rules (hand size limit, etc.)

### Troubleshooting Questions

**Q: I get "Unknown AI profile" error.**

A: You've misspelled the AI name. Valid options:
- `random_ai`
- `greedy_ai`
- `scoring_ai`

(Note: lowercase with underscore)

**Q: Simulations finish instantly with 0 results.**

A: The objective probably doesn't exist. Check:
```bash
python main.py --objective WRONG_NAME --simulations 100 --ai scoring_ai
# vs
python main.py --objective OBJ01_THE_FIRST_NIGHT --simulations 100 --ai scoring_ai
```

**Q: Why do I see "Warning: Condition type X not implemented"?**

A: Some advanced card conditions aren't fully implemented yet. This is normal for Phase 6. The simulation will continue, but that specific condition will be ignored. Check `win_loss_checker.py` for implemented types.

---

## Conclusion

You now have a comprehensive understanding of the Tuck'd-In Terrors Monte Carlo Simulator!

### Quick Reference Card

```
┌─────────────────────────────────────────────────────────────┐
│                     QUICK REFERENCE                          │
├─────────────────────────────────────────────────────────────┤
│ Basic Run:                                                   │
│   python main.py --objective OBJ01_THE_FIRST_NIGHT \       │
│       --simulations 1000 --ai scoring_ai                     │
│                                                             │
│ Full Analysis:                                              │
│   python main.py --objective OBJ01_THE_FIRST_NIGHT \       │
│       --simulations 1000 --ai scoring_ai \                  │
│       --visualize --balance-report --output-file out.json   │
│                                                             │
│ Debug Run:                                                  │
│   python main.py --objective OBJ01_THE_FIRST_NIGHT \       │
│       --simulations 10 --deep-dive 3 --verbose              │
│                                                             │
│ AI Options: random_ai, greedy_ai, scoring_ai                │
│ Objectives: OBJ01 through OBJ08                             │
│ Output: results/ directory                                  │
└─────────────────────────────────────────────────────────────┘
```

### Next Steps

1. **Run your first simulation** (if you haven't already)
2. **Try different objectives** to see variety
3. **Compare AI strategies** to understand skill impact
4. **Use balance analysis** to find interesting patterns
5. **Export data** for custom analysis

### Getting Help

- **Documentation**: README.md, ROADMAP.md, PHASE_6_COMPLETION.md
- **Code review**: review.md
- **GitHub Issues**: https://github.com/anthropics/claude-code/issues
- **Source Code**: All modules are well-commented

### Happy Simulating!

May your toys protect you, your spells enchant you, and your rituals guide you through the long night. Remember: in Tuck'd-In Terrors, every game is a story, and every simulation reveals a new possibility.

---

**Document Version:** 1.0
**Simulator Version:** 0.3.0
**Last Updated:** November 3, 2025
**Created by:** Claude (AI Assistant)
