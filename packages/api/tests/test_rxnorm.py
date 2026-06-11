import respx
from httpx import Response

from app.services.rxnorm import RxNormClient

BASE = "https://rxnav.nlm.nih.gov/REST"


@respx.mock
async def test_resolve_brand_to_ingredient():
    respx.get(f"{BASE}/approximateTerm.json").mock(
        return_value=Response(200, json={"approximateGroup": {"candidate": [{"rxcui": "202433"}]}})
    )
    respx.get(f"{BASE}/rxcui/202433/properties.json").mock(
        return_value=Response(200, json={"properties": {"name": "Tylenol", "tty": "BN"}})
    )
    respx.get(f"{BASE}/rxcui/202433/related.json").mock(
        return_value=Response(200, json={
            "relatedGroup": {"conceptGroup": [
                {"tty": "IN", "conceptProperties": [{"rxcui": "161", "name": "Acetaminophen"}]}
            ]}
        })
    )

    result = await RxNormClient().resolve("tylenol")

    assert result.matched is True
    assert result.name == "Tylenol"
    assert result.ingredient_name == "Acetaminophen"


@respx.mock
async def test_resolve_no_match():
    respx.get(f"{BASE}/approximateTerm.json").mock(
        return_value=Response(200, json={"approximateGroup": {}})
    )
    result = await RxNormClient().resolve("zzzznotadrug")
    assert result.matched is False


@respx.mock
async def test_resolve_combination_returns_all_ingredients():
    respx.get(f"{BASE}/approximateTerm.json").mock(
        return_value=Response(200, json={"approximateGroup": {"candidate": [{"rxcui": "999"}]}})
    )
    respx.get(f"{BASE}/rxcui/999/properties.json").mock(
        return_value=Response(200, json={"properties": {"name": "Co-amoxiclav", "tty": "SCD"}})
    )
    respx.get(f"{BASE}/rxcui/999/related.json").mock(
        return_value=Response(200, json={
            "relatedGroup": {"conceptGroup": [
                {"tty": "IN", "conceptProperties": [
                    {"rxcui": "723", "name": "Amoxicillin"},
                    {"rxcui": "48203", "name": "Clavulanate"},
                ]}
            ]}
        })
    )

    result = await RxNormClient().resolve("co-amoxiclav")

    assert result.ingredient_names == ["amoxicillin", "clavulanate"]
    assert result.ingredient_name == "Amoxicillin"
    