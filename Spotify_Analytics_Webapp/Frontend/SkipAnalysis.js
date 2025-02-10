// src/components/SkipAnalysis/SkipAnalysis.js
import React, { useState, useEffect } from 'react';
import axios from 'axios';
import styles from './SkipAnalysis.module.css';

function SkipAnalysis() {
  const [skipData, setSkipData] = useState([]);

  useEffect(() => {
    axios.get('http://localhost:5000/api/intermediate/skip-analysis')
      .then(res => {
        if (res.data && res.data.data) {
          setSkipData(res.data.data);
        }
      })
      .catch(err => console.error("Error fetching skip analysis:", err));
  }, []);

  return (
    <div className={styles.skipAnalysisContainer}>
      <h2>Top 20 Most Skipped Tracks</h2>
      <table className={styles.table}>
        <thead>
          <tr>
            <th>Artist</th>
            <th>Track</th>
            <th>Total Plays</th>
            <th>Skips</th>
            <th>Skip Rate (%)</th>
          </tr>
        </thead>
        <tbody>
          {skipData.map((item, index) => (
            <tr key={index}>
              <td>{item.Artist}</td>
              <td>{item.track_name}</td>
              <td>{item.total_plays}</td>
              <td>{item.skips}</td>
              <td>{item.skip_rate}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default SkipAnalysis;