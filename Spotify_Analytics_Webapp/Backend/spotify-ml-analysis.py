import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.ensemble import RandomForestClassifier, GradientBoostingRegressor
from sklearn.metrics import accuracy_score, mean_squared_error, classification_report
import xgboost as xgb
from datetime import datetime

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

# Example usage
if __name__ == "__main__":
    # Assuming df is your Spotify history DataFrame
    analyzer = SpotifyMLAnalyzer()
    
    # Train skip predictor
    skip_results = analyzer.train_skip_predictor(df)
    print("Skip Predictor Results:", skip_results)
    
    # Train duration predictor
    duration_results = analyzer.train_duration_predictor(df)
    print("Duration Predictor Results:", duration_results)
    
    # Make predictions for new data
    new_track = pd.DataFrame({
        'Timestamp': ['2024-01-22 14:30:00'],
        'Artist': ['Known Artist'],
        'Track_Name': ['Sample Track'],
        'Platform': ['Spotify'],
        'Duration': ['3:30']
    })
    
    skip_prob = analyzer.predict_skip_probability(new_track)
    print(f"Probability of skipping: {skip_prob[0]:.2f}")
    
    session_duration = analyzer.predict_session_duration(new_track)
    print(f"Predicted session duration: {session_duration[0]/60:.2f} minutes")
