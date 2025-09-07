from __future__ import annotations

import csv
import io
import os
from typing import Optional

import chardet
from bs4 import BeautifulSoup
from docx import Document
from lxml import etree
from pypdf import PdfReader

# Optional heavy import for .doc via textract
try:
	import textract  # type: ignore
except Exception:  # pragma: no cover
	extract_doc_available = False
else:
	extract_doc_available = True


SUPPORTED_EXTENSIONS = {".txt", ".csv", ".pdf", ".doc", ".docx", ".xml", ".html", ".htm"}


def _detect_text(data: bytes) -> str:
	if not data:
		return ""
	enc = chardet.detect(data).get("encoding") or "utf-8"
	try:
		return data.decode(enc, errors="replace")
	except Exception:
		return data.decode("utf-8", errors="replace")


def text_from_txt(data: bytes) -> str:
	return _detect_text(data)


def text_from_csv(data: bytes) -> str:
	text = _detect_text(data)
	reader = csv.reader(io.StringIO(text))
	lines = [", ".join(row) for row in reader]
	return "\n".join(lines)


def text_from_pdf(data: bytes) -> str:
	bio = io.BytesIO(data)
	reader = PdfReader(bio)
	out = []
	for page in reader.pages:
		try:
			out.append(page.extract_text() or "")
		except Exception:
			continue
	return "\n".join(out)


def text_from_docx(data: bytes) -> str:
	bio = io.BytesIO(data)
	doc = Document(bio)
	return "\n".join(p.text for p in doc.paragraphs)


def text_from_doc(data: bytes) -> str:
	if not extract_doc_available:
		return ""
	bio = io.BytesIO(data)
	# textract requires a filename; write to temp
	import tempfile
	with tempfile.NamedTemporaryFile(delete=True, suffix=".doc") as tmp:
		tmp.write(bio.read())
		tmp.flush()
		try:
			content = textract.process(tmp.name)
			return content.decode("utf-8", errors="replace")
		except Exception:
			return ""


def text_from_xml(data: bytes) -> str:
	try:
		root = etree.fromstring(data)
		return " ".join(root.itertext())
	except Exception:
		return _detect_text(data)


def text_from_html(data: bytes) -> str:
	try:
		soup = BeautifulSoup(data, "lxml")
		for s in soup(["script", "style"]):
			s.extract()
		return " ".join(soup.stripped_strings)
	except Exception:
		return _detect_text(data)


def extract_text_from_file(filename: str, data: bytes) -> str:
	ext = os.path.splitext(filename)[1].lower()
	if ext == ".txt":
		return text_from_txt(data)
	if ext == ".csv":
		return text_from_csv(data)
	if ext == ".pdf":
		return text_from_pdf(data)
	if ext == ".docx":
		return text_from_docx(data)
	if ext == ".doc":
		return text_from_doc(data)
	if ext == ".xml":
		return text_from_xml(data)
	if ext in {".html", ".htm"}:
		return text_from_html(data)
	# default attempt
	return _detect_text(data)
