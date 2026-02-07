"""Skills routes for managing AI agent skills."""
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.database import get_db
from app.routes.auth import get_current_user
from app.models.user import User
from app.models.skill import Skill
from app.lib.agent.skills import SkillManager

router = APIRouter()
logger = logging.getLogger(__name__)


class CreateSkillRequest(BaseModel):
    name: str
    description: Optional[str] = None
    content: str


class UpdateSkillRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    content: Optional[str] = None
    is_active: Optional[bool] = None


@router.get("/")
async def list_skills(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all available skills (system + user)."""
    manager = SkillManager(db, current_user.id)
    return manager.get_available_skills()


@router.get("/system")
async def list_system_skills(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List system skills only."""
    manager = SkillManager(db, current_user.id)
    all_skills = manager.get_available_skills()
    return [s for s in all_skills if s.get("is_system")]


@router.get("/{name}")
async def get_skill(
    name: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get a specific skill's content."""
    # Check user skills first
    skill = db.query(Skill).filter(
        Skill.user_id == current_user.id,
        Skill.name == name,
    ).first()
    if skill:
        return {
            "id": skill.id,
            "name": skill.name,
            "description": skill.description,
            "content": skill.content,
            "is_active": skill.is_active,
            "is_system": False,
            "created_at": skill.created_at.isoformat(),
            "updated_at": skill.updated_at.isoformat(),
        }

    # Check system skills
    manager = SkillManager(db, current_user.id)
    from app.lib.agent.skills import SYSTEM_SKILLS_DIR
    skill_path = SYSTEM_SKILLS_DIR / name / "SKILL.md"
    if skill_path.exists():
        content = skill_path.read_text()
        return {
            "name": name,
            "description": manager._extract_description(content),
            "content": content,
            "is_system": True,
            "is_active": True,
        }

    raise HTTPException(status_code=404, detail="Skill not found")


@router.post("/", status_code=201)
async def create_skill(
    request: CreateSkillRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new user skill."""
    # Check for duplicate name
    existing = db.query(Skill).filter(
        Skill.user_id == current_user.id,
        Skill.name == request.name,
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Skill with this name already exists")

    skill = Skill(
        user_id=current_user.id,
        name=request.name,
        description=request.description,
        content=request.content,
    )
    db.add(skill)
    db.commit()
    db.refresh(skill)

    return {
        "id": skill.id,
        "name": skill.name,
        "description": skill.description,
        "content": skill.content,
        "is_active": skill.is_active,
        "created_at": skill.created_at.isoformat(),
    }


@router.put("/{skill_id}")
async def update_skill(
    skill_id: int,
    request: UpdateSkillRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update a user skill."""
    skill = db.query(Skill).filter(
        Skill.id == skill_id,
        Skill.user_id == current_user.id,
    ).first()
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")

    if request.name is not None:
        skill.name = request.name
    if request.description is not None:
        skill.description = request.description
    if request.content is not None:
        skill.content = request.content
    if request.is_active is not None:
        skill.is_active = request.is_active

    db.commit()
    db.refresh(skill)

    return {
        "id": skill.id,
        "name": skill.name,
        "description": skill.description,
        "content": skill.content,
        "is_active": skill.is_active,
        "updated_at": skill.updated_at.isoformat(),
    }


@router.delete("/{skill_id}", status_code=204)
async def delete_skill(
    skill_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a user skill."""
    skill = db.query(Skill).filter(
        Skill.id == skill_id,
        Skill.user_id == current_user.id,
    ).first()
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")

    db.delete(skill)
    db.commit()
    return None
