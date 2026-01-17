# Self-Healing Ontology MCP Agent System

![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)
![MCP](https://img.shields.io/badge/MCP-enabled-green.svg)
![Tests](https://img.shields.io/badge/tests-passing-brightgreen.svg)

A production-ready self-healing multi-agent system that uses ontologies and MCP (Model Context Protocol) to automatically adapt when database schemas change.

## Overview

This system solves a critical problem in modern AI agent deployments: **when database schemas change, agent queries break**. Instead of manually updating every agent and query, this system:

1. **Monitors** database schemas continuously
2. **Detects** schema changes automatically
3. **Analyzes** changes using Claude AI
4. **Heals** ontology mappings automatically
5. **Reloads** MCP tools without downtime

The result: agents continue working seamlessly even when databases evolve.

## Architecture

```
┌─────────────┐      ┌──────────────┐      ┌─────────────┐
│   Agents    │─────▶│ MCP Server   │─────▶│  Database   │
│ (Analytics, │      │ (Ontology)   │      │  (SQLite,   │
│  Support)   │      │              │      │  PostgreSQL)│
└─────────────┘      └──────┬───────┘      └─────────────┘
                            │
                            ▼
                   ┌─────────────────┐
                   │ Schema Monitor  │
                   │ (SHA-256 Hash)  │
                   └────────┬────────┘
                            │
                            ▼
                   ┌─────────────────┐
                   │  Diff Engine    │
                   │ (Change Detect) │
                   └────────┬────────┘
                            │
                            ▼
                   ┌─────────────────┐
                   │ Ontology Remap  │
                   │ (Claude AI)     │
                   └─────────────────┘
```

## Features

- ✅ **Automatic Schema Change Detection** - SHA-256 hash-based monitoring
- ✅ **Intelligent Diff Analysis** - Detects renames, additions, deletions
- ✅ **AI-Powered Healing** - Uses Claude to update ontology mappings
- ✅ **MCP Protocol Support** - Native Model Context Protocol integration
- ✅ **Multi-Agent Support** - Shared semantic understanding across agents
- ✅ **Hot Reload** - MCP server reloads without downtime
- ✅ **Audit Logging** - Complete JSON audit trail
- ✅ **Alert Integration** - Slack/Teams webhook support
- ✅ **Production Ready** - Docker, tests, error handling

## Quickstart (< 5 minutes)

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Up Environment

```bash
# Create .env file
echo "ANTHROPIC_API_KEY=your_api_key_here" > .env
```

### 3. Initialize Database and Ontology

```bash
# Create sample database
python scripts/init_db.py

# Generate initial ontology
python scripts/setup_ontology.py
```

### 4. Run Quickstart Example

```bash
python examples/quickstart.py
```

You should see:
- ✓ MCP Server initialized
- ✓ Tools generated from ontology
- ✓ Schema monitoring active
- ✓ Agent system ready

### 5. Test Schema Change Healing

```bash
# In another terminal, modify the database schema
sqlite3 test_database.db "ALTER TABLE customers ADD COLUMN phone TEXT;"

# Watch the system automatically detect and heal
python examples/full_system.py
```

## Installation

### From Source

```bash
git clone https://github.com/yourusername/ontology-mcp-self-healing.git
cd ontology-mcp-self-healing
pip install -r requirements.txt
pip install -e .
```

### Using Docker

```bash
# Build and run
docker-compose up -d

# View logs
docker-compose logs -f
```

## Configuration

Configuration is managed via `config/config.yaml`:

```yaml
# Database Configuration
database:
  type: sqlite  # sqlite, postgresql, mysql
  connection_string: sqlite:///./test_database.db

# Ontology Configuration
ontology:
  main_file: ontologies/business_domain.owl
  auto_reload: true

# Schema Monitoring
monitoring:
  enabled: true
  check_interval: 60  # seconds
  detect_renames: true

# Auto-Healing
healing:
  enabled: true
  auto_approve: false  # Set to true for automatic healing
  claude_model: claude-3-5-sonnet-20241022
  validation_enabled: true

# Alerts
alerts:
  enabled: true
  webhook_url: ${ALERT_WEBHOOK_URL}  # Optional
```

## Usage Examples

### Basic MCP Server

```python
from src.mcp_server.server import OntologyMCPServer

# Initialize server
server = OntologyMCPServer()

# Get available tools
tools = server.get_tools()

# Execute query
result = await server.execute_tool(
    "query_order",
    {"query": "all orders", "limit": 10}
)
```

### Create an Agent

```python
from src.mcp_server.server import OntologyMCPServer
from src.agents.examples.analytics_agent import AnalyticsAgent

# Initialize MCP server
mcp_server = OntologyMCPServer()

# Create agent
agent = AnalyticsAgent(mcp_server, claude_api_key="your_key")

# Query using natural language
response = await agent.query("What are the total sales for last month?")
```

### Full Self-Healing System

```python
from src.system.self_healing import SelfHealingAgentSystem

# Initialize system
system = SelfHealingAgentSystem()

# Start monitoring and healing
system.start()

# System runs forever, auto-healing on schema changes
```

## Architecture Details

### MCP Server

The MCP server loads OWL ontologies and generates tools dynamically:
- Extracts class → table mappings
- Extracts property → column mappings
- Translates semantic queries to SQL
- Caches queries for performance

### Schema Monitor

Continuous monitoring using:
- SQLAlchemy inspector for schema capture
- SHA-256 hashing for change detection
- Configurable check intervals
- Event callbacks on changes

### Diff Engine

Intelligent diff computation:
- Detects table/column additions/removals
- Heuristic-based rename detection
- Type change detection
- Detailed diff reporting

### Auto Remapper

AI-powered ontology healing:
- Extracts current ontology mappings
- Generates LLM prompts with schema changes
- Validates proposed RDF triples
- Applies updates to ontology files
- Supports manual approval mode

## Production Deployment

### Docker Deployment

```bash
# Build image
docker build -t ontology-mcp-self-healing .

# Run container
docker run -d \
  -e ANTHROPIC_API_KEY=your_key \
  -v $(pwd)/ontologies:/app/ontologies \
  -v $(pwd)/logs:/app/logs \
  ontology-mcp-self-healing
```

### Docker Compose

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f self-healing

# Stop services
docker-compose down
```

See [docs/deployment.md](docs/deployment.md) for Kubernetes, Helm, and production best practices.

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# Run specific test
pytest tests/test_mcp_server.py -v
```

## Documentation

- [Architecture Guide](docs/architecture.md) - Detailed system architecture
- [Deployment Guide](docs/deployment.md) - Production deployment instructions
- [Troubleshooting](docs/troubleshooting.md) - Common issues and solutions

## Project Structure

```
ontology-mcp-self-healing/
├── README.md
├── requirements.txt
├── setup.py
├── docker-compose.yml
├── Dockerfile
├── config/
│   └── config.yaml
├── ontologies/
│   └── business_domain.owl
├── src/
│   ├── mcp_server/      # MCP server implementation
│   ├── monitoring/      # Schema monitoring
│   ├── healing/         # Auto-healing
│   ├── system/          # Orchestration
│   └── agents/         # Agent implementations
├── tests/              # Test suite
├── examples/           # Example scripts
├── scripts/            # Setup scripts
└── docs/               # Documentation
```

## Getting Started

New to this project? Follow our comprehensive [SETUP_GUIDE.md](SETUP_GUIDE.md) for step-by-step instructions on:
- Cloning the repository
- Setting up your environment
- Running examples
- Running tests
- Troubleshooting common issues

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Publishing to GitHub

Want to publish this project? See [GITHUB_SETUP.md](GITHUB_SETUP.md) for step-by-step instructions.

## Acknowledgments

- Built with [owlready2](https://owlready2.readthedocs.io/) for ontology management
- Uses [Anthropic Claude](https://www.anthropic.com/) for AI-powered healing
- Implements [MCP Protocol](https://modelcontextprotocol.io/) for agent communication
- Powered by [LangChain](https://www.langchain.com/) for agent orchestration

## Related Articles

- [Medium Article: Self-Healing AI Agents](YOUR_ARTICLE_URL) - Deep dive into the system design
- [Blog Post: MCP for Production](YOUR_BLOG_URL) - Using MCP in production systems

---

**Made with ❤️ for the AI agent community**
