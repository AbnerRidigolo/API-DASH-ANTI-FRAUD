import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'windows'))

# Usa SQLite em /tmp no Vercel (sem persistência entre requests, mas funciona para /docs)
os.environ.setdefault("DATABASE_URL", "sqlite:////tmp/antifraude.db")

from app import app
