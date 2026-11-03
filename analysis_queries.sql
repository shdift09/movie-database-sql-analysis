-- CDS 302 | Movie Database SQL Analysis
-- Database: SQLite. All queries are read-only.
-- Run statements individually in a SQLite client (e.g., DB Browser for SQLite).

-- 1. String operations: titles containing "Star" or "War"
SELECT Name AS Movie_Title, Year, Rating, Gross
FROM Movies
WHERE Name LIKE '%Star%' OR Name LIKE '%War%'
ORDER BY Gross DESC;

-- 2. Set operations: movies released from 2020 onward OR in Action genre
SELECT m.Movie_ID, m.Name AS Movie_Title
FROM Movies AS m
WHERE m.Year >= 2020
UNION
SELECT m.Movie_ID, m.Name AS Movie_Title
FROM Movies AS m
JOIN Movie_Genres AS mg ON m.Movie_ID = mg.Movie_ID
JOIN Genres AS g ON mg.Genre_ID = g.Genre_ID
WHERE g.Genre_Name = 'Action'
ORDER BY Movie_Title;

-- 3. Aggregate functions: average movie score and number of scored movies
SELECT COUNT(Score) AS Rated_Movies, ROUND(AVG(Score), 2) AS Average_Score
FROM Movies;

-- 4. GROUP BY / ORDER BY: movie count and average rating by genre
SELECT g.Genre_Name AS Genre,
       COUNT(DISTINCT m.Movie_ID) AS Movie_Count,
       ROUND(AVG(m.Score), 2) AS Average_Score
FROM Genres AS g
JOIN Movie_Genres AS mg ON g.Genre_ID = mg.Genre_ID
JOIN Movies AS m ON m.Movie_ID = mg.Movie_ID
GROUP BY g.Genre_ID, g.Genre_Name
ORDER BY Movie_Count DESC, Genre;

-- 5. HAVING: directors with multiple movies and average score >= 7.0
SELECT d.Name AS Director,
       COUNT(m.Movie_ID) AS Movie_Count,
       ROUND(AVG(m.Score), 2) AS Average_Score,
       ROUND(SUM(m.Gross), 2) AS Total_Gross
FROM Directors AS d
JOIN Movies AS m ON m.Director_ID = d.Director_ID
GROUP BY d.Director_ID, d.Name
HAVING COUNT(m.Movie_ID) > 1 AND AVG(m.Score) >= 7.0
ORDER BY Total_Gross DESC;

-- 6. JOIN: director and production company collaborations
SELECT d.Name AS Director,
       c.Company_Name AS Company,
       COUNT(m.Movie_ID) AS Collaboration_Count,
       ROUND(SUM(m.Gross), 2) AS Total_Gross
FROM Movies AS m
JOIN Directors AS d ON m.Director_ID = d.Director_ID
JOIN Companies AS c ON m.Company_ID = c.Company_ID
GROUP BY d.Director_ID, d.Name, c.Company_ID, c.Company_Name
ORDER BY Collaboration_Count DESC, Total_Gross DESC;

-- 7. JOIN: Leonardo DiCaprio's films grouped by director
-- The source CSV has one named star per movie; this query reflects that scope.
SELECT d.Name AS Director,
       COUNT(m.Movie_ID) AS Collaboration_Count,
       ROUND(SUM(m.Gross), 2) AS Total_Gross
FROM Movies AS m
JOIN Directors AS d ON m.Director_ID = d.Director_ID
JOIN Movie_Actors AS ma ON m.Movie_ID = ma.Movie_ID
JOIN Actors AS a ON ma.Actor_ID = a.Actor_ID
WHERE a.Name = 'Leonardo DiCaprio'
GROUP BY d.Director_ID, d.Name
ORDER BY Total_Gross DESC, Collaboration_Count DESC;

-- 8. WITH + window function: top 3 movies by gross revenue per release year
-- RANK() can return more than three rows for a year if there are ties.
WITH RankedMovies AS (
    SELECT Name, Year, Gross,
           RANK() OVER (PARTITION BY Year ORDER BY Gross DESC) AS Revenue_Rank
    FROM Movies
    WHERE Year IS NOT NULL AND Gross IS NOT NULL
)
SELECT Name, Year, Gross, Revenue_Rank
FROM RankedMovies
WHERE Revenue_Rank <= 3
ORDER BY Year DESC, Revenue_Rank ASC, Name;

-- 9. Business question: relationship between movie budget and gross revenue
-- This is descriptive, not a causal analysis.
SELECT Name, Year, Budget, Gross,
       ROUND(Gross - Budget, 2) AS Gross_Minus_Budget,
       Score
FROM Movies
WHERE Budget > 0 AND Gross IS NOT NULL
ORDER BY Gross_Minus_Budget DESC
LIMIT 20;
