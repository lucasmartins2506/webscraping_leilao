import io
import json
import os
import time
import urllib.parse
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import pandas as pd

from kwara_scraper import (
    EXCEL_COLUMNS,
    export_to_excel,
    scrape_kwara,
    slugify_filename,
)

BASE_DIR = Path(__file__).resolve().parent
TEMPLATE_PATH = BASE_DIR / "templates" / "index.html"


class KwaraWebHandler(BaseHTTPRequestHandler):
    def log_message(self, format: str, *args) -> None:
        # Log mais limpo no terminal
        print(f"[Web] {self.address_string()} - {format % args}")

    def _send_json(self, payload: dict, status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        route = parsed.path
        params = urllib.parse.parse_qs(parsed.query)

        if route in ("/", "/index.html"):
            if not TEMPLATE_PATH.exists():
                self._send_json({"error": "Arquivo templates/index.html não encontrado."}, status=404)
                return
            content = TEMPLATE_PATH.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)
            return

        if route == "/api/search":
            query = (params.get("q", [""])[0] or "").strip()
            force_pw = params.get("playwright", ["0"])[0] == "1"

            if not query:
                self._send_json({"error": "Informe um termo para pesquisar."}, status=400)
                return

            t0 = time.perf_counter()
            try:
                items, total_pages = scrape_kwara(
                    query,
                    force_playwright=force_pw,
                    include_metadata=True,
                )
            except Exception as e:
                self._send_json({"error": f"Falha ao consultar a Kwara: {e}"}, status=500)
                return

            elapsed = round(time.perf_counter() - t0, 2)
            excel_filename = f"{slugify_filename(query)}_leilao.xlsx"
            excel_path = BASE_DIR / excel_filename

            saved_on_disk = False
            if items:
                try:
                    export_to_excel(items, str(excel_path))
                    saved_on_disk = True
                except Exception as e:
                    print(f"[Aviso] Não foi possível salvar '{excel_filename}' no disco: {e}")

            self._send_json({
                "query": query,
                "total_items": len(items),
                "total_pages": total_pages,
                "elapsed_seconds": elapsed,
                "excel_file": excel_filename,
                "saved_on_disk": saved_on_disk,
                "items": items,
            })
            return

        if route == "/api/download":
            file_param = (params.get("file", [""])[0] or "").strip()
            safe_name = os.path.basename(file_param)
            target_path = BASE_DIR / safe_name

            if safe_name and target_path.exists() and target_path.suffix.lower() == ".xlsx":
                data = target_path.read_bytes()
                self.send_response(200)
                self.send_header(
                    "Content-Type",
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
                self.send_header("Content-Disposition", f'attachment; filename="{safe_name}"')
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)
                return

            self._send_json({"error": "Arquivo Excel não encontrado. Faça uma pesquisa primeiro."}, status=404)
            return

        self._send_json({"error": "Rota não encontrada."}, status=404)


def start_server(port: int = 8000, open_browser: bool = True) -> None:
    url = f"http://localhost:{port}"
    server = ThreadingHTTPServer(("127.0.0.1", port), KwaraWebHandler)
    print("=" * 62)
    print(f" Interface Web Kwara Search iniciada em: {url}")
    print(" Pressione Ctrl+C no terminal quando quiser encerrar o servidor.")
    print("=" * 62)

    if open_browser:
        try:
            webbrowser.open(url)
        except Exception:
            pass

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nEncerrando servidor web...")
        server.server_close()


if __name__ == "__main__":
    start_server(port=8000, open_browser=True)

