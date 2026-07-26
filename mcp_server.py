import sys
import os

# Ensure workspace root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from docu_compress.mcp_server import mcp

if __name__ == "__main__":
    mcp.run()