from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from io import BytesIO

import os

from dotenv import load_dotenv
from flask import Blueprint, abort, current_app, jsonify, redirect, render_template, request, send_file, url_for
from fpdf import FPDF

from .constants import DEFAULT_BRANCHES, DEFAULT_DEGREES, DEFAULT_ROLES, DEFAULT_YEARS
from .extensions import db
from .models import Candidate, Interview, Note, Question, Score
from .services import (
    build_question_set,
    build_summary,
    is_valid_email,
    load_question_bank,
    normalize_skills,
    parse_skills,
    average_skill_scores,
    save_question_bank,
)
from .llm_summary import generate_llm_summary

main_bp = Blueprint("main", __name__)


def _get_or_404(model, pk: int):
    instance = db.session.get(model, pk)
    if not instance:
        abort(404)
    return instance


@main_bp.route("/")
def dashboard():
    role_filter = request.args.get("role", "").strip()
    recommendation_filter = request.args.get("recommendation", "").strip()
    sort_filter = request.args.get("sort", "").strip()
    completed_page = request.args.get("completed_page", "1").strip()
    per_page = 6

    interviews = Interview.query.order_by(Interview.created_at.desc()).all()
    if role_filter:
        interviews = [i for i in interviews if i.candidate.role == role_filter]

    if recommendation_filter:
        if recommendation_filter == "Unrated":
            interviews = [i for i in interviews if not i.recommendation]
        else:
            interviews = [i for i in interviews if i.recommendation == recommendation_filter]

    skill_scores = average_skill_scores(interviews)
    if sort_filter == "skill_desc":
        interviews = sorted(
            interviews,
            key=lambda i: skill_scores.get(i.id, 0),
            reverse=True,
        )

    ongoing_interviews = [i for i in interviews if i.status != "completed"]
    completed_interviews = [i for i in interviews if i.status == "completed"]
    completed_total_count = len(completed_interviews)
    try:
        completed_page = max(1, int(completed_page))
    except ValueError:
        completed_page = 1
    completed_total_pages = max(1, (completed_total_count + per_page - 1) // per_page)
    if completed_page > completed_total_pages:
        completed_page = completed_total_pages
    completed_start = (completed_page - 1) * per_page
    completed_end = completed_start + per_page
    completed_interviews_page = completed_interviews[completed_start:completed_end]
    question_bank = load_question_bank()
    return render_template(
        "dashboard.html",
        ongoing_interviews=ongoing_interviews,
        completed_interviews=completed_interviews_page,
        completed_total_count=completed_total_count,
        completed_page=completed_page,
        completed_total_pages=completed_total_pages,
        skill_scores=skill_scores,
        default_skills=sorted(question_bank.keys()),
        role_filter=role_filter,
        recommendation_filter=recommendation_filter,
        sort_filter=sort_filter,
        default_roles=DEFAULT_ROLES,
        default_branches=DEFAULT_BRANCHES,
        default_degrees=DEFAULT_DEGREES,
        default_years=DEFAULT_YEARS,
        error=request.args.get("error", ""),
    )


@main_bp.route("/question-bank")
def question_bank():
    bank = load_question_bank()
    return render_template("question_bank.html", question_bank=bank)


@main_bp.route("/question-bank", methods=["POST"])
def add_question_bank():
    skill_existing = request.form.get("skill_existing", "").strip()
    skill_new = request.form.get("skill_new", "").strip()
    if skill_existing == "other":
        skill_existing = ""
    skill = (skill_new or skill_existing).strip()
    questions_raw = request.form.get("questions", "").strip()
    if not skill or not questions_raw:
        return redirect(url_for("main.question_bank"))

    new_questions = [line.strip() for line in questions_raw.split("\n") if line.strip()]
    bank = load_question_bank()
    bank.setdefault(skill, [])
    bank[skill].extend(new_questions)
    bank[skill] = list(dict.fromkeys(bank[skill]))
    save_question_bank(bank)
    return redirect(url_for("main.question_bank"))


@main_bp.route("/question-bank/<string:skill>/delete", methods=["POST"])
def delete_question_bank_skill(skill: str):
    bank = load_question_bank()
    if skill in bank:
        del bank[skill]
        save_question_bank(bank)
    return redirect(url_for("main.question_bank"))


@main_bp.route("/question-bank/<string:skill>/questions/delete", methods=["POST"])
def delete_question_bank_question(skill: str):
    question_text = request.form.get("question", "").strip()
    if not question_text:
        return redirect(url_for("main.question_bank"))
    bank = load_question_bank()
    if skill in bank:
        questions = bank.get(skill, [])
        if question_text in questions:
            questions.remove(question_text)
            bank[skill] = questions
            save_question_bank(bank)
    return redirect(url_for("main.question_bank"))


@main_bp.route("/interviews", methods=["POST"])
def create_interview():
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip().lower()
    branch = request.form.get("branch", "").strip()
    degree = request.form.get("degree", "").strip()
    year = request.form.get("year", "").strip()
    role = request.form.get("role", "").strip()
    custom_role = request.form.get("custom_role", "").strip()
    selected_skills = request.form.getlist("skills")
    custom_skills = request.form.get("custom_skills", "")
    assignment_score = request.form.get("assignment_score")
    assignment_remarks = request.form.get("assignment_remarks", "").strip()
    transcript = request.form.get("transcript", "").strip()

    if role == "other":
        role = custom_role

    if not name or not email or not role or not branch or not degree or not year:
        return redirect(url_for("main.dashboard", error="missing"))

    if not is_valid_email(email):
        return redirect(url_for("main.dashboard", error="invalid_email"))

    if branch not in DEFAULT_BRANCHES:
        return redirect(url_for("main.dashboard", error="invalid_branch"))
    if degree not in DEFAULT_DEGREES:
        return redirect(url_for("main.dashboard", error="invalid_degree"))
    if year not in DEFAULT_YEARS:
        return redirect(url_for("main.dashboard", error="invalid_year"))

    if Candidate.query.filter_by(email=email).first():
        return redirect(url_for("main.dashboard", error="duplicate"))

    candidate = Candidate(
        name=name,
        email=email,
        branch=branch,
        degree=degree,
        year=year,
        role=role,
        skills=",".join(normalize_skills(selected_skills, custom_skills)),
    )
    db.session.add(candidate)
    db.session.flush()

    interview = Interview(
        candidate_id=candidate.id,
        assignment_score=int(assignment_score) if assignment_score else None,
        assignment_remarks=assignment_remarks or None,
        transcript=transcript or None,
        status="ongoing",
    )
    db.session.add(interview)
    db.session.flush()

    selected_skills = normalize_skills(selected_skills, custom_skills)
    if selected_skills:
        bank = load_question_bank()
        updated = False
        for skill in selected_skills:
            if skill not in bank:
                bank[skill] = []
                updated = True
        if updated:
            save_question_bank(bank)

    for question in build_question_set(selected_skills):
        db.session.add(
            Question(
                interview_id=interview.id,
                skill=question["skill"],
                text=question["text"],
            )
        )

    for skill in selected_skills:
        db.session.add(Score(interview_id=interview.id, skill=skill, value=3))

    db.session.commit()
    return redirect(url_for("main.live_interview", interview_id=interview.id))


@main_bp.route("/interviews/<int:interview_id>/live")
def live_interview(interview_id: int):
    interview = _get_or_404(Interview, interview_id)
    questions = Question.query.filter_by(interview_id=interview_id).order_by(Question.skill, Question.id).all()
    grouped_questions: dict[str, list[Question]] = defaultdict(list)
    for question in questions:
        grouped_questions[question.skill].append(question)
    notes = Note.query.filter_by(interview_id=interview_id).order_by(Note.timestamp.desc()).all()
    scores = Score.query.filter_by(interview_id=interview_id).all()
    question_bank = load_question_bank()
    note_skills = sorted({"General", *question_bank.keys(), *[score.skill for score in scores]})
    return render_template(
        "interview.html",
        interview=interview,
        grouped_questions=grouped_questions,
        notes=notes,
        scores=scores,
        note_skills=note_skills,
    )


@main_bp.route("/interviews/<int:interview_id>/summary")
def summary(interview_id: int):
    interview = _get_or_404(Interview, interview_id)
    if interview.status != "completed":
        return render_template(
            "summary.html",
            interview=interview,
            scores=[],
            asked_questions=[],
            blocked=True,
        )

    scores = Score.query.filter_by(interview_id=interview_id).all()
    asked_questions = Question.query.filter_by(interview_id=interview_id, asked=True).all()
    return render_template(
        "summary.html",
        interview=interview,
        scores=scores,
        asked_questions=asked_questions,
        blocked=False,
    )


@main_bp.route("/api/interviews/<int:interview_id>/questions/<int:question_id>", methods=["POST"])
def update_question(interview_id: int, question_id: int):
    interview = _get_or_404(Interview, interview_id)
    if interview.status == "completed":
        return jsonify({"status": "locked"}), 400
    question = Question.query.filter_by(id=question_id, interview_id=interview_id).first_or_404()
    data = request.get_json(force=True)
    if "asked" in data:
        question.asked = bool(data["asked"])
    if "rating" in data and data["rating"] is not None:
        question.rating = int(data["rating"])
    if "note" in data:
        note_value = str(data["note"]).strip()
        question.note = note_value or None
    db.session.commit()
    return jsonify({"status": "ok"})


@main_bp.route("/api/interviews/<int:interview_id>/notes", methods=["GET", "POST"])
def add_note(interview_id: int):
    interview = _get_or_404(Interview, interview_id)
    if request.method == "GET":
        notes = Note.query.filter_by(interview_id=interview_id).order_by(Note.timestamp.desc()).all()
        return jsonify(
            {
                "status": "ok",
                "notes": [
                    {
                        "id": note.id,
                        "skill": note.skill,
                        "tag": note.tag,
                        "text": note.text,
                        "timestamp": note.timestamp.isoformat(),
                    }
                    for note in notes
                ],
            }
        )
    if interview.status == "completed":
        return jsonify({"status": "locked"}), 400
    data = request.get_json(force=True)
    skill = data.get("skill", "General")
    if skill == "other":
        skill = data.get("custom_skill", "").strip() or "General"
    note = Note(
        interview_id=interview_id,
        skill=skill,
        tag=data.get("tag", "Strength"),
        text=data.get("text", "").strip(),
    )
    if not note.text:
        return jsonify({"status": "empty"}), 400
    db.session.add(note)
    bank = load_question_bank()
    if skill and skill not in bank:
        bank[skill] = []
        save_question_bank(bank)
    db.session.commit()
    return jsonify(
        {
            "status": "ok",
            "note": {
                "id": note.id,
                "skill": note.skill,
                "tag": note.tag,
                "text": note.text,
                "timestamp": note.timestamp.isoformat(),
            },
        }
    )


@main_bp.route("/api/interviews/<int:interview_id>/notes/<int:note_id>", methods=["DELETE"])
def delete_note(interview_id: int, note_id: int):
    interview = _get_or_404(Interview, interview_id)
    if interview.status == "completed":
        return jsonify({"status": "locked"}), 400
    note = Note.query.filter_by(id=note_id, interview_id=interview_id).first_or_404()
    db.session.delete(note)
    db.session.commit()
    return jsonify({"status": "ok"})


@main_bp.route("/api/interviews/<int:interview_id>/scores", methods=["POST"])
def update_score(interview_id: int):
    interview = _get_or_404(Interview, interview_id)
    if interview.status == "completed":
        return jsonify({"status": "locked"}), 400
    data = request.get_json(force=True)
    skill = data.get("skill")
    value = int(data.get("value", 0))
    if not skill or value <= 0:
        return jsonify({"status": "invalid"}), 400
    score = Score.query.filter_by(interview_id=interview_id, skill=skill).first()
    if not score:
        score = Score(interview_id=interview_id, skill=skill, value=value)
        db.session.add(score)
    else:
        score.value = value
    db.session.commit()
    return jsonify({"status": "ok"})


@main_bp.route("/api/interviews/<int:interview_id>/generate_summary", methods=["POST"])
def generate_summary(interview_id: int):
    interview = _get_or_404(Interview, interview_id)
    if interview.status != "completed":
        return jsonify({"status": "blocked"}), 400

    scores = Score.query.filter_by(interview_id=interview_id).all()
    asked_questions = Question.query.filter_by(interview_id=interview_id, asked=True).all()

    summary = None
    recommendation = None
    reason = None

    load_dotenv(override=True)
    openrouter_token = os.getenv("OPENROUTER_API_KEY") or current_app.config.get("OPENROUTER_API_KEY")
    openrouter_model = os.getenv("OPENROUTER_MODEL") or current_app.config.get("OPENROUTER_MODEL")
    openrouter_timeout = int(
        os.getenv("OPENROUTER_TIMEOUT") or current_app.config.get("OPENROUTER_TIMEOUT", 30)
    )
    openrouter_site_url = os.getenv("OPENROUTER_SITE_URL") or current_app.config.get("OPENROUTER_SITE_URL")
    openrouter_app_name = os.getenv("OPENROUTER_APP_NAME") or current_app.config.get("OPENROUTER_APP_NAME")
    llm_enabled_env = os.getenv("LLM_ENABLED")
    llm_enabled = (
        llm_enabled_env.lower() == "true"
        if llm_enabled_env is not None
        else current_app.config.get("LLM_ENABLED")
    )

    token = openrouter_token
    model = openrouter_model or "openai/gpt-4o-mini"
    base_url = "https://openrouter.ai/api/v1/chat/completions"
    extra_headers = {}
    if openrouter_site_url:
        extra_headers["HTTP-Referer"] = openrouter_site_url
    if openrouter_app_name:
        extra_headers["X-Title"] = openrouter_app_name
    if not extra_headers:
        extra_headers = None

    if llm_enabled and token:
        try:
            payload = {
                "candidate_name": interview.candidate.name,
                "role": interview.candidate.role,
                "degree": interview.candidate.degree,
                "year": interview.candidate.year,
                "branch": interview.candidate.branch,
                "skills": parse_skills(interview.candidate.skills),
                "scores": [f"- {score.skill}: {score.value}/5" for score in scores],
                "asked_questions": [
                    f"- [{q.skill}] {q.text} | Rating: {q.rating or 'N/A'} | Note: {q.note or 'N/A'}"
                    for q in asked_questions
                ],
                "transcript": interview.transcript or "",
            }
            summary, recommendation, reason = generate_llm_summary(
                payload=payload,
                model=model,
                token=token,
                timeout=openrouter_timeout,
                base_url=base_url,
                extra_headers=extra_headers,
            )
        except Exception:
            current_app.logger.exception("LLM summary generation failed")
            summary = None

    if not summary or not recommendation or not reason:
        bullets, fallback_recommendation, fallback_reason = build_summary(interview)
        if not summary:
            summary = "\n".join(f"- {bullet}" for bullet in bullets)
        recommendation = recommendation or fallback_recommendation
        reason = reason or fallback_reason

    interview.summary = summary
    interview.recommendation = recommendation
    interview.recommendation_reason = reason
    db.session.commit()
    return jsonify(
        {
            "summary": interview.summary,
            "recommendation": recommendation,
            "reason": reason,
        }
    )


@main_bp.route("/interviews/<int:interview_id>/summary", methods=["POST"])
def save_summary(interview_id: int):
    interview = _get_or_404(Interview, interview_id)
    if interview.status != "completed":
        return redirect(url_for("main.summary", interview_id=interview_id))
    interview.summary = request.form.get("summary", "").strip()
    interview.recommendation = request.form.get("recommendation", "").strip()
    interview.recommendation_reason = request.form.get("recommendation_reason", "").strip()
    db.session.commit()
    return redirect(url_for("main.summary", interview_id=interview_id))


@main_bp.route("/interviews/<int:interview_id>/end", methods=["POST"])
def end_interview(interview_id: int):
    interview = _get_or_404(Interview, interview_id)
    if interview.status != "completed":
        interview.status = "completed"
        interview.ended_at = datetime.now(timezone.utc)
        db.session.commit()
    return redirect(url_for("main.live_interview", interview_id=interview_id))


@main_bp.route("/interviews/<int:interview_id>/export")
def export_interview(interview_id: int):
    interview = _get_or_404(Interview, interview_id)
    candidate = interview.candidate
    questions = Question.query.filter_by(interview_id=interview_id).all()
    notes = Note.query.filter_by(interview_id=interview_id).all()
    scores = Score.query.filter_by(interview_id=interview_id).all()

    payload = {
        "candidate": {
            "name": candidate.name,
            "email": candidate.email,
            "branch": candidate.branch,
            "degree": candidate.degree,
            "year": candidate.year,
            "role": candidate.role,
            "skills": parse_skills(candidate.skills),
        },
        "interview": {
            "id": interview.id,
            "created_at": interview.created_at.isoformat(),
            "assignment_score": interview.assignment_score,
            "assignment_remarks": interview.assignment_remarks,
            "transcript": interview.transcript,
            "summary": interview.summary,
            "recommendation": interview.recommendation,
            "recommendation_reason": interview.recommendation_reason,
        },
        "questions": [
            {
                "skill": q.skill,
                "text": q.text,
                "asked": q.asked,
                "rating": q.rating,
            }
            for q in questions
        ],
        "notes": [
            {
                "skill": n.skill,
                "tag": n.tag,
                "text": n.text,
                "timestamp": n.timestamp.isoformat(),
            }
            for n in notes
        ],
        "scores": [
            {"skill": s.skill, "value": s.value, "comment": s.comment}
            for s in scores
        ],
    }

    from .services import ROOT_DIR

    export_path = ROOT_DIR / f"interview_{interview_id}.json"
    export_path.write_text(
        jsonify(payload).get_data(as_text=True),
        encoding="utf-8",
    )
    return send_file(export_path, as_attachment=True)


@main_bp.route("/interviews/<int:interview_id>/export/pdf")
def export_interview_pdf(interview_id: int):
    interview = _get_or_404(Interview, interview_id)
    candidate = interview.candidate
    questions = Question.query.filter_by(interview_id=interview_id).all()
    asked_questions = [question for question in questions if question.asked]
    notes = Note.query.filter_by(interview_id=interview_id).all()
    scores = Score.query.filter_by(interview_id=interview_id).all()

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=12)
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)

    def _sanitize_pdf_text(text: str) -> str:
        return text.encode("latin-1", errors="replace").decode("latin-1")

    def write_line(text: str, bold: bool = False):
        pdf.set_font("Helvetica", style="B" if bold else "", size=12)
        pdf.multi_cell(0, 8, _sanitize_pdf_text(text))

    write_line("Interview Report", bold=True)
    write_line(f"Candidate: {candidate.name}")
    write_line(f"Email: {candidate.email}")
    write_line(f"Branch: {candidate.branch}")
    write_line(f"Degree: {candidate.degree}")
    write_line(f"Year: {candidate.year}")
    write_line(f"Role: {candidate.role}")
    write_line(f"Skills: {candidate.skills}")
    write_line("")

    write_line("Assignment Results:", bold=True)
    write_line(f"Score: {interview.assignment_score if interview.assignment_score is not None else 'N/A'}")
    write_line(f"Remarks: {interview.assignment_remarks or 'N/A'}")
    write_line("")

    write_line("Skill Scores:", bold=True)
    for score in scores:
        write_line(f"- {score.skill}: {score.value}/5")
    write_line("")

    write_line("Notes:", bold=True)
    for note in notes:
        write_line(f"- [{note.tag}] {note.skill}: {note.text}")
    write_line("")

    write_line("Asked Questions:", bold=True)
    if asked_questions:
        for question in asked_questions:
            rating = question.rating if question.rating is not None else "N/A"
            note = question.note or ""
            suffix = f" Rating: {rating}" if rating != "N/A" else ""
            note_text = f" Note: {note}" if note else ""
            write_line(f"- {question.skill}: {question.text}.{suffix}{note_text}")
    else:
        write_line("No asked questions recorded.")
    write_line("")

    write_line("Summary:", bold=True)
    summary_text = interview.summary or "N/A"
    for line in summary_text.split("\n"):
        write_line(line)
    write_line("")

    write_line("Recommendation:", bold=True)
    write_line(f"Decision: {interview.recommendation or 'N/A'}")
    write_line(f"Justification: {interview.recommendation_reason or 'N/A'}")

    buffer = BytesIO(pdf.output(dest="S").encode("latin-1"))
    return send_file(
        buffer,
        as_attachment=True,
        download_name=f"interview_{interview_id}.pdf",
        mimetype="application/pdf",
    )
