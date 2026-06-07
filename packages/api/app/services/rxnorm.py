import httpx

from app.config import get_settings
from app.schemas.drug import ResolvedDrug


class RxNormClient:
    def __init__(self):
        settings = get_settings()
        self.base_url = settings.rxnav_base
        self.timeout = settings.rxnav_timeout
        
    async def _get(self, path, params):
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.get(f"{self.base_url}{path}", params=params)
            resp.raise_for_status()
            return resp.json()
        
    async def _approx_rxcui(self, term):
        data = await self._get("/approximateTerm.json", {"term": term, "maxEntries": 1})
        cads = data.get("approximateGroup", {}).get("candidate", [])
        return cads[0]["rxcui"] if cads else None
    
    async def _properties(self, rxcui):
        data = await self._get(f"/rxcui/{rxcui}/properties.json", {})
        return data.get("properties", {})
    
    async def _ingredient(self, rxcui):
        data = await self._get(f"/rxcui/{rxcui}/related.json", {"tty": "IN"})
        for group in data.get("relatedGroup", {}).get("conceptGroup", []):
            if group.get("tty") == "IN" and group .get("conceptProperties"):
                prop = group["conceptProperties"][0]
                return prop["rxcui"], prop["name"]
        return None
    
    # interaction check
    async def _build(self, term, rxcui):
        props = await self._properties(rxcui)
        name = props.get("name")
        tty = props.get("tty")
        
        if tty == "IN":
            ing_rxcui, ing_name = rxcui, name
        else:
            ing = await self._ingredient(rxcui)
            ing_rxcui, ing_name = ing if ing else (None, None)
            
        return ResolvedDrug(
            query=term,
            matched = True,
            rxcui=rxcui,
            name=name,
            ingredient_rxcui=ing_rxcui,
            ingredient_name=ing_name
        )

    async def resolve(self, term):
        rxcui = await self._approx_rxcui(term)
        if not rxcui:
            return ResolvedDrug(query=term, matched=False)
        return await self._build(term, rxcui)

    async def resolve_exact(self, term):
        rxcui = await self._exact_rxcui(term)
        if not rxcui:
            return ResolvedDrug(query=term, matched=False)
        return await self._build(term, rxcui)