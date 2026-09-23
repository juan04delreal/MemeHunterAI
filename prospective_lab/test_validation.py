import base64
import copy
import hashlib
import json
import queue
import struct
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import Mock, patch
import lab
import collector as c
import validation as v

MINT = v.b58(bytes([2])*32)
CURVE = v.b58(bytes([3])*32)
POOL = v.b58(bytes([4])*32)
BV = v.b58(bytes([5])*32)
QV = v.b58(bytes([6])*32)
INDEX = v.b58(bytes([7])*32)


def event():
    return v.COMPLETE+bytes([1])*32+v.un58(MINT)+struct.pack('<QQQ',100000,1000,10)+v.un58(CURVE)+struct.pack('<q',100)+v.un58(POOL)+v.un58(v.WSOL)


def tx():
    accounts = [v.GLOBAL,INDEX,MINT,CURVE,BV,INDEX,v.ZERO,v.TOKEN,v.AMM,POOL]
    return {'slot':110,'blockTime':100,'transaction':{'signatures':['sig'],'message':{'accountKeys':[POOL], 'instructions':[
        {'programId':v.PUMP,'data':v.b58(v.MIGRATE),'accounts':accounts}]}},
        'meta':{'err':None,'preBalances':[0],'postBalances':[1000],'innerInstructions':[{'index':0,'instructions':[
            {'programId':v.AMM,'data':v.b58(v.CREATE_POOL+b'\0'*18),'accounts':[POOL,MINT,v.WSOL],'stackHeight':2}]}],
            'logMessages':[f'Program {v.PUMP} invoke [1]', 'Program data: '+base64.b64encode(event()).decode(),f'Program {v.PUMP} success']}}


def account(data,owner):
    return {'data':[base64.b64encode(data).decode(),'base64'],'owner':owner,'executable':False,'lamports':100}


def global_result():
    data = bytearray(145);data[:8]=hashlib.sha256(b'account:Global').digest()[:8];data[8]=1;data[113:145]=v.un58(INDEX)
    return {'context':{'slot':100},'value':account(data,v.PUMP)}


def pool_account():
    b = bytearray(261);b[:8]=hashlib.sha256(b'account:Pool').digest()[:8]
    b[43:75]=v.un58(MINT);b[75:107]=v.un58(v.WSOL);b[139:171]=v.un58(BV);b[171:203]=v.un58(QV)
    b[245:261]=(-2).to_bytes(16,'little',signed=True)
    return account(b,v.AMM)


def mint_account(decimals):
    b = bytearray(82);b[36:44]=(10000000).to_bytes(8,'little');b[44]=decimals;b[45]=1
    return account(b,v.TOKEN)


def vault(mint,amount=100000):
    b = bytearray(165);b[:32]=v.un58(mint);b[32:64]=v.un58(POOL);b[64:72]=amount.to_bytes(8,'little');b[108]=1
    return account(b,v.TOKEN)


def task():
    return {'id':'q1','opportunity':{'id':'o1','mint':MINT,'pool':POOL},'quote':{
        'status':'quote_observed','observed_at':lab.utc(),'received_epoch':time.time(),
        'raw':{'contextSlot':100,'routePlan':[{'swapInfo':{'ammKey':POOL,'inputMint':v.WSOL,'outputMint':MINT,'outAmount':'10'}}]}}}


class ValidationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for p in [patch.object(lab,'ROOT',self.root),patch.object(lab,'DATA',self.root/'data'),
                  patch.dict('os.environ',{'PROSPECTIVE_CONTROL_PATH':'','JUPITER_API_KEY':''})]:
            p.start();self.addCleanup(p.stop)
        lab.save(self.root/'control.json',{'enabled':True,'mode':'WATCH_ONLY'})
        self.state = {'schema':2,'cycles':1,'seen':[],'opportunities':{},'errors':[]}

    def test_backpressure_is_not_reported_as_rpc_disconnect(self):
        pending = {str(i):{'signature':str(i),'attempts':1,'retry_at':time.time()+1000} for i in range(c.MAX_PENDING)}
        state = {'opportunities':{},'discovery_v4':{'pending':pending,'index_address':INDEX,'index_checked_epoch':time.time()}}
        events = queue.Queue()
        rpc = Mock(return_value=123)
        with patch.object(c,'enabled',return_value=True):
            c.discovery_worker(events,state,rpc,time.monotonic()+0.1)
        rows = []
        while not events.empty():
            rows.append(events.get_nowait())
        health = next(value for kind,value in rows if kind=='rpc')
        self.assertTrue(health['connected'])
        self.assertTrue(health['discovery_page_deferred_backpressure'])
        self.assertEqual(rpc.call_count,1)

    def test_current_v2_sol_layout_supported_without_expanding_quote_universe(self):
        t=tx();i=t['transaction']['message']['instructions'][0]
        i['data']=v.b58(v.MIGRATE_V2)
        i['accounts']=[v.GLOBAL,INDEX,MINT,v.WSOL,CURVE,BV,QV,INDEX,v.ZERO,v.AMM,POOL]
        a=v.audit_migrations(t)[0]
        self.assertEqual(a['status'],'confirmed_new_migration');self.assertEqual(a['instruction_version'],'migrate_v2')
        i['accounts'][3]=lab.USDC
        self.assertEqual(v.audit_migrations(t),[])

    def test_integrated_cycle_preserves_and_resumes_unique_sample(self):
        def read(method,params):
            if method=='getSlot':return 100
            if method=='getAccountInfo':return global_result()
            if method=='getSignaturesForAddress':return [{'signature':'sig','slot':110,'err':None}]
            if method=='getTransaction':return tx()
            raise AssertionError(method)
        rpc=Mock(side_effect=read);rpc.cooldown=0;rpc.count=4;rpc.errors={}
        with patch.object(c,'ReadBudget',return_value=rpc), patch.object(lab,'service_probe',return_value=False), patch.object(lab,'VERSION',c.VERSION):
            first=c.cycle(0.01);second=c.cycle(0.01)
        self.assertEqual(first['validated_migrations'],1);self.assertEqual(second['validated_migrations'],1)
        saved=lab.load(lab.DATA/'state.json',{})
        self.assertEqual(len(saved['opportunities']),1);self.assertEqual(saved['cycles'],2)
        self.assertEqual(first['entry_quotes_observed'],0)

    def test_event_layout_round_trip_and_truncation(self):
        a=v.decode_event(event());self.assertEqual((a['mint'],a['pool'],a['mint_amount_raw']),(MINT,POOL,'100000'))
        self.assertIsNotNone(v.decode_event(event()[:168]))
        self.assertIsNone(v.decode_event(event()[:160]))

    def test_actual_migration_requires_event_and_pool_creation(self):
        self.assertEqual(v.audit_migrations(tx())[0]['status'],'confirmed_new_migration')
        for field in ['logMessages','innerInstructions']:
            t=tx();t['meta'][field]=[]
            self.assertNotEqual(v.audit_migrations(t)[0]['status'],'confirmed_new_migration')

    def test_successful_noop_is_not_new_migration(self):
        t=tx();t['meta']['logMessages']=[];t['meta']['innerInstructions']=[]
        self.assertEqual(v.audit_migrations(t)[0]['status'],'unresolved_no_new_migration_evidence')

    def test_event_from_other_program_rejected(self):
        t=tx();t['meta']['logMessages']=[f'Program {INDEX} invoke [1]','Program data: '+base64.b64encode(event()).decode(),f'Program {INDEX} success']
        self.assertNotEqual(v.audit_migrations(t)[0]['status'],'confirmed_new_migration')

    def test_log_text_spoof_does_not_create_authority(self):
        t=tx();t['meta']['logMessages']=[f'Program log: Program {v.PUMP} invoke [1]','Program data: '+base64.b64encode(event()).decode()]
        self.assertNotEqual(v.audit_migrations(t)[0]['status'],'confirmed_new_migration')

    def test_nested_other_program_log_is_not_pump_event(self):
        t=tx();t['meta']['logMessages']=[f'Program {v.PUMP} invoke [1]',f'Program {INDEX} invoke [2]',
            'Program data: '+base64.b64encode(event()).decode(),f'Program {INDEX} success',f'Program {v.PUMP} success']
        self.assertNotEqual(v.audit_migrations(t)[0]['status'],'confirmed_new_migration')

    def test_anchor_self_cpi_event_accepted(self):
        t=tx();t['meta']['logMessages']=[]
        t['meta']['innerInstructions'][0]['instructions'].append({'programId':v.PUMP,'stackHeight':2,'data':v.b58(v.EVENT_CPI+event())})
        self.assertEqual(v.audit_migrations(t)[0]['status'],'confirmed_new_migration')
        t['meta']['innerInstructions'][0]['instructions'][-1]['stackHeight']=3
        self.assertNotEqual(v.audit_migrations(t)[0]['status'],'confirmed_new_migration')

    def test_wrong_mint_pool_or_failed_tx_rejected(self):
        for offset in (40,136):
            t=tx();b=bytearray(event());b[offset]=99
            t['meta']['logMessages'][1]='Program data: '+base64.b64encode(b).decode()
            self.assertNotEqual(v.audit_migrations(t)[0]['status'],'confirmed_new_migration')
        t=tx();t['meta']['err']={'InstructionError':[0,'error']}
        self.assertEqual(v.audit_migrations(t),[])

    def test_zero_migration_liquidity_not_confirmed(self):
        t=tx();b=bytearray(event());b[72:80]=b'\0'*8
        t['meta']['logMessages'][1]='Program data: '+base64.b64encode(b).decode()
        self.assertNotEqual(v.audit_migrations(t)[0]['status'],'confirmed_new_migration')

    def test_pool_creation_from_different_top_level_not_enough(self):
        t=tx();t['meta']['innerInstructions'][0]['index']=1
        self.assertNotEqual(v.audit_migrations(t)[0]['status'],'confirmed_new_migration')

    def test_prefunded_or_rolled_back_pool_not_claimed_new(self):
        for before,after in [(1,1000),(0,0),(None,1000)]:
            t=tx();t['meta']['preBalances']=[before];t['meta']['postBalances']=[after]
            self.assertNotEqual(v.audit_migrations(t)[0]['status'],'confirmed_new_migration')

    def test_index_from_current_owned_global_only(self):
        self.assertEqual(v.migration_index(global_result()),INDEX)
        r=global_result();r['value']['owner']=INDEX
        with self.assertRaises(ValueError):v.migration_index(r)
        r=global_result();r['value']['executable']=True
        with self.assertRaises(ValueError):v.migration_index(r)
        with self.assertRaises(ValueError):v.migration_index(None)

    def test_pool_offsets_and_signed_virtual_reserve(self):
        p=v.pool_layout(pool_account())
        self.assertEqual((p['base_mint'],p['quote_mint'],p['base_vault'],p['quote_vault']),(MINT,v.WSOL,BV,QV))
        self.assertEqual(p['virtual_quote_reserves_raw'],'-2')

    def test_mint_decimals_and_supply_use_raw_integer(self):
        m=v.mint_layout(mint_account(6));self.assertEqual(m['decimals'],6);self.assertEqual(m['supply_raw'],'10000000')

    def test_extension_token_never_claimed_fully_checked(self):
        a=mint_account(6);a['owner']=v.TOKEN22
        self.assertFalse(v.mint_layout(a)['extensions_fully_validated'])

    def test_vault_mint_and_authority_are_checked(self):
        self.assertEqual(v.vault_layout(vault(MINT),MINT,POOL)['amount_raw'],'100000')
        with self.assertRaises(ValueError):v.vault_layout(vault(INDEX),MINT,POOL)
        with self.assertRaises(ValueError):v.vault_layout(vault(MINT),MINT,INDEX)

    def test_cursor_backpressure_does_not_advance_or_drop(self):
        d={'pending':{str(i):{} for i in range(c.MAX_PENDING)},'cursors':{INDEX:{'anchor':'original'}}}
        rpc=Mock();c.poll_page(d,rpc,INDEX,100)
        rpc.assert_not_called();self.assertEqual(d['cursors'][INDEX]['anchor'],'original');self.assertEqual(len(d['pending']),c.MAX_PENDING)

    def test_pagination_retains_all_pages_across_restart(self):
        d={'cursors':{INDEX:{'anchor':'old'}}}
        page=[{'signature':str(i),'slot':200-i,'err':None} for i in range(c.PAGE)]
        c.poll_page(d,Mock(return_value=page),INDEX,100)
        self.assertEqual(d['cursors'][INDEX]['before'],'99');self.assertEqual(d['cursors'][INDEX]['anchor'],'old')
        d=json.loads(json.dumps(d));rpc=Mock(return_value=[{'signature':'last','slot':50}])
        c.poll_page(d,rpc,INDEX,110)
        self.assertEqual(rpc.call_args.args[1][1]['before'],'99')
        self.assertEqual(rpc.call_args.args[1][1]['until'],'old')
        self.assertEqual(len(d['pending']),101);self.assertEqual(d['cursors'][INDEX]['anchor'],'0')
        self.assertNotIn('before',d['cursors'][INDEX])

    def test_failed_page_preserves_cursor_and_queue(self):
        d={'cursors':{INDEX:{'anchor':'old','before':'page2'}},'pending':{'a':{}}};before=copy.deepcopy(d)
        c.poll_page(d,Mock(return_value=None),INDEX,100)
        self.assertEqual(d['cursors'],before['cursors']);self.assertEqual(d['pending'],before['pending'])

    def test_bootstrap_does_not_claim_historical_coverage(self):
        d={};c.poll_page(d,Mock(return_value=[{'signature':'one','slot':20}]),INDEX,100)
        self.assertTrue(d['cursors'][INDEX]['bootstrap_history_incomplete'])

    def test_duplicate_page_is_not_double_queued(self):
        d={};rpc=Mock(return_value=[{'signature':'one','slot':20}]);c.poll_page(d,rpc,INDEX,100);c.poll_page(d,rpc,INDEX,110)
        self.assertEqual(len(d['pending']),1)

    def test_http429_honored_and_no_rpc_secret_logged(self):
        with patch.object(lab,'req',return_value={'_error':'http_error','http_status':429,'retry_after_seconds':120}) as req:
            rpc=c.ReadBudget(time.monotonic()+30)
            self.assertIsNone(rpc('getSlot',[]));self.assertGreater(rpc.cooldown,time.time()+110)
            self.assertIsNone(rpc('getSlot',[]));self.assertEqual(req.call_count,1)

    def test_budget_and_unsafe_methods_never_contact_network(self):
        rpc=c.ReadBudget(time.monotonic()+30);rpc.count=c.MAX_RPC
        with patch.object(lab,'req') as req:
            self.assertIsNone(rpc('getSlot',[]))
            for method in ['sendTransaction','simulateTransaction','requestAirdrop','build','sign']:
                with self.assertRaises(ValueError):rpc(method,[])
            req.assert_not_called()

    def test_new_runner_disabled_or_unreadable_control_fail_closed(self):
        for content in ['{"enabled":false,"mode":"WATCH_ONLY"}','not-json','{"enabled":true,"mode":"LIVE"}']:
            (self.root/'control.json').write_text(content)
            with patch.object(lab,'req') as req:
                self.assertEqual(c.cycle(0)['status'],'STOPPED');req.assert_not_called()

    def test_new_runner_unknown_schema_not_reset(self):
        lab.save(lab.DATA/'state.json',{'schema':99,'important':'keep'})
        with self.assertRaisesRegex(ValueError,'history_not_reset'):c.cycle(0)
        self.assertEqual(lab.load(lab.DATA/'state.json',{})['important'],'keep')

    def test_unresolved_and_historical_reaudit_never_create_quotes(self):
        a={**v.audit_migrations(tx())[0],'id':'audit','signature':'sig','historical_reaudit':True,'prospective_boundary_eligible':True}
        self.assertEqual(c.accept_audit(self.state,a),0);self.assertEqual(self.state['opportunities'],{})
        a={**a,'id':'two','historical_reaudit':False,'status':'unresolved'}
        self.assertEqual(c.accept_audit(self.state,a),0)

    def test_duplicate_pool_never_creates_second_sample(self):
        a={**v.audit_migrations(tx())[0],'id':'audit','signature':'sig','historical_reaudit':False,'prospective_boundary_eligible':True}
        self.assertEqual(c.accept_audit(self.state,a),1)
        self.assertEqual(c.accept_audit(self.state,{**a,'id':'second'}),0)
        self.assertEqual(len(self.state['opportunities']),1)

    def test_original_failures_and_quoted_amounts_not_mutated_by_audit(self):
        old={'id':'old','signature':'sig','mint':MINT,'pool':POOL,'entry_quotes':{'30':{'status':'not_configured'}},'exit_quotes':{}}
        self.state['opportunities']['old']=copy.deepcopy(old)
        a={**v.audit_migrations(tx())[0],'id':'old','signature':'sig','historical_reaudit':True}
        c.accept_audit(self.state,a);self.assertEqual(self.state['opportunities']['old'],old)

    def test_expired_snapshot_not_replaced_by_current_balances(self):
        t=task();t['quote']['received_epoch']=time.time()-100
        rpc=Mock();r=c.pool_check(t,rpc);rpc.assert_not_called();self.assertEqual(r['status'],'missed_snapshot_window_no_backfill')

    def test_pool_evidence_not_execution_or_full_validation(self):
        t=task();snapshot={'context':{'slot':101},'value':[pool_account(),mint_account(6),mint_account(9),vault(MINT),vault(v.WSOL)]}
        rpc=Mock(side_effect=[{'value':pool_account()},snapshot]);r=c.pool_check(t,rpc)
        self.assertEqual(r['status'],'pool_state_corroborated');self.assertFalse(r['fully_validated_quote']);self.assertFalse(r['fills_assumed'])
        self.assertEqual(r['effective_quote_reserves_raw'],'99998')
        self.assertEqual(rpc.call_args.args[1][1]['minContextSlot'],100)

    def test_later_balance_disagreement_is_flag_not_deleted_quote(self):
        t=task();original=copy.deepcopy(t)
        snapshot={'context':{'slot':101},'value':[pool_account(),mint_account(6),mint_account(9),vault(MINT,1),vault(v.WSOL)]}
        r=c.pool_check(t,Mock(side_effect=[{'value':pool_account()},snapshot]))
        self.assertEqual(r['status'],'requires_review');self.assertIn('pool_leg_exceeds_later_observed_vault',r['flags']);self.assertEqual(t,original)

    def test_report_does_not_count_raw_instruction_as_confirmed(self):
        self.state['opportunities']['old']={'id':'old','mint':MINT,'pool':POOL,'first_observed_epoch':100,'first_observed_at':'old','entry_quotes':{},'exit_quotes':{}}
        out=c.publish(self.state,0)
        self.assertEqual(out['validated_migrations'],0);self.assertEqual(out['legacy_instruction_matches'],1)
        self.assertIsNone(out['independent_coverage_fraction']);self.assertIsNone(out['realized_profit']);self.assertEqual(out['real_trades_placed'],0)

    def test_failed_transaction_is_retained_for_later_retry(self):
        state=copy.deepcopy(self.state);state['discovery_v4']={'index_address':INDEX,'index_checked_epoch':time.time(),
            'pending':{'sig':{'signature':'sig','slot':110,'first_seen_epoch':time.time(),'attempts':0,'retry_at':0}}}
        responses=[100,[],None];rpc=Mock(side_effect=responses);events=queue.Queue()
        c.discovery_worker(events,state,rpc,time.monotonic()+30)
        rows=[]
        while not events.empty():rows.append(events.get())
        d=[val for typ,val in rows if typ=='discovery_state'][0]
        self.assertEqual(d['pending']['sig']['attempts'],1);self.assertGreater(d['pending']['sig']['retry_at'],time.time())


if __name__=='__main__':unittest.main()
