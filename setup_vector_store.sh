#!/bin/bash

# EKG + Milvus + LLM Setup Script

echo "🚀 Setting up EKG Vector Store + LLM Cypher Generation"
echo "=================================================="

# Check if virtual environment is activated
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "⚠️  Please activate your virtual environment first:"
    echo "   source venv/bin/activate"
    exit 1
fi

# Install additional Python packages
echo "📦 Installing Python dependencies..."
pip install -r requirements_vector.txt

# Start Milvus if not running
echo "🗄️  Checking Milvus database..."
if ! docker ps | grep -q milvus-standalone; then
    echo "Starting Milvus standalone..."
    
    # Download Milvus docker-compose if needed
    if [ ! -f "docker-compose-milvus.yml" ]; then
        echo "Downloading Milvus docker-compose..."
        wget https://github.com/milvus-io/milvus/releases/download/v2.3.4/milvus-standalone-docker-compose.yml -O docker-compose-milvus.yml
    fi
    
    # Start Milvus
    docker-compose -f docker-compose-milvus.yml up -d
    
    echo "⏳ Waiting for Milvus to start..."
    sleep 15
else
    echo "✅ Milvus is already running"
fi

# Check Neo4j status
echo "🗃️  Checking Neo4j database..."
if ! docker ps | grep -q neo4j-ekg; then
    echo "⚠️  Neo4j container not running. Starting it..."
    docker start neo4j-ekg
    sleep 5
fi

# Setup vector database
echo "🧠 Setting up vector database with schema and patterns..."
python llm_cypher_generator.py "test query" --setup --no-execute

echo ""
echo "✅ Setup complete!"
echo ""
echo "🎯 Usage Examples:"
echo "   python llm_cypher_generator.py \"Show me all services\""
echo "   python llm_cypher_generator.py \"Which services depend on databases?\""
echo "   python llm_cypher_generator.py \"Find services written in Go\""
echo ""
echo "🔑 For OpenAI integration, set your API key:"
echo "   export OPENAI_API_KEY='your-api-key-here'"
echo "   python llm_cypher_generator.py \"your query\" --openai-key \$OPENAI_API_KEY"