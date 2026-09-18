#!/usr/bin/env python3
"""PAPER ONLY. Public-data forward experiment; never signs or submits trades."""
import collections
import datetime as dt
import email.utils
import gzip
import hashlib
import json
import math
import pathlib
import sys
import time
import urllib.request

ROOT = pathlib.Path('paper_results')
ROOT.mkdir(exist_ok=True)
CFG = dict(version='HOUR_LAB_1', seconds=3600, interval=30, cash=500., budget=25.,
           liquidity=25000., max_tokens=16, max_entries_per_token=2,
           delays=[30,90], slippage=[.01,.03], fee=.01, fixed_fee=.05,
           strategies=['hold','momentum','pullback'], entry_cutoff=3300,
           stop=.08, target=.20, trail_activation=.10, trail=.07, max_hold=720)
SEEDS = ['98kfF7rmsg1QDUEoCqNE7g7M1FdrTt92TEp2CLzypump',
         'GY9mZfyPpxXxBXBxS2hB2XjhP3kfUsywTvgveozxpump']
LIMITS = [
 'Paper mark-based fills, NOT executable quotes or real trades.',
 'Fees and slippage are explicit assumptions, not measured costs.',
 'HTTP response time cannot establish freshness of the underlying price.',
 'Thirty-second sampling misses intra-sample moves, including deeper drawdowns.',
 'Trending/recent-profile pump-suffix convenience sample is not representative of all memecoins.',
 'Twelve overlapping configurations are correlated, not twelve independent experiments.',
 'One hour cannot establish repeatable profitability. No insider-wallet or copy-trading test is performed.',
 'Contracts are not audited. Modeled exits may be impossible in real trading.',
 'Unresolved positions retain a marked value; a separate zero-recovery value is reported.',
 'GeckoTerminal checks are spot checks, not proof that every DexScreener mark is accurate.'
]
ERRORS = []

def utc(t=None):
    return dt.datetime.fromtimestamp(time.time() if t is None else t,dt.timezone.utc).isoformat()

def n(x,default=0.):
    try:
        y=float(x)
        return y if math.isfinite(y) else default
    except (ValueError,TypeError):
        return default

def save(name,obj):
    p=ROOT/name; tmp=p.with_suffix('.tmp')
    tmp.write_text(json.dumps(obj,indent=2,allow_nan=False),encoding='utf-8'); tmp.replace(p)

def append(name,obj):
    with gzip.open(ROOT/name,'at',encoding='utf-8') as f:
        f.write(json.dumps(obj,allow_nan=False)+'\n')

def get(url):
    started=time.time()
    try:
        req=urllib.request.Request(url,headers={'User-Agent':'MemecoinPaperResearch/1.0','Accept':'application/json'})
        with urllib.request.urlopen(req,timeout=12) as r:
            raw=r.read(8000000); h={k.lower():v for k,v in r.headers.items()}
        data=json.loads(raw); now=time.time(); age=n(h.get('age'))
        try: age=max(age,now-email.utils.parsedate_to_datetime(h['date']).timestamp())
        except (KeyError,TypeError,ValueError): pass
        meta=dict(url=url,requested_at=utc(started),received_ts=now,http_age_seconds=age,
                  http_date=h.get('date'),sha256=hashlib.sha256(raw).hexdigest())
        append('raw_api.jsonl.gz',dict(meta=meta,data=data))
        return data,meta
    except Exception as exc:
        error=dict(at=utc(),url=url,error=str(exc)[:300]); ERRORS.append(error)
        append('api_errors.jsonl.gz',error)
        print('API_ERROR '+json.dumps(error),flush=True)
        return None,dict(received_ts=time.time(),http_age_seconds=1e9)

def dex(mints):
    data,meta=get('https://api.dexscreener.com/tokens/v1/solana/'+','.join(mints))
    if isinstance(data,dict): data=data.get('pairs',[])
    return data if isinstance(data,list) else [],meta

