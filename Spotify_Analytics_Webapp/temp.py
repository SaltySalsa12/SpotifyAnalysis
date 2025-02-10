# backend/app.py
from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.ensemble import RandomForestClassifier, GradientBoostingRegressor
from sklearn.metrics import accuracy_score, mean_squared_error, classification_report
from datetime import datetime

app = Flask(__name__)
CORS(app)  # Enable CORS for React frontend

# ---------------------------
# Basic Queries
# ---------------------------
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

# ---------------------------
# Advanced Queries
# ---------------------------
@app.route('/api/advanced/listening-sessions', methods=['GET'])
def listening_sessions():
    conn = sqlite3.connect('spotify.db')
    query = """
        WITH session_breaks AS (
    SELECT 
        *,
        CASE 
            WHEN TIMESTAMPDIFF(MINUTE, 
                LAG(Timestamp) OVER (ORDER BY Timestamp),
                Timestamp) > 30 
            THEN 1 
            ELSE 0 
        END as new_session
    FROM spotify_history
),
sessions AS (
    SELECT 
        *,
        SUM(new_session) OVER (ORDER BY Timestamp) as session_id
    FROM session_breaks
)
SELECT 
    session_id,
    MIN(Timestamp) as session_start,
    MAX(Timestamp) as session_end,
    COUNT(*) as tracks_played,
    COUNT(DISTINCT Artist) as unique_artists,
    SUM(CAST(SUBSTRING_INDEX(Duration, ':', 1) AS INTEGER) * 60 + 
        CAST(SUBSTRING_INDEX(Duration, ':', -1) AS INTEGER))/60.0 as session_duration_minutes
FROM sessions
GROUP BY session_id
ORDER BY session_start;
    """  # Use your full query from spotify-sql-queries.sql
    result = pd.read_sql(query, conn).to_dict(orient='records')
    conn.close()
    return jsonify(result)

