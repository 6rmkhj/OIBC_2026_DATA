# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pandas", "pyarrow", "lightgbm", "threadpoolctl"]
# ///
# How to run: python submission/score_push_renew/renew_final_run.py --prepare; --run ONLY after release.json.
"""Frozen final preparation barrier and exactly six serial fits after release."""
import json
import msvcrt
import os
from pathlib import Path
import subprocess
import sys
from renew_final_common import ROOT,OUT,CUTOFFS,environment,install_frozen,configure,resource,child_identity,ensure_terminal,save,digest,now


def launch(split: str, seed: int) -> None:
    directory = OUT/'models'/split/f'seed{seed}'
    directory.mkdir(parents=True,exist_ok=True)
    status_path = directory/'worker_status.json'
    if status_path.exists():
        status = json.loads(status_path.read_text())
        ensure_terminal(status['identity'])
        if status['state']=='complete':
            assert digest(directory/'model.txt')==status['model_sha256']
            assert digest(directory/'daylight_raw.parquet')==status['raw_sha256']
            assert json.loads((directory/'controller_receipt.json').read_text())['exit_code']==0
            return
    for status in (OUT/'models').rglob('worker_status.json'):
        ensure_terminal(json.loads(status.read_text())['identity'])
    command = [sys.executable,str(Path(__file__).with_name('renew_final_fit.py')),split,str(seed)]
    save(directory/'launch_checkpoint.json',{'utc':now(),'command':command,'protocol_sha256':digest(OUT/'protocol.json')})
    with (directory/'fit.log').open('a',encoding='utf-8') as log:
        with subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,env=os.environ.copy(),creationflags=subprocess.NORMAL_PRIORITY_CLASS|subprocess.CREATE_NO_WINDOW) as process:
            identity = child_identity(process.pid)
            save(directory/'worker_status.json',{'state':'starting','identity':identity,'utc':now()})
            started = now()
            code = process.wait()
    ensure_terminal(identity)
    save(directory/'controller_receipt.json',{'exit_code':code,'started_utc':started,'finished_utc':now(),'identity':identity,'exact_worker_absent':True})
    assert code==0,f'See {directory}/fit.log'
    print('FINAL TRIAL TERMINAL',split,seed,flush=True)


def main() -> None:
    environment()
    from renew_final_freeze import freeze
    with (OUT/'controller.lock').open('a+b') as lock:
        lock.seek(0)
        msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
        freeze()
        install_frozen()
        from final_build import enrich
        from site_features import normalizer
        from cal_math import apply
        from threadpoolctl import threadpool_limits
        from renew_final_prepare import prepare
        from renew_final_predict import recent_replay
        from renew_final_common import decay_multiplier,coefficients
        import numpy as np
        import pandas as pd  # noqa: PANDAS_OK -- frozen final preparation contracts
        configure()
        with threadpool_limits(limits=16):
            if sys.argv[1:]==['--prepare']:
                np.testing.assert_allclose(decay_multiplier(np.array([0.,180.]),180),[4/3,2/3])
                np.testing.assert_array_equal(np.maximum(np.mean([[-2.,-4.],[1.,1.],[4.,1.]],axis=0),0),[1.,0.])
                boundary = pd.to_datetime(['2025-03-01 00:00+09:00','2025-03-01 01:00+09:00'])
                np.testing.assert_array_equal(boundary<=pd.Timestamp('2025-03-01',tz='Asia/Seoul'),[True,False])
                fixture = pd.DataFrame({'ts':boundary,'grp':['G1','G2'],'p_reference':[0.,100.],'wa_temp':[np.nan,15.],'extra_wa_snow':[np.nan,0.],'static_capacity':[21208.195,21447.175]})
                applied = apply(fixture,coefficients(),'temperature_then_snow')
                assert applied.p.iloc[0]==0 and applied.effective_factor.between(.925,1.075).all()
                assert np.isfinite(normalizer(np.array([-.1,0.,.5,1.]))).all()
                prepare()
                recent_replay()
                save(OUT/'evidence/prefit_checks.json',{'passed':True,'utc':now(),'identity':resource(),'protocol_sha256':digest(OUT/'protocol.json'),'prepared_manifest_sha256':digest(OUT/'prepared_manifest.json'),'new_model_fits':0,'new_confirmation_scoring':False,'fixtures':['half-life boundary','mean signed before clip','cutoff inclusive at midnight','frozen calibration/no fitting','zero night prediction','normalizer finite'],'readonly_enrich':enrich.__module__})
                print('RENEW FINAL PREFIT READY',flush=True)
                return
            assert sys.argv[1:]==['--run']
            release = json.loads((OUT/'release.json').read_text())
            assert release['approved'] and release['protocol_sha256']==digest(OUT/'protocol.json') and release['prepared_manifest_sha256']==digest(OUT/'prepared_manifest.json')
            assert json.loads((OUT/'evidence/prefit_checks.json').read_text())['passed']
            save(OUT/'controller_start.json',{'identity':resource(),'utc':now(),'environment':{k:os.environ.get(k) for k in ('TMPDIR','TMP','TEMP','NODE_COMPILE_CACHE','BUN_RUNTIME_TRANSPILER_CACHE_PATH','PYTHONDONTWRITEBYTECODE','OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS')}})
            for split in CUTOFFS:
                for seed in range(3):
                    launch(split,seed)
            from renew_final_export import finish
            finish()
            protocol = json.loads((OUT/'protocol.json').read_text())
            after = {p:digest(ROOT/p) for p in protocol['protected_sha256']}
            assert after==protocol['protected_sha256']
            save(OUT/'preservation.json',{'unchanged':True,'files':len(after),'sha256':after})
            save(OUT/'controller_receipt.json',{'exit_code':0,'finished_utc':now(),'identity':resource(),'new_model_fit_count':6,'exported_new_namespace':True})
            save(OUT/'artifact_hashes.json',{str(p.relative_to(OUT)):digest(p) for p in OUT.rglob('*') if p.is_file() and p.name not in ('artifact_hashes.json','controller.lock','controller.log') and 'tmp' not in p.relative_to(OUT).parts})
            print('RENEW FINAL EXPORT TERMINAL',flush=True)

if __name__=='__main__':
    main()
