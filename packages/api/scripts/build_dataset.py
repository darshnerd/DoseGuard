from sqlmodel import SQLModel, create_engine

import ingest_curated
import ingest_ddinter
import ingest_descriptions
import ingest_indian
import ingest_mechanisms
from _common import DB, connect, normalize, worse

INTERACTION_SOURCES = [ingest_ddinter, ingest_descriptions, ingest_mechanisms, ingest_curated]


def _ensure_schema():
    import app.models  # noqa: F401

    engine = create_engine(f"sqlite:///{DB}")
    SQLModel.metadata.create_all(engine)
    engine.dispose()


def _merge_interactions():
    merged: dict[tuple[str, str], dict] = {}
    for mod in INTERACTION_SOURCES:
        for raw_a, raw_b, attrs in mod.read():
            a, b = normalize(raw_a), normalize(raw_b)
            if not a or not b or a == b:
                continue
            key = tuple(sorted((a, b)))
            cur = merged.setdefault(key, {
                "severity": "moderate", "description": None,
                "mechanism": None, "management": None, "sources": set(),
            })
            sev = attrs.get("severity")
            if sev:
                cur["severity"] = worse(cur["severity"], sev)
            for field in ("description", "mechanism", "management"):
                if attrs.get(field) and not cur[field]:
                    cur[field] = attrs[field]
            if attrs.get("source"):
                cur["sources"].add(attrs["source"])
    return merged


def _write_interactions(conn, merged):
    rows = [
        (a, b, m["severity"], m["description"], m["mechanism"],
         m["management"], ",".join(sorted(m["sources"])))
        for (a, b), m in merged.items()
    ]
    conn.executemany(
        "INSERT INTO interaction "
        "(a_norm, b_norm, severity, description, mechanism, management, sources) "
        "VALUES (?,?,?,?,?,?,?)",
        rows,
    )
    return len(rows)


def _write_products(conn, products):
    pid = 0
    prod_rows, ing_rows = [], []
    for name, manufacturer, ingredients in products:
        nn = normalize(name)
        if not nn:
            continue
        pid += 1
        prod_rows.append((pid, name, nn, manufacturer, "IN", "indian"))
        for ing in ingredients:
            if ing:
                ing_rows.append((pid, ing, None))
    conn.executemany(
        "INSERT INTO medicineproduct (id, name, name_normalized, manufacturer, country, source) "
        "VALUES (?,?,?,?,?,?)",
        prod_rows,
    )
    conn.executemany(
        "INSERT INTO productingredient (product_id, ingredient_normalized, strength) VALUES (?,?,?)",
        ing_rows,
    )
    return len(prod_rows), len(ing_rows)


def _write_concepts(conn, merged, products):
    names = set()
    for a, b in merged:
        names.add(a)
        names.add(b)
    for _, _, ingredients in products:
        names.update(ingredients)
    conn.executemany(
        "INSERT INTO drugconcept (canonical_name, normalized_name) VALUES (?,?)",
        [(n, n) for n in sorted(names) if n],
    )
    return len([n for n in names if n])


def main():
    _ensure_schema()
    conn = connect()
    for table in ("interaction", "drugconcept", "drugalias", "medicineproduct", "productingredient"):
        conn.execute(f"DELETE FROM {table}")

    merged = _merge_interactions()
    products = list(ingest_indian.products())

    n_int = _write_interactions(conn, merged)
    n_prod, n_ing = _write_products(conn, products)
    n_con = _write_concepts(conn, merged, products)

    conn.commit()
    conn.close()
    print(f"interactions={n_int} concepts={n_con} products={n_prod} ingredients={n_ing}")


if __name__ == "__main__":
    main()
    