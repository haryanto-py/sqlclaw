import json
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from skillhub.backend.services.skill_manager import OPENCLAW_JSON

router = APIRouter(prefix="/api/users", tags=["users"])

class UpdateUsersReq(BaseModel):
    allowFrom: list[int]

@router.get("")
def get_users():
    try:
        cfg = json.loads(OPENCLAW_JSON.read_text(encoding="utf-8")) if OPENCLAW_JSON.exists() else {}
        allowFrom = cfg.get("channels", {}).get("telegram", {}).get("allowFrom", [])
        return {"allowFrom": allowFrom}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("")
def update_users(req: UpdateUsersReq):
    try:
        cfg = json.loads(OPENCLAW_JSON.read_text(encoding="utf-8")) if OPENCLAW_JSON.exists() else {}
        
        if "channels" not in cfg:
            cfg["channels"] = {}
        if "telegram" not in cfg["channels"]:
            cfg["channels"]["telegram"] = {}
            
        cfg["channels"]["telegram"]["allowFrom"] = req.allowFrom
        
        OPENCLAW_JSON.write_text(json.dumps(cfg, indent=2, ensure_ascii=False), encoding="utf-8")
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
