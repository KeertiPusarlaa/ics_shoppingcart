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

# Our custom modules
from ekg_vector_store import EKGVectorStore, EKGSchemaExtractor, create_default_query_patterns
from prompt_refinement_agent import PromptRefinementAgent

# LLM integration
from openai import OpenAI
from neo4j import GraphDatabase

# Migration planning
from migration_plan_generator import MigrationPlanGenerator


class MigrationIntelligencePipeline:
    """Specialized pipeline for migration analysis and planning"""
    
    def __init__(self, neo4j_driver, vector_store):
        self.neo4j_driver = neo4j_driver
        self.vector_store = vector_store
        
    def analyze_service_complexity(self, service_name: str = None) -> Dict[str, Any]:
        """Analyze migration complexity for services"""
        
        if service_name:
            cypher = """
            MATCH (s:Service {name: $service_name})-[:PART_OF]->(a:Application)
            OPTIONAL MATCH (s)-[:DEPENDS_ON]->(dep)
            OPTIONAL MATCH (s)-[:EXPOSES_API]->(api:API) 
            OPTIONAL MATCH (caller:Service)-[:CALLS_SERVICE]->(s)
            RETURN s.name as service, s.language as language, s.repository_path as path,
                   collect(DISTINCT dep.name) as dependencies,
                   collect(DISTINCT api.port) as exposed_ports,
                   collect(DISTINCT caller.name) as callers
            """
            params = {"service_name": service_name}
        else:
            cypher = """
            MATCH (s:Service)-[:PART_OF]->(a:Application)
            OPTIONAL MATCH (s)-[:DEPENDS_ON]->(dep)
            OPTIONAL MATCH (s)-[:EXPOSES_API]->(api:API) 
            OPTIONAL MATCH (caller:Service)-[:CALLS_SERVICE]->(s)
            RETURN s.name as service, s.language as language, s.repository_path as path,
                   collect(DISTINCT dep.name) as dependencies,
                   collect(DISTINCT api.port) as exposed_ports,
                   collect(DISTINCT caller.name) as callers
            """
            params = {}
        
        with self.neo4j_driver.session() as session:
            result = session.run(cypher, params)
            services_data = []
            
            for record in result:
                service_analysis = {
                    "service": record["service"],
                    "language": record["language"], 
                    "path": record["path"],
                    "dependencies": [d for d in record["dependencies"] if d],
                    "exposed_ports": [p for p in record["exposed_ports"] if p],
                    "callers": [c for c in record["callers"] if c],
                    "complexity_score": self._calculate_complexity_score(record),
                    "migration_risk": self._assess_migration_risk(record)
                }
                services_data.append(service_analysis)
            
            return {
                "services": services_data,
                "total_services": len(services_data),
                "high_risk_services": [s for s in services_data if s["migration_risk"] == "HIGH"],
                "language_distribution": self._get_language_distribution(services_data)
            }
    
    def _calculate_complexity_score(self, record) -> int:
        """Calculate complexity score based on dependencies and connections"""
        dependencies = len([d for d in record["dependencies"] if d])
        callers = len([c for c in record["callers"] if c]) 
        apis = len([p for p in record["exposed_ports"] if p])
        
        # Simple scoring algorithm
        score = dependencies * 2 + callers * 3 + apis * 1
        return min(score, 100)  # Cap at 100
    
    def _assess_migration_risk(self, record) -> str:
        """Assess migration risk based on complexity and language"""
        complexity = self._calculate_complexity_score(record)
        language = record.get("language", "").lower()
        
        # Legacy languages have higher risk
        legacy_languages = ["cobol", "fortran", "perl", "vb", "asp"]
        modern_languages = ["python", "go", "javascript", "typescript", "java", "kotlin"]
        
        if complexity > 20 or language in legacy_languages:
            return "HIGH"
        elif complexity > 10 or language not in modern_languages:
            return "MEDIUM" 
        else:
            return "LOW"
    
    def _get_language_distribution(self, services_data: List[Dict]) -> Dict[str, int]:
        """Get distribution of programming languages"""
        distribution = {}
        for service in services_data:
            lang = service.get("language", "Unknown")
            distribution[lang] = distribution.get(lang, 0) + 1
        return distribution


