"""Offline regressions for expired-audit starvation and snapshot-copy overhead."""
import copy
import json
import queue
import unittest
from unittest.mock import Mock, patch
import collector as c
import lab


def task(identity, received):
    return {'id': identity, 'quote': {'received_epoch': received,
        'observed_at': lab.utc(received)},
        'opportunity': {'id': 'op-' + identity, 'mint': 'mint', 'pool': 'pool'}}


class AuditQueueMaintenanceTests(unittest.TestCase):
    def run_worker(self, rows):
        tasks, events, rpc = queue.Queue(), queue.Queue(), Mock()
        for row in rows:
            tasks.put(copy.deepcopy(row))
        original = c.pool_check
        def check(row, read):
            # Use the production expiration path, not a modeled network result.
            if 'quote' not in row or row['quote']['received_epoch'] < 980:
                return original(row, read)
            read('getAccountInfo', [])
            return {'id': row['id'], 'status': 'unavailable', 'fully_validated_quote': False}
        with patch.object(c, 'enabled', side_effect=lambda: not tasks.empty()), \
             patch.object(c.time, 'monotonic', return_value=0), \
             patch.object(c.time, 'time', return_value=1000), \
             patch.object(c, 'pool_check', side_effect=check), \
             patch('builtins.print'):
            c.audit_worker(events, tasks, rpc, 1)
        output = []
        while not events.empty():
            output.append(events.get_nowait()[1])
        return output, tasks, rpc

    def test_expired_records_do_not_starve_fresh_snapshot(self):
        rows = [task('old'+str(i), 900) for i in range(6)] + [task('fresh', 995)]
        output, pending, rpc = self.run_worker(rows)
        self.assertEqual([r['id'] for r in output], [r['id'] for r in rows])
        self.assertEqual(sum(r['status']=='missed_snapshot_window_no_backfill' for r in output), 6)
        self.assertEqual(rpc.call_count, 1)
        self.assertTrue(pending.empty())

    def test_seventh_live_task_is_not_silently_dequeued(self):
        output, pending, rpc = self.run_worker([task(str(i), 995) for i in range(7)])
        self.assertEqual(len(output), 6)
        self.assertEqual(rpc.call_count, 6)
        self.assertEqual(pending.qsize(), 1)
        self.assertEqual(pending.get_nowait()['id'], '6')

    def test_expired_backlog_does_not_raise_live_request_budget(self):
        rows = [task('old'+str(i), 900) for i in range(80)] + [task('live'+str(i), 995) for i in range(8)]
        output, pending, rpc = self.run_worker(rows)
        self.assertEqual(len(output), 86)
        self.assertEqual(rpc.call_count, 6)
        self.assertEqual(pending.qsize(), 2)
        self.assertEqual(len({r['id'] for r in output}), len(output))

    def test_expired_bookkeeping_is_itself_bounded(self):
        output, pending, rpc = self.run_worker([task(str(i), 900) for i in range(105)])
        self.assertEqual(len(output), 100)
        self.assertEqual(pending.qsize(), 5)
        rpc.assert_not_called()

    def test_error_record_is_preserved_without_terminating_worker(self):
        output, pending, rpc = self.run_worker([{'id':'bad','opportunity':{}},task('fresh',995)])
        self.assertEqual(output[0]['status'], 'audit_error')
        self.assertEqual(output[0]['error'], 'KeyError')
        self.assertEqual(output[1]['id'], 'fresh')
        self.assertTrue(pending.empty())
        self.assertEqual(rpc.call_count, 1)

    def test_disabled_control_consumes_no_tasks(self):
        tasks, events = queue.Queue(), queue.Queue()
        tasks.put(task('a',995))
        with patch.object(c,'enabled',return_value=False), patch.object(c.time,'monotonic',return_value=0), \
             patch.object(c,'pool_check') as check, patch('builtins.print'):
            c.audit_worker(events,tasks,Mock(),1)
        check.assert_not_called()
        self.assertEqual(tasks.qsize(),1)
        self.assertTrue(events.empty())

    def test_worker_deadline_consumes_no_tasks(self):
        tasks, events = queue.Queue(), queue.Queue()
        tasks.put(task('a',995))
        with patch.object(c,'enabled',return_value=True), patch.object(c.time,'monotonic',return_value=2), \
             patch.object(c,'pool_check') as check, patch('builtins.print'):
            c.audit_worker(events,tasks,Mock(),1)
        check.assert_not_called()
        self.assertEqual(tasks.qsize(),1)

    def test_input_tasks_remain_unchanged(self):
        rows = [task('old',900),task('live',995)]
        saved = copy.deepcopy(rows)
        self.run_worker(rows)
        self.assertEqual(rows,saved)

    def test_restart_queue_is_ordered_by_receipt_not_signature(self):
        pending = {'a':task('a',999),'z':task('z',981),'m':task('m',985)}
        persisted = json.loads(json.dumps(pending,sort_keys=True))
        result = c.pending_audit_tasks(persisted)
        self.assertEqual([r['id'] for r in result],['z','m','a'])
        result[0]['quote']['received_epoch']=0
        self.assertEqual(persisted['z']['quote']['received_epoch'],981)

    def test_malformed_timestamp_sort_does_not_change_evidence(self):
        pending = {'a':task('a',995),'b':{'id':'b','quote':{}},'c':task('c',995)}
        pending['c']['quote']['received_epoch'] = float('nan')
        rows = c.pending_audit_tasks(pending)
        self.assertEqual({r['id'] for r in rows[:2]}, {'b','c'})
        self.assertEqual(rows[-1]['id'],'a')
        self.assertNotIn('received_epoch',pending['b']['quote'])

    def test_discovery_snapshot_excludes_growing_quote_payloads(self):
        class NoCopy:
            def __deepcopy__(self,memo):
                raise AssertionError('historical quote payload must not be copied')
        source = {'discovery_v4':{'pending':{'sig':{'attempts':2}}},
                  'migration_validation':{'known':NoCopy()},
                  'opportunities':{'op':{'id':'op','signature':'sig','mint':'mint','pool':'pool',
                      'collector_version':c.VERSION,'entry_quotes':NoCopy(),'exit_quotes':NoCopy()}},
                  'other_historical_data':NoCopy()}
        slim = c.discovery_snapshot(source)
        self.assertEqual(slim['migration_validation'],{'known':None})
        self.assertNotIn('entry_quotes',slim['opportunities']['op'])
        self.assertEqual(slim['opportunities']['op']['mint'],'mint')
        slim['discovery_v4']['pending']['sig']['attempts']=9
        self.assertEqual(source['discovery_v4']['pending']['sig']['attempts'],2)

    def test_snapshot_preserves_legacy_selection_and_order(self):
        source={'discovery_v4':{},'migration_validation':{'old1':{'status':'unresolved'}},
                'opportunities':{k:{'id':k,'signature':k,'mint':k,'pool':k,'collector_version':v}
                   for k,v in [('old1','0.3'),('old2','0.3'),('new',c.VERSION),('old3','0.3')]}}
        before=copy.deepcopy(source)
        slim=c.discovery_snapshot(source)
        def eligible(s):
            return [(o['id'],o['signature'],o['mint'],o['pool']) for o in s['opportunities'].values()
                    if o['id'] not in s['migration_validation'] and o.get('collector_version')!=c.VERSION][:2]
        self.assertEqual(eligible(source),eligible(slim))
        self.assertEqual(source,before)
        self.assertEqual(c.VERSION,'prospective-quote-lab-0.4')
        self.assertEqual((c.MAX_RPC,c.MAX_FETCHES,c.MAX_PENDING,c.PAGE,c.SNAPSHOT_MAX_AGE),(40,24,2000,100,20.0))
        self.assertEqual(lab.MIN_QUOTE_INTERVAL,2.5)


if __name__=='__main__':
    unittest.main()
