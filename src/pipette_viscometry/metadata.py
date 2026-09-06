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
    metadata = {}
    skipped_lines = []
    
    if not filepath.exists():
        return metadata, [f"File not found: {filepath}"]

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
    if not filepath or not filepath.exists():
        return {}
    df = pd.read_csv(filepath)
    mapping = {}
    for _, row in df.iterrows():
        mapping[int(row["series"])] = {
            "embryo_id": str(row["embryo_id"]) if pd.notna(row["embryo_id"]) else None,
            "include": bool(row["include"])
        }
    return mapping