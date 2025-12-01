import sqlite3
from typing import Optional
from textblob import TextBlob
import openai

class PromptRefinementAgent:
    def __init__(self, db_path: str = "refinement_agent.db"):
        self.db_path = db_path
        self._initialize_database()

    def _initialize_database(self):
        """Initialize the database schema if it doesn't exist."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS query_refinements (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_query TEXT NOT NULL,
                    refined_query TEXT,
                    feedback TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.commit()

    def store_query(self, user_query: str, refined_query: Optional[str] = None):
        """Store a user query and its refined version."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO query_refinements (user_query, refined_query) VALUES (?, ?)",
                (user_query, refined_query),
            )
            conn.commit()

    def update_feedback(self, query_id: int, feedback: str):
        """Update feedback for a specific query refinement."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE query_refinements SET feedback = ? WHERE id = ?",
                (feedback, query_id),
            )
            conn.commit()

    def fetch_refinements(self):
        """Fetch all query refinements."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM query_refinements")
            return cursor.fetchall()

    def refine_query(self, user_query: str) -> str:
        """Refine the user query with intelligent transformations."""
        # Correct spelling mistakes
        corrected_query = str(TextBlob(user_query).correct())

        # Use OpenAI to rephrase the query intelligently
        try:
            openai.api_key = "YOUR_OPENAI_API_KEY"  # Replace with your OpenAI API key
            response = openai.Completion.create(
                engine="text-davinci-003",
                prompt=f"Rephrase the following query to make it clearer and more precise:\n\n{corrected_query}",
                max_tokens=100,
                temperature=0.7
            )
            refined_query = response.choices[0].text.strip()
        except Exception as e:
            print(f"OpenAI API error: {e}")
            refined_query = corrected_query  # Fallback to the corrected query

        # Store the refined query in the database
        self.store_query(user_query, refined_query)
        return refined_query

# Example usage
if __name__ == "__main__":
    agent = PromptRefinementAgent()
    refined = agent.refine_query("list all services dependent on payment service")
    print("Refined Query:", refined)
    agent.update_feedback(1, "Works well!")
    print("All Refinements:", agent.fetch_refinements())