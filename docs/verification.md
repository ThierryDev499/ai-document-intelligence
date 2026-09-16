# Verification

Checked on Windows with Python 3.11 and Ollama on 2026-09-16.

- 8 automated API tests passed; model responses mocked only inside unit tests.
- Real `nomic-embed-text` embeddings created for the included fictional PDF.
- Real `llama3.2:3b` answer returned 30 minutes for critical incidents and cited chunk 1, page 1. The excerpt contains that response-time policy.
- Real local summary generated and persisted; reload restores summary and question history.
- Desktop 1366x900 and mobile 390x844 inspected; no horizontal overflow on mobile.
- Fixed Windows JavaScript MIME handling and added a regression test.
- Updated pypdf to 6.16.1, python-multipart to 0.0.31 and pytest to 9.0.3 after dependency auditing. The 8 tests passed again; `pip-audit` reported no known vulnerabilities in the locked dependency set.
- Docker Engine was not running: compose configuration supplied, container execution not yet verified.

The screenshots show an actual running application and fictional data. Model language quality varies; the observed answer mixed English and Portuguese. This is not a benchmark or a claim of guaranteed factual accuracy.
