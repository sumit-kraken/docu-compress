import time
from typing import Dict, Any, List

class TokenMetricsTracker:
    """
    Tracks cumulative token reduction metrics across DocuCompress AI agent calls and MCP tool invocations.
    """

    def __init__(self):
        self.reset()

    def reset(self):
        self.total_files_scanned = 0
        self.total_raw_tokens = 0
        self.total_skeleton_tokens = 0
        self.selective_method_fetches = 0
        self.method_tokens_fetched = 0
        self.history: List[Dict[str, Any]] = []

    def record_scan(self, filename: str, raw_tokens: int, skeleton_tokens: int):
        self.total_files_scanned += 1
        self.total_raw_tokens += raw_tokens
        self.total_skeleton_tokens += skeleton_tokens

        saved = max(0, raw_tokens - skeleton_tokens)
        pct = round((saved / raw_tokens) * 100, 1) if raw_tokens > 0 else 0.0

        entry = {
            "timestamp": time.time(),
            "filename": filename,
            "raw_tokens": raw_tokens,
            "skeleton_tokens": skeleton_tokens,
            "saved_tokens": saved,
            "reduction_pct": pct
        }
        self.history.append(entry)
        return entry

    def record_method_fetch(self, method_name: str, method_tokens: int):
        self.selective_method_fetches += 1
        self.method_tokens_fetched += method_tokens

    def get_summary(self) -> Dict[str, Any]:
        total_consumed = self.total_skeleton_tokens + self.method_tokens_fetched
        saved_tokens = max(0, self.total_raw_tokens - total_consumed)
        reduction_pct = round((saved_tokens / self.total_raw_tokens) * 100, 1) if self.total_raw_tokens > 0 else 0.0

        return {
            "total_files_scanned": self.total_files_scanned,
            "total_raw_tokens": self.total_raw_tokens,
            "total_skeleton_tokens": self.total_skeleton_tokens,
            "selective_method_fetches": self.selective_method_fetches,
            "method_tokens_fetched": self.method_tokens_fetched,
            "total_consumed_tokens": total_consumed,
            "saved_tokens": saved_tokens,
            "reduction_pct": reduction_pct,
            "compression_ratio": f"{round(self.total_raw_tokens / max(1, total_consumed), 1)}x",
            "history": self.history[-20:] # Last 20 operations
        }

# Global metrics singleton
metrics_tracker = TokenMetricsTracker()
