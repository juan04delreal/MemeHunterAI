import ast
import copy
import hashlib
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import research_audit as a

SPEC = {'starting_cash_raw':500000000,'max_open_positions':5,'fixed_cost_per_side_raw':50000}

def fixture():
    db=sqlite3.connect(':memory:')
    db.executescript('''
    CREATE TABLE meta(key TEXT PRIMARY KEY,value TEXT);
    CREATE TABLE accounts(id TEXT PRIMARY KEY,delay INTEGER,horizon INTEGER,cost_bps INTEGER,cash INTEGER);
    CREATE TABLE observations(id TEXT PRIMARY KEY,hash TEXT,observed REAL);
    CREATE TABLE positions(account TEXT,opportunity TEXT,mint TEXT,quantity TEXT,entry_cost INTEGER,entry_time REAL,due REAL,status TEXT,exit_net INTEGER,net_pnl INTEGER);
    CREATE TABLE events(sequence INTEGER PRIMARY KEY AUTOINCREMENT,account TEXT,opportunity TEXT,action TEXT,observed REAL,booked REAL,reason TEXT,delta INTEGER,cash_after INTEGER,detail TEXT);
    ''')
    db.executemany('INSERT INTO meta VALUES (?,?)',[('spec',a.canonical(SPEC)),('started','100'),('last_run','1100')])
    db.execute('INSERT INTO accounts VALUES (?,?,?,?,?)',(a.PRIMARY,60,900,100,508800000))
    op={'id':'o','mint':'mint','pool':'pool','actionable_epoch':100,'entry_quotes':{},'exit_quotes':{'60':{}}}
    for kind,when,scheduled,raw,h in [
        ('entry',160,160,{'inputMint':a.USDC,'outputMint':'mint','inAmount':'50000000','outAmount':'123'},0),
        ('exit',1060,1060,{'inputMint':'mint','outputMint':a.USDC,'inAmount':'123','outAmount':'60000000'},900)]:
        q={'status':'quote_observed','received_epoch':when,'raw':raw}
        raw['routePlan']=[{'percent':100,'swapInfo':{'ammKey':'pool',**raw}}]
        if kind=='entry':op['entry_quotes']['60']=q
        else:op['exit_quotes']['60']['900']=q
        identity=a.canonical(['o',kind,60,h])
        digest=a.fingerprint({'quote':q,'mint':'mint','pool':'pool','scheduled':float(scheduled)})
        db.execute('INSERT INTO observations VALUES (?,?,?)',(identity,digest,when))
        d={'quote_id':identity,'quote_sha256':digest,'mint':'mint','pool':'pool','quantity_raw':'123',
           'additional_cost_raw':550000 if kind=='entry' else 650000}
        d.update({'quoted_input_raw':50000000} if kind=='entry' else {'quoted_output_raw':60000000,'modeled_net_pnl_raw':8800000})
        delta=-50550000 if kind=='entry' else 59350000
        db.execute('INSERT INTO events(account,opportunity,action,observed,booked,reason,delta,cash_after,detail) VALUES (?,?,?,?,?,?,?,?,?)',
            (a.PRIMARY,'o','MODEL_BUY' if kind=='entry' else 'MODEL_SELL',when,when+2,'test',delta,449450000 if kind=='entry' else 508800000,a.canonical(d)))
    db.execute('INSERT INTO positions VALUES (?,?,?,?,?,?,?,?,?,?)',(a.PRIMARY,'o','mint','123',50550000,160,1060,'CLOSED',59350000,8800000))
    db.commit()
    return db, {'schema':2,'opportunities':{'o':op}}

