#!/usr/bin/env python3
"""Network-free, provisional quote-accounting pilot. Never constructs transactions."""
from __future__ import annotations
import csv
import hashlib
import io
import json
import math
import os
import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

VERSION = 'quote-paper-account-1.0'
USDC = 'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v'
WSOL = 'So11111111111111111111111111111111111111112'
SPEC = {
    'version': VERSION, 'starting_cash_raw': 500_000_000, 'entry_input_raw': 50_000_000,
    'max_open_positions': 5, 'entry_delays_seconds': [30, 60, 120, 300],
    'exit_horizons_seconds': [300, 900, 3600], 'additional_cost_bps': [100, 300],
    'fixed_cost_per_side_raw': 50_000, 'max_request_lateness_seconds': 20,
    'max_receipt_lateness_seconds': 26, 'missing_observation_grace_seconds': 60,
    'primary_account': 'E60_H900_C100', 'mode': 'PAPER_ONLY',
    'selection': 'new_evidence_confirmed_SOL_paired_opportunities_after_pilot_start',
    'model': 'exact_quote_quantity_with_cash_cost_surcharge_and_exit_cash_haircut',
    'all_results_provisional': True, 'all_accounts_are_alternative_scenarios': True,
    'quotes_are_not_fills': True, 'extra_network_requests': 0,
}
NOTE = ('PROVISIONAL PAPER ACCOUNTING, not executable fills or realized profit. '
        'Exact quoted token quantities are retained. Entry cash adds 1% or 3% plus '
        '0.05 USDC; exit cash subtracts the same scenario percentage plus 0.05 USDC. '
        'These are extra cost stresses, not measured slippage or additional AMM fees. '
        'No transaction, latency-fill, market-impact, full-route or token-extension '
        'execution validation. Alternatives share observations; never sum their P&L. '
        'Open positions have unknown liquidation value; book equity holds them at cost. '
        'Failed exits retain locked capital and position slots. Quality checks never '
        'retroactively remove trades. Model times are quote receipt times; bookkeeping '
        'may occur later. No earlier quote records are backfilled into this pilot.')


def canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)


def digest(value: Any) -> str:
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def utc(epoch: float) -> str:
    return datetime.fromtimestamp(epoch, timezone.utc).isoformat(timespec='milliseconds')


def stamp(value: Any) -> float:
    if isinstance(value, str):
        value = datetime.fromisoformat(value.replace('Z', '+00:00')).timestamp()
    if isinstance(value, bool) or not isinstance(value, (float, int)) or not math.isfinite(value):
        raise ValueError('invalid_timestamp')
    return float(value)


def amount(value: Any, zero: bool = False) -> int:
    if isinstance(value, bool) or not (isinstance(value, int) or
            isinstance(value, str) and value.isascii() and value.isdecimal() and len(value) <= 20):
        raise ValueError('invalid_integer_amount')
    result = int(value)
    if result < (0 if zero else 1) or result > 2**64 - 1:
        raise ValueError('amount_out_of_range')
    return result


def write_text(path: Path, text: str) -> None:
    temp = path.with_suffix(path.suffix + '.tmp')
    with temp.open('w', encoding='utf-8') as handle:
        handle.write(text)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temp, path)


def active(root: Path, control_path: Path | None = None) -> bool:
    try:
        control = json.loads((control_path or root / 'control.json').read_text())
        config = json.loads((root / 'config.json').read_text())
        return (control.get('enabled') is True and control.get('mode') == 'WATCH_ONLY'
                and config.get('mode') == 'WATCH_ONLY')
    except (OSError, ValueError, TypeError, AttributeError):
        return False


