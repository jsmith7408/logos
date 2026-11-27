import unittest
from unittest.mock import patch
from providers import OllamaProvider,ProviderError
from worker import DeadlineProvider
class WorkerTests(unittest.TestCase):
    def test_retired_worker(self):
        with patch('subprocess.run',side_effect=AssertionError('worker forbidden')) as run:
            with self.assertRaisesRegex(ProviderError,'disabled'): DeadlineProvider(OllamaProvider('fixture'),3).reason('q')
            run.assert_not_called()
    def test_invalid_deadline(self):
        for x in [0,float('nan'),float('inf'),True]:
            with self.assertRaises(ValueError): DeadlineProvider(OllamaProvider('fixture'),x)
