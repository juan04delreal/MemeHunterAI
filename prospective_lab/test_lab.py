import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import lab


def b58encode(data):
    n, out = int.from_bytes(data, 'big'), ''
    while n:
        n, r = divmod(n, 58)
        out = lab.ALPHABET[r] + out
    return '1' * (len(data) - len(data.lstrip(b'\0'))) + out


def response(input_mint=lab.USDC, output_mint=lab.WSOL, amount=50_000_000):
    return {'inputMint': input_mint, 'outputMint': output_mint, 'inAmount': str(amount),
            'outAmount': '100000', 'otherAmountThreshold': '99000', 'swapMode': 'ExactIn',
            'contextSlot': 1000, 'routePlan': [{'swapInfo': {'ammKey': 'test_pool'}}]}


def opportunity(oid='one', origin=100):
    return {'id': oid, 'mint': lab.WSOL, 'actionable_epoch': origin,
            'first_observed_epoch': origin, 'first_observed_at': lab.utc(origin),
            'entry_quotes': {}, 'exit_quotes': {}, 'positions': {}}


class Tests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.patches = [patch.object(lab, 'ROOT', self.root), patch.object(lab, 'DATA', self.root / 'data'),
                        patch.dict(os.environ, {'JUPITER_API_KEY': ''})]
        for p in self.patches:
            p.start()
            self.addCleanup(p.stop)
        self.state = {'schema': 2, 'cycles': 1, 'seen': [], 'opportunities': {}}
        self.cfg = {'additional_delay_seconds': [30], 'exit_horizons_seconds': [300]}

    def test_watch_only_constants(self):
        self.assertEqual(lab.VERSION, 'prospective-quote-lab-0.3')
        self.assertEqual(lab.MIGRATE_DISC, [155, 234, 231, 146, 236, 158, 162, 30])

    def test_migration_layout(self):
        accounts = ['global', 'withdraw', 'MINT', 'curve', 'ata', 'user', 'sys', 'token', lab.PUMPSWAP, 'POOL']
        tx = {'meta': {'err': None}, 'transaction': {'message': {'instructions': [
            {'programId': lab.PUMP, 'data': b58encode(bytes(lab.MIGRATE_DISC)), 'accounts': accounts}]}}}
        migration = lab.decode_migration(tx)
        self.assertEqual(migration['mint'], 'MINT')
        self.assertEqual(migration['pool'], 'POOL')
        accounts[8] = 'wrong_program'
        self.assertIsNone(lab.decode_migration(tx))

    def test_non_migration_rejected(self):
        tx = {'meta': {'err': None}, 'transaction': {'message': {'instructions': [
            {'programId': lab.PUMP, 'data': b58encode(b'12345678'), 'accounts': ['x'] * 10}]}}}
        self.assertIsNone(lab.decode_migration(tx))

    def test_keyless_quote_uses_only_quote_get(self):
        with patch.object(lab, 'req', return_value=response()) as request:
            quote = lab.jupiter_quote(lab.USDC, lab.WSOL, 50_000_000)
        self.assertEqual(quote['status'], 'quote_observed')
        self.assertEqual(quote['access_mode'], 'keyless')
        self.assertEqual(request.call_args.kwargs['headers'], {})
        self.assertEqual(len(request.call_args.args), 1)
        self.assertTrue(request.call_args.args[0].startswith(lab.QUOTE_URL + '?'))
        self.assertNotIn('wallet', request.call_args.args[0])
        self.assertNotIn('taker', request.call_args.args[0])

    def test_existing_api_key_used_without_printing(self):
        with patch.dict(os.environ, {'JUPITER_API_KEY': 'test-only-placeholder'}), patch.object(lab, 'req', return_value=response()) as request:
            quote = lab.jupiter_quote(lab.USDC, lab.WSOL, 50_000_000)
        self.assertEqual(request.call_args.kwargs['headers'], {'x-api-key': 'test-only-placeholder'})
        self.assertNotIn('test-only-placeholder', json.dumps(quote))

    def test_invalid_responses_never_become_quotes(self):
        variants = [{}, [], {'error': 'bad'}, {**response(), 'outputMint': lab.USDC},
                    {**response(), 'inAmount': '1'}, {**response(), 'outAmount': '0'},
                    {**response(), 'contextSlot': 0}, {**response(), 'routePlan': []},
                    {**response(), 'routePlan': [{}]}, {**response(), 'otherAmountThreshold': '999999'}]
        for body in variants:
            with self.subTest(body=body), patch.object(lab, 'req', return_value=body):
                self.assertNotEqual(lab.jupiter_quote(lab.USDC, lab.WSOL, 50_000_000)['status'], 'quote_observed')

    def test_http_errors_classified_and_not_quotes(self):
        for code, status in [(401, 'auth_error'), (403, 'auth_error'), (429, 'rate_limited'), (503, 'provider_error')]:
            with self.subTest(code=code), patch.object(lab, 'req', return_value={'_error': 'http_error', 'http_status': code}):
                self.assertEqual(lab.jupiter_quote(lab.USDC, lab.WSOL, 50_000_000)['status'], status)

    def test_no_route_classified(self):
        with patch.object(lab, 'req', return_value={'errorCode': 'NO_ROUTES_FOUND'}):
            self.assertEqual(lab.jupiter_quote(lab.USDC, lab.WSOL, 50_000_000)['status'], 'no_route')

    def test_execution_endpoints_blocked_before_network(self):
        with patch.object(lab.urllib.request, 'build_opener') as network:
            for url in ['https://api.jup.ag/swap/v1/swap', 'https://api.jup.ag/swap/v2/build',
                        'https://api.jup.ag/swap/v2/order', 'https://api.jup.ag/swap/v2/execute']:
                with self.assertRaises(ValueError):
                    lab.req(url)
            for method in ['sendTransaction', 'simulateTransaction', 'requestAirdrop']:
                with self.assertRaises(ValueError):
                    lab.rpc(method, [])
            network.assert_not_called()

    def test_non_https_blocked(self):
        with self.assertRaises(ValueError):
            lab.req('http://api.jup.ag/swap/v1/quote')

    def test_invalid_amount_blocked(self):
        for amount in [0, -1, True, '50000000']:
            with self.assertRaises(ValueError):
                lab.jupiter_quote(lab.USDC, lab.WSOL, amount)

    def test_expired_deadline_not_backfilled(self):
        op = opportunity()
        self.state['opportunities']['one'] = op
        with patch.object(lab, 'req') as request:
            self.assertTrue(lab.service_due(self.state, self.cfg, 160))
            request.assert_not_called()
        self.assertEqual(op['entry_quotes']['30']['status'], 'missed_deadline')
        self.assertEqual(op['positions'], {})

    def test_historical_failures_retained(self):
        op = opportunity()
        op['entry_quotes']['30'] = {'status': 'not_configured', 'observed_at': 'old'}
        self.state['opportunities']['one'] = op
        with patch.object(lab, 'req') as request:
            self.assertFalse(lab.service_due(self.state, self.cfg, 160))
            request.assert_not_called()
        self.assertEqual(op['entry_quotes']['30']['observed_at'], 'old')

    def test_rate_limit_state_persists_across_cycles(self):
        with patch.object(lab, 'req', return_value=response()), patch.object(lab.time, 'time', return_value=130):
            lab.measured_quote(self.state, lab.USDC, lab.WSOL, 50_000_000)
        self.assertEqual(self.state['quote_next_epoch'], 132.5)
        lab.save(self.root / 'state.json', self.state)
        self.assertEqual(lab.load(self.root / 'state.json', {})['quote_next_epoch'], 132.5)

    def test_429_backoff(self):
        with patch.object(lab, 'req', return_value={'_error': 'http_error', 'http_status': 429, 'retry_after_seconds': 90}), patch.object(lab.time, 'time', return_value=100):
            lab.measured_quote(self.state, lab.USDC, lab.WSOL, 50_000_000)
        self.assertEqual(self.state['quote_next_epoch'], 190)

    def test_earliest_exit_not_starved_by_entries(self):
        early = opportunity('early', -300)
        early['entry_quotes']['30'] = {'status': 'quote_observed'}
        early['positions']['30'] = {'entry_requested_epoch': -181, 'entry_received_epoch': -180, 'token_amount_raw': '100000'}
        self.state['opportunities'] = {'one': opportunity(), 'early': early}
        self.assertEqual(lab.pending_tasks(self.state, self.cfg)[0][1], 'exit')

    def test_exit_clock_starts_at_entry_receipt(self):
        op = opportunity()
        op['entry_quotes']['30'] = {'status': 'quote_observed'}
        op['positions']['30'] = {'entry_requested_epoch': 130, 'entry_received_epoch': 135, 'token_amount_raw': '100000'}
        self.state['opportunities']['one'] = op
        self.assertEqual(lab.pending_tasks(self.state, self.cfg)[0][0], 435)

    def test_health_probe_is_not_experiment_data(self):
        with patch.object(lab, 'req', side_effect=[response(), response(lab.WSOL, lab.USDC, 100000)]), patch.object(lab.time, 'time', return_value=100):
            self.assertTrue(lab.service_probe(self.state, self.cfg, 100))
            self.state['quote_next_epoch'] = 0
            self.assertTrue(lab.service_probe(self.state, self.cfg, 103))
        latest = lab.publish_snapshot(self.state, 0)
        self.assertEqual(latest['quote_provider_health'], 'healthy')
        self.assertEqual(latest['validated_migrations'], 0)
        self.assertEqual(latest['entry_quotes_observed'], 0)
        self.assertEqual(latest['exit_quotes_observed'], 0)
        self.assertIsNone(latest['realized_profit'])
        self.assertEqual(latest['real_trades_placed'], 0)

    def test_probe_defers_to_approaching_deadline(self):
        self.state['opportunities']['one'] = opportunity()
        with patch.object(lab, 'req') as request:
            self.assertFalse(lab.service_probe(self.state, self.cfg, 125))
            request.assert_not_called()

    def test_stale_quote_context_rejected(self):
        self.state['rpc_health'] = {'slot': 2000}
        with patch.object(lab, 'req', return_value=response()):
            self.assertEqual(lab.measured_quote(self.state, lab.USDC, lab.WSOL, 50_000_000)['status'], 'stale_context')

    def test_disabled_never_contacts_network(self):
        lab.save(self.root / 'control.json', {'enabled': False, 'mode': 'WATCH_ONLY'})
        with patch.object(lab, 'req') as request:
            self.assertEqual(lab.cycle(0)['status'], 'STOPPED')
            request.assert_not_called()

    def test_unknown_schema_not_reset(self):
        lab.save(self.root / 'control.json', {'enabled': True, 'mode': 'WATCH_ONLY'})
        lab.save(self.root / 'data' / 'state.json', {'schema': 99, 'important': 'preserve'})
        with self.assertRaisesRegex(ValueError, 'history_not_reset'):
            lab.cycle(0)
        self.assertEqual(lab.load(self.root / 'data' / 'state.json', {})['important'], 'preserve')


if __name__ == '__main__':
    unittest.main()
