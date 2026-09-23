#!/usr/bin/env python3
"""Prospective, read-only quotes. No transaction construction or submission."""
from __future__ import annotations

import json
import os
import queue
import threading
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode, urlsplit

ROOT = Path(__file__).resolve().parent
DATA = ROOT / 'data'
PUMPSWAP = 'pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA'
PUMP = '6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P'
MIGRATE_DISC = [155, 234, 231, 146, 236, 158, 162, 30]
MAX_TX_VERSION = 1
ALPHABET = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'
WSOL = 'So11111111111111111111111111111111111111112'
USDC = 'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v'
VERSION = 'prospective-quote-lab-0.3'
QUOTE_URL = 'https://api.jup.ag/swap/v1/quote'
READ_METHODS = frozenset({'getSlot', 'getSignaturesForAddress', 'getTransaction'})
MIN_QUOTE_INTERVAL = 2.5  # Conservative: documented keyless limit is 0.5 RPS.
MAX_LATENESS = 20.0


def utc(epoch=None):
    return datetime.fromtimestamp(time.time() if epoch is None else epoch, timezone.utc).isoformat(timespec='milliseconds')


def b58decode(s):
    n = 0
    for c in s:
        n = n * 58 + ALPHABET.index(c)
    raw = n.to_bytes((n.bit_length() + 7) // 8, 'big') if n else b''
    return b'\0' * (len(s) - len(s.lstrip('1'))) + raw


def keystr(x):
    return x.get('pubkey', '') if isinstance(x, dict) else str(x)


def decode_migration(tx):
    if not tx or (tx.get('meta') or {}).get('err') is not None:
        return None
    msg = (tx.get('transaction') or {}).get('message') or {}
    instructions = list(msg.get('instructions') or [])
    for group in (tx.get('meta') or {}).get('innerInstructions') or []:
        instructions.extend(group.get('instructions') or [])
    for ins in instructions:
        if ins.get('programId') != PUMP or not isinstance(ins.get('data'), str):
            continue
        try:
            if list(b58decode(ins['data'])[:8]) != MIGRATE_DISC:
                continue
        except (ValueError, TypeError):
            continue
        accounts = [keystr(a) for a in ins.get('accounts') or []]
        if len(accounts) < 10 or accounts[8] != PUMPSWAP:
            continue
        return {'mint': accounts[2], 'pool': accounts[9], 'quote_mint': WSOL,
                'decoder': 'official_pump_idl_migrate_layout'}
    return None


def load(path, default):
    return json.loads(path.read_text()) if path.exists() else default


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + '.tmp')
    temp.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')
    temp.replace(path)


def append_jsonl(path, row):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('a') as stream:
        stream.write(json.dumps(row, separators=(',', ':')) + '\n')


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise urllib.error.HTTPError(req.full_url, code, 'redirect_blocked', headers, fp)


def req(url, payload=None, headers=None):
    """Fail closed: only the quote GET and three explicitly read-only RPC methods."""
    parsed = urlsplit(url)
    if parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError('unsafe_endpoint')
    if payload is None:
        if parsed.netloc != 'api.jup.ag' or parsed.path != '/swap/v1/quote':
            raise ValueError('endpoint_not_allowlisted')
    elif not isinstance(payload, dict) or payload.get('method') not in READ_METHODS:
        raise ValueError('rpc_method_not_allowlisted')
    data = json.dumps(payload).encode() if payload is not None else None
    request = urllib.request.Request(url, data=data, method='POST' if data else 'GET',
        headers={'User-Agent': 'MemeHunterAI-ReadOnly-Research/0.3',
                 'Content-Type': 'application/json', **(headers or {})})
    try:
        with urllib.request.build_opener(NoRedirect()).open(request, timeout=6) as response:
            body = response.read(8_000_001)
            if len(body) > 8_000_000:
                return {'_error': 'response_too_large'}
            return json.loads(body)
    except urllib.error.HTTPError as exc:
        try:
            retry = max(0.0, min(3600.0, float(exc.headers.get('Retry-After', '0'))))
        except (ValueError, TypeError, AttributeError):
            retry = 0.0
        # Do not publish response bodies, URLs, credentials, or exception messages.
        return {'_error': 'http_error', 'http_status': exc.code, 'retry_after_seconds': retry}
    except Exception as exc:
        return {'_error': type(exc).__name__}


