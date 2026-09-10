"""Tests for loading the project-level example configuration."""

from pathlib import Path

from pipette_viscometry.config import load_config


# Resolve paths from this test file rather than relying on the shell's
# current working directory.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = PROJECT_ROOT / "config" / "config.yaml"


def test_project_config_loads():
    """The example configuration should load with the documented values."""

    config = load_config(CONFIG_PATH)

    assert config.exp_name == "Zebrafish embryos"
    assert config.exp_date == "3/16/2026"

    assert config.instrument.Rp == 20.0
    assert config.instrument.Rcac == 367.0
    assert config.instrument.P_default == 70.0

    assert config.input_dir == Path("tests/test-data")
    assert config.input_glob == "Graph series0[0-9][0-9] BF.csv"
    assert config.output_file == Path(
        "tests/test-data/output/example_results.csv"
    )
    assert config.append is True

    assert config.metadata_txt == Path("tests/test-data/PipInfo.txt")
    assert config.series_map_csv is None

    assert config.live_display is True
    assert config.theme == "dark"


def test_project_config_references_existing_input_data():
    """The bundled example should refer to files that exist in the repository."""

    config = load_config(CONFIG_PATH)

    input_dir = PROJECT_ROOT / config.input_dir
    metadata_file = PROJECT_ROOT / config.metadata_txt

    assert input_dir.is_dir(), (
        f"Configured input directory does not exist: {input_dir}"
    )
    assert metadata_file.is_file(), (
        f"Configured metadata file does not exist: {metadata_file}"
    )

    matching_files = list(input_dir.glob(config.input_glob))
    assert matching_files, (
        f"No files in {input_dir} match {config.input_glob!r}"
    )