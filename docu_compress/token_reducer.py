from typing import List, Dict, Any, Tuple
import math

class TokenReducer:
    """
    Token Reduction Engine for DocuCompress AI.
    Handles prompt prefix caching hints, state compression, and dynamic context trimming.
    """

    def __init__(self, max_context_tokens: int = 128000):
        self.max_context_tokens = max_context_tokens

    @staticmethod
    def estimate_tokens(text: str) -> int:
        """
        Calculates estimated token count using character/word heuristic (1 token ~ 3.8 chars).
        """
        if not text:
            return 0
        return max(1, math.ceil(len(text) / 3.8))

    def apply_prefix_caching(self, system_instructions: str, skeleton_map: str) -> Dict[str, Any]:
        """
        Formats static system instructions and skeleton maps with cache boundary markers
        so modern LLM inference APIs (Anthropic, Gemini, OpenAI) can cache system & skeleton prompt prefixes.
        """
        cached_prompt = (
            f"=== [CACHE_BOUNDARY: SYSTEM_PROMPT] ===\n"
            f"{system_instructions.strip()}\n\n"
            f"=== [CACHE_BOUNDARY: REPO_SKELETON] ===\n"
            f"{skeleton_map.strip()}\n\n"
            f"=== [CACHE_BOUNDARY: USER_CONTEXT_START] ===\n"
        )
        return {
            "cached_prompt": cached_prompt,
            "system_tokens": self.estimate_tokens(system_instructions),
            "skeleton_tokens": self.estimate_tokens(skeleton_map)
        }

    def compress_agent_state(self, conversation_history: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """
        Compresses intermediate agent conversation state by summarizing completed tool calls
        and stripping repetitive code outputs.
        """
        compressed = []
        for msg in conversation_history:
            role = msg.get("role")
            content = msg.get("content", "")
            
            # If tool response is large skeleton/code, compress it to summary line in conversation state
            if role == "tool" and len(content) > 1000:
                tokens = self.estimate_tokens(content)
                summary = f"[Tool Output: Compressed {len(content.splitlines())} lines (~{tokens} tokens)]\n" + "\n".join(content.splitlines()[:5]) + "\n..."
                compressed.append({"role": role, "content": summary})
            else:
                compressed.append(msg)
        return compressed
