from __future__ import annotations

from datetime import datetime, timezone

from .extensions import db


class Candidate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(200), nullable=False, unique=True)
    branch = db.Column(db.String(200), nullable=False)
    degree = db.Column(db.String(200), nullable=False)
    year = db.Column(db.String(50), nullable=False)
    role = db.Column(db.String(200), nullable=False)
    skills = db.Column(db.String(400), nullable=False)


class Interview(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    candidate_id = db.Column(db.Integer, db.ForeignKey("candidate.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    ended_at = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(20), default="ongoing", nullable=False)
    assignment_score = db.Column(db.Integer, nullable=True)
    assignment_remarks = db.Column(db.Text, nullable=True)
    transcript = db.Column(db.Text, nullable=True)
    summary = db.Column(db.Text, nullable=True)
    recommendation = db.Column(db.String(50), nullable=True)
    recommendation_reason = db.Column(db.Text, nullable=True)

    candidate = db.relationship("Candidate", backref=db.backref("interviews", lazy=True))


class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    interview_id = db.Column(db.Integer, db.ForeignKey("interview.id"), nullable=False)
    skill = db.Column(db.String(100), nullable=False)
    text = db.Column(db.Text, nullable=False)
    asked = db.Column(db.Boolean, default=False, nullable=False)
    rating = db.Column(db.Integer, nullable=True)
    note = db.Column(db.Text, nullable=True)


class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    interview_id = db.Column(db.Integer, db.ForeignKey("interview.id"), nullable=False)
    skill = db.Column(db.String(100), nullable=False)
    tag = db.Column(db.String(50), nullable=False)
    text = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)


class Score(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    interview_id = db.Column(db.Integer, db.ForeignKey("interview.id"), nullable=False)
    skill = db.Column(db.String(100), nullable=False)
    value = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text, nullable=True)
