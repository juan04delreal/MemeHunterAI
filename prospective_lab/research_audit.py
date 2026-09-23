"""Offline loss attribution and integrity audit. Read-only inputs; no network or trades."""
from __future__ import annotations
import hashlib
import json
import math
import os
import sqlite3
import statistics
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

VERSION = 'loss-audit-1.0'
PRIMARY = 'E60_H900_C100'
USDC = 'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v'
MAX_BYTES = 512 * 1024 * 1024


def canonical(x):
    return json.dumps(x, sort_keys=True, separators=(',', ':'), allow_nan=False)


def fingerprint(x):
    return hashlib.sha256(canonical(x).encode()).hexdigest()


def units(x):
    if isinstance(x, bool) or not (isinstance(x, int) or isinstance(x, str) and x.isascii() and x.isdecimal() and len(x) <= 20):
        raise ValueError('invalid_raw_amount')
    x = int(x)
    if x < 0 or x > 2**64-1:
        raise ValueError('raw_amount_range')
    return x


def read_json(path):
    if path.stat().st_size > MAX_BYTES:
        raise ValueError('input_size_limit')
    return json.loads(path.read_text())


def routes(raw):
    """Validate only a single serial route. Split routes are unresolved, not invalid."""
    plan = raw.get('routePlan')
    if not isinstance(plan, list) or not plan:
        return 'missing_route'
    legs = []
    try:
        for item in plan:
            if not isinstance(item, dict) or not isinstance(item.get('swapInfo'), dict):
                return 'malformed_route'
            if item.get('percent') != 100 and item.get('bps') != 10000:
                return 'split_or_unspecified_route_unverified'
            leg = item['swapInfo']
            if not all(isinstance(leg.get(k), str) and leg[k] for k in ('ammKey', 'inputMint', 'outputMint')):
                return 'malformed_route'
            if units(leg['inAmount']) == 0 or units(leg['outAmount']) == 0:
                return 'malformed_route'
            legs.append(leg)
        if legs[0]['inputMint'] != raw['inputMint'] or legs[-1]['outputMint'] != raw['outputMint']:
            return 'serial_route_endpoint_mismatch'
        if units(legs[0]['inAmount']) != units(raw['inAmount']):
            return 'serial_route_input_mismatch'
        for a, b in zip(legs, legs[1:]):
            if a['outputMint'] != b['inputMint']:
                return 'serial_route_mint_discontinuity'
            if units(a['outAmount']) != units(b['inAmount']):
                return 'serial_route_amount_discontinuity_review'
        if units(legs[-1]['outAmount']) != units(raw['outAmount']):
            return 'serial_route_output_or_fee_difference_review'
    except (KeyError, ValueError, TypeError, OverflowError):
        return 'malformed_route'
    return 'serial_route_arithmetic_consistent_not_execution'


def summarize_returns(values):
    if not values:
        return {'count': 0}
    total = sum(values)
    winners = sum(x for x in values if x > 0)
    losses = -sum(x for x in values if x < 0)
    return {'count': len(values), 'sum_usdc': total / 1e6,
            'median_usdc': statistics.median(values) / 1e6,
            'mean_usdc': total / len(values) / 1e6,
            'wins': sum(x > 0 for x in values), 'losses': sum(x < 0 for x in values),
            'profit_factor': winners / losses if losses else None,
            'best_usdc': max(values) / 1e6, 'worst_usdc': min(values) / 1e6,
            'without_best_one_usdc': (total - max(values)) / 1e6,
            'without_best_three_usdc': (total - sum(sorted(values, reverse=True)[:3])) / 1e6,
            'sensitivity_only_no_records_removed': True}