def bootstrap(db: sqlite3.Connection, now: float) -> float:
    db.executescript('''
    CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS accounts (
      id TEXT PRIMARY KEY, delay INTEGER NOT NULL, horizon INTEGER NOT NULL,
      cost_bps INTEGER NOT NULL, cash INTEGER NOT NULL CHECK(cash>=0));
    CREATE TABLE IF NOT EXISTS observations (
      id TEXT PRIMARY KEY, hash TEXT NOT NULL, observed REAL NOT NULL);
    CREATE TABLE IF NOT EXISTS positions (
      account TEXT NOT NULL, opportunity TEXT NOT NULL, mint TEXT NOT NULL,
      quantity TEXT NOT NULL, entry_cost INTEGER NOT NULL, entry_time REAL NOT NULL,
      due REAL NOT NULL, status TEXT NOT NULL, exit_net INTEGER, net_pnl INTEGER,
      PRIMARY KEY(account, opportunity));
    CREATE TABLE IF NOT EXISTS events (
      sequence INTEGER PRIMARY KEY AUTOINCREMENT, account TEXT NOT NULL,
      opportunity TEXT NOT NULL, action TEXT NOT NULL, observed REAL NOT NULL,
      booked REAL NOT NULL, reason TEXT NOT NULL, delta INTEGER NOT NULL,
      cash_after INTEGER NOT NULL, detail TEXT NOT NULL);
    ''')
    db.execute('BEGIN IMMEDIATE')
    saved = db.execute("SELECT value FROM meta WHERE key='spec'").fetchone()
    if saved:
        if saved[0] != canonical(SPEC):
            raise ValueError('paper_spec_changed_no_silent_reset')
        return stamp(float(db.execute("SELECT value FROM meta WHERE key='started'").fetchone()[0]))
    if db.execute('SELECT COUNT(*) FROM accounts').fetchone()[0] or db.execute('SELECT COUNT(*) FROM events').fetchone()[0]:
        raise ValueError('paper_metadata_missing_no_reset')
    db.executemany('INSERT INTO meta VALUES (?,?)', [('spec', canonical(SPEC)),
        ('started', str(now)), ('watermark', str(now)), ('last_run', str(now))])
    for delay in SPEC['entry_delays_seconds']:
        for horizon in SPEC['exit_horizons_seconds']:
            for cost in SPEC['additional_cost_bps']:
                db.execute('INSERT INTO accounts VALUES (?,?,?,?,?)',
                    (f'E{delay}_H{horizon}_C{cost}', delay, horizon, cost, SPEC['starting_cash_raw']))
    return now


def source_events(source: dict, start: float, now: float) -> list[tuple]:
    events = []
    for oid, op in source.get('opportunities', {}).items():
        if stamp(op.get('first_observed_epoch', 0)) < start:
            continue
        for delay in SPEC['entry_delays_seconds']:
            q = op.get('entry_quotes', {}).get(str(delay))
            scheduled = stamp(op['actionable_epoch']) + delay
            if q is None and now > scheduled + SPEC['missing_observation_grace_seconds']:
                q = {'status': 'absent_observation', 'observed_at': utc(scheduled + 60)}
            if q is not None:
                when = stamp(q.get('received_epoch') if q.get('received_epoch') is not None else q.get('observed_at'))
                if when <= now:
                    events.append((when, 1, oid, delay, 0, q, op, scheduled))
            # Only recorded successful entries define the exact later quantity/clock.
            entry = op.get('entry_quotes', {}).get(str(delay), {})
            if entry.get('status') != 'quote_observed' or entry.get('received_epoch') is None:
                continue
            for horizon in SPEC['exit_horizons_seconds']:
                scheduled = stamp(entry['received_epoch']) + horizon
                q = op.get('exit_quotes', {}).get(str(delay), {}).get(str(horizon))
                if q is None and now > scheduled + SPEC['missing_observation_grace_seconds']:
                    q = {'status': 'absent_observation', 'observed_at': utc(scheduled + 60)}
                if q is not None:
                    when = stamp(q.get('received_epoch') if q.get('received_epoch') is not None else q.get('observed_at'))
                    if when <= now:
                        events.append((when, 0, oid, delay, horizon, q, op, scheduled))
    return sorted(events, key=lambda e: e[:5])


