import time
from typing import Any, Dict, Optional

from . import config

try:
    from elasticsearch import Elasticsearch
except Exception:  # pragma: no cover
    Elasticsearch = None  # type: ignore
try:
    from elasticsearch import RequestsHttpConnection  # type: ignore
except Exception:  # pragma: no cover
    RequestsHttpConnection = None  # type: ignore


_es_client: Optional[Any] = None


def get_client() -> Optional[Any]:
    if not config.ES_ENABLED:
        print("🔌 ES disabled: ES_ENABLED is false")
        return None
    global _es_client
    if _es_client is not None:
        return _es_client
    if Elasticsearch is None:
        print("❌ ES import failed: 'elasticsearch' package not available")
        return None
    # Connection options for different security modes
    es_kwargs: Dict[str, Any] = {}

    # Cloud ID (Elastic Cloud)
    if config.ES_CLOUD_ID:
        es_kwargs["cloud_id"] = config.ES_CLOUD_ID
        target_desc = f"cloud_id_set={bool(config.ES_CLOUD_ID)}"

    # Host (self-managed)
    else:
        es_kwargs["hosts"] = [config.ES_HOST]
        target_desc = f"host={config.ES_HOST}"

    # TLS verification
    if not config.ES_TLS_VERIFY:
        es_kwargs["verify_certs"] = False
        es_kwargs["ssl_show_warn"] = not config.ES_IGNORE_SSL_WARNINGS
    else:
        es_kwargs["verify_certs"] = True
        if config.ES_CA_CERT:
            es_kwargs["ca_certs"] = config.ES_CA_CERT
    tls_desc = f"verify={es_kwargs.get('verify_certs', True)}, ca_set={bool(config.ES_CA_CERT)}"

    # Authentication precedence: API key > Bearer token > username/password > none
    auth_mode = "none"
    if config.ES_API_KEY:
        # supports either base64 string or (id:key)
        if ":" in config.ES_API_KEY:
            api_id, api_key = config.ES_API_KEY.split(":", 1)
            es_kwargs["api_key"] = (api_id, api_key)
        else:
            es_kwargs["api_key"] = config.ES_API_KEY
        auth_mode = "api_key"
    elif config.ES_BEARER_TOKEN:
        es_kwargs["bearer_auth"] = config.ES_BEARER_TOKEN
        auth_mode = "bearer"
    elif config.ES_USERNAME and config.ES_PASSWORD:
        es_kwargs["basic_auth"] = (config.ES_USERNAME, config.ES_PASSWORD)
        auth_mode = "basic"
    indices_conf = (config.ES_INDEXES or config.ES_INDEX or "").strip()
    print(f"🔌 ES connecting: {target_desc} | auth={auth_mode} | {tls_desc} | indices='{indices_conf}'")
    try:
        _es_client = Elasticsearch(**es_kwargs)  # type: ignore
        try:
            ok = bool(_es_client.ping())
            if ok:
                print("✅ ES ping succeeded")
            else:
                print("⚠️ ES ping returned false")
        except Exception as e:
            print(f"⚠️ ES ping error: {e}")
    except Exception as e:
        print(f"❌ ES client creation error: {e}")
        return None
    return _es_client


def _parse_indices() -> Dict[str, Any]:
    # Build list of indices from ES_INDEXES or fallback to ES_INDEX
    raw = (config.ES_INDEXES or "").strip()
    items = [i.strip() for i in raw.split(",") if i.strip()]
    if not items:
        items = [config.ES_INDEX]
    return {"list": items, "primary": items[0]}


