import sys
import os
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from docu_compress.ast_engine import ASTSkeletonizer
from docu_compress.token_reducer import TokenReducer
from docu_compress.metrics import metrics_tracker
from docu_compress.mcp_server import get_repo_skeleton, get_method_body, find_references
from docu_compress.orchestrator import OrchestrationEngine

class TestDocuCompressAI(unittest.TestCase):

    def setUp(self):
        self.skeletonizer = ASTSkeletonizer()
        self.python_code = '''
class PaymentProcessor:
    """Handles credit card and online payments."""
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.status = "INIT"

    def charge(self, amount: float, card_number: str) -> bool:
        """Processes credit card charge."""
        if amount <= 0:
            raise ValueError("Invalid amount")
        # Long processing logic loop
        for i in range(10):
            print("Verifying step", i)
        return True
'''

    def test_ast_skeletonizer(self):
        skeleton, metrics = self.skeletonizer.skeletonize(self.python_code, "payment.py")
        self.assertIn("class PaymentProcessor:", skeleton)
        self.assertIn("def charge(", skeleton)
        self.assertIn("[Body compressed:", skeleton)
        self.assertGreater(metrics["reduction_pct"], 20.0)

    def test_extract_method_body(self):
        body = self.skeletonizer.extract_method_body(self.python_code, "payment.py", "charge")
        self.assertIsNotNone(body)
        self.assertIn("def charge(", body)
        self.assertIn("Verifying step", body)

    def test_token_reduction_engine(self):
        tokens = TokenReducer.estimate_tokens(self.python_code)
        self.assertGreater(tokens, 30)

    def test_mcp_tools(self):
        skeleton = get_repo_skeleton(".")
        self.assertIn("DOCUCOMPRESS AI REPOSITORY SKELETON MAP", skeleton)

    def test_orchestrator_pipeline(self):
        orchestrator = OrchestrationEngine(".")
        result = orchestrator.run_pipeline_sync()
        self.assertIn("markdown_wiki", result)
        self.assertIn("sequenceDiagram", result["mermaid_diagram"])

if __name__ == "__main__":
    unittest.main()
