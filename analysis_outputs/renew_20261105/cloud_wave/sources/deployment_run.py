# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pandas", "pyarrow", "lightgbm", "scikit-learn", "joblib"]
# ///
# How to run: python submission/score_push/deployment_run.py
"""Immutable fixed-recipe cutoff diagnostic controller."""
import hashlib
import importlib.abc
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "analysis_outputs/score_push_20261104"
DEST = OUT / "deployment_check"


def digest(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


class FrozenImports(importlib.abc.MetaPathFinder, importlib.abc.Loader):
    """Execute snapshot bytes with original path semantics for frozen helpers."""
    def find_spec(self, fullname, path=None, target=None):
        source = DEST / "sources" / (fullname + ".py")
        if source.exists():
            return importlib.util.spec_from_loader(fullname, self)
        return None

    def create_module(self, spec):
        return None

    def exec_module(self, module) -> None:
        record = json.loads((DEST / "protocol.json").read_text())["snapshots"][module.__name__]
        source = DEST / "sources" / (module.__name__ + ".py")
        assert digest(source) == record["sha256"]
        module.__file__ = str(ROOT / record["original"])
        exec(compile(source.read_bytes(), module.__file__, "exec"), module.__dict__)


def main() -> None:
    if sys.argv[1:] == ["--worker"]:
        sys.meta_path.insert(0, FrozenImports())
        from deployment_fit import run
        run()
        return
    DEST.mkdir(exist_ok=False)
    (DEST / "sources").mkdir()
    sources = [*(ROOT / "submission/autoresearch").glob("*.py"), *(ROOT / "submission/score_push").glob("*.py"), ROOT / "submission/make_submission.py"]
    snapshots = {}
    for source in sources:
        shutil.copyfile(source, DEST / "sources" / source.name)
        snapshots[source.stem] = {"original": str(source.relative_to(ROOT)), "sha256": digest(source)}
    protected = set()
    for directory in (OUT / "final", ROOT / "submission/autoresearch_candidate", ROOT / "submission/award_candidate", ROOT / "submission/score_push_candidate", ROOT / "submission/autoresearch", ROOT / "analysis_outputs/autoresearch_20261103/final"):
        protected.update(p for p in directory.rglob("*") if p.is_file() and "__pycache__" not in p.parts)
    protected.update(sources)
    protected.update((ROOT / "submission").glob("*.csv"))
    protected.update(OUT.rglob("config.json"))
    protected.update(OUT.rglob("features.json"))
    frozen = json.loads((OUT / "final/freeze.json").read_text())
    for source in (OUT / 'final/cache/train_weather.parquet', OUT / 'final/cache/train_stations.parquet', ROOT / 'analysis_outputs/autoresearch_20261103/final/outer_features.parquet', ROOT / 'analysis_outputs/autoresearch_20261103/cache/assignment.json', ROOT / 'analysis_outputs/autoresearch_20261103/cache/features.json', ROOT / 'submission/make_submission.py'):
        frozen['input_sha256'][str(source.relative_to(ROOT))] = digest(source)
    protocol = {"created_utc": datetime.now(timezone.utc).isoformat(), "train": "ts<=2025-03-01 Asia/Seoul", "evaluation": "2025-03-01<ts<=2025-06-01 Asia/Seoul", "expected_keys": 4416, "candidate": frozen["recipe"], "incumbent": json.loads((ROOT / "analysis_outputs/autoresearch_20261103/final/config.json").read_text()), "bottom_up": {"pooled_seeds": [0,1,2,3,4], "pooled_trees":400,"site_trees":600,"leaves":127,"learning_rate":.06,"min_child_samples":200,"subsample":.8,"subsample_freq":1,"colsample_bytree":.8,"site_min_rows":1000,"site_weight":.1,"site_objective":"regression_l2", "pool_objective":"regression_l1"}, "arithmetic":"Signed finite seeds; average then clip. Same freshly fitted bottom-up both arms. Missing generation excluded, never filled. Target-day ts-1h; k=3 timestamp hours11..15.", "label_access":"Training labels predicate-filtered at Parquet read; evaluation labels opened only after predictions frozen", "decision":"POST-HOC diagnostic; no tuning or export changes; original confirmation regression retained; not pristine holdout", "resources":{"parallel_fits":1,"lgb_threads":2,"blas_threads":1,"pyarrow_threads":2,"priority":"BelowNormal"}, "bootstrap":{"seed":20261104,"replicates":2000,"blocks":"target day"}, "snapshots":snapshots,"protected_sha256":{str(p.relative_to(ROOT)):digest(p) for p in sorted(protected)}, "input_sha256":frozen["input_sha256"]}
    with (DEST / "protocol.json").open("x", encoding="utf-8") as stream:
        json.dump(protocol, stream, indent=2)
    with (DEST / "run.log").open("w", encoding="utf-8") as stream:
        result = subprocess.run([sys.executable, str(Path(__file__).resolve()), "--worker"], stdout=stream, stderr=subprocess.STDOUT, creationflags=subprocess.BELOW_NORMAL_PRIORITY_CLASS | subprocess.CREATE_NO_WINDOW, check=False)
    (DEST / "controller_receipt.json").write_text(json.dumps({"exit_code":result.returncode,"protocol_sha256":digest(DEST / "protocol.json")}), encoding="utf-8")
    assert result.returncode == 0, "See deployment_check/run.log"


if __name__ == "__main__":
    main()
