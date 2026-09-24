#!/usr/bin/env python3
"""Bounded v0.4 read-only collector; v0.3 quote clocks and raw history are retained."""
from __future__ import annotations
import copy
import json
import math
import os
import queue
import threading
import time
from pathlib import Path
from collections import Counter
import lab
import validation as v

VERSION = 'prospective-quote-lab-0.4'
READS = frozenset({'getSlot','getSignaturesForAddress','getTransaction','getAccountInfo','getMultipleAccounts'})
PAGE = 100
MAX_PENDING = 2000
MAX_FETCHES = 24
MAX_RPC = 40
SNAPSHOT_MAX_AGE = 20.0


def enabled():
    try:
        path = Path(os.environ.get('PROSPECTIVE_CONTROL_PATH','')) if os.environ.get('PROSPECTIVE_CONTROL_PATH') else lab.ROOT/'control.json'
        ctl = lab.load(path,{})
        return ctl.get('enabled') is True and ctl.get('mode')=='WATCH_ONLY'
    except (OSError,ValueError,TypeError):
        return False


class ReadBudget:
    def __init__(self, end, cooldown=0):
        self.end, self.cooldown, self.count = end, cooldown, 0
        self.lock = threading.Lock()
        self.next_start = 0.0
        self.errors = Counter()

    def __call__(self, method, params):
        if method not in READS:
            raise ValueError('rpc_method_not_allowlisted')
        with self.lock:
            if not enabled() or self.count>=MAX_RPC or time.monotonic()>=self.end or time.time()<self.cooldown:
                return None
            wait = max(0.0,self.next_start-time.monotonic())
            if time.monotonic()+wait>=self.end:
                return None
            if wait:
                time.sleep(wait)
            if not enabled():
                return None
            self.next_start = time.monotonic()+0.5
            self.count += 1
        url = os.environ.get('SOLANA_RPC_URL','').strip() or 'https://solana-rpc.publicnode.com'
        result = lab.req(url,{'jsonrpc':'2.0','id':1,'method':method,'params':params})
        if isinstance(result,dict) and not result.get('_error') and not result.get('error'):
            return result.get('result')
        with self.lock:
            label = str(result.get('http_status') or result.get('_error') or 'rpc_error') if isinstance(result,dict) else 'invalid_rpc_response'
            self.errors[label] += 1
            if isinstance(result,dict) and result.get('http_status') in (401,403,429,503):
                self.cooldown = max(self.cooldown,time.time()+max(60,float(result.get('retry_after_seconds') or 0)))
        return None


def fetch_tx(rpc, signature):
    return rpc('getTransaction',[signature,{'encoding':'jsonParsed','commitment':'confirmed','maxSupportedTransactionVersion':1}])


def poll_page(discovery, rpc, address, now):
    """A cursor advances only after every new signature in its page is retained."""
    cursor = discovery.setdefault('cursors',{}).setdefault(address,{})
    pending = discovery.setdefault('pending',{})
    known = set(discovery.setdefault('resolved',[])) | set(pending)
    discovery['page_deferred_backpressure'] = len(pending)>MAX_PENDING-PAGE
    if discovery['page_deferred_backpressure']:
        discovery['backpressure_cycles'] = discovery.get('backpressure_cycles',0)+1
        return None
    options = {'limit':PAGE,'commitment':'confirmed'}
    if cursor.get('anchor'):
        options['until'] = cursor['anchor']
    if cursor.get('before'):
        options['before'] = cursor['before']
    page = rpc('getSignaturesForAddress',[address,options])
    if not isinstance(page,list) or len(page)>PAGE:
        return None
    if any(not isinstance(h,dict) or not isinstance(h.get('signature'),str) for h in page):
        return None
    for h in page:
        sig = h['signature']
        if sig not in known:
            if h.get('err') is not None:
                discovery['resolved'].append(sig)
            else:
                pending[sig] = {'signature':sig,'slot':h.get('slot'),'blockTime':h.get('blockTime'),
                    'first_seen_epoch':now,'source_address':address,'attempts':0,'retry_at':now}
            known.add(sig)
    discovery['last_page_size'] = len(page)
    discovery['pages_received'] = discovery.get('pages_received',0)+1
    if not cursor.get('anchor'):
        if page:
            cursor['anchor'] = page[0]['signature']
            cursor['baseline_slot'] = page[0].get('slot')
            cursor['bootstrap_history_incomplete'] = True
    elif page:
        cursor.setdefault('sweep_head',page[0]['signature'])
        if len(page)==PAGE:
            cursor['before'] = page[-1]['signature']
        else:
            cursor['anchor'] = cursor.pop('sweep_head')
            cursor.pop('before',None)
            cursor['last_provider_range_reconciled_at'] = lab.utc(now)
    elif cursor.get('sweep_head'):
        cursor['anchor'] = cursor.pop('sweep_head')
        cursor.pop('before',None)
        cursor['last_provider_range_reconciled_at'] = lab.utc(now)
    else:
        cursor['last_provider_range_reconciled_at'] = lab.utc(now)
    return page


