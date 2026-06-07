import socket
from fastapi import APIRouter

router = APIRouter(prefix="/api/gateway", tags=["gateway"])

def check_port(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        try:
            s.connect((host, port))
            return True
        except (socket.timeout, ConnectionRefusedError, OSError):
            return False

@router.get("/status")
def get_gateway_status():
    # OpenClaw canvas normally runs on 3000
    is_running = check_port("127.0.0.1", 3000)
    
    return {
        "status": "running" if is_running else "stopped",
        "port": 3000,
        "host": "127.0.0.1"
    }
