#!/usr/bin/env python3
from __future__ import annotations
import json, os, time, urllib.request, urllib.error
from datetime import datetime, timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parent; DATA=ROOT/'data'
PUMPSWAP='pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA'\nPUMP='6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P'\nMIGRATE_DISC=[155,234,231,146,236,158,162,30]\nMAX_TX_VERSION=1\nALPHABET='123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'
WSOL='So11111111111111111111111111111111111111112'; USDC='EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v'
VERSION='prospective-quote-lab-0.2'
def utc(): return datetime.now(timezone.utc).isoformat(timespec='seconds')

def b58decode(s):
    n=0
    for c in s: n=n*58+ALPHABET.index(c)
    raw=n.to_bytes((n.bit_length()+7)//8,'big') if n else b''
    return b'\0'*(len(s)-len(s.lstrip('1')))+raw
def keystr(x): return x.get('pubkey','') if isinstance(x,dict) else str(x)
def decode_migration(tx):
    if not tx or (tx.get('meta') or {}).get('err') is not None: return None
    msg=(tx.get('transaction') or {}).get('message') or {}
    instructions=list(msg.get('instructions') or [])
    for group in (tx.get('meta') or {}).get('innerInstructions') or []: instructions.extend(group.get('instructions') or [])
    for ins in instructions:
        if ins.get('programId')!=PUMP or not isinstance(ins.get('data'),str): continue
        try:
            if list(b58decode(ins['data'])[:8])!=MIGRATE_DISC: continue
        except Exception: continue
        accounts=[keystr(a) for a in ins.get('accounts') or []]
        if len(accounts)<10: return None
        return {'mint':accounts[2],'pool':accounts[9],'quote_mint':WSOL,'decoder':'official_pump_idl_migrate_layout'}
    return None

def load(p,d): return json.loads(p.read_text()) if p.exists() else d
def save(p,o): p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(o,indent=2,sort_keys=True)+'\n')
def req(url,payload=None,headers=None):
    data=json.dumps(payload).encode() if payload is not None else None
    r=urllib.request.Request(url,data=data,headers={'User-Agent':'MemeHunterAI-Research/0.1','Content-Type':'application/json',**(headers or {})})
    try:
        with urllib.request.urlopen(r,timeout=12) as x: return json.loads(x.read(8_000_000))
    except Exception as e: return {'_error':type(e).__name__}
def rpc(method,params):
    url=os.environ.get('SOLANA_RPC_URL','').strip() or 'https://solana-rpc.publicnode.com'
    o=req(url,{'jsonrpc':'2.0','id':1,'method':method,'params':params})
    return o.get('result') if isinstance(o,dict) and not o.get('_error') and not o.get('error') else None
def jupiter_quote(input_mint,output_mint,amount):
    # Provider capability probe only. No wallet address, signing, or execution endpoint.
    key=os.environ.get('JUPITER_API_KEY','').strip()
    if not key: return {'status':'not_configured','observed_at':utc()}
    from urllib.parse import urlencode
    url='https://api.jup.ag/swap/v1/quote?'+urlencode({'inputMint':input_mint,'outputMint':output_mint,'amount':str(amount),'slippageBps':'100'})
    o=req(url,headers={'x-api-key':key})
    if isinstance(o,dict) and o.get('_error'): return {'status':'provider_error','error':o['_error'],'observed_at':utc()}
    return {'status':'quote_observed','observed_at':utc(),'raw':o}
def append_jsonl(path,row):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('a') as h: h.write(json.dumps(row,separators=(',',':'))+'\n')
def get_tx(sig):
    return rpc('getTransaction',[sig,{'encoding':'jsonParsed','commitment':'confirmed','maxSupportedTransactionVersion':MAX_TX_VERSION}])
def quote_entry(mint,amount_usdc_raw):
    return jupiter_quote(USDC,mint,amount_usdc_raw)
def quote_exit(mint,token_amount_raw):
    return jupiter_quote(mint,USDC,token_amount_raw)
