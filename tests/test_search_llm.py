from pharos.llm import is_grounded, template_explanation
from pharos.search import Index

EV = {"classes": ["person", "car"], "t_start": 3.0, "t_end": 6.0, "t_closest": 4.5, "severity": 0.71,
      "evidence": {"min_gap_body_units": 0.4, "min_gap_px": 18.0, "peak_closing_body_units_per_s": 2.1,
                   "ttc_s_at_peak_closing": 0.9, "samples": 20}}


def test_template_has_only_measured_numbers():
    assert is_grounded(template_explanation(EV), EV)


def test_invented_number_is_rejected():
    assert not is_grounded("A person came within 0.1 body units of a car at 4.5 s.", EV)


def test_search_ranks_matching_event_first():
    docs = [{"id": 1, "text": "person and car near miss on the crossing"},
            {"id": 2, "text": "two bicycle riders pass at a junction"}]
    r = Index(docs).search("bicycle")
    assert r and r[0]["id"] == 2
    assert Index(docs).search("zebra") == []