def quote_reason(q: dict, op: dict, scheduled: float, kind: str, quantity: int) -> str | None:
    if q.get('status') != 'quote_observed':
        return 'quote_unavailable_' + str(q.get('status', 'unknown'))[:60]
    try:
        raw = q['raw']
        expected = (USDC, op['mint']) if kind == 'entry' else (op['mint'], USDC)
        if (raw['inputMint'], raw['outputMint']) != expected or raw.get('swapMode') != 'ExactIn':
            return 'quote_pair_or_mode_mismatch'
        if amount(raw['inAmount']) != quantity:
            return 'quote_quantity_mismatch'
        out = amount(raw['outAmount'])
        amount(raw['contextSlot'])
        if amount(raw['otherAmountThreshold'], True) > out:
            return 'invalid_minimum_output'
        if not isinstance(raw.get('routePlan'), list) or not raw['routePlan'] or not all(
                isinstance(p, dict) and isinstance(p.get('swapInfo'), dict) and
                isinstance(p['swapInfo'].get('ammKey'), str) and p['swapInfo']['ammKey'] for p in raw['routePlan']):
            return 'invalid_route_shape'
        req, received = stamp(q['requested_epoch']), stamp(q['received_epoch'])
        if abs(stamp(q['scheduled_epoch']) - scheduled) > .01:
            return 'scheduled_clock_mismatch'
        if (req < scheduled - .001 or received < req or
                req - scheduled > SPEC['max_request_lateness_seconds'] or
                received - scheduled > SPEC['max_receipt_lateness_seconds'] or
                q.get('timing_eligible') is not True):
            return 'quote_timing_ineligible'
        if q.get('fills_assumed') is not False:
            return 'source_not_quote_only'
    except (ValueError, TypeError, KeyError, OverflowError):
        return 'malformed_quote'
    return None


def admission(source: dict, op: dict, receipt: float) -> str | None:
    audit = source.get('migration_validation', {}).get(op['id'], {})
    try:
        if (audit.get('status') != 'confirmed_new_migration' or
                audit.get('historical_reaudit') is not False or
                audit.get('prospective_boundary_eligible') is not True or
                audit.get('mint') != op['mint'] or audit.get('pool') != op['pool'] or
                op.get('quote_mint') != WSOL or op.get('future_information_used') is not False or
                stamp(audit['checked_at']) > receipt or
                stamp(op['first_observed_epoch']) > receipt):
            return 'migration_not_confirmed_as_of_entry'
    except (ValueError, TypeError, KeyError):
        return 'migration_evidence_missing'
    return None


def record(db, account, oid, action, when, now, reason, delta, detail):
    cash = db.execute('SELECT cash FROM accounts WHERE id=?', (account,)).fetchone()[0]
    if cash + delta < 0:
        raise ValueError('negative_cash_prevented')
    cash += delta
    db.execute('UPDATE accounts SET cash=? WHERE id=?', (cash, account))
    db.execute('INSERT INTO events(account,opportunity,action,observed,booked,reason,delta,cash_after,detail) '
               'VALUES (?,?,?,?,?,?,?,?,?)', (account, oid, action, when, now, reason, delta, cash, canonical(detail)))


