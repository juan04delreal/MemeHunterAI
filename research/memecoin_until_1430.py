#!/usr/bin/env python3
"""Extend PAPER-ONLY observation to an absolute deadline, without resetting capital.
The original job remains immutable. An overlapping collector bridges its end;
its archived snapshots reconstruct account state, then the same rules continue.
"""
import datetime as dt
import gzip
import hashlib
import io
import json
import math
import os
import pathlib
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile
import memecoin_hour_lab as lab

END_ISO = '2026-09-18T18:30:00+00:00'
END = dt.datetime.fromisoformat(END_ISO).timestamp()
PARENT_RUN = 35371372217
REPO = 'juan04delreal/MemeHunterAI'
OUT = pathlib.Path('extension_results')
START = pathlib.Path('parent_start/manifest.json')
PARENT = OUT/'original_hour'
POLICY = dict(version='EXTEND_TO_1430_ET_V1', mode='PAPER_ONLY', end_at=END_ISO,
              parent_run=PARENT_RUN, parent_commit='6ed5ecf817d6de7f874baddd2c65fd948854585c',
              entry_cutoff_at=lab.utc(END-300), interval_seconds=30,
              selection='Exact original tokens and pools; no replacements or new discoveries',
              continuity='Original observations take precedence during overlap; no cash or entry-count reset',
              changed_rules=['Extend scheduled horizon to 14:30 Eastern; stop new entries at 14:25 Eastern'],
              unchanged_rules='All entry signals, stops, targets, trailing exits, holding limits, costs, delays and session entry caps',
              method='Chronological fixed-rule state reconstruction followed by live continuation; no future quote access',
              boundary='Final observation is requested at deadline; retrieval may finish seconds later')

def save(name,obj):
    p=OUT/name; p.parent.mkdir(parents=True,exist_ok=True)
    tmp=p.with_suffix(p.suffix+'.tmp')
    tmp.write_text(json.dumps(obj,indent=2,allow_nan=False)); tmp.replace(p)

def load(path):
    return json.loads(pathlib.Path(path).read_text())

def records(path):
    with gzip.open(path,'rt') as f:
        return [json.loads(line) for line in f if line.strip()]

def prepare():
    if time.time()>=END: raise RuntimeError('Requested deadline has already passed; no retroactive live test')
    manifest=load(START)
    if manifest['config']!=lab.CFG: raise RuntimeError('Original strategy configuration mismatch')
    source=pathlib.Path(lab.__file__).read_bytes()
    if hashlib.sha256(source).hexdigest()!=manifest['code_sha256']:
        raise RuntimeError('Original strategy source hash mismatch')
    save('manifest.json',dict(policy=POLICY,frozen_at=lab.utc(),original_manifest=manifest,
                             extension_code_sha256=hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest()))
    (OUT/'original_strategy.py').write_bytes(source)
    (OUT/'extension_source.py').write_bytes(pathlib.Path(__file__).read_bytes())
    print('EXTENSION_FROZEN '+json.dumps(POLICY),flush=True)

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs): return None

def github_get(path,archive=False):
    token=os.environ.get('GH_TOKEN','')
    if not token: raise RuntimeError('Missing read-only GitHub artifact token')
    url='https://api.github.com/repos/'+REPO+'/'+path
    req=urllib.request.Request(url,headers={'Accept':'application/vnd.github+json',
        'Authorization':'Bearer '+token,'User-Agent':'PaperResearchExtension/1.0','X-GitHub-Api-Version':'2022-11-28'})
    try:
        with urllib.request.build_opener(NoRedirect).open(req,timeout=12) as r:
            body=r.read(64000001 if archive else 2000000)
    except urllib.error.HTTPError as exc:
        if not archive or exc.code not in (301,302,303,307,308): raise
        location=exc.headers.get('Location','')
        if urllib.parse.urlsplit(location).scheme!='https': raise RuntimeError('Non-HTTPS archive redirect refused')
        # Never forward the GitHub Authorization header to blob storage.
        with urllib.request.urlopen(urllib.request.Request(location,headers={'User-Agent':'PaperResearchExtension/1.0'}),timeout=25) as r:
            body=r.read(64000001)
    if len(body)>64000000: raise RuntimeError('Artifact exceeds safety size limit')
    return body if archive else json.loads(body)