def discovery_worker(events, state, rpc, end):
    d = copy.deepcopy(state.get('discovery_v4',{}))
    try:
        now = time.time()
        slot = rpc('getSlot',[{'commitment':'confirmed'}])
        if isinstance(slot,int) and not isinstance(slot,bool):
            d.setdefault('start_slot',slot)
        if now-d.get('index_checked_epoch',0)>300:
            try:
                result = rpc('getAccountInfo',[v.GLOBAL,{'encoding':'base64','commitment':'confirmed'}])
                address = v.migration_index(result)
                old = d.get('index_address')
                if old and old!=address:
                    d['index_changes'] = d.get('index_changes',0)+1
                d.update(index_address=address,index_checked_epoch=now,index_status='verified_global_layout')
            except (ValueError,TypeError,KeyError):
                d['index_status'] = 'unavailable_or_unrecognized_global'
        address = d.get('index_address') if now-d.get('index_checked_epoch',0)<600 else None
        address = address or v.PUMP
        d['active_source'] = 'migration_authority_index' if address!=v.PUMP else 'pump_program_fallback'
        page = poll_page(d,rpc,address,now) if slot is not None else None
        events.put(('rpc',{'connected':slot is not None and (page is not None or d.get('page_deferred_backpressure',False)),
                          'discovery_page_deferred_backpressure':d.get('page_deferred_backpressure',False),'slot':slot,'checked_at':lab.utc(),
                          'signature_window_saturated':isinstance(page,list) and len(page)==PAGE}))
        # Re-audit old instruction-only records; never create historical quote windows.
        audits = state.get('migration_validation',{})
        legacy = [o for o in state['opportunities'].values() if o['id'] not in audits
                  and o.get('collector_version')!=VERSION][:2]
        jobs = [(o['signature'],{'legacy_id':o['id'],'mint':o['mint'],'pool':o['pool']}) for o in legacy]
        pending = d.setdefault('pending',{})
        eligible = [h for h in pending.values() if h.get('retry_at',0)<=now]
        fresh = sorted((h for h in eligible if h['attempts']==0),key=lambda h:h.get('slot') or 0,reverse=True)
        retry = sorted((h for h in eligible if h['attempts']>0),key=lambda h:h['retry_at'])
        selected = fresh[:16]+retry[:8]
        if len(selected)<MAX_FETCHES:
            chosen = {h['signature'] for h in selected}
            selected += [h for h in eligible if h['signature'] not in chosen][:MAX_FETCHES-len(selected)]
        jobs += [(h['signature'],h) for h in selected]
        for sig,header in jobs:
            if time.monotonic()>=end or not enabled():
                break
            tx = fetch_tx(rpc,sig)
            valid_identity = isinstance(tx,dict) and sig in (tx.get('transaction') or {}).get('signatures',[])
            if not valid_identity:
                events.put(('tx_failure',None))
                if 'legacy_id' not in header:
                    header['attempts'] += 1
                    header['retry_at'] = time.time()+min(300,2**min(header['attempts'],8))
                continue
            observed = time.time()
            evidence = v.audit_migrations(tx)
            if 'legacy_id' in header:
                match = next((a for a in evidence if a['mint']==header['mint'] and a['pool']==header['pool']),None)
                audit = match or {'status':'unresolved_instruction_or_evidence_missing','mint':header['mint'],'pool':header['pool']}
                events.put(('migration_audit',{'id':header['legacy_id'],'signature':sig,'historical_reaudit':True,
                    'checked_at':lab.utc(observed),'collector_version':VERSION,**audit}))
            else:
                for audit in evidence:
                    audit.update(id=sig+':'+audit['pool'],signature=sig,checked_at=lab.utc(observed),
                        collector_version=VERSION,historical_reaudit=False,first_seen_epoch=header['first_seen_epoch'],
                        observation_lag_seconds=observed-tx['blockTime'] if isinstance(tx.get('blockTime'),(int,float)) else None,
                        prospective_boundary_eligible=isinstance(tx.get('slot'),int) and tx['slot']>=d.get('start_slot',2**64))
                    events.put(('migration_audit',audit))
                if not evidence:
                    unsupported = False
                    for _,group in v.instruction_groups(tx):
                        for i in group:
                            try:
                                unsupported |= i.get('programId')==v.PUMP and v.un58(i.get('data',''))[:8]==bytes([187,203,18,31,206,237,254,41])
                            except (ValueError,TypeError):
                                pass
                    if unsupported:
                        d['out_of_scope_or_unrecognized_v2_transactions'] = d.get('out_of_scope_or_unrecognized_v2_transactions',0)+1
                pending.pop(sig,None)
                d.setdefault('resolved',[]).append(sig)
        d['resolved'] = d.get('resolved',[])[-20000:]
    except Exception as exc:
        events.put(('discovery_error',type(exc).__name__))
    finally:
        events.put(('discovery_state',d))


