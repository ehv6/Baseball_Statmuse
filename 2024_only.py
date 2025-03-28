from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
import sqlite3
import pandas as pd
import openai
import os
import re
from dotenv import load_dotenv
import serverless_wsgi
import shutil

# Initialize environment and app
load_dotenv()
app = Flask(__name__)
CORS(app)

# Configuration
BASE_DIR = os.path.join(os.path.dirname(__file__), "2024csvs")

SOURCE_DB = "2024_baseball.db"
TARGET_DB = "/tmp/2024_baseball.db"

if os.path.exists(SOURCE_DB):
    shutil.copy(SOURCE_DB, TARGET_DB)
else:
    print(f"{SOURCE_DB} not found. Skipping copy.")

DATABASE_PATH = TARGET_DB

BASE_DIR = os.path.join(os.path.dirname(__file__), "2024csvs")

CSV_FILES = {
    "players": "2024allplayers.csv",
    "batting": "2024batting.csv",
    "fielding": "2024fielding.csv",
    "gameinfo": "2024gameinfo.csv",
    "pitching": "2024pitching.csv",
    "teamstats": "2024teamstats.csv"
}

def init_database():
    """Initialize SQLite database with CSV data if all files exist, else skip.
    Returns True if database was initialized, False otherwise."""
    # Check if all CSV files exist
    for file_name in CSV_FILES.values():
        file_path = os.path.join(BASE_DIR, file_name)
        if not os.path.exists(file_path):
            print(f"CSV file {file_path} not found. Skipping database initialization.")
            print("Using existing database as backup.")
            return False

    conn = sqlite3.connect("2024_baseball.db")
    try:
        for table_name, file_name in CSV_FILES.items():
            file_path = os.path.join(BASE_DIR, file_name)
            df = pd.read_csv(file_path)
            df.to_sql(table_name, conn, if_exists="replace", index=False)
        print("Database initialized successfully from CSV files.")
        return True
    except Exception as e:
        print(f"Error initializing database: {e}")
        return False
    finally:
        conn.close()

# Initialize database on app start
print("Loading... Initializing the database. Please wait.")
db_initialized = init_database()
if db_initialized:
    print("Database initialized successfully from CSV files. Application is ready.")
else:
    print("Using existing database. Application is ready.")

# Constants for SQL generation
SCHEMA_CONTEXT = """
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
- Player names: Use `first || ' ' || last` for full names
- Dates: Stored as YYYYMMDD strings (use string comparisons)
- Home runs: Always use `b_hr` from batting table
- Playoff games: gametype IN ('wildcard', 'divisionseries', 'lcs', 'worldseries')
- Team codes: Use 3-letter abbreviations (e.g., 'LAN' for Dodgers)
"""

ADDITIONAL_RULES = """
Critical Rules:
1. Player ID Deduplication: Use subqueries for distinct player IDs
2. Set limit to 25 on all searches
3. Explicit Aliases: Use table aliases in JOINs
4. Error Prevention: Use TRIM() and CAST() appropriately
5. Team Codes: Use official 3-letter abbreviations
6. Avoid Redundant JOINs: Use existing columns directly
"""

