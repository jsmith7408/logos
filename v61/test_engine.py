import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
from v6.core import DemoProvider
from v61.engine import Engine, encode


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return encode(value).encode()


class Integration(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.research, self.gate = root/'research.db', root/'gate.db'
        self.admin = Ed25519PrivateKey.generate()
        self.signer = Ed25519PrivateKey.generate()
        self.public = self.admin.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw).hex()
        self.e = Engine(self.research, self.gate, self.public)
        self.deployment = self.e.identity()['deployment']
        self.record = self.e.investigate('Example question', DemoProvider())
        self.key = {'x': '1'}
        self.binding = dict(key_digest=digest(canonical(self.key)), questions_digest=digest(b'q'),
                            baseline_digest=digest(b'a'), settings_digest=digest(b's'))
        self.op('enroll', '1', 'signer', pub=self.signer.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw).hex())
        self.op('study', '2', 'study', binding=self.binding)

    def op(self, action, nonce, ident, **kw):
        operation = dict(action=action, nonce=nonce, id=ident, deployment=self.deployment, **kw)
        self.assertEqual(self.e.administer(operation, self.admin.sign(canonical(operation)))['status'], 'accepted')

    def request(self):
        b = canonical([dict(id='x', answer=0, confidence=.8)])
        c = canonical([dict(id='x', answer=1, confidence=.8)])
        meta = dict(self.binding, model='synthetic', version='1', study='study', signer='signer', origin='raw')
        bm, cm = dict(meta, arm='B', sha256=digest(b)), dict(meta, arm='C', sha256=digest(c))
        return dict(action='compare', study='study', key=self.key, questions=b'q'.hex(), baseline=b'a'.hex(),
                    settings=b's'.hex(), b=b.hex(), c=c.hex(), bm=bm, cm=cm,
                    bs=self.signer.sign(canonical(bm)).hex(), cs=self.signer.sign(canonical(cm)).hex())

    def tearDown(self):
        self.e.close()
        self.tmp.cleanup()

    def test_valid_persistence_and_replay(self):
        request = self.request()
        result = self.e.compare(request, self.record['id'])
        self.assertEqual(result['status'], 'candidate_comparison')
        self.assertEqual(result['response']['metrics']['gains'], 1)
        self.e.close()
        self.e = Engine(self.research, self.gate, self.public)
        self.assertEqual(self.e.get_comparison(result['id']), result)
        self.assertEqual(self.e.search('Example')[0]['provenance'], 'demo')
        self.assertEqual(self.e.compare(request)['status'], 'blocked')

    def test_forged_signature(self):
        request = self.request()
        request['cs'] = '00'
        self.assertEqual(self.e.compare(request)['status'], 'blocked')
        self.assertEqual(self.e.compare(self.request())['status'], 'candidate_comparison')

    def test_revocation(self):
        self.op('revoke', '3', 'signer')
        self.assertEqual(self.e.compare(self.request())['status'], 'blocked')

    def test_gate_failure(self):
        self.e.command = ['/nonexistent/logos-service']
        self.assertEqual(self.e.compare(self.request())['status'], 'indeterminate')

    def test_unknown_link_and_action(self):
        with self.assertRaises(ValueError):
            self.e.compare(self.request(), 'unknown')
        with self.assertRaises(ValueError):
            self.e.compare({'action': 'administer'})

    def test_tampered_binding(self):
        request = self.request()
        request['questions'] = b'tampered'.hex()
        self.assertEqual(self.e.compare(request)['status'], 'blocked')
