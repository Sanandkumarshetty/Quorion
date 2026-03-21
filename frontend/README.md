# Front End Impemnt

Standalone UI package based on your `wireframe.docx`, built so you can integrate it later with your Python quiz logic.

## Structure

- `frontend/`: React + Vite UI with wireframe-based screens
- `flask_api/`: lightweight Flask stub with sample endpoints

## Included screens

- Landing page
- Account type selection
- Student/admin auth portal
- Student dashboard
- Waiting room
- Live quiz session
- Leaderboard
- Admin dashboard
- Quiz creation page

## Run the React app

```bash
cd front_end_impemnt/frontend
npm install
npm run dev
```

## Run the Flask stub

```bash
cd front_end_impemnt/flask_api
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

## Later integration path

1. Replace the mock data in `frontend/src/data/mockData.js` with API calls to your Python backend.
2. Keep the current route structure and connect forms and buttons to your Flask or existing Python services.
3. Move the Flask stub routes into your real backend once your quiz, auth, and leaderboard logic is ready.
