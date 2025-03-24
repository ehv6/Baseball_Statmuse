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
    - Player names: Use `first || ' ' || last` for full names (e.g., "SELECT first || ' ' || last AS player_name").
    - Dates: Stored as YYYYMMDD strings. Use string comparisons like `date BETWEEN '20240301' AND '20240331'` for March 2024.
    - Home runs: Always use `b_hr` from the `batting` table.
    - Playoff games: Defined as gametype IN ('wildcard', 'divisionseries', 'lcs', 'worldseries').
    """

    additional_rules = """
    Critical Rules:
    1. **Player ID Deduplication**:
       - Use subqueries to ensure unique player IDs before JOINs. Example:
         ```
         SELECT * FROM batting
         JOIN (SELECT DISTINCT id, first, last FROM players) AS p
         ON batting.id = p.id
         ```
    2. **Minimum 5 Results**:
       - If the natural query might return <5 rows, add `LIMIT 5` or relax filters.
       - For aggregates (e.g., "top 5"), always include `LIMIT 5`.
    3. **Explicit Aliases**:
       - Always alias tables in JOINs (e.g., `batting b JOIN players p`).
    4. **Error Prevention**:
       - Use `TRIM()` on text comparisons to avoid whitespace issues.
       - Use `CAST(date AS TEXT)` when filtering dates.
    """

    prompt = f"""
    Convert this request into a SQLite query using ONLY the provided schema.
    {schema_context}
    {additional_rules}

    Requirements:
    1. Use valid table/column names exactly as defined.
    2. Return raw columns (no markdown/formatting).
    3. For player names, concatenate `first` and `last`.
    4. Handle playoff games with `gametype IN (...)`.

    Examples:
    - "Ronald Acuna's home runs":
      ```
      SELECT p.first || ' ' || p.last AS player_name, SUM(b.b_hr) AS total_hr
      FROM (SELECT DISTINCT id, first, last FROM players) p
      JOIN batting b ON p.id = b.id
      WHERE p.last = 'Acuna' AND p.first = 'Ronald'
      GROUP BY p.id
      LIMIT 5
      ```

    - "Games in March 2024":
      ```
      SELECT * FROM gameinfo
      WHERE date BETWEEN '20240301' AND '20240331'
      LIMIT 5
      ```

    Request: {user_input}
    SQL Query:
    """

    response = client.chat.completions.create(
        model="gpt-4",
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