def reduce_event(db, source, e, now, watermark):
    when, priority, oid, delay, horizon, quote, op, scheduled = e
    kind = 'entry' if priority else 'exit'
    identity = canonical([oid, kind, delay, horizon])
    fingerprint = digest({'quote': quote, 'mint': op['mint'], 'pool': op['pool'], 'scheduled': scheduled})
    old = db.execute('SELECT hash FROM observations WHERE id=?', (identity,)).fetchone()
    if old:
        if old[0] != fingerprint:
            raise ValueError('source_observation_changed_no_rewrite')
        return watermark
    db.execute('INSERT INTO observations VALUES (?,?,?)', (identity, fingerprint, when))
    parameters = (delay,) if kind == 'entry' else (delay, horizon)
    rows = db.execute('SELECT * FROM accounts WHERE delay=?' + ('' if kind == 'entry' else ' AND horizon=?'), parameters).fetchall()
    for a in rows:
        aid = a['id']
        detail = {'quote_id': identity, 'quote_sha256': fingerprint, 'mint': op['mint'],
                  'pool': op['pool'], 'source_status': quote.get('status'), 'provisional': True,
                  'model_version': VERSION, 'cost_bps': a['cost_bps'], 'actual_fills_verified': False}
        if kind == 'entry':
            reason = 'out_of_order_no_retroactive_entry' if when < watermark else admission(source, op, when)
            reason = reason or quote_reason(quote, op, scheduled, 'entry', SPEC['entry_input_raw'])
            existing = db.execute("SELECT * FROM positions WHERE account=? AND status!='CLOSED'", (aid,)).fetchall()
            extra = (SPEC['entry_input_raw'] * a['cost_bps'] + 9999) // 10000 + SPEC['fixed_cost_per_side_raw']
            debit = SPEC['entry_input_raw'] + extra
            reason = reason or ('position_limit' if len(existing) >= SPEC['max_open_positions'] else None)
            reason = reason or ('duplicate_open_mint' if any(p['mint'] == op['mint'] for p in existing) else None)
            reason = reason or ('insufficient_virtual_cash' if a['cash'] < debit else None)
            if reason:
                record(db, aid, oid, 'SKIP_ENTRY', when, now, reason, 0, detail)
                continue
            quantity = str(amount(quote['raw']['outAmount']))
            db.execute('INSERT INTO positions VALUES (?,?,?,?,?,?,?,?,?,?)',
                (aid, oid, op['mint'], quantity, debit, when, when + a['horizon'], 'OPEN', None, None))
            detail.update(quantity_raw=quantity, quoted_input_raw=SPEC['entry_input_raw'], additional_cost_raw=extra)
            record(db, aid, oid, 'MODEL_BUY', when, now, 'predeclared_quote_quantity_model', -debit, detail)
        else:
            pos = db.execute('SELECT * FROM positions WHERE account=? AND opportunity=?', (aid, oid)).fetchone()
            if not pos or pos['status'] != 'OPEN':
                continue
            reason = 'out_of_order_exit_unresolved' if when < watermark else quote_reason(
                quote, op, scheduled, 'exit', amount(pos['quantity']))
            if not reason and abs(pos['due'] - scheduled) > .01:
                reason = 'position_exit_clock_mismatch'
            if not reason:
                gross = amount(quote['raw']['outAmount'])
                extra = (gross * a['cost_bps'] + 9999) // 10000 + SPEC['fixed_cost_per_side_raw']
                net = gross - extra
                if a['cash'] + net < 0:
                    reason = 'insufficient_cash_for_modeled_exit_cost'
            if reason:
                db.execute("UPDATE positions SET status='UNRESOLVED' WHERE account=? AND opportunity=?", (aid, oid))
                record(db, aid, oid, 'UNRESOLVED_EXIT', when, now, reason, 0, detail)
                continue
            pnl = net - pos['entry_cost']
            db.execute("UPDATE positions SET status='CLOSED',exit_net=?,net_pnl=? WHERE account=? AND opportunity=?", (net, pnl, aid, oid))
            detail.update(quantity_raw=pos['quantity'], quoted_output_raw=gross, additional_cost_raw=extra, modeled_net_pnl_raw=pnl)
            record(db, aid, oid, 'MODEL_SELL', when, now, 'matching_quantity_fixed_horizon_model', net, detail)
    return max(watermark, when)


def reconcile(db):
    expected = len(SPEC['entry_delays_seconds']) * len(SPEC['exit_horizons_seconds']) * len(SPEC['additional_cost_bps'])
    if db.execute('SELECT COUNT(*) FROM accounts').fetchone()[0] != expected:
        raise ValueError('account_count_integrity')
    for a in db.execute('SELECT * FROM accounts').fetchall():
        delta = db.execute('SELECT COALESCE(SUM(delta),0) FROM events WHERE account=?', (a['id'],)).fetchone()[0]
        positions = db.execute('SELECT * FROM positions WHERE account=?', (a['id'],)).fetchall()
        opened = [p for p in positions if p['status'] != 'CLOSED']
        pnl = sum(p['net_pnl'] for p in positions if p['status'] == 'CLOSED')
        if (a['cash'] < 0 or a['cash'] != SPEC['starting_cash_raw'] + delta or
                len(opened) > SPEC['max_open_positions'] or
                a['cash'] + sum(p['entry_cost'] for p in opened) != SPEC['starting_cash_raw'] + pnl):
            raise ValueError('ledger_reconciliation_failed')


