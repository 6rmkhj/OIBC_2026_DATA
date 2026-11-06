# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pandas", "pyarrow", "threadpoolctl"]
# ///
# How to run: python submission/score_push_renew/smooth_run.py (one immutable run).
"""Freeze, exercise fixtures, prepare inputs and fit the single approved alpha."""
import json
import msvcrt

from smooth_common import OUT, ROOT, configure, digest, environment, freeze, install_frozen, now, resource, save


def main() -> None:
    environment()
    with (OUT / "controller.lock").open("a+b") as lock:
        lock.seek(0)
        msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
        freeze()
        install_frozen()
        configure()
        import numpy as np
        from threadpoolctl import threadpool_limits
        import smooth_math
        from smooth_prepare import prepare
        from smooth_score import compare

        with threadpool_limits(limits=16):
            save(OUT / "controller_start.json", {"identity": resource(), "utc": now()})
            fixtures = smooth_math.self_check()
            original = smooth_math.normalizer
            rejected = False
            try:
                smooth_math.normalizer = lambda values: np.ones_like(values, dtype=np.float64)
                try:
                    smooth_math.self_check()
                except AssertionError:
                    rejected = True
            finally:
                smooth_math.normalizer = original
            assert rejected, "Incorrect normalization survived fixture"
            assert smooth_math.self_check() == fixtures
            save(OUT / "evidence/selfchecks.json", {"passed": True, "fixtures": fixtures,
                 "wrong_normalizer_mutation_rejected": rejected, "original_restored": True, "real_model_fits": 0})
            prepare()
            compare()
            protocol = json.loads((OUT / "protocol.json").read_text(encoding="utf-8"))
            for path, expected in protocol["protected_sha256"].items():
                assert digest(ROOT / path) == expected, path
            save(OUT / "preservation.json", {"unchanged": True, "files": len(protocol["protected_sha256"])})
            save(OUT / "controller_receipt.json", {"exit_code": 0, "identity": resource(), "utc": now(),
                 "real_model_fit_count": 0, "real_calibration_fit_count": 0, "real_alpha_fit_count": 1})
            print("SMOOTH WAVE TERMINAL", flush=True)


if __name__ == "__main__":
    main()
