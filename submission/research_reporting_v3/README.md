# Novel transport experiment reporting

This module reads experiment metadata without model imports, inference or fitting.
It retains the 36 historical groups and completed 10h, 22h and 23kst campaigns,
then reports deterministic temporal/spatial transport trials separately.

Primary metrics are in-sample LP-fitting diagnostics. Recent metrics apply frozen
coefficients to an already exposed development period. Coefficient budgets are
fixed limits, not a fitted blend alpha. Comparators use the protocol/config ID or
the nearest earlier same-family configuration, with ID ties and no score search.

The initial root README migration requires the existing v2 snapshot hash. Later
generations require every prior v3 output hash to match. Manual changes are not
overwritten. The former overview files and all old reporting sources stay intact.

The publisher reuses the original pinned publisher's lock, pending commit, ref,
separate index and Codex identity. It captures old stage metadata, never the stale
v2 root README snapshot, then validates the fresh v3 snapshot. Learned coefficient
models, saved predictions, ZIPs, runtime state and logs remain private. A completed
trial requires the matching root receipt, two metrics and three hash-valid private
artifacts; only metadata and hashes are published.

Root must freeze and review the reporting contract before production generation
or publication. `update_readme.py --check` is read-only. `publish_readme.py` defaults
to a dry run; only `--publish` permits the already authorized ordinary main push.

Fixture tests do not train, publish, or edit production reports:

```bash
/workspace/.venvs/oibc-2026/bin/python -B submission/research_reporting_v3/test_update_readme.py
/workspace/.venvs/oibc-2026/bin/python -B submission/research_reporting_v3/test_publish_readme.py
```
