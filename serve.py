from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
import os
ROOT=Path(__file__).resolve().parent
os.chdir(ROOT)
print('SENDA 02: http://127.0.0.1:8080')
ThreadingHTTPServer(('127.0.0.1',8080),SimpleHTTPRequestHandler).serve_forever()
