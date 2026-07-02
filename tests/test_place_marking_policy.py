"""Tests for the canonical token / initial_marking persistence policy.

POLICY recap (see copilot-instructions.md):
    * `initial_marking` is the only marking field the loader reads to
      populate M_0. It is the basal value of the object-net at design time.
    * `tokens` is transient runtime state. It is never persisted to .shy.
    * Programmatic patches MUST go through `set_place_value()` to write
      at the loader's read scope; setting `place["tokens"] = X` is a
      silent no-op (loader ignores it, sweep produces stale results).
    * On load, divergent legacy `tokens` triggers a WARNING and is
      reconciled to `initial_marking`.
    * On save, divergent runtime `tokens` triggers a WARNING and is
      dropped (GUI surfaces this divergence pre-save via a dialog).
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

import pytest

from shypn.netobjs.patch import (
    find_runtime_divergence,
    patch_shy_file,
    set_place_value,
)
from shypn.netobjs.place import Place


# ---------------------------------------------------------------------------
# Place save/load policy
# ---------------------------------------------------------------------------

def test_to_dict_does_not_persist_tokens():
    p = Place(x=0.0, y=0.0, id="P1", name="X")
    p.initial_marking = 7.0
    p.tokens = 7.0
    d = p.to_dict()
    assert "tokens" not in d, "to_dict must NOT persist transient runtime state"
    assert d["initial_marking"] == 7.0
    assert d["marking"] == 7.0  # legacy mirror retained


def test_to_dict_warns_on_runtime_divergence(caplog):
    p = Place(x=0.0, y=0.0, id="P1", name="X")
    p.initial_marking = 5.0
    p.tokens = 9.0  # runtime drift the modeller forgot to promote
    with caplog.at_level(logging.WARNING, logger="shypn.netobjs.place"):
        d = p.to_dict()
    assert "tokens" not in d
    assert d["initial_marking"] == 5.0
    assert any("diverges from initial_marking" in r.message for r in caplog.records)


def test_from_dict_warns_on_legacy_tokens_divergence(caplog):
    """A wrong-scope programmatic patch left tokens != initial_marking in the
    file. The loader must use initial_marking and warn loudly."""
    data = {
        "id": "P36",
        "name": "MAINT_DOSE",
        "x": 0, "y": 0,
        "initial_marking": 0,
        "tokens": 5.0,  # the wrong-scope write — silent bug source
    }
    with caplog.at_level(logging.WARNING, logger="shypn.netobjs.place"):
        p = Place.from_dict(data)
    assert p.initial_marking == 0.0
    assert p.tokens == 0.0, "loader must reconcile runtime to initial_marking"
    assert any("wrong scope" in r.message for r in caplog.records)


def test_from_dict_no_warning_when_tokens_matches():
    data = {
        "id": "P1", "name": "X",
        "x": 0, "y": 0,
        "initial_marking": 3.0,
        "tokens": 3.0,
    }
    p = Place.from_dict(data)
    assert p.initial_marking == 3.0
    assert p.tokens == 3.0


def test_promote_and_discard_runtime_tokens():
    p = Place(x=0.0, y=0.0, id="P1", name="X")
    p.initial_marking = 5.0
    p.tokens = 9.0
    assert p.has_runtime_divergence()

    p.promote_runtime_tokens()
    assert p.initial_marking == 9.0
    assert not p.has_runtime_divergence()

    p.tokens = 12.0
    p.discard_runtime_tokens()
    assert p.tokens == 9.0
    assert p.initial_marking == 9.0


# ---------------------------------------------------------------------------
# Programmatic helper: set_place_value
# ---------------------------------------------------------------------------

def _model_with(place):
    return {"places": [place], "transitions": [], "arcs": [], "events": []}


def test_set_place_value_writes_initial_marking_top_level():
    model = _model_with({
        "id": "P36", "name": "MAINT_DOSE",
        "initial_marking": 0, "tokens": 5.0,  # the broken state
    })
    set_place_value(model, "MAINT_DOSE", 7.5)
    p = model["places"][0]
    assert p["initial_marking"] == 7.5
    assert p["marking"] == 7.5
    assert "tokens" not in p, "helper must strip stale tokens key"


def test_set_place_value_lookup_by_id_or_name():
    model = _model_with({"id": "P36", "name": "MAINT_DOSE", "initial_marking": 0})
    set_place_value(model, "P36", 1.0)
    assert model["places"][0]["initial_marking"] == 1.0
    set_place_value(model, "MAINT_DOSE", 2.0)
    assert model["places"][0]["initial_marking"] == 2.0


def test_set_place_value_unknown_raises():
    model = _model_with({"id": "P1", "name": "X", "initial_marking": 0})
    with pytest.raises(KeyError):
        set_place_value(model, "DOES_NOT_EXIST", 1.0)


def test_set_place_value_rejects_unsupported_treat_as():
    model = _model_with({"id": "P1", "name": "X", "initial_marking": 0})
    with pytest.raises(ValueError):
        set_place_value(model, "X", 1.0, treat_as="tokens")


def test_set_place_value_roundtrip_through_loader():
    """End-to-end: helper writes -> Place.from_dict reads -> matches."""
    model = _model_with({
        "id": "P36", "name": "MAINT_DOSE",
        "x": 0, "y": 0,
        "initial_marking": 0, "tokens": 5.0,
    })
    set_place_value(model, "MAINT_DOSE", 12.0)
    p = Place.from_dict(model["places"][0])
    assert p.initial_marking == 12.0
    assert p.tokens == 12.0


def test_patch_shy_file_creates_backup_and_updates(tmp_path: Path):
    f = tmp_path / "model.shy"
    model = _model_with({
        "id": "P1", "name": "DOSE",
        "x": 0, "y": 0,
        "initial_marking": 0, "tokens": 5.0,
    })
    f.write_text(json.dumps(model, indent=2), encoding="utf-8")
    patch_shy_file(f, {"DOSE": 3.0}, backup=True)

    reloaded = json.loads(f.read_text())
    assert reloaded["places"][0]["initial_marking"] == 3.0
    assert "tokens" not in reloaded["places"][0]
    assert (tmp_path / "model.shy.bak").exists()


# ---------------------------------------------------------------------------
# find_runtime_divergence (used by GUI save dialog)
# ---------------------------------------------------------------------------

def test_find_runtime_divergence_lists_only_diverged():
    clean = Place(x=0.0, y=0.0, id="P1", name="A")
    clean.initial_marking = 2.0
    clean.tokens = 2.0

    drifted = Place(x=0.0, y=0.0, id="P2", name="B")
    drifted.initial_marking = 0.0
    drifted.tokens = 5.0

    out = find_runtime_divergence([clean, drifted])
    assert out == [drifted]
