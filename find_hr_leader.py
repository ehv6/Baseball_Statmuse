import openai
import sqlite3
import pandas as pd
import os
from dotenv import load_dotenv

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
    client = openai.OpenAI()  # Correct way to use OpenAI v1.0+

    prompt = f"Convert the following natural language request into a SQL query for an SQLite database:\n\nRequest: {user_input}\nSQL Query:"

    response = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[
            {"role": "system", "content": "You are an expert in SQL query generation."},
            {"role": "user", "content": prompt},
        ],
        temperature=0
    )

    query = response.choices[0].message.content.strip()
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