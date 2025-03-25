import sqlite3
import pandas as pd
import os

# Path to your SQLite database (same as in your Flask app)
DB_PATH = "alltime_baseball.db"

def test_query():
    query = """
    SELECT * FROM players
    WHERE last = 'Griffey' AND first IN ('Ken', 'Ken Jr', 'Ken Griffey');
    """
    
    # Connect to the database
    try:
        conn = sqlite3.connect(DB_PATH)
        # Execute the query and convert the result into a DataFrame
        result = pd.read_sql_query(query, conn)
        
        # Check if the result is empty or not and print
        if not result.empty:
            print("Query Results:")
            print(result)  # Print the full result in the terminal
        else:
            print("No results found.")
    
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        conn.close()

if __name__ == '__main__':
    test_query()
