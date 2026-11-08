"""Catalog sanity checks."""

import re

from ski_conditions.catalog import CATALOG, REGION_NAMES, catalog_label, sorted_catalog
from ski_conditions.const import Resort

ORIGINAL_IDS = {"sunshine_village", "lake_louise", "panorama", "kicking_horse",
                "fernie", "castle_mountain", "nakiska", "norquay"}


def test_original_ids_kept_for_migration():
    assert ORIGINAL_IDS <= set(CATALOG)


def test_rows_are_sane():
    names = set()
    for rid, r in CATALOG.items():
        assert rid == r.id and re.fullmatch(r"[a-z0-9_]+", rid)
        assert r.region in REGION_NAMES and r.country in ("CA", "US")
        assert 24 < r.latitude < 72 and -170 < r.longitude < -52, rid
        assert 0 < r.base_elevation <= r.summit_elevation < 4500, rid
        assert r.onthesnow == "" or re.fullmatch(r"[a-z-]+/[a-z0-9-]+", r.onthesnow), rid
        assert r.snowforecast == "" or re.fullmatch(r"[A-Za-z0-9-]+", r.snowforecast), rid
        assert r.onthesnow or r.snowforecast, f"{rid} has no snow-report source"
        assert (r.name, r.region) not in names
        names.add((r.name, r.region))
    assert len(CATALOG) >= 180


def test_round_trip_and_labels():
    r = CATALOG["revelstoke"]
    assert Resort.from_dict(r.to_dict()) == r
    assert catalog_label(r) == "Revelstoke — British Columbia"
    first = sorted_catalog()[0]
    assert first.country == "CA"
