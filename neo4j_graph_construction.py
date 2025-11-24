import os
import re
import json
import yaml
from pathlib import Path

REPO_ROOT = Path("ics_shopping_cart")


############################################################
# UTILITIES
############################################################

def read_text(path: Path):
    if path.exists():
        return path.read_text(encoding="utf-8", errors="ignore")
    return ""


def substitute_env_vars(value, env):
    """
    Replace ${VAR} or $VAR using the parsed .env dictionary.
    """
    if value is None:
        return value

    # ${VAR}
    pattern1 = re.compile(r"\$\{([A-Za-z0-9_]+)\}")
    # $VAR
    pattern2 = re.compile(r"\$([A-Za-z0-9_]+)")

    def repl1(m):
        k = m.group(1)
        return env.get(k, m.group(0))

    def repl2(m):
        k = m.group(1)
        return env.get(k, m.group(0))

    value = pattern1.sub(repl1, value)
    value = pattern2.sub(repl2, value)
    return value


############################################################
# 1. PARSE .env
############################################################

def parse_env_file():
    env_path = REPO_ROOT / ".env"
    if not env_path.exists():
        return {}

    env = {}
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, val = line.split("=", 1)
        key = key.strip()
        val = val.strip()
        env[key] = val

    # Perform substitution on values after global read
    for k in list(env.keys()):
        env[k] = substitute_env_vars(env[k], env)

    return env


############################################################
# 2. Detect Service Language + DB classification
############################################################

def detect_language_comprehensive(service_path):
    """Migration-ready language detection using multiple indicators"""
    dockerfile_path = service_path / "Dockerfile"
    dockerfile_text = read_text(dockerfile_path).lower()
    
    # Check package/build files (MOST RELIABLE)
    if (service_path / "package.json").exists():
        return "javascript"
    if (service_path / "pom.xml").exists() or (service_path / "build.gradle").exists():
        return "java"
    if (service_path / "go.mod").exists():
        return "go"
    if (service_path / "requirements.txt").exists() or (service_path / "pyproject.toml").exists():
        return "python"
    if (service_path / "Cargo.toml").exists():
        return "rust"
    if (service_path / "Gemfile").exists():
        return "ruby"
    if (service_path / "composer.json").exists():
        return "php"
    if any((service_path).glob("*.csproj")) or any((service_path).glob("*.fsproj")):
        return "csharp"
    
    # Check source file extensions
    source_files = list(service_path.rglob("*"))
    extensions = {f.suffix for f in source_files if f.is_file()}
    
    if ".java" in extensions:
        return "java"
    if ".go" in extensions:
        return "go"
    if ".py" in extensions:
        return "python"
    if ".rs" in extensions:
        return "rust"
    if ".rb" in extensions:
        return "ruby"
    if ".js" in extensions or ".ts" in extensions:
        return "javascript"
    if ".cs" in extensions:
        return "csharp"
    
    # Enhanced Dockerfile detection
    if any(pattern in dockerfile_text for pattern in ["from node", "npm install", "yarn install"]):
        return "javascript"
    if any(pattern in dockerfile_text for pattern in ["from python", "pip install", "python3"]):
        return "python"
    if any(pattern in dockerfile_text for pattern in ["from golang", "go build", "go mod"]):
        return "go"
    if any(pattern in dockerfile_text for pattern in ["openjdk", "temurin", "gradle", "maven"]):
        return "java"
    if any(pattern in dockerfile_text for pattern in ["dotnet", "aspnet", "mcr.microsoft.com/dotnet"]):
        return "csharp"
    if any(pattern in dockerfile_text for pattern in ["from ruby", "bundle install", "gem install"]):
        return "ruby"
    if any(pattern in dockerfile_text for pattern in ["from rust", "cargo build", "cargo install"]):
        return "rust"
    
    return "unknown"

def detect_java_version(service_path):
    """Detect Java version for migration planning"""
    # Check .java-version file
    java_version_file = service_path / ".java-version"
    if java_version_file.exists():
        version = read_text(java_version_file).strip()
        return version
    
    # Check build.gradle for Java version
    gradle_files = list(service_path.glob("build.gradle*"))
    if gradle_files:
        gradle_content = read_text(gradle_files[0])
        # Look for JavaVersion.VERSION_XX or sourceCompatibility patterns
        version_match = re.search(r'JavaVersion\.VERSION_(\d+)', gradle_content)
        if version_match:
            return version_match.group(1)
        
        # Look for Kotlin DSL jvmTarget patterns
        jvm_target_match = re.search(r'jvmTarget\.set\(JvmTarget\.JVM_(\d+)\)', gradle_content)
        if jvm_target_match:
            return jvm_target_match.group(1)
        
        # Look for sourceCompatibility patterns
        compat_match = re.search(r'sourceCompatibility\s*=\s*["\']?(\d+(?:\.\d+)?)["\']?', gradle_content)
        if compat_match:
            return compat_match.group(1)
    
    # Check pom.xml for Java version
    pom_xml = service_path / "pom.xml"
    if pom_xml.exists():
        pom_content = read_text(pom_xml)
        # Look for maven.compiler.source or java.version
        source_match = re.search(r'<maven\.compiler\.source>(\d+(?:\.\d+)?)</maven\.compiler\.source>', pom_content)
        if source_match:
            return source_match.group(1)
        
        java_version_match = re.search(r'<java\.version>(\d+(?:\.\d+)?)</java\.version>', pom_content)
        if java_version_match:
            return java_version_match.group(1)
    
    return None

