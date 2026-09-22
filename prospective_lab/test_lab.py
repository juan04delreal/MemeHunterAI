import json, tempfile, unittest
from pathlib import Path
import lab
class Tests(unittest.TestCase):
 def test_watch_only_constants(self):
  self.assertEqual(lab.VERSION,'prospective-quote-lab-0.1')
 def test_quote_without_key_is_nonexecuting(self):
  import os
  old=os.environ.pop('JUPITER_API_KEY',None)
  try: self.assertEqual(lab.jupiter_quote(lab.USDC,lab.WSOL,1000000)['status'],'not_configured')
  finally:
   if old is not None: os.environ['JUPITER_API_KEY']=old
if __name__=='__main__': unittest.main()
