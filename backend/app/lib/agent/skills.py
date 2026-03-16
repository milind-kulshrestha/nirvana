"""Skill manager for AI agent skill discovery and materialization."""
import logging
import shutil
from pathlib import Path
from sqlalchemy.orm import Session

from app.models.skill import Skill

logger = logging.getLogger(__name__)

# System skills directory (shipped with the platform)
SYSTEM_SKILLS_DIR = (
    Path(__file__).parent.parent.parent.parent / "data" / "system_skills"
)


class SkillManager:
    """Bridges DB-stored user skills with SDK's filesystem-based skill loading."""

    def __init__(self, db: Session, user_id: int):
        self.db = db
        self.user_id = user_id

    def materialize_user_skills(self, base_dir: Path) -> Path:
        """Write user's DB skills to temp filesystem for SDK discovery.

        Creates: {base_dir}/.claude/skills/{name}/SKILL.md for each active skill.
        Returns the base_dir (used as cwd for agent).
        """
        skills_dir = base_dir / ".claude" / "skills"
        skills_dir.mkdir(parents=True, exist_ok=True)

        user_skills = (
            self.db.query(Skill)
            .filter(
                Skill.user_id == self.user_id,
                Skill.is_active == True,  # noqa: E712
            )
            .all()
        )

        for skill in user_skills:
            skill_dir = skills_dir / skill.name
            skill_dir.mkdir(exist_ok=True)
            (skill_dir / "SKILL.md").write_text(skill.content)
            logger.debug(f"Materialized user skill: {skill.name}")

        return base_dir

    def copy_system_skills(self, base_dir: Path) -> None:
        """Copy system skills to the work directory."""
        if not SYSTEM_SKILLS_DIR.exists():
            logger.warning(f"System skills directory not found: {SYSTEM_SKILLS_DIR}")
            return

        target = base_dir / ".claude" / "skills"
        target.mkdir(parents=True, exist_ok=True)

        for skill_dir in SYSTEM_SKILLS_DIR.iterdir():
            if skill_dir.is_dir():
                shutil.copytree(skill_dir, target / skill_dir.name, dirs_exist_ok=True)
                logger.debug(f"Copied system skill: {skill_dir.name}")

    def get_available_skills(self) -> list[dict]:
        """List all available skills (system + user) for UI display."""
        skills = []

        # System skills
        if SYSTEM_SKILLS_DIR.exists():
            for skill_dir in SYSTEM_SKILLS_DIR.iterdir():
                if skill_dir.is_dir():
                    skill_md = skill_dir / "SKILL.md"
                    if skill_md.exists():
                        content = skill_md.read_text()
                        name = skill_dir.name
                        description = self._extract_description(content)
                        skills.append({
                            "name": name,
                            "description": description,
                            "is_system": True,
                            "is_active": True,
                        })

        # User skills
        user_skills = (
            self.db.query(Skill)
            .filter(Skill.user_id == self.user_id)
            .all()
        )
        for skill in user_skills:
            skills.append({
                "id": skill.id,
                "name": skill.name,
                "description": skill.description or "",
                "is_system": False,
                "is_active": skill.is_active,
            })

        return skills

    def get_skills_for_prompt(self) -> list[dict]:
        """Return skill metadata for injection into the system prompt.

        Returns merged list of system + user skills (user overrides system on name collision).
        """
        skills: dict[str, dict] = {}

        # System skills
        if SYSTEM_SKILLS_DIR.exists():
            for skill_dir in SYSTEM_SKILLS_DIR.iterdir():
                if skill_dir.is_dir():
                    skill_md = skill_dir / "SKILL.md"
                    if skill_md.exists():
                        content = skill_md.read_text()
                        description = self._extract_description(content)
                        skills[skill_dir.name] = {
                            "name": skill_dir.name,
                            "description": description,
                        }

        # User skills (active only) — override system skills with same name
        user_skills = (
            self.db.query(Skill)
            .filter(
                Skill.user_id == self.user_id,
                Skill.is_active == True,  # noqa: E712
            )
            .all()
        )
        for skill in user_skills:
            skills[skill.name] = {
                "name": skill.name,
                "description": skill.description or "",
            }

        return list(skills.values())

    def load_skill_content(self, skill_name: str) -> str | None:
        """Load the full SKILL.md content for a given skill name.

        Search order: user DB (active) first, then system skills directory.
        Returns raw content string or None if not found.
        """
        # User skills first
        user_skill = (
            self.db.query(Skill)
            .filter(
                Skill.user_id == self.user_id,
                Skill.name == skill_name,
                Skill.is_active == True,  # noqa: E712
            )
            .first()
        )
        if user_skill:
            return user_skill.content

        # System skills
        skill_md = SYSTEM_SKILLS_DIR / skill_name / "SKILL.md"
        if skill_md.exists():
            return skill_md.read_text()

        return None

    @staticmethod
    def _extract_description(content: str) -> str:
        """Extract description from SKILL.md YAML frontmatter."""
        if not content.startswith("---"):
            return ""
        try:
            end = content.index("---", 3)
            frontmatter = content[3:end]
            for line in frontmatter.split("\n"):
                if line.strip().startswith("description:"):
                    return line.split(":", 1)[1].strip().strip('"').strip("'")
        except (ValueError, IndexError):
            pass
        return ""
