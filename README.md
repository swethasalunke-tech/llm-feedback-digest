# llm-feedback-digest

A CLI tool that reads product feedback from CSV or JSON, uses the Anthropic Claude API to categorize entries by theme, sentiment, and priority, and outputs a weekly digest in markdown format.

---

## Requirements

- Python 3.10+
- An Anthropic API key set as `ANTHROPIC_API_KEY`

---

## Install

```bash
git clone https://github.com/your-username/llm-feedback-digest.git
cd llm-feedback-digest
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Set your API key:

```bash
export ANTHROPIC_API_KEY=sk-ant-...
```

---

## Usage

### analyze

```bash
python main.py analyze examples/feedback-sample.csv
```

### digest

```bash
python main.py digest analyzed_feedback-sample.json
python main.py digest analyzed_feedback-sample.json --output digest.md
python main.py digest analyzed_feedback-sample.json --slack-webhook https://hooks.slack.com/services/...
```

---

## License

MIT