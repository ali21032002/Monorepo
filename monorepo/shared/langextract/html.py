from typing import Any, Dict, List
import html as html_lib


def _highlight_text(text: str, entities: List[Dict[str, Any]]) -> str:
	marked = text
	# naive highlight: replace first occurrence of entity name with span
	for e in entities:
		name = e.get("name")
		type_ = e.get("type", "ENTITY")
		if not name:
			continue
		escaped = html_lib.escape(str(name))
		span = f'<mark class="entity" title="{html_lib.escape(type_)}">{escaped}</mark>'
		if escaped in marked:
			marked = marked.replace(escaped, span, 1)
	return marked


def generate_html_report(*, source_text: str, extraction: Dict[str, Any], language: str, model: str) -> str:
	entities = extraction.get("entities", [])
	relationships = extraction.get("relationships", [])
	body_text = _highlight_text(html_lib.escape(source_text), entities)

	entities_rows = "\n".join(
		f"<tr><td>{html_lib.escape(e.get('name',''))}</td><td>{html_lib.escape(e.get('type',''))}</td><td><pre>{html_lib.escape(str(e.get('attributes',{})))}</pre></td></tr>"
		for e in entities
	)

	rel_rows = "\n".join(
		f"<tr><td>{html_lib.escape(r.get('source_entity_id',''))}</td><td>{html_lib.escape(r.get('type',''))}</td><td>{html_lib.escape(r.get('target_entity_id',''))}</td><td><pre>{html_lib.escape(str(r.get('attributes',{})))}</pre></td></tr>"
		for r in relationships
	)

	html = f"""
<!doctype html>
<html lang=\"{html_lib.escape(language)}\">
<head>
<meta charset=\"utf-8\" />
<title>LangExtract Report</title>
<style>
body {{ font-family: system-ui, sans-serif; margin: 24px; }}
textarea {{ width: 100%; min-height: 140px; }}
mark.entity {{ background: #ffef99; padding: 0 2px; border-radius: 2px; }}
table {{ border-collapse: collapse; width: 100%; margin-top: 16px; }}
th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
th {{ background: #f7f7f7; }}
small {{ color: #666; }}
</style>
</head>
<body>
<h1>Extraction Report</h1>
<small>Model: {html_lib.escape(model)}</small>
<h2>Source Text</h2>
<p>{body_text}</p>
<h2>Entities</h2>
<table>
  <thead><tr><th>Name</th><th>Type</th><th>Attributes</th></tr></thead>
  <tbody>
  {entities_rows}
  </tbody>
</table>
<h2>Relationships</h2>
<table>
  <thead><tr><th>Source</th><th>Type</th><th>Target</th><th>Attributes</th></tr></thead>
  <tbody>
  {rel_rows}
  </tbody>
</table>
</body>
</html>
"""
	return html
