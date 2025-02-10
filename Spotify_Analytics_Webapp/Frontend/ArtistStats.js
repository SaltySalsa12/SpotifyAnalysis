import React, { useState, useEffect } from 'react';
import axios from 'axios';


function ArtistStats() {
  const [artistStats, setArtistStats] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    axios.get('http://localhost:5000/api/basic/artist-playtime')
      .then(response => {
        setArtistStats(response.data);
        setLoading(false);
      })
      .catch(err => {
        console.error("Error fetching artist statistics:", err);
        setError("Failed to load artist statistics");
        setLoading(false);
      });
  }, []);

  if (loading) return <div>Loading artist statistics...</div>;
  if (error) return <div>Error: {error}</div>;

  return (
    <div className="artist-stats">
      <h2>Artist Statistics</h2>
      <table className="stats-table">
        <thead>
          <tr>
            <th>Artist</th>
            <th>Total Plays</th>
            <th>Hours Played</th>
          </tr>
        </thead>
        <tbody>
          {artistStats.map((stat, index) => (
            <tr key={index}>
              <td>{stat.Artist}</td>
              <td>{stat.Total_Plays}</td>
              <td>{stat.Total_Hours_Played.toFixed(2)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default ArtistStats;