def parent_available():
    if (PARENT/'snapshots.jsonl.gz').exists(): return True
    data=github_get(f'actions/runs/{PARENT_RUN}/artifacts?per_page=100')
    matches=[a for a in data.get('artifacts',[]) if a['name']==f'memecoin-hour-results-{PARENT_RUN}' and not a.get('expired')]
    if not matches: return False
    a=matches[0]; raw=github_get(f"actions/artifacts/{a['id']}/zip",True)
    digest='sha256:'+hashlib.sha256(raw).hexdigest()
    if a.get('digest') and a['digest']!=digest: raise RuntimeError('Parent artifact digest mismatch')
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        if sum(i.file_size for i in z.infolist())>128000000: raise RuntimeError('Uncompressed artifact too large')
        for item in z.infolist():
            name=pathlib.PurePosixPath(item.filename)
            if name.is_absolute() or '..' in name.parts or ((item.external_attr>>16)&0o170000)==0o120000:
                raise RuntimeError('Unsafe archive path')
        z.extractall(PARENT)
    save('parent_artifact.json',dict(id=a['id'],name=a['name'],digest=digest,received_at=lab.utc()))
    return True

class Engine:
    def __init__(self,manifest,parent_samples,parent_ledger):
        self.tokens=manifest['tokens']; self.pools={q['mint']:q['pool'] for q in self.tokens}
        self.hs={m:[] for m in self.pools}; self.quarantine={}; self.flags=[]; self.samples=[]
        self.books=[lab.Book(s,d,c) for s in lab.CFG['strategies'] for d in lab.CFG['delays'] for c in lab.CFG['slippage']]
        if not parent_samples: raise RuntimeError('Original observations missing')
        self.parent_end=parent_samples[-1]['ts']; self.start=parent_samples[0]['ts']; self.last=-math.inf
        for sample in parent_samples: self.apply(sample,True)
        cutoff=self.start+3290  # before the original final-five-minute entry cutoff
        checks={}
        for b in self.books:
            expected=[e for e in parent_ledger[b.id]['events'] if e.get('ts',e.get('exit_ts',math.inf))<cutoff]
            actual=[e for e in b.events if e.get('ts',e.get('exit_ts',math.inf))<cutoff]
            checks[b.id]=dict(matches=(actual==expected),original_events=len(expected),replayed_events=len(actual))
        self.validation=checks
        if not all(v['matches'] for v in checks.values()): raise RuntimeError('Original pre-extension ledger failed reproducibility validation')
    def apply(self,sample,parent=False):
        t=sample['ts']
        if t<=self.last: return
        if not parent and t<=self.parent_end: return
        qs={}
        for m,q in sample['quotes'].items():
            if m not in self.pools or q['pool']!=self.pools[m] or q['p']<=0: continue
            if not parent and self.hs[m] and abs(q['p']/self.hs[m][-1][1]-1)>.50:
                old=self.quarantine.get(m)
                if not old or t-old[0]>90 or abs(q['p']/old[1]-1)>.15:
                    self.quarantine[m]=(t,q['p']); self.flags.append(dict(ts=t,mint=m,flag='EXTREME_FIRST_OBSERVATION_QUARANTINED',price=q['p'])); continue
                self.flags.append(dict(ts=t,mint=m,flag='REPEATED_NOT_INDEPENDENTLY_VERIFIED',price=q['p']))
            self.quarantine.pop(m,None); qs[m]=q; self.hs[m].append([t,q['p']])
        for b in self.books: b.step(t,qs,self.hs,t<END-300,t>=END)
        self.samples.append(dict(ts=t,quotes=qs,source='original_hour' if parent else 'extension'))
        self.last=t
    def report(self):
        stats=[]
        for q in self.tokens:
            h=self.hs[q['mint']]
            stats.append(dict(mint=q['mint'],symbol=q['symbol'],pool=q['pool'],samples=len(h),
                              first_ts=h[0][0] if h else None,last_ts=h[-1][0] if h else None,
                              first_price=h[0][1] if h else None,last_price=h[-1][1] if h else None,
                              change_pct=100*(h[-1][1]/h[0][1]-1) if h else None,
                              maximum_gap_seconds=max((b[0]-a[0] for a,b in zip(h,h[1:])),default=None)))
        return dict(started_at=lab.utc(self.start),last_observation_at=lab.utc(self.last),
                    observed_span_seconds=self.last-self.start,reached_requested_deadline=self.last>=END,
                    parent_observations=sum(s['source']=='original_hour' for s in self.samples),
                    extension_observations=sum(s['source']=='extension' for s in self.samples),
                    original_prefix_reproduction=self.validation,universe=stats,
                    books=[b.summary() for b in self.books],quality_flags=self.flags,
                    maximum_observation_gap_seconds=max((b['ts']-a['ts'] for a,b in zip(self.samples,self.samples[1:])),default=None))

