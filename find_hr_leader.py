import openai
import sqlite3
import pandas as pd
import os
from dotenv import load_dotenv
import re

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

# API key
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Define function to generate SQL query from natural language
def generate_sql_query(user_input):
    client = openai.OpenAI()

    schema_context = """
    Database Schema:
    - players (id, last, first, bat, throw, team, ...)
    - batting (gid, id, team, b_pa, b_ab, b_hr, gametype, ...)
    - gameinfo (gid, visteam, hometeam, date, ...)
    - pitching (gid, id, team, p_ipouts, p_er, ...)
    - fielding (gid, id, team, d_pos, d_po, ...)
    - teamstats (gid, team, inn1, ...)

    Relationships:
    - players.id = batting.id = pitching.id = fielding.id
    - gameinfo.gid = batting.gid = pitching.gid = fielding.gid = teamstats.gid

    Notes:
    - Player names are split into 'first' and 'last' in the 'players' table.
    - Use 'b_hr' for home runs in 'batting'.
    - Dates are stored as strings (e.g., 20240320).
    """

    additional_rules = """
    Additional Rules:
    1. **Ensure Unique Player IDs Before Joins (MOST IMPORTANT RULE):**
       The 'allplayers.csv' file (loaded into the 'players' table) may contain multiple entries for the same player.
       Before performing any JOIN operations, ensure player IDs are unique by using a subquery or DISTINCT.
       For example, use: JOIN (SELECT DISTINCT id, first, last FROM players) p ON b.id = p.id,
       or aggregate batting data before joining.
    2. The generated SQL query must always return at least 5 results.
       If the natural query returns fewer than 5 rows, adjust the query (e.g., using a LIMIT clause or other techniques)
       to ensure a minimum of 5 rows.
    """

    prompt = f"""
    Convert the natural language request into an SQLite query using ONLY the following schema:
    {schema_context}
    {additional_rules}

    Rules:
    1. Use valid table/column names (e.g., 'players.first', not 'player_name').
    2. Use explicit JOINs for multi-table queries (e.g., 'batting JOIN players ON batting.id = players.id').
    3. Never assume columns like 'player_name'; concatenate 'first' and 'last' if needed.
    4. Use 'b_hr' for home runs, not 'hr' or 'home_runs'.

    Request: {user_input}
    SQL Query:
    """

    response = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[
            {"role": "system", "content": "You are an expert SQL generator. Return ONLY the SQL query with no explanations or markdown."},
            {"role": "user", "content": prompt}
        ],
        temperature=0
    )

    query = response.choices[0].message.content.strip()
    query = re.sub(r"```sql|```", "", query).strip()
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

# Verify API key is loaded (for debugging)
if not OPENAI_API_KEY:
    raise ValueError("OpenAI API key not found. Make sure you have a valid .env file.")

# Connect to SQLite database
conn = sqlite3.connect("baseball.db")

# Ask user for input
user_input = input("Enter your baseball stats query in natural language: ")

# Generate SQL query
query = generate_sql_query(user_input)
print("\nGenerated SQL Query:\n", query)

# Execute the generated query
try:
    result = pd.read_sql_query(query, conn)
    print("\nQuery Result:")
    print(result)
except Exception as e:
    print("\nError executing query:", e)

# Close the database connection
conn.close()
