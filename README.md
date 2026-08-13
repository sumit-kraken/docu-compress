# ⚡ DocuCompress AI

> **MCP AST Skeletonizer & Multi-Agent Architecture Orchestrator**  
> Dramatically compress codebases by **75% – 90%+** into token-efficient structural AST skeletons for LLMs, AI IDEs, and architectural documentation.

---

## 📌 Overview

**DocuCompress AI** is a lightweight, high-performance code context compression engine designed for developers and AI assistants (Claude, Gemini, Cursor, Antigravity). 

When feeding entire repositories into Large Language Models (LLMs), raw source code quickly exhausts context limits and inflates API costs. **DocuCompress AI** parses source files (`.py`, `.ts`, `.js`, `.tsx`, `.jsx`, `.java`, `.cpp`, `.cs`) and strips out internal implementation details, loop logic, and verbose function bodies while preserving 100% of:

* 📦 **Module Imports & Package Dependencies**
* 🏗️ **Class Definitions & Inheritance Hierarchies**
* 🧩 **Function & Method Signatures** (with parameter types and return type annotations)
* 💡 **Decorators, JSDocs, and Docstrings**
* 🌐 **Exported Routes & API Endpoints**

---

## 🚀 Key Advantages & Benefits

* 💰 **75% – 90%+ Token Context Savings**: Shrink ~8,000 token code files down to ~250 token structural skeletons without losing architectural context.
* ⚡ **Instant Multi-Agent Pipeline**: Automatically generates a 3-agent analysis:
  1. **Explorer Agent**: Maps repository structure & generates AST skeleton map.
  2. **Deep-Dive Agent**: Traces execution flows and selectively inspects high-impact method bodies.
  3. **Wiki Publisher Agent**: Synthesizes a markdown codebase wiki and live **Mermaid sequence diagrams**.
* 🌐 **Universal Repository Support**: Works on local workspace folders and public/private Git repositories (GitHub, GitLab, Bitbucket, and GitHub Enterprise / GHE).
* 🔌 **Native Model Context Protocol (MCP)**: Exposes standard MCP tools so AI assistants (Claude Desktop, Cursor, Antigravity) can query codebase skeletons dynamically over stdio/SSE.
* 🛡️ **Privacy & Security First**: Operates 100% locally without transmitting code to external servers in Local Mode. User-provided API keys are evaluated in-memory and never saved.

---

## ⚡ Execution Modes

| Feature | **⚡ Local AST Engine (Default)** | **🤖 Live Gemini LLM Agent** |
| :--- | :--- | :--- |
| **Engine** | Native Python AST parser & deterministic multi-agent rules | Live Gemini LLM via Antigravity SDK + FastMCP Tool Calling |
| **Speed** | **Instant (1–2 seconds)** | **Interactive LLM Reasoning (5–15 seconds)** |
| **API Key Required?** | ❌ **No API Key Required** (Zero cost) | 🔑 **Requires Gemini API Key** (Provide in Web UI or env) |
| **Best For** | Offline scans, fast context reduction, CI/CD pipelines | Deep semantic codebase exploration, custom architectural Q&A |

---

## 🛠️ Local Setup & Installation

### Prerequisites
* **Python**: 3.10 or higher
* **Git**: Installed and available on system `PATH`

### Step 1: Clone Repository & Create Virtual Environment
```bash
# Clone the repository
git clone https://github.com/sumit-kraken/docu-compress.git
cd docu-compress

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# On Windows (CMD):
.\venv\Scripts\activate.bat
# On Linux / macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Run the Web Dashboard
```bash
python app.py
```
Open your browser and navigate to:
👉 **`http://localhost:8000`**

From the Web UI, you can:
1. Paste local folder paths (e.g. `.`) or Git URLs (`https://github.com/user/repo` or `https://ghe.company.com/org/repo`).
2. Toggle between **⚡ Local AST Engine** and **🤖 Live Gemini LLM Agent** mode.
3. View side-by-side **AST Skeleton Diffs**, generated **Architecture Wikis**, and interactive **Mermaid sequence flow diagrams**.

---

## 💻 CLI Usage

You can also run DocuCompress directly from the terminal via `agent.py`:

```bash
# 1. Run Local Deterministic Pipeline (No API key needed)
python agent.py --mode local --path ./path/to/your/repo

# 2. Run on a remote GitHub / GHE repository URL
python agent.py --mode local --path https://github.com/fastapi/fastapi

# 3. Run Live Gemini LLM Agent Mode
# Set your API Key environment variable first
export GEMINI_API_KEY="your_gemini_api_key"   # Linux/macOS
set GEMINI_API_KEY=your_gemini_api_key        # Windows CMD

python agent.py --mode gemini --path ./path/to/your/repo
```

---

## 🔌 Connecting via Model Context Protocol (MCP)

DocuCompress AI includes a built-in **FastMCP** server ([mcp_server.py](file:///d:/Sumit/ai/docu-compres/mcp_server.py)) that exposes tools to AI desktop apps and IDEs.

### Exposed MCP Tools

| MCP Tool Name | Description |
| :--- | :--- |
| `get_repo_skeleton` | Scans a repository path/URL and returns class & method signatures ONLY (85-90% token reduction). |
| `get_method_body` | Retrieves the exact implementation body for ONE specific function or method. |
| `find_references` | Finds all invocation sites and references of a symbol across the codebase. |

---

### Integration Guide for AI Clients

#### 1. Claude Desktop
Add DocuCompress to your `claude_desktop_config.json`:

* **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
* **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "docu-compress": {
      "command": "python",
      "args": [
        "C:/path/to/docu-compress/mcp_server.py"
      ]
    }
  }
}
```

#### 2. Cursor / Antigravity / Windsurf IDE
Add an MCP server in your IDE Settings (`Features -> MCP` or `.cursor/mcp.json`):

* **Name**: `docu-compress`
* **Type**: `stdio`
* **Command**: `python` (or path to `venv/bin/python`)
* **Args**: `["/absolute/path/to/docu-compress/mcp_server.py"]`

Once connected, your AI assistant can invoke `get_repo_skeleton` to read compressed codebases in seconds!

---

## ☁️ Cloud Deployment (Render / Docker)

A production-ready [Dockerfile](file:///d:/Sumit/ai/docu-compres/Dockerfile) and [render.yaml](file:///d:/Sumit/ai/docu-compres/render.yaml) blueprint are included for 1-click cloud deployment.

### Deploying on Render:
1. Push your repository to GitHub / GitLab.
2. Go to [Render Dashboard](https://dashboard.render.com/) -> **New +** -> **Blueprint**.
3. Connect your repository. Render will automatically detect [render.yaml](file:///d:/Sumit/ai/docu-compres/render.yaml) and deploy the Docker container.

### Local Docker Build:
```bash
docker build -t docu-compress .
docker run -d -p 8000:8000 --name docu-compress-app docu-compress
```

---

## 🧪 Running Tests

To run the unit test suite:
```bash
python -m unittest discover tests
```

---

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.
