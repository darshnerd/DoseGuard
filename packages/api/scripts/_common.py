import sqlite3
import sys
from pathlib import Path

API = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(API))
from app.normalize import normalize

DB = str(API / "doseguard.db")
SOURCES = API / "app" / "data" / "sources"

SEV_NAME = {"major": "severe", "moderate": "moderate", "minor": "low"}
SEV_RANK = {"contraindicated": 0, "severe": 1, "major": 1, "moderate": 2, "minor": 3, "low": 3}

def connect():
    c = sqlite3.connect(DB); 
    c.execute("PRAGMA synchronous=OFF"); 
    c.execute("PRAGMA journal_mode=WAL"); 
    return c

def worse(a, b):
    return a if SEV_RANK.get(a, 9) <= SEV_RANK.get(b, 9) else b
