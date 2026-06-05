# Price Reasoner

AI-powered commodity price trend reasoning engine.

## Setup

```bash
pip install -e .
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
```

## Usage

```bash
python -m price_reasoner.cli analyze --commodity 原油 --start 2023-01-01 --end 2024-01-01 --output report.md
```

## Development

```bash
pytest tests/ -v
```