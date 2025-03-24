import sqlite3
import pandas as pd

# Load CSV data into DataFrames
batting_df = pd.read_csv("2024batting.csv")
players_df = pd.read_csv("2024allplayers.csv")

# Create SQLite database
conn = sqlite3.connect("baseball.db")

# Load DataFrames into SQL tables
batting_df.to_sql("batting", conn, if_exists="replace", index=False)
players_df.to_sql("players", conn, if_exists="replace", index=False)

# Close the connection
conn.close()