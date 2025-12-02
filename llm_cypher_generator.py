"""
LLM Cypher Generation with Vector Search Integration

This script combines:
1. Your existing Neo4j EKG
2. Milvus vector database
3. LLM for Cypher generation

Usage: python llm_cypher_generator.py "Show me all services that depend on postgres"
"""

import os
import json
import argparse
from typing import List, Dict, Any
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()  # MUST load before anything else

# Neo4j
from neo4j import GraphDatabase

# Our custom modules
from ekg_vector_store import EKGVectorStore, EKGSchemaExtractor, create_default_query_patterns

# OpenAI (NO top-level client creation!)
from openai import OpenAI


def get_openai_client():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY is missing. Add it to .env.")
    return OpenAI(api_key=api_key)



class LLMCypherGenerator:
    """Generates Cypher queries from natural language using LLM + Vector Search"""
    
    def __init__(self, 
                 neo4j_uri: str = None,
                 neo4j_user: str = None, 
                 neo4j_password: str = None,
                 milvus_host: str = None,
                 milvus_port: int = None):
        
        # Load from .env if not provided
        neo4j_uri = neo4j_uri or os.getenv("NEO4J_URI", "neo4j://127.0.0.1:7687")
        neo4j_user = neo4j_user or os.getenv("NEO4J_USER", "neo4j")
        neo4j_password = neo4j_password or os.getenv("NEO4J_PASSWORD", "icsneo4j")
        milvus_host = milvus_host or os.getenv("MILVUS_HOST", "localhost")
        milvus_port = milvus_port or int(os.getenv("MILVUS_PORT", 19530))

        # Neo4j connection
        self.neo4j_driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
        
        # Vector store
        self.vector_store = EKGVectorStore(milvus_host, milvus_port)
        
        # OpenAI client — IMPORTANT: do NOT pass key manually
        openai_key = os.getenv("OPENAI_API_KEY")
        if not openai_key:
            raise ValueError("OPENAI_API_KEY not found. Please set it in .env")
        
        self.client = OpenAI(api_key=openai_key)
    
    def setup_vector_data(self):
        """Initialize vector database with schema and query patterns"""
        print("Setting up vector database...")
        
        # Extract and store schema elements
        schema_extractor = EKGSchemaExtractor(
            "neo4j://127.0.0.1:7687", "neo4j", "icsneo4j"
        )
        schema_elements = schema_extractor.extract_schema_elements()
        self.vector_store.store_schema_elements(schema_elements)
        schema_extractor.close()
        
        # Store default query patterns
        query_patterns = create_default_query_patterns()
        self.vector_store.store_query_patterns(query_patterns)
        
        print("Vector database setup complete!")
    
    def generate_cypher(self, natural_query: str) -> Dict[str, Any]:
        """Generate Cypher query from natural language using LLM + Vector Search"""
        
        # 1. Get similar schema elements and query patterns from vector search
        similar_schema = self.vector_store.search_similar_schema(natural_query, top_k=5)
        similar_queries = self.vector_store.search_similar_queries(natural_query, top_k=3)
        
        # 2. Build context for LLM
        context = self._build_llm_context(natural_query, similar_schema, similar_queries)
        
        # 3. Generate Cypher using LLM
        cypher_query = self._call_openai_with_context(context, natural_query)
        
        return {
            "natural_query": natural_query,
            "generated_cypher": cypher_query,
            "similar_schema": similar_schema,
            "similar_queries": similar_queries,
            "context_used": context
        }
    
    def _build_llm_context(self, query: str, schema_elements: List[Dict], query_patterns: List[Dict]) -> str:
        """Build comprehensive context for LLM"""
        
        context = f"""
You are an expert Cypher query generator for a Neo4j graph database containing an Enterprise Knowledge Graph (EKG) of the ICS Shopping Cart microservices system.

## Graph Ontology:
- **Application**: The overall system (ics_shopping_cart)
- **Service**: Microservices (properties: name, language, repository_path)
- **DatabaseHost**: Database backends (properties: name, repository_path)  
- **API**: Network endpoints (properties: protocol, port, host, address)
- **Schema**: Database schemas (properties: name)
- **Table**: Database tables (properties: name, full_name)

## Relationships:
- **PART_OF**: Service → Application
- **EXPOSES_API**: Service → API, DatabaseHost → API
- **DEPENDS_ON**: Service → Service/DatabaseHost (from docker-compose)
- **CALLS_SERVICE**: Service → Service (from tests)
- **USES_DATABASE**: Application → DatabaseHost
- **HAS_SCHEMA**: DatabaseHost → Schema
- **HAS_TABLE**: Schema → Table

## Relevant Schema Elements Found:
"""
        
        for elem in schema_elements:
            # Handle different possible structures
            element_type = elem.get('type', elem.get('entity_type', 'Unknown'))
            element_name = elem.get('element', elem.get('name', elem.get('entity', 'Unknown')))
            element_text = elem.get('text', str(elem))[:100]
            context += f"- {element_type}: {element_name} (text: {element_text}...)\n"
        
        context += f"\n## Similar Query Patterns:\n"
        for pattern in query_patterns:
            # Handle different possible structures
            natural_q = pattern.get('natural_query', pattern.get('question', 'Unknown query'))
            cypher_q = pattern.get('cypher_query', pattern.get('cypher', 'Unknown cypher'))
            context += f"- Query: {natural_q}\n"
            context += f"  Cypher: {cypher_q}\n\n"
        
        context += f"""
## Rules:
1. Return ONLY the Cypher query, no explanation
2. Use MATCH patterns that align with the graph structure
3. Always include WHERE clauses for filtering
4. Use RETURN to specify what data to retrieve
5. For service queries, typically match: (s:Service)-[:PART_OF]->(a:Application)
6. For dependency queries, use: DEPENDS_ON or CALLS_SERVICE relationships
7. For database queries, match through: (db:DatabaseHost) and related schemas/tables

User Question: {query}

Generate the Cypher query:"""
        
        return context
    
    def _call_openai_with_context(self, context: str, natural_query: str) -> str:
        """Call OpenAI API with comprehensive context"""
        
        try:
            from openai import OpenAI
            client = OpenAI()
            
            response = client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {
                        "role": "system",
                        "content": context
                    },
                    {
                        "role": "user", 
                        "content": f"Generate Cypher for: {natural_query}"
                    }
                ],
                max_tokens=300,
                temperature=0.1
            )
            
            cypher_query = response.choices[0].message.content.strip()
            
            # Clean up the response (remove code blocks if present)
            if cypher_query.startswith("```"):
                cypher_query = cypher_query.split("\n", 1)[1]
            if cypher_query.endswith("```"):
                cypher_query = cypher_query.rsplit("\n", 1)[0]
                
            return cypher_query.strip()
            
        except Exception as e:
            print(f"OpenAI API error: {e}")
            # Fallback to vector-based generation
            return self._vector_based_cypher_generation(natural_query, [], [])
    
    def _vector_based_cypher_generation(self, query: str, schema_elements: List[Dict], query_patterns: List[Dict]) -> str:
        """Fallback: Generate Cypher using vector similarity patterns"""
        
        # Simple pattern matching based on keywords
        query_lower = query.lower()
        
        if "service" in query_lower and "java" in query_lower:
            return "MATCH (s:Service)-[:PART_OF]->(a:Application) WHERE s.language = 'Java' RETURN s.name, s.language"
        elif "service" in query_lower and "depend" in query_lower:
            return "MATCH (s:Service)-[:DEPENDS_ON]->(d) RETURN s.name, d.name, type(d)"
        elif "database" in query_lower:
            return "MATCH (db:DatabaseHost) RETURN db.name"
        elif "api" in query_lower:
            return "MATCH (s:Service)-[:EXPOSES_API]->(api:API) RETURN s.name, api.protocol, api.port"
        else:
            return "MATCH (s:Service)-[:PART_OF]->(a:Application) RETURN s.name, s.language"
    
    def execute_cypher(self, cypher_query: str) -> List[Dict]:
        """Execute Cypher query against Neo4j"""
        
        with self.neo4j_driver.session() as session:
            try:
                result = session.run(cypher_query)
                records = []
                for record in result:
                    records.append(dict(record))
                return records
            except Exception as e:
                print(f"Cypher execution error: {e}")
                return []
    
    def close(self):
        """Close connections"""
        self.neo4j_driver.close()
        # Vector store doesn't have a close method in our implementation