def quote(p,ts):
    tx=((p.get('txns') or {}).get('m5') or {})
    return dict(mint=(p.get('baseToken') or {}).get('address'),
                symbol=(p.get('baseToken') or {}).get('symbol','?'),pool=p.get('pairAddress'),
                ts=ts,p=n(p.get('priceUsd')),liq=n((p.get('liquidity') or {}).get('usd')),
                vol=n((p.get('volume') or {}).get('m5')),buys=n(tx.get('buys')),sells=n(tx.get('sells')))

def init():
    candidates=list(SEEDS); discoveries=[]
    for page in (1,2):
        url=f'https://api.geckoterminal.com/api/v2/networks/solana/trending_pools?page={page}&include=base_token'
        data,_=get(url)
        for p in (data or {}).get('data',[]) if isinstance(data,dict) else []:
            attrs=p.get('attributes',{})
            mint=p.get('relationships',{}).get('base_token',{}).get('data',{}).get('id','').removeprefix('solana_')
            try: age=time.time()-dt.datetime.fromisoformat(attrs['pool_created_at'].replace('Z','+00:00')).timestamp()
            except (KeyError,ValueError): continue
            if mint.endswith('pump') and 300<=age<=604800 and n(attrs.get('reserve_in_usd'))>=25000 and mint not in candidates:
                candidates.append(mint); discoveries.append(dict(mint=mint,source=url,age_seconds=age))
    if len(candidates)<8:
        url='https://api.dexscreener.com/token-profiles/latest/v1'; data,_=get(url)
        for p in data if isinstance(data,list) else []:
            mint=p.get('tokenAddress','')
            if p.get('chainId')=='solana' and mint.endswith('pump') and mint not in candidates:
                candidates.append(mint); discoveries.append(dict(mint=mint,source=url,bias='recent_profile'))
    candidates=candidates[:30]; pairs,meta=dex(candidates)
    if meta['http_age_seconds']>90: raise RuntimeError('No acceptable initial API response; no hour started')
    tokens=[]; excluded=[]
    for mint in candidates:
        choices=[p for p in pairs if (p.get('baseToken') or {}).get('address')==mint]
        if not choices: excluded.append(dict(mint=mint,reason='missing')); continue
        p=max(choices,key=lambda x:n((x.get('liquidity') or {}).get('usd')))
        q=quote(p,meta['received_ts'])
        if q['p']<=0 or q['liq']<25000 or q['vol']<1000 or q['buys']+q['sells']<10:
            excluded.append(dict(mint=mint,reason='initial_filter',quote=q)); continue
        tokens.append(q)
        if len(tokens)==CFG['max_tokens']: break
    if not tokens: raise RuntimeError('No eligible tokens; no hour started')
    manifest=dict(config=CFG,frozen_at=utc(),tokens=tokens,excluded=excluded,discovery=discoveries,
                  limitations=LIMITS,api_errors=ERRORS,code_sha256=hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest())
    save('manifest.json',manifest)
    print('FROZEN_UNIVERSE '+json.dumps(manifest),flush=True)

def window(h,t,seconds,count):
    w=[(x,p) for x,p in h if t-seconds<=x<=t]
    if len(w)<count or w[0][0]>t-seconds+45: return []
    if any(b[0]-a[0]>90 for a,b in zip(w,w[1:])): return []
    return w

def eligible(q):
    return q and q['p']>0 and q['liq']>=25000 and q['buys']+q['sells']>=10 and q['vol']>=1000

def signal(s,q,h,t):
    if not eligible(q): return False
    if s=='hold': return True
    total=q['buys']+q['sells']
    if total<20 or q['vol']<5000: return False
    if s=='momentum':
        w=window(h,t,300,8)
        prior=[p for x,p in w if t-180<=x<t]
        return bool(w and prior and q['buys']/total>=.55 and .03<=q['p']/w[0][1]-1<=.30 and q['p']>=max(prior))
    w=window(h,t,600,16)
    if not w or q['buys']/total<.50: return False
    high=max(p for _,p in w); past=[p for x,p in w if x<=t-60]
    return bool(past and high/w[0][1]-1>=.05 and .03<=1-q['p']/high<=.10 and q['p']/past[-1]-1>=.005)

