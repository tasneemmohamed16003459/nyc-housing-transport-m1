# Contributor: Abdelrahman - Vercel entry point: exposes the Flask server that Dash creates.
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import server as app   # Vercel looks for a WSGI object called "app"
