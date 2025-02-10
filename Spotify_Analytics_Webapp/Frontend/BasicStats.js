// frontend/src/components/BasicStats.js
import React, { useState, useEffect } from 'react';
import axios from 'axios';

function BasicStats() {
  const [totalPlays, setTotalPlays] = useState(0);
  const [mostPlayed, setMostPlayed] = useState([]);

  useEffect(() => {
    // Fetch total plays
    axios.get('http://localhost:5000/api/basic/total-plays')
      .then(res => setTotalPlays(res.data[0].total_plays))
      .catch(err => console.error("Error fetching total plays:", err));
  
    // Fetch most played tracks
    axios.get('http://localhost:5000/api/basic/most-played-tracks')
      .then(res => setMostPlayed(res.data))
      .catch(err => console.error("Error fetching most played tracks:", err));
  }, []);

  return (
    <div>
      <h2>Basic Stats</h2>
      <p>Total Plays: {totalPlays}</p>
      <h3>Most Played Tracks</h3>
      <ul>
        {mostPlayed.map((track, index) => (
          <li key={index}>{track['Track Name']} - {track.Artist} ({track.play_count} plays)</li>
        ))}
      </ul>
    </div>
  );
}

export default BasicStats;