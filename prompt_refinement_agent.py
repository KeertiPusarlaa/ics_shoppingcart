import sqlite3
from typing import Optional, List
from textblob import TextBlob
from openai import OpenAI
import os

class PromptRefinementAgent:
    def __init__(self, db_path: str = "refinement_agent.db"):
        self.db_path = db_path
        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
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

    def refine_query(self, user_query: str, vector_database_context: str, preserve_keywords: List[str] = None) -> str:
        """Refine the user query with intelligent transformations."""
        # Correct spelling mistakes
        corrected_query = str(TextBlob(user_query).correct())

        # Use OpenAI to rephrase the query intelligently
        try:
            preserve_keywords = preserve_keywords or []
            preserve_instruction = "\n".join([f"Preserve the term '{keyword}' exactly as it is." for keyword in preserve_keywords])

            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert in refining and rephrasing natural language queries. Your task is to rephrase the user's query into a more detailed, specific, and precise version while preserving its original meaning. Use the context of previous similar queries and their refinements stored in the vector database to guide your rephrasing. Ensure the rephrased query is unambiguous and aligned with the user's intent."},
                    {"role": "user", "content": f"Original Query: {corrected_query}\n\nContext from Vector Database:\n{vector_database_context}\n\n{preserve_instruction}\nRephrase the above query into a more detailed and specific version. Use the context provided to ensure the rephrased query aligns with the user's intent and is optimized for clarity and precision."}
                ],
                max_tokens=150,
                temperature=0.7
            )
            refined_query = response.choices[0].message.content.strip()
        except Exception as e:
            print(f"OpenAI API error: {e}")
            refined_query = corrected_query  # Fallback to the corrected query

        # Store the refined query in the database
        self.store_query(user_query, refined_query)
        return refined_query

    def store_feedback_and_refinement(self, user_query: str, refined_query: str, feedback: str):
        """Store user feedback and refined query in the vector database."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO query_refinements (user_query, refined_query, feedback) VALUES (?, ?, ?)",
                (user_query, refined_query, feedback),
            )
            conn.commit()

    def retrieve_similar_queries(self, user_query: str):
        """Retrieve similar past queries and their outcomes."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT user_query, refined_query, feedback FROM query_refinements WHERE user_query LIKE ?",
                (f"%{user_query}%",),
            )
            return cursor.fetchall()

# Example usage
if __name__ == "__main__":
    agent = PromptRefinementAgent()
    refined = agent.refine_query("list all services dependent on payment service", "some vector database context")
    print("Refined Query:", refined)
    agent.update_feedback(1, "Works well!")
    print("All Refinements:", agent.fetch_refinements())