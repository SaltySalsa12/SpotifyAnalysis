# Spotify Analytics Dashboard 🎵📊
[![Python](https://img.shields.io/badge/Python-3.12%2B-blue)](https://www.python.org/)
[![React](https://img.shields.io/badge/React-18.2%2B-%2361DAFB)](https://react.dev/)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

SQL Data Analysis Queries 🔍📈
The following SQL queries power the analytics engine for Spotify listening history analysis. Executed in SQL Server Management Studio (SSMS), these T-SQL scripts extract key insights from streaming history data.

Basic Analytics
Summary Metrics

SELECT COUNT(*) as total_plays                    -- Total tracks played
SELECT COUNT(DISTINCT [Track Name])               -- Unique songs
SELECT COUNT(DISTINCT Artist)                     -- Unique artists
Calculates foundational metrics for dashboard overview cards.

Top Content Analysis

-- Top 10 tracks by total listening time
SELECT TOP 10 [Track Name], Artist, ... 
ORDER BY total_seconds_played DESC

-- Most-played artists with hours listened
SELECT Artist, COUNT(*) AS Total_Plays, ... 
ORDER BY Total_Hours_Played DESC
Powers the "Top Tracks" and "Artist Rankings" visualizations.

Intermediate Analysis
Temporal Patterns

-- Hourly listening heatmap (grouped into Morning/Afternoon/Evening/Night)
WITH listening_patterns AS (...)

-- Day-of-week analysis with average track duration
SELECT DATENAME(WEEKDAY, Timestamp) as Day_Of_Week...
Feeds the hourly heatmap and weekly trends charts.

Skip Behavior

SELECT [Track Name], Artist, 
       ROUND(...) AS Skip_Percentage
HAVING COUNT(*)>=5
Identifies tracks with >5 plays and their skip rates for ML training data.

Advanced Analysis
Session Detection

WITH session_breaks AS (...)
SELECT session_id, session_start, session_end...
Uses 30-minute gaps between plays to define listening sessions.

Artist Discovery Timeline

WITH first_listen AS (...)
SELECT day_of_week + ', ' + CAST(day AS VARCHAR)...
Tracks when new artists were first played (formatted as "Tuesday, 3rd April 2024").

Key Technical Notes
Duration Conversion: Uses CHARINDEX and SUBSTRING to convert MM:SS durations to seconds

CAST(SUBSTRING([Duration...])*60 + CAST(SUBSTRING(...))
Temporal Functions: Leverages DATEPART() and DATENAME() for time-based aggregations.

Data Filtering: Excludes null values for [Track Name] and Artist in critical queries.

These queries directly feed into the dashboard's Chart.js visualizations and ML models through Flask API endpoints. See the SpotifyQueries.sql file for full implementation details.

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



