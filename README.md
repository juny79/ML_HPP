# Leaderboard System

Simple scaffold for a prediction leaderboard system with a Flask backend and static frontend.

Structure:

- `backend/` — Flask app, routes, services, and models
- `frontend/` — static HTML/CSS/JS for submitting predictions and viewing leaderboard
- `data/` — ground truth and other data (ground_truth.csv is intentionally empty here)

To run locally:

```powershell
cd leaderboard_system
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python backend/app.py
```

Replace `data/ground_truth.csv` with your private dataset.