def detect_frameworks_and_dependencies(service_path):
    """Extract frameworks and external dependencies for migration analysis"""
    frameworks = []
    dependencies = []
    
    # Java - Maven/Gradle dependencies
    pom_xml = service_path / "pom.xml"
    if pom_xml.exists():
        pom_content = read_text(pom_xml)
        if "spring-boot" in pom_content.lower():
            frameworks.append("spring-boot")
        # Extract main dependencies
        deps = re.findall(r'<artifactId>([^<]+)</artifactId>', pom_content)
        dependencies.extend(deps[:10])  # Top 10 deps
        
    # Gradle build files
    gradle_files = list(service_path.glob("build.gradle*"))
    if gradle_files:
        gradle_content = read_text(gradle_files[0])
        content_lower = gradle_content.lower()
        if "spring-boot" in content_lower:
            frameworks.append("spring-boot")
        if "grpc" in content_lower:
            frameworks.append("grpc")
        if "protobuf" in content_lower:
            frameworks.append("protobuf")
        # Extract Gradle dependencies
        import_matches = re.findall(r'implementation\s+["\']([^"\']+)["\']', gradle_content)
        platform_matches = re.findall(r'platform\(["\']([^"\']+)["\'][^\)]*\)', gradle_content)
        dependencies.extend([dep.split(':')[1] if ':' in dep else dep for dep in import_matches[:10]])
        dependencies.extend([dep.split(':')[1] if ':' in dep else dep for dep in platform_matches[:5]])
            
    # Node.js - package.json dependencies
    package_json = service_path / "package.json"
    if package_json.exists():
        try:
            pkg_data = json.loads(read_text(package_json))
            deps = {**pkg_data.get("dependencies", {}), **pkg_data.get("devDependencies", {})}
            if "express" in deps:
                frameworks.append("express")
            if "react" in deps:
                frameworks.append("react")
            if "next" in deps:
                frameworks.append("nextjs")
            dependencies.extend(list(deps.keys())[:10])  # Top 10 deps
        except:
            pass
            
    # Go - go.mod dependencies
    go_mod = service_path / "go.mod"
    if go_mod.exists():
        content = read_text(go_mod)
        if "gin-gonic/gin" in content:
            frameworks.append("gin")
        if "gorilla/mux" in content:
            frameworks.append("gorilla-mux")
        # Extract dependencies
        deps = re.findall(r'(\S+) v[\d\.]+', content)
        dependencies.extend(deps[:10])
            
    # Python - requirements.txt
    requirements = service_path / "requirements.txt"
    if requirements.exists():
        deps = [line.strip().split("==")[0].split(">=")[0] for line in read_text(requirements).splitlines() 
                if line.strip() and not line.startswith("#")]
        dep_lower = [d.lower() for d in deps]
        if "flask" in dep_lower:
            frameworks.append("flask")
        if "django" in dep_lower:
            frameworks.append("django")
        if "fastapi" in dep_lower:
            frameworks.append("fastapi")
        dependencies.extend(deps[:10])
        
    # Ruby - Gemfile
    gemfile = service_path / "Gemfile"
    if gemfile.exists():
        content = read_text(gemfile)
        if "rails" in content.lower():
            frameworks.append("rails")
        if "sinatra" in content.lower():
            frameworks.append("sinatra")
    
    # C# - project files
    csproj_files = list(service_path.glob("*.csproj"))
    if csproj_files:
        content = read_text(csproj_files[0])
        if "Microsoft.AspNetCore" in content:
            frameworks.append("aspnet-core")
    
    return frameworks, dependencies

def detect_language(dockerfile_text):
    """Legacy function - kept for compatibility"""
    text = dockerfile_text.lower()
    if "from python" in text:
        return "python"
    if "from node" in text:
        return "node"
    if "from golang" in text or "from go" in text:
        return "go"
    if "dotnet" in text or "csharp" in text:
        return "csharp"
    if "gradle" in text or "java" in text or "openjdk" in text:
        return "java"
    if "rust" in text:
        return "rust"
    if "ruby" in text:
        return "ruby"
    return "unknown"


def is_database_host(name, dockerfile_text):
    lower = name.lower()
    text = dockerfile_text.lower()
    dbs = ["postgres", "mysql", "mongo", "redis", "valkey", "opensearch"]
    return any(k in lower for k in dbs) or any(k in text for k in dbs)


