# Tuck'd-In Terrors Monte Carlo Simulator - Web Interface

A Flask-based web interface for the Tuck'd-In Terrors Monte Carlo game simulator.

## Quick Start

### 1. Install Dependencies

```bash
cd web_app
pip install -r requirements.txt
```

Or if using uv:

```bash
uv pip install -r requirements.txt
```

### 2. Run the Server

```bash
python app.py
```

### 3. Access the Application

Open your browser and navigate to:

```
http://127.0.0.1:5000
```

## Features

### Home Page
- **Objective Selection**: Choose from 8 available game objectives
- **AI Profile Selection**: Pick from 3 AI strategies (Random, Greedy, Scoring)
- **Simulation Configuration**: Set number of simulations (1-10,000)
- **Visualization Options**: Optionally generate charts and graphs
- **Real-time Progress**: Live progress bar during simulation execution

### Results Page
- **Win Rate Overview**: Overall win percentage with visual progress bar
- **Statistics Dashboard**:
  - Total wins/losses breakdown
  - Average turns for wins and losses
  - Fastest and slowest win times
- **Performance Scorecard**: Auto-generated analysis with insights and recommendations
- **Visualizations**: Pie charts and histograms (if enabled)
- **Data Export**: Download complete results as JSON

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Home page with simulation form |
| `/simulate` | POST | Start a new simulation |
| `/status/<sim_id>` | GET | Get simulation progress status |
| `/results/<sim_id>` | GET | Get simulation results (JSON) |
| `/results/<sim_id>/view` | GET | View results page (HTML) |
| `/chart/<sim_id>/<chart_type>` | GET | Serve chart images (pie/histogram) |
| `/download/<sim_id>` | GET | Download raw results as JSON |

## Architecture

```
web_app/
├── app.py                 # Flask application with routes
├── templates/
│   ├── index.html         # Home page with simulation form
│   └── results.html       # Results display page
├── static/
│   └── js/
│       └── main.js        # Client-side JavaScript
├── requirements.txt       # Python dependencies
└── README.md             # This file
```

## How It Works

1. **User submits form** on home page with simulation parameters
2. **Flask endpoint `/simulate`** starts a background thread to run the simulation
3. **Client polls `/status/<sim_id>`** every 500ms for progress updates
4. **Progress bar updates** in real-time as simulation runs
5. **On completion**, user is redirected to results page
6. **Results page loads** data via AJAX and displays comprehensive analysis

## Technology Stack

- **Backend**: Flask 3.0+
- **Frontend**: Tailwind CSS 3.0 (CDN)
- **Charts**: Matplotlib (server-side rendering)
- **Data Format**: JSON
- **Storage**: In-memory (no database for MVP)

## Configuration

### Performance Notes

- Simulations run at ~1,000+ games per minute
- Recommended simulation counts:
  - **Quick test**: 100 simulations (~5 seconds)
  - **Standard analysis**: 1,000 simulations (~50 seconds)
  - **Comprehensive**: 10,000 simulations (~8-10 minutes)

### Memory Usage

Results are stored in-memory and will be lost when the server restarts. For production use, consider adding database persistence.

## Tips

- Start with 100 simulations to test quickly
- Use "Scoring AI" for most realistic gameplay analysis
- Enable visualizations for comprehensive reports
- Download JSON results for external analysis
- Run multiple simulations with different AI profiles to compare strategies

## Troubleshooting

### Port Already in Use

If port 5000 is already in use, modify the last line in `app.py`:

```python
app.run(debug=True, host='127.0.0.1', port=5001)  # Change port
```

### Module Import Errors

Ensure you're running from the `web_app` directory and the parent project structure is intact.

### Slow Performance

- Reduce number of simulations
- Disable visualizations for faster results
- Check system resources (CPU usage)

## Future Enhancements

- Database persistence (SQLite/PostgreSQL)
- Historical simulation comparison
- Multi-user session support
- Real-time WebSocket updates (instead of polling)
- Batch comparison mode (multiple AI profiles at once)
- Export to CSV/Excel formats
- Advanced filtering and search

## Development

### Debug Mode

Debug mode is enabled by default. To disable for production:

```python
app.run(debug=False, host='0.0.0.0', port=5000)
```

### Adding New Routes

Follow the existing pattern in `app.py`:

```python
@app.route('/your-route')
def your_function():
    # Your logic here
    return render_template('your_template.html')
```

## License

Same as parent project.
