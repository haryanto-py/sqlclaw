import json
from pathlib import Path
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from skillhub.backend.services.skill_manager import get_skills, OPENCLAW_JSON, SKILLS_DIR

router = APIRouter(prefix="/api/skills", tags=["skills"])

class ToggleSkillReq(BaseModel):
    name: str
    enabled: bool
    source: str = ""

class AddSkillReq(BaseModel):
    name: str
    description: str

@router.get("")
def list_skills():
    return {"skills": get_skills()}

@router.post("/toggle")
def toggle_skill(req: ToggleSkillReq):
    try:
        cfg = json.loads(OPENCLAW_JSON.read_text(encoding="utf-8")) if OPENCLAW_JSON.exists() else {}
        
        if "skills" not in cfg:
            cfg["skills"] = {}
        if "entries" not in cfg["skills"]:
            cfg["skills"]["entries"] = {}
            
        entries = cfg["skills"]["entries"]
        
        if req.enabled:
            # Add or enable skill
            if req.name not in entries:
                entries[req.name] = {"source": req.source or f"./skills/{req.name}.js", "config": {}}
            else:
                if "enabled" in entries[req.name]:
                    entries[req.name]["enabled"] = True
        else:
            # Disable skill
            if req.name in entries:
                entries[req.name]["enabled"] = False
                
        OPENCLAW_JSON.write_text(json.dumps(cfg, indent=2, ensure_ascii=False), encoding="utf-8")
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/add")
def add_skill(req: AddSkillReq):
    try:
        # Create boilerplate js file
        skill_file = SKILLS_DIR / f"{req.name}.js"
        if skill_file.exists():
            raise HTTPException(status_code=400, detail="Skill already exists.")
            
        SKILLS_DIR.mkdir(parents=True, exist_ok=True)
        boilerplate = f"""module.exports = {{
  name: "{req.name}",
  description: "{req.description}",
  parameters: {{
    type: "object",
    properties: {{}},
    required: []
  }},
  handler(args, {{ config }}) {{
    return {{ message: "Hello from {req.name}!" }};
  }}
}};"""
        skill_file.write_text(boilerplate, encoding="utf-8")
        
        # Add to openclaw.json
        cfg = json.loads(OPENCLAW_JSON.read_text(encoding="utf-8")) if OPENCLAW_JSON.exists() else {}
        if "skills" not in cfg:
            cfg["skills"] = {}
        if "entries" not in cfg["skills"]:
            cfg["skills"]["entries"] = {}
            
        cfg["skills"]["entries"][req.name] = {
            "source": f"./skills/{req.name}.js",
            "config": {}
        }
        OPENCLAW_JSON.write_text(json.dumps(cfg, indent=2, ensure_ascii=False), encoding="utf-8")
        
        return {"success": True}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
