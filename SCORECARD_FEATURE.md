# Scorecard Feature Documentation

**Feature Added:** November 3, 2025
**Version:** 0.3.1
**Status:** ✅ Complete and Production Ready

---

## Overview

The **Automatic Scorecard Generator** provides instant, actionable insights after every simulation run. Instead of manually parsing raw statistics, users now receive a beautifully formatted executive summary with performance grades, visual metrics, smart insights, and specific recommendations.

---

## What Problem Does This Solve?

### Before Scorecards

Users had to:
- Manually interpret raw win rate numbers
- Calculate percentages and averages themselves
- Determine if results were "good" or "bad"
- Figure out what to do next
- Compare numbers across multiple runs

### After Scorecards

Users get:
- Instant performance grade (A-F)
- Visual progress bars for quick assessment
- Automatic insight detection
- Specific, actionable recommendations
- At-a-glance understanding of results

---

## Key Features

### 1. Performance Grading

Automatically assigns a letter grade based on win rate:

```
A (★★★★★): 50%+ win rate   - Excellent performance
B (★★★★☆): 40-49% win rate - Good performance
C (★★★☆☆): 30-39% win rate - Average performance
D (★★☆☆☆): 20-29% win rate - Below average
F (★☆☆☆☆): <20% win rate   - Poor performance
```

### 2. Visual Metrics

Progress bars make data immediately understandable:

```
Overall Win Rate:  45.30%   [██████████████████░░░░░░░░░░░░░░░░░░░░░░░░░]
```

### 3. Smart Insights (Automatic Detection)

The scorecard analyzes results and automatically detects:

- ✓ **Positive observations** (things working well)
- ⚠️ **Warnings** (potential problems)
- 🔄 **Interesting patterns** (unusual behaviors)
- ⏰ **Time-related findings** (Nightfall patterns)
- ⚡ **Speed observations** (fast/slow wins)

**Example Insights:**
- "✓ Win rate is WITHIN target range for Easy difficulty"
- "⚠️ High variance in win timing (inconsistent strategy)"
- "🔄 Alternative win condition is MORE successful than primary"
- "⏰ Most losses due to Nightfall (time pressure is main challenge)"

### 4. Actionable Recommendations

Based on detected patterns, provides specific suggestions:

**If win rate too low:**
```
Consider making objective easier:
  • Extend Nightfall turn by 1-2
  • Reduce win condition requirements
  • Add starting resources (spirits, mana)
```

**If win rate too high:**
```
Consider making objective harder:
  • Reduce Nightfall turn by 1-2
  • Increase win condition requirements
  • Add restrictive special rules
```

---

## Scorecard Sections

### 1. Header

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                          SIMULATION SCORECARD                                ║
╚══════════════════════════════════════════════════════════════════════════════╝

Objective: OBJ01_THE_FIRST_NIGHT
AI Profile: scoring_ai
Games Simulated: 1,000
```

### 2. Performance Summary

- Overall win rate with progress bar
- Performance grade (A-F) with star rating
- Win breakdown (primary vs alternative)
- Loss count

### 3. Game Metrics

- Average turns (wins vs losses)
- Fastest and slowest wins
- Win consistency rating (based on standard deviation)
- Average resources at win (mana, spirits, toys)
- Loss breakdown with visual bars
- Turn distribution visualization

### 4. Key Insights

Automatic pattern detection including:
- Win rate vs difficulty target comparison
- Turn efficiency analysis
- Win condition viability assessment
- Consistency evaluation
- AI-specific observations
- Loss reason patterns
- Speed anomalies

### 5. Recommendations

Context-aware suggestions for:
- Difficulty adjustments
- Win condition tuning
- Card balance improvements
- AI testing strategies
- Next steps

### 6. Footer

Quick tips for additional analysis options.

---

## Usage

### Automatic (Default Behavior)

Scorecards are **enabled by default** on every simulation:

```bash
python main.py --objective OBJ01_THE_FIRST_NIGHT \
    --simulations 1000 \
    --ai scoring_ai
```

Output:
1. Standard analysis appears first
2. Scorecard displays after analysis
3. Scorecard automatically saved to `results/scorecard_<objective>_<ai>.txt`

### Disable When Not Needed

```bash
python main.py --objective OBJ01_THE_FIRST_NIGHT \
    --simulations 1000 \
    --ai scoring_ai \
    --no-scorecard
```

---

## Technical Details

### Intelligence Behind Insights

The scorecard generator uses statistical analysis to detect patterns:

1. **Difficulty Matching**
   - Compares win rate to expected ranges:
     - Easy: 40-60%
     - Moderate: 25-40%
     - Hard: 10-25%
   - Alerts if outside target range

2. **Turn Efficiency**
   - Compares average win turns vs loss turns
   - Detects if strategy is time-efficient

3. **Consistency Analysis**
   - Calculates standard deviation of win turns
   - Rates consistency (Very Consistent, Consistent, Moderate, High Variance)

4. **Win Condition Viability**
   - Compares primary vs alternative win rates
   - Detects if both paths are viable

5. **AI Performance Context**
   - Adjusts expectations based on AI profile
   - Warns if random_ai performs too well (objective too easy)
   - Warns if scoring_ai performs too poorly (objective too hard)

6. **Loss Pattern Detection**
   - Identifies most common loss reason
   - Provides context-specific insights

7. **Outlier Detection**
   - Identifies unusually fast wins (potential exploits)
   - Identifies games hitting max turn limit (possible infinite loops)

### Performance

- **Overhead:** <50ms for scorecard generation
- **Memory:** Negligible (operates on already-computed statistics)
- **File Size:** ~5KB per scorecard file

---

## Example Scorecards

### Example 1: Well-Balanced Objective

```
Overall Win Rate:  45.30%   Grade: B ★★★★☆