def run():
    frozen=load(OUT/'manifest.json')
    if frozen['policy']!=POLICY: raise RuntimeError('Frozen extension policy mismatch')
    manifest=frozen['original_manifest']; pools={q['mint']:q['pool'] for q in manifest['tokens']}
    lab.ROOT=OUT; lab.ERRORS.clear(); buffered=[]; engine=None; attach_error=None; errors=[]
    started=time.time(); next_parent=0; due=started; success=False; fatal=None
    save('started.json',dict(started_at=lab.utc(started),target_end=END_ISO,mode='PAPER_ONLY',tokens=list(pools)))
    print('EXTENSION_COLLECTOR_STARTED '+lab.utc(started)+' UNTIL '+END_ISO,flush=True)
    try:
        while True:
            pairs,meta=lab.dex(list(pools)); t=meta['received_ts']; qs={}
            if meta['http_age_seconds']<=90:
                for p in pairs:
                    q=lab.quote(p,t); m=q['mint']
                    if m in pools and q['pool']==pools[m] and q['p']>0: qs[m]=q
            sample=dict(ts=t,quotes=qs,meta=meta)
            buffered.append(sample); lab.append('extension_snapshots.jsonl.gz',sample)
            final=t>=END
            if engine is None and (t>=next_parent or final):
                next_parent=t+120
                try:
                    if parent_available():
                        original=load(PARENT/'manifest.json')
                        if original!=manifest: raise RuntimeError('Original manifest differs from frozen selection')
                        candidate=Engine(manifest,records(PARENT/'snapshots.jsonl.gz'),load(PARENT/'ledger.json'))
                        for prior in buffered: candidate.apply(prior)
                        engine=candidate; attach_error=None
                        save('continuation_started.json',dict(at=lab.utc(),parent_end=lab.utc(engine.parent_end),validation=engine.validation))
                        print('ORIGINAL_STATE_RECONSTRUCTED_AND_CONTINUING '+lab.utc(),flush=True)
                except Exception as exc:
                    attach_error=str(exc)[:300]; errors.append(dict(at=lab.utc(),stage='parent_attach',error=attach_error))
                    print('PARENT_ATTACH_RETRY '+attach_error,flush=True)
            elif engine is not None:
                engine.apply(sample)
            if len(buffered)%2==1 or final:
                status=dict(at=lab.utc(t),deadline=END_ISO,collected_samples=len(buffered),valid_tokens=len(qs),
                            parent_attached=engine is not None,books=[b.summary() for b in engine.books] if engine else [])
                save('checkpoint.json',status); print('EXTENSION_HEARTBEAT '+json.dumps(status),flush=True)
            if final: success=True; break
            due=min(END,max(due+30,time.time()))
            time.sleep(max(0,due-time.time()))
    except Exception as exc:
        fatal=str(exc)[:300]; print('EXTENSION_ERROR '+fatal,flush=True)
    finally:
        report=dict(mode='PAPER_ONLY_FIXED_RULE_RECONSTRUCTION_AND_FORWARD_CONTINUATION',policy=POLICY,
                    collector_started_at=lab.utc(started),collector_ended_at=lab.utc(),collector_reached_deadline=success,
                    collector_samples=len(buffered),parent_attached=engine is not None,parent_attach_error=attach_error,
                    fatal_error=fatal,api_errors=lab.ERRORS,other_errors=errors,
                    limitations=lab.LIMITS+[
                      'Original job closes at its original horizon. Extended account state is reconstructed from its snapshots with only the user-requested horizon changed.',
                      'No cash, strategy parameters, or per-token entry counts reset at the join. Overlapping observations are not counted twice.',
                      'The extended result is not a sum of the original and extension profits; report each horizon separately.',
                      'Anomaly quarantine state at the join is conservatively restarted; an extreme move can incur an extra confirmation sample.',
                      'A short single-session sample cannot establish sustainable profit.'])
        if engine:
            report.update(engine.report())
            save('ledger.json',{b.id:dict(events=b.events,trades=b.trades,equity=b.curve) for b in engine.books})
            with gzip.open(OUT/'combined_snapshots.jsonl.gz','wt') as f:
                for sample in engine.samples: f.write(json.dumps(sample,allow_nan=False)+'\n')
        save('report.json',report)
        print('EXTENDED_REPORT_JSON_BEGIN\n'+json.dumps(report)+'\nEXTENDED_REPORT_JSON_END',flush=True)
    if fatal or engine is None: raise SystemExit(1)

