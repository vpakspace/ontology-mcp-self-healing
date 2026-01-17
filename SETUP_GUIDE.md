# Complete Setup Guide

This guide provides step-by-step instructions to clone, set up, run, and test the Self-Healing Ontology MCP Agent System from scratch.

## Prerequisites

Before starting, ensure you have:

- **Python 3.10 or higher** ([Download Python](https://www.python.org/downloads/))
- **Git** ([Download Git](https://git-scm.com/downloads))
- **pip** (usually comes with Python)
- **Anthropic API Key** ([Get API Key](https://console.anthropic.com/))
- **(Optional) Docker** ([Download Docker](https://www.docker.com/get-started))

### Verify Prerequisites

```bash
# Check Python version (should be 3.10+)
python --version
# or
python3 --version

# Check pip version
pip --version
# or
pip3 --version

# Check Git version
git --version

# (Optional) Check Docker version
docker --version
```

## Step 1: Clone the Repository

### Option A: Clone from GitHub (Recommended)

```bash
# Clone the repository
git clone https://github.com/yourusername/ontology-mcp-self-healing.git

# Navigate to project directory
cd ontology-mcp-self-healing
```

### Option B: Download ZIP

1. Download ZIP from GitHub
2. Extract to your desired location
3. Navigate to extracted folder

## Step 2: Create Virtual Environment (Recommended)

Creating a virtual environment isolates project dependencies:

```bash
# Create virtual environment
python -m venv venv
# or on some systems
python3 -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# You should see (venv) in your terminal prompt
```

**Note:** Always activate the virtual environment before working on the project.

## Step 3: Install Dependencies

```bash
# Upgrade pip (recommended)
pip install --upgrade pip

# Install project dependencies
pip install -r requirements.txt

# Verify installation
pip list | grep -E "owlready2|anthropic|sqlalchemy|langchain"
```

**Expected Output:** You should see all required packages listed.

**Troubleshooting:**
- If you get permission errors, add `--user` flag: `pip install --user -r requirements.txt`
- If you get SSL errors, use: `pip install --trusted-host pypi.org --trusted-host pypi.python.org -r requirements.txt`

## Step 4: Set Up Environment Variables

Create a `.env` file in the project root:

```bash
# Create .env file
# On Windows (PowerShell):
New-Item -Path .env -ItemType File

# On Windows (CMD):
type nul > .env

# On macOS/Linux:
touch .env
```

Edit `.env` file and add your API key:

```bash
# .env file content
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Optional: Alert webhook URL (for Slack/Teams notifications)
# ALERT_WEBHOOK_URL=https://your-webhook-url.com/webhook
```

**Important:** 
- Replace `your_anthropic_api_key_here` with your actual Anthropic API key
- Never commit `.env` file to Git (it's already in `.gitignore`)
- Get your API key from: https://console.anthropic.com/

## Step 5: Initialize Database and Ontology

The project needs a sample database and ontology file:

```bash
# Create logs directory (if it doesn't exist)
mkdir -p logs
# On Windows: mkdir logs

# Initialize sample database
python scripts/init_db.py

# Generate initial ontology
python scripts/setup_ontology.py
```

**Expected Output:**
```
Database created successfully: test_database.db
  - customers table: 4 records
  - orders table: 7 records

Ontology created successfully: ontologies/business_domain.owl
```

**Verify Files Created:**
```bash
# Check database exists
ls test_database.db  # macOS/Linux
dir test_database.db  # Windows

# Check ontology exists
ls ontologies/business_domain.owl  # macOS/Linux
dir ontologies\business_domain.owl  # Windows
```

## Step 6: Run Quickstart Example

Test that everything works:

```bash
python examples/quickstart.py
```

**Expected Output:**
```
============================================================
Self-Healing Ontology MCP Agent System - Quickstart
============================================================

[1/5] Initializing MCP Server...
✓ MCP Server initialized with X tools

Available tools:
  - query_order: Query Order entities from the database...
  - query_customer: Query Customer entities from the database...

[2/5] Querying data through semantic interface...
✓ Query successful: 5 results

[3/5] Creating analytics agent...
✓ Agent created: AnalyticsAgent

[4/5] Setting up schema monitoring...
✓ Schema monitoring started

[5/5] Summary
============================================================
✓ MCP Server: Running
✓ Tools: Generated from ontology
✓ Schema Monitoring: Available
✓ Agent System: Ready
============================================================
```

**Troubleshooting:**
- If you see "Ontology file not found", run `python scripts/setup_ontology.py` again
- If you see "Database not found", run `python scripts/init_db.py` again
- If you see "ANTHROPIC_API_KEY not found", check your `.env` file

## Step 7: Run Tests

Verify all tests pass:

```bash
# Run all tests
pytest tests/ -v

# Run tests with coverage report
pytest tests/ --cov=src --cov-report=html

# View coverage report (opens in browser)
# macOS: open htmlcov/index.html
# Windows: start htmlcov/index.html
# Linux: xdg-open htmlcov/index.html
```

**Expected Output:**
```
======================== test session starts ========================
tests/test_mcp_server.py::test_translate_semantic_query_to_sql PASSED
tests/test_schema_monitor.py::test_schema_monitor_capture_schema PASSED
tests/test_diff_engine.py::test_compute_diff_column_added PASSED
...
==================== XX passed in X.XXs =====================
```

**Note:** Some tests may be skipped if optional dependencies aren't available. This is normal.

## Step 8: Run Full System (Optional)

Run the complete self-healing system:

```bash
python examples/full_system.py
```

This will:
- Start schema monitoring
- Initialize MCP server
- Set up auto-healing
- Monitor for schema changes

Press `Ctrl+C` to stop.

## Step 9: Test Schema Change Detection (Optional)

In a new terminal, modify the database schema to test auto-healing:

```bash
# Using SQLite command line
sqlite3 test_database.db "ALTER TABLE customers ADD COLUMN phone TEXT;"

# Or using Python
python -c "import sqlite3; conn = sqlite3.connect('test_database.db'); conn.execute('ALTER TABLE customers ADD COLUMN phone TEXT'); conn.commit(); conn.close(); print('Schema changed!')"
```

Watch the system detect and heal the change automatically.

## Alternative: Docker Setup

If you prefer using Docker:

### Step 1: Create `.env` file (same as above)

```bash
# .env file
ANTHROPIC_API_KEY=your_anthropic_api_key_here
```

### Step 2: Build and Run

```bash
# Build Docker image
docker build -t ontology-mcp-self-healing .

# Run with docker-compose
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## Verification Checklist

✅ Python 3.10+ installed  
✅ Virtual environment created and activated  
✅ Dependencies installed (`pip install -r requirements.txt`)  
✅ `.env` file created with `ANTHROPIC_API_KEY`  
✅ Database initialized (`python scripts/init_db.py`)  
✅ Ontology created (`python scripts/setup_ontology.py`)  
✅ Quickstart example runs successfully  
✅ Tests pass (`pytest tests/ -v`)  

## Common Issues and Solutions

### Issue: "Module not found" errors

**Solution:**
```bash
# Ensure virtual environment is activated
# Reinstall dependencies
pip install -r requirements.txt
```

### Issue: "ANTHROPIC_API_KEY not found"

**Solution:**
```bash
# Check .env file exists and contains API key
cat .env  # macOS/Linux
type .env  # Windows

# Ensure .env file is in project root directory
pwd  # macOS/Linux - should show project directory
cd  # Windows - should show project directory
```

### Issue: "Database file not found"

**Solution:**
```bash
# Reinitialize database
python scripts/init_db.py

# Verify file exists
ls -la test_database.db  # macOS/Linux
dir test_database.db  # Windows
```

### Issue: "Ontology file not found"

**Solution:**
```bash
# Regenerate ontology
python scripts/setup_ontology.py

# Verify file exists
ls -la ontologies/business_domain.owl  # macOS/Linux
dir ontologies\business_domain.owl  # Windows
```

### Issue: Tests fail with import errors

**Solution:**
```bash
# Install project in editable mode
pip install -e .

# Run tests again
pytest tests/ -v
```

### Issue: Permission errors on macOS/Linux

**Solution:**
```bash
# Use --user flag or sudo
pip install --user -r requirements.txt

# Or fix permissions
sudo chown -R $USER:$USER .
```

## Next Steps

After successful setup:

1. **Explore Examples:**
   - `examples/quickstart.py` - Basic usage
   - `examples/full_system.py` - Complete system
   - `examples/multi_agent_demo.py` - Multi-agent coordination

2. **Read Documentation:**
   - [README.md](README.md) - Overview and features
   - [docs/architecture.md](docs/architecture.md) - System architecture
   - [docs/deployment.md](docs/deployment.md) - Production deployment
   - [docs/troubleshooting.md](docs/troubleshooting.md) - Common issues

3. **Customize Configuration:**
   - Edit `config/config.yaml` for your needs
   - Modify ontology in `ontologies/business_domain.owl`

4. **Develop:**
   - Read [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines
   - Create your own agents (see `src/agents/examples/`)

## Getting Help

- **Issues:** Open an issue on GitHub
- **Documentation:** Check `docs/` directory
- **Questions:** See [troubleshooting guide](docs/troubleshooting.md)

## Project Structure

```
ontology-mcp-self-healing/
├── .env                    # Environment variables (create this)
├── config/                 # Configuration files
├── docs/                   # Documentation
├── examples/               # Example scripts
├── logs/                   # Log files (created at runtime)
├── ontologies/             # OWL ontology files
├── scripts/                # Setup scripts
├── src/                    # Source code
├── tests/                  # Test suite
├── test_database.db        # Sample database (created by init_db.py)
├── README.md              # Main documentation
├── SETUP_GUIDE.md         # This file
├── CONTRIBUTING.md        # Contribution guidelines
├── LICENSE                # MIT License
└── requirements.txt       # Python dependencies
```

---

**Congratulations!** 🎉 You've successfully set up the Self-Healing Ontology MCP Agent System!

If you encounter any issues not covered here, please open an issue on GitHub.
