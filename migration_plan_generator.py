"""
Migration Plan Generator

Generates step-by-step migration plans based on user queries and system analysis.
Provides actionable planning steps without executing actual migrations.

Usage: 
from migration_plan_generator import MigrationPlanGenerator
planner = MigrationPlanGenerator()
plan = planner.generate_migration_plan("How do I migrate Java services to newer version?")
"""

import os
import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

# Core dependencies (avoiding circular imports)
from neo4j import GraphDatabase
import openai


class MigrationType(Enum):
    LANGUAGE_UPGRADE = "language_upgrade"
    FRAMEWORK_MIGRATION = "framework_migration"
    SERVICE_DECOMPOSITION = "service_decomposition"
    TECHNOLOGY_MODERNIZATION = "technology_modernization"
    DEPENDENCY_UPGRADE = "dependency_upgrade"
    CONTAINERIZATION = "containerization"
    DATABASE_MIGRATION = "database_migration"
    API_VERSIONING = "api_versioning"
    SECURITY_UPGRADE = "security_upgrade"
    GENERAL_ASSESSMENT = "general_assessment"


@dataclass
class MigrationStep:
    """Individual migration step"""
    step_number: int
    title: str
    description: str
    category: str  # Planning, Analysis, Implementation, Testing, Deployment
    estimated_effort: str  # Low, Medium, High, Very High
    dependencies: List[str]
    risks: List[str]
    validation_criteria: List[str]


@dataclass
class MigrationPlan:
    """Complete migration plan"""
    title: str
    description: str
    migration_type: MigrationType
    affected_services: List[str]
    total_estimated_effort: str
    timeline: str
    prerequisites: List[str]
    steps: List[MigrationStep]
    risks_and_mitigations: Dict[str, str]
    success_metrics: List[str]