def source_check(event, source, observation_hashes):
    detail = json.loads(event['detail'])
    try:
        oid, kind, delay, horizon = json.loads(detail['quote_id'])
        if oid != event['opportunity']:
            return 'quote_identity_mismatch', None
        op = source['opportunities'][oid]
        q = (op['entry_quotes'][str(delay)] if kind == 'entry'
             else op['exit_quotes'][str(delay)][str(horizon)])
        scheduled = (float(op['actionable_epoch']) + delay if kind == 'entry'
                     else float(op['entry_quotes'][str(delay)]['received_epoch']) + horizon)
        digest = fingerprint({'quote': q, 'mint': op['mint'], 'pool': op['pool'], 'scheduled': scheduled})
        if digest != detail.get('quote_sha256') or digest != observation_hashes.get(detail['quote_id']):
            return 'source_hash_mismatch', q
        raw = q['raw']
        pair = (USDC, op['mint']) if kind == 'entry' else (op['mint'], USDC)
        if q.get('status') != 'quote_observed' or (raw['inputMint'], raw['outputMint']) != pair:
            return 'source_pair_or_status_mismatch', q
        expected = detail.get('quoted_input_raw') if kind == 'entry' else detail.get('quantity_raw')
        output = detail.get('quantity_raw') if kind == 'entry' else detail.get('quoted_output_raw')
        if units(raw['inAmount']) != units(expected) or units(raw['outAmount']) != units(output):
            return 'source_quantity_mismatch', q
        receipt = q['received_epoch']
        if isinstance(receipt, bool) or not isinstance(receipt, (int, float)) or not math.isfinite(receipt) or abs(receipt - event['observed']) > .001:
            return 'source_receipt_mismatch', q
        return 'matched_saved_source_not_independent_price_verification', q
    except (KeyError, ValueError, TypeError, OverflowError):
        return 'source_missing_or_malformed', None


def inspect_database(db, source):
    db.row_factory = sqlite3.Row
    integrity = db.execute('PRAGMA integrity_check').fetchone()[0]
    meta = dict(db.execute('SELECT key,value FROM meta'))
    spec = json.loads(meta['spec'])
    hashes = dict(db.execute('SELECT id,hash FROM observations'))
    starting = spec['starting_cash_raw']
    all_summaries, primary_cases = [], []
    for a in db.execute('SELECT * FROM accounts ORDER BY id').fetchall():
        rows = db.execute('SELECT * FROM events WHERE account=? ORDER BY sequence', (a['id'],)).fetchall()
        positions = db.execute('SELECT * FROM positions WHERE account=?', (a['id'],)).fetchall()
        cash, opened, closed, problems = starting, {}, [], []
        source_counts, route_counts = Counter(), Counter()
        last_time = float(meta['started'])
        for r in rows:
            cash += r['delta']
            if cash < 0 or cash != r['cash_after']:
                problems.append('cash_sequence_mismatch')
            if r['action'] not in ('MODEL_BUY', 'MODEL_SELL'):
                continue
            if r['observed'] < last_time:
                problems.append('event_time_reversal')
            last_time = max(last_time, r['observed'])
            d = json.loads(r['detail'])
            check, q = source_check(r, source, hashes)
            source_counts[check] += 1
            route = routes(q.get('raw', {})) if q else 'missing_source'
            route_counts[route] += 1
            if r['action'] == 'MODEL_BUY':
                if r['opportunity'] in opened:
                    problems.append('duplicate_open_opportunity')
                if any(x['detail']['mint'] == d['mint'] for x in opened.values()):
                    problems.append('duplicate_open_mint')
                expected_extra = (units(d['quoted_input_raw']) * a['cost_bps'] + 9999)//10000 + spec['fixed_cost_per_side_raw']
                if d['additional_cost_raw'] != expected_extra or r['delta'] != -(units(d['quoted_input_raw']) + expected_extra):
                    problems.append('entry_cost_mismatch')
                opened[r['opportunity']] = {'event': dict(r), 'detail': d, 'check': check, 'route': route}
                if len(opened) > spec['max_open_positions']:
                    problems.append('open_position_limit')
            else:
                b = opened.pop(r['opportunity'], None)
                if b is None:
                    problems.append('sell_without_open_buy')
                    continue
                gross = units(d['quoted_output_raw'])
                extra = (gross * a['cost_bps'] + 9999)//10000 + spec['fixed_cost_per_side_raw']
                pnl = r['delta'] + b['event']['delta']
                if (d['additional_cost_raw'] != extra or r['delta'] != gross-extra or
                        d['modeled_net_pnl_raw'] != pnl or
                        units(d['quantity_raw']) != units(b['detail']['quantity_raw'])):
                    problems.append('exit_quantity_cost_or_pnl_mismatch')
                closed.append({'opportunity': r['opportunity'], 'mint': d['mint'], 'pool': d['pool'],
                    'entry_epoch': b['event']['observed'], 'exit_epoch': r['observed'],
                    'entry_cost_raw': -b['event']['delta'], 'quantity_raw': d['quantity_raw'],
                    'quoted_exit_raw': gross, 'before_extra_cost_pnl_raw': gross-units(b['detail']['quoted_input_raw']),
                    'extra_cost_raw': b['detail']['additional_cost_raw'] + extra, 'net_pnl_raw': pnl,
                    'entry_source_check': b['check'], 'exit_source_check': check,
                    'entry_route_check': b['route'], 'exit_route_check': route,
                    'entry_source_hash': b['detail']['quote_sha256'], 'exit_source_hash': d['quote_sha256']})
        db_closed = [p for p in positions if p['status'] == 'CLOSED']
        db_open = [p for p in positions if p['status'] != 'CLOSED']
        if cash != a['cash'] or len(closed) != len(db_closed) or set(opened) != {p['opportunity'] for p in db_open}:
            problems.append('database_state_mismatch')
        if sum(p['net_pnl'] for p in db_closed) != sum(c['net_pnl_raw'] for c in closed):
            problems.append('closed_summary_mismatch')
        if cash + sum(p['entry_cost'] for p in db_open) != starting + sum(p['net_pnl'] for p in db_closed):
            problems.append('balance_sheet_mismatch')
        s = {'account': a['id'], 'cash_usdc': cash/1e6, 'open_positions': len(db_open),
             'unresolved_positions': sum(p['status']=='UNRESOLVED' for p in db_open),
             'integrity_problems': dict(Counter(problems)), 'source_checks': dict(source_counts),
             'route_checks': dict(route_counts), 'net_modeled': summarize_returns([c['net_pnl_raw'] for c in closed]),
             'same_positions_before_extra_costs': summarize_returns([c['before_extra_cost_pnl_raw'] for c in closed]),
             'extra_costs_on_closed_positions_usdc': sum(c['extra_cost_raw'] for c in closed)/1e6,
             'closed_losing_over_80pct': sum(c['net_pnl_raw'] <= -.8*c['entry_cost_raw'] for c in closed),
             'skip_reasons': dict(Counter(r['reason'] for r in rows if r['action']=='SKIP_ENTRY'))}
        all_summaries.append(s)
        if a['id'] == PRIMARY:
            primary_cases = sorted(closed, key=lambda c:c['net_pnl_raw'], reverse=True)
    return {'version': VERSION, 'sqlite_integrity': integrity, 'spec_sha256': fingerprint(spec),
            'paper_started_epoch': float(meta['started']), 'paper_last_run_epoch': float(meta['last_run']),
            'accounts': all_summaries, 'primary': next((x for x in all_summaries if x['account']==PRIMARY), None),
            'primary_closed_cases': primary_cases,
            'interpretation': 'Same-position cost attribution, not a counterfactual zero-cost strategy. Source matches verify saved data/arithmetic, not independent prices or fills. No original records changed.'}


