from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status
from typing import Optional
from app.core.security import verify_token
from app.core.websocket import manager
from app.core.logging import StructuredLogger

logger = StructuredLogger(__name__)
router = APIRouter(tags=["websocket"])

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: Optional[str] = None):
    """
    WebSocket Endpoint untuk pembaruan inventaris real-time dan low-stock alerts.
    Menerima token JWT melalui query parameter (?token=...) untuk autentikasi.
    """
    if not token:
        logger.log_warning("Koneksi WebSocket ditolak: Token tidak ditemukan.")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Token missing")
        return
        
    try:
        # Verifikasi token JWT
        payload = verify_token(token)
        user_id = str(payload.get("sub"))
    except Exception as e:
        logger.log_warning(f"Koneksi WebSocket ditolak: Token tidak valid ({str(e)}).")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid token")
        return
        
    # Terima koneksi WebSocket
    await manager.connect(websocket, user_id)
    
    try:
        while True:
            # Jaga koneksi tetap terbuka dan terima pesan ping/pong dari client
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)
    except Exception as e:
        logger.log_error(e, request_id=None)
        manager.disconnect(websocket, user_id)