def pool_check(task, rpc):
    q,op = task['quote'], task['opportunity']
    result = {'id':task['id'],'opportunity_id':op['id'],'collector_version':VERSION,
        'quote_observed_at':q.get('observed_at'),'checked_at':lab.utc(),'status':'unavailable',
        'fully_validated_quote':False,'fills_assumed':False,
        'limitations':'RPC pool evidence is not an execution, full multi-hop/fee model, or second-RPC-provider verification.'}
    age = time.time()-q['received_epoch']
    result['age_at_check_start_seconds'] = age
    if age>SNAPSHOT_MAX_AGE:
        result['status'] = 'missed_snapshot_window_no_backfill'
        return result
    try:
        minimum = int(q['raw']['contextSlot'])
        options = {'encoding':'base64','commitment':'confirmed','minContextSlot':minimum}
        first = rpc('getAccountInfo',[op['pool'],options])
        layout = v.pool_layout((first or {}).get('value'))
        keys = [op['pool'],op['mint'],v.WSOL,layout['base_vault'],layout['quote_vault']]
        snapshot = rpc('getMultipleAccounts',[keys,options])
        if not snapshot or len(snapshot.get('value',[]))!=5:
            return result
        accounts = snapshot['value']
        checked = v.pool_layout(accounts[0])
        if checked['base_mint']!=op['mint'] or checked['quote_mint']!=v.WSOL or any(checked[k]!=layout[k] for k in ('base_vault','quote_vault')):
            raise ValueError('pool_identity_changed_or_mismatched')
        mint,quote_mint = v.mint_layout(accounts[1]),v.mint_layout(accounts[2])
        base,quote = v.vault_layout(accounts[3],op['mint'],op['pool']),v.vault_layout(accounts[4],v.WSOL,op['pool'])
        if base['token_program']!=mint['token_program'] or quote['token_program']!=quote_mint['token_program']:
            raise ValueError('vault_program_mismatch')
        flags = []
        age = time.time()-q['received_epoch']
        slot = snapshot['context']['slot']
        if not isinstance(slot,int) or slot<minimum:
            flags.append('context_not_verified')
        if age>SNAPSHOT_MAX_AGE:
            flags.append('snapshot_too_late')
        if not all(x['extensions_fully_validated'] for x in (mint,quote_mint,base,quote)):
            flags.append('token_extensions_not_fully_validated')
        if mint['freeze_authority_present']:
            flags.append('freeze_authority_present')
        legs = [p['swapInfo'] for p in q['raw'].get('routePlan',[]) if p.get('swapInfo',{}).get('ammKey')==op['pool']]
        if not legs:
            flags.append('quote_route_uses_other_pools')
        for leg in legs:
            output = leg.get('outputMint')
            if {leg.get('inputMint'),output}!={op['mint'],v.WSOL}:
                flags.append('pool_leg_mint_mismatch')
                continue
            reserve = int(base['amount_raw'] if output==op['mint'] else quote['amount_raw'])
            if int(leg['outAmount'])>reserve:
                flags.append('pool_leg_exceeds_later_observed_vault')
        result.update(status='pool_state_corroborated' if not flags else 'requires_review',flags=flags,
            checked_at=lab.utc(),snapshot_context_slot=slot,quote_context_slot=minimum,
            snapshot_age_from_quote_seconds=age,pool=checked,mint=mint,base_vault=base,quote_vault=quote,
            effective_quote_reserves_raw=str(int(quote['amount_raw'])+int(checked['virtual_quote_reserves_raw'])),
            rpc_account_evidence={'addresses':keys,'response':snapshot})
    except (ValueError,TypeError,KeyError,IndexError) as exc:
        result.update(status='unrecognized_or_inconsistent_pool_evidence',error=type(exc).__name__)
    return result


