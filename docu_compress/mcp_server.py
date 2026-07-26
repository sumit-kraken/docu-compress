import os
import glob
import json
from typing import Dict, Any, List, Optional
from fastmcp import FastMCP

from docu_compress.ast_engine import ASTSkeletonizer
from docu_compress.metrics import metrics_tracker
from docu_compress.token_reducer import TokenReducer

# Create FastMCP server instance
mcp = FastMCP("DocuCompress AI MCP Server")
skeletonizer = ASTSkeletonizer()
token_reducer = TokenReducer()

def _should_ignore(path: str) -> bool:
    ignored = {"venv", ".git", "__pycache__", "node_modules", ".gemini", "dist", "build", ".idea", ".vscode"}
    parts = path.replace("\\", "/").split("/")
    return any(p in ignored for p in parts)

@mcp.tool()
def get_repo_skeleton(repo_path: str = ".") -> str:
    """
    Parses repository source files and returns class/method signatures ONLY (no method bodies).
    Dramatically reduces context size (85-90% token reduction).
    """
    repo_path = os.path.abspath(repo_path)
    if not os.path.exists(repo_path):
        return f"Error: Path '{repo_path}' does not exist."

    metrics_tracker.reset()
    supported_exts = {".py", ".ts", ".js", ".tsx", ".jsx", ".java", ".cpp", ".cs"}
    skeleton_map = []
    total_files = 0
    
    for root, dirs, files in os.walk(repo_path):
        if _should_ignore(root):
            continue
        for file in files:
            ext = os.path.splitext(file)[1].lower()
            if ext in supported_exts:
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, repo_path)
                
                try:
                    with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                    
                    skel, metrics = skeletonizer.skeletonize(content, rel_path)
                    metrics_tracker.record_scan(rel_path, metrics["raw_tokens_est"], metrics["skeleton_tokens_est"])
                    
                    skeleton_map.append(f"--- FILE: {rel_path} (Raw: ~{metrics['raw_tokens_est']} tokens -> Skeleton: ~{metrics['skeleton_tokens_est']} tokens | Reduction: {metrics['reduction_pct']}%) ---")
                    skeleton_map.append(skel)
                    skeleton_map.append("")
                    total_files += 1
                except Exception as e:
                    skeleton_map.append(f"--- FILE: {rel_path} (Error parsing: {str(e)}) ---")

    summary = metrics_tracker.get_summary()
    header = (
        f"=================================================================\n"
        f"⚡ DOCUCOMPRESS AI REPOSITORY SKELETON MAP\n"
        f"Files Scanned: {total_files} | Raw Tokens: ~{summary['total_raw_tokens']} -> Skeleton Tokens: ~{summary['total_skeleton_tokens']}\n"
        f"Overall Reduction: {summary['reduction_pct']}% | Compression Ratio: {summary['compression_ratio']}\n"
        f"=================================================================\n\n"
    )
    
    return header + "\n".join(skeleton_map)

@mcp.tool()
def get_code_skeleton(repo_path: str = ".") -> str:
    """
    Alias for get_repo_skeleton for compatibility.
    """
    return get_repo_skeleton(repo_path)

@mcp.tool()
def get_method_body(file_path: str, method_name: str) -> str:
    """
    Returns the exact implementation body for ONE target function or method.
    Use this sparingly after inspecting the repo skeleton.
    """
    if not os.path.exists(file_path):
        return f"Error: File '{file_path}' not found."

    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        body = skeletonizer.extract_method_body(content, file_path, method_name)
        if body:
            tokens = TokenReducer.estimate_tokens(body)
            metrics_tracker.record_method_fetch(method_name, tokens)
            return (
                f"=== METHOD BODY: {method_name} in {file_path} (~{tokens} tokens) ===\n"
                f"{body}"
            )
        else:
            return f"Method '{method_name}' not found in '{file_path}'."
    except Exception as e:
        return f"Error reading '{file_path}': {str(e)}"

@mcp.tool()
def find_references(repo_path: str, symbol_name: str) -> str:
    """
    Traces usage and references of a symbol (class, function, variable) across all repository files.
    """
    if not os.path.exists(repo_path):
        return f"Error: Path '{repo_path}' does not exist."

    matches = []
    for root, dirs, files in os.walk(repo_path):
        if _should_ignore(root):
            continue
        for file in files:
            full_path = os.path.join(root, file)
            rel_path = os.path.relpath(full_path, repo_path)
            try:
                with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                    for line_num, line in enumerate(f, 1):
                        if symbol_name in line:
                            matches.append(f"{rel_path}:{line_num}: {line.strip()}")
            except Exception:
                continue

    if not matches:
        return f"No references found for symbol '{symbol_name}'."
    
    header = f"Found {len(matches)} reference(s) to '{symbol_name}':\n"
    return header + "\n".join(matches[:50])

@mcp.tool()
def get_token_metrics() -> str:
    """
    Returns live Token Reduction Engine metrics as a JSON string.
    """
    return json.dumps(metrics_tracker.get_summary(), indent=2)

if __name__ == "__main__":
    mcp.run()
