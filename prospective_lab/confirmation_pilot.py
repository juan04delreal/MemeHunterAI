"""Network-free forward confirmation experiment. Original paper accounts are untouched."""
from __future__ import annotations
import copy
import json
import math
import os
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from research_audit import canonical, fingerprint, units, routes

VERSION = 'confirmation-pilot-1.0'
USDC = 'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v'
WSOL = 'So11111111111111111111111111111111111111112'
SPEC = {'version':VERSION,'mode':'PAPER_ONLY','starting_cash_raw':500_000_000,
        'entry_input_raw':50_000_000,'entry_delay':300,'exit_horizon':300,
        'cost_bps':[100,300],'fixed_cost_raw':50_000,'max_open':3,
        'closed_loss_pause_raw':100_000_000,'min_quote_vault_lamports':50_000_000_000,
        'min_reserve_retention_bps':9000,'min_price_ratio_bps':10200,'max_price_ratio_bps':13000,
        'max_quoted_fraction_base_vault_bps':100,'max_observation_lag_seconds':30,
        'prior_delays':[60,120],'primary':'CONFIRM_C100','quotes_are_not_fills':True,
        'no_parameter_search':True,'no_network_requests':True,'max_request_lateness':20,
        'max_receipt_lateness':26,'missing_grace':60,'max_snapshot_age':20}
NOTE = ('FORWARD PROVISIONAL PAPER TEST, NOT VERIFIED FILLS OR GUARANTEED PROFIT. '
        'Four alternative 500-USDC accounts, not one combined portfolio. Primary CONFIRM_C100. '
        'Both filtered and baseline accounts use 300-second entry, 300-second exit, '
        'maximum three open/unresolved positions, and permanent new-entry pause once '
        'closed modeled P&L reaches -100 USDC. The pause is not a maximum-loss guarantee. '
        'Entry adds 1% or 3% plus 0.05 USDC; exit subtracts the same stress costs. '
        'Pre-entry gates use only 60/120-second quotes and their already-recorded pool '
        'snapshots available by the 300-second decision time. Gates are mechanistic '
        'hypotheses, not parameters optimized for historical profit. Token extensions '
        'and full routed execution are not independently validated. No earlier '
        'opportunities are imported. Original accounts and observations stay unchanged.')


def stamp(value):
    if isinstance(value,str):
        value=datetime.fromisoformat(value.replace('Z','+00:00')).timestamp()
    if isinstance(value,bool) or not isinstance(value,(float,int)) or not math.isfinite(value):
        raise ValueError('invalid_timestamp')
    return float(value)


def utc(t):
    return datetime.fromtimestamp(t,timezone.utc).isoformat(timespec='milliseconds')


def active(root,control_path=None):
    try:
        c=json.loads(Path(control_path or root/'control.json').read_text())
        cfg=json.loads((root/'config.json').read_text())
        return c.get('enabled') is True and c.get('mode')=='WATCH_ONLY' and cfg.get('mode')=='WATCH_ONLY'
    except (OSError,ValueError,TypeError,AttributeError):
        return False


def atomic(path,value):
    tmp=path.with_suffix(path.suffix+'.tmp')
    with tmp.open('w') as f:
        f.write(canonical(value)+'\n');f.flush();os.fsync(f.fileno())
    os.replace(tmp,path)


def initialize(now,quality_offset=0):
    accounts={}
    for name in ('CONFIRM','BASELINE'):
        for cost in SPEC['cost_bps']:
            aid=f'{name}_C{cost}'
            accounts[aid]={'cash':SPEC['starting_cash_raw'],'cost_bps':cost,
                'filtered':name=='CONFIRM','positions':{},'halted':False}
    return {'schema':1,'spec':copy.deepcopy(SPEC),'spec_sha256':fingerprint(SPEC),
            'started':now,'last_run':now,'watermark':now,'quality_offset':quality_offset,
            'quality':{},'source_hashes':{},'events':[],'gate_counts':{},'accounts':accounts}


