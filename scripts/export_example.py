"""Export the explicitly named fictional handbook result, never arbitrary uploads."""
import json
from pathlib import Path

import httpx

with httpx.Client(base_url='http://127.0.0.1:8101', trust_env=False) as client:
    docs = client.get('/api/documents').json()
    doc = next(d for d in docs if d['name'] == 'operations-handbook.pdf')
    data = client.get('/api/documents/' + doc['id']).json()
    assert data['history'] and data['summary']
    result = data['history'][0]
    Path('examples/question-response.json').write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding='utf-8')
    print('Exported fictional handbook question/answer.')