def ensure_index(name: Optional[str] = None) -> None:
    es = get_client()
    if es is None:
        return
    idx = name or _parse_indices()["primary"]
    try:
        if not es.indices.exists(index=idx):
            print(f"🧱 ES creating index '{idx}'")
            es.indices.create(
                index=idx,
                mappings={
                    "properties": {
                        "timestamp": {"type": "date"},
                        "language": {"type": "keyword"},
                        "domain": {"type": "keyword"},
                        "model": {"type": "keyword"},
                        "analysisMode": {"type": "keyword"},
                        "user_message": {"type": "text"},
                        "assistant_message": {"type": "text"},
                        "has_chart": {"type": "boolean"},
                        "chart_type": {"type": "keyword"},
                        "tokens": {"type": "integer"},
                    }
                },
            )
    except Exception as e:
        # best-effort
        print(f"⚠️ ES ensure_index error for '{idx}': {e}")


def log_chat(doc: Dict[str, Any], index: Optional[str] = None) -> None:
    es = get_client()
    if es is None:
        return
    ensure_index(index)
    body = {"timestamp": int(time.time() * 1000), **doc}
    try:
        target = index or _parse_indices()["primary"]
        es.index(index=target, document=body)
        print(f"📝 ES logged chat to index '{target}'")
    except Exception as e:
        # best-effort logging only
        print(f"⚠️ ES log_chat error: {e}")


def reports_overview(days: int = 7) -> Dict[str, Any]:
    es = get_client()
    if es is None:
        return {"enabled": False}
    try:
        indices = _parse_indices()["list"]
        query = {
            "size": 0,
            "query": {
                "range": {"timestamp": {"gte": f"now-{days}d/d", "lte": "now"}}
            },
            "aggs": {
                "by_domain": {"terms": {"field": "domain"}},
                "by_language": {"terms": {"field": "language"}},
                "by_model": {"terms": {"field": "model"}},
                "charts": {"terms": {"field": "chart_type"}},
            },
        }
        resp = es.search(index=indices, body=query, ignore_unavailable=True, allow_no_indices=True)
        return {"enabled": True, "raw": resp}
    except Exception as e:
        msg = str(e)
        if "index_not_found_exception" in msg or "no such index" in msg:
            # Return empty aggregation instead of error
            return {"enabled": True, "raw": {"took": 0, "timed_out": False, "hits": {"total": {"value": 0}}, "aggregations": {}}}
        return {"enabled": True, "error": msg}


def search_messages(text: str, size: int = 20) -> Dict[str, Any]:
    es = get_client()
    if es is None:
        return {"enabled": False}
    try:
        indices = _parse_indices()["list"]
        query = {
            "query": {
                "multi_match": {
                    "query": text,
                    "fields": ["user_message", "assistant_message"],
                }
            },
            "size": size,
        }
        resp = es.search(index=indices, body=query, ignore_unavailable=True, allow_no_indices=True)
        return {"enabled": True, "hits": resp.get("hits", {})}
    except Exception as e:
        msg = str(e)
        if "index_not_found_exception" in msg or "no such index" in msg:
            return {"enabled": True, "hits": {"total": {"value": 0}, "hits": []}}
        return {"enabled": True, "error": msg}


def list_indices() -> Dict[str, Any]:
    es = get_client()
    if es is None:
        return {"enabled": False}
    try:
        indices = _parse_indices()["list"]
        existing_list = []
        missing_list = []
        for idx in indices:
            try:
                if es.indices.exists(index=idx):
                    existing_list.append(idx)
                else:
                    missing_list.append(idx)
            except Exception:
                missing_list.append(idx)
        return {"enabled": True, "configured": indices, "existing": existing_list, "missing": missing_list}
    except Exception as e:
        return {"enabled": True, "error": str(e)}


def find_indices_like(name: str) -> Dict[str, Any]:
    es = get_client()
    if es is None:
        return {"enabled": False}
    name = (name or "").strip()
    if not name:
        return {"enabled": True, "matched": []}
    patterns = []
    # Normalize: if user already provided wildcard keep it; else add contains *name*
    if any(ch in name for ch in "*?["):
        patterns.append(name)
    else:
        patterns.append(f"*{name}*")
    matched = set()
    errors: Dict[str, str] = {}
    for pat in patterns:
        try:
            res = es.indices.get(index=pat, allow_no_indices=True, ignore_unavailable=True)
            if isinstance(res, dict):
                for key in res.keys():
                    matched.add(key)
        except Exception as e:
            errors[pat] = str(e)
    return {"enabled": True, "pattern": patterns, "matched": sorted(matched), "errors": errors}


