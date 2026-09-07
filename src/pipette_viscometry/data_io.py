from pathlib import Path
import pandas as pd

def load_curve(filepath: Path | str) -> pd.DataFrame:
    """
    Loads raw CSV dataset, standardizing columns to numeric frame/microns.

    Values are coerced to numeric; non-numeric or missing entries raise
    ValueError naming the file, rather than failing later inside the fit.
    Locale-formatted numbers (e.g. "1,234") are rejected rather than parsed,
    since the separator is ambiguous -- handle those at the read_csv call.
    """
    df = pd.read_csv(filepath, comment='#')
    # Standardize expected columns
    if 'frame' in df.columns and 'microns' in df.columns:
        df = df[['frame', 'microns']].copy()
    elif len(df.columns) >= 2:
        df.columns = ['frame', 'microns'] + list(df.columns[2:])
        df = df[['frame', 'microns']].copy()
    else:
        raise ValueError(f"Unrecognized file structure in {filepath}")

    for col in ('frame', 'microns'):
        try:
            df[col] = pd.to_numeric(df[col])
        except (ValueError, TypeError) as e:
            raise ValueError(f"Non-numeric '{col}' data in {filepath}: {e}") from e

    missing = df.isna().any(axis=1)
    if missing.any():
        raise ValueError(
            f"{int(missing.sum())} row(s) with missing frame/microns in {filepath}"
        )
    return df

def append_result_row(row_data: dict, output_file: Path) -> None:
    """
    Appends single result row cleanly to target output path.
    """
    output_file.parent.mkdir(parents=True, exist_ok=True)
    df_row = pd.DataFrame([row_data])
    header_needed = not output_file.exists() or output_file.stat().st_size == 0
    df_row.to_csv(output_file, mode='a', index=False, header=header_needed)