class Book:
    def __init__(self,strategy,delay,slip):
        self.strategy=strategy; self.delay=delay; self.slip=slip
        self.id=f'{strategy}_{delay}s_{int(slip*100)}pct'; self.cash=500.
        self.pos={}; self.pending={}; self.count=collections.Counter(); self.cool={}
        self.events=[]; self.trades=[]; self.curve=[]; self.signals=0; self.cancelled=0
    def value(self,pos,mark):
        return max(0.,pos['qty']*mark*(1-self.slip)*(1-CFG['fee'])-CFG['fixed_fee'])
    def sell(self,m,q,t,reason):
        pos=self.pos.pop(m); proceeds=self.value(pos,q['p']); self.cash+=proceeds; self.cool[m]=t+180
        tr=dict(book=self.id,mint=m,symbol=pos['symbol'],signal_ts=pos['signal_ts'],entry_ts=pos['entry_ts'],
                exit_ts=t,entry_mark=pos['entry_mark'],exit_mark=q['p'],budget=25.,proceeds=proceeds,
                pnl=proceeds-25.,return_pct=(proceeds/25.-1)*100,reason=reason,quantity=pos['qty'],
                entry_delay_seconds=pos['entry_ts']-pos['signal_ts'],exit_signal_ts=pos.get('exit_signal_ts'))
        self.trades.append(tr); self.events.append(dict(action='PAPER_SELL',**tr))
    def step(self,t,qs,hs,entries=True,final=False):
        for m,pos in list(self.pos.items()):
            q=qs.get(m)
            if not q or q['liq']<10000 or q['buys']+q['sells']<=0: continue
            if final: self.sell(m,q,t,'PREPLANNED_HORIZON_CLOSE'); continue
            if pos.get('due') is not None:
                if t>=pos['due']: self.sell(m,q,t,pos['reason'])
                continue
            if self.strategy=='hold': continue
            pos['peak']=max(pos['peak'],q['p']); ret=q['p']/pos['entry_mark']-1; reason=None
            if q['liq']<25000 or q['liq']<pos['entry_liq']*.5: reason='LIQUIDITY_LOSS'
            elif ret<=-CFG['stop']: reason='STOP_OBSERVED'
            elif ret>=CFG['target']: reason='TARGET_OBSERVED'
            elif pos['peak']/pos['entry_mark']-1>=CFG['trail_activation'] and q['p']<=pos['peak']*(1-CFG['trail']): reason='TRAIL_OBSERVED'
            elif t-pos['entry_ts']>=CFG['max_hold']: reason='MAX_HOLD'
            if reason: pos.update(due=t+self.delay,reason=reason,exit_signal_ts=t)
        if not entries or final:
            self.cancelled+=len(self.pending); self.pending.clear()
        else:
            for m,order in list(self.pending.items()):
                if t<order['due']: continue
                q=qs.get(m)
                if t-order['due']>90 or (q and abs(q['p']/order['mark']-1)>.20):
                    del self.pending[m]; self.cancelled+=1; self.cool[m]=t+180; continue
                if not eligible(q) or self.cash<25: continue
                qty=(25.-CFG['fixed_fee'])/((1+CFG['fee'])*q['p']*(1+self.slip))
                self.pos[m]=dict(qty=qty,entry_mark=q['p'],entry_ts=t,entry_liq=q['liq'],peak=q['p'],symbol=q['symbol'],signal_ts=order['signal_ts'])
                self.cash-=25; self.count[m]+=1; del self.pending[m]
                self.events.append(dict(action='PAPER_BUY',book=self.id,mint=m,ts=t,mark=q['p'],qty=qty,budget=25.,signal_ts=order['signal_ts']))
            for m,q in qs.items():
                if m in self.pos or m in self.pending or self.count[m]>=(1 if self.strategy=='hold' else 2) or t<self.cool.get(m,0): continue
                if signal(self.strategy,q,hs[m],t):
                    self.pending[m]=dict(due=t+self.delay,signal_ts=t,mark=q['p']); self.signals+=1
        marked=self.cash+sum(self.value(p,hs[m][-1][1] if hs[m] else p['entry_mark']) for m,p in self.pos.items())
        self.curve.append([t,marked])
    def summary(self):
        pnls=[t['pnl'] for t in self.trades]; gain=sum(p for p in pnls if p>0); loss=-sum(p for p in pnls if p<0)
        peak=500.; dd=0.
        for _,e in self.curve: peak=max(peak,e); dd=max(dd,(peak-e)/peak)
        equity=self.curve[-1][1] if self.curve else 500.
        return dict(book=self.id,strategy=self.strategy,delay_seconds=self.delay,slippage_per_side=self.slip,
                    cash=self.cash,modeled_equity=equity,modeled_net_pnl=equity-500.,
                    closed_pnl=sum(pnls),unresolved_positions=len(self.pos),unresolved_mints=list(self.pos),
                    zero_recovery_equity=self.cash,signals=self.signals,cancelled=self.cancelled,buys=sum(self.count.values()),
                    closed=len(pnls),wins=sum(p>0 for p in pnls),losses=sum(p<0 for p in pnls),
                    win_rate_pct=100*sum(p>0 for p in pnls)/len(pnls) if pnls else None,
                    profit_factor=gain/loss if loss else None,sampled_max_drawdown_pct=dd*100)

