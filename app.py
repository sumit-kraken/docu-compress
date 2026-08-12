import os
import sys
import json
import http.server
import socketserver
import urllib.parse
from typing import Dict, Any

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from docu_compress.ast_engine import ASTSkeletonizer
from docu_compress.metrics import metrics_tracker
from docu_compress.mcp_server import get_repo_skeleton, get_method_body, find_references
from docu_compress.orchestrator import OrchestrationEngine

PORT = int(os.environ.get("PORT", 8000))
WEB_DIR = os.path.join(os.path.dirname(__file__), "web")

skeletonizer = ASTSkeletonizer()

from docu_compress.utils import resolve_repo_path

class DocuCompressHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=WEB_DIR, **kwargs)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/api/metrics":
            self.send_json_response(metrics_tracker.get_summary())
        elif parsed.path == "/api/scan":
            query = urllib.parse.parse_qs(parsed.query)
            raw_path = query.get("path", ["."])[0]
            temp_cleanup = None
            try:
                repo_path, temp_cleanup, repo_name = resolve_repo_path(raw_path)
                skeleton = get_repo_skeleton(repo_path)
                summary = metrics_tracker.get_summary()
                self.send_json_response({
                    "skeleton": skeleton,
                    "summary": summary,
                    "repo_name": repo_name
                })
            except Exception as err:
                self.send_json_response({"error": str(err)}, status=400)
            finally:
                if temp_cleanup and os.path.exists(temp_cleanup):
                    shutil.rmtree(temp_cleanup, ignore_errors=True)
        else:
            super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length).decode('utf-8')
        
        try:
            data = json.loads(body) if body else {}
        except Exception:
            data = {}

        if parsed.path == "/api/skeletonize_code":
            code = data.get("code", "")
            filename = data.get("filename", "example.py")
            skel, meta = skeletonizer.skeletonize(code, filename)
            self.send_json_response({
                "skeleton": skel,
                "metadata": meta
            })
        elif parsed.path == "/api/run_pipeline":
            raw_path = data.get("path", ".")
            logs = []
            
            def log_callback(agent, msg):
                logs.append({"agent": agent, "message": msg})

            temp_cleanup = None
            try:
                repo_path, temp_cleanup, repo_name = resolve_repo_path(raw_path)
                orchestrator = OrchestrationEngine(repo_path)
                res = orchestrator.run_pipeline_sync(log_callback)
                res["logs"] = logs
                res["repo_name"] = repo_name
                self.send_json_response(res)
            except Exception as err:
                self.send_json_response({"error": str(err), "logs": logs}, status=400)
            finally:
                if temp_cleanup and os.path.exists(temp_cleanup):
                    shutil.rmtree(temp_cleanup, ignore_errors=True)
        else:
            self.send_error(404, "Not Found")

    def send_json_response(self, data: Dict[str, Any], status: int = 200):
        response_bytes = json.dumps(data).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Content-Length', str(len(response_bytes)))
        self.end_headers()
        self.wfile.write(response_bytes)

def run_server():
    os.makedirs(WEB_DIR, exist_ok=True)
    with socketserver.TCPServer(("", PORT), DocuCompressHandler) as httpd:
        print(f"⚡ DocuCompress AI Dashboard running at http://localhost:{PORT}")
        httpd.serve_forever()

if __name__ == "__main__":
    run_server()