def export(db, directory, start, now, source):
    accounts = []
    for a in db.execute('SELECT * FROM accounts ORDER BY delay,horizon,cost_bps').fetchall():
        positions = db.execute('SELECT * FROM positions WHERE account=? ORDER BY entry_time', (a['id'],)).fetchall()
        opened = [p for p in positions if p['status'] != 'CLOSED']
        closed = [p for p in positions if p['status'] == 'CLOSED']
        wins = sum(p['net_pnl'] > 0 for p in closed)
        losses = sum(p['net_pnl'] < 0 for p in closed)
        gross_win = sum(max(0, p['net_pnl']) for p in closed)
        gross_loss = sum(max(0, -p['net_pnl']) for p in closed)
        skipped = dict(db.execute("SELECT reason,COUNT(*) FROM events WHERE account=? AND action='SKIP_ENTRY' GROUP BY reason", (a['id'],)).fetchall())
        accounts.append({'account_id': a['id'], 'entry_delay_seconds': a['delay'],
            'exit_horizon_seconds': a['horizon'], 'additional_cost_bps': a['cost_bps'],
            'starting_cash_usdc': 500, 'cash_usdc': a['cash'] / 1_000_000,
            'modeled_buys': len(positions), 'open_positions': len(opened),
            'unresolved_positions': sum(p['status'] == 'UNRESOLVED' for p in opened),
            'closed_positions': len(closed), 'wins': wins, 'losses': losses,
            'win_rate_pct': 100 * wins / len(closed) if closed else None,
            'closed_modeled_net_pnl_usdc': sum(p['net_pnl'] for p in closed) / 1_000_000,
            'profit_factor': gross_win / gross_loss if gross_loss else None,
            'open_cost_basis_usdc': sum(p['entry_cost'] for p in opened) / 1_000_000,
            'book_equity_at_cost_usdc': (a['cash'] + sum(p['entry_cost'] for p in opened)) / 1_000_000,
            'liquidation_equity_usdc': None if opened else a['cash'] / 1_000_000,
            'market_max_drawdown_pct': None, 'skip_reasons': skipped,
            'all_results_provisional': True})
    latest = {'version': VERSION, 'mode': 'PAPER_ONLY', 'updated_at': utc(now), 'started_at': utc(start),
        'status': 'RUNNING', 'spec': SPEC, 'spec_sha256': digest(SPEC), 'notes': NOTE,
        'accounts': accounts, 'primary_account': SPEC['primary_account'],
        'real_trades_placed': 0, 'realized_profit': None, 'network_requests_by_paper_layer': 0,
        'independent_market_coverage': None, 'all_results_provisional': True,
        'ledger_reconciled': True, 'research_quote_quality_counts': source.get('quote_quality_counts', {}),
        'ledger_events': db.execute('SELECT COUNT(*) FROM events').fetchone()[0],
        'unique_post_start_opportunities_with_model_buys': db.execute('SELECT COUNT(DISTINCT opportunity) FROM positions').fetchone()[0]}
    latest['primary'] = next(a for a in accounts if a['account_id'] == SPEC['primary_account'])
    write_text(directory / 'latest.json', json.dumps(latest, indent=2, sort_keys=True, allow_nan=False) + '\n')
    text = ['# Provisional Paper Accounts', '', '**PAPER ONLY — no real transactions.**', '',
        f"Started: {latest['started_at']}", f"Updated: {latest['updated_at']}", '', NOTE, '',
        'Primary predeclared account: **E60_H900_C100** (60-second entry, 15-minute horizon, 1% extra cost per side).',
        'Each row is a separate $500 account, not a slice of one portfolio. No profit-based model selection.', '',
        '| Account | Cash USDC | Open | Unresolved | Closed | Closed modeled net P&L USDC |',
        '|---|---:|---:|---:|---:|---:|']
    for a in accounts:
        text.append(f"| {a['account_id']} | {a['cash_usdc']:.2f} | {a['open_positions']} | {a['unresolved_positions']} | {a['closed_positions']} | {a['closed_modeled_net_pnl_usdc']:+.2f} |")
    text += ['', 'Open holdings are not marked as profits. Liquidation equity and market drawdown remain unknown while unmeasured.',
             'Missing exits are not deleted from the denominator: see open and unresolved counts alongside closed-only statistics.',
             'The authoritative ledger is accounts.sqlite3. ledger.csv is a rebuildable export with source quote hashes.',
             'Collector research observations are never rewritten by this paper layer.']
    write_text(directory / 'REPORT.md', '\n'.join(text) + '\n')
    out = io.StringIO(newline='')
    writer = csv.writer(out)
    writer.writerow(['sequence', 'account', 'opportunity', 'action', 'modeled_observed_utc',
                     'booked_utc', 'reason', 'cash_delta_raw', 'cash_after_raw', 'detail_json'])
    for row in db.execute('SELECT * FROM events ORDER BY sequence'):
        writer.writerow([row['sequence'], row['account'], row['opportunity'], row['action'], utc(row['observed']),
                         utc(row['booked']), row['reason'], row['delta'], row['cash_after'], row['detail']])
    write_text(directory / 'ledger.csv', out.getvalue())
    write_text(directory / 'health.json', canonical({'status': 'healthy', 'updated_at': utc(now), 'version': VERSION}) + '\n')
    return latest


