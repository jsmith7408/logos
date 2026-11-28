import sqlite3
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path
from research_adapter31 import record

class CleanupTests(unittest.TestCase):
    def test_close_success_and_failure(self):
        for fail in (False, True):
            with self.subTest(fail=fail), tempfile.TemporaryDirectory() as d:
                conn = sqlite3.connect(Path(d)/'db')
                if fail:
                    conn.execute('CREATE TABLE experimental_reasoning (bad TEXT)')
                    conn.commit()
                with patch('research_adapter31.sqlite3.connect', return_value=conn):
                    if fail:
                        with self.assertRaises(sqlite3.OperationalError):
                            record('unused','unknown')
                    else:
                        record('unused','unknown')
                with self.assertRaises(sqlite3.ProgrammingError):
                    conn.execute('SELECT 1')