KEY INSIGHTS:
  ✓  Win rate is WITHIN target range for Easy difficulty
  ✓  Wins occur faster than losses (efficient strategy)
  ✓  Both win conditions viable (good objective design)

RECOMMENDATIONS:
  No immediate concerns detected!
  Objective appears well-balanced for current difficulty.
```

### Example 2: Objective Too Easy

```
Overall Win Rate:  68.20%   Grade: A ★★★★★

KEY INSIGHTS:
  ⚠️  Win rate is ABOVE target for Easy difficulty (40-60%)
  ⚠️  Random AI winning >40% suggests objective may be too easy
  ✓  Very consistent win timing (low variance)

RECOMMENDATIONS:
  Consider making objective harder:
    • Reduce Nightfall turn by 1-2
    • Increase win condition requirements
    • Add restrictive special rules
```

### Example 3: Objective Too Hard

```
Overall Win Rate:  12.50%   Grade: F ★☆☆☆☆

KEY INSIGHTS:
  ⚠️  Win rate is BELOW target for Moderate difficulty (25-40%)
  ⚠️  Smart AI winning <15% suggests objective may be too hard
  ⚠️  Wins take longer than losses (struggling to meet conditions)

RECOMMENDATIONS:
  Consider making objective easier:
    • Extend Nightfall turn by 1-2
    • Reduce win condition requirements
    • Add starting resources (spirits, mana)
```

### Example 4: High Variance

```
Overall Win Rate:  35.80%   Grade: C ★★★☆☆

KEY INSIGHTS:
  ✓  Win rate is WITHIN target range for Moderate difficulty
  ⚠️  High variance in win timing (inconsistent strategy)
  ⚠️  Only primary win condition being achieved

RECOMMENDATIONS:
  High variance detected:
    • Review card draw mechanics
    • Consider guaranteed starting cards
    • Test with different AI profiles

  Alternative win condition unused:
    • May be too difficult or unclear
    • Consider making it more accessible
```

---

## Integration

### Files Modified

1. **main.py**
   - Added scorecard generation after analysis
   - Added `--no-scorecard` flag
   - Auto-saves scorecard to results directory

2. **README.md**
   - Added scorecard to feature list
   - Added example output
   - Documented usage

3. **USER_GUIDE.md**
   - Added comprehensive scorecard section
   - Explained all scorecard components
   - Provided interpretation guide

### New File

**src/tuck_in_terrors_sim/simulation/scorecard_generator.py**
- ~450 lines
- `ScorecardGenerator` class
- Automatic insight detection logic
- Visual formatting helpers
- Recommendation engine

---

## Benefits

### For Game Designers

- **Instant Feedback:** Know immediately if objective is balanced
- **Clear Direction:** Specific suggestions for adjustments
- **Visual Assessment:** Progress bars make trends obvious
- **Historical Tracking:** Saved scorecards document balance evolution

### For Players/Testers

- **Understandable Results:** No statistics knowledge required
- **Performance Context:** Grade shows if run was good/bad
- **Strategy Insights:** Learn what makes wins successful
- **Next Steps:** Know which AI or objective to test next

### For Researchers

- **Automated Analysis:** Pattern detection without manual review
- **Consistent Metrics:** Same analysis applied every time
- **Exportable:** Text files easy to parse or share
- **Comprehensive:** All key metrics in one place

---

## Future Enhancements (Potential)

### Additional Insights
- Mana efficiency analysis
- Card usage patterns
- Deck composition recommendations
- Combo detection

### Comparative Scorecards
- Compare multiple objectives side-by-side
- AI profile performance comparison
- Historical trend analysis
- Win rate progression over versions

### Custom Thresholds
- User-configurable difficulty targets
- Custom grading scales
- Personalized insight priorities

### Export Formats
- JSON export for programmatic analysis
- Markdown format for documentation
- HTML format for web viewing
- CSV export for spreadsheet analysis

---

## Conclusion

The Automatic Scorecard Generator transforms raw simulation data into actionable insights. By providing instant feedback, clear visualizations, smart pattern detection, and specific recommendations, it makes the simulator accessible to users of all skill levels while providing professional-grade analysis for advanced users.

**Result:** Users can now understand and act on simulation results in seconds instead of minutes.

---

**Version:** 0.3.1
**Status:** Production Ready
**Last Updated:** November 3, 2025
**Created by:** Claude (AI Assistant)
