// src/components/ListeningActivityChart/ListeningActivityChart.js
import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Chart } from 'react-chartjs-2';
import { 
  Chart as ChartJS, 
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend
} from 'chart.js';
import styles from './ListeningActivityChart.module.css';

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend
);

function ListeningActivityChart() {
  const [chartData, setChartData] = useState({
    labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
    datasets: []
  });

  useEffect(() => {
    axios.get('http://localhost:5000/api/visualization/activity-stackedbarchart')
      .then(res => {
        if (res.data && Array.isArray(res.data)) {
          // Group data by day and hour
          const days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
          const hours = Array.from({ length: 24 }, (_, i) => i); // 0-23 hours

          const datasets = hours.map(hour => ({
            label: `${hour}:00`,
            data: days.map((_, dayIndex) => {
              const entry = res.data.find(item => 
                item.day_of_week === dayIndex && parseInt(item.hour) === hour
              );
              return entry ? entry.plays : 0;
            }),
            backgroundColor: `hsl(${(hour / 24) * 360}, 70%, 50%)`, // Color by hour
          }));

          setChartData({
            labels: days,
            datasets: datasets
          });
        }
      })
      .catch(err => console.error("Error fetching data:", err));
  }, []);

  return (
    <div className={styles.chartContainer}>
      <h2 className={styles.title}>Listening Activity by Day and Hour</h2>
      <div className={styles.chartWrapper}>
        <Chart
          type='bar'
          data={chartData}
          options={{
            responsive: true,
            maintainAspectRatio: false,
            scales: {
              x: {
                stacked: true,
                title: { 
                  display: true, 
                  text: 'Day of Week',
                  color: '#00ff88', // Green text
                  font: { size: 14 }
                },
                grid: { 
                  color: 'rgba(0, 255, 136, 0.1)' // Light green grid lines
                },
                ticks: {
                  color: '#00ff88' // Green ticks
                }
              },
              y: {
                stacked: true,
                title: { 
                  display: true, 
                  text: 'Number of Plays',
                  color: '#00ff88', // Green text
                  font: { size: 14 }
                },
                grid: { 
                  color: 'rgba(0, 255, 136, 0.1)' // Light green grid lines
                },
                ticks: {
                  color: '#00ff88' // Green ticks
                }
              }
            },
            plugins: {
              legend: {
                display: true,
                position: 'bottom',
                labels: {
                  color: '#00ff88', // Green legend text
                  boxWidth: 20,
                  padding: 10
                }
              },
              tooltip: {
                callbacks: {
                  label: (context) => {
                    const label = context.dataset.label || '';
                    const value = context.raw || 0;
                    return `${label}: ${value} plays`;
                  }
                },
                backgroundColor: '#1a1a1a', // Dark background
                titleColor: '#00ff88', // Green title
                bodyColor: '#00ff88', // Green body text
                borderColor: '#00ff88', // Green border
                borderWidth: 1
              }
            }
          }}
        />
      </div>
    </div>
  );
}

export default ListeningActivityChart;