#!/usr/bin/env python3
"""
Pipeline Flow Demonstration

Shows the complete flow from:
1. Natural language query
2. Vector similarity search  
3. LLM-generated Cypher
4. Neo4j execution
5. Results presentation

Usage: python pipeline_flow_demo.py
"""

from enhanced_llm_cypher_generator import EnhancedLLMCypherGenerator
import json
import sys


def demonstrate_query_flow(generator, query: str):
    """Demonstrate the complete query processing flow"""
    
    print(f"🎯 QUERY: {query}")
    print("=" * 80)
    
    # Step 1: Generate Cypher with context
    print("📝 Step 1: Generating Cypher with LLM + Vector Context...")
    result = generator.generate_cypher(query)
    
    print(f"   Generated Cypher: {result['generated_cypher']}")
    print(f"   Similar Schema Elements: {len(result.get('similar_schema', []))}")
    print(f"   Similar Query Patterns: {len(result.get('similar_queries', []))}")
    print()
    
    # Step 2: Execute the query
    print("🔍 Step 2: Executing against Neo4j...")
    try:
        records = generator.execute_cypher(result['generated_cypher'])
        print(f"   ✅ Success! Retrieved {len(records)} records")
        
        # Show first few results
        if records:
            print("   📊 Sample Results:")
            for i, record in enumerate(records[:3]):
                print(f"      {i+1}: {record}")
            if len(records) > 3:
                print(f"      ... and {len(records) - 3} more")
        
    except Exception as e:
        print(f"   ❌ Execution Error: {e}")
        records = []
    
    print()
    return result, records


def main():
    """Main demonstration function"""
    
    print("🚀 ENHANCED LLM CYPHER GENERATOR - PIPELINE DEMONSTRATION")
    print("=" * 80)
    
    # Initialize generator
    print("🔧 Initializing Enhanced LLM Cypher Generator...")
    try:
        generator = EnhancedLLMCypherGenerator()
        print("✅ Generator initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize generator: {e}")
        sys.exit(1)
    
    # Demo queries from simple to complex
    demo_queries = [
        # Basic service queries
        "Show me all Java services",
        "What services depend on postgres?",
        
        # API and infrastructure
        "Which services expose HTTP APIs?",
        "Show me all database hosts",
        
        # Migration analysis
        "Analyze migration risk for all services",
        "Show services with most dependencies", 
        "Find services that other services call",
        
        # Comprehensive analysis
        "Show me comprehensive migration analysis for all services"
    ]
    
    try:
        # Run demonstrations
        for i, query in enumerate(demo_queries, 1):
            print(f"\n🎬 DEMONSTRATION {i}/{len(demo_queries)}")
            result, records = demonstrate_query_flow(generator, query)
            
            # Special handling for migration analysis
            if 'migration_analysis' in result:
                print("🔍 Migration Analysis Results:")
                analysis = result['migration_analysis']
                print(f"   Total Services: {analysis['total_services']}")
                print(f"   High Risk Services: {len(analysis['high_risk_services'])}")
                print(f"   Language Distribution: {analysis['language_distribution']}")
            
            input("   Press Enter to continue...")
        
        print(f"\n🎉 DEMONSTRATION COMPLETE!")
        print("=" * 80)
        
    except KeyboardInterrupt:
        print("\n👋 Demonstration stopped by user")
    except Exception as e:
        print(f"\n❌ Demonstration error: {e}")
    finally:
        generator.close()


if __name__ == "__main__":
    main()
