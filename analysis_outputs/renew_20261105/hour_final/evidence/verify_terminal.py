# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pandas", "pyarrow", "threadpoolctl"]
# ///
# How to run: python analysis_outputs/renew_20261105/hour_final/evidence/verify_terminal.py
"""Full no-fit arithmetic, CSV, archive and preservation audit."""
import csv
import json
import os
import sys
import zipfile
from pathlib import Path
for name in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):
    os.environ[name] = '16'
ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT/'submission/score_push_renew'))
from hour_final_common import OUT,PRIOR,CANDIDATE,SPLITS,COEFFICIENT,COMPOSITION,digest,save,now,configure,install_frozen
import numpy as np
import pandas as pd  # noqa: PANDAS_OK -- full original parquet equality and formula replay
from threadpoolctl import threadpool_limits

def read(path: Path):
    return json.loads(path.read_text(encoding='utf-8-sig'))

def main() -> None:
    configure()
    install_frozen()
    protocol = read(OUT/'protocol.json')
    for path,sha in protocol['protected_sha256'].items():
        assert digest(ROOT/path)==sha,path
    assert digest(OUT/'selected_hour_coefficients.json')==COEFFICIENT
    coeff = read(OUT/'selected_hour_coefficients.json')
    factors = np.array([r['factor'] for r in coeff['factors']['hours']])
    freeze = read(OUT/'prediction_freeze.json')
    assert freeze['before_diagnostic_labels']
    assert pd.Timestamp(protocol['created_utc'])<pd.Timestamp(freeze['utc'])
    reads = read(OUT/'evidence/diagnostic_label_reads.json')
    assert len(reads)==2
    for receipt in reads:
        assert pd.Timestamp(receipt['label_read_started_utc'])>=pd.Timestamp(freeze['utc'])
        assert receipt['prediction_freeze_sha256']==digest(OUT/'prediction_freeze.json')
    diagnostics = read(OUT/'diagnostic_metrics.json')
    assert diagnostics['descriptive_only'] and diagnostics['no_reselection'] and diagnostics['all_history_exposed']
    records = []
    for split in SPLITS:
        prior = pd.read_parquet(PRIOR/'predictions'/split/'predictions.parquet',columns=['ts','grp','p','static_capacity']).rename(columns={'p':'p_reference'})
        saved_path = OUT/'predictions'/split/'predictions.parquet'
        saved = pd.read_parquet(saved_path)
        assert digest(saved_path)==freeze['sha256'][split]
        pd.testing.assert_frame_equal(saved[list(prior)],prior)
        hours = prior.ts.dt.tz_convert('Asia/Seoul').dt.hour.to_numpy()
        bins = np.select([hours<10,hours<12,hours<14,hours<16],[0,1,2,3],default=4)
        bounded = factors[bins]
        effective = 1+.5*(bounded-1)
        before = prior.p_reference.to_numpy()*effective
        expected = np.clip(before,0,prior.static_capacity.to_numpy())
        np.testing.assert_array_equal(saved.hour_bin,bins)
        np.testing.assert_array_equal(saved.bounded_hour_factor,bounded)
        np.testing.assert_array_equal(saved.effective_hour_factor,effective)
        np.testing.assert_array_equal(saved.before_capacity_clip,before)
        np.testing.assert_array_equal(saved.p,expected)
        np.testing.assert_array_equal(saved.capacity_clipped,before>prior.static_capacity.to_numpy())
        assert saved.loc[prior.p_reference.eq(0),'p'].eq(0).all()
        if split!='test':
            labels = pd.read_parquet(PRIOR/'predictions'/split/'scored_predictions.parquet',columns=['ts','grp','y','smp','k'])
            scored = pd.read_parquet(OUT/'predictions'/split/'scored_predictions.parquet')
            pd.testing.assert_frame_equal(scored[list(saved)],saved)
            pd.testing.assert_frame_equal(scored[['ts','grp','y','smp','k']],labels)
            for name in ('p_reference','p'):
                weight = scored.smp*scored.k
                w = float((weight*(scored[name]-scored.y).abs()).sum())
                revenue = float((scored.smp*scored.y).sum())
                expected_score = {'W':w,'W_pct':100*w/float((weight*scored.y).sum()),'revenue':revenue,'S':revenue-.1*w,'rows':len(scored)}
                assert expected_score==diagnostics['scores'][split][name]
        records.append({'split':split,'rows':len(saved),'full_formula_max_error':0.,'exact_reference_keys_values_capacity':True,'zero_reference_stays_zero':True})
    test = pd.read_parquet(OUT/'predictions/test/predictions.parquet').sort_values(['grp','ts'])
    with (CANDIDATE/'forecast.csv').open(encoding='utf-8',newline='') as stream:
        reader = csv.DictReader(stream)
        assert reader.fieldnames==['group','ts','forecast_kwh']
        exported = list(reader)
    assert len(exported)==len(test)==17520
    assert [(r['group'],r['ts']) for r in exported]==list(zip(test.grp,test.ts.astype(str)))
    values = np.array([float(r['forecast_kwh']) for r in exported])
    np.testing.assert_array_equal(values,np.round(test.p.to_numpy(),3))
    assert (values>=0).all() and (values<=test.static_capacity.to_numpy()).all()
    assert digest(CANDIDATE/'composition.csv')==COMPOSITION
    assert (CANDIDATE/'composition.csv').read_bytes()==(ROOT/'submission/autoresearch_candidate/composition.csv').read_bytes()
    with zipfile.ZipFile(CANDIDATE/'submission_files.zip') as archive:
        assert sorted(archive.namelist())==['composition.csv','forecast.csv']
        assert archive.testzip() is None
        for name in archive.namelist():
            assert archive.read(name)==(CANDIDATE/name).read_bytes()
    manifest = read(CANDIDATE/'manifest.json')
    assert manifest['new_scalar_fits']==0 and manifest['new_tree_fits']==0
    assert manifest['original_user_reported_official_score']==6454220836
    assert not manifest['official_score_available'] and not manifest['uploaded']
    assert manifest['diagnostic_metrics']==diagnostics['scores']
    for name,sha in manifest['files_sha256'].items():
        assert digest(CANDIDATE/name)==sha
    for name,sha in read(OUT/'candidate_artifact_hashes.json').items():
        assert digest(CANDIDATE/name)==sha
    validation = read(OUT/'export_validation.log')
    assert validation['status']=='PASS' and validation['sites']==253 and validation['forecast_rows']==17520
    assert validation['rows_above_own_capacity']==0
    assert read(OUT/'export_receipt.json')['validator_exit_code']==0
    external = read(OUT/'evidence/run_attempt01_exit.json')
    start = read(OUT/'evidence/run_attempt01_start.json')
    assert external['exit_code']==0 and external['has_exited'] and external['exact_worker_absent']
    assert external['native_handle_retained_before_wait']
    assert (start['pid'],start['creation_filetime'])==(external['pid'],external['creation_filetime'])
    for name in ('controller_start.json','controller_receipt.json'):
        receipt = read(OUT/name)
        assert receipt['scalar_fits']==0 and receipt['tree_fits']==0
        r = receipt['identity']
        assert (r['pid'],r['creation_filetime'])==(start['pid'],start['creation_filetime'])
        assert r['priority_class']==32 and r['model_threads']==16
        assert r['pyarrow_cpu']==4 and r['pyarrow_io']==4
        assert all(p['num_threads']==16 for p in r['threadpools'])
    save(OUT/'evidence/terminal_audit.json',{'passed':True,'utc':now(),'invocation':'python analysis_outputs/renew_20261105/hour_final/evidence/verify_terminal.py','scenario':'all26352 prediction rows/diagnostics,exact CSV keys/rounding/capacity/ZIP,prior files hashes,freeze-before-label receipts,native lifecycle/resources','binary_observable':'all assertions passed','protected_files':len(protocol['protected_sha256']),'predictions':records,'forecast_rows':17520,'composition_byte_identical':True,'zip_members_exact':True,'new_scalar_fits':0,'new_tree_fits':0,'validator_exit_code':0,'external_exit_code':0,'candidate':str(CANDIDATE.relative_to(ROOT))})
    print('HOUR FINAL TERMINAL AUDIT PASS',flush=True)
if __name__=='__main__':
    with threadpool_limits(limits=16):
        main()
