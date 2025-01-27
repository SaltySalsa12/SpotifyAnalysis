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

--[OR]
Select DATEPART(HOUR, Timestamp) as Hour_of_The_Day,  
Case 
When DATEPART(hour, Timestamp) between 5 and 11 then 'Morning'
When DATEPART(HOUR, Timestamp) between 12 and 16 then 'Afternoon'
When DATEPART(HOUR, Timestamp) between 17 and 20 then 'Evening'
Else 'Night'
End as Time_of_The_Day,
COUNT(*) as Total_Play_Count,
COUNT(Distinct [Track Name]) as Unique_Tracks,
CAST(Count(distinct [Track Name])*1.0 / COUNT(*) * 100 as float) as Unique_Track_Percentage,
COUNT(Distinct Artist) as Unique_Artist
From SpotifyProject..StreamingHistory
Group by DATEPART(HOUR, Timestamp), 
Case
            WHEN DATEPART(HOUR, Timestamp) BETWEEN 5 AND 11 THEN 'Morning'
            WHEN DATEPART(HOUR, Timestamp) BETWEEN 12 AND 16 THEN 'Afternoon'
            WHEN DATEPART(HOUR, Timestamp) BETWEEN 17 AND 20 THEN 'Evening'
            ELSE 'Night'
        END 
order by Hour_of_The_Day

--2. Day Of Week Analysis

Select DATENAME(WEEKDAY, Timestamp) as Day_Of_Week, Count(*) as Play_Count, Count(Distinct [Track Name]) as Unique_Tracks, 
AVG(
CAST(SUBSTRING([Duration (MM:SS)], 1, CHARINDEX(':',[Duration (MM:SS)]) - 1)as int)*60 + CAST(Substring([Duration (MM:SS)], CHARINDEX(':', [Duration (MM:SS)]) + 1, LEN([Duration (MM:SS)]))as int)/60
) as Average_Minutes_per_Week,
COUNT(Distinct [Track Name])*1.0/COUNT(*)*100 as Track_Variety_Percentage,
SUM(
CAST(SUBSTRING([Duration (MM:SS)], 1, CHARINDEX(':',[Duration (MM:SS)]) - 1)as int)*60 + CAST(Substring([Duration (MM:SS)], CHARINDEX(':', [Duration (MM:SS)]) + 1, LEN([Duration (MM:SS)]))as int)
)/3600 as Total_Hours
From SpotifyProject..StreamingHistory
Where [Duration (MM:SS)] is not null
Group by DATENAme(WEEKDAY, Timestamp)
Order by 
	CASE DATENAME(WEEKDAY, Timestamp)
	When 'Sunday' then 1
	When 'Monday' then 2
	When 'Tuesday' then 3
	When 'Wednesday' then 4
	When 'Thursday' then 5
	When 'Friday' then 6
	When 'Saturday' then 7
END

--3. Monthly Listening Trends

--SELECT 
--    FORMAT(Timestamp, 'yyyy-MM') as month,
--    COUNT(*) as total_plays,
--    COUNT(DISTINCT [Track Name]) as unique_tracks,
--    COUNT(DISTINCT Artist) as unique_artists,
--    ROUND(SUM(
--        CAST(SUBSTRING([Duration (MM:SS)], 1, CHARINDEX(':', [Duration (MM:SS)]) - 1) as float) * 60 + 
--        CAST(SUBSTRING([Duration (MM:SS)], CHARINDEX(':', [Duration (MM:SS)]) + 1, LEN([Duration (MM:SS)])) as float)
--    ) / 60, 2) as total_minutes
--FROM SpotifyProject..StreamingHistory
--GROUP BY FORMAT(Timestamp, 'yyyy-MM')
--ORDER BY month;
-----------------------------------------------------------------------------------------------------------------------------
WITH MonthlyData AS (
    SELECT 
        FORMAT(Timestamp, 'yyyy-MM') AS month,
        COUNT(*) AS total_plays,
        ROUND(SUM(
            -- Convert MM:SS duration to total minutes
            CAST(LEFT([Duration (MM:SS)], CHARINDEX(':', [Duration (MM:SS)]) - 1) AS FLOAT) * 60 +
            CAST(RIGHT([Duration (MM:SS)], LEN([Duration (MM:SS)]) - CHARINDEX(':', [Duration (MM:SS)])) AS FLOAT)
        ) / 60, 2) AS total_minutes
    FROM SpotifyProject..StreamingHistory
    GROUP BY FORMAT(Timestamp, 'yyyy-MM')
)
SELECT 
    md.month,
    md.total_plays,
    md.total_minutes,
    -- Get top 5 artists for the month
    (
        SELECT STRING_AGG(Artist, ', ') 
        FROM (
            SELECT TOP 5 Artist 
            FROM SpotifyProject..StreamingHistory 
            WHERE FORMAT(Timestamp, 'yyyy-MM') = md.month 
            GROUP BY Artist 
            ORDER BY COUNT(*) DESC
        ) AS a
    ) AS top_5_artists,
    -- Get top 5 songs for the month
    (
        SELECT STRING_AGG([Track Name], ', ') 
        FROM (
            SELECT TOP 5 [Track Name] 
            FROM SpotifyProject..StreamingHistory 
            WHERE FORMAT(Timestamp, 'yyyy-MM') = md.month 
            GROUP BY [Track Name] 
            ORDER BY COUNT(*) DESC
        ) AS s
    ) AS top_5_songs
