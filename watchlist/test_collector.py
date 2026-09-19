import copy
import hashlib
import unittest
import collector as c

WALLET = 'kEFiAX3jo5NmemysQov342TZ9mGh6yp92GDRjhA8XDf'
MINT = '91ryaCo5yGpYZM3bs6GUPs97VWJQj7RozBmqPULgpump'

def encode(data):
    value = int.from_bytes(data, 'big')
    result = ''
    while value:
        value, r = divmod(value, 58)
        result = c.ALPHABET[r] + result
    return '1' * (len(data) - len(data.lstrip(b'\0'))) + result

def sample(instruction='buy', side='in', program=c.PUMP):
    accounts = ['x','x',MINT,'x','x','x',WALLET]
    if program == c.SWAP:
        accounts = ['pool',WALLET,'global',MINT,c.WSOL]
    row = {'owner': WALLET, 'mint': MINT, 'uiTokenAmount': {'amount':'2500000','decimals':6}}
    return {'transaction': {'message': {'accountKeys':[{'pubkey':WALLET,'signer':True}],
             'instructions':[{'programId':program,'accounts':accounts,
              'data':encode(hashlib.sha256(('global:'+instruction).encode()).digest()[:8])}]}},
            'meta': {'err':None,'fee':5000,'preBalances':[1000000000], 'postBalances':[900000000],
              'preTokenBalances':[] if side == 'in' else [row], 'postTokenBalances':[row] if side == 'in' else []}}

class Tests(unittest.TestCase):
    def test_addresses(self):
        cfg = c.load(c.ROOT/'config.json')
        for addr in cfg['tokens']+[w['address'] for w in cfg['wallets']]:
            self.assertTrue(c.valid_address(addr), addr)
    def test_buy(self):
        r = c.decode_flows(sample(),{WALLET})[0]
        self.assertEqual(r['classification'],'buy_candidate')
        self.assertEqual(r['token_delta'],'2.5')
        self.assertIsNone(r['realized_profit'])
    def test_sell(self):
        self.assertEqual(c.decode_flows(sample('sell','out'),{WALLET})[0]['classification'],'sell_candidate')
    def test_pumpswap(self):
        self.assertEqual(c.decode_flows(sample(program=c.SWAP),{WALLET})[0]['classification'],'buy_candidate')
    def test_no_allocation_as_buy(self):
        tx=sample(); tx['transaction']['message']['instructions']=[]
        self.assertEqual(c.decode_flows(tx,{WALLET})[0]['classification'],'inflow_unclassified')
    def test_liquidity_not_buy(self):
        self.assertEqual(c.decode_flows(sample('deposit'),{WALLET})[0]['classification'],'inflow_unclassified')
    def test_unknown_program(self):
        self.assertEqual(c.decode_flows(sample(program=WALLET),{WALLET})[0]['classification'],'inflow_unclassified')
    def test_failed_transaction(self):
        tx=sample(); tx['meta']['err']={'InstructionError':[0,'error']}
        self.assertEqual(c.decode_flows(tx,{WALLET}),[])
    def test_mixed(self):
        tx=sample(); tx['transaction']['message']['instructions'] += sample('sell')['transaction']['message']['instructions']
        self.assertEqual(c.decode_flows(tx,{WALLET})[0]['classification'],'mixed_trade_unclassified')
    def test_forbidden_method(self):
        with self.assertRaises(c.FeedError):
            c.RPC().call('not_a_read_method', [])

if __name__ == '__main__':
    unittest.main()