def rpc(method, params):
    if method not in READ_METHODS:
        raise ValueError('rpc_method_not_allowlisted')
    url = os.environ.get('SOLANA_RPC_URL', '').strip() or 'https://solana-rpc.publicnode.com'
    result = req(url, {'jsonrpc': '2.0', 'id': 1, 'method': method, 'params': params})
    return result.get('result') if isinstance(result, dict) and not result.get('_error') and not result.get('error') else None


def jupiter_quote(input_mint, output_mint, amount):
    if not isinstance(amount, int) or isinstance(amount, bool) or amount <= 0:
        raise ValueError('invalid_input_amount')
    key = os.environ.get('JUPITER_API_KEY', '').strip()
    url = QUOTE_URL + '?' + urlencode({'inputMint': input_mint, 'outputMint': output_mint,
        'amount': str(amount), 'slippageBps': '100', 'swapMode': 'ExactIn'})
    started = time.time()
    raw = req(url, headers={'x-api-key': key} if key else {})
    received = time.time()
    quote = {'status': 'invalid_response', 'provider': 'jupiter_metis_v1',
        'access_mode': 'api_key' if key else 'keyless', 'requested_epoch': started,
        'observed_at': utc(received), 'received_epoch': received,
        'request_latency_seconds': received - started, 'fills_assumed': False}
    if isinstance(raw, dict) and raw.get('_error'):
        code = raw.get('http_status')
        quote.update(status=('auth_error' if code in (401, 403) else 'rate_limited' if code == 429 else 'provider_error'),
                     error=raw['_error'], http_status=code,
                     retry_after_seconds=raw.get('retry_after_seconds', 0))
        return quote
    if not isinstance(raw, dict):
        return quote
    if raw.get('error') or raw.get('errorCode'):
        quote['status'] = 'no_route' if raw.get('errorCode') in {'NO_ROUTES_FOUND', 'COULD_NOT_FIND_ANY_ROUTE', 'TOKEN_NOT_TRADABLE'} else 'provider_error'
        return quote
    try:
        valid = (raw.get('inputMint') == input_mint and raw.get('outputMint') == output_mint
            and raw.get('swapMode') == 'ExactIn' and int(raw['inAmount']) == amount
            and int(raw['outAmount']) > 0 and int(raw['contextSlot']) > 0
            and 0 <= int(raw['otherAmountThreshold']) <= int(raw['outAmount'])
            and isinstance(raw.get('routePlan'), list) and bool(raw['routePlan'])
            and all(isinstance(p, dict) and isinstance(p.get('swapInfo'), dict) and p['swapInfo'].get('ammKey') for p in raw['routePlan']))
    except (ValueError, TypeError, KeyError, OverflowError):
        valid = False
    if valid:
        fields = ('inputMint', 'outputMint', 'inAmount', 'outAmount', 'otherAmountThreshold',
                  'swapMode', 'slippageBps', 'platformFee', 'priceImpactPct', 'routePlan', 'contextSlot', 'timeTaken')
        quote.update(status='quote_observed', raw={k: raw[k] for k in fields if k in raw})
    return quote


def get_tx(sig):
    return rpc('getTransaction', [sig, {'encoding': 'jsonParsed', 'commitment': 'confirmed',
                                      'maxSupportedTransactionVersion': MAX_TX_VERSION}])


def quote_entry(mint, amount_usdc_raw):
    return jupiter_quote(USDC, mint, amount_usdc_raw)


def quote_exit(mint, token_amount_raw):
    return jupiter_quote(mint, USDC, token_amount_raw)


