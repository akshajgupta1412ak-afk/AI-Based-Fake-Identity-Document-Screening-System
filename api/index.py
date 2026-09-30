"""
Vercel Serverless Function Entry Point
Imports the Flask application WSGI instance and exposes it for Vercel.
"""

import sys
import os

# Add root project directory to sys.path so modules and packages resolve cleanly
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set VERCEL environment flag if not present
os.environ.setdefault('VERCEL', '1')

# Import Flask app instance
from app import app

# Vercel looks for the WSGI application callable named 'app'
