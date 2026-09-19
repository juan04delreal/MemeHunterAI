#!/usr/bin/env python3
"""Read-only, bounded Solana observation cycle. No transaction signing or execution."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import re
import time
import urllib.error
import urllib.request
from collections import defaultdict
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / 'data'
ALPHABET = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'
PUMP = '6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P'
SWAP = 'pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA'
WSOL = 'So11111111111111111111111111111111111111112'
USDC = 'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v'
QUOTES = {WSOL, USDC}
READ_METHODS = {'getSlot', 'getSignaturesForAddress', 'getTransaction'}
VERSION = 'early-wallet-observer-1.2'
MAX_SUPPORTED_TRANSACTION_VERSION = 1


def utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def b58decode(s: str) -> bytes:
    n = 0
    for c in s:
        n = n * 58 + ALPHABET.index(c)
    return b'\0' * (len(s) - len(s.lstrip('1'))) + (n.to_bytes((n.bit_length()+7)//8, 'big') if n else b'')


def valid_address(s: str) -> bool:
    try:
        return len(b58decode(s)) == 32
    except (ValueError, TypeError):
        return False


def load(path: Path, default=None):
    return json.loads(path.read_text()) if path.exists() else default


def save(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + '.tmp')
    tmp.write_text(json.dumps(obj, ensure_ascii=True, indent=2, sort_keys=True) + '\n')
    tmp.replace(path)


class FeedError(RuntimeError):
    """Sanitized exception: URLs and credentials must never reach logs."""
    def __init__(self, message, code=None):
        super().__init__(message)
        self.code = code


def request_json(url: str, payload=None):
    if not url.startswith('https://'):
        raise FeedError('HTTPS required')
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, headers={
        'User-Agent': 'MemeHunterAI-ReadOnlyResearch/1.0', 'Accept': 'application/json',
        'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=12) as r:
            raw = r.read(12_000_001)
            if len(raw) > 12_000_000:
                raise FeedError('response size limit')
            return json.loads(raw)
    except urllib.error.HTTPError as e:
        raise FeedError(f'HTTP {e.code}') from None
    except (urllib.error.URLError, TimeoutError, OSError, ValueError):
        raise FeedError('network/JSON error') from None


class RPC:
    def __init__(self):
        self.url = os.environ.get('SOLANA_RPC_URL', '').strip() or 'https://solana-rpc.publicnode.com'
        self.last = 0.0
        self.calls = 0
        self.label = 'configured-private-endpoint' if os.environ.get('SOLANA_RPC_URL', '').strip() else 'publicnode-public'

    def call(self, method, params):
        if method not in READ_METHODS:
            raise FeedError('method not in read-only allowlist')
        time.sleep(max(0, .4 - (time.monotonic() - self.last)))
        self.last = time.monotonic()
        self.calls += 1
        obj = request_json(self.url, {'jsonrpc': '2.0', 'id': self.calls, 'method': method, 'params': params})
        if not isinstance(obj, dict) or 'result' not in obj or obj.get('error'):
            code = (obj.get('error') or {}).get('code', 'unknown') if isinstance(obj, dict) else 'invalid'
            raise FeedError(f'RPC error {code}', code=code)
        return obj['result']


def keystr(a):
    return a.get('pubkey', '') if isinstance(a, dict) else str(a)


def decode_flows(tx: dict, watched: set[str]) -> list[dict]:
    """Net owner deltas, plus conservative Pump instruction attribution.

    A transaction-level buy candidate is NOT a cost basis, profit, or proof of early entry.
    Complex multi-instruction transactions remain candidates pending audit.
    """
    meta = tx.get('meta') or {}
    if meta.get('err') is not None:
        return []
    msg = (tx.get('transaction') or {}).get('message') or {}
    keys = msg.get('accountKeys') or []
    signers = {keystr(k) for k in keys if isinstance(k, dict) and k.get('signer')}
    instructions = list(msg.get('instructions') or [])
    for group in meta.get('innerInstructions') or []:
        instructions.extend(group.get('instructions') or [])
    contexts = defaultdict(set)
    for ins in instructions:
        program = ins.get('programId')
        if program not in {PUMP, SWAP} or not isinstance(ins.get('data'), str):
            continue
        try:
            prefix = b58decode(ins['data'])[:8]
            accounts = [keystr(a) for a in ins.get('accounts', [])]
            for name, side in [('buy', 'buy'), ('buy_exact_sol_in', 'buy'), ('buy_exact_quote_in', 'buy'), ('sell', 'sell')]:
                if prefix != hashlib.sha256(('global:' + name).encode()).digest()[:8]:
                    continue
                if program == PUMP and len(accounts) > 6:
                    contexts[(accounts[6], accounts[2])].add(side)
                elif program == SWAP and len(accounts) > 4:
                    contexts[(accounts[1], accounts[3])].add(side)
        except (ValueError, IndexError, TypeError):
            continue
    owners = watched | signers | {owner for owner, _ in contexts}
    balances = defaultdict(lambda: [Decimal(0), Decimal(0)])
    for phase, field in enumerate(['preTokenBalances', 'postTokenBalances']):
        for row in meta.get(field) or []:
            owner, mint = row.get('owner'), row.get('mint')
            if owner not in owners or not mint:
                continue
            amt = row.get('uiTokenAmount') or {}
            try:
                balances[(owner, mint)][phase] += Decimal(amt['amount']) / (Decimal(10) ** int(amt['decimals']))
            except (KeyError, ValueError, ArithmeticError):
                continue
    native = {}
    for i, key in enumerate(keys):
        if keystr(key) in owners and i < len(meta.get('postBalances') or []) and i < len(meta.get('preBalances') or []):
            native[keystr(key)] = (int(meta['postBalances'][i]) - int(meta['preBalances'][i])) / 1e9
    out = []
    for (owner, mint), (before, after) in balances.items():
        delta = after - before
        if not delta or mint in QUOTES:
            continue
        sides = contexts.get((owner, mint), set())
        classification = 'inflow_unclassified' if delta > 0 else 'outflow_unclassified'
        if sides == {'buy'} and delta > 0:
            classification = 'buy_candidate'
        elif sides == {'sell'} and delta < 0:
            classification = 'sell_candidate'
        elif len(sides) > 1:
            classification = 'mixed_trade_unclassified'
        out.append({'wallet': owner, 'mint': mint, 'classification': classification,
                    'token_delta': str(delta), 'pre_amount': str(before), 'post_amount': str(after),
                    'native_sol_delta_including_rent_fees_and_other_flows': native.get(owner),
                    'transaction_fee_lamports': meta.get('fee'),
                    'attribution': 'program_discriminator_and_account_roles' if sides else 'balance_change_only',
                    'realized_profit': None, 'historical_entry_price': None})
    return out


def money(v):
    try:
        n = float(v)
        return f'${n:,.6f}' if abs(n) < 1 else f'${n:,.2f}'
    except (TypeError, ValueError):
        return 'unavailable'


def report(state: dict, cfg: dict, latest: dict) -> None:
    lines = ['# Early-wallet live research watchlist', '',
             '**WATCH ONLY. No trading, no private keys, no verified profitable-copy list.**', '',
             f"Last observation (UTC): `{latest['updated_at']}`", '',
             f"Status: **{latest['status']}** | Completed observation cycles: {state['cycles']}",
             f"Configured seed coins: {len(cfg['tokens'])} | Wallet leads: {len(cfg['wallets'])}",
             f"RPC: {latest['rpc_status']} | Pending transaction decodes: {len(state['pending'])}",
             f"Unresolved transactions retained in evidence logs: {state.get('unresolved_transaction_count', 0)}", '',
             'Refresh this page. Data is checkpointed about every 5 minutes; the collector targets 60-second cycles.',
             'The hourly supervisor renews bounded GitHub jobs. Runner/provider delays and restarts can cause gaps.', '',
             '## Market snapshots (not executable quotes)', '',
             '| Mint | Symbol | Observed price | Pool liquidity |', '|---|---|---:|---:|']
    for mint in cfg['tokens']:
        p = latest['markets'].get(mint, {})
        symbol = re.sub(r'[^a-zA-Z0-9 _.-]', '', str(p.get('symbol', 'unknown')))[:25]
        lines.append(f"| `{mint}` | {symbol} | {money(p.get('price_usd'))} | {money(p.get('liquidity_usd'))} |")
    lines += ['', '## Wallet leads (unverified)', '',
              '| Wallet | Role | Last successful address scan (UTC) |', '|---|---|---|']
    for w in cfg['wallets']:
        ws = state['wallets'].get(w['address'], {})
        lines.append(f"| `{w['address']}` | {w['role']} | {ws.get('last_scan_at', 'not yet available')} |")
    lines += ['', '## Cross-token observations since this collector started', '',
              'These are sampled, instruction-supported **buy candidates**, not verified early buys or independent wallets.', '',
              '| Wallet | Distinct supplied mints with observed buy candidates |', '|---|---:|']
    overlaps = sorted(state['overlap'].items(), key=lambda item: (-len(item[1]), item[0]))[:30]
    if not overlaps:
        lines += ['| None recorded yet | 0 |']
    for addr, mints in overlaps:
        lines.append(f'| `{addr}` | {len(mints)} |')
    lines += ['', '## Data-quality limits', '',
              '- Initial wallet scans establish a forward baseline; they do not reconstruct earlier buys.',
              '- Wallet-address signatures are monitored; unsolicited SPL transfers can be missed when the owner is not referenced.',
              '- Pool discovery samples two rotating selected pools per cycle; it is not a complete buyer list or launch-rank study.',
              '- Unknown programs, transfers, allocations, and complex transactions are not promoted to verified buys.',
              '- Pool creation time is NOT token creation time. Early-entry flags and profit are intentionally unset.',
              '- A mark is not an exit quote. No simulated fills or P&L are invented.',
              '- RPC errors and pagination gaps are retained in the event logs. A running job alone is not proof of a healthy wallet feed.', '',
              '## Latest observed events', '']
    for row in state['recent_events'][-15:]:
        lines.append(f"- `{row.get('observed_at')}` {row.get('classification')} `{row.get('wallet')}` / `{row.get('mint')}` / tx `{row.get('signature')}`")
    if latest['errors']:
        lines += ['', '## Latest feed errors', ''] + ['- ' + x for x in latest['errors']]
    lines += ['', '## Stop and results', '',
              'Set `watchlist/control.json` to `{"enabled": false}` on this branch. The current job checks the stop switch each cycle.',
              'The hourly supervisor must also be disabled when stopping. Existing data is retained.',
              'Read `watchlist/data/latest.json`, `state.json`, and the dated JSONL event files for analysis.', '']
    path = DATA / 'REPORT.md'
    path.write_text('\n'.join(lines))



def bootstrap_recovery(state: dict) -> None:
    """Requeue previously retired transaction signatures once after the v1 reader repair.

    Recovery records are historical evidence only. They must never be counted as forward
    signals at their original block time.
    """
    marker = 'txv1-recovery-20260919'
    if state.get('recovery_bootstrap') == marker:
        return
    retired, first_failure = {}, {}
    for path in sorted(DATA.glob('events/**/*.jsonl')):
        try:
            lines = path.read_text().splitlines()
        except OSError:
            continue
        for raw in lines:
            try:
                event = json.loads(raw)
            except ValueError:
                continue
            sig = event.get('signature')
            if not sig:
                continue
            if event.get('kind') == 'transaction_decode_error':
                first_failure.setdefault(sig, event.get('observed_at'))
            elif event.get('kind') == 'transaction_unavailable':
                retired[sig] = event
    seen = set(state.get('seen', []))
    recovered = set(state.get('recovered_signatures', []))
    for sig, event in retired.items():
        if sig in recovered or sig in state.get('pending', {}):
            continue
        seen.discard(sig)
        state.setdefault('pending', {})[sig] = {
            'detected_at': first_failure.get(sig) or event.get('observed_at') or utc(),
            'block_time': event.get('chain_block_time'),
            'sources': event.get('sources') or ['historical-unresolved'],
            'priority': -1,
            'attempts': 0,
            'recovery': True,
        }
    state['seen'] = list(seen)
    state['recovery_bootstrap'] = marker
    state['recovery_bootstrap_found'] = len(retired)
    state.setdefault('recovered_signatures', [])
    state.setdefault('recovered_transaction_count', 0)


def run_cycle() -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    cfg = load(ROOT / 'config.json')
    assert cfg['mode'] == 'WATCH_ONLY'
    for a in cfg['tokens'] + [w['address'] for w in cfg['wallets']]:
        if not valid_address(a):
            raise ValueError('invalid configured public address')
    state = load(DATA / 'state.json', {'schema': 1, 'started_at': utc(), 'cycles': 0, 'wallets': {},
        'pending': {}, 'seen': [], 'tracked_new_mints': [], 'overlap': {}, 'recent_events': [], 'rpc_retry_after': 0})
    bootstrap_recovery(state)
    state['cycles'] += 1
    seen = set(state['seen'])
    rows, errors, markets = [], [], {}
    now = utc()
    def emit(kind, **kw):
        rows.append({'kind': kind, 'observed_at': utc(), **kw})
    mints = list(dict.fromkeys(cfg['tokens'] + state['tracked_new_mints']))
    for start in range(0, len(mints), 30):
        chunk = mints[start:start+30]
        try:
            pairs = request_json('https://api.dexscreener.com/tokens/v1/solana/' + ','.join(chunk))
            if not isinstance(pairs, list):
                raise FeedError('DEX response not a list')
            for mint in chunk:
                options = [p for p in pairs if p.get('chainId') == 'solana' and (p.get('baseToken') or {}).get('address') == mint]
                if not options:
                    emit('market_missing', mint=mint)
                    continue
                p = max(options, key=lambda p: float((p.get('liquidity') or {}).get('usd') or 0))
                item = {'mint': mint, 'symbol': (p.get('baseToken') or {}).get('symbol'),
                    'pair': p.get('pairAddress'), 'dex': p.get('dexId'), 'price_usd': p.get('priceUsd'),
                    'liquidity_usd': (p.get('liquidity') or {}).get('usd'), 'market_cap': p.get('marketCap'),
                    'pair_created_at_ms': p.get('pairCreatedAt'), 'token_creation_time': None,
                    'volume': p.get('volume'), 'transactions_aggregate': p.get('txns'),
                    'provider_event_time': None, 'source': 'DEX Screener', 'executable_quote': False}
                markets[mint] = item
                emit('market_snapshot', **item)
        except FeedError as e:
            errors.append('market feed: ' + str(e))
            emit('feed_error', feed='market', error=str(e))
    rpc = RPC()
    rpc_status = 'cooldown'
    watched = {w['address'] for w in cfg['wallets']}
    def enqueue(sig, source, block_time):
        if sig in seen:
            return True
        if sig in state['pending']:
            entry = state['pending'][sig]
            if source in watched:
                entry['priority'] = 0
            if source not in entry['sources']:
                entry['sources'].append(source)
            return True
        if len(state['pending']) >= 2000:
            return False
        state['pending'][sig] = {'detected_at': utc(), 'block_time': block_time,
                                'sources': [source], 'priority': 0 if source in watched else 1, 'attempts': 0}
        return True
    if time.time() >= state['rpc_retry_after']:
        try:
            slot = rpc.call('getSlot', [{'commitment': 'confirmed'}])
            emit('rpc_heartbeat', slot=slot, provider=rpc.label)
            rpc_status = 'connected'
            for wallet in cfg['wallets']:
                addr = wallet['address']
                ws = state['wallets'].setdefault(addr, {'initialized': False, 'cursor': '', 'scan': None})
                if not ws['initialized']:
                    recent = rpc.call('getSignaturesForAddress', [addr, {'limit': 1, 'commitment': 'confirmed'}])
                    ws['cursor'] = recent[0]['signature'] if recent else ''
                    ws['initialized'] = True
                    ws['last_chain_activity_time'] = recent[0].get('blockTime') if recent else None
                    ws['last_scan_at'] = utc()
                    emit('wallet_baseline', wallet=addr, cursor=ws['cursor'], last_chain_activity_time=ws['last_chain_activity_time'])
                    continue
                scan = ws.get('scan') or {'anchor': ws['cursor'], 'head': '', 'before': ''}
                opts = {'limit': 100, 'commitment': 'confirmed'}
                if scan['before']:
                    opts['before'] = scan['before']
                history = rpc.call('getSignaturesForAddress', [addr, opts])
                ws['last_scan_at'] = utc()
                if history and not scan['head']:
                    scan['head'] = history[0]['signature']
                    ws['last_chain_activity_time'] = history[0].get('blockTime')
                complete, found_anchor, blocked = False, False, False
                for h in history:
                    sig = h['signature']
                    if sig == scan['anchor']:
                        complete, found_anchor = True, True
                        break
                    if h.get('err') is None and not enqueue(sig, addr, h.get('blockTime')):
                        blocked = True
                        emit('backlog_limit', wallet=addr, capacity=2000)
                        break
                    if h.get('err') is not None:
                        emit('failed_chain_transaction', wallet=addr, signature=sig, chain_block_time=h.get('blockTime'))
                    scan['before'] = sig
                if not blocked and len(history) < 100:
                    complete = True
                    if scan['anchor'] and not found_anchor:
                        emit('coverage_gap', wallet=addr, reason='previous cursor not found before available history ended')
                if complete:
                    ws['cursor'] = scan['head'] or ws['cursor']
                    ws['scan'] = None
                else:
                    ws['scan'] = scan
            # Bounded discovery sample; never advertised as all trades in these pools.
            seed_pools = [(m, markets[m]['pair']) for m in cfg['tokens'] if m in markets and valid_address(markets[m].get('pair', ''))]
            if seed_pools:
                offset = ((state['cycles'] - 1) * 2) % len(seed_pools)
                for i in range(min(2, len(seed_pools))):
                    mint, pool = seed_pools[(offset + i) % len(seed_pools)]
                    sample = rpc.call('getSignaturesForAddress', [pool, {'limit': 3, 'commitment': 'confirmed'}])
                    emit('pool_sample', mint=mint, pool=pool, signatures=len(sample), exhaustive=False)
                    for h in sample:
                        if h.get('err') is None and not enqueue(h['signature'], pool, h.get('blockTime')):
                            emit('pool_sample_skipped', mint=mint, reason='decode backlog full')
            pending = sorted(state['pending'], key=lambda sig: (state['pending'][sig]['priority'], state['pending'][sig]['detected_at']))
            for sig in pending[:30]:
                entry = state['pending'][sig]
                try:
                    tx = rpc.call('getTransaction', [sig, {'encoding': 'jsonParsed', 'commitment': 'confirmed', 'maxSupportedTransactionVersion': MAX_SUPPORTED_TRANSACTION_VERSION}])
                except FeedError as exc:
                    # A transaction-specific RPC error must not stop other wallet scans.
                    # Network/HTTP errors retain global backoff rather than hammering a provider.
                    if exc.code is None:
                        raise
                    entry['attempts'] += 1
                    errors.append('transaction decode: ' + str(exc))
                    emit('transaction_decode_error', signature=sig, error=str(exc),
                         attempts=entry['attempts'], sources=entry['sources'])
                    if entry['attempts'] >= 8:
                        if entry.get('recovery'):
                            emit('recovery_still_unresolved', signature=sig, attempts=entry['attempts'],
                                 sources=entry['sources'], reason='repeated RPC decode error')
                            entry['attempts'] = 0
                        else:
                            emit('transaction_unavailable', signature=sig, attempts=entry['attempts'],
                                 sources=entry['sources'], reason='repeated RPC decode error; unresolved')
                            state['unresolved_transaction_count'] = state.get('unresolved_transaction_count', 0) + 1
                            del state['pending'][sig]
                            seen.add(sig)
                    continue
                if tx is None:
                    entry['attempts'] += 1
                    if entry['attempts'] >= 8:
                        if entry.get('recovery'):
                            emit('recovery_still_unresolved', signature=sig, attempts=entry['attempts'],
                                 sources=entry['sources'], reason='transaction still unavailable')
                            entry['attempts'] = 0
                        else:
                            emit('transaction_unavailable', signature=sig, attempts=entry['attempts'], sources=entry['sources'])
                            state['unresolved_transaction_count'] = state.get('unresolved_transaction_count', 0) + 1
                            del state['pending'][sig]
                            seen.add(sig)
                    continue
                # Keep audit evidence, not merely a dashboard count.
                recovered_at = utc() if entry.get('recovery') else None
                emit('transaction_evidence', signature=sig, detected_at=entry['detected_at'],
                     recovered_at=recovered_at, recovery=bool(entry.get('recovery')),
                     rpc_max_supported_transaction_version=MAX_SUPPORTED_TRANSACTION_VERSION,
                     sources=entry['sources'], transaction=tx)
                chain_time = tx.get('blockTime')
                lag = None
                if isinstance(chain_time, (int, float)):
                    lag = datetime.fromisoformat(entry['detected_at']).timestamp() - chain_time
                for flow in decode_flows(tx, watched):
                    row = {'signature': sig, 'observed_at': utc(), 'detected_at': entry['detected_at'],
                        'chain_block_time': chain_time, 'detection_lag_seconds': lag,
                        'sources': entry['sources'], 'early_entry_verified': False,
                        'recovered_at': recovered_at, 'classifier_version': VERSION,
                        'rpc_max_supported_transaction_version': MAX_SUPPORTED_TRANSACTION_VERSION,
                        'sample_period': ('recovered_historical' if entry.get('recovery') else
                            ('during_monitor' if isinstance(chain_time, (int, float)) and chain_time >= datetime.fromisoformat(state['started_at']).timestamp()
                             else 'before_monitor_or_unknown')), **flow}
                    emit('wallet_flow', **{k: v for k, v in row.items() if k != 'observed_at'})
                    state['recent_events'].append(row)
                    if flow['classification'] == 'buy_candidate' and not entry.get('recovery'):
                        if flow['mint'] in cfg['tokens'] and row['sample_period'] == 'during_monitor':
                            buys = state['overlap'].setdefault(flow['wallet'], [])
                            if flow['mint'] not in buys:
                                buys.append(flow['mint'])
                        if flow['wallet'] in watched and flow['mint'] not in mints and flow['mint'] not in state['tracked_new_mints']:
                            if len(state['tracked_new_mints']) < 87:
                                state['tracked_new_mints'].append(flow['mint'])
                            else:
                                emit('new_mint_tracking_limit', mint=flow['mint'])
                if entry.get('recovery'):
                    state['recovered_transaction_count'] = state.get('recovered_transaction_count', 0) + 1
                    state.setdefault('recovered_signatures', []).append(sig)
                    state['recovered_signatures'] = state['recovered_signatures'][-5000:]
                    state['unresolved_transaction_count'] = max(0, state.get('unresolved_transaction_count', 0) - 1)
                seen.add(sig)
                del state['pending'][sig]
            state['rpc_retry_after'] = 0
        except FeedError as e:
            rpc_status = 'unavailable_or_partial'
            errors.append('wallet RPC: ' + str(e))
            emit('feed_error', feed='wallet_rpc', error=str(e), retry_after_seconds=300)
            state['rpc_retry_after'] = time.time() + 300
    else:
        errors.append('wallet RPC cooling down after an error; no claim of current wallet coverage')
    previous_seen = set(state['seen'])
    state['seen'] = (state['seen'] + [s for s in sorted(seen) if s not in previous_seen])[-12000:]
    state['recent_events'] = state['recent_events'][-100:]
    status = 'OBSERVING' if rpc_status == 'connected' and markets else 'DEGRADED'
    if rpc_status == 'connected' and (len(state['pending']) > 100 or any(w.get('scan') for w in state['wallets'].values())):
        status = 'CATCHING_UP'
    if rpc_status == 'connected' and errors:
        status = 'PARTIAL_COVERAGE'
    latest = {'version': VERSION, 'updated_at': utc(), 'started_at': state['started_at'], 'status': status,
              'mode': 'WATCH_ONLY', 'run_id': os.environ.get('GITHUB_RUN_ID', 'local'),
              'rpc_status': rpc_status, 'rpc_provider': rpc.label, 'rpc_calls_this_cycle': rpc.calls,
              'pending_transactions': len(state['pending']), 'markets': markets, 'errors': sorted(set(errors)),
              'unresolved_transaction_count': state.get('unresolved_transaction_count', 0),
              'wallet_address_scans_current': rpc_status == 'connected',
              'market_mints_without_price': [m for m in cfg['tokens'] if not markets.get(m, {}).get('price_usd')],
              'seed_token_count': len(cfg['tokens']), 'wallet_lead_count': len(cfg['wallets']),
              'real_trades_placed': 0, 'verified_early_wallets': 0, 'realized_profit': None,
              'target_cycle_seconds': 60, 'complete_historical_reconstruction': False}
    log = DATA / 'events' / now[:10] / f"{os.environ.get('GITHUB_RUN_ID', 'local')}-{state['cycles']:07d}.jsonl"
    log.parent.mkdir(parents=True, exist_ok=True)
    log.write_text(''.join(json.dumps(r, ensure_ascii=True, separators=(',', ':')) + '\n' for r in rows))
    save(DATA / 'state.json', state)
    save(DATA / 'latest.json', latest)
    report(state, cfg, latest)
    print(json.dumps({k: latest[k] for k in ['updated_at', 'status', 'rpc_status', 'pending_transactions', 'seed_token_count', 'wallet_lead_count']}) + f' markets={len(markets)}', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--once', action='store_true', help='one bounded read-only cycle')
    args = parser.parse_args()
    if not args.once:
        parser.error('--once is required; the workflow controls duration and stop checks')
    run_cycle()
