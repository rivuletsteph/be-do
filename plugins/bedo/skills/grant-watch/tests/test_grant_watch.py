import datetime as dt
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))
import grant_watch as g  # noqa: E402

TODAY = dt.date(2026, 11, 6)
WATCH = {"agencies": ["USDA-NIFA"], "keywords": ["water quality"],
         "applied": [{"number": "USDA-NIFA-NLGCA-000001", "year": 2024, "status": "declined"}],
         "ignore_agencies": ["DOD-WHS"]}
HITS = {
    "agencies:USDA-NIFA": [{"id": "1", "number": "USDA-NIFA-NLGCA-011938", "title": "Capacity",
                            "agencyCode": "USDA-NIFA", "closeDate": "11/10/2026", "oppStatus": "posted"}],
    'keyword:"water quality"': [
        {"id": "2", "number": "X-1", "title": "Far &amp; away", "agencyCode": "EPA", "closeDate": "06/01/2027"},
        {"id": "3", "number": "X-2", "title": "Gone", "agencyCode": "EPA", "closeDate": "10/01/2026"},
        {"id": "4", "number": "X-3", "title": "Noise", "agencyCode": "DOD-WHS", "closeDate": "11/20/2026"}],
    "keyword:USDA-NIFA-NLGCA": [{"id": "1", "number": "USDA-NIFA-NLGCA-011938", "title": "Capacity",
                                 "agencyCode": "USDA-NIFA", "closeDate": "11/10/2026"}],
}


def fetch(body):
    (k, v), = [(k, v) for k, v in body.items()]
    return [dict(h) for h in HITS.get(f"{k}:{v}", [])]


def test_prefix_spans_cycles():
    assert g.prefix("USDA-NIFA-NLGCA-011938") == "USDA-NIFA-NLGCA"
    assert g.prefix("TAT-FY27") == "TAT-FY27"


def test_phrases_are_quoted():
    q = {t: b for _, t, b in g.queries({"keywords": ["water quality", "aquifer"]})}
    assert q["water quality"] == {"keyword": '"water quality"'}
    assert q["aquifer"] == {"keyword": "aquifer"}


def test_report():
    rep = g.report(WATCH, g.collect(WATCH, fetch), {"2"}, TODAY, 12)
    soon = rep["soon"]
    assert [r["number"] for r in soon] == ["USDA-NIFA-NLGCA-011938"]
    assert soon[0]["days_left"] == 4 and soon[0]["applied_before"][0]["year"] == 2024
    assert sorted(soon[0]["matched"]) == ["agency: USDA-NIFA", "applied: USDA-NIFA-NLGCA"]
    assert rep["new"] == []                      # id 2 was seen last week
    assert "3" not in [r["id"] for r in soon + rep["new"]]   # closed: dropped
    assert "4" not in rep["seen"] or all(r["id"] != "4" for r in soon)  # ignored agency
    assert g.text(rep).count("Far & away") == 0  # beyond the window, not new


def test_every_past_cycle_is_named():
    w = dict(WATCH, applied=WATCH["applied"] + [{"number": "USDA-NIFA-NLGCA-011938", "year": 2026, "status": "not submitted"}])
    rep = g.report(w, g.collect(w, fetch), set(), TODAY, 12)
    assert "applied 2024 declined; 2026 not submitted" in g.text(rep)