def run():
    manifest=json.loads((ROOT/'manifest.json').read_text())
    if manifest['config']!=CFG: raise RuntimeError('Frozen configuration mismatch')
    tokens=manifest['tokens']; pools={q['mint']:q['pool'] for q in tokens}; mints=list(pools)
    hs={m:[] for m in mints}; quarantined={}; flags=[]; checks=[]; samples=0
    books=[Book(s,d,c) for s in CFG['strategies'] for d in CFG['delays'] for c in CFG['slippage']]
    start=None; mono=None; next_poll=None; error=None; finished=False
    try:
        while True:
            pairs,meta=dex(mints); t=meta['received_ts']; qs={}
            if meta['http_age_seconds']<=90:
                for p in pairs:
                    q=quote(p,t); m=q['mint']
                    if m not in pools or q['pool']!=pools[m] or q['p']<=0: continue
                    if hs[m] and abs(q['p']/hs[m][-1][1]-1)>.50:
                        old=quarantined.get(m)
                        if not old or t-old[0]>90 or abs(q['p']/old[1]-1)>.15:
                            quarantined[m]=(t,q['p']); flags.append(dict(ts=t,mint=m,flag='EXTREME_FIRST_OBSERVATION_QUARANTINED',price=q['p'])); continue
                        flags.append(dict(ts=t,mint=m,flag='REPEATED_NOT_INDEPENDENTLY_VERIFIED',price=q['p']))
                    quarantined.pop(m,None); qs[m]=q
            if start is None:
                if not qs: raise RuntimeError('No valid opening quotes; hour did not start')
                start=t; mono=time.monotonic(); next_poll=mono
                save('started.json',dict(started_at=utc(start),target_end=utc(start+3600),opening=qs))
                print('EXPERIMENT_STARTED '+utc(start),flush=True)
            elapsed=time.monotonic()-mono; final=elapsed>=3600
            for m,q in qs.items(): hs[m].append([t,q['p']])
            for b in books: b.step(t,qs,hs,elapsed<3300,final)
            append('snapshots.jsonl.gz',dict(ts=t,elapsed_seconds=elapsed,meta=meta,quotes=qs)); samples+=1
            if samples%2==1 or final:
                checkpoint=dict(at=utc(t),elapsed_seconds=elapsed,valid_tokens=len(qs),samples=samples,books=[b.summary() for b in books])
                save('checkpoint.json',checkpoint); print('HEARTBEAT '+json.dumps(checkpoint),flush=True)
            if final: finished=True; break
            if (samples-1)%20==0:
                token=tokens[(((samples-1)//20))%len(tokens)]
                url=f"https://api.geckoterminal.com/api/v2/networks/solana/pools/{token['pool']}/ohlcv/minute?aggregate=1&limit=3&currency=usd&token=base"
                data,cm=get(url)
                candles=(data or {}).get('data',{}).get('attributes',{}).get('ohlcv_list',[]) if isinstance(data,dict) else []
                checks.append(dict(mint=token['mint'],at=utc(),dex_mark=qs.get(token['mint']),candles=candles))
            next_poll+=30
            if next_poll<time.monotonic(): next_poll=time.monotonic()
            time.sleep(max(0,next_poll-time.monotonic()))
    except Exception as exc:
        error=str(exc); print('TEST_ERROR '+error,flush=True)
    finally:
        end=time.time(); stats=[]
        for q in tokens:
            h=hs[q['mint']]; ps=[p for _,p in h]
            stats.append(dict(mint=q['mint'],symbol=q['symbol'],pool=q['pool'],samples=len(h),
                              first_ts=h[0][0] if h else None,last_ts=h[-1][0] if h else None,
                              first_price=ps[0] if ps else None,last_price=ps[-1] if ps else None,
                              change_pct=(ps[-1]/ps[0]-1)*100 if ps else None,
                              maximum_gap_seconds=max((b[0]-a[0] for a,b in zip(h,h[1:])),default=None)))
        report=dict(mode='PAPER_ONLY_AGGREGATOR_MARKS',config=CFG,started_at=utc(start) if start else None,
                    ended_at=utc(end),elapsed_seconds=end-start if start else 0,completed_full_hour=finished,
                    error=error,observations=samples,universe=stats,books=[b.summary() for b in books],
                    quality_flags=flags,api_errors=ERRORS,independent_spot_checks=checks,limitations=LIMITS)
        save('report.json',report)
        save('ledger.json',{b.id:dict(events=b.events,trades=b.trades,equity=b.curve) for b in books})
        print('REPORT_JSON_BEGIN\n'+json.dumps(report)+'\nREPORT_JSON_END',flush=True)
    if error: raise SystemExit(1)

def self_test():
    q=dict(p=1.,liq=100000.,buys=40,sells=20,vol=10000.,symbol='SYNTHETIC_TEST')
    hs={'m':[[0,1.]]}; b=Book('hold',30,.01)
    b.step(0,{'m':q},hs); assert not b.pos
    b.step(29,{'m':q},hs); assert not b.pos
    b.step(30,{'m':q},hs); assert b.cash==475 and len(b.pos)==1
    b.step(60,{'m':q},hs,False,True); assert 498<b.cash<500
    assert abs(b.cash-500-b.trades[0]['pnl'])<1e-8
    c=Book('hold',30,.03)
    for t in (0,30): c.step(t,{'m':q},hs)
    c.step(60,{'m':q},hs,False,True); assert c.cash<b.cash
    d=Book('hold',30,.01)
    for t in (0,30): d.step(t,{'m':q},hs)
    d.step(3600,{},hs,False,True); assert len(d.pos)==1 and not d.trades
    assert not signal('momentum',q,[[0,1.]],0)
    h=[[i*30,1+i*.004] for i in range(11)]
    assert signal('momentum',dict(q,p=h[-1][1]),h,300)
    assert not window([[0,1.],[200,1.],[300,1.]],300,300,3)
    d.strategy='momentum'; d.step(60,{'m':dict(q,p=.9)},hs,False)
    assert d.pos['m']['due']==90
    d.step(90,{'m':dict(q,p=.5)},hs,False)
    assert d.trades[0]['return_pct']<-45
    print('SELF_TEST_PASS: entry delay, accounting, cost stress, missing exit, warm-up, momentum, data gaps, uncapped delayed stop. Synthetic fixtures, not trading results.',flush=True)

if __name__=='__main__':
    modes={'self-test':self_test,'init':init,'run':run}
    if len(sys.argv)!=2 or sys.argv[1] not in modes: raise SystemExit('Usage: python3 memecoin_hour_lab.py self-test|init|run')
    modes[sys.argv[1]]()
