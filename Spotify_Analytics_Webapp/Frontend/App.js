import React from 'react';
import BasicStats from './components/BasicStats/BasicStats';
import ArtistStats from './components/ArtistStats/ArtistStats';
import ListeningActivityChart from './components/ListeningActivityChart/ListeningActivityChart';
import SkipAnalysis from './components/SkipAnalysis/SkipAnalysis';
import MLPredictions from './components/MLPredictions/MLPredictions';  // Make sure this is imported
import styles from './App.module.css';

function App() {
  return (
    <div className={styles.appContainer}>
      <h1 className={styles.title}>Spotify Analysis Hub</h1>
      <div className={styles.gridContainer}>
        {/* Basic Stats Section */}
        <div className={styles.gridItem}>
          <BasicStats />
        </div>

        {/* Artist Stats Section */}
        <div className={styles.gridItem}>
          <ArtistStats />
        </div>

        {/* Full-width Charts */}
        <div className={styles.gridItemFull}>
          <ListeningActivityChart />
        </div>

        {/* Skip Analysis Section */}
        <div className={styles.gridItemFull}>
          <SkipAnalysis />
        </div>

        {/* ML Predictions Section - Add as new grid item */}
        <div className={styles.gridItemFull}>
          <div className={styles.mlContainer}>  {/* Changed from appContainer */}
            <h2 className={styles.subTitle}>Predictions</h2>
            <MLPredictions />
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
