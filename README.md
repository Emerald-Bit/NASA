# NASA APOD Assistant

A small REST API that gets NASA's Astronomy Picture of the Day and uses Google Gemini to describe it in a randomly selected Yoda or Darth Vader voice. Responses are concise, use British English, and refuse suspected prompt injection attempts.

## What this project demonstrates

- **REST API:** FastAPI endpoints at `/health` and `/apod`, with interactive API docs at `/docs`.
- **End-to-end flow:** `/apod` connects NASA APOD data to Gemini and returns a typed JSON response.
- **Validation and typing:** Pydantic response model, typed Python code, and runtime checks for configuration values.
- **Async Python:** asynchronous APOD endpoint and request interface.
- **Testing:** pytest unit tests for API, NASA request, and LLM behavior, including error cases.
- **Docker:** container image for running the service consistently.
- **CI/CD:** GitHub Actions runs tests and Pyright type checks; pushes to `main` deploy to Azure Container Apps.
- **Production practices:** structured logging, request timeouts/retries, and clear handling of external service failures.

## Requirements

Python 3.12 and API keys for [NASA](https://api.nasa.gov/) and Google Gemini. Docker is needed only for the container option.

## Run locally

```bash
git clone <repository-url>
cd <repository-folder>
python -m venv .venv
```

Activate the virtual environment, then install and configure:

```bash
# Windows PowerShell: .venv\Scripts\Activate.ps1
# macOS/Linux:        source .venv/bin/activate
pip install -r requirements.txt
```

Create a `.env` file in the project root:

```dotenv
NASA_API_KEY=your_nasa_api_key
GOOGLE_API_KEY=your_google_api_key
```

The external API keys are loaded from `.env`. Model and response settings are kept in [`app/config.py`](app/config.py), including the Gemini model, temperature, timeout, retry limit, token limit, and Yoda/Vader system prompts. [`config.example.py`](config.example.py) provides a blank reference for these settings.

Start the API:

```bash
uvicorn app.main:app --reload
```

Open <http://localhost:8000/docs> to try the endpoints.

## Run with Docker

After creating the `.env` file as above:

```bash
docker build -t nasa-apod-assistant .
docker run --rm -p 8000:8000 --env-file .env nasa-apod-assistant
```

Then visit <http://localhost:8000/docs>.

## Run checks

```bash
pytest
pyright
```

The Azure deployment workflow expects `RESOURCE_GROUP`, `CONTAINER_APP_NAME`, and `ACR_NAME` repository variables, plus `AZURE_CLIENT_ID`, `AZURE_TENANT_ID`, and `AZURE_SUBSCRIPTION_ID` secrets. Configure the Container App with `NASA_API_KEY` and `GOOGLE_API_KEY` as environment secrets.
