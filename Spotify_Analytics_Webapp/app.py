# backend/app.py
import re
from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import pandas as pd
import logging
import traceback
from ml_model import SpotifyMLAnalyzer

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "http://localhost:3000"}})

# Configure logging
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter(
    '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
))
app.logger.addHandler(handler)
app.logger.setLevel(logging.DEBUG)

# Initialize ML system
ml_analyzer = SpotifyMLAnalyzer()

def load_training_data():
    conn = sqlite3.connect('spotify.db')
    query = """
        SELECT Timestamp, Artist, "Track Name" AS Track_Name, Album,
               Platform, "Duration (MM:SS)" AS Duration, Skipped
        FROM spotify_history
        WHERE Timestamp IS NOT NULL
          AND Artist IS NOT NULL
          AND "Track Name" IS NOT NULL
          AND "Duration (MM:SS)" IS NOT NULL
          AND Skipped IS NOT NULL
    """
    df = pd.read_sql(query, conn)
    conn.close()
    
    valid_durations = df['Duration'].str.match(r'^\d+:\d{2}$')
    return df[valid_durations]

# Train models during startup
try:
    app.logger.info("Initializing ML models...")
    df = load_training_data()
    
    if df.empty:
        raise RuntimeError("No valid training data available")
        
    ml_analyzer.train_skip_predictor(df)
    ml_analyzer.train_duration_predictor(df)
    app.logger.info("ML models trained successfully")
    
except Exception as e:
    app.logger.error(f"Model training failed: {str(e)}")
    traceback.print_exc()
    exit(1)

# API Endpoints
@app.route('/api/ml/predict-skip', methods=['POST'])
def predict_skip():
    try:
        data = request.json
        required = ['Timestamp', 'Artist', 'Track_Name', 'Album', 'Duration']
        if missing := [field for field in required if field not in data]:
            return jsonify({"error": "Missing fields", "missing": missing}), 400
            
        if not re.match(r'^\d+:\d{2}$', data['Duration']):
            return jsonify({"error": "Invalid duration format"}), 400

        input_df = pd.DataFrame([{
            'Timestamp': data['Timestamp'],
            'Artist': data['Artist'],
            'Track_Name': data['Track_Name'],
            'Album': data['Album'],
            'Platform': data.get('Platform', 'Spotify'),
            'Duration': data['Duration']
        }])

        probabilities = ml_analyzer.predict_skip_probability(input_df)
        return jsonify({
            "probability": float(probabilities[0]),
            "status": "success"
        })
        
    except Exception as e:
        app.logger.error(f"Skip prediction error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/ml/predict-session-duration', methods=['POST'])
def predict_session_duration():
    try:
        data = request.json
        required = ['Timestamp', 'Artist', 'Track_Name', 'Album', 'Duration']
        if missing := [field for field in required if field not in data]:
            return jsonify({"error": "Missing fields", "missing": missing}), 400

        input_df = pd.DataFrame([{
            'Timestamp': data['Timestamp'],
            'Artist': data['Artist'],
            'Track_Name': data['Track_Name'],
            'Album': data['Album'],
            'Platform': data.get('Platform', 'Spotify'),
            'Duration': data['Duration']
        }])

        duration = ml_analyzer.predict_session_duration(input_df)
        return jsonify({
            "duration_minutes": float(duration[0] / 60),
            "status": "success"
        })
        
    except Exception as e:
        app.logger.error(f"Duration prediction error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/basic/total-plays', methods=['GET'])
def total_plays():
    conn = sqlite3.connect('spotify.db')
    query = "SELECT COUNT(*) as total_plays FROM spotify_history"
    result = pd.read_sql(query, conn).to_dict(orient='records')
    conn.close()
    return jsonify(result)

@app.route('/api/basic/most-played-tracks', methods=['GET'])
def most_played_tracks():
    conn = sqlite3.connect('spotify.db')
    query = """
        SELECT "Track Name", Artist, COUNT(*) as play_count
        FROM spotify_history
        GROUP BY "Track Name", Artist
        ORDER BY play_count DESC
        LIMIT 10;
    """
    result = pd.read_sql(query, conn).to_dict(orient='records')
    conn.close()
    return jsonify(result)

@app.route('/api/basic/artist-playtime', methods=['GET'])
def artist_playtime():
    conn = sqlite3.connect('spotify.db')
    query = """
        SELECT 
            Artist,
            COUNT(*) AS Total_Plays,
            ROUND(SUM(
                CAST(substr("Duration (MM:SS)", 1, instr("Duration (MM:SS)", ':') - 1) AS INTEGER) * 60 + 
                CAST(substr("Duration (MM:SS)", instr("Duration (MM:SS)", ':') + 1) AS INTEGER)
            ) / 3600.0, 2) as Total_Hours_Played
        FROM spotify_history
        WHERE Artist IS NOT NULL
        GROUP BY Artist
        ORDER BY Total_Hours_Played DESC
        limit 10;
    """
    try:
        result = pd.read_sql(query, conn).to_dict(orient='records')
        conn.close()
        return jsonify(result)
    except Exception as e:
        conn.close()
        return jsonify({"error": str(e)}), 500

# ---------------------------
# Visualization Queries
# ---------------------------
@app.route('/api/visualization/activity-stackedbarchart', methods=['GET'])
def activity_heatmap():
    conn = sqlite3.connect('spotify.db')
    query = """
        SELECT 
            strftime('%H', Timestamp) AS hour,
            strftime('%w', Timestamp) AS day_of_week,
            COUNT(*) AS plays
        FROM spotify_history
        GROUP BY hour, day_of_week
        ORDER BY day_of_week, hour;
    """
    result = pd.read_sql(query, conn)
    conn.close()

    # Convert day_of_week (0-6, where 0=Sunday) to (0-6, where 0=Monday)
    result['day_of_week'] = (result['day_of_week'].astype(int) - 1) % 7
    return jsonify(result.to_dict(orient='records'))

# ---------------------------
# Intermediate Queries
# ---------------------------
@app.route('/api/intermediate/skip-analysis', methods=['GET'])
def skip_analysis():
    try:
        conn = sqlite3.connect('spotify.db')
        query = """
            SELECT 
                Artist, 
                "Track Name" AS track_name,
                COUNT(*) AS total_plays,
                SUM(CASE WHEN Skipped = 'Yes' THEN 1 ELSE 0 END) AS skips,
                ROUND((SUM(CASE WHEN Skipped = 'Yes' THEN 1 ELSE 0 END) * 100.0) / COUNT(*), 1) AS skip_rate
            FROM spotify_history
            GROUP BY Artist, "Track Name"
            HAVING total_plays >= 5  -- Only include tracks with at least 5 total plays
            ORDER BY skips DESC
            LIMIT 20;
        """
        result = pd.read_sql(query, conn).to_dict(orient='records')
        conn.close()
        return jsonify({
            'count': len(result),
            'data': result
        })
    except sqlite3.Error as e:
        return jsonify({'error': f'Database error: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)