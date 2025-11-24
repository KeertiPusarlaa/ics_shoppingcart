# Java Migration Planning - Natural Language Scenarios

## Successful Query Patterns for Ad Service Migration

### 1. **Basic Migration Assessment**
**User Input:** "Show me migration details for ad service: java_version, frameworks, dependencies, and which services call it"

**Generated Cypher:**
```cypher
MATCH (s:Service {name: "ad"}) 
OPTIONAL MATCH (s)-[:DEPENDS_ON]->(dependency)
OPTIONAL MATCH (caller:Service)-[:CALLS_SERVICE]->(s)
RETURN s.name AS service, 
       s.java_version AS java_version, 
       s.frameworks AS frameworks, 
       collect(distinct dependency.name) AS dependencies, 
       collect(distinct caller.name) AS called_by
```

**Results:**
- Service: ad
- Java Version: 21.0
- Frameworks: ['grpc', 'protobuf']
- Dependencies: ['otel-collector', 'flagd']
- Called by: ['product-catalog', 'product-reviews', 'recommendation', 'cart', 'currency', 'shipping', 'checkout', 'frontend', 'email', 'payment']

### 2. **Migration Impact Analysis**
**User Input:** "Migration assessment for ad service: show current java_version, frameworks array, dependencies array, and services that will be impacted by Java upgrade"

**Generated Cypher:**
```cypher
MATCH (adService:Service {name: "ad"}) 
WHERE toLower(adService.language) = 'java'
OPTIONAL MATCH (adService)-[:DEPENDS_ON]->(dependency)
WITH adService, collect(dependency.name) AS dependenciesArray
OPTIONAL MATCH (impactedService:Service)-[:DEPENDS_ON]->(adService)
RETURN adService.name AS serviceName, 
       adService.java_version AS currentJavaVersion, 
       adService.frameworks AS frameworksArray, 
       dependenciesArray, 
       collect(impactedService.name) AS impactedServices
```

**Results:**
- Service Name: ad
- Current Java Version: 21.0
- Frameworks: ['grpc', 'protobuf']
- Dependencies: ['otel-collector', 'flagd']
- Impacted Services: ['frontend']

### 3. **Risk Assessment Query**
**User Input:** "Before upgrading ad service from Java 21.0, I need to understand the blast radius - what services will be affected and what are the technology dependencies?"

**Generated Cypher:**
```cypher
MATCH (adService:Service {name: "ad", language: "java"})-[:CALLS_SERVICE|DEPENDS_ON*]->(affected)
RETURN DISTINCT affected.name AS ServiceAffected, 
       labels(affected) AS Type, 
       affected.language AS Language
ORDER BY Type, ServiceAffected
```

## Migration Planning Insights

### Current State Analysis
- **Ad Service**: Already on Java 21.0 (Latest LTS)
- **Frameworks**: gRPC and Protobuf (Java 21 compatible)
- **External Libraries**: OpenTelemetry stack (modern, compatible)
- **Impact Radius**: 10+ downstream services require coordination

### Migration Recommendations
1. **✅ No urgent upgrade needed** - Already on Java 21 LTS
2. **🔄 Focus on maintenance** - Ensure dependencies stay current
3. **🎯 Testing coordination** - 10 downstream services need validation
4. **📦 Framework compatibility** - gRPC/Protobuf are Java 21 ready

### Effective Query Patterns
- Use explicit property names: `java_version`, `frameworks`, `dependencies`
- Specify service by exact name: `{name: "ad"}`
- Include impact analysis with `CALLS_SERVICE` relationships
- Count affected services for risk assessment

### Business Value Queries
- "Show me migration details for [service]: java_version, frameworks, dependencies"
- "Migration assessment for [service]: current version, frameworks, impact analysis"
- "Risk assessment: [service] upgrade blast radius and technology dependencies"