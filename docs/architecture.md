# Architecture Guide

## System Overview

The Self-Healing Ontology MCP Agent System is designed to automatically maintain semantic mappings between ontologies and database schemas, ensuring AI agents can continue querying data even when schemas change.

## Components

### 1. MCP Server (`src/mcp_server/`)

**Purpose**: Bridge between semantic queries and SQL databases.

**Key Files**:
- `server.py`: Main server implementation
- `tools.py`: Tool generation from ontology

**How it works**:
1. Loads OWL ontology from file
2. Extracts class → table and property → column mappings
3. Generates MCP tools dynamically
4. Translates semantic queries to SQL at runtime
5. Executes queries and returns results

**Features**:
- Connection pooling for performance
- Query caching with TTL
- Hot-reload support
- Multiple database backends (SQLite, PostgreSQL)

### 2. Schema Monitor (`src/monitoring/`)

**Purpose**: Continuously monitor database schema for changes.

**Key Files**:
- `schema_monitor.py`: Monitoring loop and change detection
- `diff_engine.py`: Schema diff computation

**How it works**:
1. Captures schema snapshot using SQLAlchemy inspector
2. Computes SHA-256 hash of schema
3. Compares hash on configurable interval
4. Computes detailed diffs when hash changes
5. Triggers callbacks for detected changes

**Features**:
- SHA-256 hash-based detection
- Heuristic rename detection
- Configurable check intervals
- Event-driven callbacks

### 3. Auto Remapper (`src/healing/`)

**Purpose**: Automatically update ontology mappings when schema changes.

**Key Files**:
- `auto_remapper.py`: Claude API integration for remapping
- `validator.py`: Triple validation

**How it works**:
1. Extracts current ontology mappings
2. Generates LLM prompt with schema changes
3. Calls Claude API for remapping suggestions
4. Validates proposed RDF triples
5. Applies updates to ontology file (with approval)

**Features**:
- Claude API integration
- RDF triple validation
- Manual approval mode
- Backup creation before updates

### 4. Self-Healing System (`src/system/`)

**Purpose**: Orchestrate monitoring → detection → healing workflow.

**Key Files**:
- `self_healing.py`: Main orchestration logic
- `alerts.py`: Alert management

**How it works**:
1. Initializes all components
2. Starts schema monitoring
3. Handles schema change events
4. Triggers ontology remapping
5. Reloads MCP server after healing
6. Sends alerts for operations teams

**Features**:
- Complete audit logging
- Configurable auto-approve
- Graceful error handling
- Webhook alert integration

### 5. Agent System (`src/agents/`)

**Purpose**: Provide base agent class using MCP tools.

**Key Files**:
- `base_agent.py`: Base agent implementation
- `examples/`: Example agents (analytics, support)

**How it works**:
1. Initializes LangChain agent
2. Creates tools from MCP server
3. Executes queries using natural language
4. Agents share semantic understanding via MCP

**Features**:
- LangChain integration
- Shared ontology understanding
- Natural language queries
- Tool-based architecture

## Data Flow

### Query Flow

```
Agent Query (Natural Language)
    ↓
BaseAgent.query()
    ↓
LangChain Agent
    ↓
MCP Tool Execution
    ↓
Ontology → SQL Translation
    ↓
Database Query
    ↓
Result → Agent → User
```

### Healing Flow

```
Schema Change Detected
    ↓
SchemaMonitor.on_change()
    ↓
DiffEngine.compute_diff()
    ↓
SelfHealingAgentSystem._heal_ontology()
    ↓
OntologyRemapper.remap_ontology()
    ↓
Claude API Call
    ↓
Triple Validation
    ↓
Ontology File Update
    ↓
MCP Server Reload
    ↓
Alert Sent
```

## Ontology Format

The system uses OWL ontologies with custom annotations:

```xml
<!-- Class to Table Mapping -->
<owl:Class rdf:about="#Customer">
    <mapsToTable rdf:datatype="xsd:string">customers</mapsToTable>
</owl:Class>

<!-- Property to Column Mapping -->
<owl:DatatypeProperty rdf:about="#email">
    <mapsToColumn rdf:datatype="xsd:string">email</mapsToColumn>
</owl:DatatypeProperty>

<!-- Rename Handling -->
<owl:DatatypeProperty rdf:about="#oldProperty">
    <equivalentProperty rdf:resource="#newProperty"/>
</owl:DatatypeProperty>
```

## Configuration

Configuration is managed via YAML with environment variable support:

```yaml
database:
  connection_string: ${DATABASE_URL}  # Environment variable substitution

healing:
  auto_approve: ${AUTO_APPROVE:-false}  # Default value support
```

## Error Handling

The system uses structured logging and graceful error handling:

- All components log with `structlog`
- Errors are caught and logged, not propagated
- Retry logic for transient failures
- Audit logging for all operations

## Performance Considerations

1. **Connection Pooling**: SQLAlchemy connection pools for database access
2. **Query Caching**: MCP server caches query results with TTL
3. **Async Operations**: Schema monitoring and healing use async/await
4. **Lazy Loading**: Ontology loaded only when needed

## Security

- API keys stored in environment variables
- No sensitive data in logs
- Input validation for all queries
- Audit logging for compliance

## Extensibility

The system is designed for extensibility:

- **Database Adapters**: Easy to add new database backends
- **Agent Types**: Simple to create new agent types
- **Alert Channels**: Easy to add new alert channels
- **Remapping Strategies**: Can add different remapping strategies

## Future Enhancements

- [ ] Support for MongoDB and other NoSQL databases
- [ ] Multi-ontology support
- [ ] Web-based monitoring dashboard
- [ ] Kubernetes operator for K8s deployments
- [ ] GraphQL API layer
- [ ] Real-time schema change notifications
