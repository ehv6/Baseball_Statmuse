from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
import sqlite3
import pandas as pd
import openai
import os
import re
from dotenv import load_dotenv

# Initialize environment and app
load_dotenv()
app = Flask(__name__)
CORS(app)

# Configuration
BASE_DIR = "/Users/tushigbattulga/Desktop/Personal Projects/Baseball_Statmuse/2024csvs_files"
CSV_FILES = {
    "players": "2024allplayers.csv",
    "batting": "2024batting.csv",
    "fielding": "2024fielding.csv",
    "gameinfo": "2024gameinfo.csv",
    "pitching": "2024pitching.csv",
    "teamstats": "2024teamstats.csv"
}

# Initialize database
def init_database():
    conn = sqlite3.connect("baseball.db")
    for table_name, file_name in CSV_FILES.items():
        df = pd.read_csv(os.path.join(BASE_DIR, file_name))
        df.to_sql(table_name, conn, if_exists="replace", index=False)
    conn.close()
    print("Database initialized")

# Initialize once when app starts
init_database()

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

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/query', methods=['POST'])
def handle_query():
    try:
        data = request.json
        user_input = data.get('query')
        query = generate_sql_query(user_input)
        
        with sqlite3.connect("baseball.db") as conn:
            result = pd.read_sql_query(query, conn).to_dict(orient='records')
            
        return jsonify({
            "query": query,
            "results": result[:50]  # Limit results for safety
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Verify API key
    if not os.getenv("OPENAI_API_KEY"):
        raise ValueError("Missing OpenAI API key")
        
    app.run(debug=True)