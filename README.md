# The Gray Area — Newsletter Server

A backend server that automatically generates and delivers balanced, AI-authored news newsletters. For each top headline, the system produces a pro/con/neutral article with an AI-generated image and emails it to subscribers daily.

Users can subscribe using google form connected through zappier https://docs.google.com/forms/d/e/1FAIpQLSerIkAB_RKVyh19-fDQLF61Ux1a5m9aeUrPQ41TdBsV5osH2g/viewform

## How It Works

1. **News Fetching** — NewsAPI retrieves the day's top headlines
2. **Keyword Expansion** — GPT-3 converts each headline into a rich search query
3. **Sentiment Analysis** — Articles are classified as positive, neutral, or negative using the [BERTweet](https://huggingface.co/finiteautomata/bertweet-base-sentiment-analysis) transformer model
4. **Article Generation** — GPT-3 writes pro, con, and neutral perspectives for each story
5. **Image Generation** — DALL-E generates a symbolic illustration for each article
6. **Storage** — Articles and images are saved to Firebase Firestore and Cloud Storage
7. **Delivery** — Formatted HTML newsletters are sent to all subscribers via the Gmail API

## Tech Stack

| Layer | Technology |
|---|---|
| Web framework | Flask |
| AI text generation | OpenAI GPT-3 (`text-davinci-003`) |
| AI image generation | OpenAI DALL-E |
| Sentiment analysis | Hugging Face Transformers (BERTweet) |
| Database | Firebase Firestore |
| File storage | Firebase Cloud Storage |
| Email delivery | Gmail API (OAuth 2.0) |
| Job scheduling | APScheduler |
| News source | NewsAPI |

## API Endpoints

### `GET /get_article`

Retrieve a single article by its Firestore document ID.

| Parameter | Type | Description |
|---|---|---|
| `article_id` | string | Firestore document ID |

**Response**

```json
{
  "title": "...",
  "category": "...",
  "description": "...",
  "date": "...",
  "pro_title": "...",
  "pro": "...",
  "against_title": "...",
  "against": "..."
}
```

### `POST /subscribe`

Add a new subscriber and immediately send them the current newsletter.

| Parameter | Type | Description |
|---|---|---|
| `email` | string | Subscriber email address |

### `POST /unsubscribe`

Remove a subscriber from the mailing list.

| Parameter | Type | Description |
|---|---|---|
| `email` | string | Subscriber email address |

## Setup

### Prerequisites

- Python 3.9+
- A [Firebase](https://firebase.google.com/) project with Firestore and Cloud Storage enabled
- An [OpenAI](https://platform.openai.com/) account with API access
- A [NewsAPI](https://newsapi.org/) account
- A Gmail account with OAuth 2.0 credentials

### 1. Clone and install dependencies

```bash
git clone <repo-url>
cd Gray-Area-Server
pip install -r requirements.txt
```

> **macOS note:** `requirements.txt` includes `tensorflow-macos`. If you are on Linux or Windows, replace it with `tensorflow`.

### 2. Set environment variables

Copy `.env.example` to `.env` and fill in your keys:

```bash
cp .env.example .env
```

```
OPENAI=your_openai_api_key
NEWSAPI=your_newsapi_key
```

### 3. Add Firebase credentials

Download your Firebase service account key and save it as `firebaseServiceAccount.json` in the project root.
This file is listed in `.gitignore` and must **never** be committed.

### 4. Set up Gmail OAuth

Run the one-time authorization flow to generate `credentials.json`:

```python
from mail_utils import initialize_gmail_api
initialize_gmail_api()
```

This opens a browser window for consent and saves `credentials.json` locally.
This file is listed in `.gitignore` and must **never** be committed.

### 5. Run the server

```bash
python main.py
```

The server starts on port `5000` by default (override with the `PORT` environment variable).
A newsletter is generated and sent automatically every day at 01:00 UTC.

## Deployment

The project includes a `Procfile` for Heroku:

```
web: python main.py
```

Set the `OPENAI` and `NEWSAPI` environment variables in your Heroku config, and upload your credential files via a secrets manager or config vars — never commit them to the repository.

## Project Structure

```
├── main.py                          # Flask app, scheduler, and Firestore listener
├── cyber_journalist.py              # GPT-3 article and DALL-E image generation
├── news_generator.py                # News pipeline: keyword expansion → sentiment → article
├── news_utils.py                    # NewsAPI wrapper
├── firebase_utils.py                # Firestore and Cloud Storage helpers
├── mail_utils.py                    # Gmail API integration and HTML template rendering
├── TheGrayArea-Newsletter-Table.html # Email newsletter template
├── requirements.txt                 # Python dependencies
├── Procfile                         # Heroku process definition
└── .env.example                     # Environment variable template
```

## License

MIT
