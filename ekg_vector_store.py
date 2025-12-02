"""
Milvus Vector DB Integration for EKG LLM Cypher Generation

This module handles:
1. Schema embedding and storage
2. Query pattern storage and retrieval
3. Context augmentation for LLM Cypher generation
"""

import os
import json
from pathlib import Path
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass

from dotenv import load_dotenv
load_dotenv()

# Vector DB and embeddings imports
from pymilvus import Collection, FieldSchema, CollectionSchema, DataType, connections, utility
from sentence_transformers import SentenceTransformer

# Neo4j integration
from neo4j import GraphDatabase

from openai import OpenAI

def get_openai_client():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not set.")
    return OpenAI(api_key=api_key)



@dataclass
class SchemaElement:
    """Represents a graph schema element for embedding"""
    element_type: str  # 'node', 'relationship', 'property'
    name: str
    description: str
    context: Dict[str, Any]


@dataclass 
class QueryPattern:
    """Represents a natural language -> Cypher query pattern"""
    natural_query: str
    cypher_query: str
    description: str
    complexity: str  # 'simple', 'medium', 'complex'


class EKGVectorStore:
    """Manages vector embeddings for EKG schema and query patterns"""
    
    def __init__(self, 
                 milvus_host: str = "localhost",
                 milvus_port: int = 19530,
                 embedding_model: str = "all-MiniLM-L6-v2"):
        
        self.milvus_host = milvus_host
        self.milvus_port = milvus_port
        
        # Initialize embedding model
        self.embedding_model = SentenceTransformer(embedding_model)
        self.embedding_dim = self.embedding_model.get_sentence_embedding_dimension()
        
        # Collection names
        self.schema_collection_name = "ekg_schema_embeddings"
        self.query_collection_name = "ekg_query_patterns"
        
        # Connect to Milvus
        self._connect_milvus()
        
        # Initialize collections
        self._setup_collections()
    
    def _connect_milvus(self):
        """Connect to Milvus database"""
        connections.connect("default", host=self.milvus_host, port=self.milvus_port)
        print(f"Connected to Milvus at {self.milvus_host}:{self.milvus_port}")
    
    def _setup_collections(self):
        """Create and setup Milvus collections"""
        self._setup_schema_collection()
        self._setup_query_collection()
    
    def _setup_schema_collection(self):
        """Setup collection for schema embeddings"""
        fields = [
            FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
            FieldSchema(name="element_type", dtype=DataType.VARCHAR, max_length=50),
            FieldSchema(name="name", dtype=DataType.VARCHAR, max_length=200),
            FieldSchema(name="description", dtype=DataType.VARCHAR, max_length=1000),
            FieldSchema(name="context", dtype=DataType.VARCHAR, max_length=2000),
            FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=self.embedding_dim)
        ]
        
        schema = CollectionSchema(fields, "EKG Schema Embeddings")
        
        if not utility.has_collection(self.schema_collection_name):
            self.schema_collection = Collection(self.schema_collection_name, schema)
            # Create index for vector similarity search
            index_params = {
                "metric_type": "COSINE",
                "index_type": "IVF_FLAT",
                "params": {"nlist": 128}
            }
            self.schema_collection.create_index("embedding", index_params)
        else:
            self.schema_collection = Collection(self.schema_collection_name)
    
    def _setup_query_collection(self):
        """Setup collection for query pattern embeddings"""
        fields = [
            FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
            FieldSchema(name="natural_query", dtype=DataType.VARCHAR, max_length=500),
            FieldSchema(name="cypher_query", dtype=DataType.VARCHAR, max_length=2000),
            FieldSchema(name="description", dtype=DataType.VARCHAR, max_length=500),
            FieldSchema(name="complexity", dtype=DataType.VARCHAR, max_length=20),
            FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=self.embedding_dim)
        ]
        
        schema = CollectionSchema(fields, "EKG Query Pattern Embeddings")
        
        if not utility.has_collection(self.query_collection_name):
            self.query_collection = Collection(self.query_collection_name, schema)
            # Create index
            index_params = {
                "metric_type": "COSINE", 
                "index_type": "IVF_FLAT",
                "params": {"nlist": 128}
            }
            self.query_collection.create_index("embedding", index_params)
        else:
            self.query_collection = Collection(self.query_collection_name)
    
    def embed_text(self, text: str) -> List[float]:
        """Generate embedding for text"""
        return self.embedding_model.encode(text).tolist()
    
    def store_schema_elements(self, elements: List[SchemaElement]):
        """Store schema elements with embeddings"""
        embeddings = []
        element_types = []
        names = []
        descriptions = []
        contexts = []
        
        for element in elements:
            # Create comprehensive text for embedding
            embed_text = f"{element.element_type}: {element.name}. {element.description}"
            if element.context:
                embed_text += f" Context: {json.dumps(element.context)}"
            
            embedding = self.embed_text(embed_text)
            
            embeddings.append(embedding)
            element_types.append(element.element_type)
            names.append(element.name)
            descriptions.append(element.description)
            contexts.append(json.dumps(element.context))
        
        # Insert into collection
        data = [element_types, names, descriptions, contexts, embeddings]
        self.schema_collection.insert(data)
        self.schema_collection.flush()
        print(f"Stored {len(elements)} schema elements")
    
    def store_query_patterns(self, patterns: List[QueryPattern]):
        """Store query patterns with embeddings"""
        embeddings = []
        natural_queries = []
        cypher_queries = []
        descriptions = []
        complexities = []
        
        for pattern in patterns:
            # Embed the natural language query
            embedding = self.embed_text(pattern.natural_query)
            
            embeddings.append(embedding)
            natural_queries.append(pattern.natural_query)
            cypher_queries.append(pattern.cypher_query)
            descriptions.append(pattern.description)
            complexities.append(pattern.complexity)
        
        # Insert into collection
        data = [natural_queries, cypher_queries, descriptions, complexities, embeddings]
        self.query_collection.insert(data)
        self.query_collection.flush()
        print(f"Stored {len(patterns)} query patterns")
    
    def search_similar_schema(self, query: str, top_k: int = 5) -> List[Dict]:
        """Search for similar schema elements"""
        self.schema_collection.load()
        
        query_embedding = self.embed_text(query)
        
        search_params = {"metric_type": "COSINE", "params": {"nprobe": 10}}
        results = self.schema_collection.search(
            [query_embedding],
            "embedding",
            search_params,
            limit=top_k,
            output_fields=["element_type", "name", "description", "context"]
        )
        
        similar_elements = []
        for result in results[0]:
            similar_elements.append({
                "element_type": result.entity.get("element_type"),
                "name": result.entity.get("name"),
                "description": result.entity.get("description"),
                "context": json.loads(result.entity.get("context")),
                "similarity": result.score
            })
        
        return similar_elements
    
    def search_similar_queries(self, query: str, top_k: int = 3) -> List[Dict]:
        """Search for similar query patterns"""
        self.query_collection.load()
        
        query_embedding = self.embed_text(query)
        
        search_params = {"metric_type": "COSINE", "params": {"nprobe": 10}}
        results = self.query_collection.search(
            [query_embedding],
            "embedding", 
            search_params,
            limit=top_k,
            output_fields=["natural_query", "cypher_query", "description", "complexity"]
        )
        
        similar_queries = []
        for result in results[0]:
            similar_queries.append({
                "natural_query": result.entity.get("natural_query"),
                "cypher_query": result.entity.get("cypher_query"),
                "description": result.entity.get("description"),
                "complexity": result.entity.get("complexity"),
                "similarity": result.score
            })
        
        return similar_queries


