"""Exercise the REAL running API. Run from the backend container (no extra packages).

Creates one completed mission, kept as evidence, and deletes one cancelled mission.
"""
import json
import os
import uuid
from urllib.request import Request, urlopen
from urllib.error import HTTPError

BASE = os.environ.get('TEST_BASE_URL', 'http://localhost:8000').rstrip('/')


def call(method, path, data=None, expected=200):
    body = json.dumps(data).encode() if data is not None else None
    request = Request(BASE + path, data=body, method=method,
                      headers={'Content-Type': 'application/json'} if body else {})
    try:
        response = urlopen(request, timeout=10)
    except HTTPError as error:
        response = error
    with response:
        payload = response.read()
        assert response.status == expected, (method, path, response.status, payload)
        return json.loads(payload) if payload else None


assert call('GET', '/api/health')['database'] == 'connected'
before = call('GET', '/api/stats')
call('POST', '/api/missions', {}, expected=400)
call('POST', '/api/missions', [], expected=400)
payload = {'title': f'Smoke test {uuid.uuid4().hex[:8]}', 'sector': 'Test Outpost',
           'category': 'Science', 'reward': 120}
call('POST', '/api/missions', {**payload, 'reward': True}, expected=400)
mission = call('POST', '/api/missions', payload, expected=201)
assert mission['status'] == 'available'
assert any(m['id'] == mission['id'] for m in call('GET', '/api/missions'))
completed = call('PATCH', f"/api/missions/{mission['id']}/complete")
assert completed['status'] == 'completed' and completed['completed_at']
call('PATCH', f"/api/missions/{mission['id']}/complete", expected=409)
call('DELETE', f"/api/missions/{mission['id']}", expected=409)
after = call('GET', '/api/stats')
assert after['credits'] == before['credits'] + 120
assert after['completed'] == before['completed'] + 1
call('PATCH', '/api/missions/2147483647/complete', expected=404)
cancelled = call('POST', '/api/missions', {**payload, 'title': 'Cancel test'}, expected=201)
call('DELETE', f"/api/missions/{cancelled['id']}", expected=204)
assert all(m['id'] != cancelled['id'] for m in call('GET', '/api/missions'))
print(f"PASS: health, writes, reads, validation, completion, duplicate protection, credits, cancellation.")
print(f"Completed mission #{mission['id']} remains as evidence in PostgreSQL.")