def valid_quote(q,op,kind,scheduled,quantity):
    if q.get('status')!='quote_observed':
        return 'quote_unavailable_'+str(q.get('status','unknown'))[:40]
    try:
        raw=q['raw'];pair=(USDC,op['mint']) if kind=='entry' else (op['mint'],USDC)
        if (raw['inputMint'],raw['outputMint'])!=pair or raw.get('swapMode')!='ExactIn':
            return 'quote_pair_or_mode'
        if units(raw['inAmount'])!=quantity or units(raw['outAmount'])<1 or units(raw['contextSlot'])<1:
            return 'quote_quantity_or_context'
        if units(raw['otherAmountThreshold'])>units(raw['outAmount']):return 'invalid_minimum_output'
        if not isinstance(raw.get('routePlan'),list) or not raw['routePlan'] or not all(
                isinstance(p,dict) and isinstance(p.get('swapInfo'),dict) and p['swapInfo'].get('ammKey') for p in raw['routePlan']):
            return 'invalid_route_shape'
        req,received=stamp(q['requested_epoch']),stamp(q['received_epoch'])
        if (abs(stamp(q['scheduled_epoch'])-scheduled)>.01 or req<scheduled-.001 or received<req or
                req-scheduled>SPEC['max_request_lateness'] or received-scheduled>SPEC['max_receipt_lateness'] or
                q.get('timing_eligible') is not True or q.get('fills_assumed') is not False):
            return 'quote_timing_or_fill_flag'
    except (ValueError,KeyError,TypeError,OverflowError):return 'malformed_quote'
    return None


def admission(source,op,decision):
    a=source.get('migration_validation',{}).get(op['id'],{})
    try:
        if (a.get('status')!='confirmed_new_migration' or a.get('historical_reaudit') is not False or
            a.get('prospective_boundary_eligible') is not True or a.get('mint')!=op['mint'] or
            a.get('pool')!=op['pool'] or op.get('quote_mint')!=WSOL or op.get('future_information_used') is not False or
            stamp(a['checked_at'])>decision or stamp(op['first_observed_epoch'])>decision):
            return 'migration_not_confirmed_as_of_decision'
    except (KeyError,TypeError,ValueError):return 'migration_evidence_missing'
    return None


def confirmation_gate(op,quality,decision):
    evidence={'decision_epoch':decision,'thresholds_sha256':fingerprint(SPEC)}
    try:
        lag=stamp(op['first_observed_epoch'])-stamp(op['chain_block_time'])
        if not 0<=lag<=SPEC['max_observation_lag_seconds']:return 'late_or_unknown_discovery',evidence
        qs=[];snapshots=[]
        for delay in SPEC['prior_delays']:
            q=op.get('entry_quotes',{}).get(str(delay),{})
            reason=valid_quote(q,op,'entry',stamp(op['actionable_epoch'])+delay,SPEC['entry_input_raw'])
            if reason or stamp(q['received_epoch'])>decision:return 'prior_quote_unavailable_or_future',evidence
            if routes(q['raw'])!='serial_route_arithmetic_consistent_not_execution':return 'prior_route_not_verified',evidence
            s=quality.get(f"{op['id']}:entry:{delay}:")
            if not s or stamp(s['checked_at'])>decision:return 'prior_snapshot_missing_or_future',evidence
            if (s.get('status') not in ('pool_state_corroborated','requires_review') or
                set(s.get('flags',[]))-{'token_extensions_not_fully_validated'}):
                return 'prior_snapshot_quality_flag',evidence
            if (s['pool']['base_mint']!=op['mint'] or s['pool']['quote_mint']!=WSOL or
                s.get('opportunity_id')!=op['id'] or
                abs(stamp(s['quote_observed_at'])-stamp(q['received_epoch']))>.002 or
                not 0<=stamp(s['checked_at'])-stamp(q['received_epoch'])<=SPEC['max_snapshot_age'] or
                s['mint'].get('freeze_authority_present') is not False):
                return 'snapshot_identity_timing_or_freeze',evidence
            legs=[p['swapInfo'] for p in q['raw']['routePlan'] if p['swapInfo']['ammKey']==op['pool']]
            if len(legs)!=1 or (legs[0]['inputMint'],legs[0]['outputMint'])!=(WSOL,op['mint']):
                return 'prior_route_other_pool',evidence
            qs.append(q);snapshots.append(s)
        q0,q1=qs;s0,s1=snapshots
        out0,out1=units(q0['raw']['outAmount']),units(q1['raw']['outAmount'])
        reserve0,reserve1=units(s0['quote_vault']['amount_raw']),units(s1['quote_vault']['amount_raw'])
        base=units(s1['base_vault']['amount_raw'])
        evidence.update(price_ratio_bps=out0*10000//out1,
            reserve_retention_bps=reserve1*10000//reserve0 if reserve0 else None,
            quote_vault_raw=reserve1,quoted_base_fraction_bps=out1*10000//base if base else None,
            quote_hashes=[fingerprint(q) for q in qs],snapshot_hashes=[s['source_row_sha256'] for s in snapshots],
            token_extensions_fully_validated=all(s['mint'].get('extensions_fully_validated') is True for s in snapshots))
        if reserve1<SPEC['min_quote_vault_lamports']:return 'thin_quote_reserve',evidence
        if not reserve0 or reserve1*10000<reserve0*SPEC['min_reserve_retention_bps']:return 'quote_reserve_deterioration',evidence
        if not base or out1*10000>base*SPEC['max_quoted_fraction_base_vault_bps']:return 'entry_large_relative_to_inventory',evidence
        if not SPEC['min_price_ratio_bps']*out1<=out0*10000<=SPEC['max_price_ratio_bps']*out1:
            return 'no_moderate_price_confirmation',evidence
        return None,evidence
    except (KeyError,TypeError,ValueError,ZeroDivisionError,OverflowError):
        return 'incomplete_confirmation_evidence',evidence


