# Tuck'd-In Terrors: Monte Carlo Simulator Roadmap

This roadmap outlines the planned development phases for the Tuck'd-In Terrors Monte Carlo Simulator.

## Phase 1: Core Game Logic & Basic Simulation (Completed)

- **Objective:** Implement the fundamental game rules, card structures, and a very basic simulation loop.
- **Key Tasks:**
  - [x] Define core data structures (Card, Toy, Spell, Ritual, Objective, GameState).
  - [x] Implement basic card parsing from JSON.
  - [x] Implement GameState management (deck, hand, discard, play area, resources: mana, spirits, memory tokens).
  - [x] Implement core turn phases (Begin, Main, End).
  - [x] Basic mana generation and card draw.
  - [x] Initial Action Resolver for playing cards (basic cost payment, moving card to play).
  - [x] Basic EffectEngine capable of simple, direct actions (e.g., DRAW_CARDS, ADD_MANA, CREATE_SPIRIT_TOKENS, CREATE_MEMORY_TOKENS).
  - [x] Initial Objective "The First Night" win/loss condition checking.
  - [x] Basic Nightmare Creep mechanism for "The First Night".
  - [x] Simple AI (RandomAI) to make basic play decisions (play first valid card).
  - [x] Rudimentary simulation runner (single game, basic logging).
  - [x] Initial test suite for core components.
  - [x] First Memory basic implementation (selection, tracking in GameState).

## Phase 2: Expanding Effect Engine & Card Interactions (Completed)

- **Objective:** Enhance the EffectEngine to handle more complex effects, conditions, and triggers. Implement a wider range of card abilities.
- **Key Tasks:**
  - [x] Implement effect triggers (ON_PLAY, ON_DISCARD, etc.).
  - [x] Implement conditional logic for effects (IF_X_THEN_Y).
    - [x] `IS_FIRST_MEMORY`, `IS_FIRST_MEMORY_IN_PLAY`, `IS_FIRST_MEMORY_IN_DISCARD`
    - [x] `HAS_COUNTER_TYPE_VALUE_GE`
    - [x] `DECK_SIZE_LE`
    - [x] `IS_MOVING_FROM_ZONE`, `IS_MOVING_TO_ZONE` (initial support)
  - [x] Implement more action types:
    - [x] `PLACE_COUNTER_ON_CARD`
    - [x] `SACRIFICE_CARD_IN_PLAY` (target SELF or specific ID)
    - [x] `RETURN_THIS_CARD_TO_HAND` (from play)
    - [x] `MILL_DECK`
    - [x] `EXILE_CARD_FROM_ZONE` (Deck, Hand, Discard)
    - [x] `RETURN_CARD_FROM_ZONE_TO_ZONE` (Discard/Exile to Hand/Deck Top)
    - [x] `BROWSE_DECK` (placeholder for AI choice)
  - [x] Refine AI to handle slightly more diverse actions.
  - [x] Implement effects for a representative subset of initial cards (e.g., Toy Cow, Plushcaller, some spells).
  - [x] Detailed logging for game events and effect resolution.
  - [x] Expand test coverage for new effects and interactions.
  - [x] First Memory interaction refinement for implemented cards.

## Phase 3: Advanced Game Mechanics & Objective Implementation (Completed)

- **Objective:** Implement more advanced game mechanics, fully support "The First Night" objective with all its rules, and prepare for more objectives.
- **Key Tasks:**
  - [x] Full Nightmare Creep logic for "The First Night" (discard or sacrifice spirit).
    - [x] (Covered by early Phase 4 PLAYER_CHOICE implementation)
  - [x] Implement "Haunt" keyword mechanics (return from discard, associated effects).
  - [x] Implement "Echo" keyword mechanics (effects on re-entry or specific conditions).
  - [x] Refine interaction between `ActionResolver` and `EffectEngine` for complex sequences.
  - [x] Track objective-specific progress (e.g., distinct toys played, mana from effects).
  - [x] Implement remaining cards relevant to "The First Night" and common mechanics.
  - [x] Advanced test cases including multi-turn scenarios and complex interactions for "The First Night".
  - [x] Ensure First Memory interactions are robust across various zones and states.

## Phase 4: Player Choice, AI Enhancement & Multi-Objective Foundation (In Progress)

