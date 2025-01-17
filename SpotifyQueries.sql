--Basic Queries
Select * FROM SpotifyProject..StreamingHistory
-- 1. Total number of tracks played
SELECT COUNT(*) as total_plays
FROM SpotifyProject..StreamingHistory

-- 2. Number of unique songs
SELECT COUNT(DISTINCT [Track Name]) as unique_songs
FROM SpotifyProject..StreamingHistory

-- 3. Number of unique artists
SELECT COUNT(DISTINCT Artist) as unique_artists
FROM SpotifyProject..StreamingHistory

--4. Total Seconds Played
--SELECT [Track Name], Artist, COUNT(*) AS Total_Plays, 
--SUM(CAST(LEFT([Duration (MM:SS)], ':', 1) AS int)*60 + CAST(RIGHT([Duration (MM:SS)], ':', -1) AS int)) AS Total_Seconds_Played
--FROM SpotifyProject..StreamingHistory
--GROUP BY [Track Name], Artist
--ORDER BY Total_Seconds_Played DESC
--ABOVE CODE DOES NOT WORK DUE TO ISSUES WITH THE SUBSTRING CLAUSE AND ITS USECASE IN SSMS, SO USE THE ONE BELOW IF USING THE SERVER ELSE THE ABOVE WITH THE 
-- "SUBSTRING_INDEX" WILL WORK
SELECT top 10
    [Track Name], Artist, COUNT(*) AS play_count,
    SUM(
        CAST(SUBSTRING([Duration (MM:SS)], 1, CHARINDEX(':', [Duration (MM:SS)]) - 1) AS INT) * 60 +
        CAST(SUBSTRING([Duration (MM:SS)], CHARINDEX(':', [Duration (MM:SS)]) + 1, LEN([Duration (MM:SS)])) AS INT)
    ) AS total_seconds_played
FROM SpotifyProject..StreamingHistory
WHERE [Track Name] is not null and Artist is not null
GROUP BY [Track Name], Artist
ORDER BY total_seconds_played DESC;


-- 5. Most played artists with total listening time
SELECT Artist, COUNT(*) AS Total_Plays, 
SUM(
CAST(SUBSTRING([Duration (MM:SS)], 1, CHARINDEX(':', [Duration (MM:SS)]) - 1) as int) * 60 +
CAST(SUBSTRING([Duration (MM:SS)], CHARINDEX(':', [Duration (MM:SS)]) + 1, LEN([Duration (MM:SS)])) as int)
)/3600.00 as Total_Hours_Played
FROM SpotifyProject..StreamingHistory
WHERE Artist is not null
GROUP BY Artist
ORDER BY Total_Hours_Played desc

-----------------------------------------------------------------------------------------------------------------------------
--INTERMEDIATE 
-- 1. Listening patterns by hour of day
WITH listening_patterns AS (
    SELECT 
        DATEPART(HOUR, Timestamp) as hour_of_day,
        CASE 
            WHEN DATEPART(HOUR, Timestamp) BETWEEN 5 AND 11 THEN 'Morning'
            WHEN DATEPART(HOUR, Timestamp) BETWEEN 12 AND 16 THEN 'Afternoon'
            WHEN DATEPART(HOUR, Timestamp) BETWEEN 17 AND 20 THEN 'Evening'
            ELSE 'Night'
        END as time_of_day,
        COUNT(*) as play_count,
        COUNT(DISTINCT [Track Name]) as unique_tracks,
        COUNT(DISTINCT Artist) as unique_artists,
        SUM(
			CAST(SUBSTRING([Duration (MM:SS)], 1, CHARINDEX(':', [Duration (MM:SS)]) - 1) as int) * 60 +
			CAST(SUBSTRING([Duration (MM:SS)], CHARINDEX(':', [Duration (MM:SS)]) + 1, LEN([Duration (MM:SS)])) as int)
		)/3600.00 as Total_Hours_Played,
        ROUND(CAST(COUNT(DISTINCT [Track Name]) AS float) / COUNT(*) * 100, 2) as track_variety_percentage
    FROM SpotifyProject..StreamingHistory
	WHERE [Duration (MM:SS)] is not null
    GROUP BY 
        DATEPART(HOUR, Timestamp),
        CASE 
            WHEN DATEPART(HOUR, Timestamp) BETWEEN 5 AND 11 THEN 'Morning'
            WHEN DATEPART(HOUR, Timestamp) BETWEEN 12 AND 16 THEN 'Afternoon'
            WHEN DATEPART(HOUR, Timestamp) BETWEEN 17 AND 20 THEN 'Evening'
            ELSE 'Night'
        END
)
SELECT 
    FORMAT(hour_of_day, '00') + ':00' as hour_of_day,
    time_of_day,
    play_count,
    unique_tracks,
    unique_artists,
    Total_Hours_Played,
    track_variety_percentage as variety_score
FROM listening_patterns
ORDER BY hour_of_day;

WITH Listening_analysis AS (
Select DATEPART(hour, Timestamp) as hour_of_the_day
	case when Datepart(hour, timestamp) = 
from SpotifyProject..StreamingHistory
-- 4. Skip analysis
SELECT 
[Track Name], Artist, COUNT(*) AS Total_Plays, SUM(CASE WHEN Skipped = 'Yes' THEN 1 ELSE 0 END) AS Skips,
ROUND(CAST(SUM(CASE WHEN Skipped = 'Yes' THEN 1 ELSE 0 END) AS FLOAT) / COUNT(*) * 100, 4) AS Skip_Percentage
FROM SpotifyProject..StreamingHistory
GROUP BY [Track Name], Artist
HAVING COUNT(*)>=5
ORDER BY Skip_Percentage DESC


-----------------------------------------------------------------------------------------------------------------------------
--Queries for Visualisation
--1. Query to show the average completion rate and its average time played
SELECT 
    [Track Name],
    Artist,
    COUNT(*) AS total_plays,
    SUM(CASE WHEN Skipped = 'No' THEN 1 ELSE 0 END) AS completed_plays,
    ROUND(
        (CAST(SUM(CASE WHEN Skipped = 'No' THEN 1 ELSE 0 END) AS FLOAT) / COUNT(*)) * 100, 
        2
    ) AS completion_rate,
    AVG(
        CAST(LEFT([Duration (MM:SS)], CHARINDEX(':', [Duration (MM:SS)]) - 1) AS INTEGER) * 60 +
        CAST(SUBSTRING([Duration (MM:SS)], CHARINDEX(':', [Duration (MM:SS)]) + 1, LEN([Duration (MM:SS)])) AS INTEGER)
    ) AS avg_duration_seconds
FROM SpotifyProject..StreamingHistory
GROUP BY [Track Name], Artist
HAVING COUNT(*) >= 10
ORDER BY completion_rate DESC