def ingest_quality(state,path,source):
    if not path.exists():return True
    size=path.stat().st_size
    if size<state['quality_offset']:raise ValueError('quality_history_truncated')
    read=0
    with path.open('rb') as f:
        f.seek(state['quality_offset'])
        while read<2_000_000:
            begin=f.tell();line=f.readline(200_001)
            if not line:break
            if len(line)>200_000:raise ValueError('quality_row_oversize')
            if not line.endswith(b'\n'):break
            read+=len(line)
            row=json.loads(line);identity=row.get('id','')
            if ':entry:' in identity:
                oid,suffix=identity.rsplit(':entry:',1)
                op=source.get('opportunities',{}).get(oid)
                if suffix in {'60:','120:'} and op and stamp(op['first_observed_epoch'])>=state['started']:
                    slim={k:row[k] for k in ('id','opportunity_id','status','flags','checked_at','quote_observed_at','pool','mint','base_vault','quote_vault') if k in row}
                    slim['source_row_sha256']=fingerprint(row)
                    old=state['quality'].get(identity)
                    if old and old['source_row_sha256']!=slim['source_row_sha256']:raise ValueError('quality_observation_changed')
                    state['quality'][identity]=slim
            state['quality_offset']=f.tell()
    return state['quality_offset']>=size


def event_stream(source,start,now):
    result=[]
    for oid,op in source.get('opportunities',{}).items():
        if stamp(op.get('first_observed_epoch',0))<start:continue
        scheduled=stamp(op['actionable_epoch'])+SPEC['entry_delay']
        entry=op.get('entry_quotes',{}).get(str(SPEC['entry_delay']))
        q=entry
        if q is None and now>scheduled+SPEC['missing_grace']:
            q={'status':'absent_observation','observed_at':utc(scheduled+SPEC['missing_grace'])}
        if q is not None:
            when=stamp(q.get('received_epoch') if q.get('received_epoch') is not None else q['observed_at'])
            if when<=now:result.append((when,1,oid,q,op,scheduled))
        if not entry or entry.get('status')!='quote_observed' or entry.get('received_epoch') is None:continue
        scheduled=stamp(entry['received_epoch'])+SPEC['exit_horizon']
        q=op.get('exit_quotes',{}).get(str(SPEC['entry_delay']),{}).get(str(SPEC['exit_horizon']))
        if q is None and now>scheduled+SPEC['missing_grace']:
            q={'status':'absent_observation','observed_at':utc(scheduled+SPEC['missing_grace'])}
        if q is not None:
            when=stamp(q.get('received_epoch') if q.get('received_epoch') is not None else q['observed_at'])
            if when<=now:result.append((when,0,oid,q,op,scheduled))
    return sorted(result,key=lambda x:x[:3])


def record(state,aid,oid,action,when,now,reason,delta,detail):
    account=state['accounts'][aid]
    if account['cash']+delta<0:raise ValueError('negative_cash_prevented')
    account['cash']+=delta
    state['events'].append({'sequence':len(state['events'])+1,'account':aid,'opportunity':oid,
        'action':action,'observed':when,'booked':now,'reason':reason,'delta_raw':delta,
        'cash_after_raw':account['cash'],'detail':detail})