def discover(events, seen, stop, end):
    """Discovery never blocks the independent deadline scheduler."""
    try:
        slot = rpc('getSlot', [{'commitment': 'confirmed'}])
        sigs = rpc('getSignaturesForAddress', [PUMP, {'limit': 100, 'commitment': 'confirmed'}]) if slot is not None else None
        events.put(('rpc', {'connected': slot is not None and isinstance(sigs, list),
                           'slot': slot, 'checked_at': utc(), 'signature_window_saturated': isinstance(sigs, list) and len(sigs) == 100}))
        for header in reversed(sigs if isinstance(sigs, list) else []):
            if stop.is_set() or time.monotonic() >= end:
                break
            sig = header.get('signature')
            if not sig or sig in seen or header.get('err') is not None:
                continue
            tx = get_tx(sig)
            if tx is None:
                events.put(('tx_failure', None))
                continue
            events.put(('seen', sig))
            migration = decode_migration(tx)
            if migration:
                observed = time.time()
                block_time = tx.get('blockTime')
                events.put(('opportunity', {'id': sig, 'signature': sig, **migration,
                    'chain_block_time': block_time, 'first_observed_at': utc(observed),
                    'first_observed_epoch': observed, 'actionable_at': utc(observed), 'actionable_epoch': observed,
                    'observation_lag_seconds': observed - block_time if isinstance(block_time, (int, float)) else None,
                    'selection_reason': 'verified_pump_migrate_instruction', 'future_information_used': False,
                    'wallet_evidence_as_of_decision': 'unknown_not_collected', 'collector_version': VERSION,
                    'entry_quotes': {}, 'exit_quotes': {}, 'positions': {}}))
    except Exception as exc:
        events.put(('discovery_error', type(exc).__name__))


def pending_tasks(state, cfg):
    tasks = []
    for op in state['opportunities'].values():
        for delay in cfg.get('additional_delay_seconds', [30, 60, 120, 300]):
            if str(delay) not in op['entry_quotes']:
                tasks.append((op['actionable_epoch'] + delay, 'entry', op['id'], str(delay), None))
        for delay, pos in op.get('positions', {}).items():
            exits = op['exit_quotes'].get(delay, {})
            # New exits start at receipt of the entry quote, not before it was known.
            origin = pos.get('entry_received_epoch', pos['entry_requested_epoch'])
            for horizon in cfg.get('exit_horizons_seconds', [300, 900, 3600]):
                if str(horizon) not in exits:
                    tasks.append((origin + horizon, 'exit', op['id'], delay, str(horizon)))
    return sorted(tasks)


def measured_quote(state, input_mint, output_mint, amount):
    quote = jupiter_quote(input_mint, output_mint, amount)
    received = quote['received_epoch']
    state['quote_next_epoch'] = received + max(MIN_QUOTE_INTERVAL, float(quote.get('retry_after_seconds', 0)),
        60.0 if quote['status'] == 'rate_limited' else 300.0 if quote['status'] == 'auth_error' else 0.0)
    slot = state.get('rpc_health', {}).get('slot')
    if quote['status'] == 'quote_observed' and isinstance(slot, int):
        quote['context_slot_delta_from_rpc'] = int(quote['raw']['contextSlot']) - slot
        if quote['context_slot_delta_from_rpc'] < -150:
            quote['status'] = 'stale_context'
    quote['freshness_note'] = 'Context slot checked when RPC available; not an execution guarantee.'
    return quote


def service_due(state, cfg, now):
    tasks = pending_tasks(state, cfg)
    if not tasks or tasks[0][0] > now:
        return False
    scheduled, kind, oid, delay, horizon = tasks[0]
    op = state['opportunities'][oid]
    if now - scheduled > MAX_LATENESS:
        quote = {'status': 'missed_deadline', 'observed_at': utc(now), 'requested_epoch': None,
                 'late_by_seconds': now - scheduled, 'reason': 'deadline_expired_no_backfill'}
    elif now < state.get('quote_next_epoch', 0):
        return False
    else:
        amount = 50_000_000 if kind == 'entry' else int(op['positions'][delay]['token_amount_raw'])
        quote = measured_quote(state, USDC if kind == 'entry' else op['mint'],
                               op['mint'] if kind == 'entry' else USDC, amount)
        quote['late_by_seconds'] = max(0.0, quote['requested_epoch'] - scheduled)
        quote['received_late_by_seconds'] = max(0.0, quote['received_epoch'] - scheduled)
        quote['timing_eligible'] = quote['late_by_seconds'] <= MAX_LATENESS
    quote['scheduled_epoch'] = scheduled
    quote['collector_version'] = VERSION
    if kind == 'entry':
        quote.update(scheduled_delay_seconds=int(delay), hypothetical_input_usdc=50.0)
        quote['actual_delay_from_actionable_seconds'] = (quote['requested_epoch'] - op['actionable_epoch']) if quote.get('requested_epoch') is not None else None
        op['entry_quotes'][delay] = quote
        if quote['status'] == 'quote_observed':
            op['positions'][delay] = {'token_amount_raw': quote['raw']['outAmount'],
                'entry_requested_epoch': quote['requested_epoch'], 'entry_received_epoch': quote['received_epoch'],
                'entry_observed_at': quote['observed_at'], 'hypothetical_only': True}
    else:
        quote.update(entry_delay_seconds=int(delay), exit_horizon_seconds=int(horizon),
                     hypothetical_token_input_raw=op['positions'][delay]['token_amount_raw'])
        op['exit_quotes'].setdefault(delay, {})[horizon] = quote
    append_jsonl(DATA / 'quotes.jsonl', {'opportunity_id': oid, 'kind': kind, **quote})
    return True


