# Tuck'd-In Terrors Monte Carlo Simulator - Project Roadmap

This document outlines the development phases for building the "Tuck'd-In Terrors" Monte Carlo simulator in Python. Our goal is to create a tool that can provide valuable insights for game balancing and design improvement.

---

## Phase 1: Foundation & Data Modeling (The Digital DNA)

**Objective:** Define the core data structures and formats that will represent every aspect of "Tuck'd-In Terrors" in code. This forms the blueprint for all subsequent logic.

- [x] **1.1. Define Game Element Schemas & Enums (`enums.py`)**
  - [x] Create `CardType`, `Zone`, `TurnPhase`, `ResourceType` enums.
  - [x] Define initial `CardSubType`, `EffectTriggerType`, `EffectConditionType`, `EffectActionType`, `EffectActivationCostType`, and `PlayerChoiceType` enums.
- [x] **1.2. Define Card Object Structure (`card.py`)**
  - [x] Create base `Card` class.
  - [x] Create `Toy`, `Ritual`, `Spell` subclasses.
  - [x] Define `EffectLogic` class structure (including fields for `trigger`, `conditions`, `actions`, `activation_costs`, `is_echo_effect`, `is_once_per_turn`, `is_once_per_game`).
- [x] **1.3. Define Objective Card Structure (`objective.py`)**
  - [x] Create `ObjectiveCard` class.
  - [x] Define `ObjectiveLogicComponent` class structure for representing win conditions, setup instructions, Nightmare Creep logic, etc.
- [x] **1.4. Create Initial JSON Data Files (`data/`)** _(You have the examples; populating with full game data is an ongoing task for you as needed.)_
- [x] **1.5. Implement Data Loaders (`data_loaders.py`)**
  - [x] Create `load_card_definitions(filepath)` function.
  - [x] Create `load_objective_definitions(filepath)` function.
- [x] **1.6. Write Initial Unit Tests (`tests/game_elements/`)**
  - [x] `test_enums.py` (if applicable for any complex enum logic).
  - [x] `test_card.py`: Test `Card`/subclass instantiation.
  - [x] `test_objective.py`: Test `ObjectiveCard` and `ObjectiveLogicComponent` instantiation.
  - [x] `test_data_loaders.py`: Test parsing of example JSON files.

---

## Phase 2: Core Game Logic Implementation (The Heartbeat)

**Objective:** Build the fundamental engine that can process turns, manage resources, and execute basic card plays according to "Tuck'd-In Terrors" rules.

- [ ] **2.1. Define GameState Class (`game_state.py`)**
  - [ ] Implement the class to hold all dynamic game information (deck, hand, discard, play area, resources, turn, objective progress, etc.).
- [ ] **2.2. Implement Game Setup Module (`game_setup.py`)**
  - [ ] Function to initialize a `GameState` instance based on a loaded `ObjectiveCard` and `Card` definitions.
  - [ ] Implement First Memory determination and placement logic as per objective rules.
  - [ ] Handle deck construction (including card rotations), initial hand draw, and starting resources.
- [ ] **2.3. Implement Turn Structure Engine (`turn_manager.py`)**
  - [ ] `begin_turn_phase` logic (mana gain, untap cards, draw card, initial Nightmare Creep application).
  - [ ] `main_phase` structure (will primarily be driven by AI actions later).
  - [ ] `end_turn_phase` logic (lose unspent mana, resolve end-of-turn effects, hand size check, advance turn).
- [ ] **2.4. Implement Basic Action & Resource Management (`action_resolver.py`)**
  - [ ] Functions for playing cards (Free Toy play, playing cards by paying mana).
  - [ ] Basic resource spending/gaining functions (mana, spirit tokens, memory tokens).
  - [ ] Tapping/Untapping cards.
- [ ] **2.5. Implement Initial Effect Engine (Simplified) (`effect_engine.py`)**
  - [ ] `resolve_effect` function structure.
  - [ ] Implement a few simple `EffectActionType`s (e.g., DRAW_CARDS, CREATE_SPIRIT_TOKENS).
  - [ ] Basic condition checking based on `EffectConditionType`.
- [ ] **2.6. Implement Basic Nightmare Creep Module (`nightmare_creep.py`)**
  - [ ] Function to apply Nightmare Creep effects based on the current `ObjectiveCard`'s `nightmare_creep_effect` logic (for simple, non-escalating cases initially).
- [ ] **2.7. Implement Basic Win/Loss Condition Checker (`win_loss_checker.py`)**
  - [ ] Check for Nightfall (turn limit reached).
  - [ ] Implement logic for 1-2 simple `ObjectiveCard` win conditions based on their `ObjectiveLogicComponent` definitions.
- [ ] **2.8. Write Unit Tests (`tests/game_logic/`)**
  - [ ] Test game setup for different objectives.
  - [ ] Test turn progression and phase transitions.
  - [ ] Test simple actions and resource changes.
  - [ ] Test basic win/loss condition triggering.

---

## Phase 3: AI Player Development (The Phantom Hand)

**Objective:** Create a foundational AI that can make valid plays within the "Tuck'd-In Terrors" ruleset, enabling automated game simulations.

- [ ] **3.1. Define AI Player Base (`ai_player_base.py`)**
  - [ ] Create an abstract base class for AI players, defining the interface for making decisions.
- [ ] **3.2. Implement Action Generator Module (`action_generator.py`)**
  - [ ] `get_valid_actions(game_state)` function to analyze the `GameState` and return a list of all legal actions the AI can take.
