# backend/ml_model.py
import pandas as pd
import numpy as np
import re
import logging
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.ensemble import RandomForestClassifier, GradientBoostingRegressor
from sklearn.exceptions import NotFittedError

logger = logging.getLogger(__name__)

class SpotifyMLAnalyzer:
    def __init__(self):
        self.skip_scaler = StandardScaler()
        self.duration_scaler = StandardScaler()
        self.label_encoders = {}
        self.skip_predictor = None
        self.duration_predictor = None
        self.feature_cols = {
            'skip': [
                'hour', 'day_of_week', 'month', 'is_weekend',
                'artist_popularity', 'track_popularity', 'album_popularity',
                'Artist_encoded', 'Track_Name_encoded', 'Album_encoded', 'Platform_encoded'
            ],
            'duration': [
                'hour', 'day_of_week', 'month', 'is_weekend',
                'artist_popularity', 'track_popularity'
            ]
        }

    def preprocess_data(self, df, is_training=True):
        try:
            df = df.copy()
            required_cols = [
                'Timestamp', 'Artist', 'Track_Name', 'Album',
                'Duration', 'Platform'
            ]
            if is_training:
                required_cols.append('Skipped')
            
            missing = [col for col in required_cols if col not in df.columns]
            if missing:
                raise ValueError(f"Missing columns: {missing}")

            # Temporal features
            df['parsed_time'] = pd.to_datetime(
                df['Timestamp'], errors='coerce', format='mixed'
            ).dt.tz_localize(None)
            
            df['hour'] = df['parsed_time'].dt.hour.astype('Int8')
            df['day_of_week'] = df['parsed_time'].dt.dayofweek.astype('Int8')
            df['month'] = df['parsed_time'].dt.month.astype('Int8')
            df['is_weekend'] = (df['day_of_week'].isin([5, 6])).astype('Int8')
            
            time_mask = df['parsed_time'].isna()
            if time_mask.any():
                logger.warning(f"Removed {time_mask.sum()} invalid timestamps")
                df = df[~time_mask]

            # Duration handling
            df['duration_seconds'] = df['Duration'].apply(
                lambda x: int(x.split(':')[0])*60 + int(x.split(':')[1])
                if re.match(r'^\d+:\d{2}$', x) else None
            )
            df = df.dropna(subset=['duration_seconds'])

            # Popularity features
            df['artist_popularity'] = df['Artist'].map(
            df['Artist'].value_counts()
            ).fillna(0).astype('int32')

            df['track_popularity'] = df['Track_Name'].map(
            df['Track_Name'].value_counts()
            ).fillna(0).astype('int32')

            df['album_popularity'] = df['Album'].map(
            df['Album'].value_counts()
            ).fillna(0).astype('int32')

            # Categorical encoding
            for col in ['Artist', 'Track_Name', 'Album', 'Platform']:
                if col not in self.label_encoders:
                    self.label_encoders[col] = LabelEncoder()
                    self.label_encoders[col].fit(
                        pd.Series(df[col].unique().tolist() + ['Unknown'])
                    )
                
                df[col] = df[col].fillna('Unknown').apply(
                    lambda x: x if x in self.label_encoders[col].classes_ else 'Unknown'
                )
                df[f'{col}_encoded'] = self.label_encoders[col].transform(df[col])

            if is_training:
                df['Skipped'] = df['Skipped'].map({'Yes': 1, 'No': 0})
                df = df.dropna(subset=['Skipped'])

            return df.dropna()
        
        except Exception as e:
            logger.error(f"Preprocessing failed: {str(e)}")
            raise

    def train_skip_predictor(self, df):
        processed_df = self.preprocess_data(df, is_training=True)
        self.skip_scaler.fit(processed_df[self.feature_cols['skip']])
        X = self.skip_scaler.transform(processed_df[self.feature_cols['skip']])
        y = processed_df['Skipped']
        
        self.skip_predictor = RandomForestClassifier(
            n_estimators=100, 
            max_depth=10, 
            random_state=42
        )
        self.skip_predictor.fit(X, y)
        return self

    def train_duration_predictor(self, df):
        processed_df = self.preprocess_data(df)
        
        # Session detection
        processed_df = processed_df.sort_values('parsed_time')
        processed_df['session_id'] = (
            (processed_df['parsed_time'].diff() > pd.Timedelta(minutes=30))
            .cumsum()
        )
        
        session_features = processed_df.groupby('session_id').agg({
            'hour': 'first',
            'day_of_week': 'first',
            'month': 'first',
            'is_weekend': 'first',
            'artist_popularity': 'mean',
            'track_popularity': 'mean',
            'duration_seconds': 'sum'
        }).reset_index()

        self.duration_scaler.fit(session_features[self.feature_cols['duration']])
        X = self.duration_scaler.transform(session_features[self.feature_cols['duration']])
        y = session_features['duration_seconds']
        
        self.duration_predictor = GradientBoostingRegressor(
            n_estimators=100,
            max_depth=5,
            random_state=42
        )
        self.duration_predictor.fit(X, y)
        return self

    def predict_skip_probability(self, new_data):
        try:
            processed_data = self.preprocess_data(new_data, is_training=False)
            if processed_data.empty:
                return np.array([0.5])
            
            X = self.skip_scaler.transform(processed_data[self.feature_cols['skip']])
            return self.skip_predictor.predict_proba(X)[:, 1]
        
        except Exception as e:
            logger.error(f"Skip prediction failed: {str(e)}")
            return np.array([0.5])

    def predict_session_duration(self, new_data):
        try:
            processed_data = self.preprocess_data(new_data)
            if processed_data.empty:
                return np.array([1800])
            
            X = self.duration_scaler.transform(processed_data[self.feature_cols['duration']])
            return self.duration_predictor.predict(X)
        
        except Exception as e:
            logger.error(f"Duration prediction failed: {str(e)}")
            return np.array([1800])
        

