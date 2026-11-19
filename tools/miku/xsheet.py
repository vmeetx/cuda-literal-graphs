"""Dev-only: read the exposure sheets (a tiny YAML subset: scalars and a list of flow maps)."""
from pathlib import Path

HERE = Path(__file__).resolve().parent / "xsheets"


def _scalar(v):
    v = v.strip()
    if v in ("true", "false"):
        return v == "true"
    try:
        return int(v)
    except ValueError:
        try:
            return float(v)
        except ValueError:
            return v


def load(name):
    out, frames = {}, []
    for line in (HERE / f"{name}.yaml").read_text().splitlines():
        s = line.split("#", 1)[0].rstrip()
        if not s.strip():
            continue
        if s.strip().startswith("- {"):
            body = s.strip()[3:].rstrip("}")
            frames.append({k.strip(): _scalar(v) for k, v in (kv.split(":", 1) for kv in body.split(","))})
        elif ":" in s and not s.startswith(" "):
            k, v = s.split(":", 1)
            if v.strip():
                out[k.strip()] = _scalar(v)
    out["frames"] = frames
    out["ticks"] = sum(f["ticks"] for f in frames)
    return out
