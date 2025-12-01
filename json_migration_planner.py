#!/usr/bin/env python3
"""
JSON Migration Plan Generator

Direct interface to generate migration plans in JSON format
Usage: python json_migration_planner.py "your migration query"
"""

import sys
import json
from migration_plan_generator import MigrationPlanGenerator

def generate_json_migration_plan(query: str):
    """Generate and output migration plan in JSON format"""
    
    print(f"🔍 Generating JSON migration plan for: {query}")
    print("=" * 80)
    
    try:
        planner = MigrationPlanGenerator()
        json_result = planner.generate_migration_plan_json(query)
        planner.close()
        
        # Pretty print JSON
        formatted_json = json.dumps(json_result, indent=2, ensure_ascii=False)
        print(formatted_json)
        
        return json_result
        
    except Exception as e:
        error_response = {
            "error": {
                "message": f"Migration plan generation failed: {str(e)}",
                "type": "generation_error", 
                "timestamp": "2025-11-25T00:00:00Z"
            }
        }
        print(json.dumps(error_response, indent=2))
        return error_response

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python json_migration_planner.py \"your migration query\"")
        sys.exit(1)
    
    query = " ".join(sys.argv[1:])
    generate_json_migration_plan(query)