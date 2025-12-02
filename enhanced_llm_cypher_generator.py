"""
Enhanced LLM Cypher Generation with Migration Intelligence Pipeline

Advanced version that combines:
1. Dynamic context building
2. Migration pattern recognition  
3. Risk assessment capabilities
4. Technology stack analysis

Usage: from enhanced_llm_cypher_generator import EnhancedLLMCypherGenerator
"""

import os
import json
from typing import List, Dict, Any, Optional
from pathlib import Path

# Core dependencies
from llm_cypher_generator import LLMCypherGenerator
from ekg_vector_store import EKGVectorStore, EKGSchemaExtractor, create_default_query_patterns

# LLM integration
from openai import OpenAI
client = OpenAI()
from neo4j import GraphDatabase


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


class EnhancedLLMCypherGenerator(LLMCypherGenerator):
    """Enhanced version with migration intelligence and dynamic context building"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.migration_pipeline = MigrationIntelligencePipeline(
            self.neo4j_driver, self.vector_store
        )
    
    def generate_cypher(self, natural_query: str) -> Dict[str, Any]:
        """Enhanced generation with migration intelligence"""
        
        # Check if this is a migration-related query
        query_lower = natural_query.lower()
        is_migration_query = any(keyword in query_lower for keyword in 
                               ["migration", "migrate", "risk", "complexity", "analysis", "assessment"])
        
        if is_migration_query:
            return self._generate_migration_cypher(natural_query)
        else:
            # Use standard generation for non-migration queries
            return super().generate_cypher(natural_query)
    
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
            context += f"- {elem['type']}: {elem['element']}\n"
        
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

User Question: {query}

Generate the migration-focused Cypher query:"""
        
        return context
    
    def _call_openai_with_migration_context(self, context: str, natural_query: str) -> str:
        """Call OpenAI API with migration-specific context"""
        
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
