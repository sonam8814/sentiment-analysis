# NPS Sentiment Analytics Dashboard

AI-powered dashboard that ingests NPS data from Supabase, redacts PII, runs Aspect-Based Sentiment Analysis via LLM, and surfaces toxic promoters for triage.

## Quick Start

### 1. Prerequisites
- Python >= 3.10, < 3.13
- A Supabase project with the `nps_responses` table
- API keys for Groq and Google Gemini

### 2. Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m spacy download en_core_web_lg
```

### 3. Configure Environment

```bash
cp .env.example .env
# Edit .env with your actual credentials
```

### 4. Supabase Schema SQL

Run this in your Supabase SQL editor:

```sql
CREATE TABLE nps_responses (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
    response_date DATE NOT NULL,
    nps_score INT2 NOT NULL CHECK (nps_score BETWEEN 0 AND 10),
    comment TEXT,
    customer_id TEXT,
    segment TEXT
);

CREATE INDEX idx_nps_response_date ON nps_responses (response_date);

-- Row Level Security (read-only via anon key)
ALTER TABLE nps_responses ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Allow anonymous read access"
    ON nps_responses
    FOR SELECT
    USING (true);
```

### 5. Run the Dashboard

```bash
streamlit run app.py
```

## Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `SUPABASE_URL` | Yes | -- | Supabase project URL |
| `SUPABASE_ANON_KEY` | Yes | -- | Supabase anonymous key (read-only) |
| `SUPABASE_TABLE_NAME` | No | `nps_responses` | Table name |
| `GROQ_API_KEY` | Yes | -- | Groq API key |
| `GROQ_MODEL` | No | `llama-3.3-70b-versatile` | Groq model |
| `GEMINI_API_KEY` | Yes | -- | Google Gemini API key |
| `GEMINI_MODEL` | No | `gemini-2.0-flash` | Gemini model |
| `LLM_PROVIDER_PRIMARY` | No | `groq` | Primary LLM (`groq` or `gemini`) |
| `LLM_BATCH_SIZE` | No | `10` | Comments per LLM call |
| `LLM_MAX_RETRIES` | No | `3` | Max retries per provider |
| `LLM_TIMEOUT_SECONDS` | No | `30` | LLM call timeout |
| `CACHE_DIR` | No | `./data/cache` | Disk cache directory |
| `CACHE_EXPIRY_DAYS` | No | `30` | Cache TTL in days |
| `LOG_LEVEL` | No | `INFO` | Log level |

## Dashboard Pages

- **Overview** -- KPI cards (NPS, promoters, detractors with deltas), NPS trend line, category donut, top 5 aspects
- **Aspects** -- Stacked sentiment bars, aspect x segment heatmap, filterable comment list
- **Toxic Promoters** -- Triage table for score 9-10 + negative sentiment, CSV export, glowing detractors
- **Raw Data** -- Full dataset browser with filters, search, pagination (50 rows/page), CSV export

## Architecture

```
app.py                  -> Streamlit entry point (routing only)
config/settings.py      -> Pydantic settings from .env
config/theme.py         -> Color tokens
src/data/               -> Supabase client, PII redaction (Presidio + regex), cleaning
src/ai/                 -> LLM client (Groq/Gemini fallback), ABSA engine, disk cache
src/analytics/          -> NPS calculator, mismatch detector, aggregator (no Streamlit imports)
src/ui/                 -> Styles, sidebar, components, page modules
src/utils/              -> Logging (Loguru), custom exceptions
tests/                  -> pytest suite (71 tests)
```

## Testing

```bash
pytest -v
```

## Troubleshooting

| Issue | Fix |
|---|---|
| `ValidationError` on startup | Check all required env vars are set in `.env` |
| Groq rate limit errors | App auto-falls back to Gemini; check logs |
| Stale data in dashboard | Click "Refresh Data" in the sidebar |
| PII appearing in logs | Set `LOG_LEVEL=DEBUG` and check -- redaction counts are logged, never values |
| Presidio model missing | Run `python -m spacy download en_core_web_lg` |

## License

This project is licensed under the MIT License.
