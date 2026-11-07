#!/usr/bin/env python3
"""Black-box security regression checks for R5-R. Creates disposable labs only."""
import argparse, hashlib, json, os, pathlib, shutil, subprocess, sys, tempfile

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--r5r',default='PPP_R5R/r5r.py',help='Path to original R5-R script')
    args=ap.parse_args()
    script=pathlib.Path(args.r5r).resolve(strict=True)
    if script.name!='r5r.py': raise SystemExit('Expected r5r.py')
    results=[]
    with tempfile.TemporaryDirectory(prefix='ppp-r5r2-') as tmp:
        base=pathlib.Path(tmp)
        def cmd(root,action,*opts):
            return subprocess.run([sys.executable,str(script),action,'--root',str(root),*opts],capture_output=True,text=True,timeout=20)
        def check(name,ok,detail=''):
            results.append({'test':name,'pass':bool(ok),'detail':detail[:240]})
            print(('PASS' if ok else 'FAIL'),name,detail[:120])
        def lab(tag):
            r=base/tag
            for action in ('prepare','plan'):
                p=cmd(r,action)
                if p.returncode: raise RuntimeError(f'{action}: {p.stderr}')
            digest=json.loads((r/'state'/'plan.json').read_text())['plan_sha256']
            return r,digest
        def approve(r,d):return cmd(r,'approve','--digest',d,'--confirm','AUTORIZO DEMO R5R')
        def counts(r):return sum(p.is_file() for p in (r/'inbox').glob('*.txt')),sum(p.is_file() for p in (r/'sorted').rglob('*.txt'))
        r,d=lab('no_approval');p=cmd(r,'execute');check('ejecucion_sin_aprobacion',p.returncode!=0 and counts(r)==(30,0))
        r,d=lab('bad_digest');p=approve(r,'0'*64);check('digest_incorrecto',p.returncode!=0 and not (r/'state'/'approval.json').exists())
        r,d=lab('wrong_phrase');p=cmd(r,'approve','--digest',d,'--confirm','NO');check('frase_incorrecta',p.returncode!=0)
        r,d=lab('altered_source');assert approve(r,d).returncode==0
        f=r/'inbox'/'doc_001.txt';f.write_text('CAMBIO SINTETICO\n');p=cmd(r,'execute')
        check('hash_origen_modificado',p.returncode!=0 and counts(r)==(30,0))
        r,d=lab('occupied');assert approve(r,d).returncode==0
        target=r/'sorted'/'universidad';target.mkdir();(target/'doc_001.txt').write_text('OCUPADO')
        p=cmd(r,'execute');check('destino_ocupado',p.returncode!=0 and (target/'doc_001.txt').read_text()=='OCUPADO' and counts(r)==(30,1))
        r,d=lab('symlink');assert approve(r,d).returncode==0
        outside=base/'external_sentinel.txt';outside.write_text('NO TOCAR')
        (r/'inbox'/'doc_001.txt').unlink();(r/'inbox'/'doc_001.txt').symlink_to(outside)
        p=cmd(r,'execute');check('symlink_origen_externo',p.returncode!=0 and outside.read_text()=='NO TOCAR')
        r,d=lab('symlink_destination');assert approve(r,d).returncode==0
        external_dir=base/'external_dir';external_dir.mkdir()
        (r/'sorted'/'universidad').symlink_to(external_dir,target_is_directory=True)
        p=cmd(r,'execute');check('symlink_destino_externo',p.returncode!=0 and not list(external_dir.iterdir()))
        r,d=lab('tampered_plan');assert approve(r,d).returncode==0
        path=r/'state'/'plan.json';plan=json.loads(path.read_text());plan['actions'][0]['destination']='../../external';path.write_text(json.dumps(plan))
        p=cmd(r,'execute');check('plan_modificado',p.returncode!=0 and counts(r)==(30,0))
        r,d=lab('repeat');assert approve(r,d).returncode==0
        p1=cmd(r,'execute');p2=cmd(r,'execute');v=cmd(r,'verify')
        check('ejecucion_idempotente',p1.returncode==p2.returncode==v.returncode==0 and '0 movimientos nuevos' in p2.stdout and counts(r)==(0,30))
        p1=cmd(r,'rollback');p2=cmd(r,'rollback');v=cmd(r,'verify')
        check('reversion_idempotente',p1.returncode==p2.returncode==v.returncode==0 and '0 movimientos' in p2.stdout and counts(r)==(30,0))
        # Simulated crash: pre-move some items using same-directory sandbox paths, then resume.
        r,d=lab('partial');assert approve(r,d).returncode==0
        plan=json.loads((r/'state'/'plan.json').read_text())
        for a in plan['actions'][:7]:
            src=r/a['source'];dst=r/a['destination'];dst.parent.mkdir(parents=True,exist_ok=True);os.rename(src,dst)
        p=cmd(r,'execute');v=cmd(r,'verify');b=cmd(r,'rollback');v2=cmd(r,'verify')
        check('recuperacion_estado_parcial_simulado',p.returncode==v.returncode==b.returncode==v2.returncode==0 and counts(r)==(30,0),'Simula 7 renombres ya hechos, NO un crash real')
        # Verify an important limitation: symlinked state file is not independently guarded.
        r,d=lab('state_symlink_probe');state=r/'state'/'approval.json';sentinel=base/'sentinel_approval.json';sentinel.write_text('NO TOCAR')
        state.symlink_to(sentinel)
        p=approve(r,d)
        vulnerable=(sentinel.read_text()!='NO TOCAR')
        check('rechazo_symlink_archivo_estado',not vulnerable and p.returncode!=0,'Prueba adversarial; FAIL identifica una vulnerabilidad de R5-R')
        # Write reports only in temporary lab? Export report to current directory with fixed filename.
        report={'suite':'R5-R.2','tested_script_sha256':hashlib.sha256(script.read_bytes()).hexdigest(),'tests':results,'passed':sum(x['pass'] for x in results),'failed':sum(not x['pass'] for x in results),'warning':'Los resultados NO certifican seguridad ante adversarios concurrentes ni TOCTOU.'}
        output=pathlib.Path('r5r2_reporte.json').resolve()
        if output.exists():raise RuntimeError('Reporte existente: no sobrescribir '+str(output))
        output.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
        print('\nRESULTADO:',report['passed'],'PASS,',report['failed'],'FAIL. Reporte:',output.name)
        print('Los FAIL son hallazgos; no usar el ejecutor con archivos personales.')
        return 0 if not report['failed'] else 1
if __name__=='__main__':sys.exit(main())
