import sys
print(f"Python: {sys.version}")

import a2wsgi
print(f"a2wsgi: {a2wsgi.__version__}")

import uvicorn
print(f"uvicorn: {uvicorn.__version__}")

import fastapi
print(f"fastapi: {fastapi.__version__}")
