import ast
import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import confirmation_pilot as c

M='mint';P='pool'

def quote(kind='entry',when=400,out=10000,quantity=50000000):
    im,om=(c.USDC,M) if kind=='entry' else (M,c.USDC)
    return {'status':'quote_observed','requested_epoch':when,'received_epoch':when+.1,'scheduled_epoch':when,
        'timing_eligible':True,'fills_assumed':False,'raw':{'inputMint':im,'outputMint':om,'swapMode':'ExactIn',
        'inAmount':str(quantity),'outAmount':str(out),'otherAmountThreshold':str(out*99//100),'contextSlot':100,
        'routePlan':[{'percent':100,'swapInfo':{'ammKey':'conversion','inputMint':c.USDC,'outputMint':c.WSOL,'inAmount':str(quantity),'outAmount':'400000000'}},
                     {'percent':100,'swapInfo':{'ammKey':P,'inputMint':c.WSOL,'outputMint':M,'inAmount':'400000000','outAmount':str(out)}}]}}

def opportunity(oid='o',origin=100):
    return {'id':oid,'mint':M,'pool':P,'quote_mint':c.WSOL,'actionable_epoch':origin,'first_observed_epoch':origin,
            'chain_block_time':origin-2,'future_information_used':False,'entry_quotes':{'60':quote(when=origin+60,out=11000),
            '120':quote(when=origin+120,out=10000),'300':quote(when=origin+300,out=9000)},'exit_quotes':{}}

def source(op=None):
    op=op or opportunity()
    return {'schema':2,'opportunities':{op['id']:op},'migration_validation':{op['id']:{'status':'confirmed_new_migration',
            'historical_reaudit':False,'prospective_boundary_eligible':True,'mint':M,'pool':P,'checked_at':c.utc(op['actionable_epoch'])}}}

def snapshot(op,delay):
    when=op['actionable_epoch']+delay+.5
    return {'id':f"{op['id']}:entry:{delay}:",'opportunity_id':op['id'],'status':'requires_review',
       'flags':['token_extensions_not_fully_validated'],'checked_at':c.utc(when),
       'quote_observed_at':c.utc(op['actionable_epoch']+delay+.1),
       'pool':{'base_mint':M,'quote_mint':c.WSOL},'mint':{'freeze_authority_present':False,'extensions_fully_validated':False},
       'quote_vault':{'amount_raw':'100000000000'},'base_vault':{'amount_raw':'10000000'},'source_row_sha256':'test_hash'}

class ConfirmationTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
        (self.root/'control.json').write_text('{"enabled":true,"mode":"WATCH_ONLY"}')
        (self.root/'config.json').write_text('{"mode":"WATCH_ONLY"}')
        self.op=opportunity();self.src=source(self.op);self.state=c.initialize(90)
        self.state['quality']={f'o:entry:{d}:':snapshot(self.op,d) for d in (60,120)}
    def entry(self):
        return c.event_stream(self.src,90,400.2)[0]
    def gate(self):return c.confirmation_gate(self.op,self.state['quality'],400)
    def buy(self):c.consume(self.state,self.src,self.entry(),400.2)
    def exit(self,out=60000000):
        self.op['exit_quotes']={'300':{'300':quote('exit',700.1,out,9000)}}
        e=[e for e in c.event_stream(self.src,90,700.3) if e[1]==0][0]
        c.consume(self.state,self.src,e,700.3)
    def test_initial_four_alternatives_and_cash_benchmark(self):
        r=c.report(self.state,90);self.assertEqual(len(r['accounts']),4);self.assertEqual(r['cash_benchmark_usdc'],500)
        self.assertEqual(r['primary']['cash_usdc'],500);self.assertEqual(r['primary']['modeled_buys'],0)
    def test_confirmation_requires_only_pre_entry_data(self):
        reason,evidence=self.gate();self.assertIsNone(reason);self.assertEqual(evidence['price_ratio_bps'],11000)
        self.assertFalse(evidence['token_extensions_fully_validated'])
    def test_snapshot_after_decision_rejected(self):
        self.state['quality']['o:entry:120:']['checked_at']=c.utc(401)
        self.assertEqual(self.gate()[0],'prior_snapshot_missing_or_future')
    def test_future_prior_quote_rejected(self):
        self.op['entry_quotes']['120']['received_epoch']=401
        self.assertIsNotNone(self.gate()[0])
    def test_missing_snapshot_rejected(self):
        self.state['quality'].pop('o:entry:60:');self.assertEqual(self.gate()[0],'prior_snapshot_missing_or_future')
    def test_unrecognized_snapshot_not_silently_accepted(self):
        self.state['quality']['o:entry:120:']['status']='unrecognized_or_inconsistent_pool_evidence'
        self.assertEqual(self.gate()[0],'prior_snapshot_quality_flag')
    def test_adverse_reserve_flag_rejected(self):
        self.state['quality']['o:entry:120:']['flags'].append('pool_leg_exceeds_later_observed_vault')
        self.assertEqual(self.gate()[0],'prior_snapshot_quality_flag')
    def test_freeze_authority_rejected(self):
        self.state['quality']['o:entry:120:']['mint']['freeze_authority_present']=True
        self.assertEqual(self.gate()[0],'snapshot_identity_timing_or_freeze')
    def test_other_pool_identity_rejected(self):
        self.state['quality']['o:entry:120:']['pool']['base_mint']='other'
        self.assertIsNotNone(self.gate()[0])
    def test_wrong_snapshot_quote_time_rejected(self):
        self.state['quality']['o:entry:120:']['quote_observed_at']=c.utc(110)
        self.assertIsNotNone(self.gate()[0])
    def test_thin_reserve_rejected(self):
        self.state['quality']['o:entry:120:']['quote_vault']['amount_raw']='1000000000'
        self.assertEqual(self.gate()[0],'thin_quote_reserve')
    def test_deteriorating_reserve_rejected(self):
        self.state['quality']['o:entry:120:']['quote_vault']['amount_raw']='80000000000'
        self.assertEqual(self.gate()[0],'quote_reserve_deterioration')
    def test_large_entry_relative_to_inventory_rejected(self):
        self.state['quality']['o:entry:120:']['base_vault']['amount_raw']='100000'
        self.assertEqual(self.gate()[0],'entry_large_relative_to_inventory')
    def test_chasing_large_move_rejected(self):
        self.op['entry_quotes']['60']['raw']['outAmount']='15000'
        self.op['entry_quotes']['60']['raw']['routePlan'][-1]['swapInfo']['outAmount']='15000'
        self.assertEqual(self.gate()[0],'no_moderate_price_confirmation')
    def test_falling_quote_implied_price_rejected(self):
        self.op['entry_quotes']['60']['raw']['outAmount']='9000'
        self.op['entry_quotes']['60']['raw']['otherAmountThreshold']='8910'
        self.op['entry_quotes']['60']['raw']['routePlan'][-1]['swapInfo']['outAmount']='9000'
        self.assertEqual(self.gate()[0],'no_moderate_price_confirmation')
    def test_delayed_discovery_rejected(self):
        self.op['chain_block_time']=1;self.assertEqual(self.gate()[0],'late_or_unknown_discovery')
    def test_no_future_migration_admission(self):
        self.src['migration_validation']['o']['checked_at']=c.utc(401)
        self.buy();self.assertTrue(all(not x['positions'] for x in self.state['accounts'].values()))
    def test_historical_reaudit_not_admitted(self):
        self.src['migration_validation']['o']['historical_reaudit']=True
        self.buy();self.assertEqual(self.state['accounts']['BASELINE_C100']['positions'],{})
    def test_exact_quantity_and_stress_costs(self):
        self.buy();p=self.state['accounts']['CONFIRM_C100']['positions']['o']
        self.assertEqual(p['quantity_raw'],'9000');self.assertEqual(self.state['accounts']['CONFIRM_C100']['cash'],449450000)
        self.exit();c.reconcile(self.state)
        self.assertEqual(self.state['accounts']['CONFIRM_C100']['cash'],508800000)
        self.assertEqual(self.state['accounts']['CONFIRM_C100']['positions']['o']['net_pnl_raw'],8800000)
    def test_filtered_and_baseline_not_pooled(self):
        self.state['quality']={};self.buy()
        self.assertEqual(len(self.state['accounts']['BASELINE_C100']['positions']),1)
        self.assertEqual(len(self.state['accounts']['CONFIRM_C100']['positions']),0)
    def test_no_duplicate_processing(self):
        self.buy();before=copy.deepcopy(self.state);self.buy();self.assertEqual(self.state,before)
    def test_changed_source_fails_closed(self):
        self.buy();self.op['entry_quotes']['300']['raw']['outAmount']='1'
        with self.assertRaisesRegex(ValueError,'source_changed'):self.buy()
    def test_bad_exit_quantity_unresolved(self):
        self.buy();self.op['exit_quotes']={'300':{'300':quote('exit',700.1,60000000,1)}}
        e=[e for e in c.event_stream(self.src,90,700.3) if e[1]==0][0];c.consume(self.state,self.src,e,700.3)
        self.assertEqual(self.state['accounts']['CONFIRM_C100']['positions']['o']['status'],'UNRESOLVED')
        self.assertEqual(self.state['accounts']['CONFIRM_C100']['cash'],449450000)
    def test_absent_exit_locks_capital(self):
        self.buy();e=[e for e in c.event_stream(self.src,90,800) if e[1]==0][0];c.consume(self.state,self.src,e,800)
        self.assertEqual(self.state['accounts']['CONFIRM_C100']['positions']['o']['status'],'UNRESOLVED')
    def test_no_trade_from_old_opportunity(self):self.assertEqual(c.event_stream(self.src,101,1000),[])
    def test_future_quote_not_used(self):self.assertEqual(c.event_stream(self.src,90,399),[])
    def test_entry_validation_late_quote(self):
        self.op['entry_quotes']['300']['received_epoch']=427
        e=c.event_stream(self.src,90,430)[0];c.consume(self.state,self.src,e,430)
        self.assertEqual(self.state['accounts']['BASELINE_C100']['positions'],{})
    def test_live_fill_flag_rejected(self):
        self.op['entry_quotes']['300']['fills_assumed']=True;self.buy()
        self.assertEqual(self.state['accounts']['BASELINE_C100']['positions'],{})
    def test_frozen_spec_mismatch_rejected(self):
        self.state['spec']['max_open']=100
        with self.assertRaises(ValueError):c.reconcile(self.state)
    def test_account_parameter_change_rejected(self):
        self.state['accounts']['BASELINE_C100']['cost_bps']=1
        with self.assertRaises(ValueError):c.reconcile(self.state)
    def test_negative_or_wrong_cash_rejected(self):
        self.state['accounts']['BASELINE_C100']['cash']=-1
        with self.assertRaises(ValueError):c.reconcile(self.state)
    def test_source_never_mutated(self):
        before=copy.deepcopy(self.src);self.buy();self.assertEqual(self.src,before)
    def test_bootstrap_excludes_old_data_and_restart_preserves_start(self):
        first=c.run(self.src,self.root,now=500);second=c.run(self.src,self.root,now=501)
        self.assertEqual(first['started_at'],second['started_at']);self.assertEqual(second['primary']['modeled_buys'],0)
    def test_missing_state_cannot_reset_cash(self):
        c.run(self.src,self.root,now=500);(self.root/'data/confirmation_pilot/state.json').unlink()
        with self.assertRaisesRegex(ValueError,'missing_state'):c.run(self.src,self.root,now=501)
    def test_disabled_does_not_create_directory(self):
        (self.root/'control.json').write_text('{"enabled":false,"mode":"WATCH_ONLY"}')
        self.assertEqual(c.run(self.src,self.root,now=500),{'status':'STOPPED'});self.assertFalse((self.root/'data').exists())
    def test_bad_control_fails_closed(self):
        (self.root/'control.json').write_text('bad')
        self.assertEqual(c.run(self.src,self.root,now=500),{'status':'STOPPED'})
    def test_quality_ingestion_only_post_start_relevant_rows(self):
        self.state['quality']={}
        path=self.root/'quality.jsonl';row=snapshot(self.op,120);path.write_text(json.dumps(row)+'\n')
        self.assertTrue(c.ingest_quality(self.state,path,self.src));self.assertIn('o:entry:120:',self.state['quality'])
        self.assertEqual(self.state['quality_offset'],path.stat().st_size)
    def test_quality_ingestion_restart_no_double_change(self):
        self.state['quality']={}
        path=self.root/'quality.jsonl';path.write_text(json.dumps(snapshot(self.op,120))+'\n')
        c.ingest_quality(self.state,path,self.src);old=copy.deepcopy(self.state);c.ingest_quality(self.state,path,self.src)
        self.assertEqual(self.state,old)
    def test_quality_file_truncation_not_silent(self):
        path=self.root/'quality.jsonl';path.write_text('{}\n');self.state['quality_offset']=10
        with self.assertRaisesRegex(ValueError,'truncated'):c.ingest_quality(self.state,path,self.src)
    def test_empty_quality_path_is_allowed_not_validation(self):
        self.assertTrue(c.ingest_quality(self.state,self.root/'absent',self.src))
    def test_clock_reversal_does_not_change_saved_state(self):
        c.run(self.src,self.root,now=500);path=self.root/'data/confirmation_pilot/state.json';before=path.read_bytes()
        with self.assertRaisesRegex(ValueError,'clock'):c.run(self.src,self.root,now=499)
        self.assertEqual(path.read_bytes(),before)
    def test_original_files_unchanged(self):
        d=self.root/'data/paper_accounts';d.mkdir(parents=True);(d/'accounts.sqlite3').write_bytes(b'original')
        (self.root/'data/state.json').write_text('original research')
        c.run(self.src,self.root,now=500)
        self.assertEqual((d/'accounts.sqlite3').read_bytes(),b'original');self.assertEqual((self.root/'data/state.json').read_text(),'original research')
    def test_module_has_no_network_or_transaction_calls(self):
        tree=ast.parse(Path(c.__file__).read_text());forbidden={'requests','urllib','socket','subprocess','http','websocket','ccxt'}
        for n in ast.walk(tree):
            if isinstance(n,ast.Import):self.assertFalse(forbidden & {a.name.split('.')[0] for a in n.names})
            if isinstance(n,ast.ImportFrom):self.assertNotIn((n.module or '').split('.')[0],forbidden)
    def test_zero_trades_not_described_as_profitable(self):
        r=c.report(self.state,90);self.assertTrue(r['all_results_provisional']);self.assertEqual(r['fully_validated_fills'],0)
        self.assertIsNone(r['realized_profit']);self.assertEqual(r['primary']['closed'],0)
    def test_closed_loss_pause_persists_and_existing_positions_can_exit(self):
        for i in range(3):
            op=opportunity(f'o{i}',100+i*1000);op['mint']=f'mint{i}'
            # Return to a single mint in sequentially closed positions; no simultaneous duplicates.
            op['mint']=M;src=source(op)
            stateq={f"{op['id']}:entry:{d}:":snapshot(op,d) for d in (60,120)};self.state['quality'].update(stateq)
            e=c.event_stream(src,90,op['actionable_epoch']+300.2)[0];c.consume(self.state,src,e,e[0]+.1)
            op['exit_quotes']={'300':{'300':quote('exit',op['actionable_epoch']+600.1,1,9000)}}
            e=[e for e in c.event_stream(src,90,op['actionable_epoch']+601) if e[1]==0][0]
            c.consume(self.state,src,e,e[0]+.1)
        a=self.state['accounts']['CONFIRM_C100'];self.assertTrue(a['halted']);self.assertEqual(len(a['positions']),2)
        c.reconcile(self.state)
    def test_three_open_cap_and_duplicate_mint(self):
        self.buy()
        for i in range(1,5):
            op=opportunity(f'x{i}',100+i);src=source(op)
            e=c.event_stream(src,90,op['actionable_epoch']+300.2)[0];c.consume(self.state,src,e,e[0]+.1)
        reasons=[e['reason'] for e in self.state['events'] if e['account']=='BASELINE_C100']
        self.assertIn('duplicate_open_mint',reasons)
        self.assertEqual(len(self.state['accounts']['BASELINE_C100']['positions']),1)

    def test_three_distinct_open_positions_are_cap(self):
        for i in range(5):
            op=opportunity(f'd{i}',100+i);mint=f'mint{i}';op['mint']=mint
            for q in op['entry_quotes'].values():
                q['raw']['outputMint']=mint;q['raw']['routePlan'][-1]['swapInfo']['outputMint']=mint
            src=source(op);src['migration_validation'][op['id']]['mint']=mint
            for d in (60,120):
                snap=snapshot(op,d);snap['pool']['base_mint']=mint
                self.state['quality'][snap['id']]=snap
            e=c.event_stream(src,90,op['actionable_epoch']+301)[0];c.consume(self.state,src,e,e[0]+.2)
        for a in self.state['accounts'].values():self.assertEqual(len(a['positions']),3)
        self.assertIn('position_limit',[e['reason'] for e in self.state['events']]);c.reconcile(self.state)

    def test_end_to_end_new_only_start_buy_exit_restart(self):
        c.run({'schema':2,'opportunities':{}},self.root,now=90)
        qfile=self.root/'data'/'quote_quality.jsonl'
        qfile.write_text(''.join(json.dumps(snapshot(self.op,d))+'\n' for d in (60,120)))
        before=copy.deepcopy(self.src);r=c.run(self.src,self.root,now=400.2)
        self.assertEqual(r['primary']['open'],1);self.assertEqual(r['primary']['cash_usdc'],449.45)
        self.assertEqual(self.src,before)
        self.op['exit_quotes']={'300':{'300':quote('exit',700.1,60000000,9000)}}
        r=c.run(self.src,self.root,now=701);r2=c.run(self.src,self.root,now=702)
        self.assertEqual(r['primary'],r2['primary']);self.assertEqual(r2['primary']['cash_usdc'],508.8)
        self.assertEqual(r2['primary']['closed'],1)

    def test_control_change_before_commit_does_not_write(self):
        with patch.object(c,'active',side_effect=[True,False]):
            result=c.run(self.src,self.root,now=90)
        self.assertEqual(result['status'],'STOPPED');self.assertFalse((self.root/'data').exists())

    def test_mid_batch_error_keeps_old_checkpoint(self):
        c.run({'schema':2,'opportunities':{}},self.root,now=90)
        path=self.root/'data/confirmation_pilot/state.json';old=path.read_bytes()
        with patch.object(c,'consume',side_effect=ValueError('test')):
            with self.assertRaises(ValueError):c.run(self.src,self.root,now=400.2)
        self.assertEqual(path.read_bytes(),old)

    def test_failed_export_restarts_without_duplicate_buy(self):
        c.run({'schema':2,'opportunities':{}},self.root,now=90)
        qfile=self.root/'data'/'quote_quality.jsonl';qfile.write_text(''.join(json.dumps(snapshot(self.op,d))+'\n' for d in (60,120)))
        original=c.atomic
        def fail(path,value):
            if path.name=='latest.json':raise OSError('test')
            return original(path,value)
        with patch.object(c,'atomic',side_effect=fail):
            with self.assertRaises(OSError):c.run(self.src,self.root,now=400.2)
        result=c.run(self.src,self.root,now=401)
        self.assertEqual(result['primary']['modeled_buys'],1);self.assertEqual(result['primary']['cash_usdc'],449.45)

    def test_ingestion_backlog_advances_without_modeling_early(self):
        c.run({'schema':2,'opportunities':{}},self.root,now=90)
        path=self.root/'data/quote_quality.jsonl'
        path.write_text((json.dumps({'id':'irrelevant','padding':'x'*100000})+'\n')*21)
        first=c.run(self.src,self.root,now=400.2)
        self.assertFalse(first['quality_ingestion_caught_up']);self.assertEqual(first['primary']['modeled_buys'],0)
        second=c.run(self.src,self.root,now=401)
        self.assertTrue(second['quality_ingestion_caught_up'])

if __name__=='__main__':unittest.main()
