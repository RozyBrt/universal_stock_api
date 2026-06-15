from fastapi.testclient import TestClient
from app.main import app
from app.core.security import create_access_token
import pytest

client = TestClient(app)

def test_websocket_connection_success():
    """Menguji koneksi WebSocket berhasil dengan token JWT yang valid"""
    token = create_access_token(data={"sub": "1"})
    
    with client.websocket_connect(f"/api/v1/ws?token={token}") as websocket:
        # Koneksi berhasil terjalin
        assert websocket is not None

def test_websocket_connection_no_token():
    """Menguji koneksi WebSocket ditolak karena token tidak dicantumkan"""
    with pytest.raises(Exception):
        with client.websocket_connect("/api/v1/ws"):
            pass

def test_websocket_connection_invalid_token():
    """Menguji koneksi WebSocket ditolak karena token tidak valid"""
    with pytest.raises(Exception):
        with client.websocket_connect("/api/v1/ws?token=invalid_token_here"):
            pass
