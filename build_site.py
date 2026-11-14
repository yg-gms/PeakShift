"""Export the public sample data and build the GitHub Pages app."""
import hashlib
import json
from pathlib import Path
import shutil

from appliances import APPLIANCES, SOURCE
from explore import DATA_FILE, load_hourly
from forecast import build_weekday_profiles


ROOT = Path(__file__).resolve().parent

if __name__ == "__main__":
    output = ROOT / "_site"
    shutil.copytree(ROOT / "web", output, dirs_exist_ok=True)
    hourly = load_hourly(DATA_FILE)
    profiles = build_weekday_profiles(hourly)
    counts = hourly["mean"].resample("D").count()
    complete = set(counts[counts == 24].index)
    days = {
        str(day.date()): [round(float(v), 6) for v in readings["mean"]]
        for day, readings in hourly.groupby(hourly.index.normalize()) if day in complete
    }
    data = {
        "appliances": APPLIANCES, "appliance_source": SOURCE,
        "profiles": [[float(v) for v in profiles.loc[weekday]] for weekday in range(7)],
        "readings": days,
        "evaluation": json.loads((ROOT / "results/evaluation.json").read_text()),
    }
    (output / "data.json").write_text(json.dumps(data, separators=(",", ":"), allow_nan=False))
    shutil.copyfile(ROOT / "daily_planner.py", output / "daily_planner.py")
    # Version assets so a new deployment replaces cached styles and controls.
    index = (output / "index.html").read_text()
    for asset in ["style.css", "app.js"]:
        version = hashlib.sha256((output / asset).read_bytes()).hexdigest()[:12]
        index = index.replace(f'"{asset}"', f'"{asset}?v={version}"')
    (output / "index.html").write_text(index)
    (output / ".nojekyll").touch()
    print(f"Built {output} with {len(days)} complete recorded days.")
