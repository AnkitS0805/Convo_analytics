# 🤖 Multi-Agent Analytics Platform

<div align="center">

**An intelligent, conversational analytics system powered by AWS Bedrock and LangGraph**

[![Python 3.13](https://img.shields.io/badge/python-3.13-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.29+-red.svg)](https://streamlit.io)
[![LangGraph](https://img.shields.io/badge/LangGraph-Latest-green.svg)](https://github.com/langchain-ai/langgraph)
[![AWS Bedrock](https://img.shields.io/badge/AWS-Bedrock-orange.svg)](https://aws.amazon.com/bedrock/)

</div>

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Key Features](#-key-features)
- [Architecture](#-architecture)
- [Project Structure](#-project-structure)
- [Installation](#-installation)
- [Usage](#-usage)
- [How It Works](#-how-it-works)
- [Configuration](#-configuration)
- [Examples](#-examples)
- [Troubleshooting](#-troubleshooting)
- [Contributing](#-contributing)

---

## 🎯 Overview

The **Multi-Agent Analytics Platform** is an enterprise-grade, intelligent data analytics system that allows users to ask questions in natural language and receive comprehensive insights with visualizations. Built using a **multi-agent architecture** orchestrated by **LangGraph**, it leverages **AWS Bedrock** (Nova models) for natural language understanding and generation.

### What Makes It Special?

- **🧠 Intelligent Routing**: Automatically determines if your query needs database access or can be answered directly
- **📊 SQL Generation**: Converts natural language to optimized SQL queries with schema awareness
- **🔄 Auto-Correction**: Automatically fixes SQL errors and retries failed queries
- **📈 Rich Insights**: Provides executive summaries, key findings, detailed analysis, and actionable recommendations
- **📉 Visualizations**: Generates beautiful Vega-Lite charts automatically
- **👀 Full Transparency**: See every agent's decision, timing, and output in real-time
- **💬 Conversation History**: Review all past queries and their execution traces

---

## ✨ Key Features

### 🎭 Multi-Agent System

| Agent | Role | Description |
|-------|------|-------------|
| **Router Agent** | Query Classification | Determines if query needs database access or can be answered directly |
| **SQL Planner Agent** | SQL Generation | Converts natural language to optimized, schema-aware SQL queries |
| **SQL Executor** | Query Execution | Runs SQL queries with error handling and auto-correction |
| **Synthesizer Agent** | Insight Generation | Transforms raw data into actionable business insights |
| **Non-Data QA Agent** | General Responses | Handles greetings and system capability questions |

### 🔧 Technical Features

- ✅ **JSON Repair**: Automatic fixing of malformed LLM responses
- ✅ **Schema Validation**: Prevents column hallucination with explicit relationship mapping
- ✅ **Error Recovery**: Automatic SQL correction with retry logic
- ✅ **Comprehensive Logging**: INFO/DEBUG/WARNING/ERROR logs for full observability
- ✅ **Beautiful UI**: Professional Streamlit interface with agent trace visualization
- ✅ **Chart Generation**: Automatic Vega-Lite chart specs with actual query data

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Streamlit UI Layer                       │
│  - Conversation History  - Agent Traces  - Visualizations   │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              LangGraph Orchestrator (State Machine)         │
│  - State Management  - Agent Coordination  - Flow Control   │
└─┬──────┬─────────┬──────────┬──────────┬────────────────────┘
  │      │         │          │          │
  ▼      ▼         ▼          ▼          ▼
┌────┐┌─────┐ ┌────────┐ ┌────────┐ ┌──────────┐
│    ││     │ │  SQL   │ │  SQL   │ │Synthe-   │
│Rtr ││Non  │ │Planner │ │Executor│ │sizer     │
│    ││Data │ │        │ │        │ │          │
└────┘└─────┘ └────────┘ └────────┘ └──────────┘
  │      │         │          │          │
  └──────┴─────────┴──────────┴──────────┘
                   │
                   ▼
        ┌──────────────────────┐
        │   AWS Bedrock LLMs   │
        │  - Nova Lite v1.0    │
        │  - Nova Pro v1.0     │
        │  - Titan Embed v2    │
        └──────────────────────┘
                   │
                   ▼
        ┌──────────────────────┐
        │  SQLite Database     │
        │  (AdventureWorks)    │
        └──────────────────────┘
```

---

## 📁 Project Structure

```
multi_agent_analytics/
│
├── src/
│   └── app/
│       ├── agents/              # Multi-agent system components
│       │   ├── router_agent.py           # Query routing with confidence scoring
│       │   ├── sql_planner_agent.py      # Natural language → SQL conversion
│       │   ├── synthesizer_agent.py      # Data → Insights transformation
│       │   └── non_data_agent.py         # General Q&A handler
│       │
│       ├── graph/               # LangGraph orchestration
│       │   ├── builder.py                # Graph construction and node logic
│       │   └── state.py                  # State definitions (AgentStep, TurnTrace)
│       │
│       ├── db/                  # Database layer
│       │   ├── engine.py                 # SQLAlchemy engine setup
│       │   ├── schema_introspector.py    # Schema metadata extraction
│       │   └── sql_runner.py             # SQL execution with validation
│       │
│       ├── llm/                 # LLM integration
│       │   └── bedrock_client.py         # AWS Bedrock client with retry & repair
│       │
│       ├── ui/                  # Streamlit interface
│       │   ├── streamlit_app.py          # Main application entry point
│       │   └── agent_trace_ui.py         # Agent visualization components
│       │
│       ├── prompts/             # Jinja2 prompt templates (if any)
│       │
│       ├── etl/                 # Data pipeline (not used in runtime)
│       │   └── load_csv_to_db.py         # CSV → SQLite loader
│       │
│       ├── constants.py         # Application constants
│       └── logging_config.py    # Centralized logging setup
│
├── data/                        # Database and data files
│   ├── adventureworks.db                 # SQLite database (generated)
│   └── archive/                          # Source CSV files (optional)
│
├── tests/                       # Unit tests
│   └── test_*.py                         # Test files mirroring src structure
│
├── .env.example                 # Environment variables template
├── .gitignore                   # Git ignore rules
├── pyproject.toml               # Poetry dependency management
└── README.md                    # This file
```

### Key Files Explained

| File | Purpose |
|------|----------|
| `streamlit_app.py` | Main UI with conversation history and agent traces |
| `builder.py` | LangGraph orchestrator coordinating all agents |
| `router_agent.py` | Classifies queries as "data" or "non_data" with confidence |
| `sql_planner_agent.py` | Generates SQL with schema awareness and error prevention |
| `synthesizer_agent.py` | Creates rich insights from query results |
| `bedrock_client.py` | AWS Bedrock integration with JSON repair and retry logic |
| `state.py` | Data structures for agent steps and execution traces |
| `agent_trace_ui.py` | Reusable UI components for agent visualization |

---

## 🚀 Installation

### Prerequisites

- **Python 3.13+** ([Download](https://www.python.org/downloads/))
- **AWS Account** with Bedrock access ([Setup Guide](https://docs.aws.amazon.com/bedrock/latest/userguide/getting-started.html))
- **Git** ([Download](https://git-scm.com/downloads))

### Step 1: Clone the Repository

```bash
git clone https://github.com/yourusername/multi_agent_analytics.git
cd multi_agent_analytics
```

### Step 2: Create Virtual Environment

```bash
# Create virtual environment
python3.13 -m venv .venv

# Activate virtual environment
# On Linux/Mac:
source .venv/bin/activate

# On Windows:
# .venv\Scripts\activate
```

### Step 3: Install Dependencies

```bash
# Install the package in editable mode
pip install -e .
```

This will install all dependencies defined in `pyproject.toml`.

### Step 4: Configure Environment Variables

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env with your credentials
nano .env  # or use your preferred editor
```

**Required Environment Variables:**

```bash
# AWS Bedrock Configuration
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_access_key_here
AWS_SECRET_ACCESS_KEY=your_secret_key_here
AWS_SESSION_TOKEN=your_session_token_here  # If using temporary credentials

# Bedrock Model IDs
BEDROCK_LLM_MODEL_ID=us.amazon.nova-lite-v1:0
BEDROCK_EMBEDDING_MODEL_ID=amazon.titan-embed-text-v2:0

# Database
DATABASE_URL=sqlite:///data/adventureworks.db

# Application Settings
MAX_PREVIEW_ROWS=100
SQL_TIMEOUT_SECONDS=30
```

### Step 5: Verify Installation

```bash
# Check Python version
python --version  # Should be 3.13+

# Verify dependencies
pip list | grep streamlit
pip list | grep langgraph
```

---

## 🎮 Usage

### Running the Application

```bash
# Ensure virtual environment is activated
source .venv/bin/activate  # Linux/Mac
# or
# .venv\Scripts\activate  # Windows

# Run the Streamlit app
streamlit run src/app/ui/streamlit_app.py
```

**Access the application:**
- **Local URL**: http://localhost:8501
- **Network URL**: http://YOUR_IP:8501 (for remote access)

### Stopping the Application

```bash
# Press Ctrl+C in the terminal
```

---

## 💡 How It Works

### Query Processing Flow

```
1. User enters question → "What are the top 5 product categories by sales?"
                          ↓
2. Router Agent → Classifies as "data" query (needs database)
                          ↓
3. SQL Planner → Generates optimized SQL with proper JOINs
                          ↓
4. SQL Executor → Runs query, auto-corrects if errors occur
                          ↓
5. Synthesizer → Creates insights: summary, findings, recommendations, chart
                          ↓
6. UI Display → Shows results with visualization and agent traces
```

### Agent Execution Example

**User Query:** `"Show me customer trends by region"`

**Step 1 - Router Agent:**
```
✅ Route: data
📊 Confidence: high
💡 Intent: "Analyze customer distribution across regions"
⏱️ Duration: 2.3s
```

**Step 2 - SQL Planner:**
```sql
SELECT t.Region, COUNT(DISTINCT s.CustomerKey) AS CustomerCount
FROM AdventureWorks_Sales_2015 s
JOIN AdventureWorks_Territories t ON s.TerritoryKey = t.SalesTerritoryKey
GROUP BY t.Region
ORDER BY CustomerCount DESC
```
```
✅ Tables: Sales_2015, Territories
📊 Metrics: Region, CustomerCount
📈 Confidence: high
⏱️ Duration: 3.1s
```

**Step 3 - SQL Executor:**
```
✅ Status: SUCCESS
📊 Rows: 6
📋 Columns: 2
⏱️ Duration: 0.8s
```

**Step 4 - Synthesizer:**
```
📊 Executive Summary:
   "Analysis reveals North America leads with 1,234 customers (45% of total),
    followed by Europe at 876 customers. Strong concentration in developed markets."

🔍 Key Findings:
   • North America: 1,234 customers (45%)
   • Europe: 876 customers (32%)
   • Pacific: 623 customers (23%)

📈 Detailed Analysis:
   "Regional distribution shows clear market dominance in North America..."

💡 Recommendations:
   1. Expand marketing in Pacific region (growth opportunity)
   2. Maintain strong presence in North America
   3. Investigate European conversion rates

📊 Chart: Bar chart showing regional distribution
⏱️ Duration: 4.2s
```

---

## ⚙️ Configuration

### Environment Variables

See `.env.example` for all available options:

| Variable | Description | Default |
|----------|-------------|----------|
| `AWS_REGION` | AWS region for Bedrock | `us-east-1` |
| `AWS_ACCESS_KEY_ID` | AWS access key | Required |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key | Required |
| `BEDROCK_LLM_MODEL_ID` | LLM model to use | `us.amazon.nova-lite-v1:0` |
| `DATABASE_URL` | SQLite database path | `sqlite:///data/adventureworks.db` |
| `MAX_PREVIEW_ROWS` | Max rows in query preview | `100` |
| `SQL_TIMEOUT_SECONDS` | SQL execution timeout | `30` |

### Customizing Prompts

Prompts are defined in each agent file:
- **Router**: `src/app/agents/router_agent.py` (line ~45)
- **SQL Planner**: `src/app/agents/sql_planner_agent.py` (line ~47)
- **Synthesizer**: `src/app/agents/synthesizer_agent.py` (line ~59)

---

## 📚 Examples

### Data Analytics Queries

```
✅ "What are the top 5 product categories by total sales?"
✅ "Show me customer trends by region"
✅ "Which products have the highest profit margins?"
✅ "Compare sales across 2015, 2016, and 2017"
✅ "What are the most popular product subcategories?"
```

### General Queries

```
✅ "Hello! What can you help me with?"
✅ "How does this system work?"
✅ "What kind of questions can I ask?"
```

### Expected Output

For **"What are the top 5 product categories by total sales?"**:

- **Executive Summary**: 2-3 sentence overview
- **Key Findings**: 3-5 bullet points with actual numbers
- **Detailed Analysis**: Comprehensive paragraph
- **Recommendations**: 2-4 actionable insights
- **Visualization**: Bar chart showing categories vs sales
- **Raw Data Table**: Actual query results

---

## 🐛 Troubleshooting

### Issue: "System Not Ready" Error

**Cause**: Missing or incorrect AWS credentials

**Solution**:
```bash
# Check .env file has correct values
cat .env | grep AWS

# Verify Bedrock access
aws bedrock list-foundation-models --region us-east-1
```

### Issue: "No such column" SQL Error

**Cause**: LLM hallucinating non-existent columns

**Solution**: The system has auto-correction. If it persists:
- Check `src/app/agents/sql_planner_agent.py` has correct schema relationships
- Verify database schema: `sqlite3 data/adventureworks.db ".schema"`

### Issue: Chart Not Rendering

**Cause**: Missing `data` property in Vega-Lite spec

**Solution**: Already fixed! Charts now include actual query data.

### Issue: JSON Parsing Errors

**Cause**: Malformed JSON from LLM

**Solution**: Automatic JSON repair is enabled. Check logs for:
```
INFO | JSON repair: added closing quote before brace
INFO | JSON repair successful, re-parsing
```

### Enable Debug Logging

```python
# In src/app/logging_config.py, change:
logging.basicConfig(level=logging.DEBUG)  # Instead of INFO
```

---

## 🤝 Contributing

### Development Setup

```bash
# Clone and setup
git clone https://github.com/yourusername/multi_agent_analytics.git
cd multi_agent_analytics
python3.13 -m venv .venv
source .venv/bin/activate
pip install -e .

# Install development dependencies
pip install pytest ruff mypy

# Run tests
pytest tests/

# Run linting
ruff check src/

# Run type checking
mypy src/
```

### Code Style

- **PEP 8** compliance
- **Type hints** for all functions
- **Docstrings** in Google format
- **Ruff** for linting
- **Comments** for complex logic

### Pull Request Process

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes with tests
4. Run linting and tests
5. Commit with clear messages (`git commit -m 'Add amazing feature'`)
6. Push to your fork (`git push origin feature/amazing-feature`)
7. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## 🙏 Acknowledgments

- **AWS Bedrock** for powerful LLM capabilities
- **LangGraph** for agent orchestration framework
- **Streamlit** for beautiful UI framework
- **AdventureWorks** sample database

---

## 📞 Support

For issues, questions, or contributions:
- **GitHub Issues**: [Create an issue](https://github.com/yourusername/multi_agent_analytics/issues)
- **Documentation**: See files in this repository

---

<div align="center">

**Built with ❤️ using AWS Bedrock, LangGraph, and Streamlit**

⭐ Star this repo if you find it helpful!

</div>
