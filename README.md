# 🧠 Cognitive Bias Audit & Decision Rectification Agent Swarm

**Multi-language README available:**
- [English Version](README.md) (current)
- [中文版本](README_zh.md)

---

## 🌟 Core Features

- **🤖 Multi-Agent Collaboration**: Four specialized agents working collaboratively to cover the entire decision analysis process
- **🔍 Intelligent Bias Detection**: Built-in knowledge base of 30+ cognitive biases using Chain-of-Thought reasoning
- **⚔️ Adversarial Challenge**: Generates sharp logical challenge questions for deep stress testing
- **📊 Real-time Visualization**: Three-panel web UI displaying decision trees, conversation flows, and audit reports
- **💾 Data Persistence**: SQLite database stores complete session history and bias fingerprints
- **🐳 Containerized Deployment**: Full Docker support for both development and production environments

## 🏗️ System Architecture

### Agent Roles

| Agent       | Role                | Core Functionality           |
| ----------- | ------------------- | ---------------------------- |
| **Agent A** | Decision Tree Builder | Parses natural language, builds structured decision trees |
| **Agent B** | Bias Pattern Matcher | Detects cognitive biases, generates risk heatmaps |
| **Agent C** | Adversarial Challenger | Generates logical challenge questions for stress testing |
| **Agent D** | Meta-Cognition Recorder | Records decision evolution, generates audit reports |

### Technology Stack

- **Programming Language**: Python 3.11+
- **Multi-Agent Framework**: LangGraph (chosen for flexible state management and workflow control)
- **LLM Interface**: OpenAI API compatible interface
- **Frontend**: Streamlit Web UI
- **Database**: SQLite + SQLAlchemy
- **Configuration Management**: YAML + environment variables
- **Deployment**: Docker + Docker Compose

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- OpenAI API Key
- Docker (optional, for containerized deployment)

### Installation Steps

1. **Clone the Repository**

```bash
git clone https://github.com/DU-718/cogbias-swarm.git
cd cogbias-swarm
```

2. **Install Dependencies**

```bash
pip install -r requirements.txt
```

3. **Configure Environment Variables**

```bash
cp .env.example .env
# Edit .env file and set your OpenAI API Key
```

4. **Run the Application**

```bash
streamlit run src/ui/app.py
```

### Docker Deployment

```bash
# Build the image
docker build -t cogbias-swarm .

# Run the container
docker run -p 8501:8501 -e OPENAI_API_KEY=your_key cogbias-swarm

# Or use Docker Compose
docker-compose up -d
```

## 📖 User Guide

### Basic Workflow

1. **Input Decision Problem**: Enter your decision description in the Web UI
2. **Decision Tree Construction**: Agent A parses and builds structured decision trees
3. **Bias Detection**: Agent B scans the decision tree to identify cognitive biases
4. **Adversarial Challenge**: Agent C generates sharp logical challenge questions
5. **User Response**: Answer challenge questions to improve decision logic
6. **Iterative Optimization**: System updates decision tree based on responses, cycles detection
7. **Report Generation**: Final comprehensive cognitive audit report

### Web UI Interface

The system provides a three-panel interface:

- **Left Panel**: Decision tree visualization (JSON tree structure)
- **Center Panel**: Real-time conversation flow (with bias markers)
- **Right Panel**: Audit report preview and export

## 🔧 Configuration

### Main Configuration Items

Edit the `config.yaml` file for system configuration:

```yaml
# LLM Configuration
llm:
  model: "gpt-4-turbo-preview"
  temperature: 0.1
  max_tokens: 4096

# Agent Configuration
agents:
  agent_a:
    max_iterations: 5
  agent_b:
    bias_threshold: 0.7
  agent_c:
    challenge_intensity: "moderate"

# Workflow Configuration
workflow:
  max_iterations: 10
  timeout_minutes: 30
```

### Environment Variables

Important environment variables (configure in `.env`):

- `OPENAI_API_KEY`: OpenAI API key
- `OPENAI_BASE_URL`: API base URL (supports compatible interfaces)
- `LOG_LEVEL`: Logging level
- `DATABASE_URL`: Database connection string

## 🧪 Testing

Run unit tests:

```bash
pytest tests/ -v
```

Test coverage includes:

- Agent functionality tests
- Workflow state management tests
- Data persistence tests
- Error handling tests

## 📊 System Features Detailed

### Bias Detection Capabilities

The system includes 30+ common cognitive biases:

- **Confirmation Bias**: Tendency to seek information that confirms existing beliefs
- **Anchoring Bias**: Over-reliance on initial information
- **Overconfidence Bias**: Overestimating one's own knowledge and abilities
- **Sunk Cost Fallacy**: Continuing irrational investments due to previous investments
- **Groupthink**: Suppressing dissent to reach consensus
- **Hindsight Bias**: Believing outcomes were predictable after they occur

### Decision Tree Structure

Decision trees use a hierarchical structure:

```
Conclusion Node (Conclusion)
├── Premise Node (Facts/Assumptions)
│   ├── Evidence Node (Reasoning Type + Strength)
│   └── Evidence Node
└── Premise Node
    └── Evidence Node
```

### Audit Report Content

Final audit reports include:

1. **Decision Evolution Summary**: Initial vs final decision comparison
2. **Bias Exposure List**: Detected bias types and frequencies
3. **Personal Bias Fingerprint**: Analysis of user's cognitive weaknesses
4. **Improvement Recommendations**: Targeted decision improvement strategies

## 🔍 API Usage

The system provides programmatic API interfaces:

```python
from src.core.graph import WorkflowManager
import yaml

# Load configuration
with open('config.yaml') as f:
    config = yaml.safe_load(f)

# Create workflow manager
manager = WorkflowManager(config)

# Create new session
result = manager.create_session("Should I invest in this project?")

# Process user response
response_result = manager.submit_response(
    session_id=result['session_id'],
    response_text="My response content",
    question_id="question_123"
)

# Generate audit report
report = manager.generate_audit_report(result['session_id'])
```

## 🐛 Troubleshooting

### Common Issues

1. **LLM Call Failures**
   - Check API Key configuration
   - Verify network connection
   - Check log files
2. **Database Connection Errors**
   - Check database file permissions
   - Verify database path configuration
3. **Web UI Access Issues**
   - Check port availability
   - Verify Streamlit configuration

### Logs

Log file location: `./logs/cogbias.log`

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the project
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

### Development Standards

- Follow PEP 8 code style
- Write unit tests for new features
- Update relevant documentation
- Use type annotations

## 📄 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Thanks to the LangChain team for the excellent framework
- Thanks to research achievements in cognitive science
- Thanks to all contributors and users

## 📞 Contact

For questions or suggestions, please contact via:

- Project Issues: [GitHub Issues]
- Documentation: [Project Wiki]

***

**🧠 Make better decisions by identifying cognitive biases**