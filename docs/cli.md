# CLI Reference

The Command-Line Interface (CLI) provides a convenient way to use LangExtract from the terminal.

## Installation

```powershell
cd monorepo\cli
python -m venv .venv
. .venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Usage

### Extract from Text

```powershell
python app.py extract --text "علی در تهران زندگی می‌کند." --language fa --report-out report.html
```

### Extract from File

```powershell
python app.py extract --file input.txt --language fa --report-out report.html
```

## Options

- `--text`: Input text to extract from
- `--file`: Input file path
- `--language`: Language code (`fa` or `en`)
- `--schema`: Extraction schema (default: `general`)
- `--domain`: Domain context (default: `general`)
- `--report-out`: Output HTML report path
- `--model`: Ollama model name (optional)

## Examples

See the [Examples](examples.md) page for more usage examples.