class SpotifyMLAnalyzer:
    def __init__(self):
        self.label_encoders = {}
        self.scaler = StandardScaler()
        self.skip_predictor = None
        self.duration_predictor = None
    
    def preprocess_data(self, df):
        """Preprocess the Spotify history data for ML models."""
        # Create temporal features
        df['hour'] = pd.to_datetime(df['Timestamp']).dt.hour
        df['day_of_week'] = pd.to_datetime(df['Timestamp']).dt.dayofweek
        df['month'] = pd.to_datetime(df['Timestamp']).dt.month
        df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int)
        
        # Convert duration to seconds
        df['duration_seconds'] = df['Duration'].apply(
            lambda x: sum(int(i) * 60**idx for idx, i in enumerate(reversed(str(x).split(':'))))
        )
        
        # Create frequency-based features
        artist_plays = df['Artist'].value_counts()
        df['artist_popularity'] = df['Artist'].map(artist_plays)
        
        track_plays = df['Track_Name'].value_counts()
        df['track_popularity'] = df['Track_Name'].map(track_plays)
        
        # Encode categorical variables
        categorical_cols = ['Artist', 'Track_Name', 'Platform']
        for col in categorical_cols:
            if col not in self.label_encoders:
                self.label_encoders[col] = LabelEncoder()
                df[f'{col}_encoded'] = self.label_encoders[col].fit_transform(df[col])
            else:
                # Handle new categories in test data
                df[f'{col}_encoded'] = df[col].map(
                    dict(zip(self.label_encoders[col].classes_, 
                           self.label_encoders[col].transform(self.label_encoders[col].classes_)))
                ).fillna(-1)
        
        return df
    
    def prepare_features(self, df):
        """Prepare feature matrix for ML models."""
        feature_cols = [
            'hour', 'day_of_week', 'month', 'is_weekend',
            'artist_popularity', 'track_popularity',
            'Artist_encoded', 'Track_Name_encoded', 'Platform_encoded'
        ]
        
        X = df[feature_cols]
        return self.scaler.fit_transform(X)
    
    def train_skip_predictor(self, df):
        """Train a model to predict if a track will be skipped."""
        processed_df = self.preprocess_data(df)
        X = self.prepare_features(processed_df)
        y = (processed_df['Skipped'] == 'Yes').astype(int)
        
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        self.skip_predictor = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42
        )
        
        self.skip_predictor.fit(X_train, y_train)
        
        # Evaluate the model
        y_pred = self.skip_predictor.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        report = classification_report(y_test, y_pred)
        
        return {
            'accuracy': accuracy,
            'classification_report': report,
            'feature_importance': dict(zip(
                ['hour', 'day_of_week', 'month', 'is_weekend',
                 'artist_popularity', 'track_popularity',
                 'Artist_encoded', 'Track_Name_encoded', 'Platform_encoded'],
                self.skip_predictor.feature_importances_
            ))
        }
    
    def train_duration_predictor(self, df):
        """Train a model to predict listening session durations."""
        processed_df = self.preprocess_data(df)
        
        # Create listening sessions (30-minute gap between plays)
        processed_df['timestamp'] = pd.to_datetime(processed_df['Timestamp'])
        processed_df = processed_df.sort_values('timestamp')
        processed_df['time_diff'] = processed_df['timestamp'].diff()
        processed_df['new_session'] = processed_df['time_diff'] > pd.Timedelta(minutes=30)
        processed_df['session_id'] = processed_df['new_session'].cumsum()
        
        # Aggregate sessions
        session_features = processed_df.groupby('session_id').agg({
            'hour': 'first',
            'day_of_week': 'first',
            'month': 'first',
            'is_weekend': 'first',
            'artist_popularity': 'mean',
            'track_popularity': 'mean',
            'duration_seconds': 'sum'
        }).reset_index()
        
        X = self.scaler.fit_transform(session_features.drop(['session_id', 'duration_seconds'], axis=1))
        y = session_features['duration_seconds']
        
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        self.duration_predictor = GradientBoostingRegressor(
            n_estimators=100,
            max_depth=5,
            random_state=42
        )
        
        self.duration_predictor.fit(X_train, y_train)
        
        # Evaluate the model
        y_pred = self.duration_predictor.predict(X_test)
        mse = mean_squared_error(y_test, y_pred)
        rmse = np.sqrt(mse)
        
        return {
            'rmse_seconds': rmse,
            'feature_importance': dict(zip(
                ['hour', 'day_of_week', 'month', 'is_weekend',
                 'artist_popularity', 'track_popularity'],
                self.duration_predictor.feature_importances_
            ))
        }
    
    def predict_skip_probability(self, new_data):
        """Predict the probability of skipping a track."""
        processed_data = self.preprocess_data(new_data)
        X = self.prepare_features(processed_data)
        return self.skip_predictor.predict_proba(X)[:, 1]
    
    def predict_session_duration(self, new_data):
        """Predict the duration of a listening session."""
        processed_data = self.preprocess_data(new_data)
        X = self.scaler.transform(processed_data[
            ['hour', 'day_of_week', 'month', 'is_weekend',
             'artist_popularity', 'track_popularity']
        ])
        return self.duration_predictor.predict(X)

# Initialize the ML analyzer
ml_analyzer = SpotifyMLAnalyzer()

# Load your Spotify history data into a DataFrame
# Replace this with your actual data loading logic
df = pd.read_csv('spotify_history.csv')  # Example: Load data from a CSV file
ml_analyzer.train_skip_predictor(df)  # Train the skip predictor
ml_analyzer.train_duration_predictor(df)  # Train the duration predictor

# ---------------------------
# ML Endpoints
# ---------------------------
@app.route('/api/ml/predict-skip', methods=['POST'])
def predict_skip():
    """Predict the probability of skipping a track."""
    data = request.json
    new_track = pd.DataFrame([data])
    skip_probability = ml_analyzer.predict_skip_probability(new_track)
    return jsonify({"probability": float(skip_probability[0])})

@app.route('/api/ml/predict-session-duration', methods=['POST'])
def predict_session_duration():
    """Predict the duration of a listening session."""
    data = request.json
    new_track = pd.DataFrame([data])
    session_duration = ml_analyzer.predict_session_duration(new_track)
    return jsonify({"duration_minutes": float(session_duration[0] / 60)})

if __name__ == '__main__':
    app.run(debug=True)