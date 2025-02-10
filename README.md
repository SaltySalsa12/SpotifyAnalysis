# Spotify Analytics Dashboard 🎵📊

[![Python](https://img.shields.io/badge/Python-3.12%2B-blue)](https://www.python.org/)
[![React](https://img.shields.io/badge/React-18.2%2B-%2361DAFB)](https://react.dev/)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

A full-stack web application that analyzes Spotify listening habits, predicts track-skipping behavior using machine learning, and visualizes user engagement trends.

![Dashboard Screenshot](screenshot.png) --[Work in Progress --Coming Soon]

## Features ✨

- **ML-Powered Predictions**  
  - Skip probability prediction (Random Forest Classifier)  
  - Session duration estimation (Gradient Boosting Regressor)  
- **Interactive Visualizations**  
  - Hourly listening heatmaps (Chart.js)  
  - Top skipped tracks table  
  - Artist playtime rankings  
- **Analytics**  
  - Total plays/month  
  - Most-played tracks  
  - Platform usage breakdown  
--And More Coming Soon

## Tech Stack 🛠️

| Category       | Technologies                                                                 |
|----------------|------------------------------------------------------------------------------|
| **Frontend**   | React, Chart.js, CSS Modules, Axios                                         |
| **Backend**    | Flask, REST API, Flask-CORS                                                 |
| **ML**         | Scikit-learn, Pandas, NumPy                                                 |
| **Database**   | SQLite, SQLAlchemy (ORM)                                                   |
| **Tools**      | Git, Webpack, ESLint, Postman                                               |

## Installation 🚀

### Prerequisites
- Python 3.12+
- Node.js 18.x
- SQLite

### Setup
1. **Clone the Repository**  
   ```bash
   git clone https://github.com/yourusername/spotify-analytics-dashboard.git
   cd spotify-analytics-dashboard

2. **Backend Setup**
    cd backend
    pip install -r requirements.txt
    python app.py  # Starts Flask server at http://localhost:5000

3. **Frontend Setup**
   cd frontend
   npm install
   npm start  # Starts React app at http://localhost:3000


API Endpoints 🌐
Endpoint	Method	Description
/api/ml/predict-skip	POST	Predict skip probability for a track
/api/basic/most-played-tracks	GET	Fetch top 10 played tracks
/api/visualization/activity	GET	Get hourly listening activity data
