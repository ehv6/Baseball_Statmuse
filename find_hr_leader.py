import sqlite3
import pandas as pd

# Define data file paths
filepath_batting = "/Users/tushigbattulga/Downloads/2024csvs_files/2024batting.csv"
filepath_players = "/Users/tushigbattulga/Downloads/2024csvs_files/2024allplayers.csv"

# Create SQLite database connection
conn = sqlite3.connect("baseball.db")

# Load CSV data into Pandas DataFrames
batting_df = pd.read_csv(filepath_batting)
players_df = pd.read_csv(filepath_players)

# Load data into SQL tables
batting_df.to_sql("batting", conn, if_exists="replace", index=False)
players_df.to_sql("players", conn, if_exists="replace", index=False)

# Query to find player with most HRs
query = """
SELECT 
  p.first || ' ' || p.last AS player_name,
  SUM(b.b_hr) AS total_home_runs
FROM batting b
JOIN players p ON b.id = p.id
GROUP BY b.id
ORDER BY total_home_runs DESC
LIMIT 1;
"""

# Execute and print results
result = pd.read_sql_query(query, conn)
print("\nPlayer with the most home runs:")
print(result)

# Close the database connection
conn.close()
