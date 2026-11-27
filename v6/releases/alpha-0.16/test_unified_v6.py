import unittest, sqlite3, urllib.request, urllib.parse
import test_correction
from test_collective import Fixed
import test_dashboard

class AtomicTests(unittest.TestCase):
    setUp=test_correction.Tests.setUp
    tearDown=test_correction.Tests.tearDown
    def test_rollback(self):
        source=self.c.run('1+1',{'a':Fixed('2'),'b':Fixed('3')})
        self.core.db.execute("CREATE TRIGGER fail_correction BEFORE INSERT ON corrections BEGIN SELECT RAISE(ABORT,'injected'); END")
        with self.assertRaises(sqlite3.IntegrityError): self.r.run(source['id'])
        for table in ('adjudication','corrections'):
            self.assertEqual(self.core.db.execute(f'SELECT count(*) FROM {table}').fetchone()[0],0)
        self.assertEqual(self.c.get(source['id']),source)
        self.core.db.execute('DROP TRIGGER fail_correction')
        self.assertEqual(self.r.run(source['id'])['decisions'][1]['revised'],'2')

class IntegratedDashboardTests(unittest.TestCase):
    setUp=test_dashboard.DashboardTests.setUp
    tearDown=test_dashboard.DashboardTests.tearDown
    page=test_dashboard.DashboardTests.page
    token=test_dashboard.DashboardTests.token
    def test_collective(self):
        page=urllib.request.urlopen(self.url+'/collective',urllib.parse.urlencode(dict(token=self.token(),questions='2+2',provider='demo')).encode()).read().decode()
        self.assertIn('local_arithmetic_correction',page)
        self.assertIn('abstain',page)
        self.assertIn('local_arithmetic_check',page)
        self.assertIn('authenticated&quot;: false',page)
