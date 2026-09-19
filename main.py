import json
import mimetypes
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qsl, urlparse

from jinja2 import Environment, FileSystemLoader, select_autoescape


BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "storage" / "data.json"
env = Environment(
    loader=FileSystemLoader(BASE_DIR),
    autoescape=select_autoescape(["html"]),
)


class HttpHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = urlparse(self.path).path
        if path in ("/", "/index.html"):
            self.send_file("index.html")
        elif path in ("/message", "/message.html"):
            self.send_file("message.html")
        elif path in ("/style.css", "/logo.png"):
            self.send_file(path.lstrip("/"))
        elif path == "/read":
            with DATA_FILE.open(encoding="utf-8") as file:
                messages = json.load(file)
            template = env.get_template("read.html")
            content = template.render(messages=messages).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(content)
        else:
            self.send_file("error.html", 404)

    def do_POST(self):
        if urlparse(self.path).path != "/message":
            self.send_file("error.html", 404)
            return

        data = self.rfile.read(int(self.headers["Content-Length"]))
        message = dict(parse_qsl(data.decode("utf-8"), keep_blank_values=True))
        timestamp = str(datetime.now())
        with DATA_FILE.open(encoding="utf-8") as file:
            messages = json.load(file)
        messages[timestamp] = message
        with DATA_FILE.open("w", encoding="utf-8") as file:
            json.dump(messages, file, ensure_ascii=False, indent=2)

        self.send_response(303)
        self.send_header("Location", "/read")
        self.end_headers()

    def send_file(self, filename, status=200):
        content = (BASE_DIR / filename).read_bytes()
        content_type = mimetypes.guess_type(filename)[0]
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.end_headers()
        self.wfile.write(content)


if __name__ == "__main__":
    DATA_FILE.parent.mkdir(exist_ok=True)
    if not DATA_FILE.exists():
        DATA_FILE.write_text("{}", encoding="utf-8")
    server = HTTPServer(("0.0.0.0", 3000), HttpHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
