import os
from app import app
from flask import url_for

client = app.test_client()

with app.test_request_context():
    idx_url = url_for('index')
    assert idx_url == '/', f"Expected '/', got '{idx_url}'"
    dash_url = url_for('dashboard')
    assert dash_url == '/dashboard', f"Expected '/dashboard', got '{dash_url}'"
    print(f"PASS: url_for('index') -> '{idx_url}' and url_for('dashboard') -> '{dash_url}'")

# 1. Root /
res = client.get('/')
assert res.status_code == 200, f"Expected 200, got {res.status_code}"
html = res.get_data(as_text=True)
assert 'Know Which Documents' in html, "Expected 'Know Which Documents' in landing page"
assert 'to Trust.' in html, "Expected 'to Trust.' in landing page"
assert 'Get Started' in html, "Expected 'Get Started' in landing page"
assert 'Cache-Control' in res.headers, "Expected Cache-Control header"
print("PASS: Root '/' returns 200 with landing page content and Cache-Control:", res.headers.get('Cache-Control'))

# 2. Aliases /index, /api, /api/index, /api/index.py
for p in ['/index', '/api', '/api/index', '/api/index.py']:
    res = client.get(p)
    assert res.status_code == 200, f"Failed on path {p}"
    assert 'Know Which Documents' in res.get_data(as_text=True)
    print(f"PASS: Route alias '{p}' returns 200 with landing page")

# 3. Direct dashboard route
res = client.get('/dashboard')
assert res.status_code == 200
html_dash = res.get_data(as_text=True)
assert 'Security Overview' in html_dash, "Expected 'Security Overview' in dashboard"
assert 'Integrity: SHA-256' in html_dash, "Expected 'Integrity: SHA-256' in dashboard"
print("PASS: Direct '/dashboard' returns 200 with complete dashboard UI")

# 4. Upload route
res = client.get('/upload')
assert res.status_code == 200
html_up = res.get_data(as_text=True)
assert 'Document Screening Ingestion' in html_up
assert 'Automated Screening Checkpoints' in html_up
print("PASS: Direct '/upload' returns 200 with upload UI")

# 5. Non-existent route 404 handler
res = client.get('/nonexistent_route_404_test')
assert res.status_code == 302
loc = res.headers.get('Location')
assert loc in ['/', 'http://localhost/'], f"Expected redirect to '/', got '{loc}'"
print(f"PASS: 404 handler redirects to landing page root ('{loc}')")

# 6. Verify middleware logic
from api.index import VercelQueryPathMiddleware
test_wsgi_environ = {}
def mock_app(environ, start_response):
    return [environ['PATH_INFO'].encode('utf-8')]

wrapped = VercelQueryPathMiddleware(mock_app)

# Case A: Vercel rewrite with __url=/
env_a = {'QUERY_STRING': '__url=/', 'PATH_INFO': '/api/index.py'}
res_a = wrapped(env_a, lambda s, h: None)
assert env_a['PATH_INFO'] == '/', f"Expected '/', got {env_a['PATH_INFO']}"
assert env_a['QUERY_STRING'] == '', f"Expected empty query string, got {env_a['QUERY_STRING']}"
print("PASS: Middleware Case A (__url=/) -> PATH_INFO='/'")

# Case B: Vercel rewrite with __url=/dashboard
env_b = {'QUERY_STRING': '__url=/dashboard&test=1', 'PATH_INFO': '/api/index.py'}
res_b = wrapped(env_b, lambda s, h: None)
assert env_b['PATH_INFO'] == '/dashboard'
assert env_b['QUERY_STRING'] == 'test=1'
print("PASS: Middleware Case B (__url=/dashboard) -> PATH_INFO='/dashboard', QUERY_STRING='test=1'")

# Case C: Vercel cold-start direct invocation without __url
env_c = {'QUERY_STRING': '', 'PATH_INFO': '/api/index.py'}
res_c = wrapped(env_c, lambda s, h: None)
assert env_c['PATH_INFO'] == '/'
print("PASS: Middleware Case C (cold-start /api/index.py without __url) -> PATH_INFO='/'")

print("\n*** ALL ROUTING AND MIDDLEWARE TESTS PASSED! ***")
