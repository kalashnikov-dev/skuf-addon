# Skuf Addon — LLM Observer & RAG Service

A Java Minecraft addon connected to a Python/FastAPI service that processes events and generates LLM responses. The main focus is on backend integration, retrieval, persistent memory, and deployment.

## Highlights

- **LLM integration:** FastAPI backend supporting OpenAI-compatible APIs, Azure AI Foundry, and Gemini.
- **RAG:** embeddings and Qdrant for finding relevant information in a Markdown knowledge base and past interactions.
- **Persistent memory:** facts and recent history saved locally, even when Qdrant is offline.
- **Java–Python communication:** HTTP requests run in background threads to avoid blocking the game server.
- **Deployment:** Docker on Google Cloud, with GitHub Actions for builds and automatic updates.
- **Tests:** Python unit tests for knowledge chunking, memory, and command parsing.

## How it works

```text
Java addon (events and messages)
           |
           | POST /events
           v
      FastAPI service
           |
           +-- Memory and RAG (JSON files / Qdrant)
           |
           +-- LLM provider
           |
           v
    Response or no response
           |
           v
        Java addon
```

The Java addon sends events to the Python API. The service gathers relevant context, sends it to the configured model, and returns a response when needed. It can also return no response, so not every event has to produce a message. The Python backend can be run and tested separately from the game. Model calls run outside the main application threads.

## RAG and memory

The system combines two types of memory:

- **Local memory:** stores facts and recent interactions as JSON. Data survives restarts, and updates use atomic file writes. Facts are filtered before being added to a prompt.
- **Semantic search:** splits Markdown documents into chunks, creates embeddings, and stores them in Qdrant. It can retrieve relevant knowledge and selected past interactions using similarity search.

Qdrant is optional. If it or the embedding service is unavailable, the local memory still works. When semantic search is enabled, matching text is added to the LLM prompt to give the model more context. The service also supports optional LLM-based fact extraction from messages and deduplicates saved facts.

## Engineering notes

**Responsiveness.** Java uses background workers for HTTP calls, while FastAPI moves blocking LLM requests to worker threads. This keeps the main application threads available.

**Failure handling.** The model client retries some temporary API errors. Memory and retrieval failures are handled separately so the service can continue without semantic search.

**CI/CD.** GitHub Actions builds the Java addon and deploys changed components to a Google Cloud VM over SSH. The Python service runs in Docker. Credentials are stored in GitHub Secrets or server-side environment files.

## Tech stack

- **AI / backend:** Python, FastAPI, LLM APIs, embeddings, RAG, Qdrant
- **Integration:** Java, HTTP, JSON
- **Infrastructure:** Docker, Google Cloud Platform, GitHub Actions, Git, Gradle

## Tests

From `observer-service/`:

```bash
pip install pytest
python -m pytest tests -q
```

Tests cover chunking, fact storage, deduplication, session persistence, and memory commands. A separate GitHub Actions workflow builds the Java project with Gradle.

## Repository structure

```text
observer-service/
  app/main.py          FastAPI endpoints
  app/bog_a.py         LLM calls and prompts
  app/rag/             Embeddings, retrieval, and memory
  knowledge/           Markdown knowledge base
  tests/               Python tests
  Dockerfile           API container

src/main/java/com/arturgpt/skufaddon/observer/
                       Java events and HTTP client
deploy/                Docker Compose and deployment scripts
.github/workflows/     CI/CD workflows
```

## Limitations

- RAG needs external services; without them, only local memory is available.
- Retrieval and response quality have not been evaluated with a standard benchmark.
- A standalone demo and more integration tests are possible next steps.

The Java addon is based on the GregTech Modern addon template.

## License

GNU Lesser General Public License v3.0 — see [LICENSE.MD](LICENSE.MD).
