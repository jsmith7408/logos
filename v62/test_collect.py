import json
import os
import tempfile
import unittest
from unittest.mock import patch
from v62.collector import Collector
from v62.providers import Provider, ProviderError


def response(name, text='42'):
    if name in ('openai','grok'):
        data = dict(status='completed', model='resolved', output=[
            dict(type='message', role='assistant', content=[dict(type='output_text', text=text)])])
    elif name == 'gemini':
        data = dict(modelVersion='resolved', candidates=[
            dict(finishReason='STOP', content=dict(parts=[dict(text='hidden', thought=True),dict(text=text)]))])
    else:
        data = dict(model='resolved',done=True,done_reason='stop',message=dict(content=text))
    return json.dumps(data).encode()


class Tests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db = self.temp.name + '/test.db'
        self.c = Collector(self.db)
        self.creds = patch.dict(os.environ, {'OPENAI_API_KEY':'secret1','GEMINI_API_KEY':'secret2','XAI_API_KEY':'secret3'})
        self.creds.start()
        self.ps = [Provider(n,'example') for n in ('openai','gemini','grok','ollama')]

    def tearDown(self):
        self.c.close()
        self.creds.stop()
        self.temp.cleanup()

    def fake(self,url,payload,headers,timeout):
        name = 'openai' if 'openai.com' in url else 'grok' if 'api.x.ai' in url else 'gemini' if 'googleapis.com' in url else 'ollama'
        return response(name)

    def test_all_adapters(self):
        r = self.c.run('What is 6*7?',self.ps,allow_network=True,send=self.fake)
        self.assertEqual(r['comparison'],'exact_text_agreement')
        self.assertEqual(r['evidence_status'],'unverified')
        self.assertEqual([x['answer'] for x in r['calls']],['42']*4)
        self.assertTrue(all(x['raw_hash'] for x in r['calls']))

    def test_no_network_default(self):
        with self.assertRaises(PermissionError):
            self.c.run('x',self.ps,send=lambda *a:self.fail('network attempted'))

    def test_persistence_and_secret_exclusion(self):
        r = self.c.run('x',self.ps,allow_network=True,send=self.fake)
        self.c.close()
        self.c = Collector(self.db)
        self.assertEqual(self.c.report(r['run_id']),r)
        with open(self.db,'rb') as f:
            raw=f.read()
        self.assertNotIn(b'secret1',raw)
        self.assertNotIn(b'secret2',raw)
        self.assertNotIn(b'secret3',raw)

    def test_disagreement(self):
        r = self.c.run('x',self.ps[:2],allow_network=True,
                       send=lambda url,*a:response('openai','42') if 'openai' in url else response('gemini','43'))
        self.assertEqual(r['comparison'],'text_differs')

    def test_partial_failure(self):
        def send(url,*a):
            if 'api.x.ai' in url: raise ProviderError('http_429')
            return self.fake(url,*a)
        r = self.c.run('x',self.ps,allow_network=True,send=send)
        self.assertEqual(r['comparison'],'partial_coverage')
        self.assertEqual(r['calls'][2]['error'],'http_429')

    def test_invalid_payload_preserved(self):
        r = self.c.run('x',self.ps[:1],allow_network=True,send=lambda *a:b'not JSON')
        self.assertEqual(r['calls'][0]['error'],'invalid_response')
        self.assertIsNotNone(r['calls'][0]['raw_hash'])

    def test_refusal_or_incomplete(self):
        with self.assertRaises(ProviderError):
            self.ps[0].parse(b'{"status":"incomplete"}')

    def test_bounds_and_duplicate(self):
        with self.assertRaises(ValueError): Provider('gemini','a/b')
        with self.assertRaises(ValueError): Provider('openai','x',max_tokens=5000)
        with self.assertRaises(ValueError): self.c.run('x',[self.ps[0]]*2,allow_network=True)

    def test_missing_key(self):
        with patch.dict(os.environ,{'OPENAI_API_KEY':''}):
            r=self.c.run('x',self.ps[:1],allow_network=True,send=lambda *a:self.fail('network attempted'))
        self.assertEqual(r['calls'][0]['error'],'missing_or_invalid_credential')

    def test_unexpected_error_sanitized(self):
        def bad(*a): raise RuntimeError('secret1')
        r=self.c.run('x',self.ps[:1],allow_network=True,send=bad)
        self.assertEqual(r['calls'][0]['error'],'unexpected_error')

    def test_fixed_endpoints_and_caps(self):
        for p in self.ps:
            url,payload=p.prepare('x')
            self.assertTrue(url.startswith('https://') or url=='http://127.0.0.1:11434/api/chat')
            cap=(payload.get('max_output_tokens') or payload.get('generationConfig',{}).get('maxOutputTokens')
                 or payload.get('options',{}).get('num_predict'))
            self.assertEqual(cap,1024)
