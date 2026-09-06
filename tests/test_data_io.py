# tests/test_data_io.py
import pandas as pd
import pytest
from pipette_viscometry.data_io import load_curve, append_result_row


def write_csv(tmp_path, name, text):
    p = tmp_path / name
    p.write_text(text, encoding="utf-8")
    return p


def test_load_curve_named_columns(tmp_path):
    p = write_csv(tmp_path, "named.csv", "frame,microns\n0,2.5993\n1,3.4658\n")
    df = load_curve(p)
    assert list(df.columns) == ["frame", "microns"]
    assert len(df) == 2
    assert pytest.approx(df["microns"].iloc[1]) == 3.4658


def test_load_curve_renames_unrecognized_headers(tmp_path):
    p = write_csv(tmp_path, "other.csv", "t,pos,extra\n0,2.5,a\n1,3.5,b\n")
    df = load_curve(p)
    assert list(df.columns) == ["frame", "microns"]
    assert pytest.approx(df["microns"].tolist()) == [2.5, 3.5]


def test_load_curve_skips_comment_lines(tmp_path):
    p = write_csv(tmp_path, "commented.csv", "# exported\nframe,microns\n0,2.5\n")
    df = load_curve(p)
    assert len(df) == 1


def test_load_curve_coerces_numeric_strings(tmp_path):
    # Quoted / whitespace-padded values must still land as numeric dtype.
    p = write_csv(tmp_path, "padded.csv", 'frame,microns\n0," 2.5 "\n1," 3.5 "\n')
    df = load_curve(p)
    assert pd.api.types.is_numeric_dtype(df["frame"])
    assert pd.api.types.is_numeric_dtype(df["microns"])
    assert pytest.approx(df["microns"].tolist()) == [2.5, 3.5]


def test_load_curve_rejects_non_numeric(tmp_path):
    p = write_csv(tmp_path, "text.csv", "frame,microns\n0,2.5\n1,N/A\n")
    with pytest.raises(ValueError, match="Non-numeric 'microns'"):
        load_curve(p)


def test_load_curve_rejects_locale_formatted_numbers(tmp_path):
    # "1,234" is ambiguous (thousands vs decimal separator) -- reject, never guess.
    p = write_csv(tmp_path, "locale.csv", 'frame,microns\n0,"1,234"\n')
    with pytest.raises(ValueError, match="Non-numeric 'microns'"):
        load_curve(p)


def test_load_curve_rejects_unicode_minus(tmp_path):
    # U+2212, produced by Excel/Word autocorrect.
    p = write_csv(tmp_path, "minus.csv", "frame,microns\n0,\u22122.5\n")
    with pytest.raises(ValueError, match="Non-numeric 'microns'"):
        load_curve(p)


def test_load_curve_rejects_blank_cells(tmp_path):
    p = write_csv(tmp_path, "blank.csv", "frame,microns\n0,2.5\n1,\n2,3.5\n")
    with pytest.raises(ValueError, match="1 row\(s\) with missing"):
        load_curve(p)


def test_load_curve_error_names_the_file(tmp_path):
    p = write_csv(tmp_path, "culprit.csv", "frame,microns\n0,bad\n")
    with pytest.raises(ValueError, match="culprit.csv"):
        load_curve(p)


def test_load_curve_rejects_single_column(tmp_path):
    p = write_csv(tmp_path, "one.csv", "frame\n0\n1\n")
    with pytest.raises(ValueError, match="Unrecognized file structure"):
        load_curve(p)


def test_load_curve_result_is_independent_of_source(tmp_path):
    # Returned frame must be a copy: mutating it must not warn or alias.
    p = write_csv(tmp_path, "copy.csv", "frame,microns,extra\n0,2.5,9\n")
    df = load_curve(p)
    df.loc[0, "microns"] = 99.0
    assert df["microns"].iloc[0] == 99.0


def test_append_result_row_writes_header_once(tmp_path):
    out = tmp_path / "nested" / "results.csv"
    append_result_row({"embryo_id": "E1", "eta": 482.7}, out)
    append_result_row({"embryo_id": "E2", "eta": 501.2}, out)
    df = pd.read_csv(out)
    assert list(df["embryo_id"]) == ["E1", "E2"]
    assert len(df) == 2
