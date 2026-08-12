import argparse
import asyncio
import os
import sys

# Ensure UTF-8 stdout encoding for Windows console
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Ensure workspace root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from docu_compress.orchestrator import OrchestrationEngine

# Antigravity Agent & Gemini LLM Integration
try:
    from google.antigravity import Agent, LocalAgentConfig
    from google.antigravity.types import McpStdioServer
    HAS_ANTIGRAVITY_SDK = True
except ImportError:
    HAS_ANTIGRAVITY_SDK = False


async def run_gemini_agent(prompt: str):
    """
    MODE 1: Live Gemini LLM Agent
    Uses Google Gemini model via Antigravity SDK with MCP tools attached.
    """
    print("=========================================================")
    print("🤖 MODE 1: LIVE GEMINI LLM AGENT")
    print("=========================================================")
    print("⚡ Connecting to Gemini Model with MCP tools attached...\n")
    
    mcp_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mcp_server.py")
    config = LocalAgentConfig(
        system_instructions="""
        You are DocuCompress AI, an agent specializing in codebase exploration.
        1. Always start by using `get_repo_skeleton` to understand file structures with minimal tokens.
        2. Do NOT request full code files unless necessary.
        3. Use `get_method_body` ONLY when you need to inspect high-impact business logic.
        4. Synthesize your findings into a clear Markdown Architecture Summary with Mermaid sequence diagrams.
        """,
        mcp_servers=[
            McpStdioServer(
                name="docucompress_mcp",
                command=sys.executable,
                args=[mcp_script]
            )
        ]
    )

    chunks = []
    async with Agent(config) as agent:
        print(f"💬 Prompt: {prompt}\n")
        response = await agent.chat(prompt)
        
        async for chunk in response:
            chunk_str = str(chunk)
            chunks.append(chunk_str)
            print(chunk_str, end="", flush=True)
        print("\n")
    return "".join(chunks)


def run_local_orchestrator(repo_path: str = "."):
    """
    MODE 2: Deterministic Local Orchestrator Engine
    Runs local AST skeletonizer & multi-agent pipeline instantly without API keys or LLM token costs.
    """
    print("=========================================================")
    print("⚡ MODE 2: LOCAL ORCHESTRATOR ENGINE (NO API KEY REQUIRED)")
    print("=========================================================\n")

    orchestrator = OrchestrationEngine(repo_path)

    def progress_callback(agent: str, msg: str):
        print(f"🔹 [{agent}] {msg}")

    result = orchestrator.run_pipeline_sync(progress_callback)

    print("\n=========================================================")
    print("📊 FINAL TOKEN REDUCTION METRICS")
    print("=========================================================")
    metrics = result["metrics"]
    print(f"• Target Repository    : {result.get('repo_name', repo_path)}")
    print(f"• Total Files Scanned  : {metrics['total_files_scanned']}")
    print(f"• Raw Tokens Est.      : {metrics['total_raw_tokens']}")
    print(f"• Skeleton Tokens Est. : {metrics['total_skeleton_tokens']}")
    print(f"• Saved Tokens         : {metrics['saved_tokens']}")
    print(f"• Reduction Percentage : {metrics['reduction_pct']}%")
    print(f"• Compression Ratio    : {metrics['compression_ratio']}")
    print("=========================================================\n")

    print("📝 GENERATED WIKI SUMMARY SNIPPET:")
    print("---------------------------------------------------------")
    print("\n".join(result["markdown_wiki"].splitlines()[:25]))
    print("---------------------------------------------------------\n")


async def main():
    parser = argparse.ArgumentParser(description="DocuCompress AI — Agentic Code Compression Pipeline")
    parser.add_argument("--mode", choices=["local", "gemini"], default="local", 
                        help="Select mode: 'local' (Deterministic Engine, default) or 'gemini' (Live LLM Agent)")
    parser.add_argument("--path", default=".", help="Target repository directory path")
    args = parser.parse_args()

    if args.mode == "gemini":
        if not HAS_ANTIGRAVITY_SDK:
            print("⚠️ Antigravity SDK not found. Falling back to local orchestrator...")
            run_local_orchestrator(args.path)
        else:
            prompt = f"Explore the codebase at '{args.path}' and produce an architecture overview with Mermaid diagrams."
            await run_gemini_agent(prompt)
    else:
        run_local_orchestrator(args.path)


if __name__ == "__main__":
    asyncio.run(main())