class AuditTests(unittest.TestCase):
    def setUp(self):
        self.db,self.source=fixture();self.addCleanup(self.db.close)
    def result(self):return a.inspect_database(self.db,self.source)
    def test_balances_independently_reconcile(self):
        r=self.result();self.assertEqual(r['primary']['integrity_problems'],{});self.assertEqual(r['primary']['cash_usdc'],508.8)
    def test_before_after_cost_attribution(self):
        r=self.result()['primary'];self.assertEqual(r['net_modeled']['sum_usdc'],8.8);self.assertEqual(r['same_positions_before_extra_costs']['sum_usdc'],10);self.assertEqual(r['extra_costs_on_closed_positions_usdc'],1.2)
    def test_all_source_hashes_compared(self):
        r=self.result()['primary']['source_checks'];self.assertEqual(r,{'matched_saved_source_not_independent_price_verification':2})
    def test_source_change_is_flagged(self):
        self.source['opportunities']['o']['exit_quotes']['60']['900']['raw']['outAmount']='1000000000'
        self.assertEqual(self.result()['primary']['source_checks']['source_hash_mismatch'],1)
    def test_observation_hash_change_is_flagged(self):
        self.db.execute("UPDATE observations SET hash='bad'")
        self.assertEqual(self.result()['primary']['source_checks']['source_hash_mismatch'],2)
    def test_missing_source_visible(self):
        self.source['opportunities']={}
        self.assertEqual(self.result()['primary']['source_checks']['source_missing_or_malformed'],2)
    def test_wrong_intermediate_cash_detected(self):
        self.db.execute('UPDATE events SET cash_after=1 WHERE sequence=1')
        self.assertIn('cash_sequence_mismatch',self.result()['primary']['integrity_problems'])
    def test_wrong_final_balance_detected(self):
        self.db.execute('UPDATE accounts SET cash=2')
        self.assertIn('database_state_mismatch',self.result()['primary']['integrity_problems'])
    def test_wrong_exit_pnl_detected(self):
        d=json.loads(self.db.execute('SELECT detail FROM events WHERE sequence=2').fetchone()[0]);d['modeled_net_pnl_raw']=9
        self.db.execute('UPDATE events SET detail=? WHERE sequence=2',(a.canonical(d),))
        self.assertIn('exit_quantity_cost_or_pnl_mismatch',self.result()['primary']['integrity_problems'])
    def test_wrong_exit_quantity_detected(self):
        d=json.loads(self.db.execute('SELECT detail FROM events WHERE sequence=2').fetchone()[0]);d['quantity_raw']='1'
        self.db.execute('UPDATE events SET detail=? WHERE sequence=2',(a.canonical(d),))
        r=self.result()['primary'];self.assertIn('exit_quantity_cost_or_pnl_mismatch',r['integrity_problems']);self.assertIn('source_quantity_mismatch',r['source_checks'])
    def test_time_reversal_detected(self):
        self.db.execute('UPDATE events SET observed=140 WHERE sequence=2')
        self.assertIn('event_time_reversal',self.result()['primary']['integrity_problems'])
    def test_rejected_out_of_order_entry_is_not_a_fill_error(self):
        self.db.execute("INSERT INTO events(account,opportunity,action,observed,booked,reason,delta,cash_after,detail) VALUES (?,?,?,?,?,?,?,?,?)", (a.PRIMARY,'late','SKIP_ENTRY',101,1070,'out_of_order_no_retroactive_entry',0,508800000,'{}'))
        self.assertEqual(self.result()['primary']['integrity_problems'],{})
    def test_empty_returns_not_profitable(self):self.assertEqual(a.summarize_returns([]),{'count':0})
    def test_outlier_sensitivity_does_not_mutate(self):
        x=[100000000,-20000000,-10000000];r=a.summarize_returns(x)
        self.assertEqual(r['sum_usdc'],70);self.assertEqual(r['without_best_one_usdc'],-30);self.assertEqual(len(x),3)
    def test_empty_route_rejected(self):self.assertEqual(a.routes({'routePlan':[]}), 'missing_route')
    def test_consistent_serial_route_not_called_fill(self):
        q=self.source['opportunities']['o']['entry_quotes']['60']['raw'];self.assertEqual(a.routes(q),'serial_route_arithmetic_consistent_not_execution')
    def test_split_route_not_falsely_invalid(self):
        q=self.source['opportunities']['o']['entry_quotes']['60']['raw'];q['routePlan'][0]['percent']=50
        self.assertEqual(a.routes(q),'split_or_unspecified_route_unverified')
    def test_mismatched_endpoints_detected(self):
        q=self.source['opportunities']['o']['entry_quotes']['60']['raw'];q['routePlan'][0]['swapInfo']['outputMint']='other'
        self.assertEqual(a.routes(q),'serial_route_endpoint_mismatch')
    def test_fee_difference_flagged_for_review(self):
        q=self.source['opportunities']['o']['entry_quotes']['60']['raw'];q['routePlan'][0]['swapInfo']['outAmount']='122'
        self.assertEqual(a.routes(q),'serial_route_output_or_fee_difference_review')
    def test_integer_validation(self):
        for v in (True,-1,1.1,'1.0','-1',2**64,None):
            with self.subTest(v=v),self.assertRaises(ValueError):a.units(v)
    def test_nonfinite_canonical_rejected(self):
        with self.assertRaises(ValueError):a.canonical(float('nan'))
    def test_readonly_full_audit_does_not_change_database(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);d=root/'data'/'paper_accounts';d.mkdir(parents=True)
            (root/'control.json').write_text('{"enabled":true,"mode":"WATCH_ONLY"}')
            (root/'config.json').write_text('{"mode":"WATCH_ONLY"}')
            (root/'data'/'state.json').write_text(json.dumps(self.source))
            dst=sqlite3.connect(d/'accounts.sqlite3');self.db.backup(dst);dst.close()
            before=(d/'accounts.sqlite3').read_bytes()
            with patch.dict('os.environ',{},clear=True):r=a.audit(root)
            self.assertEqual(before,(d/'accounts.sqlite3').read_bytes());self.assertTrue(r['input_database_unchanged']);self.assertEqual(r['network_requests'],0)
    def test_disabled_does_not_open_database(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'control.json').write_text('{"enabled":false,"mode":"WATCH_ONLY"}')
            with patch.dict('os.environ',{},clear=True),patch.object(a.sqlite3,'connect') as connect:
                self.assertEqual(a.audit(root),{'status':'STOPPED'});connect.assert_not_called()
    def test_module_no_network_or_process_imports(self):
        tree=ast.parse(Path(a.__file__).read_text())
        forbidden={'requests','urllib','socket','subprocess','http','websocket','ccxt'}
        for node in ast.walk(tree):
            if isinstance(node,ast.Import):self.assertFalse(forbidden & {n.name.split('.')[0] for n in node.names})
            if isinstance(node,ast.ImportFrom):self.assertNotIn((node.module or '').split('.')[0],forbidden)
    def test_no_source_data_mutation(self):
        old=copy.deepcopy(self.source);self.result();self.assertEqual(self.source,old)
    def test_no_sql_insert_update_delete_in_auditor(self):
        source=Path(a.__file__).read_text();self.assertNotIn('INSERT INTO',source);self.assertNotIn('UPDATE positions',source);self.assertNotIn('DELETE FROM',source)

if __name__=='__main__':unittest.main()
