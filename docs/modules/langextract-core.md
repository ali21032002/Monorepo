# LangExtract Core Module

The core extraction module provides the main functionality for extracting entities and relationships from text.

## Functions

::: langextract.core.run_extraction
    options:
      show_source: true
      show_root_heading: true

::: langextract.core.run_multi_model_analysis
    options:
      show_source: true
      show_root_heading: true

## Usage Example

```python
from langextract import run_extraction

result = run_extraction(
    text="علی در تهران زندگی می‌کند.",
    language="fa",
    schema="general",
    domain="general"
)

print(result["entities"])
print(result["relationships"])
```

