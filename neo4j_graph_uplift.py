import os
import json
from pathlib import Path
from neo4j import GraphDatabase

GRAPH_JSON_PATH = Path("neo4j_ekg_data.json")


def load_graph_data(path: Path):
    if not path.exists():
        raise FileNotFoundError(f"Graph JSON not found at {path}")
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def get_neo4j_driver():
    uri = os.getenv("NEO4J_URI", "neo4j://127.0.0.1:7687")
    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD", "icsneo4j")
    return GraphDatabase.driver(uri, auth=(user, password))


def setup_constraints(tx):
    tx.run(
        "CREATE CONSTRAINT IF NOT EXISTS FOR (a:Application) "
        "REQUIRE a.name IS UNIQUE"
    )
    tx.run(
        "CREATE CONSTRAINT IF NOT EXISTS FOR (s:Service) "
        "REQUIRE s.name IS UNIQUE"
    )
    tx.run(
        "CREATE CONSTRAINT IF NOT EXISTS FOR (d:DatabaseHost) "
        "REQUIRE d.name IS UNIQUE"
    )
    tx.run(
        "CREATE CONSTRAINT IF NOT EXISTS FOR (api:API) "
        "REQUIRE api.id IS UNIQUE"
    )
    tx.run(
        "CREATE CONSTRAINT IF NOT EXISTS FOR (sch:Schema) "
        "REQUIRE sch.name IS UNIQUE"
    )
    tx.run(
        "CREATE CONSTRAINT IF NOT EXISTS FOR (t:Table) "
        "REQUIRE t.full_name IS UNIQUE"
    )


def create_application(tx, app):
    tx.run(
        """
        MERGE (a:Application {name: $name})
        SET a.type = $type
        """,
        name=app["name"],
        type=app.get("type"),
    )


def create_services(tx, services):
    tx.run(
        """
        UNWIND $services AS svc
        MERGE (s:Service {name: svc.name})
        SET s.language = svc.language,
            s.repository_path = svc.repository_path,
            s.frameworks = svc.frameworks,
            s.dependencies = svc.dependencies,
            s.java_version = svc.java_version
        """,
        services=services,
    )


def create_databases(tx, databases):
    tx.run(
        """
        UNWIND $databases AS db
        MERGE (d:DatabaseHost {name: db.name})
        SET d.repository_path = db.repository_path
        """,
        databases=databases,
    )


def build_api_id(api):
    return "|".join(
        [
            api.get("service") or "",
            api.get("host") or "",
            str(api.get("port") or ""),
            api.get("protocol") or "",
        ]
    )


def create_apis(tx, apis):
    # apis must already have "id" property populated
    tx.run(
        """
        UNWIND $apis AS api
        MERGE (a:API {id: api.id})
        SET a.service_key = api.service,
            a.protocol   = api.protocol,
            a.port       = api.port,
            a.host       = api.host,
            a.address    = api.address
        """,
        apis=apis,
    )


def link_services_to_application(tx, app_name, services):
    tx.run(
        """
        MATCH (app:Application {name: $app_name})
        UNWIND $services AS svc
        MATCH (s:Service {name: svc.name})
        MERGE (s)-[:PART_OF]->(app)
        """,
        app_name=app_name,
        services=services,
    )


def link_app_to_databases(tx, app_name, databases):
    tx.run(
        """
        MATCH (app:Application {name: $app_name})
        UNWIND $databases AS db
        MATCH (d:DatabaseHost {name: db.name})
        MERGE (app)-[:USES_DATABASE]->(d)
        """,
        app_name=app_name,
        databases=databases,
    )


def build_api_owner_mapping(service_names, db_names):
    """
    Map API.service keys to actual Service / DatabaseHost names.
    Covers env-prefix quirks.
    """
    special = {
        "frontend_proxy": "frontend-proxy",
        "image_provider": "image-provider",
        "product_catalog": "product-catalog",
        "product_reviews": "product-reviews",
        "locust_web": "load-generator",
        "envoy": "frontend-proxy",
        "envoy_admin": "frontend-proxy",
        "jaeger_ui": "jaeger",
        "jaeger_grpc": "jaeger",
        "postgres": "postgres",
        "valkey": "valkey-cart",  # will only work if you create such a node later
    }

    def resolve(key):
        target = special.get(key, key)
        if target in service_names or target in db_names:
            return target
        target_dash = target.replace("_", "-")
        if target_dash in service_names or target_dash in db_names:
            return target_dash
        return None

    return resolve


def link_exposes_api(tx, api_rels):
    """
    api_rels: list of dicts
      { owner_label, owner_name, api_id }
    """
    tx.run(
        """
        UNWIND $rels AS rel
        MATCH (o:`Service` {name: rel.owner_name})
        MATCH (api:API {id: rel.api_id})
        MERGE (o)-[:EXPOSES_API]->(api)
        """,
        rels=[r for r in api_rels if r["owner_label"] == "Service"],
    )

    tx.run(
        """
        UNWIND $rels AS rel
        MATCH (o:DatabaseHost {name: rel.owner_name})
        MATCH (api:API {id: rel.api_id})
        MERGE (o)-[:EXPOSES_API]->(api)
        """,
        rels=[r for r in api_rels if r["owner_label"] == "DatabaseHost"],
    )


def build_name_resolver(service_names, db_names):
    """
    Resolver for compose/test edge endpoints.
    Handles basic renames like postgresql -> postgres.
    """
    special = {
        "postgresql": "postgres",
    }

    def resolve(name):
        name0 = special.get(name, name)
        if name0 in service_names or name0 in db_names:
            return name0

        name_dash = name0.replace("_", "-")
        if name_dash in service_names or name_dash in db_names:
            return name_dash

        return None

    return resolve