class LLMCypherGenerator:
    """Generates Cypher queries from natural language using LLM + Vector Search"""
    
    def __init__(self, 
                 neo4j_uri: str = "neo4j://127.0.0.1:7687",
                 neo4j_user: str = "neo4j", 
                 neo4j_password: str = "icsneo4j",
                 openai_api_key: str = None,
                 milvus_host: str = "localhost",
                 milvus_port: int = 19530):
        
        # Neo4j connection
        self.neo4j_driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
        
        # Vector store
        self.vector_store = EKGVectorStore(milvus_host, milvus_port)
        
        # Migration intelligence pipeline
        self.migration_pipeline = MigrationIntelligencePipeline(self.neo4j_driver, self.vector_store)
        
        # OpenAI setup
        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        # Migration planner
        self.migration_planner = None

        # Initialize PromptRefinementAgent
        self.prompt_refinement_agent = PromptRefinementAgent()
    
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
        """Enhanced generation with iterative query refinement and learning."""

        preserve_keywords = ["kafka"]  # Add terms to preserve

        while True:
            # Fetch vector database context
            vector_database_context = self._get_vector_database_context(natural_query)

            # Refine the user query using the PromptRefinementAgent
            refined_query = self.prompt_refinement_agent.refine_query(natural_query, vector_database_context, preserve_keywords)

            # Prompt the user for confirmation
            print(f"Refined Query: \"{refined_query}\"")
            confirmation = input("Does this match your intent? (yes/no): ").strip().lower()

            if confirmation == "yes":
                # Save the final query to the database
                self.prompt_refinement_agent.store_query(natural_query, refined_query)
                break

            # Allow the user to provide corrections
            user_feedback = input("Please provide the correct query or feedback: ").strip()
            self.prompt_refinement_agent.store_feedback_and_refinement(natural_query, refined_query, user_feedback)

            # Update the natural query for the next iteration
            natural_query = user_feedback

        # Check if this is a migration planning query
        if self._is_migration_planning_query(refined_query):
            return self._generate_migration_plan_response(refined_query)

        # Check if this is a migration analysis query (needs better Cypher generation)
        query_lower = refined_query.lower()
        is_migration_analysis = any(keyword in query_lower for keyword in 
                                  ["migration", "migrate", "risk", "complexity", "analysis", "assessment"])

        if is_migration_analysis:
            return self._generate_migration_cypher(refined_query)
        else:
            # Use standard generation for regular data queries
            return self._generate_standard_cypher(refined_query)
    
    def _generate_migration_cypher(self, natural_query: str) -> Dict[str, Any]:
        """Generate Cypher specifically for migration analysis queries"""
        
        # 1. Get vector context as usual
        similar_schema = self.vector_store.search_similar_schema(natural_query, top_k=5)
        similar_queries = self.vector_store.search_similar_queries(natural_query, top_k=3)
        
        # 2. Build migration-specific context
        context = self._build_migration_context(natural_query, similar_schema, similar_queries)
        
        # 3. Generate using OpenAI with migration focus
        cypher_query = self._call_openai_with_migration_context(context, natural_query)
        
        # 4. If it's a comprehensive analysis, enhance with pipeline data
        if "comprehensive" in natural_query.lower() or "all services" in natural_query.lower():
            pipeline_analysis = self.migration_pipeline.analyze_service_complexity()
            return {
                "natural_query": natural_query,
                "generated_cypher": cypher_query, 
                "migration_analysis": pipeline_analysis,
                "similar_schema": similar_schema,
                "similar_queries": similar_queries,
                "context_used": context
            }
        
        return {
            "natural_query": natural_query,
            "generated_cypher": cypher_query,
            "similar_schema": similar_schema, 
            "similar_queries": similar_queries,
            "context_used": context
        }
    
    def _generate_standard_cypher(self, natural_query: str) -> Dict[str, Any]:
        """Standard Cypher generation for non-migration queries"""
        
        # Special handling for 'kafka' to ensure it is treated as a Service node
        if "kafka" in natural_query.lower():
            return {
                "natural_query": natural_query,
                "generated_cypher": "MATCH (s:Service)-[:DEPENDS_ON]->(dep:Service {name: 'kafka'}) RETURN s.name"
            }

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
    
    def _is_migration_planning_query(self, query: str) -> bool:
        """Check if query is asking for migration planning rather than data"""
        
        query_lower = query.lower()
        
        planning_keywords = [
            "plan", "planning", "how to", "steps", "migrate", "migration plan",
            "strategy", "approach", "roadmap", "timeline", "process"
        ]
        
        return any(keyword in query_lower for keyword in planning_keywords)
    
    def _generate_migration_plan_response(self, natural_query: str) -> Dict[str, Any]:
        """Generate migration plan instead of Cypher query"""
        
        # Initialize migration planner if not already done
        if not self.migration_planner:
            try:
                self.migration_planner = MigrationPlanGenerator()
            except Exception as e:
                return {
                    "natural_query": natural_query,
                    "response_type": "migration_plan",
                    "error": f"Migration planner unavailable: {str(e)}",
                    "fallback_message": "Migration planning feature requires additional setup. Please use regular queries for now."
                }
        
        try:
            # Generate migration plan
            migration_plan = self.migration_planner.generate_migration_plan(natural_query)
            
            return {
                "natural_query": natural_query,
                "response_type": "migration_plan",
                "migration_plan": {
                    "title": migration_plan.title,
                    "description": migration_plan.description,
                    "migration_type": migration_plan.migration_type.value,
                    "affected_services": migration_plan.affected_services,
                    "timeline": migration_plan.timeline,
                    "total_effort": migration_plan.total_estimated_effort,
                    "prerequisites": migration_plan.prerequisites,
                    "steps": [
                        {
                            "step": step.step_number,
                            "title": step.title,
                            "description": step.description,
                            "category": step.category,
                            "effort": step.estimated_effort,
                            "dependencies": step.dependencies,
                            "risks": step.risks,
                            "validation": step.validation_criteria
                        }
                        for step in migration_plan.steps
                    ],
                    "risks_and_mitigations": migration_plan.risks_and_mitigations,
                    "success_metrics": migration_plan.success_metrics
                }
            }
            
        except Exception as e:
            return {
                "natural_query": natural_query,
                "response_type": "migration_plan",
                "error": f"Migration planning failed: {str(e)}",
                "fallback_message": "Could not generate migration plan. Try asking for system data instead."
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

## CRITICAL Cypher Syntax Rules:
- Multiple relationship types: Use `DEPENDS_ON|CALLS_SERVICE` (NOT `:DEPENDS_ON|:CALLS_SERVICE`)
- Variable length paths: Use `[:DEPENDS_ON|CALLS_SERVICE*1..3]` (NOT `[:DEPENDS_ON|:CALLS_SERVICE*1..3]`)
- Single relationships: Use `-[r:DEPENDS_ON|CALLS_SERVICE]->` (NOT `-[r:DEPENDS_ON|:CALLS_SERVICE]->`)

User Question: {query}

Generate the Cypher query:"""
        
        return context
    
    def _call_openai_with_context(self, context: str, natural_query: str) -> str:
        """Call OpenAI API with comprehensive context and handle errors gracefully."""
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": context},
                    {"role": "user", "content": f"Generate Cypher for: {natural_query}"}
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
            error_str = str(e).lower()
            if "authentication" in error_str or "api key" in error_str:
                print("OpenAI API error: Invalid API key. Please check your API key.")
            elif "rate limit" in error_str or "quota" in error_str:
                print("OpenAI API error: Rate limit exceeded. Please try again later.")
            else:
                print(f"OpenAI API error: {e}")
            
            # Return fallback query generation
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
    
    def _build_migration_context(self, query: str, schema_elements: List[Dict], query_patterns: List[Dict]) -> str:
        """Build migration-specific context for LLM"""
        
        context = f"""
You are an expert Cypher query generator specializing in enterprise migration analysis for the ICS Shopping Cart microservices system.

## Migration Analysis Focus:
Generate Cypher queries that help assess:
1. **Service Dependencies**: Which services depend on what (DEPENDS_ON, CALLS_SERVICE)
2. **Technology Stack**: Programming languages, frameworks used by services
3. **Risk Assessment**: Services with high complexity or legacy technology
4. **Impact Analysis**: Downstream effects of migrating specific services

## Graph Schema for Migration Analysis:
- **Service** nodes: name, language, repository_path
- **DatabaseHost** nodes: name, repository_path  
- **API** nodes: protocol, port, host
- **DEPENDS_ON**: Service dependencies (infrastructure & service-to-service)
- **CALLS_SERVICE**: Runtime service calls (from tests)
- **EXPOSES_API**: Services exposing network endpoints

## Migration Query Patterns:
"""
        
        # Add relevant schema elements
        for elem in schema_elements:
            element_type = elem.get('type', elem.get('entity_type', 'Unknown'))
            element_name = elem.get('element', elem.get('name', elem.get('entity', 'Unknown')))
            context += f"- {element_type}: {element_name}\n"
        
        # Add migration-specific query examples
        context += f"""

## Example Migration Queries:
- "Show services with most dependencies": 
  MATCH (s:Service)-[:DEPENDS_ON]->(d) RETURN s.name, count(d) as dep_count ORDER BY dep_count DESC

- "Find Java services for migration":
  MATCH (s:Service) WHERE s.language = 'Java' RETURN s.name, s.repository_path

- "Analyze service call patterns":
  MATCH (caller:Service)-[:CALLS_SERVICE]->(target:Service) RETURN caller.name, target.name

- "Database dependencies analysis":
  MATCH (s:Service)-[:DEPENDS_ON]->(db:DatabaseHost) RETURN s.name, db.name

## Instructions:
1. Return ONLY the Cypher query, no explanation
2. Focus on migration-relevant data (dependencies, languages, complexity)
3. Use aggregation (count, collect) for analysis queries
4. Include ORDER BY for ranking/prioritization queries
5. Use WHERE clauses to filter by technology stack when relevant

## CRITICAL Cypher Syntax Rules:
- Multiple relationship types: Use `DEPENDS_ON|CALLS_SERVICE` (NOT `:DEPENDS_ON|:CALLS_SERVICE`)
- Variable length paths: Use `[:DEPENDS_ON|CALLS_SERVICE*1..3]` (NOT `[:DEPENDS_ON|:CALLS_SERVICE*1..3]`)
- Single relationships: Use `-[r:DEPENDS_ON|CALLS_SERVICE]->` (NOT `-[r:DEPENDS_ON|:CALLS_SERVICE]->`)

User Question: {query}

Generate the migration-focused Cypher query:"""
        
        return context
    
    def _call_openai_with_migration_context(self, context: str, natural_query: str) -> str:
        """Call OpenAI API with migration-specific context"""
        
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {
                        "role": "system", 
                        "content": context
                    },
                    {
                        "role": "user",
                        "content": f"Generate migration analysis Cypher for: {natural_query}"
                    }
                ],
                max_tokens=400,
                temperature=0.1
            )
            
            cypher_query = response.choices[0].message.content.strip()
            
            # Clean up the response
            if cypher_query.startswith("```"):
                cypher_query = cypher_query.split("\n", 1)[1] 
            if cypher_query.endswith("```"):
                cypher_query = cypher_query.rsplit("\n", 1)[0]
                
            return cypher_query.strip()
            
        except Exception as e:
            print(f"OpenAI API error: {e}")
            # Fallback to migration-specific patterns
            return self._migration_fallback_cypher(natural_query)
    
    def _migration_fallback_cypher(self, query: str) -> str:
        """Fallback Cypher generation for migration queries"""
        
        query_lower = query.lower()
        
        if "risk" in query_lower or "complexity" in query_lower:
            return """
            MATCH (s:Service)-[:PART_OF]->(a:Application)
            OPTIONAL MATCH (s)-[:DEPENDS_ON]->(dep)
            OPTIONAL MATCH (caller)-[:CALLS_SERVICE]->(s)
            RETURN s.name, s.language, 
                   count(DISTINCT dep) as dependencies,
                   count(DISTINCT caller) as callers
            ORDER BY dependencies DESC, callers DESC
            """
            
        elif "java" in query_lower:
            return "MATCH (s:Service) WHERE s.language = 'Java' RETURN s.name, s.repository_path"
            
        elif "depend" in query_lower:
            return "MATCH (s:Service)-[:DEPENDS_ON]->(d) RETURN s.name, d.name, labels(d)"
            
        elif "database" in query_lower:
            return "MATCH (s:Service)-[:DEPENDS_ON]->(db:DatabaseHost) RETURN s.name, db.name"
            
        else:
            return "MATCH (s:Service)-[:PART_OF]->(a:Application) RETURN s.name, s.language"

    def _get_vector_database_context(self, query: str) -> str:
        """Fetch relevant context from the vector database."""
        similar_schema = self.vector_store.search_similar_schema(query, top_k=5)
        similar_queries = self.vector_store.search_similar_queries(query, top_k=3)

        context = "\n## Similar Schema Elements:\n"
        for schema in similar_schema:
            context += f"- {schema['name']}: {schema['description']}\n"

        context += "\n## Similar Query Patterns:\n"
        for pattern in similar_queries:
            context += f"- Query: {pattern['natural_query']}\n  Cypher: {pattern['cypher_query']}\n"

        return context

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
        
        # Generate Cypher or Migration Plan
        try:
            result = generator.generate_cypher(args.query)
            
            # Handle migration plan response
            if result.get('response_type') == 'migration_plan':
                if 'error' in result:
                    print(f"❌ {result['error']}")
                    if 'fallback_message' in result:
                        print(f"💡 {result['fallback_message']}")
                    return
                
                # Display migration plan
                plan = result['migration_plan']
                print(f"📋 MIGRATION PLAN: {plan['title']}")
                print("=" * 60)
                print(f"📄 Description: {plan['description']}")
                print(f"🎯 Type: {plan['migration_type'].replace('_', ' ').title()}")
                print(f"🏷️  Affected Services: {len(plan['affected_services'])} {'service' if len(plan['affected_services']) == 1 else 'services'}")
                if plan['affected_services']:
                    print(f"   Services: {', '.join(plan['affected_services'])}")
                print(f"⏰ Timeline: {plan['timeline']}")
                print(f"💪 Effort Level: {plan['total_effort'].replace('_', ' ').title()}")
                print()
                
                print("📋 PREREQUISITES:")
                for i, prereq in enumerate(plan['prerequisites'], 1):
                    print(f"   {i}. {prereq}")
                print()
                
                print("🔄 MIGRATION STEPS:")
                for step in plan['steps']:
                    print(f"   Step {step['step']}: {step['title']}")
                    print(f"      Category: {step['category']} | Effort: {step['effort']}")
                    print(f"      Description: {step['description']}")
                    if step['dependencies']:
                        print(f"      Dependencies: {', '.join(step['dependencies'])}")
                    print()
                
                print("⚠️ RISKS & MITIGATIONS:")
                for risk, mitigation in plan['risks_and_mitigations'].items():
                    print(f"   Risk: {risk}")
                    print(f"   Mitigation: {mitigation}")
                    print()
                
                print("🎯 SUCCESS METRICS:")
                for i, metric in enumerate(plan['success_metrics'], 1):
                    print(f"   {i}. {metric}")
                
                return
            
            # Handle regular Cypher query
            print(f"📝 Generated Cypher:")
            print(f"   {result['generated_cypher']}")
            print()
        except Exception as e:
            print(f"Generation Error: {e}")
            import traceback
            traceback.print_exc()
            return
        
        # Execute the query (only for regular Cypher)
        if result.get('response_type') != 'migration_plan':
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
