"""
Vercel Serverless Function Entry Point
Imports the Flask application WSGI instance and exposes it for Vercel.
Includes automatic diagnostic error reporting for serverless cold-starts.
"""

import sys
import os
import traceback

# Add root project directory to sys.path so modules and packages resolve cleanly
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

# Set VERCEL environment flag if not present
os.environ.setdefault('VERCEL', '1')

import urllib.parse

try:
    from app import app

    class VercelQueryPathMiddleware:
        def __init__(self, wsgi_app):
            self.wsgi_app = wsgi_app

        def __call__(self, environ, start_response):
            query_string = environ.get('QUERY_STRING', '')
            if '__url=' in query_string:
                parsed = urllib.parse.parse_qs(query_string)
                if '__url' in parsed and parsed['__url']:
                    real_path = parsed['__url'][0]
                    if not real_path.startswith('/'):
                        real_path = '/' + real_path
                    environ['PATH_INFO'] = real_path
                    # Clean up __url so application query parameters stay clean
                    clean_params = [p for p in query_string.split('&') if not p.startswith('__url=')]
                    environ['QUERY_STRING'] = '&'.join(clean_params)
            return self.wsgi_app(environ, start_response)

    app.wsgi_app = VercelQueryPathMiddleware(app.wsgi_app)
except Exception as e:
    err_trace = traceback.format_exc()
    print("FATAL SERVERLESS STARTUP ERROR:", err_trace, flush=True)
    from flask import Flask
    app = Flask(__name__)

    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def catch_all_error(path):
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Serverless Diagnostic Error</title>
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, monospace; padding: 32px; background: #0F172A; color: #F8FAFC; }}
                .card {{ background: #1E293B; border: 1px solid #334155; border-radius: 8px; padding: 24px; max-width: 900px; margin: 0 auto; }}
                h2 {{ color: #EF4444; margin-top: 0; }}
                pre {{ background: #090D16; color: #FCA5A5; padding: 16px; border-radius: 6px; overflow-x: auto; font-size: 13px; line-height: 1.5; }}
            </style>
        </head>
        <body>
            <div class="card">
                <h2>Application Startup Diagnostic (Vercel Serverless)</h2>
                <p>The Python application encountered an unhandled exception during initialization:</p>
                <pre>{err_trace}</pre>
            </div>
        </body>
        </html>
        """, 500