FROM MonthlyData md
ORDER BY md.month;

-- 4. Skip analysis
SELECT 
[Track Name], Artist, COUNT(*) AS Total_Plays, SUM(CASE WHEN Skipped = 'Yes' THEN 1 ELSE 0 END) AS Skips,
ROUND(CAST(SUM(CASE WHEN Skipped = 'Yes' THEN 1 ELSE 0 END) AS FLOAT) / COUNT(*) * 100, 4) AS Skip_Percentage
FROM SpotifyProject..StreamingHistory
GROUP BY [Track Name], Artist
HAVING COUNT(*)>=5
ORDER BY Skip_Percentage DESC

-----------------------------------------------------------------------------------------------------------------------------
--Advanced Queries
--1. Listening Sessions Analysis
WITH session_breaks AS (
   SELECT 
       *,
       CASE 
           WHEN DATEDIFF(MINUTE, 
               LAG(Timestamp) OVER (ORDER BY Timestamp),
               Timestamp) > 30 
           THEN 1 
           ELSE 0 
       END as new_session
   FROM SpotifyProject..StreamingHistory
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
   ROUND(SUM(
       CAST(SUBSTRING([Duration (MM:SS)], 1, CHARINDEX(':', [Duration (MM:SS)]) - 1) as float) * 60 + 
       CAST(SUBSTRING([Duration (MM:SS)], CHARINDEX(':', [Duration (MM:SS)]) + 1, LEN([Duration (MM:SS)])) as float)
   ) / 60.0, 2) as session_duration_minutes
FROM sessions
GROUP BY session_id
ORDER BY session_start;


-----------------------------------------------------------------------------------------------------------------------------
--2. Artist Discovery Timeline(When was the first time you played a certain artist and who)

WITH first_listen AS (
    SELECT 
        Artist,
        MIN(Timestamp) as first_listen_date,
        COUNT(*) as total_plays
    FROM SpotifyProject..StreamingHistory
    GROUP BY Artist
),
ordinal_suffix AS (
    SELECT 
        first_listen_date,
        total_plays, -- Include total_plays here
        DATENAME(WEEKDAY, first_listen_date) AS day_of_week,
        DAY(first_listen_date) AS day,
        DATENAME(MONTH, first_listen_date) AS month,
        YEAR(first_listen_date) AS year,
        CASE 
            WHEN DAY(first_listen_date) % 10 = 1 AND DAY(first_listen_date) != 11 THEN 'st'
            WHEN DAY(first_listen_date) % 10 = 2 AND DAY(first_listen_date) != 12 THEN 'nd'
            WHEN DAY(first_listen_date) % 10 = 3 AND DAY(first_listen_date) != 13 THEN 'rd'
            ELSE 'th'
        END AS suffix
    FROM first_listen
)
SELECT 
    day_of_week + ', ' + 
    CAST(day AS VARCHAR) + suffix + ' ' + 
    month + ' ' + 
    CAST(year AS VARCHAR) AS discovery_date,
    COUNT(*) as new_artists_discovered,
    AVG(total_plays * 1.0) as avg_plays_per_artist
FROM ordinal_suffix
GROUP BY 
    day_of_week + ', ' + 
    CAST(day AS VARCHAR) + suffix + ' ' + 
    month + ' ' + 
    CAST(year AS VARCHAR)
ORDER BY MIN(first_listen_date);