def service_probe(state, cfg, now):
    health = state.setdefault('provider_health', {})
    tasks = pending_tasks(state, cfg)
    if now < state.get('quote_next_epoch', 0) or (tasks and tasks[0][0] <= now + 8):
        return False
    pending = health.get('pending_exit_amount')
    if not pending and now < health.get('next_probe_epoch', 0):
        return False
    quote = measured_quote(state, WSOL if pending else USDC, USDC if pending else WSOL,
                           int(pending) if pending else 50_000_000)
    kind = 'exit' if pending else 'entry'
    health[kind] = quote
    health.update(checked_at=quote['observed_at'], access_mode=quote['access_mode'],
                  endpoint=QUOTE_URL, version=VERSION, experiment_sample=False)
    if not pending:
        health.pop('exit', None)
    if quote['status'] == 'quote_observed' and not pending:
        health['pending_exit_amount'] = quote['raw']['outAmount']
        health['status'] = 'entry_verified_exit_pending'
    else:
        health.pop('pending_exit_amount', None)
        health['status'] = 'healthy' if pending and quote['status'] == 'quote_observed' else quote['status']
        health['next_probe_epoch'] = time.time() + (600 if health['status'] == 'healthy' else 300)
    append_jsonl(DATA / 'provider_checks.jsonl', {'kind': kind, 'experiment_sample': False, **quote})
    save(DATA / 'provider_health.json', health)
    return True


def publish_snapshot(state, new_migrations):
    entries = [q for op in state['opportunities'].values() for q in op['entry_quotes'].values()]
    exits = [q for op in state['opportunities'].values() for group in op['exit_quotes'].values() for q in group.values()]
    health = state.get('provider_health', {})
    rpc_health = state.get('rpc_health', {})
    latest = {'version': VERSION, 'updated_at': utc(), 'mode': 'WATCH_ONLY', 'cycles': state['cycles'],
        'rpc_connected': rpc_health.get('connected', False), 'slot': rpc_health.get('slot'),
        'rpc_consecutive_failures': state.get('rpc_consecutive_failures', 0),
        'transaction_fetch_failures': state.get('transaction_fetch_failures', 0),
        'validated_migrations': len(state['opportunities']), 'new_migrations_this_cycle': new_migrations,
        'entry_quotes_observed': sum(q.get('status') == 'quote_observed' for q in entries),
        'exit_quotes_observed': sum(q.get('status') == 'quote_observed' for q in exits),
        'quote_failures': sum(q.get('status') != 'quote_observed' for q in entries + exits),
        'missed_deadlines': sum(q.get('status') == 'missed_deadline' for q in entries + exits),
        'quote_provider_api_key_configured': bool(os.environ.get('JUPITER_API_KEY', '').strip()),
        'quote_provider_access_mode': 'api_key' if os.environ.get('JUPITER_API_KEY', '').strip() else 'keyless',
        'quote_provider_health': health.get('status', 'not_checked'),
        'quote_provider_checked_at': health.get('checked_at'),
        'health_checks_excluded_from_experiment': True, 'real_trades_placed': 0, 'realized_profit': None,
        'coverage_note': 'Bounded latest-100 signature polling; complete migration coverage is NOT established.',
        'signature_window_saturated': rpc_health.get('signature_window_saturated', False)}
    save(DATA / 'state.json', state)
    save(DATA / 'latest.json', latest)
    lines = ['# Prospective Quote Lab', '', '**WATCH ONLY — no trades.**', '', f"Updated: {latest['updated_at']}",
        f'Collector: {VERSION}', f"RPC connected: {latest['rpc_connected']}",
        f"Validated Pump migrations: {latest['validated_migrations']}",
        f"Observed entry quotes: {latest['entry_quotes_observed']}", f"Observed exit quotes: {latest['exit_quotes_observed']}",
        f"Quote failures/unavailable: {latest['quote_failures']}", f"Missed deadlines (no backfill): {latest['missed_deadlines']}",
        f"Jupiter API key configured: {latest['quote_provider_api_key_configured']}",
        f"Quote access mode: {latest['quote_provider_access_mode']}", f"Provider connection test: {latest['quote_provider_health']}",
        '', 'Connection-test SOL/USDC quotes are separate from migration samples and never imply profit.',
        'Existing failed observations are retained. Expired deadlines are never backfilled.',
        'New exit horizons start when the entry quote was received; actual request/receipt times are retained.',
        'Quotes are route snapshots, not fills. Network fees, execution slippage, and realized profit are not established.',
        latest['coverage_note'], '', '## Recent opportunities', '',
        '| Mint | First observed | Lag from chain | Entry quote states |', '|---|---|---:|---|']
    for op in sorted(state['opportunities'].values(), key=lambda x: x['first_observed_epoch'], reverse=True)[:20]:
        quotes = ', '.join(k + ':' + v.get('status', '?') for k, v in sorted(op['entry_quotes'].items(), key=lambda x: int(x[0]))) or 'none'
        lines.append(f"| {op['mint']} | {op['first_observed_at']} | {op.get('observation_lag_seconds')} | {quotes} |")
    (DATA / 'REPORT.md').write_text('\n'.join(lines) + '\n')
    return latest