class EKGSchemaExtractor:
    """Extracts schema information from Neo4j for embedding"""
    
    def __init__(self, neo4j_uri: str, neo4j_user: str, neo4j_password: str):
        self.driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
    
    def extract_schema_elements(self) -> List[SchemaElement]:
        """Extract all schema elements from Neo4j graph"""
        elements = []
        
        with self.driver.session() as session:
            # Extract node types
            node_types = session.run("CALL db.labels()").values()
            for node_type in node_types:
                label = node_type[0]
                
                # Get sample properties
                props_result = session.run(f"""
                    MATCH (n:{label})
                    WITH keys(n) as props
                    UNWIND props as prop
                    RETURN DISTINCT prop
                """)
                properties = [record["prop"] for record in props_result]
                
                elements.append(SchemaElement(
                    element_type="node",
                    name=label,
                    description=f"Node type representing {label} entities in the ICS Shopping Cart system",
                    context={"properties": properties, "label": label}
                ))
            
            # Extract relationship types
            rel_types = session.run("CALL db.relationshipTypes()").values()
            for rel_type in rel_types:
                rel = rel_type[0]
                
                # Get relationship patterns
                patterns_result = session.run(f"""
                    MATCH (a)-[r:{rel}]->(b)
                    RETURN DISTINCT labels(a)[0] as source_label, labels(b)[0] as target_label
                    LIMIT 5
                """)
                patterns = [{"source": record["source_label"], "target": record["target_label"]} 
                           for record in patterns_result]
                
                elements.append(SchemaElement(
                    element_type="relationship",
                    name=rel,
                    description=f"Relationship type {rel} connecting related entities",
                    context={"patterns": patterns, "relationship": rel}
                ))
        
        return elements
    
    def close(self):
        self.driver.close()


