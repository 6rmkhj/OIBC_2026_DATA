# Additional-stage research reporting

This directory reports the original ten-hour and extended campaigns together
with `analysis_outputs/research_23kst_20261108`. It never starts training.
The additional-stage search stops at **2026-11-08 12:00 UTC** and its final
deadline is **2026-11-08 14:00 UTC / 23:00 KST**. These are execution windows,
not claims about completed training time.

After the new campaign has been prepared and its sources reviewed:

```bash
/workspace/.venvs/oibc-2026/bin/python submission/research_reporting_v2/update_readme.py
/workspace/.venvs/oibc-2026/bin/python submission/research_reporting_v2/publish_readme.py --dry-run
```

Only `--publish` permits an ordinary GitHub push. The original audited
`submission/score_push_22h/checkpoint_git.py` is imported unchanged, sharing its
lock, pending commit, dedicated `codex/checkpoints` ref and Codex identity.
The working HEAD and index remain untouched. No force push or merge occurs.
If an older pending commit is recovered first,
`requested_readme_snapshot_in_commit` can be false; regenerate a fresh report
and invoke the same wrapper again to publish the requested snapshot.

The generator owns the root README and `analysis_outputs/experiment_overview_v2`.
It preserves the previous overview as history and checks document hashes before
overwriting any managed output. CSV parts are linked from the new overview and
each remains below 2 MiB. The snapshot manifest binds output hashes to the
reporting sources, frozen dependencies, source metadata and stated deadlines.
Publication requires a snapshot no more than fifteen minutes old.

The additional publication scope contains pinned source files, frozen
configuration and contracts, independent audit JSON, finalized trial/base
results and their receipt/transform metadata. Recovered summaries of earlier
failures remain diagnostics with zero new model fits. New seed validation is
reported separately from novel experiments. A completed novel trial requires
every declared seed/fold receipt. Model binaries, datasets, predictions, ZIPs,
logs, raw controller state and automation identifiers remain excluded.

All historical periods have already been exposed. Their error comparisons do
not constitute a new official leaderboard score or an independent holdout.

Reproducible publication checks use disposable local repositories only:

```bash
/workspace/.venvs/oibc-2026/bin/python submission/research_reporting_v2/test_publish_readme.py
```
