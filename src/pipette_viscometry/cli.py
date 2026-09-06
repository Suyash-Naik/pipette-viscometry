import argparse
import re
import sys
from pathlib import Path
from .config import load_config, select_config_file
from .data_io import load_curve, append_result_row
from .metadata import parse_pip_info, load_series_map
from .gui import InteractiveFitter

SERIES_REGEX = re.compile(r"series0*(\d+)", re.IGNORECASE)

def main():
    parser = argparse.ArgumentParser(description="Pipette Viscometry Interactive Fitting Tool")
    parser.add_argument("--config", help="Path to config YAML file (omit to pick one in a file dialog)")
    args = parser.parse_args()

    config_path = args.config
    if config_path is None:
        config_path = select_config_file()
        if config_path is None:
            print("No config file selected.")
            sys.exit(0)
        print(f"Using config: {config_path}")

    cfg = load_config(config_path)
    
    # Load metadata and overrides
    meta_dict, parse_reports = parse_pip_info(cfg.metadata_txt) if cfg.metadata_txt else ({}, [])
    series_map = load_series_map(cfg.series_map_csv)

    if parse_reports:
        print(f"--- Metadata Parser Log ({len(parse_reports)} non-matching lines) ---")
        for rep in parse_reports[:5]:
            print(f"  [Ignored] {rep}")

    files = sorted(list(cfg.input_dir.glob(cfg.input_glob)))
    if not files:
        print(f"No files matched glob '{cfg.input_glob}' in {cfg.input_dir}")
        sys.exit(0)

    for file_path in files:
        match = SERIES_REGEX.search(file_path.name)
        series_num = int(match.group(1)) if match else None

        # Check explicit overrides
        if series_num and series_num in series_map:
            override = series_map[series_num]
            if not override["include"]:
                print(f"Skipping {file_path.name} (Excluded via series_map)")
                continue
            embryo_id = override["embryo_id"]
        elif series_num:
            embryo_id = f"E{series_num}"
        else:
            embryo_id = "Unknown"

        meta = meta_dict.get(embryo_id)

        print(f"Processing: {file_path.name} -> ID: {embryo_id}")

        df = load_curve(file_path)
        fitter = InteractiveFitter(df["frame"].values, df["microns"].values, file_path.name, cfg)
        skipped, aborted, visco_res, asp_fit, ret_fit = fitter.show()

        if aborted:
            print("Processing aborted by user.")
            break

        row = {
            "embryo_id": embryo_id,
            "series": series_num,
            "filename": file_path.name,
            "date": meta.date if meta else cfg.exp_date,
            "time": meta.time if meta else "",
            "P": cfg.instrument.P_default,
            "Rp": cfg.instrument.Rp,
            "Rcac": cfg.instrument.Rcac,
            "lasp": asp_fit.slope if asp_fit else None,
            "lret": ret_fit.slope if ret_fit else None,
            "eta": visco_res.eta if visco_res else None,
            "Pc": visco_res.Pc if visco_res else None,
            "gamma": visco_res.gamma if visco_res else None,
            "skipped": skipped,
            "notes": meta.notes if meta else ""
        }

        append_result_row(row, cfg.output_file)

if __name__ == "__main__":
    main()