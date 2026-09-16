import json
from pathlib import Path

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.ai import LocalAI
from app.main import app


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv('DATA_DIR', str(tmp_path))
    monkeypatch.setattr(LocalAI, 'embed', lambda self, texts, query=False: [[1.0, 0.0] for _ in texts])
    with TestClient(app) as client:
        yield client


def upload(client):
    return client.post('/api/documents', files={'file': ('test.pdf', Path('examples/operations-handbook.pdf').read_bytes(), 'application/pdf')})


def test_ingestion_and_isolation(client):
    first, second = upload(client).json(), upload(client).json()
    data = client.get('/api/documents/' + first['id']).json()
    assert data['pages'] == 1
    assert data['chunks'] and data['history'] == []
    assert client.delete('/api/documents/' + first['id']).status_code == 204
    assert client.get('/api/documents/' + first['id']).status_code == 404
    assert client.get('/api/documents/' + second['id']).status_code == 200


@pytest.mark.parametrize('name,data', [('bad.txt', b'hello'), ('bad.pdf', b'not a pdf'), ('bad.pdf', b'%PDF-broken')])
def test_rejects_invalid_pdf(client, name, data):
    assert client.post('/api/documents', files={'file': (name, data)}).status_code == 422
    assert client.get('/api/documents').json() == []


def test_model_failure_does_not_persist_document(client, monkeypatch):
    def fail(*args, **kwargs):
        raise HTTPException(503, 'offline')
    monkeypatch.setattr(LocalAI, 'embed', fail)
    assert upload(client).status_code == 503
    assert client.get('/api/documents').json() == []


def test_question_citations_and_history(client, monkeypatch):
    doc = upload(client).json()
    source = client.get('/api/documents/' + doc['id']).json()['chunks'][0]['id']
    monkeypatch.setattr(LocalAI, 'chat', lambda *args: json.dumps({'answer':'30 minutes', 'source_ids':[source]}))
    response = client.post(f"/api/documents/{doc['id']}/questions", json={'question':'Support response time?'})
    assert response.status_code == 201
    assert response.json()['sources'][0]['id'] == source
    assert len(client.get('/api/documents/' + doc['id']).json()['history']) == 1
    monkeypatch.setattr(LocalAI, 'chat', lambda *args: json.dumps({'answer':'Invented', 'source_ids':[999999]}))
    assert client.post(f"/api/documents/{doc['id']}/questions", json={'question':'Support response time?'}).status_code == 502


def test_summary_and_model_change(client, monkeypatch):
    doc = upload(client).json()
    monkeypatch.setattr(LocalAI, 'chat', lambda *args: 'Operational handbook summary.')
    assert client.post(f"/api/documents/{doc['id']}/summary").json()['summary']
    monkeypatch.setenv('EMBED_MODEL', 'different-model')
    assert client.post(f"/api/documents/{doc['id']}/questions", json={'question':'Retention?'}).status_code == 409


def test_browser_assets(client):
    assert 'text/javascript' in client.get('/static/app.js').headers['content-type']
    assert client.get('/').status_code == 200
