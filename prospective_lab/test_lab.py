import hashlib, os, unittest
import lab

def b58encode(data):
    n=int.from_bytes(data,'big'); out=''
    while n:
        n,r=divmod(n,58); out=lab.ALPHABET[r]+out
    return '1'*(len(data)-len(data.lstrip(b'\0')))+(out or '')

class Tests(unittest.TestCase):
    def test_watch_only_constants(self):
        self.assertEqual(lab.VERSION,'prospective-quote-lab-0.2')
        self.assertEqual(lab.MIGRATE_DISC,[155,234,231,146,236,158,162,30])
    def test_migration_layout(self):
        accounts=['global','withdraw','MINT','curve','ata','user','sys','token',lab.PUMPSWAP,'POOL']
        tx={'meta':{'err':None,'innerInstructions':[]},'transaction':{'message':{'instructions':[{
            'programId':lab.PUMP,'data':b58encode(bytes(lab.MIGRATE_DISC)),'accounts':accounts}]}}}
        m=lab.decode_migration(tx)
        self.assertEqual(m['mint'],'MINT'); self.assertEqual(m['pool'],'POOL')
    def test_non_migration_rejected(self):
        tx={'meta':{'err':None},'transaction':{'message':{'instructions':[{
            'programId':lab.PUMP,'data':b58encode(b'12345678'),'accounts':['x']*10}]}}}
        self.assertIsNone(lab.decode_migration(tx))
    def test_quote_without_key_never_executes(self):
        old=os.environ.pop('JUPITER_API_KEY',None)
        try: self.assertEqual(lab.jupiter_quote(lab.USDC,lab.WSOL,1_000_000)['status'],'not_configured')
        finally:
            if old is not None: os.environ['JUPITER_API_KEY']=old

if __name__=='__main__': unittest.main()
