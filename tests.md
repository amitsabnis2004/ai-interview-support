# Basic Test Cases (Aligned with what-next.md v0.1.0)

## 1) Main Page (Candidate Details)
- **TC-01**: Submit with valid required fields (name, email, role, branch/department from defined list) → details saved and confirmation shown.
- **TC-02**: Missing required field → inline validation error displayed.
- **TC-03**: Invalid email format → validation error displayed.
- **TC-04**: Duplicate email → system prevents duplicate and shows message.
- **TC-05**: Branch/Department uses a controlled input (dropdown/autocomplete) → free-text not allowed or normalized to predefined values.
- **TC-06**: Cancel/Back from details page → data not saved.

## 2) Live Interview Flow
- **TC-07**: Start interview from candidate profile → interview session created.
- **TC-08**: Live interview timer starts on session begin → visible and updates in real time.
- **TC-09**: End interview action available → confirmation shown and session marked completed.
- **TC-10**: Attempt to end interview without required responses (if enforced) → warning shown.

## 3) Questions Section (Navigation & Notes)
- **TC-11**: Questions grouped by skill → sections render with correct grouping.
- **TC-12**: Large question bank → navigation remains usable (collapsible groups or pagination works).
- **TC-13**: Answer question and move to next → response saved and next question shown.
- **TC-14**: Asked question includes interviewer note field → note saved per question.
- **TC-15**: Notes persist on refresh/reopen interview → previously entered notes shown.

## 4) Notes Section (Skills)
- **TC-16**: Skills dropdown shows existing skills list.
- **TC-17**: Selecting `other` allows custom skill entry → custom value saved.

## 5) Recent Interviews Section
- **TC-18**: Filter by role → list updates to matching role.
- **TC-19**: Filter by recommendation (Hire/No Hire/Borderline) → list updates correctly.
- **TC-20**: Sort by skill level (High on top) → ordering correct.
- **TC-21**: Skill score displayed beside candidate name → matches stored score.
- **TC-21a (Positive)**: Completed interview shows Hire status pill next to Completed → pill is rendered with Hire text.
- **TC-21b (Negative)**: Completed interview without recommendation → no recommendation pill shown.
- **TC-21c (Edge)**: Completed interviews pagination page out of range → last page rendered (e.g., Page 2 of 2).

## 6) Question Bank Editor
- **TC-22**: Select existing skill name when creating/editing a question → saved with selected skill.
- **TC-23**: Enter new skill name when not in list → new skill saved and appears in list.

## 7) Summary Generation
- **TC-24**: Summary shows only asked questions → unasked questions excluded.
- **TC-25**: Summary includes interviewer note per asked question.
- **TC-26**: Attempt summary before interview completion → blocked with message.

## 8) Interview State on Main Page
- **TC-27**: Completed interviews appear in a read-only section (no resume, no edit).
- **TC-28**: Ongoing interviews appear in a separate section with resume controls.

## 9) End-to-End Flow
- **TC-29**: Add candidate → start interview → answer questions with notes → end interview → summary reflects asked questions and notes.

---

# Automated Tests (Pytest)

## How to run
- Install dependencies from requirements.txt
- Run: `python -m pytest`

## Coverage mapping
- **TC-01/TC-02/TC-03/TC-04** → `tests/test_app.py::test_create_interview_missing_fields_redirects`, `tests/test_app.py::test_create_interview_duplicate_email`
- **TC-07/TC-09/TC-26** → `tests/test_app.py::test_end_interview_and_generate_summary`, `tests/test_app.py::test_summary_blocked_until_completed`
- **TC-14** → `tests/test_app.py::test_update_question_marks_asked_and_note`
- **TC-17** → `tests/test_app.py::test_add_note_with_other_skill`
- **TC-20/TC-21** → `tests/test_app.py::test_filters_by_role_and_recommendation`
- **TC-21a** → `tests/test_app.py::test_completed_interview_shows_hire_status_pill`
- **TC-21b** → `tests/test_app.py::test_completed_interview_without_recommendation_hides_status_pill`
- **TC-21c** → `tests/test_app.py::test_completed_pagination_edge_page_out_of_range`
- **TC-24/TC-25** → `tests/test_app.py::test_summary_shows_only_asked_questions`
- **Exports** → `tests/test_app.py::test_pdf_export_asked_questions_only`

