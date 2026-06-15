from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, List, Any
from app.core.logging import StructuredLogger

logger = StructuredLogger(__name__)

class ConnectionManager:
    """
    Mengelola semua koneksi WebSocket aktif di memori server (In-Memory).
    
    Menghubungkan user_id (string) ke daftar koneksi WebSocket aktif,
    memungkinkan multi-koneksi per user (misal user buka beberapa tab).
    """
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, user_id: str):
        """Menerima koneksi WebSocket dan mendaftarkannya"""
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)
        logger.log_info(
            f"🔌 WebSocket Terkoneksi: User ID {user_id}",
            extra={"user_id": user_id, "active_sessions_for_user": len(self.active_connections[user_id])}
        )

    def disconnect(self, websocket: WebSocket, user_id: str):
        """Menghapus koneksi WebSocket yang ditutup"""
        if user_id in self.active_connections:
            if websocket in self.active_connections[user_id]:
                self.active_connections[user_id].remove(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
        logger.log_info(f"🔌 WebSocket Terputus: User ID {user_id}")

    async def send_personal_message(self, message: Dict[str, Any], user_id: str):
        """Mengirim pesan hanya ke user spesifik (ke semua tab aktifnya)"""
        if user_id in self.active_connections:
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.log_warning(f"Gagal mengirim pesan ke User ID {user_id}: {str(e)}")

    async def broadcast(self, message: Dict[str, Any]):
        """Menyiarkan (broadcast) pesan ke semua koneksi WebSocket yang aktif"""
        for user_id, connections in list(self.active_connections.items()):
            for connection in list(connections):
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.log_warning(f"Gagal broadcast ke User ID {user_id}: {str(e)}")
                    # Bersihkan koneksi yang rusak
                    try:
                        connections.remove(connection)
                    except ValueError:
                        pass
            if not connections:
                del self.active_connections[user_id]

# Global instance manager
manager = ConnectionManager()
