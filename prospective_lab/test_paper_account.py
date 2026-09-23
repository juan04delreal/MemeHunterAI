import copy
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import paper_account as p


def quote(mint, scheduled, kind='entry', quantity=1000000, out=55000000):
    return {'status':'quote_observed','requested_epoch':scheduled+.1,'received_epoch':scheduled+.2,
        'observed_at':p.utc(scheduled+.2),'scheduled_epoch':scheduled,'timing_eligible':True,'fills_assumed':False,
        'raw':{'inputMint':p.USDC if kind=='entry' else mint,'outputMint':mint if kind=='entry' else p.USDC,
            'inAmount':'50000000' if kind=='entry' else str(quantity),'outAmount':str(quantity) if kind=='entry' else str(out),
            'otherAmountThreshold':str(quantity*99//100) if kind=='entry' else str(out*99//100),
            'contextSlot':1000,'swapMode':'ExactIn','routePlan':[{'swapInfo':{'ammKey':'pool'}}]}}


def add(source, oid='a', origin=110, delays=(30,), horizons=(), out=55000000, mint=None):
    mint = mint or 'mint'+oid
    op = {'id':oid,'mint':mint,'pool':'pool'+oid,'quote_mint':p.WSOL,
        'first_observed_epoch':origin,'actionable_epoch':origin,'future_information_used':False,
        'entry_quotes':{},'exit_quotes':{}}
    for delay in delays:
        q=quote(mint,origin+delay)
        op['entry_quotes'][str(delay)] = q
        op['exit_quotes'][str(delay)] = {str(h):quote(mint,q['received_epoch']+h,'exit',out=out) for h in horizons}
    source['opportunities'][oid]=op
    source['migration_validation'][oid]={'id':oid,'mint':mint,'pool':op['pool'],
        'status':'confirmed_new_migration','checked_at':p.utc(origin-.1),
        'historical_reaudit':False,'prospective_boundary_eligible':True}
    return op


class PaperAccountTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        (self.root/'control.json').write_text('{"enabled":true,"mode":"WATCH_ONLY"}')
        self.cfg={'mode':'WATCH_ONLY','additional_delay_seconds':[30,60,120,300],
                  'exit_horizons_seconds':[300,900,3600],'hypothetical_quote_sizes_usd':[50]}
        (self.root/'config.json').write_text(json.dumps(self.cfg))
        self.source={'schema':2,'opportunities':{},'migration_validation':{},'quote_quality_counts':{}}
        self.initial=p.run(self.source,self.root,100)
        self.path=self.root/'data/paper_accounts/accounts.sqlite3'

    def tick(self, now):return p.run(self.source,self.root,now)
    def account(self, report, name='E30_H300_C100'):
        return next(a for a in report['accounts'] if a['account_id']==name)
    def sql(self, query, params=()):
        with sqlite3.connect(self.path) as db:return db.execute(query,params).fetchall()

    def test_24_separate_500_accounts_start_without_old_trades(self):
        self.assertEqual(len(self.initial['accounts']),24)
        self.assertTrue(all(a['cash_usdc']==500 for a in self.initial['accounts']))
        self.assertEqual(self.initial['ledger_events'],0)
        self.assertEqual(self.initial['primary_account'],'E60_H900_C100')

    def test_historical_opportunity_excluded_even_with_new_exit(self):
        add(self.source,origin=10,horizons=(300,))
        r=self.tick(500);self.assertTrue(all(a['modeled_buys']==0 for a in r['accounts']))

    def test_future_quote_never_used_early(self):
        add(self.source)
        r=self.tick(130);self.assertEqual(r['ledger_events'],0)
        self.assertEqual(self.account(self.tick(150))['modeled_buys'],1)

    def test_exact_quote_quantity_and_cash_surcharge(self):
        add(self.source)
        r=self.tick(150)
        self.assertEqual(self.account(r)['cash_usdc'],449.45)
        self.assertEqual(self.account(r,'E30_H300_C300')['cash_usdc'],448.45)
        qty=self.sql('SELECT DISTINCT quantity FROM positions')
        self.assertEqual(qty,[('1000000',)])

    def test_matching_exit_net_reconciles(self):
        add(self.source,horizons=(300,))
        self.tick(150);r=self.tick(450);a=self.account(r)
        self.assertEqual(a['closed_positions'],1);self.assertEqual(a['cash_usdc'],503.85)
        self.assertEqual(a['closed_modeled_net_pnl_usdc'],3.85)
        self.assertEqual(a['open_positions'],0);self.assertTrue(r['ledger_reconciled'])

    def test_flat_prices_lose_explicit_costs(self):
        add(self.source,horizons=(300,),out=50000000)
        r=self.tick(450)
        self.assertEqual(self.account(r)['closed_modeled_net_pnl_usdc'],-1.1)
        self.assertEqual(self.account(r,'E30_H300_C300')['closed_modeled_net_pnl_usdc'],-3.1)

    def test_restart_does_not_duplicate_cash_fills_or_events(self):
        add(self.source,horizons=(300,))
        first=self.tick(450);second=self.tick(451)
        self.assertEqual(first['accounts'],second['accounts'])
        self.assertEqual(first['ledger_events'],second['ledger_events'])

    def test_five_positions_cap_preserves_skips(self):
        for i in range(7):add(self.source,oid=str(i),origin=110+i)
        a=self.account(self.tick(160))
        self.assertEqual(a['open_positions'],5);self.assertEqual(a['skip_reasons']['position_limit'],2)
        self.assertEqual(a['cash_usdc'],247.25)

    def test_no_second_open_position_in_same_mint(self):
        add(self.source,oid='a',mint='same');add(self.source,oid='b',origin=111,mint='same')
        a=self.account(self.tick(150));self.assertEqual(a['modeled_buys'],1)
        self.assertEqual(a['skip_reasons']['duplicate_open_mint'],1)

    def test_insufficient_cash_does_not_borrow(self):
        for i in range(11):add(self.source,oid=str(i),origin=110+i*400,horizons=(300,),out=1)
        a=self.account(self.tick(4600))
        self.assertGreaterEqual(a['cash_usdc'],0)
        self.assertGreater(a['skip_reasons'].get('insufficient_virtual_cash',0),0)

    def test_unconfirmed_candidate_not_admitted(self):
        add(self.source);self.source['migration_validation']['a']['status']='unresolved'
        a=self.account(self.tick(150));self.assertEqual(a['modeled_buys'],0)

    def test_future_audit_cannot_select_earlier_entry(self):
        add(self.source);self.source['migration_validation']['a']['checked_at']=p.utc(160)
        self.assertEqual(self.account(self.tick(170))['modeled_buys'],0)

    def test_later_quality_flags_do_not_delete_adverse_model_trades(self):
        add(self.source,horizons=(300,),out=1000000)
        self.tick(150);self.source['quote_quality_counts']={'requires_review':999}
        a=self.account(self.tick(450));self.assertEqual(a['losses'],1)
        self.assertEqual(a['closed_modeled_net_pnl_usdc'],-49.61)

    def test_missing_exit_locks_cash_and_position(self):
        add(self.source);self.tick(150)
        a=self.account(self.tick(520));self.assertEqual(a['unresolved_positions'],1)
        self.assertEqual(a['cash_usdc'],449.45);self.assertEqual(a['closed_positions'],0)
        self.assertIsNone(a['liquidation_equity_usdc'])

    def test_failed_exit_not_replaced_with_other_horizon(self):
        op=add(self.source,horizons=(300,900))
        op['exit_quotes']['30']['300']['status']='no_route'
        self.tick(150);a=self.account(self.tick(1100))
        self.assertEqual(a['unresolved_positions'],1);self.assertEqual(a['closed_positions'],0)
        self.assertEqual(self.account(self.tick(1101),'E30_H900_C100')['closed_positions'],1)

    def test_wrong_exit_quantity_stays_unresolved(self):
        op=add(self.source,horizons=(300,));op['exit_quotes']['30']['300']['raw']['inAmount']='999'
        a=self.account(self.tick(450));self.assertEqual(a['unresolved_positions'],1)
        self.assertEqual(a['closed_modeled_net_pnl_usdc'],0)

    def test_late_entry_not_a_fill(self):
        op=add(self.source);q=op['entry_quotes']['30'];q['requested_epoch']+=30;q['received_epoch']+=30
        self.assertEqual(self.account(self.tick(190))['modeled_buys'],0)

    def test_delayed_response_rejected_even_when_request_on_time(self):
        op=add(self.source);op['entry_quotes']['30']['received_epoch']+=30
        self.assertEqual(self.account(self.tick(190))['modeled_buys'],0)

    def test_no_quote_not_fabricated(self):
        add(self.source,delays=())
        r=self.tick(500);self.assertTrue(all(a['modeled_buys']==0 for a in r['accounts']))
        self.assertGreater(r['ledger_events'],0)

    def test_invalid_integer_shapes_rejected(self):
        for x in [True,1.5,'1e6','-1','1.1',0,2**64]:
            with self.subTest(x=x),self.assertRaises(ValueError):p.amount(x)

    def test_large_token_quantity_kept_exact(self):
        op=add(self.source);q=op['entry_quotes']['30'];q['raw']['outAmount']='18000000000000000000';q['raw']['otherAmountThreshold']='17000000000000000000'
        self.tick(150);self.assertEqual(self.sql('SELECT DISTINCT quantity FROM positions'),[('18000000000000000000',)])

    def test_mismatched_mints_rejected(self):
        op=add(self.source);op['entry_quotes']['30']['raw']['outputMint']='different'
        self.assertEqual(self.account(self.tick(150))['modeled_buys'],0)

    def test_real_fill_flag_rejected(self):
        op=add(self.source);op['entry_quotes']['30']['fills_assumed']=True
        self.assertEqual(self.account(self.tick(150))['modeled_buys'],0)

    def test_source_mutation_fails_closed_without_rewriting_ledger(self):
        op=add(self.source);first=self.tick(150);n=first['ledger_events']
        op['entry_quotes']['30']['raw']['outAmount']='222'
        with self.assertRaisesRegex(ValueError,'source_observation_changed'):self.tick(151)
        self.assertEqual(self.sql('SELECT COUNT(*) FROM events')[0][0],n)

    def test_mid_batch_failure_rolls_back_cash_and_events(self):
        add(self.source)
        original=p.record
        calls=[0]
        def broken(*args):
            original(*args);calls[0]+=1
            if calls[0]==2:raise RuntimeError('intentional_test')
        with patch.object(p,'record',side_effect=broken),self.assertRaises(RuntimeError):self.tick(150)
        self.assertEqual(self.sql('SELECT COUNT(*) FROM events')[0][0],0)
        self.assertEqual(self.account(self.tick(151))['cash_usdc'],449.45)

    def test_export_failure_after_commit_resumes_without_double_fill(self):
        add(self.source)
        with patch.object(p,'export',side_effect=OSError('test')),self.assertRaises(OSError):self.tick(150)
        self.assertEqual(self.account(self.tick(151))['modeled_buys'],1)
        self.assertEqual(self.sql("SELECT COUNT(*) FROM events WHERE account='E30_H300_C100' AND action='MODEL_BUY'")[0][0],1)

    def test_frozen_spec_cannot_silently_change(self):
        with patch.dict(p.SPEC,{'entry_input_raw':100000000}),self.assertRaisesRegex(ValueError,'spec_changed'):
            self.tick(150)

    def test_missing_database_does_not_reset_funds(self):
        self.path.unlink()
        with self.assertRaisesRegex(ValueError,'database_missing'):self.tick(150)

    def test_corrupt_cash_detected_and_not_repaired_by_reset(self):
        with sqlite3.connect(self.path) as db:db.execute("UPDATE accounts SET cash=999 WHERE id='E30_H300_C100'")
        with self.assertRaisesRegex(ValueError,'reconciliation'):self.tick(150)
        self.assertEqual(self.sql("SELECT cash FROM accounts WHERE id='E30_H300_C100'")[0][0],999)

    def test_disabled_unreadable_or_live_control_stops_before_writes(self):
        for text in ['broken','{"enabled":false,"mode":"WATCH_ONLY"}','{"enabled":true,"mode":"LIVE"}']:
            (self.root/'control.json').write_text(text)
            self.assertEqual(self.tick(150)['status'],'STOPPED')

    def test_clock_reversal_stops(self):
        self.tick(150)
        with self.assertRaisesRegex(ValueError,'clock_reversal'):self.tick(149)

    def test_out_of_order_observation_not_inserted_as_earlier_fill(self):
        add(self.source,oid='a',origin=120);self.tick(160)
        add(self.source,oid='b',origin=110)
        a=self.account(self.tick(170));self.assertEqual(a['modeled_buys'],1)
        self.assertEqual(a['skip_reasons']['out_of_order_no_retroactive_entry'],1)

    def test_source_state_and_research_files_unchanged(self):
        add(self.source);before=copy.deepcopy(self.source)
        (self.root/'data/quotes.jsonl').write_text('original\n')
        self.tick(150)
        self.assertEqual(self.source,before);self.assertEqual((self.root/'data/quotes.jsonl').read_text(),'original\n')

    def test_health_probes_are_not_experiment_events(self):
        self.source['provider_health']={'entry':quote('mint',120)}
        self.assertEqual(self.tick(150)['ledger_events'],0)

    def test_paper_layer_has_no_network_or_transaction_imports(self):
        import ast
        tree=ast.parse(Path(p.__file__).read_text())
        names=[]
        for node in ast.walk(tree):
            if isinstance(node,ast.Import):names.extend(x.name.split('.')[0] for x in node.names)
            if isinstance(node,ast.ImportFrom):names.append(node.module.split('.')[0])
        self.assertFalse(set(names)&{'socket','urllib','requests','httpx','websockets','solana','solders','ccxt','subprocess'})
        with patch('socket.socket',side_effect=AssertionError('network forbidden')):
            add(self.source,horizons=(300,));self.tick(450)

    def test_paper_error_isolated_from_collector(self):
        with patch.object(p,'run',side_effect=ValueError('sensitive-text-not-logged')):
            result=p.safe_run(self.source,self.root)
        self.assertEqual(result['status'],'error')
        self.assertNotIn('sensitive-text',json.dumps(result))
        self.assertEqual(json.loads((self.path.parent/'health.json').read_text())['status'],'error')

    def test_provisional_and_no_realized_profit_claims(self):
        add(self.source,horizons=(300,));r=self.tick(450)
        self.assertTrue(r['all_results_provisional']);self.assertIsNone(r['realized_profit'])
        self.assertEqual(r['real_trades_placed'],0);self.assertEqual(r['network_requests_by_paper_layer'],0)
        self.assertTrue(all(a['market_max_drawdown_pct'] is None for a in r['accounts']))


    def test_changed_research_settings_pause_paper_only(self):
        self.cfg['additional_delay_seconds']=[15]
        (self.root/'config.json').write_text(json.dumps(self.cfg))
        with self.assertRaisesRegex(ValueError,'research_contract_changed'):self.tick(150)
        self.assertEqual(self.sql('SELECT COUNT(*) FROM events')[0][0],0)

    def test_collector_hook_runs_without_mutating_source_or_research_output(self):
        import collector, lab
        state={'schema':2,'cycles':1,'seen':[],'opportunities':{},'errors':[]}
        before=copy.deepcopy(state)
        with patch.object(lab,'ROOT',self.root), patch.object(lab,'DATA',self.root/'data'), \
                patch.object(collector,'enabled',return_value=True), patch.object(p,'safe_run',return_value={'status':'RUNNING'}) as account:
            result=collector.publish(state,0)
        account.assert_called_once()
        self.assertEqual(state,before);self.assertEqual(result['real_trades_placed'],0)
        self.assertNotIn('modeled_buys',result)

    def test_collector_survives_paper_hook_error(self):
        import collector, lab
        state={'schema':2,'cycles':1,'seen':[],'opportunities':{},'errors':[]}
        with patch.object(lab,'ROOT',self.root), patch.object(lab,'DATA',self.root/'data'), \
                patch.object(collector,'enabled',return_value=True), patch.object(p,'safe_run',side_effect=RuntimeError('test')):
            result=collector.publish(state,0)
        self.assertEqual(result['mode'],'WATCH_ONLY')
        self.assertTrue((self.root/'data/latest.json').exists())

    def test_control_change_before_commit_rolls_back_model_buys(self):
        add(self.source)
        with patch.object(p,'active',side_effect=[True,False]):
            self.assertEqual(self.tick(150)['status'],'STOPPED')
        self.assertEqual(self.sql('SELECT COUNT(*) FROM events')[0][0],0)


if __name__=='__main__':unittest.main()
