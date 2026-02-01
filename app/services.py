from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Iterable
import json

from sqlalchemy import text

from .constants import DEFAULT_QUESTION_BANK
from .extensions import db
from .models import Interview, Note, Question, Score

BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent
DB_PATH = ROOT_DIR / "interviews.db"
QUESTION_BANK_PATH = ROOT_DIR / "question_bank.json"


def load_question_bank() -> dict[str, list[str]]:
    if QUESTION_BANK_PATH.exists():
        try:
            return json.loads(QUESTION_BANK_PATH.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return DEFAULT_QUESTION_BANK
    QUESTION_BANK_PATH.write_text(
        json.dumps(DEFAULT_QUESTION_BANK, indent=2),
        encoding="utf-8",
    )
    return DEFAULT_QUESTION_BANK


def save_question_bank(bank: dict[str, list[str]]) -> None:
    QUESTION_BANK_PATH.write_text(
        json.dumps(bank, indent=2),
        encoding="utf-8",
    )


def parse_skills(raw: str | None) -> list[str]:
    if not raw:
        return []
    return [skill.strip() for skill in raw.split(",") if skill.strip()]


def normalize_skills(selected: Iterable[str], custom_raw: str | None) -> list[str]:
    skills = [skill.strip() for skill in selected if skill.strip()]
    skills.extend(parse_skills(custom_raw))
    unique = []
    seen = set()
    for skill in skills:
        if skill.lower() in seen:
            continue
        seen.add(skill.lower())
        unique.append(skill)
    return unique


def is_valid_email(email: str) -> bool:
    if not email or "@" not in email:
        return False
    local, _, domain = email.partition("@")
    return bool(local) and "." in domain


def build_question_set(skills: Iterable[str]) -> list[dict]:
    question_bank = load_question_bank()
    questions = []
    for skill in skills:
        for text in question_bank.get(skill, []):
            questions.append({"skill": skill, "text": text})
    return questions


def average_skill_scores(interviews: list[Interview]) -> dict[int, float]:
    if not interviews:
        return {}
    interview_ids = [interview.id for interview in interviews]
    scores = Score.query.filter(Score.interview_id.in_(interview_ids)).all()
    totals: dict[int, int] = defaultdict(int)
    counts: dict[int, int] = defaultdict(int)
    for score in scores:
        totals[score.interview_id] += score.value
        counts[score.interview_id] += 1
    averages: dict[int, float] = {}
    for interview_id in interview_ids:
        if counts.get(interview_id):
            averages[interview_id] = totals[interview_id] / counts[interview_id]
    return averages


def build_summary(interview: Interview) -> tuple[list[str], str, str]:
    scores = Score.query.filter_by(interview_id=interview.id).all()
    notes = Note.query.filter_by(interview_id=interview.id).order_by(Note.timestamp).all()

    strengths = [note.text for note in notes if note.tag == "Strength"]
    weaknesses = [note.text for note in notes if note.tag in {"Weakness", "Red Flag"}]

    scored = sorted(scores, key=lambda s: s.value, reverse=True)
    top_scores = [s for s in scored if s.value >= 4][:2]
    low_scores = [s for s in scored if s.value <= 2][:2]

    bullets: list[str] = []
    for item in top_scores:
        bullets.append(f"Strong {item.skill} performance (score {item.value}/5).")
    if strengths:
        bullets.append(f"Strength noted: {strengths[0]}")

    for item in low_scores:
        bullets.append(f"Needs improvement in {item.skill} (score {item.value}/5).")
    if weaknesses:
        bullets.append(f"Concern: {weaknesses[0]}")

    if interview.assignment_score is not None:
        bullets.append(
            f"Assignment score: {interview.assignment_score}/100. {interview.assignment_remarks or ''}".strip()
        )

    if interview.transcript:
        bullets.append("Interview transcript provided for review.")

    if not bullets:
        bullets.append("No significant strengths or weaknesses recorded. Add notes and scores to refine.")

    avg_score = None
    if scores:
        avg_score = sum(score.value for score in scores) / len(scores)

    recommendation = "Borderline"
    if avg_score is not None:
        if avg_score >= 4:
            recommendation = "Hire"
        elif avg_score <= 2.5:
            recommendation = "No Hire"
    reason = "Recommendation based on skill scores and evidence from notes."
    if avg_score is not None:
        reason = (
            f"Average score: {avg_score:.1f}/5. Recommendation considers strengths, weaknesses, and interview notes."
        )

    return bullets[:6], recommendation, reason


def _get_table_columns(table_name: str) -> set[str]:
    result = db.session.execute(text(f"PRAGMA table_info({table_name})"))
    return {row[1] for row in result}


def migrate_sqlite_schema() -> None:
    migrations = {
        "candidate": {
            "email": "ALTER TABLE candidate ADD COLUMN email VARCHAR(200)",
            "branch": "ALTER TABLE candidate ADD COLUMN branch VARCHAR(200)",
            "degree": "ALTER TABLE candidate ADD COLUMN degree VARCHAR(200)",
            "year": "ALTER TABLE candidate ADD COLUMN year VARCHAR(50)",
        },
        "interview": {
            "ended_at": "ALTER TABLE interview ADD COLUMN ended_at DATETIME",
            "status": "ALTER TABLE interview ADD COLUMN status VARCHAR(20)",
        },
        "question": {
            "note": "ALTER TABLE question ADD COLUMN note TEXT",
        },
    }

    for table, columns in migrations.items():
        existing = _get_table_columns(table)
        for column, statement in columns.items():
            if column not in existing:
                db.session.execute(text(statement))

    if "email" in _get_table_columns("candidate"):
        db.session.execute(text("UPDATE candidate SET email = COALESCE(email, '')"))
    if "branch" in _get_table_columns("candidate"):
        db.session.execute(text("UPDATE candidate SET branch = COALESCE(branch, 'Other')"))
    if "degree" in _get_table_columns("candidate"):
        db.session.execute(text("UPDATE candidate SET degree = COALESCE(degree, 'B.Tech')"))
    if "year" in _get_table_columns("candidate"):
        db.session.execute(text("UPDATE candidate SET year = COALESCE(year, 'Graduate')"))
    if "status" in _get_table_columns("interview"):
        db.session.execute(text("UPDATE interview SET status = COALESCE(status, 'completed')"))
    db.session.commit()


def init_database(database_uri: str) -> None:
    db.create_all()
    if database_uri.startswith("sqlite"):
        migrate_sqlite_schema()
