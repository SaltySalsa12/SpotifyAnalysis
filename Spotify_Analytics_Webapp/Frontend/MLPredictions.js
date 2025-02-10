import React, { useState } from 'react';
import axios from 'axios';
import styles from './MLPredictions.module.css';

function MLPredictions() {
  const [trackData, setTrackData] = useState({
    Timestamp: '',
    Artist: '',
    Track_Name: '',
    Album: '',
    Platform: 'Spotify',
    Duration: '',
  });
  const [skipProbability, setSkipProbability] = useState(null);
  const [sessionDuration, setSessionDuration] = useState(null);
  const [error, setError] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setTrackData(prev => ({ ...prev, [name]: value }));
  };

  const validateDuration = (duration) => {
    return /^\d+:\d{2}$/.test(duration);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setIsLoading(true);

    try {
      // Validate duration format
      if (!validateDuration(trackData.Duration)) {
        throw new Error('Duration must be in MM:SS format (e.g., 3:30)');
      }

      // Format timestamp to ISO string
      const formattedData = {
        ...trackData,
        Timestamp: new Date(trackData.Timestamp).toISOString()
      };

      // Send both requests in parallel
      const [skipResponse, durationResponse] = await Promise.all([
        axios.post('http://localhost:5000/api/ml/predict-skip', formattedData),
        axios.post('http://localhost:5000/api/ml/predict-session-duration', formattedData)
      ]);

      setSkipProbability(skipResponse.data.probability);
      setSessionDuration(durationResponse.data.duration_minutes);

    } catch (err) {
      const errorMessage = err.response?.data?.error || err.message;
      setError(errorMessage || 'Failed to fetch predictions. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className={styles.container}>
      <h2>ML Predictions</h2>
      <form onSubmit={handleSubmit} className={styles.form}>
        <div className={styles.formGroup}>
          <label>Timestamp</label>
          <input
            type="datetime-local"
            name="Timestamp"
            value={trackData.Timestamp}
            onChange={handleChange}
            required
          />
        </div>

        <div className={styles.formGroup}>
          <label>Artist</label>
          <input
            type="text"
            name="Artist"
            value={trackData.Artist}
            onChange={handleChange}
            required
          />
        </div>

        <div className={styles.formGroup}>
          <label>Track Name</label>
          <input
            type="text"
            name="Track_Name"
            value={trackData.Track_Name}
            onChange={handleChange}
            required
          />
        </div>

        <div className={styles.formGroup}>
            <label>Album</label>
            <input
                type="text"
                name="Album"
            value={trackData.Album}
            onChange={handleChange}
            required
            />
        </div>

        <div className={styles.formGroup}>
          <label>Duration (MM:SS)</label>
          <input
            type="text"
            name="Duration"
            value={trackData.Duration}
            onChange={handleChange}
            placeholder="e.g., 3:30"
            required
          />
        </div>

        <button 
          type="submit" 
          className={styles.submitButton}
          disabled={isLoading}
        >
          {isLoading ? 'Predicting...' : 'Predict'}
        </button>
      </form>

      {isLoading && (
        <div className={styles.loading}>
          <div className={styles.spinner}></div>
          <p>Analyzing track data...</p>
        </div>
      )}

      {skipProbability !== null && (
        <div className={styles.result}>
          <h3>Skip Probability: {(skipProbability * 100).toFixed(2)}%</h3>
          <p className={styles.interpretation}>
            {skipProbability > 0.7 ? 'High skip likelihood' : 
             skipProbability > 0.4 ? 'Moderate skip chance' : 'Low skip probability'}
          </p>
        </div>
      )}

      {sessionDuration !== null && (
        <div className={styles.result}>
          <h3>Predicted Session Duration: {sessionDuration.toFixed(2)} minutes</h3>
        </div>
      )}

      {error && (
        <div className={styles.error}>
          <strong>Error:</strong> {error}
          {error.includes('server') && (
            <p>Please check your connection and try again later</p>
          )}
        </div>
      )}
    </div>
  );
}

export default MLPredictions;