def consume(state,source,event,now):
    when,entry,oid,q,op,scheduled=event
    identity=f'{oid}:{entry}'
    source_hash=fingerprint({'quote':q,'mint':op['mint'],'pool':op['pool'],'scheduled':scheduled})
    old=state['source_hashes'].get(identity)
    if old:
        if old!=source_hash:raise ValueError('source_changed_no_rewrite')
        return
    state['source_hashes'][identity]=source_hash
    gate,evidence=confirmation_gate(op,state['quality'],scheduled) if entry else (None,{})
    if entry:
        key=gate or 'confirmation_pass';state['gate_counts'][key]=state['gate_counts'].get(key,0)+1
    for aid,account in state['accounts'].items():
        detail={'source_sha256':source_hash,'mint':op['mint'],'pool':op['pool'],'provisional':True,'verified_fill':False}
        if entry:
            reason='out_of_order_entry' if when<state['watermark'] else admission(source,op,scheduled)
            reason=reason or valid_quote(q,op,'entry',scheduled,SPEC['entry_input_raw'])
            if account['filtered']:
                reason=reason or gate;detail['confirmation_evidence']=evidence
            opened=[p for p in account['positions'].values() if p['status']!='CLOSED']
            extra=(SPEC['entry_input_raw']*account['cost_bps']+9999)//10000+SPEC['fixed_cost_raw']
            cost=SPEC['entry_input_raw']+extra
            reason=reason or ('closed_loss_budget_pause' if account['halted'] else None)
            reason=reason or ('position_limit' if len(opened)>=SPEC['max_open'] else None)
            reason=reason or ('duplicate_open_mint' if any(p['mint']==op['mint'] for p in opened) else None)
            reason=reason or ('insufficient_virtual_cash' if account['cash']<cost else None)
            if reason:
                record(state,aid,oid,'SKIP_ENTRY',when,now,reason,0,detail);continue
            qty=units(q['raw']['outAmount'])
            account['positions'][oid]={'mint':op['mint'],'quantity_raw':str(qty),'entry_cost':cost,
                'entry_epoch':when,'due':when+SPEC['exit_horizon'],'status':'OPEN','net_pnl_raw':None}
            detail.update(quantity_raw=str(qty),extra_cost_raw=extra)
            record(state,aid,oid,'MODEL_BUY',when,now,'frozen_forward_rule',-cost,detail)
        else:
            p=account['positions'].get(oid)
            if not p or p['status']!='OPEN':continue
            reason='out_of_order_exit' if when<state['watermark'] else valid_quote(q,op,'exit',scheduled,units(p['quantity_raw']))
            if not reason and abs(p['due']-scheduled)>.01:reason='position_clock_mismatch'
            if not reason:
                gross=units(q['raw']['outAmount']);extra=(gross*account['cost_bps']+9999)//10000+SPEC['fixed_cost_raw'];net=gross-extra
                if account['cash']+net<0:reason='insufficient_exit_cost_cash'
            if reason:
                p['status']='UNRESOLVED';record(state,aid,oid,'UNRESOLVED_EXIT',when,now,reason,0,detail);continue
            p.update(status='CLOSED',exit_net_raw=net,net_pnl_raw=net-p['entry_cost'])
            detail.update(quantity_raw=p['quantity_raw'],gross_quote_raw=gross,extra_cost_raw=extra,net_pnl_raw=p['net_pnl_raw'])
            record(state,aid,oid,'MODEL_SELL',when,now,'matching_quantity_300_second_exit',net,detail)
            if sum(p['net_pnl_raw'] for p in account['positions'].values() if p['status']=='CLOSED')<=-SPEC['closed_loss_pause_raw']:
                account['halted']=True
    state['watermark']=max(state['watermark'],when)


def reconcile(state):
    if state['schema']!=1 or state['spec']!=SPEC or state['spec_sha256']!=fingerprint(SPEC):raise ValueError('frozen_spec_or_schema_changed')
    expected={f'{name}_C{cost}' for name in ('CONFIRM','BASELINE') for cost in SPEC['cost_bps']}
    if set(state['accounts'])!=expected:raise ValueError('account_set_changed')
    for aid,a in state['accounts'].items():
        if a['cost_bps']!=int(aid.split('_C')[1]) or a['filtered']!=(aid.startswith('CONFIRM_')):
            raise ValueError('account_parameters_changed')
        events=[e for e in state['events'] if e['account']==aid];cash=SPEC['starting_cash_raw']
        for e in events:
            cash+=e['delta_raw']
            if cash<0 or e['cash_after_raw']!=cash:raise ValueError('cash_ledger_mismatch')
        opened=[p for p in a['positions'].values() if p['status']!='CLOSED']
        pnl=sum(p['net_pnl_raw'] for p in a['positions'].values() if p['status']=='CLOSED')
        if cash!=a['cash'] or len(opened)>SPEC['max_open'] or len({p['mint'] for p in opened})!=len(opened) or cash+sum(p['entry_cost'] for p in opened)!=SPEC['starting_cash_raw']+pnl:
            raise ValueError('account_reconciliation_failed')