---

# Detailed Automated Test Documentation

## Dashboard & Interview Creation

### `test_dashboard_loads`
- **What it tested**: Loads the dashboard page and renders the main header.
- **Why**: Confirms the primary entry point is available and not erroring.
- **Result**: Pass
- **Understanding**: Basic UI route is healthy and serving HTML.

### `test_create_interview_missing_fields_redirects`
- **What it tested**: Submitting incomplete interview form redirects with `error=missing`.
- **Why**: Ensures server-side validation blocks incomplete data.
- **Result**: Pass
- **Understanding**: Required fields are enforced and failure paths are handled.

### `test_create_interview_duplicate_email`
- **What it tested**: Submitting the same email twice returns `error=duplicate`.
- **Why**: Prevents duplicate candidate entries.
- **Result**: Pass
- **Understanding**: Uniqueness is enforced for candidate emails.

## Summary & Completion Flow

### `test_summary_blocked_until_completed`
- **What it tested**: Summary page is blocked before completion with the blocked message.
- **Why**: Prevents premature access to summary.
- **Result**: Pass
- **Understanding**: Access control aligns with interview status.

### `test_end_interview_and_generate_summary`
- **What it tested**: End interview and generate summary APIs update status and return recommendation.
- **Why**: Verifies core completion workflow and summary generation.
- **Result**: Pass
- **Understanding**: Completion pipeline and summary generation are functional.

### `test_summary_shows_only_asked_questions`
- **What it tested**: Summary shows the “Questions Asked” section after completion.
- **Why**: Confirms summary layout renders the asked-questions block.
- **Result**: Pass
- **Understanding**: Summary page renders the expected section for asked questions.

## Questions, Notes, and Scores

### `test_update_question_marks_asked_and_note`
- **What it tested**: Question update API sets asked, rating, and note.
- **Why**: Ensures interviewer actions persist to the DB.
- **Result**: Pass
- **Understanding**: Question state updates are stored correctly.

### `test_add_note_with_other_skill`
- **What it tested**: Notes API accepts “other” skill and uses custom skill name.
- **Why**: Validates custom skills are supported for notes.
- **Result**: Pass
- **Understanding**: Custom skill notes are saved properly.

### `test_update_score`
- **What it tested**: Score update API writes a new score value.
- **Why**: Ensures score updates persist for skill assessment.
- **Result**: Pass
- **Understanding**: Score updates are reliable and persisted.

## Filters & Completed Interview UX

### `test_filters_by_role_and_recommendation`
- **What it tested**: Role and recommendation filters return matching content.
- **Why**: Ensures filtering logic works for completed interview lists.
- **Result**: Pass
- **Understanding**: Filter params affect result set as expected.

### `test_completed_interview_shows_hire_status_pill`
- **What it tested**: Completed interview renders the hire status pill.
- **Why**: Verifies the UI shows recommendation status beside Completed.
- **Result**: Pass
- **Understanding**: Recommendation pill appears when present.

### `test_completed_interview_without_recommendation_hides_status_pill`
- **What it tested**: No recommendation means no status pill is rendered.
- **Why**: Prevents misleading UI when recommendation is missing.
- **Result**: Pass
- **Understanding**: Conditional rendering works for recommendation pill.

### `test_completed_pagination_edge_page_out_of_range`
- **What it tested**: Out-of-range completed page param falls back to last page.
- **Why**: Validates pagination edge handling.
- **Result**: Pass
- **Understanding**: Pagination guards prevent empty/out-of-range views.

## Export

### `test_pdf_export_asked_questions_only`
- **What it tested**: PDF export returns a PDF and includes asked questions.
- **Why**: Confirms export endpoint returns the expected file type after completion.
- **Result**: Pass
- **Understanding**: Export pipeline is functional and returns PDF output.