def audit(root):
    root = Path(root)
    ctl = read_json(Path(os.environ.get('PROSPECTIVE_CONTROL_PATH', str(root/'control.json'))))
    if ctl.get('enabled') is not True or ctl.get('mode') != 'WATCH_ONLY':
        return {'status': 'STOPPED'}
    if read_json(root/'config.json').get('mode') != 'WATCH_ONLY':
        return {'status': 'STOPPED'}
    source_path = root/'data'/'state.json'
    db_path = root/'data'/'paper_accounts'/'accounts.sqlite3'
    source = read_json(source_path)
    if source.get('schema') != 2 or db_path.stat().st_size > MAX_BYTES:
        raise ValueError('unsupported_input')
    before = hashlib.sha256(db_path.read_bytes()).hexdigest()
    db = sqlite3.connect(db_path.resolve().as_uri()+'?mode=ro&immutable=1', uri=True)
    try:
        db.execute('PRAGMA query_only=ON')
        result = inspect_database(db, source)
    finally:
        db.close()
    after = hashlib.sha256(db_path.read_bytes()).hexdigest()
    if before != after:
        raise ValueError('input_database_changed_during_audit')
    result.update(status='AUDITED', generated_at=datetime.now(timezone.utc).isoformat(),
                  input_database_sha256=before, input_database_unchanged=True,
                  input_state_sha256=hashlib.sha256(source_path.read_bytes()).hexdigest(),
                  network_requests=0, real_trades=0, guaranteed_profit=False)
    return result


if __name__ == '__main__':
    print('LOSS_AUDIT_JSON_BEGIN')
    print(json.dumps(audit(Path(__file__).resolve().parent), sort_keys=True, allow_nan=False))
    print('LOSS_AUDIT_JSON_END')
