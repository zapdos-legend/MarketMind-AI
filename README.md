# MarketMind-AI

MarketMind-AI is a beginner-friendly Flask web app that turns a short business brief into a practical marketing strategy. It helps users organize their idea, audience, goals, budget, timeline, competitors, and preferred channels into a clear go-to-market plan.

The app can use the OpenAI API when an API key is available, but an OpenAI API key is optional because MarketMind-AI includes a local fallback response for demos, development, and portfolio review.

## Features

- Simple web form for entering a business or campaign topic.
- Optional fields for audience, goal, budget, timeline, competitors, channels, and notes.
- AI-assisted marketing strategy generation when `OPENAI_API_KEY` is configured.
- Local fallback marketing strategy when no OpenAI API key is provided.
- Beginner-friendly output with positioning, channels, campaign ideas, metrics, risks, and next steps.
- Flask routes for submitting a brief and viewing generated results.
- Clean Bootstrap-style templates for a portfolio-ready web experience.

## Tech Stack

- **Python**
- **Flask**
- **HTML / Jinja templates**
- **CSS**
- **JavaScript**
- **OpenAI Responses API** optional integration

## Setup on Windows PowerShell

> These steps assume you have Python installed and are running commands from the project folder.

### 1. Clone or open the project

```powershell
cd path\to\MarketMind-AI
```

### 2. Create a virtual environment

```powershell
python -m venv .venv
```

### 3. Activate the virtual environment

```powershell
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation scripts, run this command once in the same PowerShell window, then try activating again:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

### 4. Install dependencies

```powershell
pip install -r requirements.txt
```

If `requirements.txt` is empty, install Flask manually:

```powershell
pip install flask
```

### 5. Create your `.env` file

Copy the example environment file:

```powershell
Copy-Item .env.example .env
```

Then open `.env` and update the values as needed:

```powershell
notepad .env
```

Example:

```env
OPENAI_API_KEY=your_api_key_here
```

The OpenAI API key is optional. If you leave it blank or do not provide one, the app will still run and use its built-in local fallback strategy generator.

## Run the Flask App

From the project folder, with your virtual environment activated, run:

```powershell
python app.py
```

Then open your browser and visit:

```text
http://127.0.0.1:5000
```

Fill out the strategy form, submit it, and review the generated marketing plan on the results page.

## Environment Variables

MarketMind-AI reads configuration from environment variables:

| Variable | Required | Description |
| --- | --- | --- |
| `OPENAI_API_KEY` | No | Optional API key for OpenAI-powered strategy generation. |
| `OPENAI_MODEL` | No | Optional model override for OpenAI requests. |
| `SECRET_KEY` | No | Flask secret key. A development default is used if not set. |
| `FLASK_DEBUG` | No | Set to `1` to enable Flask debug mode while developing. |
| `FLASK_RUN_HOST` | No | Host used when running `python app.py`. Defaults to `127.0.0.1`. |
| `FLASK_RUN_PORT` | No | Port used when running `python app.py`. Defaults to `5000`. |

## Project Structure

```text
MarketMind-AI/
├── app.py              # Flask routes and app startup
├── ai_engine.py        # OpenAI integration and local fallback strategy
├── prompt_builder.py   # Builds the marketing strategy prompt
├── templates/          # Jinja HTML templates
├── static/             # CSS and JavaScript assets
├── .env.example        # Example environment variable file
└── README.md           # Project documentation
```

## Portfolio Notes

MarketMind-AI is designed to demonstrate practical Flask development, form handling, prompt construction, optional AI integration, graceful fallback behavior, and clean user-facing documentation.