def pending_audit_tasks(pending):
    """Restore observation order; JSON key sorting is not deadline order."""
    def order(task):
        value = (task.get('quote') or {}).get('received_epoch')
        valid = type(value) in (int, float) and math.isfinite(value)
        return (value if valid else float('-inf'), str(task.get('id', '')))
    return [copy.deepcopy(task) for task in sorted(pending.values(), key=order)]


def discovery_snapshot(state):
    """Freeze worker inputs without copying the ever-growing quote history."""
    fields = ('id', 'signature', 'mint', 'pool', 'collector_version')
    return {'discovery_v4': copy.deepcopy(state.get('discovery_v4', {})),
            'migration_validation': dict.fromkeys(state.get('migration_validation', {})),
            'opportunities': {oid: {k: op[k] for k in fields if k in op}
                              for oid, op in state['opportunities'].items()}}


def audit_worker(events, tasks, rpc, end):
    # At most six live snapshot attempts, within the unchanged shared RPC budget.
    # Expiration is offline bookkeeping, capped separately at 100 total records.
    performed = processed = expired = 0
    while time.monotonic()<end and enabled():
        if performed>=6 or processed>=100:
            break  # Do not dequeue a seventh live task and strand it until restart.
        try:
            task = tasks.get(timeout=0.25)
        except queue.Empty:
            continue
        processed += 1
        try:
            result = pool_check(task, rpc)
        except Exception as exc:
            result = {'id':task['id'],'status':'audit_error','error':type(exc).__name__,'checked_at':lab.utc()}
        if result.get('status') == 'missed_snapshot_window_no_backfill':
            # pool_check returns this before making any RPC request.
            expired += 1
        else:
            performed += 1
        events.put(('quote_audit', result))
    print('QUOTE_AUDIT_WORKER ' + json.dumps({'maintenance':'audit-scheduler-1',
        'live_attempts':performed,'expired_records':expired,'processed_records':processed,
        'queued_remaining':tasks.qsize()},sort_keys=True), flush=True)


def accept_audit(state, audit):
    """No re-audit, unresolved match, or duplicate pool creates a new quote experiment."""
    state.setdefault('migration_validation',{})[audit['id']] = audit
    lab.append_jsonl(lab.DATA/'migration_audits.jsonl',audit)
    confirmed = state.setdefault('confirmed_pools',{})
    if audit.get('status')!='confirmed_new_migration':
        return 0
    key = audit['mint']+':'+audit['pool']
    if key in confirmed:
        return 0
    confirmed[key] = audit['id']
    if audit.get('historical_reaudit') or not audit.get('prospective_boundary_eligible'):
        return 0
    observed = time.time()
    op = {'id':audit['id'],'signature':audit['signature'],'mint':audit['mint'],'pool':audit['pool'],'quote_mint':v.WSOL,
        'decoder':'pump_migrate_event_and_pool_creation_v1','chain_block_time':audit.get('chain_block_time'),
        'chain_slot':audit.get('chain_slot'),'first_candidate_seen_epoch':audit.get('first_seen_epoch'),
        'first_observed_epoch':observed,'first_observed_at':lab.utc(observed),'actionable_epoch':observed,'actionable_at':lab.utc(observed),
        'observation_lag_seconds':observed-audit['chain_block_time'] if isinstance(audit.get('chain_block_time'),(int,float)) else None,
        'selection_reason':'corroborated_pump_migrate_event_and_pool_creation','future_information_used':False,
        'wallet_evidence_as_of_decision':'unknown_not_collected','collector_version':VERSION,
        'entry_quotes':{},'exit_quotes':{},'positions':{}}
    state['opportunities'][op['id']] = op
    lab.append_jsonl(lab.DATA/'opportunities.jsonl',op)
    return 1


