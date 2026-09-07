# tests/test_metadata.py
from pathlib import Path

import pytest

from pipette_viscometry.cli import validate_paths
from pipette_viscometry.config import Config, InstrumentParams
from pipette_viscometry.metadata import load_series_map, parse_pip_info

PIPINFO = """Zebrafish embryos
exp started at 100 hours post death

E1 15:39 AM 3/16/2026 2.0 2.25  Notes for experiment 1
E2 15:57 AM 2/16/2026 2.0 2.25  Notes for experiment 2
"""


def make_cfg(tmp_path, **overrides):
    defaults = dict(
        exp_name="test",
        exp_date="3/16/2026",
        instrument=InstrumentParams(Rp=20.0, Rcac=367.0, P_default=70.0),
        input_dir=tmp_path,
        input_glob="*.csv",
        output_file=tmp_path / "out.csv",
        append=True,
        live_display=False,
    )
    defaults.update(overrides)
    return Config(**defaults)


# --- parse_pip_info -------------------------------------------------------


def test_parse_pip_info_reads_entries(tmp_path):
    p = tmp_path / "PipInfo.txt"
    p.write_text(PIPINFO, encoding="utf-8")
    meta, skipped = parse_pip_info(p)
    assert set(meta) == {"E1", "E2"}
    assert meta["E1"].date == "3/16/2026"
    assert meta["E1"].time == "15:39 AM"
    assert meta["E1"].param_1 == 2.0
    assert meta["E1"].param_2 == 2.25
    assert meta["E1"].notes == "Notes for experiment 1"


def test_parse_pip_info_reports_non_matching_lines(tmp_path):
    p = tmp_path / "PipInfo.txt"
    p.write_text(PIPINFO, encoding="utf-8")
    _, skipped = parse_pip_info(p)
    # The two header lines do not match the entry format.
    assert len(skipped) == 2
    assert all("Line " in s for s in skipped)


def test_parse_pip_info_raises_on_missing_file(tmp_path):
    # A configured-but-missing metadata file must not degrade to empty metadata:
    # every result row would silently fall back to the config-wide date.
    missing = tmp_path / "PipInfo.txt"
    with pytest.raises(FileNotFoundError, match="Metadata file not found"):
        parse_pip_info(missing)


def test_parse_pip_info_error_names_the_path(tmp_path):
    missing = tmp_path / "nope.txt"
    with pytest.raises(FileNotFoundError, match="nope.txt"):
        parse_pip_info(missing)


# --- load_series_map ------------------------------------------------------


def test_load_series_map_none_is_not_configured():
    # None means the optional override file was never configured -- not an error.
    assert load_series_map(None) == {}


def test_load_series_map_reads_overrides(tmp_path):
    p = tmp_path / "series_map.csv"
    p.write_text("series,embryo_id,include\n1,E1,True\n2,E2,False\n", encoding="utf-8")
    mapping = load_series_map(p)
    assert mapping[1] == {"embryo_id": "E1", "include": True}
    assert mapping[2]["include"] is False


def test_load_series_map_raises_on_missing_file(tmp_path):
    # Returning {} here would silently re-include every excluded series.
    missing = tmp_path / "series_map.csv"
    with pytest.raises(FileNotFoundError, match="Series map file not found"):
        load_series_map(missing)


# --- validate_paths -------------------------------------------------------


def test_validate_paths_clean_config(tmp_path):
    assert validate_paths(make_cfg(tmp_path)) == []


def test_validate_paths_flags_missing_metadata(tmp_path):
    cfg = make_cfg(tmp_path, metadata_txt=tmp_path / "PipInfo.txt")
    problems = validate_paths(cfg)
    assert len(problems) == 1
    assert "Metadata file not found" in problems[0]


def test_validate_paths_flags_missing_series_map(tmp_path):
    cfg = make_cfg(tmp_path, series_map_csv=tmp_path / "series_map.csv")
    problems = validate_paths(cfg)
    assert len(problems) == 1
    assert "Series map file not found" in problems[0]


def test_validate_paths_flags_missing_input_dir(tmp_path):
    cfg = make_cfg(tmp_path, input_dir=tmp_path / "absent")
    problems = validate_paths(cfg)
    assert len(problems) == 1
    assert "Input directory not found" in problems[0]


def test_validate_paths_ignores_unconfigured_optional_paths(tmp_path):
    # Both optional paths left as None must not be reported as missing.
    cfg = make_cfg(tmp_path, metadata_txt=None, series_map_csv=None)
    assert validate_paths(cfg) == []


def test_validate_paths_reports_all_problems_at_once(tmp_path):
    cfg = make_cfg(
        tmp_path,
        input_dir=tmp_path / "absent",
        metadata_txt=tmp_path / "PipInfo.txt",
        series_map_csv=tmp_path / "series_map.csv",
    )
    assert len(validate_paths(cfg)) == 3


def test_validate_paths_rejects_file_as_input_dir(tmp_path):
    # input_dir pointing at a file would glob to nothing and look like "no matches".
    f = tmp_path / "notadir.csv"
    f.write_text("frame,microns\n", encoding="utf-8")
    problems = validate_paths(make_cfg(tmp_path, input_dir=f))
    assert "Input directory not found" in problems[0]


def test_example_config_paths_exist():
    # The shipped example config must stay runnable from the repo root.
    from pipette_viscometry.config import load_config

    cfg = load_config(Path("tests/test-data/example_config.yaml"))
    assert validate_paths(cfg) == []
