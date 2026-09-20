# GovSaathi

GovSaathi is a multilingual government-scheme and tax-information assistant. The project is developed in stages: Django provides database models and content administration, FastAPI provides the application API, React provides the user interface, and a standalone RAG pipeline provides grounded answers with citations.

## Project status

The project roadmap is organized into seven stages. The early stages use mocked answers so that database, API, persistence, and frontend work can be tested before integrating machine-learning components.

## Architecture

```text
Django Admin ──┐
               ├── PostgreSQL
FastAPI API ───┘
      │
      └── React frontend

Standalone RAG pipeline
(scraping → loading → chunking → embeddings → FAISS/ChromaDB → generation)
      │
      └── integrated into FastAPI in Week 14–16
```

### Responsibilities

- **Django:** schema definition, migrations, and admin UI. It does not provide DRF endpoints or chat API views.
- **FastAPI:** asynchronous SQLAlchemy API, authentication, CORS, chat persistence, and later RAG integration.
- **PostgreSQL:** shared database created through Django migrations and used by both Django and FastAPI.
- **React:** chat interface, loading and error states, language controls, message history, and citations.
- **RAG module:** independent ingestion, retrieval, generation, and evaluation pipeline.

## Repository structure

```text
project-root/
├── django_backend/
│   ├── manage.py
│   ├── config/
│   └── knowledge_base/
│       ├── models.py
│       ├── admin.py
│       ├── migrations/
│       └── tests.py
├── fastapi_backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── auth.py
│   │   └── routes/
│   │       ├── chat.py
│   │       └── history.py
│   └── tests/
├── frontend/
│   └── src/
├── rag/
│   ├── src/
│   │   ├── loader.py
│   │   ├── chunker.py
│   │   ├── ingest.py
│   │   ├── vector_store.py
│   │   ├── generator.py
│   │   └── pipeline.py
│   ├── scripts/
│   │   └── build_index.py
│   ├── data/raw/
│   ├── indexes/              # generated; do not commit
│   └── evaluation/
├── .env.example
├── .gitignore
├── README.md
└── requirements.txt
```

The exact folder names can differ, but Django, FastAPI, React, and RAG code should remain separate. The RAG module must not depend on Django or FastAPI.

## Database models

Django defines and migrates these shared tables:

- **Scheme:** government-scheme name, description, eligibility, benefits, application process, source, language, and timestamps.
- **TaxDocument:** tax topic, title, content, financial year or applicability, source, language, and timestamps.
- **ChatSession:** a conversation owner or session token, title, created time, and updated time.
- **ChatMessage:** session, role (`user` or `assistant`), message text, citations, detected language, and timestamp.

FastAPI uses asynchronous SQLAlchemy models that map to the same PostgreSQL tables. Django remains the authority for schema migrations.

## Development roadmap

### Week 1–2: Django models and admin

Set up Django with `Scheme`, `TaxDocument`, `ChatSession`, and `ChatMessage` models. Enable the Django admin panel and manually add 10–15 sample schemes or tax entries.

Scope:

- Create Django project and application.
- Configure PostgreSQL.
- Create models and migrations.
- Register models in `admin.py`.
- Create a superuser.
- Add and edit knowledge-base entries through `/admin/`.
- Do not add DRF or API views.

Deliverable: an admin panel for managing knowledge-base content.

### Week 3–4: FastAPI mock API

Create a separate FastAPI project using asynchronous SQLAlchemy and the same PostgreSQL database.

Endpoints:

```text
POST /api/chat
GET  /api/history/{session_id}
```

`POST /api/chat` should accept a query and return a realistic mocked RAG response:

```json
{
  "answer": "You may be eligible for ...",
  "citations": [
    {
      "title": "Sample scheme entry",
      "source": "Django knowledge base",
      "page": null
    }
  ],
  "detected_language": "en",
  "session_id": "session-id"
}
```

Test the endpoints with curl or Postman before connecting React.

Deliverable: a working FastAPI server with mocked responses.

### Week 5: Authentication and persistence