def create_default_query_patterns() -> List[QueryPattern]:
    """Create default query patterns for ICS Shopping Cart EKG"""
    return [
        QueryPattern(
            natural_query="Show me all services",
            cypher_query="MATCH (s:Service) RETURN s.name, s.language, s.repository_path",
            description="Retrieve all services with their basic properties",
            complexity="simple"
        ),
        QueryPattern(
            natural_query="What services depend on databases?",
            cypher_query="MATCH (s:Service)-[:DEPENDS_ON]->(db:DatabaseHost) RETURN s.name, db.name",
            description="Find services that have database dependencies",
            complexity="simple"
        ),
        QueryPattern(
            natural_query="Show me the complete service dependency chain",
            cypher_query="""
            MATCH path = (s:Service)-[:DEPENDS_ON*1..3]->(target)
            RETURN s.name as service, 
                   [n in nodes(path) | n.name] as dependency_chain,
                   length(path) as chain_length
            ORDER BY chain_length DESC
            """,
            description="Find multi-level service dependencies",
            complexity="complex"
        ),
        QueryPattern(
            natural_query="Which services expose APIs?",
            cypher_query="MATCH (s:Service)-[:EXPOSES_API]->(api:API) RETURN s.name, api.protocol, api.port, api.host",
            description="Find services and their exposed APIs",
            complexity="simple"
        ),
        QueryPattern(
            natural_query="Find services written in specific programming language",
            cypher_query="MATCH (s:Service) WHERE s.language = $language RETURN s.name, s.repository_path",
            description="Filter services by programming language",
            complexity="simple"
        ),
        QueryPattern(
            natural_query="Show me service call patterns from tests",
            cypher_query="MATCH (caller:Service)-[:CALLS_SERVICE]->(callee:Service) RETURN caller.name, callee.name",
            description="Display service-to-service communication patterns",
            complexity="simple"
        ),
        QueryPattern(
            natural_query="What are the database schemas and tables?",
            cypher_query="""
            MATCH (db:DatabaseHost)-[:HAS_SCHEMA]->(schema:Schema)-[:HAS_TABLE]->(table:Table)
            RETURN db.name as database, schema.name as schema, collect(table.name) as tables
            """,
            description="Show database structure with schemas and tables",
            complexity="medium"
        ),
        QueryPattern(
            natural_query="Find the most connected services",
            cypher_query="""
            MATCH (s:Service)
            OPTIONAL MATCH (s)-[:DEPENDS_ON]->(dep)
            OPTIONAL MATCH (dependent)-[:DEPENDS_ON]->(s)
            OPTIONAL MATCH (s)-[:EXPOSES_API]->(api:API)
            RETURN s.name, 
                   count(DISTINCT dep) as dependencies,
                   count(DISTINCT dependent) as dependents,
                   count(DISTINCT api) as apis,
                   (count(DISTINCT dep) + count(DISTINCT dependent) + count(DISTINCT api)) as total_connections
            ORDER BY total_connections DESC
            LIMIT 10
            """,
            description="Rank services by their connectivity in the system",
            complexity="complex"
        ),
        QueryPattern(
            natural_query="Show me Java services in the application with their versions and frameworks",
            cypher_query="""
            MATCH (service:Service)-[:PART_OF]->(app:Application)
            WHERE toLower(service.language) = 'java'
            RETURN service.name, service.java_version, service.frameworks, service.dependencies, app.name as application
            """,
            description="Find Java services with version and framework information for migration planning",
            complexity="medium"
        ),
        QueryPattern(
            natural_query="Migration assessment for specific service with impact analysis",
            cypher_query="""
            MATCH (service:Service {name: $serviceName})-[:PART_OF]->(app:Application)
            WHERE toLower(service.language) = 'java'
            OPTIONAL MATCH (service)-[:DEPENDS_ON]->(dep)
            OPTIONAL MATCH (caller:Service)-[:CALLS_SERVICE]->(service)
            RETURN service.name, service.java_version, service.frameworks, service.dependencies,
                   collect(DISTINCT dep.name) as serviceDependencies,
                   collect(DISTINCT caller.name) as downstreamServices,
                   app.name as application
            """,
            description="Comprehensive migration analysis for a specific Java service",
            complexity="complex"
        ),
        QueryPattern(
            natural_query="Find services in application that need Java version upgrade",
            cypher_query="""
            MATCH (service:Service)-[:PART_OF]->(app:Application)
            WHERE toLower(service.language) = 'java' AND service.java_version IS NOT NULL
            WITH service, app, CASE 
                WHEN service.java_version CONTAINS '.' THEN toFloat(service.java_version)
                ELSE toFloat(service.java_version)
            END AS version_num
            WHERE version_num < 21.0
            RETURN service.name, service.java_version, service.frameworks, service.dependencies, app.name as application
            """,
            description="Identify Java services needing version upgrades for migration planning",
            complexity="complex"
        ),
        QueryPattern(
            natural_query="Comprehensive Java ecosystem migration analysis with priority and risk assessment",
            cypher_query="""
            MATCH (javaService:Service)-[:PART_OF]->(app:Application)
            WHERE toLower(javaService.language) = 'java'
            WITH javaService, app,
                 CASE 
                   WHEN javaService.java_version CONTAINS '.' THEN toFloat(javaService.java_version)
                   ELSE toFloat(javaService.java_version)
                 END AS versionNum
            OPTIONAL MATCH (javaService)-[:DEPENDS_ON]->(serviceDep)
            OPTIONAL MATCH (downstream:Service)-[:CALLS_SERVICE]->(javaService)
            OPTIONAL MATCH (javaService)-[:EXPOSES_API]->(api:API)
            WITH javaService, app, versionNum, 
                 collect(DISTINCT serviceDep.name) AS serviceDependencies,
                 collect(DISTINCT downstream.name) AS impactedServices,
                 count(DISTINCT downstream) AS riskScore,
                 collect(DISTINCT api.protocol) AS exposedProtocols
            RETURN javaService.name AS serviceName,
                   javaService.java_version AS currentVersion,
                   CASE 
                     WHEN versionNum >= 21.0 THEN 'Current'
                     WHEN versionNum >= 17.0 THEN 'Moderate Priority'
                     ELSE 'High Priority'
                   END AS migrationPriority,
                   javaService.frameworks AS frameworks,
                   javaService.dependencies AS externalLibs,
                   serviceDependencies,
                   impactedServices,
                   riskScore,
                   exposedProtocols,
                   app.name AS application
            ORDER BY versionNum ASC, riskScore DESC
            """,
            description="Advanced migration analysis with business intelligence and risk assessment",
            complexity="complex"
        )
    ]


if __name__ == "__main__":
    # Example usage
    print("EKG Milvus Vector Store Integration")
    print("This module provides vector search capabilities for LLM Cypher generation")