def main():
    """Main function to run the LLM Cypher generator"""
    
    parser = argparse.ArgumentParser(description="Generate Cypher queries from natural language")
    parser.add_argument("query", help="Natural language query")
    parser.add_argument("--setup", action="store_true", help="Initialize vector database")
    
    args = parser.parse_args()
    
    # Initialize the generator
    generator = LLMCypherGenerator()
    
    if args.setup:
        generator.setup_vector_data()
        return
    
    try:
        print(f"🤖 Processing: {args.query}")
        print("-" * 50)
        
        # Generate Cypher
        try:
            result = generator.generate_cypher(args.query)
            
            print(f"📝 Generated Cypher:")
            print(f"   {result['generated_cypher']}")
            print()
        except Exception as e:
            print(f"Generation Error: {e}")
            import traceback
            traceback.print_exc()
            return
        
        # Execute the query
        print(f"🔍 Executing query...")
        records = generator.execute_cypher(result['generated_cypher'])
        
        if records:
            print(f"✅ Results ({len(records)} records):")
            for i, record in enumerate(records[:10]):  # Show first 10 results
                print(f"   {i+1}: {record}")
            if len(records) > 10:
                print(f"   ... and {len(records) - 10} more records")
        else:
            print("❌ No results found")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        generator.close()


if __name__ == "__main__":
    main()
