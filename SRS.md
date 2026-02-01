# Software Requirements Specification (SRS)

Project: AI Interview Support
Date: January 26, 2026
Version: 0.1.0

## 1. Purpose
Define detailed requirements for v0.1.0 of the AI Interview Support web app. This document converts the v0.1.0 backlog and test expectations into explicit, testable requirements.

## 2. Scope
The system supports:
- Capturing candidate details
- Conducting a live interview session with question navigation and interviewer notes
- Managing a question bank with skill taxonomy
- Generating a summary report for completed interviews
- Listing recent interviews with filters and sorting

Out of scope for v0.1.0:
- Export/download of reports
- Role-based access control
- Offline mode
- Advanced analytics dashboards

## 3. Stakeholders
- Interviewers (primary users)
- Hiring managers (review summaries)
- Admins (manage question bank and skills)

## 4. Assumptions and Constraints
- The app is web-based with server-side persistence.
- Interview sessions are created from candidate profiles.
- Skills are shared across the question bank and interview notes.
- A question can belong to a single skill for v0.1.0.

## 5. Functional Requirements

### 5.1 Main Page: Candidate Details
FR-1: The candidate details form SHALL require name, email, and role.
FR-2: The branch/department field SHALL be a controlled input (dropdown or autocomplete from predefined values).
FR-3: The system SHALL prevent duplicate candidate creation by email.
FR-4: The system SHALL show inline validation errors for missing required fields and invalid email format.
FR-5: The system SHALL allow users to cancel/back without saving.

### 5.2 Interview State on Main Page
FR-6: The main page SHALL display two sections: Ongoing Interviews and Completed Interviews.
FR-7: Completed interviews SHALL be read-only (no resume, no edit candidate details).
FR-8: Ongoing interviews SHALL provide a resume action.

### 5.3 Live Interview Flow
FR-9: Starting an interview from a candidate profile SHALL create a new interview session.
FR-10: A live interview timer SHALL be visible and update in real time once the session starts.
FR-11: The user SHALL have an explicit action to end the interview.
FR-12: On end interview, the system SHALL mark the interview as completed and lock further edits to candidate details.

### 5.4 Questions Section
FR-13: Questions SHALL be grouped by skill in the interview UI.
FR-14: The UI SHALL support navigation for large question sets (e.g., collapsible groups or pagination).
FR-15: Answering a question and moving to the next SHALL persist the response.
FR-16: Each asked question SHALL include an interviewer note field.
FR-17: Notes SHALL be persisted per question and restored when the interview is reopened.

### 5.5 Notes Section (Skills)
FR-18: The notes section SHALL provide a dropdown of existing skills.
FR-19: The notes section SHALL include an `other` option that allows custom skill entry.
FR-20: Custom skills entered via `other` SHALL be stored and become selectable in future sessions.

### 5.6 Recent Interviews Section
FR-21: The recent interviews list SHALL support filtering by role.
FR-22: The recent interviews list SHALL support filtering by recommendation (Hire, No Hire, Borderline).
FR-23: The recent interviews list SHALL support sorting by skill level (High to Low).
FR-24: The recent interviews list SHALL show a skill score beside each candidate name.

### 5.7 Question Bank Editor
FR-25: The question editor SHALL allow selecting an existing skill for a question.
FR-26: The question editor SHALL allow entering a new skill name if it does not exist.
FR-27: Newly added skill names SHALL appear in the existing skills list.

### 5.8 Summary Generation
FR-28: A summary SHALL be available only for completed interviews.
FR-29: The summary SHALL include only asked questions.
FR-30: The summary SHALL include the interviewer note for each asked question.

## 6. Data Requirements
DR-1: Candidate entities SHALL store name, email, role, and branch/department.
DR-2: Interview entities SHALL store status (ongoing/completed), start time, end time, and timer duration.
DR-3: Question entities SHALL store text, skill, and any metadata used for grouping.
DR-4: Interview responses SHALL store answer and interviewer note per question.
DR-5: Skill entities SHALL support both predefined and custom values.

## 7. UI/UX Requirements
UR-1: Form fields SHALL display inline validation errors near the related input.
UR-2: The live timer SHALL be clearly visible during interviews.
UR-3: Question groups by skill SHALL be visually distinct and navigable.
UR-4: Recent interviews filters and sorting controls SHALL be visible above the list.
UR-5: Completed interviews SHALL be visually labeled as read-only.

## 8. Non-Functional Requirements
NFR-1: The UI SHALL remain responsive with large question banks (100+ questions).
NFR-2: Data changes (answers/notes) SHALL persist within 2 seconds of user action.
NFR-3: The system SHALL prevent inconsistent branch/department values.

## 9. Acceptance Criteria Summary (Derived from Tests)
- Controlled branch/department input; no inconsistent free-text.
- Timer starts on interview begin; end interview marks completion.
- Questions grouped by skill with scalable navigation.
- Interviewer notes per asked question are persisted and shown in summary.
- Skills dropdown includes `other` and persists new skills.
- Recent interviews filter by role/recommendation and sort by skill level.
- Summary includes only asked questions and notes; blocked if interview incomplete.
- Main page separates ongoing and completed interviews.

## 10. Open Questions
- What is the canonical list of branch/department values?
- How is skill score computed and stored?
- What are the rules for required questions before ending an interview?
