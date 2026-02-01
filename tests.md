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
- **TC-17a (Positive)**: GET notes API returns notes ordered by most recent first.
- **TC-17b (Positive)**: Delete note succeeds for ongoing interview.
- **TC-17c (Negative)**: Delete note blocked when interview is completed.

## 5) Recent Interviews Section
- **TC-18**: Filter by role → list updates to matching role.
- **TC-19**: Filter by recommendation (Hire/No Hire/Borderline) → list updates correctly.
- **TC-20**: Sort by skill level (High on top) → ordering correct.
- **TC-21**: Skill score displayed beside candidate name → matches stored score.
- **TC-21a (Positive)**: Completed interview shows Hire status pill next to Completed → pill is rendered with Hire text.
- **TC-21b (Negative)**: Completed interview without recommendation → no recommendation pill shown.
- **TC-21c (Edge)**: Completed interviews pagination page out of range → last page rendered (e.g., Page 2 of 2).
- **TC-21d (Edge)**: Completed interviews pagination invalid page (non-numeric) → defaults to first page.

## 6) Question Bank Editor
- **TC-22**: Select existing skill name when creating/editing a question → saved with selected skill.
- **TC-23**: Enter new skill name when not in list → new skill saved and appears in list.
- **TC-23a (Positive)**: Delete a specific question from a skill → only that question is removed.
- **TC-23b (Negative)**: Delete a missing question → no changes to the list.

## 7) Summary Generation
- **TC-24**: Summary shows only asked questions → unasked questions excluded.
- **TC-25**: Summary includes interviewer note per asked question.
- **TC-26**: Attempt summary before interview completion → blocked with message.
- **TC-26a (Edge)**: Generate summary with LLM disabled → fallback summary, recommendation, and reason returned.

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
- **TC-17a** → `tests/test_app.py::test_get_notes_returns_ordered_list`
- **TC-17b** → `tests/test_app.py::test_delete_note_success`
- **TC-17c** → `tests/test_app.py::test_delete_note_locked_when_completed`
- **TC-20/TC-21** → `tests/test_app.py::test_filters_by_role_and_recommendation`
- **TC-21a** → `tests/test_app.py::test_completed_interview_shows_hire_status_pill`
- **TC-21b** → `tests/test_app.py::test_completed_interview_without_recommendation_hides_status_pill`
- **TC-21c** → `tests/test_app.py::test_completed_pagination_edge_page_out_of_range`
- **TC-21d** → `tests/test_app.py::test_completed_pagination_invalid_page_defaults`
- **TC-24/TC-25** → `tests/test_app.py::test_summary_shows_only_asked_questions`
- **TC-26a** → `tests/test_app.py::test_generate_summary_returns_fallback_when_llm_disabled`
- **Exports** → `tests/test_app.py::test_pdf_export_asked_questions_only`

---

# Detailed Automated Test Documentation

## Classification (Positive / Negative / Edge)

### Positive
- **TC-01**, **TC-07**, **TC-08**, **TC-09**, **TC-11**, **TC-12**, **TC-13**, **TC-14**, **TC-15**, **TC-16**, **TC-17**, **TC-17a**, **TC-17b**, **TC-18**, **TC-19**, **TC-20**, **TC-21**, **TC-21a**, **TC-22**, **TC-23**, **TC-23a**, **TC-24**, **TC-25**, **TC-27**, **TC-28**, **TC-29**

### Negative
- **TC-02**, **TC-03**, **TC-04**, **TC-10**, **TC-17c**, **TC-21b**, **TC-23b**, **TC-26**

### Edge
- **TC-21c**, **TC-21d**, **TC-26a**

### Automated Test Classification (by test name)
| Test | Classification |
| --- | --- |
| test_dashboard_loads | Positive |
| test_create_interview_missing_fields_redirects | Negative |
| test_create_interview_duplicate_email | Negative |
| test_summary_blocked_until_completed | Negative |
| test_end_interview_and_generate_summary | Positive |
| test_summary_shows_only_asked_questions | Positive |
| test_update_question_marks_asked_and_note | Positive |
| test_add_note_with_other_skill | Positive |
| test_get_notes_returns_ordered_list | Positive |
| test_delete_note_success | Positive |
| test_delete_note_locked_when_completed | Negative |
| test_update_score | Positive |
| test_filters_by_role_and_recommendation | Positive |
| test_completed_interview_shows_hire_status_pill | Positive |
| test_completed_interview_without_recommendation_hides_status_pill | Negative |
| test_completed_pagination_edge_page_out_of_range | Edge |
| test_completed_pagination_invalid_page_defaults | Edge |
| test_delete_question_bank_question | Positive |
| test_delete_question_bank_question_missing_no_change | Negative |
| test_generate_summary_returns_fallback_when_llm_disabled | Edge |
| test_pdf_export_asked_questions_only | Positive |

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

### `test_get_notes_returns_ordered_list`
- **What it tested**: Notes API returns notes in reverse chronological order.
- **Why**: Ensures newest notes show first in the UI.
- **Result**: Pass
- **Understanding**: Notes ordering is consistent for live review.

### `test_delete_note_success`
- **What it tested**: DELETE note API removes a note for an ongoing interview.
- **Why**: Confirms notes can be cleaned up during live interviews.
- **Result**: Pass
- **Understanding**: Note deletion works and updates the list.

### `test_delete_note_locked_when_completed`
- **What it tested**: DELETE note API blocks changes once interview is completed.
- **Why**: Prevents edits in a locked interview state.
- **Result**: Pass
- **Understanding**: Notes are immutable after completion.

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

### `test_completed_pagination_invalid_page_defaults`
- **What it tested**: Non-numeric completed page parameter defaults to page 1.
- **Why**: Ensures invalid inputs don’t break paging behavior.
- **Result**: Pass
- **Understanding**: Pagination defaults keep the UI stable.

## Export

### `test_pdf_export_asked_questions_only`
- **What it tested**: PDF export returns a PDF and includes asked questions.
- **Why**: Confirms export endpoint returns the expected file type after completion.
- **Result**: Pass
- **Understanding**: Export pipeline is functional and returns PDF output.

## Question Bank

### `test_delete_question_bank_question`
- **What it tested**: Deleting a specific question removes only that question.
- **Why**: Allows fine-grained cleanup of the question bank.
- **Result**: Pass
- **Understanding**: Per-question delete behaves correctly.

### `test_delete_question_bank_question_missing_no_change`
- **What it tested**: Deleting a non-existent question leaves the list intact.
- **Why**: Ensures safe handling of invalid delete requests.
- **Result**: Pass
- **Understanding**: Question bank remains consistent on invalid deletes.

## Summary Fallback

### `test_generate_summary_returns_fallback_when_llm_disabled`
- **What it tested**: Summary generation returns fallback output when LLM is disabled.
- **Why**: Ensures summary still works without external LLM.
- **Result**: Pass
- **Understanding**: Fallback summary pipeline is functional.