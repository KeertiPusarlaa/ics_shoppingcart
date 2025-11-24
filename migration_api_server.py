"""
Migration API Server

Flask REST API for the Enhanced LLM Cypher Generator
Provides endpoints for migration analysis and natural language queries

Usage:
python migration_api_server.py

Endpoints:
- POST /query - Natural language to Cypher generation
- POST /migration-analysis - Specialized migration analysis  
- GET /health - Health check
"""

from flask import Flask, request, jsonify
import os
import json
from typing import Dict, Any
import traceback

# Our enhanced generator
from enhanced_llm_cypher_generator import EnhancedLLMCypherGenerator

app = Flask(__name__)
# CORS disabled - install flask_cors if needed

# Global generator instance
generator = None


def initialize_generator():
    """Initialize the enhanced generator"""
    global generator
    try:
        # Use environment variables or defaults
        openai_key = os.getenv("OPENAI_API_KEY")
        if not openai_key:
            print("⚠️ Warning: No OPENAI_API_KEY found in environment")
        
        generator = EnhancedLLMCypherGenerator(
            openai_api_key=openai_key
        )
        print("✅ Enhanced LLM Cypher Generator initialized")
        return True
    except Exception as e:
        print(f"❌ Failed to initialize generator: {e}")
        return False


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "Migration API Server",
        "generator_ready": generator is not None
    })


@app.route('/query', methods=['POST'])
def natural_language_query():
    """Convert natural language to Cypher and execute"""
    try:
        if not generator:
            return jsonify({"error": "Generator not initialized"}), 500
        
        data = request.get_json()
        if not data or 'query' not in data:
            return jsonify({"error": "Missing 'query' in request body"}), 400
        
        natural_query = data['query']
        execute_query = data.get('execute', True)
        
        print(f"🤖 Processing query: {natural_query}")
        
        # Generate Cypher
        result = generator.generate_cypher(natural_query)
        
        # Execute if requested
        if execute_query and 'generated_cypher' in result:
            try:
                records = generator.execute_cypher(result['generated_cypher'])
                result['execution_results'] = records
                result['record_count'] = len(records)
            except Exception as e:
                result['execution_error'] = str(e)
        
        return jsonify({
            "status": "success",
            "query": natural_query, 
            "result": result
        })
        
    except Exception as e:
        print(f"❌ Query error: {e}")
        traceback.print_exc()
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500


@app.route('/migration-analysis', methods=['POST'])
def migration_analysis():
    """Specialized migration analysis endpoint"""
    try:
        if not generator:
            return jsonify({"error": "Generator not initialized"}), 500
        
        data = request.get_json() or {}
        service_name = data.get('service_name')  # Optional: analyze specific service
        
        print(f"📊 Running migration analysis for: {service_name or 'all services'}")
        
        # Use the migration intelligence pipeline
        analysis_result = generator.migration_pipeline.analyze_service_complexity(service_name)
        
        return jsonify({
            "status": "success",
            "analysis": analysis_result,
            "service_filter": service_name
        })
        
    except Exception as e:
        print(f"❌ Migration analysis error: {e}")
        traceback.print_exc()
        return jsonify({
            "status": "error", 
            "error": str(e)
        }), 500


@app.route('/setup', methods=['POST'])
def setup_vector_database():
    """Initialize vector database (one-time setup)"""
    try:
        if not generator:
            return jsonify({"error": "Generator not initialized"}), 500
        
        print("🔧 Setting up vector database...")
        generator.setup_vector_data()
        
        return jsonify({
            "status": "success",
            "message": "Vector database setup completed"
        })
        
    except Exception as e:
        print(f"❌ Setup error: {e}")
        traceback.print_exc()
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500


@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "status": "error",
        "error": "Endpoint not found"
    }), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        "status": "error", 
        "error": "Internal server error"
    }), 500


if __name__ == "__main__":
    print("🚀 Starting Migration API Server...")
    
    # Initialize generator
    if initialize_generator():
        print("🌐 Server ready at http://localhost:5000")
        print("\n📚 Available endpoints:")
        print("   POST /query - Natural language queries")
        print("   POST /migration-analysis - Migration analysis") 
        print("   POST /setup - Setup vector database")
        print("   GET  /health - Health check")
        
        app.run(debug=True, host='0.0.0.0', port=5000)
    else:
        print("❌ Failed to start server - generator initialization failed")