class MigrationPlanGenerator:
    """Generates comprehensive migration plans based on user queries and system analysis"""
    
    def __init__(self, neo4j_uri: str = "neo4j://127.0.0.1:7687",
                 neo4j_user: str = "neo4j", 
                 neo4j_password: str = "icsneo4j"):
        # Direct Neo4j connection to avoid circular imports
        self.neo4j_driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
        # Cache for EKG-derived data
        self._ekg_cache = {}

    def _get_all_services_from_ekg(self) -> List[str]:
        """Get all service names dynamically from EKG"""
        if 'all_services' in self._ekg_cache:
            return self._ekg_cache['all_services']
            
        with self.neo4j_driver.session() as session:
            result = session.run("""
                MATCH (s:Service)-[:PART_OF]->(:Application)
                RETURN DISTINCT s.name as name
                ORDER BY s.name
            """)
            services = [record['name'] for record in result if record['name']]
            self._ekg_cache['all_services'] = services
            return services
    
    def _get_services_by_language_from_ekg(self, language: str) -> List[str]:
        """Get services by language dynamically from EKG"""
        cache_key = f'services_{language.lower()}'
        if cache_key in self._ekg_cache:
            return self._ekg_cache[cache_key]
            
        with self.neo4j_driver.session() as session:
            result = session.run("""
                MATCH (s:Service)-[:PART_OF]->(:Application)
                WHERE toLower(s.language) = toLower($language)
                RETURN DISTINCT s.name as name
                ORDER BY s.name
            """, language=language)
            services = [record['name'] for record in result if record['name']]
            self._ekg_cache[cache_key] = services
            return services
    
    def _find_services_by_pattern_from_ekg(self, pattern: str) -> List[str]:
        """Find services matching a pattern dynamically from EKG"""
        with self.neo4j_driver.session() as session:
            result = session.run("""
                MATCH (s:Service)-[:PART_OF]->(:Application)
                WHERE toLower(s.name) CONTAINS toLower($pattern)
                   OR toLower(s.repository_path) CONTAINS toLower($pattern)
                RETURN DISTINCT s.name as name
                ORDER BY s.name
            """, pattern=pattern)
            return [record['name'] for record in result if record['name']]
        
    def generate_migration_plan(self, user_query: str) -> MigrationPlan:
        """Generate a comprehensive migration plan based on deep system analysis"""
        
        print("🔍 Starting comprehensive migration analysis...")
        
        # 1. Analyze the query to determine migration type and scope
        migration_context = self._analyze_migration_query(user_query)
        print(f"📋 Migration Context: {migration_context['migration_type'].value} - {migration_context['complexity_level']} complexity")
        
        # 2. Deep Neo4j analysis - get actual system dependencies
        neo4j_analysis = self._perform_comprehensive_neo4j_analysis(migration_context)
        print(f"🗄️ Neo4j Analysis: Found {len(neo4j_analysis.get('services', []))} services with {len(neo4j_analysis.get('dependencies', []))} dependencies")
        
        # 3. Milvus vector search for migration patterns (if available)
        milvus_insights = self._perform_milvus_analysis(user_query, migration_context)
        print(f"🔎 Milvus Analysis: Found {len(milvus_insights.get('similar_patterns', []))} similar patterns")
        
        # 4. Execute targeted Cypher queries for precise dependency mapping
        dependency_analysis = self._perform_detailed_dependency_analysis(migration_context)
        print(f"🔗 Dependency Analysis: Mapped {len(dependency_analysis.get('critical_paths', []))} critical paths")
        
        # 5. Gather comprehensive system intelligence
        system_analysis = self._gather_enhanced_system_intelligence(migration_context, neo4j_analysis, dependency_analysis)
        
        # 6. Generate EKG-driven plan using LLM with actual data
        plan_content = self._generate_plan_with_llm(user_query, migration_context, system_analysis)
        
        # 7. Create simplified plan based on EKG analysis
        simplified_plan = self._create_ekg_based_plan(plan_content, migration_context, system_analysis, neo4j_analysis)
        
        print("✅ Migration plan generation complete!")
        return simplified_plan
    
    def _analyze_migration_query(self, query: str) -> Dict[str, Any]:
        """Analyze user query to determine migration type and scope"""
        
        query_lower = query.lower()
        
        # Determine migration type
        migration_type = MigrationType.GENERAL_ASSESSMENT  # default
        
        if any(keyword in query_lower for keyword in ["java", "jdk", "version", "upgrade java"]):
            migration_type = MigrationType.LANGUAGE_UPGRADE
        elif any(keyword in query_lower for keyword in ["framework", "spring", "grpc", "react", "nextjs"]):
            migration_type = MigrationType.FRAMEWORK_MIGRATION
        elif any(keyword in query_lower for keyword in ["modernize", "modern", "technology stack"]):
            migration_type = MigrationType.TECHNOLOGY_MODERNIZATION
        elif any(keyword in query_lower for keyword in ["dependency", "dependencies", "library", "package"]):
            migration_type = MigrationType.DEPENDENCY_UPGRADE
        elif any(keyword in query_lower for keyword in ["container", "docker", "kubernetes"]):
            migration_type = MigrationType.CONTAINERIZATION
        elif any(keyword in query_lower for keyword in ["database", "postgres", "db migration"]):
            migration_type = MigrationType.DATABASE_MIGRATION
        elif any(keyword in query_lower for keyword in ["api", "endpoint", "versioning"]):
            migration_type = MigrationType.API_VERSIONING
        elif any(keyword in query_lower for keyword in ["security", "vulnerability", "secure"]):
            migration_type = MigrationType.SECURITY_UPGRADE
        
        # Determine scope - specific services or system-wide using EKG data
        affected_services = []
        
        # Get all services dynamically from EKG
        all_services = self._get_all_services_from_ekg()
        
        # Look for specific service names mentioned in query (exact matches first)
        for service in all_services:
            service_variations = [
                service,
                service.replace('-', ' '),
                service.replace('_', ' '),
                service.replace('-', ''),
                service.replace('_', '')
            ]
            
            # Check for exact service name mentions first
            for variation in service_variations:
                if f" {variation} " in f" {query_lower} " or f" {variation} service" in query_lower:
                    if service not in affected_services:
                        affected_services.append(service)
                    break
        
        # Special language-based service discovery
        if "java service" in query_lower and not affected_services:
            affected_services = self._get_services_by_language_from_ekg("java")
        elif "python service" in query_lower and not affected_services:
            affected_services = self._get_services_by_language_from_ekg("python")
        elif "javascript service" in query_lower or "js service" in query_lower and not affected_services:
            affected_services = self._get_services_by_language_from_ekg("javascript")
        elif "go service" in query_lower and not affected_services:
            affected_services = self._get_services_by_language_from_ekg("go")
        elif "rust service" in query_lower and not affected_services:
            affected_services = self._get_services_by_language_from_ekg("rust")
        elif "csharp service" in query_lower or "c# service" in query_lower and not affected_services:
            affected_services = self._get_services_by_language_from_ekg("csharp")
        
        # Pattern-based discovery for partial matches (only if no exact matches found)
        if not affected_services:
            # Exclude common words that shouldn't trigger pattern matching
            exclude_words = {"create", "generate", "migration", "plan", "service", "only", "for", "with", "all", "system", "the", "and", "or", "but", "if", "when", "from", "to", "in", "on", "at", "by", "of", "as"}
            
            for word in query_lower.split():
                if len(word) > 3 and word not in exclude_words:  # Avoid short words and common terms
                    # Only search for words that could be service names
                    if word in all_services or any(word in service for service in all_services):
                        pattern_matches = self._find_services_by_pattern_from_ekg(word)
                        affected_services.extend([s for s in pattern_matches if s not in affected_services])
                        # Stop after finding first match to avoid over-matching
                        if affected_services:
                            break
        
        return {
            "migration_type": migration_type,
            "affected_services": affected_services,
            "query_intent": self._classify_query_intent(query_lower),
            "complexity_level": self._estimate_complexity(query_lower, affected_services)
        }
    
    def _generate_dynamic_prerequisites_from_ekg(self, services: List[str], dependencies: List[Dict]) -> List[str]:
        """Generate prerequisites based on actual EKG data"""
        prerequisites = []
        
        if services:
            prerequisites.append(f"Backup strategy for {len(services)} {'service' if len(services) == 1 else 'services'}: {', '.join(services)}")
        
        if dependencies:
            external_deps = [d for d in dependencies if d.get('to_language') == 'external']
            if external_deps:
                prerequisites.append(f"External dependency validation for {len(external_deps)} integrations")
            
            prerequisites.append(f"Dependency chain testing for {len(dependencies)} relationships")
        
        # Language-specific prerequisites from EKG
        languages = set()
        with self.neo4j_driver.session() as session:
            result = session.run("""
                MATCH (s:Service) WHERE s.name IN $services
                RETURN DISTINCT s.language as language
            """, services=services)
            languages = {r['language'] for r in result if r['language']}
        
        for lang in languages:
            if lang == 'java':
                prerequisites.append("Java version compatibility testing environment")
            elif lang == 'javascript':
                prerequisites.append("Node.js and npm/yarn testing environment")
            elif lang == 'python':
                prerequisites.append("Python virtual environment and dependency management")
        
        # Always include basic requirements
        prerequisites.extend([
            "Rollback procedures and deployment pipeline",
            "Test environment with production-like data"
        ])
        
        return prerequisites
    
    def _generate_dynamic_success_metrics_from_ekg(self, services: List[str], dependencies: List[Dict]) -> List[str]:
        """Generate success metrics based on actual EKG data"""
        metrics = []
        
        if services:
            metrics.extend([
                f"All {len(services)} {'service' if len(services) == 1 else 'services'} operational post-migration",
                f"Zero downtime for critical services: {', '.join(services)}"
            ])
        
        if dependencies:
            # Extract specific dependency names for more detailed metrics
            dep_names = []
            for dep in dependencies:
                if isinstance(dep, dict):
                    dep_name = dep.get('to_name') or dep.get('target') or dep.get('name') or str(dep)
                elif isinstance(dep, str):
                    dep_name = dep
                else:
                    dep_name = str(dep)
                if dep_name and dep_name not in dep_names:
                    dep_names.append(dep_name)
            
            metrics.extend([
                f"All {len(dependencies)} dependency relationships validated",
                "Response time maintained within 5% of baseline"
            ])
            
            if dep_names:
                clean_dep_names = [name for name in dep_names if isinstance(name, str) and len(name) < 50]
                if clean_dep_names:
                    # Generate executable validation commands for dependencies
                    validation_commands = []
                    for dep in clean_dep_names[:5]:
                        validation_commands.append(f"curl -f http://{dep}/health")
                    
                    metrics.append(f"Dependencies validated with commands: {'; '.join(validation_commands)}")
        
        # Add EKG-derived performance metrics
        metrics.extend([
            "All service health checks passing",
            "Database connections and queries functional",
            "External integrations operational"
        ])
        
        return metrics
    
    def _extract_implementation_details(self, service_name: str, record: Dict) -> Dict[str, Any]:
        """Extract actual implementation details from EKG for agent execution"""
        language = record.get("language", "").lower()
        repo_path = record.get("repository_path") or record.get("path", "")
        
        details = {
            "service_name": service_name,
            "language": language,
            "repository_path": repo_path,
            "config_files": self._identify_config_files(language, repo_path),
            "build_system": self._identify_build_system(language),
            "package_manager": self._identify_package_manager(language),
            "runtime_config": self._extract_runtime_config(record),
            "environment_variables": self._extract_env_variables(service_name, record),
            "current_versions": self._extract_current_versions(record),
            "target_versions": self._generate_target_versions(language, record),
            "file_modifications": self._generate_file_modifications(service_name, language, record)
        }
        
        return details
    
    def _identify_config_files(self, language: str, repo_path: str) -> List[str]:
        """Identify configuration files that need to be modified"""
        config_files = []
        
        if language == "javascript":
            config_files = [f"{repo_path}/package.json", f"{repo_path}/package-lock.json", f"{repo_path}/.nvmrc"]
        elif language == "java":
            config_files = [f"{repo_path}/pom.xml", f"{repo_path}/build.gradle", f"{repo_path}/gradle.properties"]
        elif language == "python":
            config_files = [f"{repo_path}/requirements.txt", f"{repo_path}/pyproject.toml", f"{repo_path}/setup.py"]
        elif language == "go":
            config_files = [f"{repo_path}/go.mod", f"{repo_path}/go.sum"]
        elif language == "rust":
            config_files = [f"{repo_path}/Cargo.toml", f"{repo_path}/Cargo.lock"]
        elif language == "csharp":
            config_files = [f"{repo_path}/*.csproj", f"{repo_path}/*.sln", f"{repo_path}/Directory.Build.props"]
        
        # Common files for all services
        config_files.extend([f"{repo_path}/Dockerfile", f"{repo_path}/docker-compose.yml"])
        
        return config_files
    
    def _identify_build_system(self, language: str) -> Dict[str, str]:
        """Identify build system and commands"""
        build_systems = {
            "javascript": {"system": "npm", "install": "npm install", "build": "npm run build", "test": "npm test"},
            "java": {"system": "maven/gradle", "install": "mvn install", "build": "mvn package", "test": "mvn test"},
            "python": {"system": "pip", "install": "pip install -r requirements.txt", "build": "python setup.py build", "test": "pytest"},
            "go": {"system": "go", "install": "go mod download", "build": "go build", "test": "go test"},
            "rust": {"system": "cargo", "install": "cargo fetch", "build": "cargo build", "test": "cargo test"},
            "csharp": {"system": "dotnet", "install": "dotnet restore", "build": "dotnet build", "test": "dotnet test"}
        }
        return build_systems.get(language, {"system": "unknown", "install": "", "build": "", "test": ""})
    
    def _identify_package_manager(self, language: str) -> str:
        """Identify package manager for dependency updates"""
        managers = {
            "javascript": "npm",
            "java": "maven",
            "python": "pip", 
            "go": "go mod",
            "rust": "cargo",
            "csharp": "nuget"
        }
        return managers.get(language, "unknown")
    
    def _extract_runtime_config(self, record: Dict) -> Dict[str, Any]:
        """Extract runtime configuration from EKG data"""
        exposed_apis = record.get("exposed_apis", [])
        
        config = {
            "ports": [api.get('port') for api in exposed_apis if api.get('port')],
            "protocols": [api.get('protocol') for api in exposed_apis if api.get('protocol')],
            "endpoints": [api.get('address') for api in exposed_apis if api.get('address')]
        }
        
        return config
    
    def _extract_env_variables(self, service_name: str, record: Dict) -> List[str]:
        """Extract environment variables that may need updates"""
        # Generate common environment variables based on service patterns
        env_vars = [
            f"{service_name.upper()}_HOST",
            f"{service_name.upper()}_PORT", 
            f"{service_name.upper()}_VERSION"
        ]
        
        # Add dependency-based environment variables
        for dep in record.get("runtime_dependencies", []):
            env_vars.extend([
                f"{dep.upper()}_URL",
                f"{dep.upper()}_HOST"
            ])
            
        return env_vars
    
    def _generate_migration_commands(self, service_name: str, record: Dict) -> Dict[str, List[str]]:
        """Generate executable migration commands for the service"""
        language = record.get("language", "").lower()
        repo_path = record.get("path", "")
        build_system = self._identify_build_system(language)
        
        commands = {
            "pre_migration": [
                f"cd {repo_path}",
                f"git checkout -b migration-{service_name}-$(date +%Y%m%d)",
                "git status",
                f"docker build -t {service_name}:backup ."
            ],
            "dependency_update": self._generate_dependency_update_commands(language, repo_path),
            "build_and_test": [
                build_system.get("install", ""),
                build_system.get("build", ""),
                build_system.get("test", "")
            ],
            "deployment": [
                f"docker build -t {service_name}:latest .",
                f"docker tag {service_name}:latest {service_name}:migration-$(date +%Y%m%d)",
                "docker-compose up -d --no-deps {service_name}"
            ],
            "rollback": [
                f"docker stop {service_name}",
                f"docker run -d --name {service_name} {service_name}:backup",
                "git checkout main",
                f"git branch -D migration-{service_name}-*"
            ]
        }
        
        # Remove empty commands
        return {k: [cmd for cmd in v if cmd.strip()] for k, v in commands.items()}
    
    def _generate_dependency_update_commands(self, language: str, repo_path: str) -> List[str]:
        """Generate language-specific dependency update commands"""
        commands = []
        
        if language == "javascript":
            commands = [
                "npm audit",
                "npm update",
                "npm audit fix",
                "npm ci"
            ]
        elif language == "java":
            commands = [
                "mvn versions:display-dependency-updates",
                "mvn versions:use-latest-versions",
                "mvn clean compile"
            ]
        elif language == "python":
            commands = [
                "pip list --outdated",
                "pip install --upgrade -r requirements.txt",
                "pip freeze > requirements.txt"
            ]
        elif language == "go":
            commands = [
                "go list -u -m all",
                "go get -u ./...",
                "go mod tidy"
            ]
        elif language == "rust":
            commands = [
                "cargo update",
                "cargo check"
            ]
        elif language == "csharp":
            commands = [
                "dotnet list package --outdated",
                "dotnet add package --version latest",
                "dotnet restore"
            ]
            
        return commands
    
    def _generate_validation_scripts(self, service_name: str, record: Dict) -> Dict[str, List[str]]:
        """Generate validation scripts for migration verification"""
        exposed_apis = record.get("exposed_apis", [])
        
        scripts = {
            "health_checks": [],
            "integration_tests": [],
            "performance_tests": []
        }
        
        # Generate health check scripts based on exposed APIs
        for api in exposed_apis:
            port = api.get('port')
            protocol = api.get('protocol', 'http')
            if port:
                scripts["health_checks"].extend([
                    f"curl -f {protocol}://localhost:{port}/health || echo 'Health check failed for {service_name}:{port}'",
                    f"nc -zv localhost {port} || echo 'Port {port} not accessible for {service_name}'"
                ])
        
        # Generate integration tests for dependencies
        for dep in record.get("runtime_dependencies", []):
            scripts["integration_tests"].append(
                f"curl -f http://{dep}/health && echo 'Dependency {dep} is healthy' || echo 'Dependency {dep} failed'"
            )
        
        # Generate performance baseline tests
        if exposed_apis:
            main_port = exposed_apis[0].get('port')
            if main_port:
                scripts["performance_tests"].extend([
                    f"ab -n 100 -c 10 http://localhost:{main_port}/ > /tmp/{service_name}_perf_test.log",
                    f"echo 'Performance baseline saved for {service_name}'"
                ])
        
        return scripts
    
    def _extract_current_versions(self, record: Dict) -> Dict[str, str]:
        """Extract current versions from EKG data with intelligent defaults"""
        current_versions = {}
        language = record.get("language", "").lower()
        
        # Extract Java version if available
        java_version = record.get("java_version")
        if java_version:
            current_versions["java"] = java_version
        elif language == "java":
            current_versions["java"] = "17.0.0"  # Common enterprise Java version
        
        # Extract dependency versions from EKG
        code_dependencies = record.get("code_dependencies", [])
        if code_dependencies:
            for dep in code_dependencies:
                if isinstance(dep, str):
                    # Try to parse version from dependency string (e.g., "express@4.17.1")
                    if "@" in dep:
                        name, version = dep.split("@", 1)
                        current_versions[name] = version
                    else:
                        # Provide realistic current versions based on common usage
                        current_versions[dep] = self._get_common_current_version(dep, language)
        
        # Extract framework versions
        frameworks = record.get("frameworks", [])
        for framework in frameworks:
            if isinstance(framework, str):
                current_versions[framework] = self._get_common_current_version(framework, language)
        
        # Add language runtime versions with realistic defaults
        if language == "javascript":
            if "node" not in current_versions:
                current_versions["node"] = "16.20.0"  # Common LTS version
            if "express" not in current_versions and any("express" in dep for dep in code_dependencies):
                current_versions["express"] = "4.17.1"
        elif language == "python":
            if "python" not in current_versions:
                current_versions["python"] = "3.9.16"  # Common production version
        elif language == "go":
            if "go" not in current_versions:
                current_versions["go"] = "1.19.5"  # Common stable version
        elif language == "rust":
            if "rust" not in current_versions:
                current_versions["rust"] = "1.65.0"  # Common stable version
        elif language == "csharp":
            if "dotnet" not in current_versions:
                current_versions["dotnet"] = "6.0"  # Common enterprise version
        
        return current_versions
    
    def _get_common_current_version(self, dependency: str, language: str) -> str:
        """Get common current versions for dependencies based on language"""
        # Common current versions by language and dependency
        version_map = {
            "javascript": {
                "express": "4.17.1",
                "grpcio": "1.24.4",
                "grpc": "1.24.4",
                "opentelemetry": "1.8.0",
                "sinatra": "2.2.0"
            },
            "java": {
                "spring-boot": "2.7.0",
                "maven": "3.8.6",
                "grpc-java": "1.45.1",
                "opentelemetry": "1.15.0"
            },
            "python": {
                "flask": "2.0.3",
                "fastapi": "0.75.2",
                "grpcio": "1.44.0",
                "opentelemetry": "1.11.1",
                "psycopg2-binary": "2.9.3",
                "openai": "0.27.0"
            },
            "go": {
                "grpc": "1.45.2",
                "opentelemetry": "1.7.0"
            },
            "csharp": {
                "aspnetcore": "6.0",
                "grpc": "2.44.0"
            },
            "ruby": {
                "sinatra": "2.2.0",
                "grpc": "1.44.0"
            }
        }
        
        # Check language-specific versions first
        if language in version_map and dependency in version_map[language]:
            return version_map[language][dependency]
        
        # Check common dependencies across languages
        for lang_versions in version_map.values():
            if dependency in lang_versions:
                return lang_versions[dependency]
        
        # Default fallback
        return "current"
    
    def _generate_target_versions(self, language: str, record: Dict) -> Dict[str, str]:
        """Generate target versions for migration based on actual dependencies in EKG"""
        target_versions = {}
        code_dependencies = record.get("code_dependencies", [])
        frameworks = record.get("frameworks", [])
        
        # Language runtime target versions
        if language == "javascript":
            target_versions["node"] = "20.10.0"
        elif language == "java":
            target_versions["java"] = "21.0.1"
        elif language == "python":
            target_versions["python"] = "3.11.6"
        elif language == "go":
            target_versions["go"] = "1.21.3"
        elif language == "rust":
            target_versions["rust"] = "1.73.0"
        elif language == "csharp":
            target_versions["dotnet"] = "8.0"
        
        # Only add target versions for dependencies that actually exist in EKG data
        all_deps = set(code_dependencies + frameworks)
        
        if language == "javascript":
            if any("express" in dep for dep in all_deps):
                target_versions["express"] = "4.18.2"
            if any("grpc" in dep.lower() for dep in all_deps):
                target_versions["grpc"] = "1.25.0"
        elif language == "java":
            if any("spring" in dep.lower() for dep in all_deps):
                target_versions["spring-boot"] = "3.1.5"
            if any("maven" in dep.lower() for dep in all_deps):
                target_versions["maven"] = "3.9.4"
            if any("grpc" in dep.lower() for dep in all_deps):
                target_versions["grpc-java"] = "1.55.1"
        elif language == "python":
            if any("flask" in dep.lower() for dep in all_deps):
                target_versions["flask"] = "2.3.3"
            if any("fastapi" in dep.lower() for dep in all_deps):
                target_versions["fastapi"] = "0.104.1"
            if any("grpc" in dep.lower() for dep in all_deps):
                target_versions["grpcio"] = "1.58.0"
        elif language == "csharp":
            if any("aspnet" in dep.lower() for dep in all_deps):
                target_versions["aspnetcore"] = "8.0"
        
        return target_versions
    
    def _generate_file_modifications(self, service_name: str, language: str, record: Dict) -> Dict[str, Dict]:
        """Generate specific file content modifications for agent execution"""
        repo_path = record.get("repository_path") or record.get("path", "")
        current_versions = self._extract_current_versions(record)
        target_versions = self._generate_target_versions(language, record)
        exposed_apis = record.get("exposed_apis", [])
        
        modifications = {}
        
        if language == "javascript":
            # Package.json modifications
            modifications[f"{repo_path}/package.json"] = {
                "file_type": "json",
                "modifications": [
                    {
                        "action": "update_dependency",
                        "dependency": "express",
                        "from_version": current_versions.get("express", "4.17.1"),
                        "to_version": target_versions.get("express", "4.18.2")
                    },
                    {
                        "action": "update_engines",
                        "field": "node",
                        "from_version": ">=16.0.0",
                        "to_version": ">=20.0.0"
                    }
                ]
            }
            
            # Dockerfile modifications
            modifications[f"{repo_path}/Dockerfile"] = {
                "file_type": "dockerfile",
                "modifications": [
                    {
                        "action": "update_base_image",
                        "from_line": "FROM node:16-alpine",
                        "to_line": "FROM node:20-alpine"
                    }
                ]
            }
            
        elif language == "java":
            # Maven pom.xml modifications
            modifications[f"{repo_path}/pom.xml"] = {
                "file_type": "xml",
                "modifications": [
                    {
                        "action": "update_property",
                        "property": "maven.compiler.source",
                        "from_value": "11",
                        "to_value": "21"
                    },
                    {
                        "action": "update_property", 
                        "property": "maven.compiler.target",
                        "from_value": "11", 
                        "to_value": "21"
                    }
                ]
            }
            
        elif language == "python":
            # Requirements.txt modifications
            modifications[f"{repo_path}/requirements.txt"] = {
                "file_type": "text",
                "modifications": [
                    {
                        "action": "update_requirement",
                        "package": "flask",
                        "from_version": "2.0.0",
                        "to_version": "2.3.3"
                    }
                ]
            }
            
            # Dockerfile modifications
            modifications[f"{repo_path}/Dockerfile"] = {
                "file_type": "dockerfile", 
                "modifications": [
                    {
                        "action": "update_base_image",
                        "from_line": "FROM python:3.9-slim",
                        "to_line": "FROM python:3.11-slim"
                    }
                ]
            }
        
        # Environment configuration modifications
        if exposed_apis:
            main_port = exposed_apis[0].get('port')
            if main_port:
                modifications[f"{repo_path}/docker-compose.yml"] = {
                    "file_type": "yaml",
                    "modifications": [
                        {
                            "action": "verify_port",
                            "service": service_name,
                            "current_port": main_port,
                            "ensure_exposed": True
                        }
                    ]
                }
        
        return modifications
    
    def _classify_query_intent(self, query: str) -> str:
        """Classify the user's intent"""
        if any(keyword in query for keyword in ["plan", "how to", "steps", "planning"]):
            return "planning"
        elif any(keyword in query for keyword in ["assess", "analysis", "evaluate"]):
            return "assessment"
        elif any(keyword in query for keyword in ["risk", "impact", "affected"]):
            return "risk_analysis"
        else:
            return "general_inquiry"
    
    def _estimate_complexity(self, query: str, affected_services: List[str]) -> str:
        """Estimate migration complexity"""
        if len(affected_services) > 10:
            return "very_high"
        elif len(affected_services) > 5:
            return "high"
        elif len(affected_services) > 0:
            return "medium"
        elif any(keyword in query for keyword in ["system", "all", "entire"]):
            return "very_high"
        else:
            return "low"
    
    def _gather_system_intelligence(self, migration_context: Dict[str, Any]) -> Dict[str, Any]:
        """Gather relevant system data for migration planning"""
        
        # Get service analysis directly from Neo4j
        service_analysis = self._analyze_services_directly(migration_context["affected_services"])
        
        # Gather technology stack information
        tech_inventory = self._get_technology_inventory()
        
        # Assess dependencies and interconnections
        dependency_map = self._analyze_service_dependencies(migration_context["affected_services"])
        
        return {
            "service_analysis": service_analysis,
            "technology_inventory": tech_inventory,
            "dependency_mapping": dependency_map,
            "risk_factors": self._identify_risk_factors(service_analysis, migration_context)
        }
    
    def _analyze_services_directly(self, target_services: List[str]) -> Dict[str, Any]:
        """Direct Neo4j analysis of services with code-level implementation details"""
        
        if target_services:
            cypher = """
            MATCH (s:Service) WHERE s.name IN $services
            OPTIONAL MATCH (s)-[:DEPENDS_ON]->(dep)
            OPTIONAL MATCH (caller:Service)-[:CALLS_SERVICE]->(s)
            OPTIONAL MATCH (s)-[:EXPOSES_API]->(api:API)
            RETURN s.name as service, s.language as language, s.repository_path as path,
                   s.dependencies as code_dependencies, s.frameworks as frameworks,
                   s.java_version as java_version,
                   collect(DISTINCT dep.name) as runtime_dependencies,
                   collect(DISTINCT caller.name) as callers,
                   collect(DISTINCT {port: api.port, protocol: api.protocol, address: api.address}) as exposed_apis
            """
            params = {"services": target_services}
        else:
            cypher = """
            MATCH (s:Service)-[:PART_OF]->(a:Application)
            OPTIONAL MATCH (s)-[:DEPENDS_ON]->(dep)
            OPTIONAL MATCH (caller:Service)-[:CALLS_SERVICE]->(s)
            OPTIONAL MATCH (s)-[:EXPOSES_API]->(api:API)
            RETURN s.name as service, s.language as language, s.repository_path as path,
                   s.dependencies as code_dependencies, s.frameworks as frameworks,
                   s.java_version as java_version,
                   collect(DISTINCT dep.name) as runtime_dependencies,
                   collect(DISTINCT caller.name) as callers,
                   collect(DISTINCT {port: api.port, protocol: api.protocol, address: api.address}) as exposed_apis
            """
            params = {}
        
        with self.neo4j_driver.session() as session:
            result = session.run(cypher, params)
            services_data = []
            
            for record in result:
                # Extract actual implementation details for agent execution
                service_name = record["service"]
                service_analysis = {
                    "service": service_name,
                    "language": record["language"], 
                    "repository_path": record["path"],
                    "code_dependencies": record.get("code_dependencies", []),
                    "frameworks": record.get("frameworks", []),
                    "java_version": record.get("java_version"),
                    "runtime_dependencies": [d for d in record["runtime_dependencies"] if d],
                    "callers": [c for c in record["callers"] if c],
                    "exposed_apis": [api for api in record["exposed_apis"] if api.get('port')],
                    "implementation_details": self._extract_implementation_details(service_name, record),
                    "migration_commands": self._generate_migration_commands(service_name, record),
                    "validation_scripts": self._generate_validation_scripts(service_name, record),
                    "complexity_score": len([d for d in record.get("runtime_dependencies", []) if d]) * 2 + len([c for c in record.get("callers", []) if c]) * 3,
                    "migration_risk": "HIGH" if (len([d for d in record.get("runtime_dependencies", []) if d]) > 3 or len([c for c in record.get("callers", []) if c]) > 5) else "MEDIUM" if (len([d for d in record.get("runtime_dependencies", []) if d]) > 1) else "LOW"
                }
                services_data.append(service_analysis)
            
            return {
                "services": services_data,
                "total_services": len(services_data),
                "high_risk_services": [s for s in services_data if s["migration_risk"] == "HIGH"]
            }
    
    def _get_technology_inventory(self) -> Dict[str, Any]:
        """Get comprehensive technology inventory"""
        
        # Use Neo4j to get technology distribution
        cypher = """
        MATCH (s:Service)-[:PART_OF]->(a:Application)
        RETURN s.language as language, s.frameworks as frameworks, 
               count(s) as service_count
        ORDER BY service_count DESC
        """
        
        with self.neo4j_driver.session() as session:
            result = session.run(cypher)
            tech_data = []
            for record in result:
                tech_data.append({
                    "language": record["language"],
                    "frameworks": record["frameworks"],
                    "service_count": record["service_count"]
                })
        
        return {
            "language_distribution": tech_data,
            "total_services": sum(item["service_count"] for item in tech_data)
        }
    
    def _analyze_service_dependencies(self, target_services: List[str]) -> Dict[str, Any]:
        """Analyze service dependencies for migration planning"""
        
        if target_services:
            # Specific services dependency analysis
            cypher = """
            MATCH (s:Service) WHERE s.name IN $services
            OPTIONAL MATCH (s)-[:DEPENDS_ON]->(dep)
            OPTIONAL MATCH (caller)-[:CALLS_SERVICE]->(s)
            RETURN s.name as service,
                   collect(DISTINCT dep.name) as dependencies,
                   collect(DISTINCT caller.name) as callers
            """
            params = {"services": target_services}
        else:
            # System-wide dependency analysis
            cypher = """
            MATCH (s:Service)-[:PART_OF]->(a:Application)
            OPTIONAL MATCH (s)-[:DEPENDS_ON]->(dep)
            OPTIONAL MATCH (caller)-[:CALLS_SERVICE]->(s)
            RETURN s.name as service,
                   collect(DISTINCT dep.name) as dependencies,
                   collect(DISTINCT caller.name) as callers
            ORDER BY size(collect(DISTINCT caller.name)) DESC
            """
            params = {}
        
        with self.neo4j_driver.session() as session:
            result = session.run(cypher, params)
            dependency_data = {}
            for record in result:
                service_name = record["service"]
                dependency_data[service_name] = {
                    "dependencies": [d for d in record["dependencies"] if d],
                    "callers": [c for c in record["callers"] if c],
                    "dependency_count": len([d for d in record["dependencies"] if d]),
                    "caller_count": len([c for c in record["callers"] if c])
                }
        
        return dependency_data
    
    def _identify_risk_factors(self, service_analysis: Dict[str, Any], migration_context: Dict[str, Any]) -> List[str]:
        """Identify risk factors based ONLY on EKG data - no assumptions"""
        
        risks = []
        
        # Get actual services and dependencies from EKG analysis
        services = service_analysis.get('services', [])
        dependencies = service_analysis.get('dependencies', [])
        
        # Risk based on actual dependency count from EKG
        for service in services:
            dep_count = service.get('dependency_count', 0)
            caller_count = service.get('caller_count', 0)
            
            if dep_count > 5:
                risks.append(f"Service {service['name']} has {dep_count} dependencies requiring careful testing")
            
            if caller_count > 3:
                risks.append(f"Service {service['name']} has {caller_count} callers - high impact if changed")
        
        # Risk based on actual service interconnections from EKG
        if len(dependencies) > 0:
            external_deps = [d for d in dependencies if d.get('to_language') == 'external']
            if external_deps:
                risks.append(f"External dependencies detected: {len(external_deps)} external integrations")
        
        # Language-specific risks based on EKG data
        languages = set(s.get('language', 'unknown') for s in services)
        for lang in languages:
            if lang == 'java':
                java_services = [s['name'] for s in services if s.get('language') == 'java']
                risks.append(f"Java version compatibility for services: {', '.join(java_services)}")
        
        return risks
    
    def _generate_plan_with_llm(self, user_query: str, migration_context: Dict[str, Any], system_analysis: Dict[str, Any]) -> str:
        """Generate migration plan content using LLM"""
        
        # Build context based ONLY on EKG analysis data
        services = system_analysis.get('services', [])
        dependencies = system_analysis.get('dependencies', [])
        
        context = f"""
You are an expert migration consultant. Generate a migration plan based ONLY on the provided EKG data.

## ACTUAL EKG DATA ANALYSIS:
- Services to migrate: {len(services)} services
- Service names: {[s['name'] for s in services]}
- Service languages: {[f"{s['name']}: {s.get('language', 'unknown')}" for s in services]}
- Total dependencies: {len(dependencies)} relationships
- Migration type: {migration_context['migration_type'].value}

## ACTUAL SERVICE DETAILS FROM EKG:

"""
        
        # Add detailed service information from EKG
        for service in services:
            context += f"""
### Service: {service['name']}
- Language: {service.get('language', 'unknown')}
- Dependencies: {service.get('runtime_deps', [])}
- Called by: {service.get('called_by', [])}
- Repository: {service.get('repository_path', 'N/A')}"""
        
        context += f"""

## ACTUAL DEPENDENCIES FROM EKG:
"""
        for dep in dependencies:
            context += f"- {dep['from_service']} {dep['relationship_type']} {dep['to_service']}\n"
        
        context += f"""

## Risk Factors (from EKG analysis):
{chr(10).join(system_analysis.get('risk_factors', []))}

CRITICAL: Base the migration plan ONLY on the above EKG data. Do not make assumptions about:
- Service versions not mentioned in EKG
- Dependencies not shown in EKG data  
- Generic migration steps - use actual service details
- Hardcoded timelines - calculate based on dependency count

Generate specific migration steps for the actual services and dependencies shown above.
"""

        try:
            from openai import OpenAI
            client = OpenAI()
            
            response = client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": context},
                    {"role": "user", "content": f"Create detailed migration plan for: {user_query}"}
                ],
                max_tokens=2000,
                temperature=0.1
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"LLM API error: {e}")
            return f"""
# Migration Plan - {migration_context['migration_type'].value.replace('_', ' ').title()}

## Executive Summary
Execute {migration_context['migration_type'].value.replace('_', ' ')} with minimal system disruption.

## Prerequisites  
- System backup and rollback procedures
- Test environment setup
- Monitoring and alerting configuration

## Migration Steps
1. **Assessment** - Analyze current state and requirements
2. **Planning** - Develop detailed migration strategy
3. **Testing** - Validate changes in test environment  
4. **Implementation** - Execute migration in stages
5. **Validation** - Verify successful completion

## Timeline
Estimated based on complexity: {migration_context['complexity_level']} complexity migration.
"""
    
    def _structure_migration_plan(self, plan_content: str, migration_context: Dict[str, Any], system_analysis: Dict[str, Any]) -> MigrationPlan:
        """Structure the raw plan content into MigrationPlan object"""
        
        # Extract structured data from plan content (simplified version)
        # In a full implementation, you'd parse the LLM response more thoroughly
        
        steps = [
            MigrationStep(
                step_number=1,
                title="Migration Assessment",
                description="Analyze current system state and define migration scope",
                category="Planning",
                estimated_effort="Medium",
                dependencies=[],
                risks=["Incomplete assessment"],
                validation_criteria=["Complete inventory", "Defined scope"]
            ),
            MigrationStep(
                step_number=2,
                title="Impact Analysis",
                description="Identify dependencies and potential impacts",
                category="Analysis", 
                estimated_effort="High",
                dependencies=["Migration Assessment"],
                risks=["Missing dependencies"],
                validation_criteria=["Dependency map complete", "Impact scenarios documented"]
            )
        ]
        
        return MigrationPlan(
            title=f"Migration Plan - {migration_context['migration_type'].value.replace('_', ' ').title()}",
            description=f"Comprehensive migration plan based on user query",
            migration_type=migration_context['migration_type'],
            affected_services=migration_context.get('affected_services', []),
            total_estimated_effort=migration_context['complexity_level'],
            timeline="8-16 weeks (varies by complexity)",
            prerequisites=[
                "System backups and rollback procedures",
                "Test environment setup",
                "Monitoring and alerting configuration"
            ],
            steps=steps,
            risks_and_mitigations={
                "Service downtime": "Use blue-green deployment",
                "Data loss": "Comprehensive backup strategy",
                "Integration failures": "Staged rollout with rollback"
            },
            success_metrics=[
                "Zero data loss",
                "Minimal downtime (<1% SLA impact)", 
                "All services operational post-migration",
                "Performance baseline maintained"
            ]
        )
    
    def _perform_comprehensive_neo4j_analysis(self, migration_context: Dict[str, Any]) -> Dict[str, Any]:
        """Perform comprehensive Neo4j analysis to understand real system architecture"""
        try:
            with self.neo4j_driver.session() as session:
                analysis_results = {}
                
                # Get services - focus ONLY on requested services from EKG
                affected_services = migration_context.get('affected_services', [])
                if affected_services:
                    # Get ONLY the specific services mentioned - no assumptions
                    services_query = """
                    MATCH (s:Service)-[:PART_OF]->(a:Application)
                    WHERE s.name IN $service_names
                    OPTIONAL MATCH (s)-[:DEPENDS_ON]->(dep)
                    OPTIONAL MATCH (s)-[:CALLS_SERVICE]->(called)
                    OPTIONAL MATCH (caller)-[:CALLS_SERVICE]->(s)
                    WITH s, a, collect(DISTINCT dep.name) as runtime_deps, 
                         collect(DISTINCT called.name) as calls_out,
                         collect(DISTINCT caller.name) as called_by
                    RETURN DISTINCT s.name as name, s.language as language, 
                           s.frameworks as frameworks, s.repository_path as repository_path, 
                           s.dependencies as dependencies, s.java_version as java_version, 
                           a.name as application, runtime_deps, calls_out, called_by,
                           size(runtime_deps) as dependency_count,
                           size(called_by) as caller_count
                    ORDER BY s.name
                    """
                    services_result = session.run(services_query, service_names=affected_services)
                else:
                    # Get all services - remove duplicates 
                    services_query = """
                    MATCH (s:Service)-[:PART_OF]->(a:Application)
                    RETURN DISTINCT s.name as name, s.language as language, s.frameworks as frameworks,
                           s.repository_path as repository_path, s.dependencies as dependencies,
                           s.java_version as java_version, a.name as application
                    ORDER BY s.name
                    """
                    services_result = session.run(services_query)
                # Use enhanced service analysis for implementation details
                enhanced_services = self._analyze_services_directly(affected_services)
                analysis_results['services'] = enhanced_services.get('services', [])
                
                # Get ONLY dependencies for the specific services from EKG
                if affected_services:
                    # Get dependencies involving ONLY the specific services
                    deps_query = """
                    MATCH (s1:Service)-[r]->(s2)
                    WHERE type(r) IN ['DEPENDS_ON', 'CALLS_SERVICE']
                      AND s1.name IN $service_names
                    RETURN DISTINCT s1.name as from_service, type(r) as relationship_type,
                           s2.name as to_service, 
                           CASE WHEN s2:Service THEN s2.language ELSE 'external' END as to_language
                    ORDER BY s1.name, s2.name
                    """
                    deps_result = session.run(deps_query, service_names=affected_services)
                else:
                    # Get all dependencies - remove duplicates
                    deps_query = """
                    MATCH (s1:Service)-[r]->(s2:Service)
                    WHERE type(r) IN ['DEPENDS_ON', 'CALLS_SERVICE']
                    RETURN DISTINCT s1.name as from_service, type(r) as relationship_type,
                           s2.name as to_service, s1.language as from_language,
                           s2.language as to_language
                    ORDER BY s1.name, s2.name
                    """
                    deps_result = session.run(deps_query)
                analysis_results['dependencies'] = [dict(record) for record in deps_result]
                
                # Get technology stack distribution
                tech_query = """
                MATCH (s:Service)-[:PART_OF]->(a:Application)
                RETURN s.language as language, count(*) as service_count,
                       collect(s.name) as services
                ORDER BY service_count DESC
                """
                tech_result = session.run(tech_query)
                analysis_results['technology_stack'] = [dict(record) for record in tech_result]
                
                # Get database usage patterns
                db_query = """
                MATCH (s:Service)-[:USES_DATABASE]->(d:DatabaseHost)
                RETURN s.name as service, d.name as database, 
                       labels(d) as db_labels, d.host as db_host
                """
                db_result = session.run(db_query)
                analysis_results['database_usage'] = [dict(record) for record in db_result]
                
                return analysis_results
                
        except Exception as e:
            print(f"Warning: Neo4j analysis failed: {e}")
            return {'services': [], 'dependencies': [], 'technology_stack': [], 'database_usage': []}
    
    def _perform_milvus_analysis(self, query: str, migration_context: Dict[str, Any]) -> Dict[str, Any]:
        """Use Milvus vector search to find similar migration patterns"""
        try:
            # Try to import and use vector store if available
            try:
                from ekg_vector_store import EKGVectorStore
                vector_store = EKGVectorStore()
                
                # Search for migration-related patterns
                search_queries = [
                    f"migration {migration_context['migration_type'].value}",
                    f"upgrade {' '.join(migration_context.get('affected_services', []))}",
                    f"dependency management {query}",
                    "best practices migration planning"
                ]
                
                insights = {
                    'similar_patterns': [],
                    'best_practices': [],
                    'migration_examples': []
                }
                
                for search_query in search_queries:
                    try:
                        results = vector_store.search_similar_queries(
                            query=search_query,
                            top_k=3
                        )
                        
                        for result in results:
                            natural_query = result.get('natural_query', '')
                            cypher_query = result.get('cypher_query', '')
                            content = f"{natural_query} -> {cypher_query}"
                            score = result.get('distance', 1.0)
                            
                            if score < 0.3:  # Low distance means high similarity
                                if 'migration' in natural_query.lower():
                                    insights['similar_patterns'].append({
                                        'content': content[:300],
                                        'score': score,
                                        'query': search_query
                                    })
                                
                                if any(term in natural_query.lower() for term in ['best practice', 'recommend', 'should']):
                                    insights['best_practices'].append({
                                        'content': content[:200],
                                        'score': score
                                    })
                                    
                                if any(term in natural_query.lower() for term in ['example', 'case study', 'experience']):
                                    insights['migration_examples'].append({
                                        'content': content[:250],
                                        'score': score
                                    })
                    
                    except Exception as search_error:
                        print(f"Milvus search failed for '{search_query}': {search_error}")
                        continue
                
                # Note: EKGVectorStore uses Milvus connections which don't need explicit closing
                return insights
                
            except ImportError:
                print("Milvus vector store not available - using fallback analysis")
                return self._generate_fallback_insights(migration_context)
                
        except Exception as e:
            print(f"Warning: Milvus analysis failed: {e}")
            return {'similar_patterns': [], 'best_practices': [], 'migration_examples': []}
    
    def _perform_detailed_dependency_analysis(self, migration_context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute targeted Cypher queries for detailed dependency analysis"""
        try:
            with self.neo4j_driver.session() as session:
                dependency_data = {}
                
                # Get affected services for filtering
                affected_services = migration_context.get('affected_services', [])
                
                # Get critical dependency paths - only for specified services
                if affected_services:
                    service_filter = "AND (s1.name IN $services OR s2.name IN $services)"
                    critical_paths_query = f"""
                    MATCH path = (s1:Service)-[:DEPENDS_ON|CALLS_SERVICE*1..4]->(s2:Service)
                    WHERE s1.name <> s2.name {service_filter}
                    WITH s1, s2, path, length(path) as depth
                    ORDER BY depth DESC
                    RETURN s1.name as start_service, s1.language as start_language,
                           s2.name as end_service, s2.language as end_language,
                           depth as dependency_depth,
                           [n in nodes(path) | n.name] as dependency_chain
                    LIMIT 20
                    """
                    critical_result = session.run(critical_paths_query, services=affected_services)
                else:
                    # Fallback to all services if none specified
                    critical_paths_query = """
                    MATCH path = (s1:Service)-[:DEPENDS_ON|CALLS_SERVICE*1..4]->(s2:Service)
                    WHERE s1.name <> s2.name
                    WITH s1, s2, path, length(path) as depth
                    ORDER BY depth DESC
                    RETURN s1.name as start_service, s1.language as start_language,
                           s2.name as end_service, s2.language as end_language,
                           depth as dependency_depth,
                           [n in nodes(path) | n.name] as dependency_chain
                    LIMIT 20
                    """
                    critical_result = session.run(critical_paths_query)
                dependency_data['critical_paths'] = [dict(record) for record in critical_result]
                
                # Identify potential circular dependencies - only for specified services
                if affected_services:
                    circular_deps_query = """
                    MATCH (s1:Service)-[:DEPENDS_ON|CALLS_SERVICE*2..5]->(s1)
                    WHERE s1.name IN $services
                    RETURN s1.name as service, s1.language as language,
                           'circular_dependency' as issue_type
                    """
                    circular_result = session.run(circular_deps_query, services=affected_services)
                else:
                    circular_deps_query = """
                    MATCH (s1:Service)-[:DEPENDS_ON|CALLS_SERVICE*2..5]->(s1)
                    RETURN s1.name as service, s1.language as language,
                           'circular_dependency' as issue_type
                    """
                    circular_result = session.run(circular_deps_query)
                dependency_data['circular_dependencies'] = [dict(record) for record in circular_result]
                
                # Find high-impact services (most connected) - only for specified services
                if affected_services:
                    high_impact_query = """
                    MATCH (s:Service)-[:PART_OF]->(a:Application)
                    WHERE s.name IN $services
                    OPTIONAL MATCH (s)-[:DEPENDS_ON|CALLS_SERVICE]->(dep:Service)
                    OPTIONAL MATCH (caller:Service)-[:DEPENDS_ON|CALLS_SERVICE]->(s)
                    WITH s, count(DISTINCT dep) as outgoing_deps, 
                         count(DISTINCT caller) as incoming_deps,
                         collect(DISTINCT dep.name) as dependencies,
                         collect(DISTINCT caller.name) as callers
                    RETURN s.name as service, s.language as language,
                           outgoing_deps, incoming_deps,
                           (outgoing_deps + incoming_deps) as total_connections,
                           dependencies, callers,
                           CASE 
                             WHEN (outgoing_deps + incoming_deps) > 8 THEN 'CRITICAL'
                             WHEN (outgoing_deps + incoming_deps) > 4 THEN 'HIGH'
                             WHEN (outgoing_deps + incoming_deps) > 1 THEN 'MEDIUM'
                             ELSE 'LOW'
                           END as impact_level
                    ORDER BY total_connections DESC
                    LIMIT 15
                    """
                    high_impact_result = session.run(high_impact_query, services=affected_services)
                else:
                    high_impact_query = """
                    MATCH (s:Service)-[:PART_OF]->(a:Application)
                    OPTIONAL MATCH (s)-[:DEPENDS_ON|CALLS_SERVICE]->(dep:Service)
                    OPTIONAL MATCH (caller:Service)-[:DEPENDS_ON|CALLS_SERVICE]->(s)
                    WITH s, count(DISTINCT dep) as outgoing_deps, 
                         count(DISTINCT caller) as incoming_deps,
                         collect(DISTINCT dep.name) as dependencies,
                         collect(DISTINCT caller.name) as callers
                    RETURN s.name as service, s.language as language,
                           outgoing_deps, incoming_deps,
                           (outgoing_deps + incoming_deps) as total_connections,
                           dependencies, callers,
                           CASE 
                             WHEN (outgoing_deps + incoming_deps) > 8 THEN 'CRITICAL'
                             WHEN (outgoing_deps + incoming_deps) > 4 THEN 'HIGH'
                             WHEN (outgoing_deps + incoming_deps) > 1 THEN 'MEDIUM'
                             ELSE 'LOW'
                           END as impact_level
                    ORDER BY total_connections DESC
                    LIMIT 15
                    """
                    high_impact_result = session.run(high_impact_query)
                dependency_data['high_impact_services'] = [dict(record) for record in high_impact_result]
                
                # Get language-specific dependency clusters - only for specified services
                if affected_services:
                    language_clusters_query = """
                    MATCH (s1:Service)-[:DEPENDS_ON|CALLS_SERVICE]->(s2:Service)
                    WHERE s1.language = s2.language 
                    AND (s1.name IN $services OR s2.name IN $services)
                    RETURN s1.language as language,
                           count(*) as internal_connections,
                           collect(DISTINCT s1.name) + collect(DISTINCT s2.name) as services_in_cluster
                    ORDER BY internal_connections DESC
                    """
                    clusters_result = session.run(language_clusters_query, services=affected_services)
                else:
                    language_clusters_query = """
                    MATCH (s1:Service)-[:DEPENDS_ON|CALLS_SERVICE]->(s2:Service)
                    WHERE s1.language = s2.language
                    RETURN s1.language as language,
                           count(*) as internal_connections,
                           collect(DISTINCT s1.name) + collect(DISTINCT s2.name) as services_in_cluster
                    ORDER BY internal_connections DESC
                    """
                    clusters_result = session.run(language_clusters_query)
                dependency_data['language_clusters'] = [dict(record) for record in clusters_result]
                
                return dependency_data
                
        except Exception as e:
            print(f"Warning: Dependency analysis failed: {e}")
            return {
                'critical_paths': [], 
                'circular_dependencies': [], 
                'high_impact_services': [],
                'language_clusters': []
            }
    

    
    def _gather_enhanced_system_intelligence(self, migration_context: Dict[str, Any], 
                                           neo4j_analysis: Dict[str, Any], 
                                           dependency_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Gather comprehensive system intelligence for enhanced planning"""
        
        # Calculate migration complexity based on real data
        complexity_score = self._calculate_complexity_score(neo4j_analysis, dependency_analysis)
        
        # Identify migration blockers
        migration_blockers = self._identify_migration_blockers(dependency_analysis)
        
        # Assess service migration readiness
        readiness_assessment = self._assess_migration_readiness(neo4j_analysis, dependency_analysis)
        
        return {
            'complexity_score': complexity_score,
            'migration_blockers': migration_blockers,
            'readiness_assessment': readiness_assessment,
            'risk_factors': self._calculate_enhanced_risks(neo4j_analysis, dependency_analysis),
            'optimization_opportunities': self._identify_optimization_opportunities(neo4j_analysis, dependency_analysis)
        }
    
    def _calculate_complexity_score(self, neo4j_analysis: Dict[str, Any], 
                                   dependency_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate migration complexity based on actual system analysis"""
        
        total_services = len(neo4j_analysis.get('services', []))
        total_dependencies = len(neo4j_analysis.get('dependencies', []))
        critical_paths = len(dependency_analysis.get('critical_paths', []))
        circular_deps = len(dependency_analysis.get('circular_dependencies', []))
        high_impact_services = len([s for s in dependency_analysis.get('high_impact_services', []) 
                                   if s.get('impact_level') in ['CRITICAL', 'HIGH']])
        
        # Calculate weighted complexity score (0-100)
        base_score = min(total_services * 2, 30)
        dependency_score = min(total_dependencies * 1.5, 25) 
        complexity_score = min(critical_paths * 3, 20)
        risk_score = min(circular_deps * 5 + high_impact_services * 3, 25)
        
        total_score = base_score + dependency_score + complexity_score + risk_score
        
        return {
            'total_score': int(total_score),
            'complexity_level': 'VERY HIGH' if total_score > 80 else 
                              'HIGH' if total_score > 60 else 
                              'MEDIUM' if total_score > 40 else 'LOW',
            'contributing_factors': {
                'service_count': total_services,
                'dependency_count': total_dependencies,
                'critical_paths': critical_paths,
                'circular_dependencies': circular_deps,
                'high_impact_services': high_impact_services
            }
        }
    
    def _identify_migration_blockers(self, dependency_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify potential migration blockers"""
        blockers = []
        
        # Circular dependencies are major blockers
        circular_deps = dependency_analysis.get('circular_dependencies', [])
        for dep in circular_deps:
            blockers.append({
                'type': 'CIRCULAR_DEPENDENCY',
                'service': dep.get('service'),
                'severity': 'HIGH',
                'description': f"Circular dependency detected in {dep.get('service')} service"
            })
        
        # Critical high-impact services
        high_impact = dependency_analysis.get('high_impact_services', [])
        for service in high_impact:
            if service.get('impact_level') == 'CRITICAL':
                blockers.append({
                    'type': 'HIGH_IMPACT_SERVICE',
                    'service': service.get('service'),
                    'severity': 'HIGH',
                    'description': f"{service.get('service')} has {service.get('total_connections')} connections - requires careful coordination"
                })
        
        return blockers
    
    def _assess_migration_readiness(self, neo4j_analysis: Dict[str, Any], 
                                   dependency_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Assess readiness of services for migration"""
        
        services = neo4j_analysis.get('services', [])
        high_impact = {s.get('service'): s for s in dependency_analysis.get('high_impact_services', [])}
        
        readiness_report = {
            'ready': [],
            'needs_preparation': [],
            'high_risk': []
        }
        
        for service in services:
            service_name = service.get('name')
            impact_data = high_impact.get(service_name, {})
            
            total_connections = impact_data.get('total_connections', 0)
            impact_level = impact_data.get('impact_level', 'LOW')
            
            if impact_level == 'LOW' and total_connections <= 2:
                readiness_report['ready'].append({
                    'service': service_name,
                    'language': service.get('language'),
                    'reason': 'Low impact, minimal dependencies'
                })
            elif impact_level in ['MEDIUM', 'HIGH']:
                readiness_report['needs_preparation'].append({
                    'service': service_name,
                    'language': service.get('language'),
                    'connections': total_connections,
                    'reason': f'{impact_level} impact - needs coordination'
                })
            else:
                readiness_report['high_risk'].append({
                    'service': service_name,
                    'language': service.get('language'),
                    'connections': total_connections,
                    'reason': f'Critical service with {total_connections} connections'
                })
        
        return readiness_report
    
    def _calculate_enhanced_risks(self, neo4j_analysis: Dict[str, Any], 
                                 dependency_analysis: Dict[str, Any]) -> List[str]:
        """Calculate enhanced risk factors based on actual system analysis"""
        risks = []
        
        # Service count risks
        service_count = len(neo4j_analysis.get('services', []))
        if service_count > 20:
            risks.append(f"Large system scope: {service_count} services require coordination")
        
        # Dependency complexity risks
        critical_paths = dependency_analysis.get('critical_paths', [])
        if len(critical_paths) > 10:
            risks.append(f"Complex dependency chains: {len(critical_paths)} critical paths identified")
        
        # Circular dependency risks
        circular_deps = dependency_analysis.get('circular_dependencies', [])
        if circular_deps:
            risks.append(f"Circular dependencies detected in {len(circular_deps)} services")
        
        # Language diversity risks
        languages = set()
        for service in neo4j_analysis.get('services', []):
            if service.get('language'):
                languages.add(service.get('language'))
        
        if len(languages) > 5:
            risks.append(f"Technology diversity: {len(languages)} different languages require specialized expertise")
        
        return risks
    
    def _identify_optimization_opportunities(self, neo4j_analysis: Dict[str, Any], 
                                           dependency_analysis: Dict[str, Any]) -> List[str]:
        """Identify optimization opportunities during migration"""
        opportunities = []
        
        # Language consolidation opportunities
        tech_stack = neo4j_analysis.get('technology_stack', [])
        small_language_groups = [lang for lang in tech_stack if lang.get('service_count', 0) == 1]
        
        if len(small_language_groups) > 2:
            opportunities.append(f"Language consolidation: {len(small_language_groups)} single-service languages could be migrated to common platforms")
        
        # Dependency simplification
        high_impact = dependency_analysis.get('high_impact_services', [])
        bottlenecks = [s for s in high_impact if s.get('total_connections', 0) > 6]
        
        if bottlenecks:
            opportunities.append(f"Dependency optimization: {len(bottlenecks)} services could benefit from interface simplification")
        
        # Architecture modernization
        language_clusters = dependency_analysis.get('language_clusters', [])
        tightly_coupled = [cluster for cluster in language_clusters if cluster.get('internal_connections', 0) > 5]
        
        if tightly_coupled:
            opportunities.append(f"Microservice boundaries: {len(tightly_coupled)} language clusters show tight coupling that could be optimized")
        
        return opportunities
    
    def _generate_analysis_driven_plan(self, user_query: str, migration_context: Dict[str, Any], 
                                     system_analysis: Dict[str, Any], neo4j_analysis: Dict[str, Any], 
                                     dependency_analysis: Dict[str, Any]) -> str:
        """Generate migration plan using comprehensive system analysis"""
        
        # Build detailed context for LLM
        analysis_summary = f"""
## COMPREHENSIVE SYSTEM ANALYSIS

### System Overview:
- Total Services: {len(neo4j_analysis.get('services', []))}
- Technology Stack: {', '.join([f"{ts.get('language')} ({ts.get('service_count')} services)" for ts in neo4j_analysis.get('technology_stack', [])])}
- Total Dependencies: {len(neo4j_analysis.get('dependencies', []))}
- Migration Complexity: {system_analysis.get('complexity_score', {}).get('complexity_level', 'UNKNOWN')}

### Critical Dependencies Identified:
{chr(10).join([f"- {path.get('start_service')} -> {path.get('end_service')} (depth: {path.get('dependency_depth')})" for path in dependency_analysis.get('critical_paths', [])[:5]])}

### High-Impact Services:
{chr(10).join([f"- {service.get('service')} ({service.get('language')}): {service.get('total_connections')} connections - {service.get('impact_level')} impact" for service in dependency_analysis.get('high_impact_services', [])[:5]])}

### Migration Blockers:
{chr(10).join([f"- {blocker.get('type')}: {blocker.get('description')}" for blocker in system_analysis.get('migration_blockers', [])[:3]])}

### Service Readiness:
- Ready for migration: {len(system_analysis.get('readiness_assessment', {}).get('ready', []))} services
- Need preparation: {len(system_analysis.get('readiness_assessment', {}).get('needs_preparation', []))} services  
- High risk: {len(system_analysis.get('readiness_assessment', {}).get('high_risk', []))} services

### Optimization Opportunities:
{chr(10).join([f"- {opp}" for opp in system_analysis.get('optimization_opportunities', [])[:3]])}
"""

        context = f"""
You are an expert enterprise migration architect with deep knowledge of complex microservices systems.

{analysis_summary}

## Migration Context:
- Migration Type: {migration_context['migration_type'].value}
- Complexity Level: {migration_context['complexity_level']}
- Affected Services: {migration_context.get('affected_services', 'System-wide assessment')}

## User Request:
{user_query}

Based on this REAL SYSTEM ANALYSIS (not generic assumptions), generate a comprehensive, actionable migration plan that:

1. **Addresses the specific dependencies and blockers identified**
2. **Sequences migration steps based on actual service readiness**  
3. **Includes specific risk mitigations for identified issues**
4. **Leverages the optimization opportunities discovered**
5. **Provides realistic timelines based on system complexity**

Structure your response as a detailed migration plan with:
- Executive Summary (based on actual analysis)
- Prerequisites (specific to identified blockers)
- Phased Migration Steps (ordered by dependency analysis)
- Risk Mitigation (targeting actual risks found)
- Success Metrics (relevant to system architecture)
- Timeline Estimates (based on complexity score)

Make every recommendation specific to the analyzed system architecture.
"""

        try:
            from openai import OpenAI
            client = OpenAI()
            
            response = client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": context},
                    {"role": "user", "content": f"Create analysis-driven migration plan for: {user_query}"}
                ],
                max_tokens=3000,
                temperature=0.1
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"LLM API error: {e}")
            return self._generate_enhanced_fallback_plan(migration_context, system_analysis, neo4j_analysis, dependency_analysis)
    
    def _generate_enhanced_fallback_plan(self, migration_context: Dict[str, Any], 
                                       system_analysis: Dict[str, Any], 
                                       neo4j_analysis: Dict[str, Any],
                                       dependency_analysis: Dict[str, Any]) -> str:
        """Generate enhanced fallback plan based on actual analysis"""
        
        service_count = len(neo4j_analysis.get('services', []))
        complexity = system_analysis.get('complexity_score', {}).get('complexity_level', 'MEDIUM')
        ready_services = len(system_analysis.get('readiness_assessment', {}).get('ready', []))
        high_risk_services = len(system_analysis.get('readiness_assessment', {}).get('high_risk', []))
        
        return f"""
# Analysis-Driven Migration Plan

## Executive Summary
Based on comprehensive system analysis of {service_count} services with {complexity} complexity, this migration requires a phased approach prioritizing {ready_services} ready services while carefully managing {high_risk_services} high-risk services.

## Prerequisites (Based on System Analysis)
1. **Dependency Mapping Validation**: Verify the {len(dependency_analysis.get('critical_paths', []))} critical dependency paths identified
2. **High-Impact Service Coordination**: Establish change control for {len([s for s in dependency_analysis.get('high_impact_services', []) if s.get('impact_level') in ['CRITICAL', 'HIGH']])} critical services
3. **Migration Blocker Resolution**: Address {len(system_analysis.get('migration_blockers', []))} identified blockers before proceeding

## Phase 1: Ready Services Migration (Weeks 1-4)
- Target {ready_services} services identified as migration-ready
- Low-risk, minimal dependency services
- Parallel execution possible

## Phase 2: Preparation-Required Services (Weeks 5-8) 
- Target {len(system_analysis.get('readiness_assessment', {}).get('needs_preparation', []))} services needing coordination
- Implement dependency management
- Sequential execution recommended

## Phase 3: High-Risk Services (Weeks 9-16)
- Target {high_risk_services} high-impact services
- Extensive testing and rollback preparation
- Careful orchestration required

## Risk Mitigation (System-Specific)
{chr(10).join([f"- {risk}" for risk in system_analysis.get('risk_factors', [])[:5]])}

## Success Metrics
- Zero circular dependency introduction
- Maintain service availability > 99.9%
- Complete dependency chain validation
- Performance baseline maintenance

## Estimated Timeline: {12 + (service_count // 5)} weeks
"""
    
    def _structure_enhanced_migration_plan(self, plan_content: str, migration_context: Dict[str, Any],
                                         system_analysis: Dict[str, Any], neo4j_analysis: Dict[str, Any], 
                                         dependency_analysis: Dict[str, Any]) -> MigrationPlan:
        """Structure the enhanced migration plan with comprehensive analysis data"""
        
        # Extract structured information - prioritize user-specified services from query
        if migration_context.get('affected_services'):
            affected_services = migration_context['affected_services']
        else:
            affected_services = [s.get('name') for s in neo4j_analysis.get('services', [])]
        
        complexity_info = system_analysis.get('complexity_score', {})
        readiness_info = system_analysis.get('readiness_assessment', {})
        
        # Calculate realistic timeline
        base_weeks = 8
        complexity_multiplier = {
            'LOW': 1.0,
            'MEDIUM': 1.5, 
            'HIGH': 2.0,
            'VERY HIGH': 2.5
        }.get(complexity_info.get('complexity_level', 'MEDIUM'), 1.5)
        
        service_factor = len(affected_services) // 5 + 1
        estimated_weeks = int(base_weeks * complexity_multiplier + service_factor)
        
        # Create migration steps based on analysis
        steps = self._create_analysis_based_steps(migration_context, system_analysis, dependency_analysis)
        
        # Generate comprehensive risks and mitigations
        risks_and_mitigations = {}
        for risk in system_analysis.get('risk_factors', []):
            risks_and_mitigations[risk] = self._get_mitigation_for_risk(risk)
        
        for blocker in system_analysis.get('migration_blockers', []):
            risk_key = f"{blocker.get('type')}: {blocker.get('service', 'System')}"
            risks_and_mitigations[risk_key] = self._get_mitigation_for_blocker(blocker)
        
        return MigrationPlan(
            title=f"Analysis-Driven {migration_context['migration_type'].value} Plan",
            description=f"Comprehensive migration plan based on deep system analysis of {len(affected_services)} services",
            migration_type=migration_context['migration_type'],
            affected_services=affected_services,
            total_estimated_effort=complexity_info.get('complexity_level', 'MEDIUM'),
            timeline=f"{estimated_weeks} weeks",
            prerequisites=self._generate_analysis_based_prerequisites(system_analysis, dependency_analysis),
            steps=steps,
            risks_and_mitigations=risks_and_mitigations,
            success_metrics=self._generate_analysis_based_success_metrics(neo4j_analysis, system_analysis)
        )
    
    def _create_analysis_based_steps(self, migration_context: Dict[str, Any], 
                                   system_analysis: Dict[str, Any], 
                                   dependency_analysis: Dict[str, Any]) -> List[MigrationStep]:
        """Create migration steps based on actual system analysis"""
        steps = []
        
        # Step 1: Dependency Analysis Validation
        steps.append(MigrationStep(
            step_number=1,
            title="Validate Dependency Analysis",
            description=f"Confirm {len(dependency_analysis.get('critical_paths', []))} critical paths and resolve {len(dependency_analysis.get('circular_dependencies', []))} circular dependencies",
            category="Planning",
            estimated_effort="Medium",
            dependencies=[],
            risks=["Undiscovered dependencies", "Analysis accuracy"],
            validation_criteria=[
                "All dependency paths verified",
                "Circular dependencies documented",
                "High-impact services identified"
            ]
        ))
        
        # Step 2: Migration Blocker Resolution
        blockers = system_analysis.get('migration_blockers', [])
        if blockers:
            steps.append(MigrationStep(
                step_number=2,
                title="Resolve Migration Blockers",
                description=f"Address {len(blockers)} identified migration blockers including circular dependencies and high-impact services",
                category="Planning",
                estimated_effort="High",
                dependencies=["Validate Dependency Analysis"],
                risks=[blocker.get('description') for blocker in blockers[:3]],
                validation_criteria=[
                    "All circular dependencies resolved",
                    "High-impact service coordination established",
                    "Rollback procedures validated"
                ]
            ))
        
        # Step 3: Ready Services Migration
        readiness = system_analysis.get('readiness_assessment', {})
        ready_count = len(readiness.get('ready', []))
        if ready_count > 0:
            steps.append(MigrationStep(
                step_number=3,
                title=f"Migrate Ready Services ({ready_count} services)",
                description=f"Execute migration for {ready_count} services identified as ready with minimal dependencies",
                category="Implementation",
                estimated_effort="Medium" if ready_count < 5 else "High",
                dependencies=["Resolve Migration Blockers"] if blockers else ["Validate Dependency Analysis"],
                risks=["Service downtime", "Integration failures"],
                validation_criteria=[
                    "All ready services migrated successfully",
                    "Dependencies remain functional",
                    "Performance benchmarks met"
                ]
            ))
        
        # Step 4: Coordination-Required Services  
        needs_prep = len(readiness.get('needs_preparation', []))
        if needs_prep > 0:
            steps.append(MigrationStep(
                step_number=4,
                title=f"Migrate Coordination-Required Services ({needs_prep} services)",
                description=f"Execute coordinated migration for {needs_prep} services requiring dependency management",
                category="Implementation", 
                estimated_effort="High",
                dependencies=[f"Migrate Ready Services ({ready_count} services)"] if ready_count > 0 else ["Resolve Migration Blockers"],
                risks=["Cascade failures", "Dependency conflicts", "Extended downtime"],
                validation_criteria=[
                    "Service coordination successful",
                    "Dependency chains validated",
                    "Integration tests passed"
                ]
            ))
        
        # Step 5: High-Risk Services
        high_risk_count = len(readiness.get('high_risk', []))
        if high_risk_count > 0:
            steps.append(MigrationStep(
                step_number=5,
                title=f"Migrate High-Risk Services ({high_risk_count} services)",
                description=f"Carefully execute migration for {high_risk_count} critical services with extensive connections",
                category="Implementation",
                estimated_effort="Very High",
                dependencies=[f"Migrate Coordination-Required Services ({needs_prep} services)"] if needs_prep > 0 else [f"Migrate Ready Services ({ready_count} services)"],
                risks=["System-wide outage", "Critical service failure", "Complex rollback scenarios"],
                validation_criteria=[
                    "Critical services fully operational",
                    "All dependent services verified",
                    "Complete system integration validated"
                ]
            ))
        
        # Step 6: System Validation
        steps.append(MigrationStep(
            step_number=len(steps) + 1,
            title="Complete System Validation",
            description="Comprehensive validation of entire migrated system including performance and integration testing",
            category="Testing",
            estimated_effort="High",
            dependencies=[s.title for s in steps if s.category == "Implementation"],
            risks=["Performance degradation", "Undiscovered integration issues"],
            validation_criteria=[
                "End-to-end system testing passed",
                "Performance benchmarks met",
                "All services operational",
                "Monitoring and alerting verified"
            ]
        ))
        
        return steps
    
    def _get_mitigation_for_risk(self, risk: str) -> str:
        """Get specific mitigation strategy for identified risk"""
        if "circular" in risk.lower():
            return "Implement interface abstraction and phased dependency breaking"
        elif "high impact" in risk.lower() or "connections" in risk.lower():
            return "Use blue-green deployment with extensive testing and rollback procedures"
        elif "complexity" in risk.lower():
            return "Break migration into smaller phases with validation checkpoints"
        elif "coordination" in risk.lower():
            return "Implement comprehensive change management and communication protocols"
        else:
            return "Implement comprehensive monitoring, testing, and rollback procedures"
    
    def _get_mitigation_for_blocker(self, blocker: Dict[str, Any]) -> str:
        """Get specific mitigation for migration blocker"""
        blocker_type = blocker.get('type', '')
        
        if blocker_type == 'CIRCULAR_DEPENDENCY':
            return f"Refactor {blocker.get('service')} to break circular dependency before migration"
        elif blocker_type == 'HIGH_IMPACT_SERVICE':
            return f"Implement comprehensive testing and phased deployment for {blocker.get('service')}"
        else:
            return "Implement systematic resolution process with validation checkpoints"
    
    def _generate_analysis_based_prerequisites(self, system_analysis: Dict[str, Any], 
                                             dependency_analysis: Dict[str, Any]) -> List[str]:
        """Generate prerequisites based on actual system analysis"""
        prerequisites = []
        
        # Based on migration blockers
        blockers = system_analysis.get('migration_blockers', [])
        if blockers:
            prerequisites.append(f"Resolution plan for {len(blockers)} migration blockers")
        
        # Based on circular dependencies
        circular_deps = dependency_analysis.get('circular_dependencies', [])
        if circular_deps:
            prerequisites.append(f"Circular dependency resolution for {len(circular_deps)} services")
        
        # Based on high-impact services
        high_impact = [s for s in dependency_analysis.get('high_impact_services', []) 
                      if s.get('impact_level') in ['CRITICAL', 'HIGH']]
        if high_impact:
            prerequisites.append(f"Change control processes for {len(high_impact)} critical services")
        
        # Standard prerequisites
        prerequisites.extend([
            "Comprehensive backup and rollback procedures",
            "Monitoring and alerting system verification", 
            "Test environment with production-like data",
            "Cross-team communication and coordination plan"
        ])
        
        return prerequisites
    
    def _generate_analysis_based_success_metrics(self, neo4j_analysis: Dict[str, Any], 
                                               system_analysis: Dict[str, Any]) -> List[str]:
        """Generate success metrics based on system analysis"""
        service_count = len(neo4j_analysis.get('services', []))
        
        metrics = [
            f"All {service_count} services operational post-migration",
            "Zero data loss during migration process",
            "Service availability maintained above 99.9%",
            "Response time degradation less than 5%",
            "All dependency relationships validated and functional"
        ]
        
        # Add metrics based on complexity
        complexity = system_analysis.get('complexity_score', {})
        if complexity.get('complexity_level') in ['HIGH', 'VERY HIGH']:
            metrics.extend([
                "Complex dependency chains remain stable",
                "High-impact services show no performance regression",
                "Critical path validation successful"
            ])
        
        # Add optimization metrics if opportunities exist
        optimizations = system_analysis.get('optimization_opportunities', [])
        if optimizations:
            metrics.append("Migration optimization opportunities successfully implemented")
        
        return metrics
    

    
    def _create_ekg_based_plan(self, plan_content: str, migration_context: Dict[str, Any], 
                             system_analysis: Dict[str, Any], neo4j_analysis: Dict[str, Any]) -> MigrationPlan:
        """Create migration plan based purely on EKG data"""
        
        # Get actual services from EKG but filter by user-requested services
        all_services_data = neo4j_analysis.get('services', [])
        dependencies = neo4j_analysis.get('dependencies', [])
        
        # Use the specific services requested by user from migration_context
        requested_services = migration_context.get('affected_services', [])
        if requested_services:
            # Filter EKG services to only include requested ones
            services = [s for s in all_services_data if (s.get('service') or s.get('name')) in requested_services]
            affected_services = requested_services
        else:
            # Fallback to all services if no specific ones requested
            services = all_services_data
            affected_services = list(set(s.get('service') or s.get('name') for s in services if s.get('service') or s.get('name')))
        
        # Calculate realistic timeline based on EKG data
        dep_count = len(dependencies)
        service_count = len(affected_services)
        estimated_weeks = max(4, service_count * 2 + dep_count // 2)
        
        # Create EKG-based steps
        steps = []
        step_num = 1
        
        # Analysis step based on actual dependencies with specific details
        if dependencies:
            # Extract specific dependency relationships for detailed description
            dep_details = []
            for dep in dependencies:
                if isinstance(dep, dict):
                    from_svc = dep.get('from_service', 'unknown')
                    to_svc = dep.get('to_service', dep.get('to_name', 'unknown'))
                    rel_type = dep.get('relationship_type', 'unknown')
                    dep_details.append(f"{from_svc} → {to_svc} ({rel_type})")
                else:
                    dep_details.append(str(dep))
            
            # Limit to first 5 for readability, show all if <= 5
            if len(dep_details) <= 5:
                dep_description = f"Review specific dependencies: {', '.join(dep_details)}"
            else:
                dep_description = f"Review key dependencies: {', '.join(dep_details[:5])} (and {len(dep_details)-5} more)"
            
            steps.append(MigrationStep(
                step_number=step_num,
                title=f"Analyze {service_count} Service Dependencies",
                description=dep_description,
                category="Planning",
                estimated_effort="Medium",
                dependencies=[],
                risks=[f"Critical dependencies: {', '.join(dep_details[:3])}{'...' if len(dep_details) > 3 else ''}"],
                validation_criteria=[f"All {len(dependencies)} dependencies validated: {', '.join([d.split(' → ')[1].split(' (')[0] for d in dep_details[:3]])}{'...' if len(dep_details) > 3 else ''}"]
            ))
            step_num += 1
        
        # Service-specific migration steps (remove duplicates)
        processed_services = set()
        for service in services:
            service_name = service.get('service') or service.get('name')
            if service_name in processed_services:
                continue
            processed_services.add(service_name)
            
            service_lang = service.get('language', 'unknown')
            service_deps = service.get('runtime_deps', [])
            # Handle both string and dict dependencies safely
            service_dep_names = []
            if service_deps:
                for d in service_deps:
                    if isinstance(d, dict):
                        dep_name = d.get('to_name') or d.get('name') or str(d)
                    else:
                        dep_name = str(d)
                    if dep_name and dep_name not in service_dep_names:
                        service_dep_names.append(dep_name)
            
            # Build detailed description with actual dependency names
            if service_dep_names:
                dep_description = f"Migrate {service_lang} service with dependencies on: {', '.join(service_dep_names)}"
            else:
                dep_description = f"Migrate {service_lang} service (no external dependencies)"
            
            # Get implementation details for this service
            impl_details = service.get('implementation_details', {})
            migration_commands = service.get('migration_commands', {})
            validation_scripts = service.get('validation_scripts', {})
            
            # Create detailed implementation step with executable commands
            step_description = f"""Execute migration for {service_lang} service:

**Pre-migration Commands:**
{chr(10).join([f"  {cmd}" for cmd in migration_commands.get('pre_migration', [])])}

**Dependency Updates:**
{chr(10).join([f"  {cmd}" for cmd in migration_commands.get('dependency_update', [])])}

**Build and Test:**
{chr(10).join([f"  {cmd}" for cmd in migration_commands.get('build_and_test', [])])}

**Configuration Files to Update:**
{chr(10).join([f"  {file}" for file in impl_details.get('config_files', [])])}

**File Modifications for Agent Execution:**
{chr(10).join([f"  📝 {file_path}:" + chr(10) + chr(10).join([f"     - {mod['action']}: {mod.get('dependency', mod.get('property', mod.get('field', 'N/A')))}" + (f" ({mod.get('from_version', mod.get('from_value', ''))} → {mod.get('to_version', mod.get('to_value', ''))})" if mod.get('from_version') or mod.get('from_value') else "") for mod in file_info['modifications']]) for file_path, file_info in impl_details.get('file_modifications', {}).items()])}

**Current vs Target Versions:**
{chr(10).join([f"  {name}: {impl_details.get('current_versions', {}).get(name, 'unknown')} → {target_version}" for name, target_version in impl_details.get('target_versions', {}).items()])}

**Environment Variables:**
{chr(10).join([f"  {var}" for var in impl_details.get('environment_variables', [])])}
"""
            
            steps.append(MigrationStep(
                step_number=step_num,
                title=f"Migrate {service_name} Service",
                description=step_description,
                category="Implementation", 
                estimated_effort="High" if len(service_dep_names) > 3 else "Medium",
                dependencies=[f"Analyze {service_count} Service Dependencies"] if steps else [],
                risks=[f"Service depends on: {', '.join(service_dep_names)}", f"Config files: {len(impl_details.get('config_files', []))} files"] if service_dep_names else [],
                validation_criteria=[f"Health checks: {', '.join(validation_scripts.get('health_checks', [])[:2])}{'...' if len(validation_scripts.get('health_checks', [])) > 2 else ''}", f"Integration tests pass for: {', '.join(service_dep_names)}" if service_dep_names else f"{service_name} service operational"]
            ))
            step_num += 1
        
        # Final validation step with specific service names
        service_names = ', '.join(affected_services) if affected_services else 'target services'
        steps.append(MigrationStep(
            step_number=step_num,
            title="Validate Complete Migration",
            description=f"End-to-end testing of migrated services: {service_names}",
            category="Testing",
            estimated_effort="High",
            dependencies=[step.title for step in steps if step.category == "Implementation"],
            risks=[f"Integration issues between {service_names} and dependent services"],
            validation_criteria=[f"Services operational: {service_names}", f"All integrations tested for {service_names}"]
        ))
        
        # EKG-based risks with specific details
        risks_and_mitigations = {}
        
        # Add dependency-specific risks
        if dependencies:
            dep_services = set()
            for dep in dependencies:
                if isinstance(dep, dict):
                    to_svc = dep.get('to_service', dep.get('to_name'))
                    if to_svc:
                        dep_services.add(to_svc)
            
            if dep_services:
                risks_and_mitigations[f"Service dependencies on: {', '.join(list(dep_services)[:3])}{'...' if len(dep_services) > 3 else ''}"] = f"Validate {', '.join(list(dep_services))} availability and compatibility before migration"
        
        # Add general system risks
        if len(affected_services) == 1:
            risks_and_mitigations[f"Single service migration impact on {affected_services[0]}"] = f"Thorough testing and rollback plan for {affected_services[0]}"
        
        # Add any additional risk factors from system analysis
        for risk in system_analysis.get('risk_factors', []):
            risks_and_mitigations[risk] = "Implement comprehensive testing and monitoring"
        
        return MigrationPlan(
            title=f"EKG-Driven {migration_context['migration_type'].value} Plan",
            description=f"Migration plan for {len(affected_services)} {'service' if len(affected_services) == 1 else 'services'} based on actual EKG analysis",
            migration_type=migration_context['migration_type'],
            affected_services=affected_services,
            total_estimated_effort=migration_context.get('complexity_level', 'Medium'),
            timeline=f"{estimated_weeks} weeks",
            prerequisites=self._generate_dynamic_prerequisites_from_ekg(affected_services, dependencies),
            steps=steps,
            risks_and_mitigations=risks_and_mitigations,
            success_metrics=self._generate_dynamic_success_metrics_from_ekg(affected_services, dependencies)
        )

    def close(self):
        """Close connections"""
        if hasattr(self, 'neo4j_driver'):
            self.neo4j_driver.close()


def main():
    """Demo the migration plan generator"""
    
    planner = MigrationPlanGenerator()
    
    # Example queries
    queries = [
        "How do I migrate Java services to newer versions?",
        "Plan for upgrading ad service Java version with minimal downtime",
        "What steps needed to modernize the entire shopping cart system?",
        "Migration plan for moving from current frameworks to latest versions"
    ]
    
    try:
        for query in queries:
            print(f"\n🎯 Query: {query}")
            print("=" * 60)
            
            plan = planner.generate_migration_plan(query)
            
            print(f"📋 Plan: {plan.title}")
            print(f"📊 Affected Services: {len(plan.affected_services)} services")
            print(f"⏰ Timeline: {plan.timeline}")
            print(f"🔄 Steps: {len(plan.steps)} steps")
            print(f"⚠️ Risks: {len(plan.risks_and_mitigations)} identified")
            
            print("\n🚀 Next Steps:")
            for i, step in enumerate(plan.steps[:3], 1):
                print(f"   {i}. {step.title} ({step.category}, {step.estimated_effort} effort)")
            
            print("\n" + "="*60)
    
    except Exception as e:
        print(f"Error: {e}")
    finally:
        planner.close()


if __name__ == "__main__":
    main()