# ICS Shopping Cart EKG (Enterprise Knowledge Graph)

This project builds a concise, ontology-aligned knowledge graph of the **ICS Shopping Cart** and uplifts it into a **local Neo4j Desktop** instance.  
The goal is repeatable graph construction, clean ontology mapping, and minimal but accurate representation of the runtime architecture.

---

## 1. Ontology Used (Minimal Subset)

Only the ontology classes required to represent the runtime system were used:

### **Application**
Represents the entire system as a single top-level entity (the `ics_shopping_cart`).

### **Service**
A deployable microservice or component under `src/`.  
Properties:  
- `name`  
- `language` (derived from Dockerfile)  
- `repository_path`

### **DatabaseHost**
Stateful backends used at runtime.  
Detected through keywords in service names/Dockerfiles (`postgres`, `opensearch`, `valkey`).

### **API**
A concrete network interface for a service.  
APIs are constructed **entirely from `.env`**; this ensures ports, hosts, and addresses always resolve correctly, even when Dockerfiles expose variables like `${CURRENCY_PORT}`.

Properties include:  
- `host`  
- `port`  
- `protocol`  
- `address`

### **Schema / Table**
Postgres-only.  
Tables extracted from `src/postgres/init.sql`.

### **Relationships**
- **EXPOSES_API** — Service → API  
- **DEPENDS_ON** — from `docker-compose.yml`  
- **CALLS_SERVICE** — inferred from trace-testing YAMLs  
- **USES_DATABASE** — Service → DatabaseHost  
- **HAS_SCHEMA**, **HAS_TABLE** — for Postgres  
- **PART_OF** — API → Application, Service → Application  

This subset is sufficient to capture the complete runtime topology without modeling file-level details or implementation internals.

---

## 2. Graph Construction Workflow

The script that generates the graph, neo4j_graph_construction.py, proceeds in several phases:

### **1. Repository Scan**
- Looks under `src/` to find all top-level directories.  
- Dockerfiles are parsed for language detection.  
- Database detection is keyword-based.

### **2. Environment Variable Resolution**
- Parses `.env` to extract:
  - `${SERVICE}_PORT`
  - `${SERVICE}_HOST`
  - `${SERVICE}_ADDR`
- Resolves all runtime networking info.  
- Produces one API node per discovered network interface.

### **3. Compose Dependencies**
- Reads `docker-compose.yml`  
- Extracts `depends_on` entries  
- Generates `DEPENDS_ON` edges.

### **4. Test-based Edges**
- Parses YAML under `test/tracetesting/`  
- Searches for service names to infer runtime call paths  
- Produces `CALLS_SERVICE` edges.

### **5. Database Schema Extraction**
- Extracts table names from Postgres `init.sql`.

### **6. JSON Export**
All nodes and relationships are assembled into neo4j_ekg_data.json.

This file is the single source of truth for the Neo4j uplift step.

---

## 3. Contents of `neo4j_ekg_data.json`

The JSON contains the following top-level keys:

- **application**  
  One `Application` node representing `ics_shopping_cart`.

- **services**  
  A list of all Services with language + repository metadata.

- **databases**  
  DatabaseHost nodes.

- **apis**  
  API nodes resolved purely from `.env`.

- **compose_edges**  
  Map of Service → dependencies.

- **test_edges**  
  Inferred caller → callee relationships from tracing tests.

- **postgres_tables**  
  Extracted table names for `postgres`.

This JSON is complete, self-contained, and stable across graph rebuilds.

---

## 4. Graph Uplift Workflow (Neo4j)

The script `neo4j_graph_uplift.py` performs the full end-to-end uplift:

1. **Read `neo4j_ekg_data.json`**  
   - Automatically handles encoding and validation.

2. **Connect to Neo4j Desktop**  
   - URI, username, and password are configurable at the top of the script.

3. **Create Nodes**  
- `Application`, `Service`, `DatabaseHost`, `API`, `Schema`, `Table`.

4. **Create Relationships**  
- Executes Cypher MERGE statements for all ontology-defined edges.

5. **Commit and close connection**

The uplift process is deterministic and repeatable.

---

## 5. Maintenance and Extension

### **Adding New Ontology Elements**
If the system expands (e.g., new runtime components):
 
- Add new detection logic to the construction script.  
- Add a corresponding MERGE block to the uplift script.  
- No other changes required.

### **Adding New Relationships**
- Extend the JSON schema with new edges.
- Add relationship creation logic in the uplift script.

The separation of **construction (JSON)** and **uplift (Cypher)** keeps maintenance small and controlled.

---