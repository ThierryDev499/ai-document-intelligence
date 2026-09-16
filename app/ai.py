import os

import httpx
import numpy as np
from fastapi import HTTPException


class LocalAI:
    def __init__(self):
        self.url = os.getenv('OLLAMA_URL', 'http://127.0.0.1:11434').rstrip('/')
        self.chat_model = os.getenv('CHAT_MODEL', 'llama3.2:3b')
        self.embed_model = os.getenv('EMBED_MODEL', 'nomic-embed-text')

    def request(self, path, payload):
        try:
            with httpx.Client(timeout=180, trust_env=False) as client:
                response = client.post(self.url + path, json=payload)
                response.raise_for_status()
                return response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise HTTPException(503, 'Modelo local indisponivel. Verifique o Ollama e os modelos configurados.') from exc

    def embed(self, texts, query=False):
        prefix = 'search_query: ' if query else 'search_document: '
        result = self.request('/api/embed', {
            'model': self.embed_model, 'input': [prefix + t for t in texts], 'truncate': False,
        }).get('embeddings', [])
        vectors = np.asarray(result, dtype=float)
        if vectors.ndim != 2 or len(vectors) != len(texts) or not np.isfinite(vectors).all():
            raise HTTPException(502, 'Embeddings invalidos retornados pelo modelo.')
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        if np.any(norms == 0):
            raise HTTPException(502, 'Embedding vazio retornado pelo modelo.')
        return (vectors / norms).tolist()

    def chat(self, system, text, schema=None):
        payload = {
            'model': self.chat_model, 'stream': False,
            'options': {'temperature': 0, 'num_ctx': 8192, 'num_predict': 650},
            'messages': [{'role': 'system', 'content': system}, {'role': 'user', 'content': text}],
        }
        if schema:
            payload['format'] = schema
        result = self.request('/api/chat', payload).get('message', {}).get('content', '').strip()
        if not result:
            raise HTTPException(502, 'O modelo retornou uma resposta vazia.')
        return result
