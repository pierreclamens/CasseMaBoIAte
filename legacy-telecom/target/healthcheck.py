import socket
from urllib.request import urlopen

with urlopen('http://127.0.0.1/healthz', timeout=2) as response:
    assert response.read() == b'ok'
    assert response.headers.get('Server', '').startswith('nginx/')
with socket.create_connection(('127.0.0.1', 22), timeout=2) as connection:
    assert connection.recv(128).startswith(b'SSH-2.0-')
