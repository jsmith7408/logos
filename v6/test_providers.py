import unittest
from unittest.mock import patch
from providers import OllamaProvider, ProviderError
class Tests(unittest.TestCase):
    def test_retired_adapter(self):
        with patch('socket.create_connection',side_effect=AssertionError('network forbidden')) as connect:
            with self.assertRaisesRegex(ProviderError,'disabled'): OllamaProvider('anything').reason('q')
            connect.assert_not_called()