Add JWT authentication or simple session tokens if per-user history is required. Configure CORS for the React development server. Save and retrieve `ChatSession` and `ChatMessage` records in PostgreSQL, including mocked assistant answers.

Deliverable: a stateful mock API where chat history remains available after refreshing the page.

### Week 6–8: React frontend

Build the chat interface with:

- Message list and user/assistant bubbles.
- Query input and submit behavior.
- Loading state.
- Error state.
- Language toggle.
- Citation panel under each assistant answer.
- API calls to the FastAPI mock endpoints.

Because responses are mocked and immediate, focus on UI/UX before introducing real model latency.

Deliverable: a complete frontend connected to the fake-answer API.

### Week 9–13: Standalone RAG pipeline

Build the RAG pipeline independently from Django, FastAPI, and React:

```text
source documents
    ↓
scraping/loading
    ↓
cleaning and chunking
    ↓
embeddings
    ↓
FAISS or ChromaDB index
    ↓
retrieval
    ↓
LLM generation
```

The standalone function should accept a query string and return an answer with sources. Test it using a script or notebook before web integration.

Deliverable: a working standalone RAG function.

Generated indexes are local build artifacts. Keep source data and the index-building script in version control, but normally ignore generated index directories.

### Week 14–16: FastAPI RAG integration

Replace the hardcoded response inside `POST /api/chat` with a call to the standalone RAG module.

Handle:

- Retrieval latency.
- React loading indicators.
- Empty or low-confidence retrieval results.
- RAG and model exceptions.
- Request timeouts.
- Optional token streaming.
- Citation formatting.

Deliverable: a working end-to-end GovSaathi application using real retrieval and generation.

### Week 17–24: Fine-tuning, evaluation, and write-up

If included in the research scope:

- Add QLoRA fine-tuning.
- Build an evaluation dataset.
- Run RAGAS and BLEU evaluation where appropriate.
- Compare mocked, baseline-RAG, and improved systems.
- Document methodology, results, limitations, and future work.
- Polish the demo.

Deliverable: an evaluated system and final write-up.

## Running the components

### Django

```bash
cd django_backend
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver 8000
```

Open the admin panel at `http://127.0.0.1:8000/admin/`.

### FastAPI

```bash
python -m uvicorn main:app --app-dir .\fastapi_backend --reload --port 8001
```

Open the API documentation at `http://127.0.0.1:8001/docs`.

### React

```bash
cd frontend
npm install
npm run dev
```

Set the frontend API base URL to the FastAPI server, normally `http://127.0.0.1:8001` during development.

### RAG index

```bash
python -m rag.scripts.build_index
```

Use the command defined by the implementation. Do not rebuild or delete an index while the API is actively serving requests.

## Environment variables

Create a local `.env` file from `.env.example`:

```env
DATABASE_URL=postgresql://user:password@localhost:5432/govsaathi
SECRET_KEY=change-me
FASTAPI_CORS_ORIGINS=http://localhost:5173
GROQ_API_KEY=your-key
```

Never commit `.env`, API keys, passwords, downloaded documents, or generated vector indexes.

## Testing checklist

- Django migrations run successfully.
- All four models are visible in Django admin.
- 10–15 sample knowledge-base entries can be created and edited.
- FastAPI starts without import errors.
- `POST /api/chat` returns answer, citations, detected language, and session information.
- `GET /api/history/{session_id}` returns saved messages.
- React can call FastAPI through CORS.
- Refreshing the frontend preserves history.
- Standalone RAG returns an answer and sources.
- FastAPI handles empty retrieval and model errors gracefully.
- Generated indexes are excluded from Git.

## Scope rules

- Django owns models, migrations, and admin content management.
- FastAPI owns API behavior and persistence logic.
- React owns presentation and user interaction.
- RAG owns ingestion, retrieval, generation, and evaluation.
- Do not mix scraping, embeddings, or LLM calls into Django models or FastAPI route files.
- Do not add DRF during the Django foundation stage.

## License

Add the project license here.
