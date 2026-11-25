import json
from pathlib import Path

SRC = Path(__file__).resolve().parents[3] / "drumam" / "archive" / "samasa_decision_tree.html"
RULES = Path(__file__).resolve().parents[1] / "rules.json"


def test_snapshot_matches_html():
    from extract_rules import extract
    assert json.loads(RULES.read_text(encoding="utf-8")) == extract(SRC)


def test_tree_shape():
    r = json.loads(RULES.read_text(encoding="utf-8"))
    assert len(r["nodes"]) == 15
    assert len(r["results"]) == 24
    assert r["nodes"]["start"]["yes"] == "check_avyayi"
    assert r["nodes"]["start"]["no"] == "ask_dvandva"
    assert r["nodes"]["start"]["kind"] == "form"
    assert r["nodes"]["ask_bv_role"]["kind"] == "semantic"
    assert r["results"]["r_km_adj"]["type"] == "karmadharaya"


def test_option_nodes_are_snapshotted():
    r = json.loads(RULES.read_text(encoding="utf-8"))
    assert len(r["nodes"]["ask_km_type"]["options"]) == 7
    assert len(r["nodes"]["ask_bv_sub"]["options"]) == 3
    assert r["nodes"]["ask_bv_sub"]["options"][0]["next"] == "r_bv_saha"
