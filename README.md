# tabwatch

> A browser extension companion with a Python backend that tracks and summarizes your browsing sessions for productivity review.

---

## Installation

```bash
pip install tabwatch
```

Or clone and install locally:

```bash
git clone https://github.com/yourusername/tabwatch.git && cd tabwatch && pip install -e .
```

---

## Usage

Start the backend server (the browser extension will connect automatically):

```bash
tabwatch start
```

After a browsing session, generate a summary report:

```bash
tabwatch summary --date today
```

Example output:

```
Session Summary — 2024-11-14
────────────────────────────
Total active time:   3h 42m
Top domains:
  github.com        1h 15m
  docs.python.org     48m
  stackoverflow.com   33m

Productivity score: 81/100
```

You can also export reports as JSON or CSV:

```bash
tabwatch summary --format json --output report.json
```

---

## Browser Extension

Load the `extension/` directory as an unpacked extension in Chrome or Firefox. It will automatically connect to the local backend on `localhost:7474`.

---

## Requirements

- Python 3.9+
- Chrome or Firefox

---

## License

This project is licensed under the [MIT License](LICENSE).