def cycle(run_seconds=20.0):
    cfg, ctl = load(ROOT / 'config.json', {}), load(ROOT / 'control.json', {})
    if ctl.get('enabled') is not True or ctl.get('mode') != 'WATCH_ONLY' or cfg.get('mode', 'WATCH_ONLY') != 'WATCH_ONLY':
        return {'status': 'STOPPED'}
    state = load(DATA / 'state.json', {'schema': 2, 'started_at': utc(), 'cycles': 0, 'seen': [], 'opportunities': {}, 'errors': []})
    if state.get('schema') != 2:
        raise ValueError('unknown_state_schema_history_not_reset')
    state['cycles'] += 1
    events, stop = queue.Queue(), threading.Event()
    end = time.monotonic() + run_seconds
    worker = threading.Thread(target=discover, args=(events, set(state['seen']), stop, end), daemon=True)
    worker.start()
    seen = set(state['seen'])
    new_migrations = 0
    while worker.is_alive() or not events.empty() or time.monotonic() < end:
        ctl = load(ROOT / 'control.json', {})
        enabled = ctl.get('enabled') is True and ctl.get('mode') == 'WATCH_ONLY'
        if not enabled:
            stop.set()
        while not events.empty():
            kind, value = events.get_nowait()
            if kind == 'seen' and value not in seen:
                state['seen'].append(value)
                seen.add(value)
            elif kind == 'rpc':
                state['rpc_health'] = value
                state['rpc_consecutive_failures'] = 0 if value['connected'] else state.get('rpc_consecutive_failures', 0) + 1
            elif kind == 'tx_failure':
                state['transaction_fetch_failures'] = state.get('transaction_fetch_failures', 0) + 1
            elif kind == 'opportunity' and value['id'] not in state['opportunities']:
                state['opportunities'][value['id']] = value
                append_jsonl(DATA / 'opportunities.jsonl', value)
                new_migrations += 1
            elif kind == 'discovery_error':
                state['errors'] = (state.get('errors', []) + [value])[-100:]
                state['rpc_health'] = {'connected': False, 'checked_at': utc()}
                state['rpc_consecutive_failures'] = state.get('rpc_consecutive_failures', 0) + 1
        if enabled:
            if not service_due(state, cfg, time.time()):
                service_probe(state, cfg, time.time())
        elif not worker.is_alive():
            break
        time.sleep(0.25)
    state['seen'] = state['seen'][-20000:]
    return publish_snapshot(state, new_migrations)


if __name__ == '__main__':
    # Hot handover after the existing runner pulls a tested checkpoint; no job cancellation.
    from collector import activate, cycle as verified_cycle
    activate()
    print(json.dumps(verified_cycle()))