def run(source: dict, root: Path, now: float | None = None, control_path: Path | None = None) -> dict:
    """Consume already observed records only; writes solely to data/paper_accounts."""
    now = stamp(time.time() if now is None else now)
    root = Path(root)
    if not active(root, control_path):
        return {'status': 'STOPPED'}
    config = json.loads((root / 'config.json').read_text())
    if (source.get('schema') != 2 or
            config.get('additional_delay_seconds') != SPEC['entry_delays_seconds'] or
            config.get('exit_horizons_seconds') != SPEC['exit_horizons_seconds'] or
            config.get('hypothetical_quote_sizes_usd') != [50]):
        raise ValueError('research_contract_changed_no_silent_paper_reconfiguration')
    directory = root / 'data' / 'paper_accounts'
    directory.mkdir(parents=True, exist_ok=True)
    database = directory / 'accounts.sqlite3'
    if not database.exists() and (directory / 'latest.json').exists():
        raise ValueError('paper_database_missing_no_account_reset')
    db = sqlite3.connect(database, timeout=2, isolation_level=None)
    db.row_factory = sqlite3.Row
    try:
        db.execute('PRAGMA journal_mode=DELETE')
        db.execute('PRAGMA synchronous=FULL')
        start = bootstrap(db, now)
        if now < float(db.execute("SELECT value FROM meta WHERE key='last_run'").fetchone()[0]):
            raise ValueError('clock_reversal')
        reconcile(db)
        watermark = float(db.execute("SELECT value FROM meta WHERE key='watermark'").fetchone()[0])
        for event in source_events(source, start, now):
            watermark = reduce_event(db, source, event, now, watermark)
        reconcile(db)
        if not active(root, control_path):
            db.rollback()
            return {'status': 'STOPPED'}
        db.executemany('UPDATE meta SET value=? WHERE key=?', [(str(watermark), 'watermark'), (str(now), 'last_run')])
        db.commit()
        return export(db, directory, start, now, source)
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def safe_run(source: dict, root: Path, control_path: Path | None = None) -> dict:
    """Paper failure cannot silently stop or alter the underlying quote collection."""
    try:
        return run(source, root, control_path=control_path)
    except Exception as exc:
        health = {'status': 'error', 'updated_at': utc(time.time()), 'version': VERSION,
                  'error_type': type(exc).__name__, 'paper_accounting_paused_this_cycle': True}
        # No exception messages/URLs/credentials are emitted. Preserve the database.
        try:
            directory = Path(root) / 'data' / 'paper_accounts'
            directory.mkdir(parents=True, exist_ok=True)
            write_text(directory / 'health.json', canonical(health) + '\n')
        except OSError:
            pass
        print('PAPER_ACCOUNT_ERROR: ' + type(exc).__name__)
        return health