def report(state,now):
    accounts=[]
    for aid,a in sorted(state['accounts'].items()):
        positions=list(a['positions'].values());closed=[p for p in positions if p['status']=='CLOSED'];opened=[p for p in positions if p['status']!='CLOSED']
        values=[p['net_pnl_raw'] for p in closed];win=sum(max(0,x) for x in values);loss=-sum(min(0,x) for x in values)
        accounts.append({'account':aid,'cash_usdc':a['cash']/1e6,'modeled_buys':len(positions),'closed':len(closed),
            'open':len(opened),'unresolved':sum(p['status']=='UNRESOLVED' for p in opened),'closed_modeled_pnl_usdc':sum(values)/1e6,
            'wins':sum(x>0 for x in values),'losses':sum(x<0 for x in values),'profit_factor':win/loss if loss else None,
            'book_equity_at_cost_usdc':(a['cash']+sum(p['entry_cost'] for p in opened))/1e6,
            'liquidation_equity_usdc':None if opened else a['cash']/1e6,'new_entries_paused':a['halted']})
    return {'version':VERSION,'status':'RUNNING','mode':'PAPER_ONLY','updated_at':utc(now),'started_at':utc(state['started']),
        'spec':SPEC,'spec_sha256':fingerprint(SPEC),'ledger_reconciled':True,'accounts':accounts,
        'primary':next(a for a in accounts if a['account']==SPEC['primary']),'gate_counts':state['gate_counts'],
        'quality_ingestion_caught_up':state.get('quality_ingestion_caught_up',True),'cash_benchmark_usdc':500,'all_results_provisional':True,'fully_validated_fills':0,'real_trades':0,
        'network_requests':0,'realized_profit':None,'notes':NOTE}


def run(source,root,now=None,control_path=None):
    root=Path(root);now=stamp(time.time() if now is None else now)
    if not active(root,control_path):return {'status':'STOPPED'}
    if source.get('schema')!=2:raise ValueError('unsupported_source_schema')
    d=root/'data'/'confirmation_pilot';path=d/'state.json';quality_path=root/'data'/'quote_quality.jsonl'
    if path.exists():state=json.loads(path.read_text())
    else:
        if (d/'latest.json').exists():raise ValueError('missing_state_no_cash_reset')
        state=initialize(now,quality_path.stat().st_size if quality_path.exists() else 0)
    reconcile(state)
    if now<state['last_run']:raise ValueError('clock_reversal')
    quality_caught_up=ingest_quality(state,quality_path,source)
    state['quality_ingestion_caught_up']=quality_caught_up
    if quality_caught_up:
        for event in event_stream(source,state['started'],now):consume(state,source,event,now)
    reconcile(state);state['last_run']=now
    if not active(root,control_path):return {'status':'STOPPED'}
    d.mkdir(parents=True,exist_ok=True)
    atomic(path,state)
    result=report(state,now);atomic(d/'latest.json',result);atomic(d/'health.json',{'status':'healthy' if quality_caught_up else 'quality_ingestion_backlog','updated_at':utc(now),'version':VERSION})
    return result


def safe_run(source,root,control_path=None):
    try:return run(source,root,control_path=control_path)
    except Exception as exc:
        result={'status':'error','updated_at':utc(time.time()),'version':VERSION,'error_type':type(exc).__name__}
        try:
            d=Path(root)/'data'/'confirmation_pilot';d.mkdir(parents=True,exist_ok=True);atomic(d/'health.json',result)
        except OSError:pass
        print('CONFIRMATION_PILOT_ERROR: '+type(exc).__name__)
        return result


if __name__=='__main__':
    root=Path(__file__).resolve().parent
    if active(root,os.environ.get('PROSPECTIVE_CONTROL_PATH')):
        try:
            path=root/'data'/'state.json'
            if path.stat().st_size>512*1024*1024:raise ValueError('source_size_bound')
            source=json.loads(path.read_text())
            result=safe_run(source,root,control_path=os.environ.get('PROSPECTIVE_CONTROL_PATH'))
            print(json.dumps({'confirmation_pilot_status':result['status'],'version':VERSION}))
        except Exception as exc:
            print('CONFIRMATION_PILOT_INPUT_ERROR: '+type(exc).__name__)
    else:
        print('{"confirmation_pilot_status":"STOPPED"}')
