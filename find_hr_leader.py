import sqlite3
import pandas as pd

# Define datapath
filepath_batting = "/Users/tushigbattulga/Downloads/2024csvs_files/2024batting.csv"
filepath_players = "/Users/tushigbattulga/Downloads/2024csvs_files/2024allplayers.csv"

# Load CSV data into DataFrames
batting_df = pd.read_csv(filepath_batting)
players_df = pd.read_csv(filepath_players)

# Create SQLite database
conn = sqlite3.connect("baseball.db")

# Load DataFrames into SQL tables
batting_df.to_sql("batting", conn, if_exists="replace", index=False)
players_df.to_sql("players", conn, if_exists="replace", index=False)

# Close the connection
conn.close()