def publish(state, new):
    latest = lab.publish_snapshot(state,new)
    d = state.get('discovery_v4',{})
    audits = state.get('migration_validation',{})
    statuses = dict(Counter(a['status'] for a in audits.values()))
    quality = state.get('quote_quality_counts',{})
    latest.update(version=VERSION,legacy_instruction_matches=sum(o.get('collector_version')!=VERSION for o in state['opportunities'].values()),
        validated_migrations=len(state.get('confirmed_pools',{})),migration_validation_statuses=statuses,
        migration_instruction_candidates=len(audits),discovery_source=d.get('active_source','unknown'),
        discovery_index_status=d.get('index_status','unknown'),pending_transaction_count=len(d.get('pending',{})),
        catchup_in_progress=any(c.get('before') for c in d.get('cursors',{}).values()),
        backpressure_cycles=d.get('backpressure_cycles',0),out_of_scope_or_unrecognized_v2_transactions=d.get('out_of_scope_or_unrecognized_v2_transactions',0),
        quote_quality_counts=quality,quote_audits_pending=len(state.get('quote_quality_pending',{})),
        rpc_calls_last_cycle=state.get('rpc_calls_last_cycle'),rpc_error_categories=state.get('rpc_error_categories',{}),
        coverage_note='Bounded migration-authority cursor and retry queue; SOL-paired migrate and migrate_v2 only; non-SOL pairs excluded. Independent total-market coverage is not established.',
        independent_coverage_fraction=None,fully_validated_quote_count=0)
    lab.save(lab.DATA/'latest.json',latest)
    report = lab.DATA/'REPORT.md'
    text = report.read_text()
    text = text.replace('Validated Pump migrations: '+str(len(state['opportunities'])),
                        'Evidence-confirmed unique migrations: '+str(latest['validated_migrations']))
    text = text.replace('Bounded latest-100 signature polling; complete migration coverage is NOT established.',latest['coverage_note'])
    text += ('\n## Evidence and coverage audit\n\n'
        'Historical instruction matches and their raw quotes are retained, not automatically validated.\n'
        'Completion events, pool-creation instructions, and zero-to-positive pool funding are required for new samples. Prefunded or missing-evidence cases remain unresolved.\n'
        'Re-audits and initial historical catch-up never create backfilled quote experiments.\n'
        f"Migration classifications: {json.dumps(statuses,sort_keys=True)}\n"
        f"Discovery source: {latest['discovery_source']}; pending transactions: {latest['pending_transaction_count']}; catch-up: {latest['catchup_in_progress']}\n"
        f"Out-of-scope or unrecognized migrate_v2 transactions: {latest['out_of_scope_or_unrecognized_v2_transactions']}\n"
        f"Pool snapshot checks: {json.dumps(quality,sort_keys=True)}\n"
        'Pool-state corroboration does not validate full route fees, execution, or hypothetical market impact.\n'
        'Old quotes without simultaneous pool snapshots cannot be retroactively given that evidence.\n')
    report.write_text(text)
    # Isolated, network-free virtual accounting; no research observations are changed.
    if enabled():
        try:
            from paper_account import safe_run
            control_path = Path(os.environ['PROSPECTIVE_CONTROL_PATH']) if os.environ.get('PROSPECTIVE_CONTROL_PATH') else None
            safe_run(state, lab.ROOT, control_path=control_path)
        except Exception as exc:
            print('PAPER_ACCOUNT_HOOK_ERROR: ' + type(exc).__name__)
    return latest