def cycle():
    DATA.mkdir(parents=True,exist_ok=True); cfg=load(ROOT/'config.json',{}); ctl=load(ROOT/'control.json',{})
    if ctl.get('enabled') is not True or ctl.get('mode')!='WATCH_ONLY': return {'status':'STOPPED'}
    st=load(DATA/'state.json',{'schema':2,'started_at':utc(),'cycles':0,'seen':[],'opportunities':{},'errors':[]})
    if st.get('schema')!=2:
        st={'schema':2,'started_at':utc(),'cycles':0,'seen':[],'opportunities':{},'errors':['state_reset_from_feasibility_v0.1']}
    st['cycles']+=1; now=time.time(); now_iso=utc(); seen=set(st.get('seen',[]))
    slot=rpc('getSlot',[{'commitment':'confirmed'}]); rpc_ok=slot is not None; new_migrations=0
    sigs=rpc('getSignaturesForAddress',[PUMP,{'limit':100,'commitment':'confirmed'}]) if rpc_ok else None
    if isinstance(sigs,list):
        for h in reversed(sigs):
            sig=h.get('signature')
            if not sig or sig in seen or h.get('err') is not None: continue
            tx=get_tx(sig)
            if tx is None: continue
            seen.add(sig)
            mig=decode_migration(tx)
            if not mig: continue
            observed=time.time(); bt=tx.get('blockTime')
            op={'id':sig,'signature':sig,'mint':mig['mint'],'pool':mig['pool'],'quote_mint':mig['quote_mint'],
                'decoder':mig['decoder'],'chain_block_time':bt,'first_observed_at':utc(),'first_observed_epoch':observed,
                'actionable_at':utc(),'actionable_epoch':observed,
                'observation_lag_seconds':(observed-bt if isinstance(bt,(int,float)) else None),
                'selection_reason':'verified_pump_migrate_instruction','future_information_used':False,
                'wallet_evidence_as_of_decision':'unknown_not_collected','entry_quotes':{},'exit_quotes':{},'positions':{}}
            st['opportunities'][sig]=op; append_jsonl(DATA/'opportunities.jsonl',op); new_migrations+=1
    st['seen']=(st.get('seen',[])+[x for x in seen if x not in set(st.get('seen',[]))])[-20000:]

    # Fixed $50 USDC hypothetical input. No order building or submission occurs.
    request_budget=12
    for op in sorted(st['opportunities'].values(),key=lambda x:x['first_observed_epoch']):
        for delay in cfg.get('additional_delay_seconds',[30,60,120,300]):
            k=str(delay)
            if k in op['entry_quotes'] or time.time()<op['actionable_epoch']+delay or request_budget<=0: continue
            scheduled=op['actionable_epoch']+delay; requested=time.time()
            q=quote_entry(op['mint'],50_000_000)
            q.update({'scheduled_delay_seconds':delay,'scheduled_epoch':scheduled,'requested_epoch':requested,
                      'actual_delay_from_actionable_seconds':requested-op['actionable_epoch'],
                      'late_by_seconds':max(0,requested-scheduled),'hypothetical_input_usdc':50.0})
            op['entry_quotes'][k]=q; append_jsonl(DATA/'quotes.jsonl',{'opportunity_id':op['id'],'kind':'entry',**q}); request_budget-=1
            if q.get('status')=='quote_observed' and q.get('raw',{}).get('outAmount'):
                op['positions'][k]={'token_amount_raw':q['raw']['outAmount'],'entry_requested_epoch':requested,'entry_observed_at':q['observed_at']}
        if request_budget<=0: break

    for op in sorted(st['opportunities'].values(),key=lambda x:x['first_observed_epoch']):
        for entry_delay,pos in list(op.get('positions',{}).items()):
            exits=op['exit_quotes'].setdefault(entry_delay,{})
            for horizon in cfg.get('exit_horizons_seconds',[300,900,3600]):
                hk=str(horizon)
                if hk in exits or time.time()<pos['entry_requested_epoch']+horizon or request_budget<=0: continue
                scheduled=pos['entry_requested_epoch']+horizon; requested=time.time()
                q=quote_exit(op['mint'],int(pos['token_amount_raw']))
                q.update({'entry_delay_seconds':int(entry_delay),'exit_horizon_seconds':horizon,'scheduled_epoch':scheduled,
                          'requested_epoch':requested,'late_by_seconds':max(0,requested-scheduled),
                          'hypothetical_token_input_raw':pos['token_amount_raw']})
                exits[hk]=q; append_jsonl(DATA/'quotes.jsonl',{'opportunity_id':op['id'],'kind':'exit',**q}); request_budget-=1

    save(DATA/'state.json',st)
    entries=[q for o in st['opportunities'].values() for q in o.get('entry_quotes',{}).values()]
    exits=[q for o in st['opportunities'].values() for d in o.get('exit_quotes',{}).values() for q in d.values()]
    latest={'version':VERSION,'updated_at':utc(),'mode':'WATCH_ONLY','rpc_connected':rpc_ok,'slot':slot,'cycles':st['cycles'],
            'validated_migrations':len(st['opportunities']),'new_migrations_this_cycle':new_migrations,
            'entry_quotes_observed':sum(q.get('status')=='quote_observed' for q in entries),
            'exit_quotes_observed':sum(q.get('status')=='quote_observed' for q in exits),
            'quote_failures':sum(q.get('status')!='quote_observed' for q in entries+exits),
            'quote_provider_api_key_configured':bool(os.environ.get('JUPITER_API_KEY','').strip()),
            'real_trades_placed':0,'realized_profit':None}
    save(DATA/'latest.json',latest)
    lines=['# Prospective Quote Lab','','**WATCH ONLY — no trades.**','',f"Updated: {latest['updated_at']}",
           '',f"RPC connected: {rpc_ok}",f"Validated Pump migrations: {latest['validated_migrations']}",
           f"Observed entry quotes: {latest['entry_quotes_observed']}",f"Observed exit quotes: {latest['exit_quotes_observed']}",
           f"Quote failures/unavailable: {latest['quote_failures']}",f"Jupiter API key configured: {latest['quote_provider_api_key_configured']}",
           '','Migrations are admitted only from the official Pump migrate discriminator/account layout.',
           'Quote deadlines are measured from first actionable observation. Late observations remain late.',
           'Quotes are route snapshots, not fills. No realized profit is claimed.','',
           '## Recent opportunities','','| Mint | First observed | Lag from chain | Entry quote states |','|---|---|---:|---|']
    for op in sorted(st['opportunities'].values(),key=lambda x:x['first_observed_epoch'],reverse=True)[:20]:
        qs=', '.join(k+':'+v.get('status','?') for k,v in sorted(op.get('entry_quotes',{}).items(),key=lambda z:int(z[0]))) or 'none'
        lines.append(f"| {op['mint']} | {op['first_observed_at']} | {op.get('observation_lag_seconds')} | {qs} |")
    (DATA/'REPORT.md').write_text('\n'.join(lines)+'\n')
    return latest
if __name__=='__main__': print(json.dumps(cycle()))