- **Objective:** Introduce systems for handling player choices within effects, make the AI more capable of handling these choices, and lay the groundwork for easily adding more objectives.
- **Key Tasks:**
  - [x] Design and implement `PLAYER_CHOICE` action type in `EffectEngine`.
    - [x] `PlayerChoiceType` enum defined.
    - [x] `CHOOSE_YES_NO` implemented and tested (e.g., for "Echo Bear" like effects).
    - [x] `DISCARD_CARD_OR_SACRIFICE_SPIRIT` implemented and tested (handles Nightmare Creep for "The First Night").
      - [x] Successfully triggers `DISCARD_CARDS_CHOSEN_FROM_HAND` or `SACRIFICE_RESOURCE`.
    - [x] `CHOOSE_CARD_FROM_HAND` (as sub-choice for discard) implemented and tested.
    - [x] `CANCEL_IMPENDING_LEAVE_PLAY` action implemented and tested.
  - [ ] Implement other `PlayerChoiceType` enum values as needed by card effects:
    - [ ] `CHOOSE_TARGET_FOR_EFFECT` (e.g., choose a Toy in play, card in discard).
      - [ ] Define how options are presented (list of `CardInPlay` instances, `Card` definitions).
      - [ ] Implement AI logic to select from these targets.
    - [ ] `ORDER_CARDS` (e.g., for "Browse deck and reorder").
    - [ ] `DISTRIBUTE_RESOURCES` (e.g., distribute N counters among M targets).
    - [ ] `CHOOSE_MODE` (for modal spells/effects: "Choose one - ...; or Choose one - ...").
  - [ ] Refine `AIPlayerBase` and `RandomAI` to handle a wider variety of `PlayerChoiceType` options.
    - [ ] Ensure `RandomAI` can intelligently pick from provided valid options for new choice types.
  - [ ] Implement a selection of cards from `cards.json` that heavily utilize `PLAYER_CHOICE` to drive development.
    - [ ] Example: "Patchwork Pal" (Choose a counter type), "Moment of Lucidity" (Choose card from discard).
  - [ ] Begin structuring for multiple objectives:
    - [ ] Ensure `ObjectiveCard` class can define varied Nightmare Creep effects that leverage `PLAYER_CHOICE`.
    - [ ] Ensure win condition checking is flexible.
  - [ ] Comprehensive testing for all implemented player choice scenarios.

## Phase 5: Simulation Expansion & Initial Analysis

- **Objective:** Run simulations for multiple games, implement data logging for key metrics, and perform initial balance analysis based on "The First Night".
- **Key Tasks:**
  - [ ] Simulation Runner: Configure and run batches of simulations (e.g., 100s or 1000s of games).
  - [ ] Data Logging:
    - [ ] Log win/loss rates.
    - [ ] Log turn count for game end.
    - [ ] Log reasons for win/loss (primary, alternative, nightfall).
    - [ ] Log key objective progress metrics (e.g., spirits created, mana from effects for "The First Night").
    - [ ] Log usage/impact of First Memory.
  - [ ] Basic Analysis Engine:
    - [ ] Read logged data.
    - [ ] Calculate and display summary statistics (mean, median, std dev for key metrics).
    - [ ] Generate simple plots/histograms for distributions.
  - [ ] UI for Results: Basic textual or simple graphical display of simulation results.
  - [ ] Implement 2-3 more distinct objectives with their unique rules, creep effects, and win conditions.
    - [ ] Test these objectives with the simulation runner.
  - [ ] Refine AI for better decision-making based on observed simulation patterns (if time allows, otherwise basic RandomAI is fine for initial metrics).

## Phase 6: Advanced AI, Broader Objective Coverage & Balancing

- **Objective:** Develop more sophisticated AI profiles, implement most/all remaining objectives, and use simulation data for comprehensive game balance analysis and card adjustments.
- **Key Tasks:**
  - [ ] AI Profiles:
    - [ ] Develop an AI that prioritizes specific win conditions.
    - [ ] Develop an AI that might attempt to play more "thematically" or use specific card combos.
  - [ ] Implement all remaining defined Objective cards.
  - [ ] Full `cards.json` Implementation: Aim to implement effects for all (or nearly all) cards.
  - [ ] Advanced Simulation Analysis:
    - [ ] Compare performance across different objectives and AI profiles.
    - [ ] Identify under/overpowered cards or mechanics.
    - [ ] Analyze resource curves (mana, spirits, memory tokens) across game length.
  - [ ] Balancing Iteration:
    - [ ] Propose and (optionally) implement adjustments to card costs/effects or objective parameters based on analysis.
    - [ ] Re-run simulations to test impact of balance changes.
  - [ ] Documentation: Finalize documentation for simulator usage and findings.

## Post-Launch / Future Enhancements

- [ ] User Interface for configuring simulations (beyond script parameters).
- [ ] More detailed "play-by-play" game log replay feature.
- [ ] Integration with a database for storing and querying large-scale simulation results.
- [ ] Machine Learning approaches for AI player strategies or balance testing.