- [ ] **3.3. Implement Basic AI v0.1 (`ai_profiles/random_ai.py`)**
  - [ ] AI makes random valid selections from the actions provided by the `ActionGenerator`.
  - [ ] Handles simple choices presented by `PLAYER_CHOICE` effects (e.g., Nightmare Creep choices).
- [ ] **3.4. Integrate AI with Game Logic Engine**
  - [ ] Ensure the AI's chosen actions are correctly passed to and processed by the `action_resolver.py` and `effect_engine.py` during the `main_phase`.
- [ ] **3.5. Write Unit Tests (`tests/ai/`)**
  - [ ] Test `action_generator.py` for various game states.
  - [ ] Test basic AI decision-making and action execution within simple, controlled game scenarios.

---

## Phase 4: Advanced Game Mechanics & Comprehensive Effect Implementation (The Deep Magic)

**Objective:** Implement the full spectrum of card effects, keywords, advanced objective logic, and other nuanced game mechanics from "Tuck'd-In Terrors."

- [ ] **4.1. Expand Full Effect Engine (`effect_engine.py`)**
  - [ ] Systematically implement handlers for all defined `EffectTriggerType`, `EffectConditionType`, `EffectActionType`, and `EffectActivationCostType` values from `enums.py`.
  - [ ] Handle complex targeting, chained effects, dice rolls, Storm mechanic, conditional logic based on First Memory, etc.
- [ ] **4.2. Implement All Objective Logic**
  - [ ] Ensure `game_setup.py` handles all specific `setup_instructions` from all 8 objectives.
  - [ ] Ensure `win_loss_checker.py` correctly evaluates all primary and alternative win conditions.
  - [ ] Ensure `nightmare_creep.py` implements the full escalating logic for all objectives.
- [ ] **4.3. Implement First Memory Special Interactions & Evolution**
  - [ ] Full support for ✧ (Echo) effects in the `EffectEngine`.
  - [ ] Implement the "Evolving First Memory" advanced mechanic (if its rules are defined).
- [ ] **4.4. Implement Other Advanced Game Rules**
  - [ ] E.g., Flashback mechanic, Memory Anchor variant rules (if chosen for simulation).
- [ ] **4.5. Write Comprehensive Integration Tests**
  - [ ] Test complex card interactions, full objective playthroughs (with basic AI), and edge cases.

---

## Phase 5: Simulation Orchestration & Data Analysis (The Oracle)

**Objective:** Enable the execution of a large number of automated game simulations, collect detailed data from these simulations, and generate meaningful analysis and insights.

- [ ] **5.1. Implement Simulation Runner Module (`simulation_runner.py`)**
  - [ ] `run_simulations(objective_id, num_simulations, ai_profile_id)` function to manage batches of games.
  - [ ] Robust error handling for individual simulation failures within a batch.
- [ ] **5.2. Implement Comprehensive Data Logging Module (`data_logger.py`)**
  - [ ] Log all specified data points for each completed simulation (outcome, turns, resources, objective progress, key events).
  - [ ] Store logs in a structured format (e.g., JSON lines, CSV).
- [ ] **5.3. Implement Data Aggregation & Analysis Engine (`analysis_engine.py`)**
  - [ ] Functions to process raw log data.
  - [ ] Calculate statistics: win rates (primary/alternative/loss), average game length, resource economy metrics, objective-specific success metrics.
- [ ] **5.4. Integrate Analysis with UI/Reporting (`ui/results_display.py`)**
  - [ ] Functions to display key findings in a readable format (console output initially).
  - [ ] (Future: Potentially generate simple reports or data for external visualization tools).
- [ ] **5.5. Write Tests for Simulation and Analysis Components**
  - [ ] Test data logging accuracy and basic analysis calculations on sample log data.

---

## Phase 6: Iteration, Testing & Refinement (The Polish)

**Objective:** Thoroughly debug and validate the entire simulation, optimize performance, enhance AI strategies, and ultimately use the tool to analyze and inform the balance of "Tuck'd-In Terrors."

- [ ] **6.1. Conduct Extensive Debugging & Validation**
  - [ ] Rule-by-rule validation against the "Tuck'd-In Terrors" rulebook.
  - [ ] Test known card combos and edge cases identified during design or playtesting.
- [ ] **6.2. Enhance AI Strategy & Profile Development (`ai/ai_profiles/`)**
  - [ ] Develop more sophisticated heuristic-based AI.
  - [ ] Implement Objective-focused AI profiles that prioritize actions relevant to the current objective.
  - [ ] Improve AI's strategic resource management and use of advanced mechanics (Flashback, Evolving First Memory).
- [ ] **6.3. Perform Performance Optimization**
  - [ ] Profile the simulation code to identify and optimize performance bottlenecks, especially in the game logic loop and AI decision-making.
- [ ] **6.4. Refine Usability & Interface (of the simulator tool)**
  - [ ] Improve configuration options for running simulations.
  - [ ] Enhance the clarity and depth of results presentation.
- [ ] **6.5. Conduct Final Validation & Balance Analysis Application**
  - [ ] Run extensive test suites across all objectives using various AI profiles.
  - [ ] Analyze aggregated data to identify balance issues (over/underpowered cards, objective difficulty, resource flow problems).
  - [ ] (Advanced) Implement functionality to simulate "What-If" scenarios with minor rule or card data changes to test their impact.
  - [ ] Generate reports to inform potential game design adjustments.

---

This roadmap should provide a clear path forward. We can check off items as we complete them.
