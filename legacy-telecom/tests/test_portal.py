"""Exerce le parseur HTTP et le catalogue en mémoire, sans socket ni Docker."""
import io
from http.client import HTTPResponse
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from urllib.parse import urlencode

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'target' / 'app'))
from database import initialize
from server import Handler


class Connection:
    def __init__(self, request):
        self.request = request
        self.output = bytearray()

    def makefile(self, mode, *args):
        return io.BytesIO(self.request)

    def sendall(self, data):
        self.output.extend(data)


class QuietHandler(Handler):
    def log_message(self, *args):
        pass


class PortalTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.database = Path(cls.temp.name) / 'portal.db'
        cls.password = 'LT-test-only-1234'
        initialize(cls.database, cls.password)
        cls.server = SimpleNamespace(database=cls.database)

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def get(self, path):
        request = f'GET {path} HTTP/1.0\r\nHost: localhost\r\n\r\n'.encode()
        connection = Connection(request)
        QuietHandler(connection, ('127.0.0.1', 12345), self.server)
        response = HTTPResponse(Connection(bytes(connection.output)))
        response.begin()
        with response:
            return response.status, response.read().decode('utf-8')

    def query(self, payload):
        return self.get('/legacy/offer?' + urlencode({'id': payload}))

    def test_public_navigation_does_not_leak_password(self):
        for path in ('/', '/offres', '/assistance', '/legacy/', '/legacy/offer?id=1', '/static/style.css'):
            with self.subTest(path=path):
                status, body = self.get(path)
                self.assertEqual(status, 200)
                self.assertNotIn(self.password, body)
                self.assertNotIn('flag{', body)

    def test_robots_points_to_legacy(self):
        self.assertIn('Disallow: /legacy/', self.get('/robots.txt')[1])

    def test_legitimate_offer(self):
        status, body = self.query('2')
        self.assertEqual(status, 200)
        self.assertIn('ADSL Découverte', body)
        self.assertNotIn('Pro Connect', body)

    def test_invalid_id_provides_sql_clue(self):
        status, body = self.query("1'")
        self.assertEqual(status, 500)
        self.assertIn('Erreur SQL', body)
        self.assertIn('SELECT id, name, price, description FROM offers', body)

    def test_enumerate_schema_then_retrieve_credentials(self):
        status, body = self.query("-1 UNION SELECT 1,name,sql,'schema' FROM sqlite_master WHERE type='table' -- ")
        self.assertEqual(status, 200)
        self.assertIn('employees', body)
        self.assertIn('username TEXT', body)
        status, body = self.query('-1 UNION SELECT id,username,password,role FROM employees -- ')
        self.assertEqual(status, 200)
        self.assertIn('support', body)
        self.assertIn(self.password, body)

    def test_direct_file_requests_are_not_served(self):
        for path in ('/root/root.txt', '/home/support/user.txt', '/var/lib/legacy-state/state.json', '/static/../../entrypoint.py', '/.env'):
            with self.subTest(path=path):
                self.assertEqual(self.get(path)[0], 404)

    def test_stacked_queries_cannot_destroy_database(self):
        self.assertEqual(self.query('1; DROP TABLE employees; --')[0], 500)
        with sqlite3.connect(self.database) as db:
            self.assertEqual(db.execute('SELECT count(*) FROM employees').fetchone()[0], 1)

    def test_html_from_database_is_escaped(self):
        with sqlite3.connect(self.database) as db:
            db.execute("INSERT INTO offers VALUES (99, '<script>alert(1)</script>', 'test', 'test')")
        body = self.query('99')[1]
        self.assertIn('&lt;script&gt;', body)
        self.assertNotIn('<script>', body)

    def test_request_length_is_bounded(self):
        self.assertEqual(self.query('1' * 2001)[0], 400)


if __name__ == '__main__':
    unittest.main()