EXAMPLES = """
Examples:
- "Ronald Acuna's home runs":
  SELECT p.first || ' ' || p.last AS player_name, SUM(b.b_hr) AS total_hr
  FROM (SELECT DISTINCT id, first, last FROM players) p
  JOIN batting b ON p.id = b.id
  WHERE p.last = 'Acuna' AND p.first = 'Ronald'
  GROUP BY p.id

- "Dodgers players with 10+ HRs":
  SELECT p.first || ' ' || p.last AS player_name, SUM(b.b_hr) AS total_hr
  FROM (SELECT DISTINCT id, first, last FROM players WHERE team = 'LAN') p
  JOIN batting b ON p.id = b.id
  GROUP BY p.id
  HAVING SUM(b.b_hr) >= 10

- "Yankees playoff games":
  SELECT gid, date, visteam, hometeam
  FROM gameinfo
  WHERE (visteam = 'NYA' OR hometeam = 'NYA')
    AND gametype IN ('wildcard', 'divisionseries', 'lcs', 'worldseries')
    
- "Pitchers with the most strikeouts":
      ```
      SELECT 
        p.first || ' ' || p.last AS pitcher_name,
        pi.team,
        SUM(pi.p_k) AS total_strikeouts
      FROM (SELECT DISTINCT id, first, last FROM players)
      JOIN pitching pi ON p.id = pi.id
      GROUP BY p.id
      ORDER BY total_strikeouts DESC
      ```
      
- "All of Shohei Ohtani's home runs":
    SELECT 
        p.first || ' ' || p.last AS player_name,
        g.date,
        CASE 
            WHEN b.team = g.hometeam THEN 'vs ' || g.visteam
            ELSE 'at ' || g.visteam
        END AS matchup,
        b.b_hr AS home_runs
    FROM (SELECT DISTINCT id, first, last FROM players) p
    JOIN batting b ON p.id = b.id
    JOIN gameinfo g ON b.gid = g.gid
    WHERE p.last = 'Ohtani' 
    AND p.first = 'Shohei'
    AND b.b_hr > 0
    ORDER BY g.date DESC
    
- "Players with most regular season strikeouts":
      ```
      SELECT 
        p.first || ' ' || p.last AS pitcher_name,
        pi.team,
        SUM(pi.p_k) AS total_strikeouts
      FROM (SELECT DISTINCT id, first, last FROM players) p
      JOIN pitching pi ON p.id = pi.id
      JOIN gameinfo g ON pi.gid = g.gid
      WHERE g.gametype = 'regular'
      GROUP BY p.id
      ORDER BY total_strikeouts DESC
      ```
- "Mike Trout's 2024 OPS (On-base Plus Slugging)":
    ```
    SELECT 
    p.first || ' ' || p.last AS player_name,
    (SUM(b.b_h + b.b_w + b.b_hbp) * 1.0 / NULLIF(SUM(b.b_ab + b.b_w + b.b_hbp + b.b_sf), 0)) + 
    (SUM(b.b_h + (2 * b.b_d) + (3 * b.b_t) + (4 * b.b_hr)) * 1.0 / NULLIF(SUM(b.b_ab), 0)) AS ops
    FROM (SELECT DISTINCT id, first, last FROM players WHERE last = 'Trout' AND first = 'Mike') p
    JOIN batting b ON p.id = b.id
    JOIN gameinfo g ON b.gid = g.gid
    WHERE g.date BETWEEN '20240101' AND '20241231'
    AND g.gametype = 'regular'
    GROUP BY p.id
    ```
"""

def generate_sql_query(user_input):
    """Generate SQL query from natural language using OpenAI"""
    client = openai.OpenAI()
    prompt = f"""
Convert this baseball statistics request to SQLite query using:
{SCHEMA_CONTEXT}
{ADDITIONAL_RULES}
{EXAMPLES}

Request: {user_input}
SQL Query:
"""
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an expert SQL generator. Return ONLY SQL with no markdown."},
                {"role": "user", "content": prompt}
            ],
            temperature=0
        )
        query = response.choices[0].message.content.strip()
        return re.sub(r"```sql|```", "", query).strip()
    except Exception as e:
        raise RuntimeError(f"OpenAI API error: {str(e)}")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/query', methods=['POST'])
def handle_query():
    """Handle natural language query requests"""
    try:
        data = request.get_json()
        if not data or 'query' not in data:
            return jsonify({"error": "Missing query parameter"}), 400

        user_input = data['query'].strip()
        if not user_input:
            return jsonify({"error": "Empty query"}), 400

        query = generate_sql_query(user_input)

        with sqlite3.connect(DATABASE_PATH) as conn:
            result = pd.read_sql_query(query, conn).to_dict(orient='records')

        return jsonify({
            "query": query,
            "results": result[:25]  # Safety limit
        })

    except sqlite3.Error as e:
        return jsonify({"error": f"Database error: {str(e)}"}), 500
    except pd.errors.DatabaseError as e:
        return jsonify({"error": f"Query error: {str(e)}"}), 400
    except RuntimeError as e:
        return jsonify({"error": str(e)}), 500
    except Exception as e:
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500

if __name__ == '__main__':
    if not os.getenv("OPENAI_API_KEY"):
        raise ValueError("Missing OpenAI API key in environment variables")
    app.run(host='0.0.0.0', port=5001)
    
def vercel_handler(event, context):
    return serverless_wsgi.handle_request(app, event, context)