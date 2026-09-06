from dataclasses import dataclass
from pathlib import Path
import yaml

@dataclass(frozen=True)
class InstrumentParams:
    Rp: float
    Rcac: float
    P_default: float

@dataclass(frozen=True)
class Config:
    exp_name: str
    exp_date: str
    instrument: InstrumentParams
    input_dir: Path
    input_glob: str
    output_file: Path
    append: bool
    live_display: bool
    theme: str = "light"
    metadata_txt: Path | None = None
    series_map_csv: Path | None = None

def load_config(config_path: str | Path) -> Config:
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")
    
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
        
    inst = data["instrument"]
    instrument = InstrumentParams(
        Rp=float(inst["Rp"]),
        Rcac=float(inst["Rcac"]),
        P_default=float(inst["P_default"])
    )
    
    paths = data["paths"]
    return Config(
        exp_name=data["experiment"]["name"],
        exp_date=data["experiment"]["date"],
        instrument=instrument,
        input_dir=Path(paths["input_dir"]),
        input_glob=paths.get("input_glob", "*Values*.csv"),
        output_file=Path(paths["output_file"]),
        append=paths.get("append", True),
        live_display=data.get("gui", {}).get("live_display", True),
        theme=data.get("gui", {}).get("theme", "light"),
        metadata_txt=Path(paths["metadata_txt"]) if paths.get("metadata_txt") else None,
        series_map_csv=Path(paths["series_map_csv"]) if paths.get("series_map_csv") else None,
    )

def select_config_file(initial_dir: str | Path | None = None) -> Path | None:
    """Open a file dialog to pick a config YAML. Returns None if cancelled.

    tkinter is imported lazily so headless runs that pass --config never touch it.
    """
    import tkinter as tk
    from tkinter import filedialog

    root = tk.Tk()
    root.withdraw()
    root.update()
    try:
        chosen = filedialog.askopenfilename(
            parent=root,
            title="Select experiment config file",
            initialdir=str(initial_dir) if initial_dir else str(Path.cwd()),
            filetypes=[("YAML config", "*.yaml *.yml"), ("All files", "*.*")],
        )
    finally:
        root.destroy()

    return Path(chosen) if chosen else None