def self_test():
    lab.self_test()
    q=dict(mint='m',pool='p',symbol='SYNTHETIC_TEST',p=1.,liq=100000.,buys=40,sells=20,vol=10000.)
    start=END-5000
    samples=[dict(ts=start+i*30,quotes={'m':dict(q,ts=start+i*30)}) for i in range(121)]
    manifest=dict(tokens=[q]); hs={'m':[]}
    books=[lab.Book(s,d,c) for s in lab.CFG['strategies'] for d in lab.CFG['delays'] for c in lab.CFG['slippage']]
    for i,s in enumerate(samples):
        hs['m'].append([s['ts'],1.])
        for b in books: b.step(s['ts'],s['quotes'],hs,i*30<3300,i==120)
    engine=Engine(manifest,samples,{b.id:dict(events=b.events) for b in books})
    assert all(b.pos for b in engine.books if b.strategy=='hold')
    count=len(engine.samples); engine.apply(samples[-1]); assert len(engine.samples)==count
    engine.apply(dict(ts=END,quotes={'m':dict(q,ts=END)}))
    assert not any(b.pos for b in engine.books)
    assert all(sum(b.count.values())==1 for b in engine.books if b.strategy=='hold')
    assert all(498<b.cash<500 for b in engine.books if b.strategy=='hold' and b.slip==.01)
    assert engine.report()['reached_requested_deadline']
    print('EXTENSION_SELF_TEST_PASS: prefix reproduction, preserved holdings, no capital reset, overlap deduplication, single horizon liquidation. Synthetic fixtures only.',flush=True)

if __name__=='__main__':
    modes={'prepare':prepare,'run':run,'self-test':self_test}
    if len(sys.argv)!=2 or sys.argv[1] not in modes: raise SystemExit('Usage: memecoin_until_1430.py prepare|run|self-test')
    modes[sys.argv[1]]()
