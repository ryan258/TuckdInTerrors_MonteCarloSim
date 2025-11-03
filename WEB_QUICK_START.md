# Quick Start Guide - Web Interface

## Your web interface is ready! 🎉

The Flask development server is now running at:

**http://127.0.0.1:5000**

---

## What You Can Do

### 1. Run Simulations
- Choose from 8 objectives (OBJ01-OBJ08)
- Select AI profile (Random, Greedy, or Scoring AI)
- Configure number of simulations (1-10,000)
- Enable visualizations for charts

### 2. View Results
- Win rate overview with visual progress bars
- Detailed statistics (avg turns, fastest/slowest wins)
- Performance scorecard with insights
- Charts (if enabled): Win/Loss pie chart + Turn distribution histogram
- Download raw results as JSON

---

## How to Access

1. Open your browser
2. Go to: **http://127.0.0.1:5000**
3. Fill out the simulation form
4. Click "Run Simulation"
5. Watch the progress bar
6. View comprehensive results!

---

## Stopping the Server

The server is currently running in the background. To stop it:

```bash
# Find the process
ps aux | grep "web_app/app.py"

# Kill it
kill <process_id>
```

Or simply close your terminal.

---

## Restarting the Server

If you need to restart the server later:

```bash
cd /Users/ryanjohnson/Projects/TuckdInTerrors_MonteCarloSim
.venv/bin/python web_app/app.py
```

---

## Features

✅ **Real-time Progress** - Live progress bar during simulations
✅ **Smart Analysis** - Automatic scorecard generation with insights
✅ **Visual Charts** - Pie charts and histograms (optional)
✅ **Fast Performance** - 1000+ games per minute
✅ **Data Export** - Download results as JSON
✅ **Responsive Design** - Clean, modern interface with Tailwind CSS

---

## Recommended Settings for Testing

**Quick Test:**
- Objective: OBJ01_THE_FIRST_NIGHT
- AI Profile: Scoring AI
- Simulations: 100
- Visualizations: ✓ Enabled

**Comprehensive Analysis:**
- Objective: Any
- AI Profile: Scoring AI
- Simulations: 1000-5000
- Visualizations: ✓ Enabled

---

## Troubleshooting

**Server won't start?**
- Make sure you're in the project root directory
- Ensure the virtual environment is active: `.venv/bin/activate`
- Check port 5000 isn't already in use

**Simulation errors?**
- Verify game data files exist: `data/cards.json`, `data/objectives.json`
- Check that all dependencies are installed: `uv pip install -r web_app/requirements.txt`

**Charts not showing?**
- Make sure you enabled "Generate visualizations" checkbox
- Charts are generated during simulation (adds ~2-3 seconds)

---

## File Locations

- **Web App Code**: `web_app/app.py`
- **Templates**: `web_app/templates/`
- **Static Files**: `web_app/static/`
- **Results**: `results/` (auto-created)
- **Virtual Environment**: `.venv/`

---

Enjoy your web-based Monte Carlo simulator! 🎲🎮
