import asyncio
import csv
import gzip
import io
import json
from urllib.parse import urlencode

import httpx

from app.normalize import normalize

_ENDPOINT = "https://pubchem.ncbi.nlm.nih.gov/sdq/sdqagent.cgi"


def _build_url(field: str, value: str, limit: int) -> str:
    query = {
        "download": "*",
        "collection": "drugbankddi",
        "start": 1,
        "limit": limit,
        "where": {"ands": [{field: value}]},
    }
    return _ENDPOINT + "?" + urlencode({
        "infmt": "json",
        "outfmt": "csv",
        "query": json.dumps(query, separators=(",", ":")),
    })


def _decode(content: bytes) -> str:
    if content.startswith(b"\x1f\x8b"): 
        content = gzip.decompress(content)
    return content.decode("utf-8", errors="replace")


async def _fetch(client: httpx.AsyncClient, field: str, value: str, limit: int) -> list[dict]:
    try:
        resp = await client.get(_build_url(field, value, limit))
        if resp.status_code >= 400:
            return []
        return list(csv.DictReader(io.StringIO(_decode(resp.content))))
    except Exception:
        return []


async def live_pairs(names: list[str], timeout: float = 4.0, limit: int = 20000) -> list[dict]:
    wanted = {normalize(n) for n in names if n}
    if len(wanted) < 2:
        return []

    async def _gather() -> list[list[dict]]:
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            tasks = []
            for name in names:
                tasks.append(_fetch(client, "synonym", name, limit))
                tasks.append(_fetch(client, "name2", name, limit))
            return await asyncio.gather(*tasks)

    try:
        pages = await asyncio.wait_for(_gather(), timeout + 1)
    except Exception: 
        return []

    out: list[dict] = []
    seen: set[tuple[str, str]] = set()
    for rows in pages:
        for row in rows:
            a = normalize(row.get("synonym") or "")
            b = normalize(row.get("name2") or "")
            if a not in wanted or b not in wanted or a == b:
                continue
            key = tuple(sorted((a, b)))
            if key in seen:
                continue
            seen.add(key)
            out.append({
                "ingredient_a": key[0],
                "ingredient_b": key[1],
                "severity": "moderate",
                "description": (row.get("descr") or "").strip() or None,
                "source": "PubChem",
            })
    return out
