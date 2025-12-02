#!/usr/bin/env python3

# Quick test script to debug service discovery
from migration_plan_generator import MigrationPlanGenerator

def test_service_discovery():
    generator = MigrationPlanGenerator()
    
    test_queries = [
        "Generate migration plan only for product-reviews service",
        "Create migration plan for payment service",
        "Migration plan for fraud-detection"
    ]
    
    for query in test_queries:
        print(f"\nTesting query: '{query}'")
        context = generator._analyze_migration_query(query)
        print(f"Found services: {context['affected_services']}")
        print(f"Total services found: {len(context['affected_services'])}")

if __name__ == "__main__":
    test_service_discovery()