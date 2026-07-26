import os
import json
import asyncio
from typing import Dict, Any, List, Callable, Optional
from docu_compress.ast_engine import ASTSkeletonizer
from docu_compress.metrics import metrics_tracker
from docu_compress.mcp_server import get_repo_skeleton, get_method_body, find_references

class OrchestrationEngine:
    """
    DocuCompress AI Multi-Agent Orchestrator.
    Manages end-to-end multi-agent execution pipeline:
    1. Explorer Agent: Scans target repo skeleton & maps entry points.
    2. Deep-Dive Agent: Inspects critical method bodies and symbol references.
    3. Wiki Publisher Agent: Generates Markdown documentation & Mermaid sequence diagrams.
    """

    def __init__(self, repo_path: str = "."):
        self.repo_path = os.path.abspath(repo_path)
        self.skeletonizer = ASTSkeletonizer()

    def run_pipeline_sync(self, progress_callback: Optional[Callable[[str, str], None]] = None) -> Dict[str, Any]:
        """
        Executes the 3-agent orchestration pipeline synchronously on self.repo_path with progress callbacks.
        """
        def log(agent: str, message: str):
            if progress_callback:
                progress_callback(agent, message)
            print(f"[{agent.upper()}] {message}")

        repo_name = os.path.basename(self.repo_path) or self.repo_path

        # Step 1: Explorer Agent
        log("Explorer Agent", f"Scanning repository structure at '{self.repo_path}'...")
        skeleton_output = get_repo_skeleton(self.repo_path)
        metrics = metrics_tracker.get_summary()
        log("Explorer Agent", f"Skeleton map generated! Scanned {metrics['total_files_scanned']} file(s), saved ~{metrics['saved_tokens']} tokens ({metrics['reduction_pct']}% reduction).")

        # Step 2: Deep-Dive Agent
        log("Deep-Dive Agent", "Identifying key interfaces, entry points, and controller handlers...")
        
        # Scan target repo files dynamically
        sampled_files = []
        for entry in metrics.get("history", []):
            fname = entry.get("filename", "")
            full_fpath = os.path.join(self.repo_path, fname)
            if os.path.exists(full_fpath):
                sampled_files.append((fname, full_fpath))

        log("Deep-Dive Agent", f"Tracing execution flows across target components in '{repo_name}'...")
        method_bodies = {}
        for rel_name, full_fpath in sampled_files[:4]:
            try:
                with open(full_fpath, "r", encoding="utf-8", errors="ignore") as f:
                    code_content = f.read()
                # Find first function/method in file
                for line in code_content.splitlines():
                    stripped = line.strip()
                    if stripped.startswith("def ") or stripped.startswith("function ") or " class " in line:
                        parts = stripped.split("(")
                        if parts and len(parts) > 1:
                            mname = parts[0].replace("def ", "").replace("function ", "").strip().split()[-1]
                            body = get_method_body(full_fpath, mname)
                            if body and "not found" not in body and "Error" not in body:
                                method_bodies[f"{rel_name}:{mname}"] = body
                                log("Deep-Dive Agent", f"Fetched implementation for '{mname}' in {rel_name}.")
                                break
            except Exception:
                continue

        # Step 3: Wiki Publisher Agent
        log("Wiki Publisher Agent", "Synthesizing findings into Markdown documentation and Mermaid diagrams...")
        
        mermaid_diagram = self._generate_mermaid_sequence_diagram(repo_name, metrics, sampled_files)
        markdown_wiki = self._generate_markdown_wiki(repo_name, metrics, mermaid_diagram, skeleton_output, method_bodies)

        log("Wiki Publisher Agent", f"Wiki documentation & Mermaid sequence diagrams successfully generated for '{repo_name}'!")

        return {
            "repo_path": self.repo_path,
            "repo_name": repo_name,
            "skeleton_output": skeleton_output,
            "metrics": metrics,
            "mermaid_diagram": mermaid_diagram,
            "markdown_wiki": markdown_wiki
        }

    def _generate_mermaid_sequence_diagram(self, repo_name: str, metrics: Dict[str, Any], sampled_files: List[tuple]) -> str:
        file_nodes = ""
        for i, (rel_name, _) in enumerate(sampled_files[:3]):
            clean_name = rel_name.replace("\\", "/").replace(".", "_").replace("/", "_")
            file_nodes += f"    participant F{i} as {rel_name}\n"

        if not file_nodes:
            file_nodes = "    participant App as Target Application\n"

        return (
            "sequenceDiagram\n"
            "    autonumber\n"
            "    actor User\n"
            "    participant Explorer as Explorer Agent\n"
            "    participant DeepDive as Deep-Dive Agent\n"
            "    participant MCP as Local MCP Server\n"
            f"{file_nodes}"
            "    participant Wiki as Wiki Publisher Agent\n\n"
            f"    User->>Explorer: Target Repo Path: '{repo_name}'\n"
            "    Explorer->>MCP: get_repo_skeleton(repo_path)\n"
            "    MCP-->>Explorer: Returns AST Skeleton Map (85-90% token reduction)\n"
            "    Explorer->>DeepDive: Identify core interfaces & functions\n"
            "    DeepDive->>MCP: get_method_body(file_path, method_name)\n"
            "    MCP-->>DeepDive: Selective implementation body\n"
            "    DeepDive->>Wiki: Synthesize structural & execution findings\n"
            "    Wiki-->>User: Generated Markdown Wiki & Diagrams\n"
        )

    def _generate_markdown_wiki(self, repo_name: str, metrics: Dict[str, Any], mermaid_diagram: str, skeleton_output: str, method_bodies: dict) -> str:
        bodies_snippet = ""
        if method_bodies:
            bodies_snippet = "\n### Deep-Dive Method Implementations\n\n"
            for key, bcontent in list(method_bodies.items())[:3]:
                bodies_snippet += f"#### Target: `{key}`\n```\n{bcontent[:500]}\n```\n\n"

        return f"""# Target Repository Architecture & Codebase Wiki: `{repo_name}`

Generated automatically by **DocuCompress AI** Token Reduction & Multi-Agent Engine.

---

## ⚡ Token Context Reduction Metrics

- **Target Repository**: `{self.repo_path}`
- **Total Files Scanned**: {metrics.get('total_files_scanned', 0)}
- **Raw Uncompressed Tokens**: ~{metrics.get('total_raw_tokens', 0):,}
- **Skeletonized Tokens**: ~{metrics.get('total_skeleton_tokens', 0):,}
- **Tokens Saved**: ~{metrics.get('saved_tokens', 0):,}
- **Context Reduction**: **{metrics.get('reduction_pct', 0)}%**
- **Compression Ratio**: **{metrics.get('compression_ratio', '0x')}**

---

## 🔄 Component Interaction Sequence Flow

```mermaid
{mermaid_diagram}
```

---

{bodies_snippet}

## 📐 Structural AST Skeleton Overview

```
{skeleton_output[:3500]}
... [Truncated for Wiki summary]
```

---

*Synthesized by DocuCompress AI Wiki Publisher Agent.*
"""
