from pathlib import Path
import pandas as pd

def load_curve(filepath: Path | str) -> pd.DataFrame:
    """
    Loads raw CSV dataset safely handling headers and numeric dtypes.
    """
    df = pd.read_csv(filepath, comment='#')
    # Standardize expected columns
    if 'frame' in df.columns and 'microns' in df.columns:
        return df[['frame', 'microns']]
    elif len(df.columns) >= 2:
        df.columns = ['frame', 'microns'] + list(df.columns[2:])
        return df[['frame', 'microns']]
    raise ValueError(f"Unrecognized file structure in {filepath}")

def append_result_row(row_data: dict, output_file: Path) -> None:
    """
    Appends single result row cleanly to target output path.
    """
    output_file.parent.mkdir(parents=True, exist_ok=True)
    df_row = pd.DataFrame([row_data])
    header_needed = not output_file.exists() or output_file.stat().st_size == 0
    df_row.to_csv(output_file, mode='a', index=False, header=header_needed)