import urllib.request
import urllib.error
import json

cases = [
    ('', 422),
    ('   ', 422),
    ('123', 422),
    ('123456789', 422),
    ('12345678901', 422),
    ('abcdefghij', 422),
    ('12345abcde', 422),
    ('<script>alert(1)</script>', 422),
    ('4763331979', 409),  # already monitored duplicate
]

for pnr_val, expected in cases:
    url = 'http://127.0.0.1:8000/api/add-pnr'
    data = json.dumps({'pnr': pnr_val}).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'}, method='POST')
    try:
        resp = urllib.request.urlopen(req)
        code = resp.getcode()
    except urllib.error.HTTPError as e:
        code = e.code
    except Exception as e:
        code = str(e)
    status = 'PASS' if code == expected else 'FAIL'
    print(f'{status} add-pnr input "{pnr_val[:20]}" -> {code} (expected {expected})')