def cycle(run_seconds=20.0):
    cfg = lab.load(lab.ROOT/'config.json',{})
    if not enabled() or cfg.get('mode','WATCH_ONLY')!='WATCH_ONLY':
        return {'status':'STOPPED'}
    state = lab.load(lab.DATA/'state.json',{'schema':2,'started_at':lab.utc(),'cycles':0,'seen':[],'opportunities':{},'errors':[]})
    if state.get('schema')!=2:
        raise ValueError('unknown_state_schema_history_not_reset')
    state['cycles'] += 1
    state.setdefault('quality_version_started_at',lab.utc())
    events,tasks = queue.Queue(),queue.Queue()
    pending = state.setdefault('quote_quality_pending',{})
    for task in pending_audit_tasks(pending):
        tasks.put(task)
    end = time.monotonic()+run_seconds
    rpc = ReadBudget(end,state.get('rpc_cooldown_epoch',0))
    workers = [threading.Thread(target=discovery_worker,args=(events,discovery_snapshot(state),rpc,end),daemon=True),
               threading.Thread(target=audit_worker,args=(events,tasks,rpc,end),daemon=True)]
    for worker in workers:
        worker.start()
    new = 0
    while any(w.is_alive() for w in workers) or not events.empty() or time.monotonic()<end:
        while not events.empty():
            kind,value = events.get_nowait()
            if kind=='rpc':
                state['rpc_health'] = value
                state['rpc_consecutive_failures'] = 0 if value['connected'] else state.get('rpc_consecutive_failures',0)+1
            elif kind=='tx_failure':
                state['transaction_fetch_failures'] = state.get('transaction_fetch_failures',0)+1
            elif kind=='discovery_state':
                state['discovery_v4'] = value
            elif kind=='migration_audit':
                new += accept_audit(state,value)
            elif kind=='quote_audit':
                pending.pop(value['id'],None)
                counts = state.setdefault('quote_quality_counts',{})
                counts[value['status']] = counts.get(value['status'],0)+1
                lab.append_jsonl(lab.DATA/'quote_quality.jsonl',value)
            elif kind=='discovery_error':
                state['errors'] = (state.get('errors',[])+[value])[-100:]
                state['rpc_health'] = {'connected':False,'checked_at':lab.utc()}
                state['rpc_consecutive_failures'] = state.get('rpc_consecutive_failures',0)+1
        if enabled() and time.monotonic()<end:
            before = lab.pending_tasks(state,cfg)
            if lab.service_due(state,cfg,time.time()):
                _,kind,oid,delay,horizon = before[0]
                op = state['opportunities'][oid]
                q = op['entry_quotes'][delay] if kind=='entry' else op['exit_quotes'][delay][horizon]
                if q.get('status')=='quote_observed':
                    identity = ':'.join([oid,kind,delay,horizon or ''])
                    task = {'id':identity,'quote':copy.deepcopy(q),'opportunity':{'id':oid,'mint':op['mint'],'pool':op['pool']}}
                    if len(pending)<100:
                        pending[identity] = task
                        tasks.put(copy.deepcopy(task))
                    else:
                        row = {'id':identity,'status':'audit_queue_full','checked_at':lab.utc()}
                        counts = state.setdefault('quote_quality_counts',{})
                        counts['audit_queue_full'] = counts.get('audit_queue_full',0)+1
                        lab.append_jsonl(lab.DATA/'quote_quality.jsonl',row)
            else:
                lab.service_probe(state,cfg,time.time())
        if not enabled() and not any(w.is_alive() for w in workers):
            break
        time.sleep(0.1)
    for w in workers:
        w.join()
    state['rpc_cooldown_epoch'] = rpc.cooldown
    state['rpc_calls_last_cycle'] = rpc.count
    state['rpc_error_categories'] = dict(rpc.errors)
    return publish(state,new)


def activate():
    lab.VERSION = VERSION
    lab.READ_METHODS = READS


if __name__=='__main__':
    activate()
    print(json.dumps(cycle()))