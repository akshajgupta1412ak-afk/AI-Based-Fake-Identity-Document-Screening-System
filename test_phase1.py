"""
Automated Test Script for Phase 1
Verifies routes, template rendering, and session handling.
"""

from app import app


def test_routes():
    client = app.test_client()

    routes = ['/dashboard', '/login', '/upload', '/history', '/about']
    for r in routes:
        res = client.get(r)
        assert res.status_code == 200, f"Route {r} returned {res.status_code}"
        print(f"[PASS] Route {r:<12} -> HTTP 200 OK")

    # Test root redirect
    res_root = client.get('/')
    assert res_root.status_code == 302, f"Root returned {res_root.status_code}"
    print(f"[PASS] Route {'/':<12} -> HTTP 302 Redirect to {res_root.headers.get('Location')}")

    # Test login POST
    res_login = client.post('/login', data={'username': 'admin', 'password': 'admin123'})
    assert res_login.status_code == 302, f"Login POST returned {res_login.status_code}"
    print(f"[PASS] Route {'/login POST':<12} -> HTTP 302 Login Successful")

    # Test bad login POST
    res_bad = client.post('/login', data={'username': 'wrong', 'password': 'bad'})
    assert res_bad.status_code == 200, f"Bad login returned {res_bad.status_code}"
    assert b"Invalid credentials" in res_bad.data
    print("[PASS] Bad Login Rejected with error message")

    print("\n>>> ALL PHASE 1 TESTS COMPLETED SUCCESSFULLY! <<<")


if __name__ == '__main__':
    test_routes()
