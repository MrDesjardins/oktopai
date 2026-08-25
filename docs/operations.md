# Local operations

## Ollama

If `ollama serve` reports that port `11434` is already in use, an Ollama daemon is already running. Do not start a second daemon.

```bash
ollama list
curl http://127.0.0.1:11434/api/tags
PYTHONPATH=src python3 -m oktopai.cli models
```

Model installation is explicit and can be several gigabytes:

```bash
ollama pull qwen2.5-coder:7b
```

## oktopai smoke tests

```bash
PYTHONPATH=src python3 -m oktopai.cli inspect
PYTHONPATH=src python3 -m oktopai.cli route "Fix this TypeScript generic"
PYTHONPATH=src python3 -m oktopai.cli ask --file src/oktopai/router.py "Review this router"
PYTHONPATH=src python3 -m oktopai.cli preload "Generate a test"
PYTHONPATH=src python3 -m oktopai.cli events
```

For persistent lifecycle state across requests, run the newline-delimited local daemon:

```bash
PYTHONPATH=src python3 -m oktopai.cli daemon --max-warm 2
```

Send JSON requests on stdin:

```json
{"action":"route","prompt":"Fix this TypeScript generic"}
{"action":"preload","prompt":"Why does this React component rerender?"}
{"action":"ask","prompt":"Explain this code","file":"src/example.ts"}
```

The daemon keeps one lifecycle manager alive and can retain two physical models when memory permits.

## Tests

The normal suite does not require Ollama:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

The integration check is opt-in:

```bash
OKTOPAI_LIVE_TESTS=1 PYTHONPATH=src python3 -m unittest discover -s tests -v
```

## Generated data

`.oktopai/` contains sessions, events, benchmark reports, and raw outputs. It is ignored by git because it may contain repository code and model responses.