def link_compose_dependencies(tx, compose_edges, service_names, db_names):
    """
    Create (:Service|DatabaseHost)-[:DEPENDS_ON]->(:Service|DatabaseHost)
    for endpoints that actually exist.
    """
    resolve = build_name_resolver(service_names, db_names)

    rels = []
    for raw_src, raw_deps in compose_edges.items():
        src = resolve(raw_src)
        if not src:
            continue
        for raw_tgt in raw_deps:
            tgt = resolve(raw_tgt)
            if not tgt:
                continue
            rels.append({"src": src, "tgt": tgt})

    if not rels:
        return

    tx.run(
        """
        UNWIND $rels AS r
        // source
        OPTIONAL MATCH (s:Service {name: r.src})
        OPTIONAL MATCH (sd:DatabaseHost {name: r.src})
        WITH r, coalesce(s, sd) AS srcNode
        WHERE srcNode IS NOT NULL

        OPTIONAL MATCH (t:Service {name: r.tgt})
        OPTIONAL MATCH (td:DatabaseHost {name: r.tgt})
        WITH srcNode, coalesce(t, td) AS dstNode
        WHERE dstNode IS NOT NULL

        MERGE (srcNode)-[:DEPENDS_ON]->(dstNode)
        """,
        rels=rels,
    )


def link_test_edges(tx, test_edges, service_names, db_names):
    """
    Use test edges as Service->Service CALLS_SERVICE relationships.
    Only create relationships when both endpoints resolve to Service nodes.
    """
    resolve = build_name_resolver(service_names, db_names)

    rels = []
    for src_raw, dst_raw in test_edges:
        src = resolve(src_raw)
        dst = resolve(dst_raw)
        if not src or not dst:
            continue
        if src not in service_names or dst not in service_names:
            continue
        rels.append({"src": src, "tgt": dst})

    if not rels:
        return

    tx.run(
        """
        UNWIND $rels AS r
        MATCH (s:Service {name: r.src})
        MATCH (t:Service {name: r.tgt})
        MERGE (s)-[:CALLS_SERVICE]->(t)
        """,
        rels=rels,
    )


def create_postgres_schema(tx, postgres_tables, db_name="postgres"):
    """
    From entries like 'accounting."order"' or 'reviews.productreviews',
    create Schema and Table nodes and link:

      (DatabaseHost {name: db_name})-[:HAS_SCHEMA]->(Schema)
      (Schema)-[:HAS_TABLE]->(Table)
    """
    if not postgres_tables:
        return

    parsed = []
    for full in postgres_tables:
        text = full.strip()
        # simple split on first dot
        if "." not in text:
            continue
        schema, table = text.split(".", 1)
        schema = schema.strip('"')
        table = table.strip('"')
        parsed.append(
            {
                "schema": schema,
                "table": table,
                "full_name": f"{schema}.{table}",
            }
        )

    if not parsed:
        return

    tx.run(
        """
        MATCH (db:DatabaseHost {name: $db_name})
        WITH db
        UNWIND $items AS row
        MERGE (s:Schema {name: row.schema})
        MERGE (db)-[:HAS_SCHEMA]->(s)
        MERGE (t:Table {full_name: row.full_name})
        SET t.name = row.table
        MERGE (s)-[:HAS_TABLE]->(t)
        """,
        db_name=db_name,
        items=parsed,
    )


def main():
    data = load_graph_data(GRAPH_JSON_PATH)

    application = data["application"]
    services = data.get("services", [])
    databases = data.get("databases", [])
    apis = data.get("apis", [])
    compose_edges = data.get("compose_edges", {})
    test_edges = data.get("test_edges", [])
    postgres_tables = data.get("postgres_tables", [])

    # Enrich APIs with stable ids
    for api in apis:
        api["id"] = build_api_id(api)

    service_names = {s["name"] for s in services}
    db_names = {d["name"] for d in databases}

    # Precompute owner mapping for API relationships
    resolve_api_owner = build_api_owner_mapping(service_names, db_names)
    api_rels = []
    for api in apis:
        svc_key = api.get("service")
        owner = resolve_api_owner(svc_key) if svc_key else None
        if owner is None:
            continue
        if owner in service_names:
            owner_label = "Service"
        elif owner in db_names:
            owner_label = "DatabaseHost"
        else:
            continue
        api_rels.append(
            {
                "owner_label": owner_label,
                "owner_name": owner,
                "api_id": api["id"],
            }
        )

    driver = get_neo4j_driver()
    try:
        with driver.session() as session:
            # Constraints
            session.execute_write(setup_constraints)

            # Nodes
            session.execute_write(create_application, application)
            session.execute_write(create_services, services)
            session.execute_write(create_databases, databases)
            session.execute_write(create_apis, apis)

            # Core ontology relationships
            session.execute_write(
                link_services_to_application,
                application["name"],
                services,
            )
            session.execute_write(
                link_app_to_databases,
                application["name"],
                databases,
            )
            session.execute_write(link_exposes_api, api_rels)
            session.execute_write(
                create_postgres_schema,
                postgres_tables,
                "postgres",
            )

            # Dependencies
            session.execute_write(
                link_compose_dependencies,
                compose_edges,
                service_names,
                db_names,
            )
            session.execute_write(
                link_test_edges,
                test_edges,
                service_names,
                db_names,
            )

        print("Neo4j uplift complete.")
    finally:
        driver.close()


if __name__ == "__main__":
    main()
