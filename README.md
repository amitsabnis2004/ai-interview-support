# AI-Assisted Technical Interview Companion

A web-based interview companion that standardizes question flow, structured notes, skill scoring, and summary generation for technical interviews.

This README is the primary project document. It consolidates the plan, requirements, architecture, tests, and roadmap from:
- [PRODUCT_SPEC.md](PRODUCT_SPEC.md)
- [SRS.md](SRS.md)
- [architecture.md](architecture.md)
- [project_plan.md](project_plan.md)
- [tests.md](tests.md)
- [what-next.md](what-next.md)
- [llm.md](llm.md)

## 1) Product overview
The application helps interviewers run consistent interviews, capture structured evidence, and produce standardized summaries with a hire recommendation. It is built with Flask, SQLite, and SQLAlchemy, with a lightweight HTML/CSS/JS frontend.

## 2) Goals and non-goals
### Goals
- Standardize questions and scoring per role/skill.
- Reduce interviewer cognitive load during live interviews.
- Produce clear, editable summaries with evidence-based rationale.
- Minimize bias with structured inputs and rubric-based scoring.

### Non-goals (MVP)
- Automated candidate rejection or autonomous decisions.
- Personality/emotion/voice/video analysis.
- Multi-user collaboration.
- ATS integrations.

## 3) User journey
1. Pre-interview setup
   - Select role and skill set
   - Load standard question bank
   - Capture candidate profile
2. Live interview
   - Ask questions and rate answers (1–5)
   - Add tagged notes (Strength, Weakness, Red Flag)
   - Update skill scores
3. Post-interview
   - Generate summary + recommendation
   - Edit summary and justification
   - Export JSON/PDF report

## 4) Architecture and system design
High-level components:
- UI: Dashboard, Live Interview, Summary & Results
- API: Flask routes + SQLAlchemy ORM
- Data: SQLite database + JSON/PDF exports
- Summary: rule-based fallback + optional LLM adapter

Diagrams and flows are documented in [architecture.md](architecture.md).

## 5) Functional requirements (summary)
Derived from [SRS.md](SRS.md):
- Candidate details validate required fields and email format.
- Branch/department is controlled input from predefined values.
- Duplicate candidate emails are prevented.
- Live interview supports timer and explicit end.
- Questions are grouped by skill and include notes per asked question.
- Notes allow existing skills and an `other` option for custom skills.
- Summary is available only after completion and includes asked questions only.
- Recent interviews support filtering by role/recommendation and sorting by skill level.

## 6) Data model (minimal)
From [PRODUCT_SPEC.md](PRODUCT_SPEC.md):
- Candidate: name, email, branch, degree, year, role, skills
- Interview: status, created/ended timestamps, assignment results, transcript, summary, recommendation
- Question: skill, text, asked, rating, note
- Note: skill, tag, text, timestamp
- Score: skill, value

## 7) Summary generation
Two-stage approach:
1) Rule-based fallback (deterministic)
   - Highlights top strengths and weaknesses from scores and notes
   - Adds assignment remarks if present
   - Produces 4–6 evidence-based bullets
2) LLM (optional)
   - Uses structured prompt and JSON parsing
   - Output is editable

LLM integration is configured via OpenRouter. See [llm.md](llm.md) for setup.

Required environment variables in .env:
- LLM_ENABLED=true
- OPENROUTER_API_KEY=your_key_here
- OPENROUTER_MODEL=openai/gpt-4o-mini
- OPENROUTER_TIMEOUT=30
- OPENROUTER_SITE_URL=https://your-domain-or-localhost
- OPENROUTER_APP_NAME=Interview Companion

## 8) Project plan (MVP)
From [project_plan.md](project_plan.md):
- M1: Discovery & Spec
- M2: UI Skeleton
- M3: Core Functionality
- M4: Summary Generation
- M5: Export & Polish

## 9) Testing strategy
Automated tests are defined in [tests.md](tests.md) and implemented in tests/test_app.py.

Run tests:
- python -m pytest

Coverage highlights:
- Candidate creation validation and duplicate prevention
- Interview completion + summary generation
- Notes persistence and deletion
- Filters and sorting in the dashboard
- Pagination edges for completed interviews
- Question bank question deletion
- PDF export for asked questions

See [tests.md](tests.md) for detailed test cases, classification, and coverage mapping.

## 10) Local setup
1. Create a virtual environment
2. Install dependencies from requirements.txt
3. Configure .env (optional for LLM)
4. Run app.py and open the dashboard URL printed in the console

## 11) Docker
The Dockerfile provides a single-container setup with SQLite persistence. Mount a volume if you want to persist interviews.db outside the container.

## 12) Project structure
- app.py: Flask entrypoint
- app/: application package (routes, models, services)
- app/templates/: HTML templates
- app/static/: CSS styles
- question_bank.json: default question bank
- interviews.db: SQLite database (auto-generated)
- Dockerfile: container build

## 13) Roadmap and future plans
From [what-next.md](what-next.md):
- v0.1.0: controlled inputs, live timer, grouped questions, asked question notes, filtering and sorting, summary rules
- v0.1.1: custom role only on other selection, question bank counts
- v0.1.2: paging for completed interviews, Calibri font, smoother colors and shapes
- LLM: improve parsing and handle provider limits

From [PRODUCT_SPEC.md](PRODUCT_SPEC.md):
- Role templates and rubric customization
- Multi-interviewer support
- ATS export
- Analytics dashboard
- Move SQLite to managed DB for multi-user deployments

## 14) References
- [PRODUCT_SPEC.md](PRODUCT_SPEC.md)
- [SRS.md](SRS.md)
- [architecture.md](architecture.md)
- [project_plan.md](project_plan.md)
- [tests.md](tests.md)
- [what-next.md](what-next.md)
- [llm.md](llm.md)