def count_documents(indices: list[str]) -> Dict[str, Any]:
    es = get_client()
    if es is None:
        return {"enabled": False}
    counts: Dict[str, int] = {}
    total = 0
    errors: Dict[str, str] = {}
    for idx in indices:
        try:
            resp = es.count(index=idx, ignore_unavailable=True, allow_no_indices=True)
            c = int(resp.get("count", 0)) if isinstance(resp, dict) else 0
            counts[idx] = c
            total += c
        except Exception as e:
            errors[idx] = str(e)
    return {"enabled": True, "counts": counts, "total": total, "errors": errors}


def count_by_pattern(name: str) -> Dict[str, Any]:
    es = get_client()
    if es is None:
        return {"enabled": False}
    pat = (name or "").strip()
    if not pat:
        return {"enabled": True, "count": 0}
    if not any(ch in pat for ch in "*?["):
        # contains to be more permissive
        pat = f"*{pat}*"
    try:
        resp = es.count(index=pat, ignore_unavailable=True, allow_no_indices=True)
        c = int(resp.get("count", 0)) if isinstance(resp, dict) else 0
        return {"enabled": True, "pattern": pat, "count": c}
    except Exception as e:
        return {"enabled": True, "pattern": pat, "error": str(e), "count": 0}


def fetch_documents_by_pattern(name: str, size: int = 10) -> Dict[str, Any]:
    es = get_client()
    if es is None:
        return {"enabled": False}
    pat = (name or "").strip()
    if not pat:
        return {"enabled": True, "docs": []}
    # permissive contains pattern by default
    if not any(ch in pat for ch in "*?["):
        pat = f"*{pat}*"
    try:
        body = {"query": {"match_all": {}}}
        resp = es.search(index=pat, body=body, size=size, sort=["_doc"], ignore_unavailable=True, allow_no_indices=True)
        hits = (resp.get("hits", {}) or {}).get("hits", [])
        docs = []
        for h in hits:
            if not isinstance(h, dict):
                continue
            docs.append({
                "_index": h.get("_index"),
                "_id": h.get("_id"),
                "_source": h.get("_source"),
            })
        total = (resp.get("hits", {}) or {}).get("total", {})
        total_val = total.get("value") if isinstance(total, dict) else None
        return {"enabled": True, "pattern": pat, "docs": docs, "count": len(docs), "total": total_val, "took": resp.get("took")}
    except Exception as e:
        return {"enabled": True, "pattern": pat, "error": str(e), "docs": []}

def health() -> Dict[str, Any]:
    """Return detailed ES connection health for diagnostics."""
    info: Dict[str, Any] = {
        "enabled": bool(config.ES_ENABLED),
        "host": config.ES_HOST,
        "cloud_id_set": bool(config.ES_CLOUD_ID),
        "tls_verify": bool(config.ES_TLS_VERIFY),
        "ca_cert_set": bool(config.ES_CA_CERT),
        "indices": (config.ES_INDEXES or config.ES_INDEX or "").strip(),
    }
    try:
        es = get_client()
        if es is None:
            info["client_created"] = False
            return info
        info["client_created"] = True
        try:
            info["ping"] = bool(es.ping())
        except Exception as e:
            info["ping_error"] = str(e)
        try:
            cluster = es.info()
            if isinstance(cluster, dict):
                info["cluster_name"] = cluster.get("name")
                ver = cluster.get("version") or {}
                if isinstance(ver, dict):
                    info["version"] = ver.get("number")
        except Exception as e:
            info["info_error"] = str(e)
    except Exception as e:
        info["error"] = str(e)
    return info


