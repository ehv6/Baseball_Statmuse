import openai
import sqlite3
import pandas as pd
import os

# Define base directory where CSV files are stored
base_dir = "/Users/tushigbattulga/Desktop/Personal Projects/Baseball_Statmuse/2024csvs_files"

# List of CSV files to load (mapping table names to file names)
csv_files = {
    "players": "2024allplayers.csv",
    "batting": "2024batting.csv",
    "fielding": "2024fielding.csv",
    "gameinfo": "2024gameinfo.csv",
    "pitching": "2024pitching.csv",
    "teamstats": "2024teamstats.csv"
}

# Set OpenAI API Key
OPENAI_API_KEY = "your-api-key-here"

# Define function to generate SQL query from natural language
def generate_sql_query(user_input):
    prompt = f"Convert the following natural language request into a SQL query for an SQLite database:\n\nRequest: {user_input}\nSQL Query:"
    
    response = openai.ChatCompletion.create(
        model="gpt-4-turbo",  # Most accurate for queries
        messages=[{"role": "system", "content": "You are an expert in SQL query generation."},
                  {"role": "user", "content": prompt}],
        temperature=0  # Stable results
    )

    query = response["choices"][0]["message"]["content"].strip()
    return query

# Create SQLite database connection
conn = sqlite3.connect("baseball.db")

# Load each CSV file into a Pandas DataFrame and store it in SQL
tables_loaded = []
for table_name, file_name in csv_files.items():
    file_path = os.path.join(base_dir, file_name)
    df = pd.read_csv(file_path)
    df.to_sql(table_name, conn, if_exists="replace", index=False)
    tables_loaded.append(table_name)
    print(f"Loaded {table_name} from {file_name}")

print("\nAll tables successfully loaded into the database.")

# Query to find player with most HRs
query = """
SELECT 
  p.first || ' ' || p.last AS player_name,
  SUM(b.b_hr) AS total_home_runs
FROM batting b
JOIN (SELECT DISTINCT id, first, last FROM players) p ON b.id = p.id
WHERE b.gametype = 'regular'
GROUP BY b.id
ORDER BY total_home_runs DESC
LIMIT 5;
"""

# Execute and print results
result = pd.read_sql_query(query, conn)
print("\nPlayer with the most home runs:")
print(result)

# Close the database connection
conn.close()