############################################################
# 3. Parse Services + DatabaseHosts
############################################################

def parse_components():
    src_root = REPO_ROOT / "src"
    if not src_root.exists():
        raise RuntimeError("src/ not found")

    services = []
    databases = []

    for entry in os.listdir(src_root):
        p = src_root / entry
        if not p.is_dir():
            continue

        df_path = p / "Dockerfile"
        df_text = read_text(df_path)
        
        # Use comprehensive language detection
        language = detect_language_comprehensive(p)
        frameworks, dependencies = detect_frameworks_and_dependencies(p)
        
        # Detect Java version for migration planning
        java_version = None
        if language == "java":
            java_version = detect_java_version(p)

        if is_database_host(entry, df_text):
            databases.append({
                "name": entry,
                "type": "DatabaseHost",
                "repository_path": str(p)
            })
        else:
            service_data = {
                "name": entry,
                "type": "Service",
                "language": language,
                "frameworks": frameworks,
                "dependencies": dependencies,
                "repository_path": str(p)
            }
            if java_version:
                service_data["java_version"] = java_version
            services.append(service_data)

    return services, databases


############################################################
# 4. Parse docker-compose for dependencies
############################################################

def load_compose_dependencies():
    compose_path = REPO_ROOT / "docker-compose.yml"
    if not compose_path.exists():
        return {}

    compose = yaml.safe_load(compose_path.read_text())
    svcs = compose.get("services", {})
    deps = {}

    for svc, body in svcs.items():
        d = body.get("depends_on", [])
        if isinstance(d, dict):
            d = list(d.keys())
        deps[svc] = d

    # remove empty dependency lists
    return {k: v for k, v in deps.items() if v}


############################################################
# 5. Test YAML dependency edges
############################################################

def extract_test_edges():
    test_root = REPO_ROOT / "test" / "tracetesting"
    if not test_root.exists():
        return []

    edges = []
    service_names = [
        d for d in os.listdir(REPO_ROOT / "src")
        if (REPO_ROOT / "src" / d).is_dir()
    ]

    for root, _, files in os.walk(test_root):
        for f in files:
            if not f.endswith((".yaml", ".yml")):
                continue
            path = Path(root) / f
            text = read_text(path)
            caller = Path(root).name

            for s in service_names:
                if s in text:
                    if caller != s:
                        edges.append((caller, s))

    # dedupe
    edges = list(set(edges))
    return edges


############################################################
# 6. Extract Postgres tables
############################################################

def extract_postgres_schema():
    pg_dir = REPO_ROOT / "src" / "postgres"
    init_sql = pg_dir / "init.sql"
    if not init_sql.exists():
        return []

    sql = read_text(init_sql)
    tables = []

    for line in sql.splitlines():
        up = line.upper()
        if "CREATE TABLE" in up:
            parts = line.replace("(", " ").split()
            try:
                tbl = parts[parts.index("TABLE") + 1]
                tables.append(tbl)
            except:
                pass

    return tables


############################################################
# 7. Extract APIs from .env
############################################################

def extract_api_nodes(env):
    apis = []

    # Pattern: PREFIX_PORT, PREFIX_ADDR, PREFIX_HOST
    pat = re.compile(r"^([A-Z0-9_]+)_(PORT|ADDR|HOST)$")
    collected = {}

    for key, val in env.items():
        m = pat.match(key)
        if not m:
            continue
        prefix = m.group(1)
        field = m.group(2).lower()

        svc_name = prefix.lower()
        if svc_name not in collected:
            collected[svc_name] = {}
        collected[svc_name][field] = val

    # Build API nodes
    for svc, meta in collected.items():
        if "port" not in meta and "addr" not in meta:
            continue

        addr = meta.get("addr")
        port = meta.get("port")
        host = meta.get("host")

        # infer protocol
        if addr and addr.startswith("http"):
            protocol = "http"
        else:
            protocol = "tcp"

        # infer host if missing
        if not host and addr:
            cleaned = addr.replace("http://", "").replace("https://", "")
            if ":" in cleaned:
                host = cleaned.split(":")[0]

        apis.append({
            "service": svc,
            "protocol": protocol,
            "port": port,
            "host": host,
            "address": addr
        })

    return apis


############################################################
# MAIN
############################################################

def main():
    # Application root node
    application = {"name": "ics_shopping_cart", "type": "Application"}

    # Parse core pieces
    services, databases = parse_components()
    env = parse_env_file()
    apis = extract_api_nodes(env)
    compose_edges = load_compose_dependencies()
    test_edges = extract_test_edges()
    postgres_tables = extract_postgres_schema()

    graph = {
        "application": application,
        "services": services,
        "databases": databases,
        "apis": apis,
        "compose_edges": compose_edges,
        "test_edges": test_edges,
        "postgres_tables": postgres_tables
    }

    print(json.dumps(graph, indent=2))


if __name__ == "__main__":
    main()
