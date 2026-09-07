import re
from dataclasses import dataclass, field
from pathlib import Path
import pandas as pd

@dataclass
class EmbryoMeta:
    embryo_id: str
    time: str
    date: str
    param_1: float | None = None
    param_2: float | None = None
    param_extra: list[float] = field(default_factory=list)
    notes: str = ""

LINE_REGEX = re.compile(
    r"^\s*E(?P<num>\d+)\s+(?P<time>\d{1,2}:\d{2}\s?[AP]M)\s+(?P<date>\d{1,2}/\d{1,2}/\d{4})(?P<params>(?:\s+[\d.]+)*)\s*(?P<notes>.*)$",
    re.IGNORECASE
)

def parse_pip_info(filepath: Path) -> tuple[dict[str, EmbryoMeta], list[str]]:
    """
    Parses a PipInfo.txt metadata file into {embryo_id: EmbryoMeta}.

    Returns the metadata plus a list of lines that did not match the expected
    format. A missing file is an error, not a skipped line: callers pass this
    path only when metadata was explicitly configured, so silently returning
    empty metadata would drop per-embryo date/time/notes from every result row.
    """
    metadata = {}
    skipped_lines = []

    if not filepath.exists():
        raise FileNotFoundError(f"Metadata file not found: {filepath}")

    with open(filepath, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line_str = line.strip()
            if not line_str:
                continue
            match = LINE_REGEX.match(line_str)
            if not match:
                skipped_lines.append(f"Line {line_num}: {line_str}")
                continue

            num = match.group("num")
            embryo_id = f"E{num}"
            raw_params = match.group("params").strip().split()
            params = [float(p) for p in raw_params if p]

            p1 = params[0] if len(params) > 0 else None
            p2 = params[1] if len(params) > 1 else None
            p_extra = params[2:] if len(params) > 2 else []

            metadata[embryo_id] = EmbryoMeta(
                embryo_id=embryo_id,
                time=match.group("time"),
                date=match.group("date"),
                param_1=p1,
                param_2=p2,
                param_extra=p_extra,
                notes=match.group("notes").strip()
            )
            
    return metadata, skipped_lines

def load_series_map(filepath: Path | None) -> dict[int, dict]:
    """
    Loads optional per-series overrides into {series: {embryo_id, include}}.

    None means "not configured" and yields an empty map. A configured path that
    does not exist is an error: returning empty would silently drop every
    include=False exclusion and process series the user meant to leave out.
    """
    if filepath is None:
        return {}
    if not filepath.exists():
        raise FileNotFoundError(f"Series map file not found: {filepath}")
    df = pd.read_csv(filepath)
    mapping = {}
    for _, row in df.iterrows():
        mapping[int(row["series"])] = {
            "embryo_id": str(row["embryo_id"]) if pd.notna(row["embryo_id"]) else None,
            "include": bool(row["include"])
        }
    return mapping