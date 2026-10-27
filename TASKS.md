# HyperPredict — Team Task Tracker

This is the initial task plan for the NHANES dataset review. Task owners are identified by their GitHub usernames where applicable. Update status only when there is evidence/output to review.

**Statuses:** Todo · In Progress · Review · Done

## Immediate milestone: dataset review for the instructor

| ID | Task | Owner | Status | Deliverable / acceptance check |
|---|---|---|---|---|
| HP-01 | Read the NHANES cycle documentation and confirm candidate files | @SaraMAlshaye | In Progress | Notes include cycle, source links, variable names, units, and limitations |
| HP-02 | Verify whether SpO₂ is available in the same cycle; do not assume it is | @mashaelalmojally | Todo | Documented yes/no/uncertain result with official source |
| HP-03 | Download candidate files locally and inspect columns, row counts, and SEQN uniqueness | @saaraaldayel | Todo | Data inventory; no raw data committed to GitHub |
| HP-04 | Define the proposed prediction target and identify possible target leakage | @SaraMAlshaye + @mashaelalmojally | Todo | Written target definition and list of features to exclude/test |
| HP-05 | Merge selected files using SEQN and report row counts/missingness after merge | @mashaelalmojally + @saaraaldayel | Todo | Reproducible script and summary table |
| HP-06 | Create initial EDA charts and a short findings note | @SaraMAlshaye | Todo | At least target/measurement distributions where valid, missingness summary, limitations |
| HP-07 | Update README and keep this tracker current | @SaraMAlshaye | In Progress | Source and dataset status documented; tasks have owners/status |
| HP-08 | Prepare a brief progress summary for the instructor | All team members | Todo | Explain dataset choice, validation still needed, work completed, and next steps |

## Workstream ownership (provisional)

- **@SaraMAlshaye — Data audit & documentation:** source documentation, data inventory, data-quality report, and README.
- **@mashaelalmojally — Dataset validation & preparation:** variable availability, merge plan, missing-data checks, and reproducible preprocessing.
- **@saaraaldayel — Exploratory analysis & prototype readiness:** initial EDA outputs, charts, and documenting what the future app needs from a trained model.

These workstreams are provisional and should be balanced after the first data inventory. All members should review the target definition and leakage risk together.

## Definition of done

A task is Done only when:
1. The requested file, script, or result exists.
2. The result has been checked by another team member when appropriate.
3. Relevant source links and assumptions are documented.
4. No secrets, credentials, or unapproved raw health data are committed.

## Dataset safeguards

- NHANES is a candidate dataset until the team verifies required variables in one compatible cycle.
- Verify SpO₂ availability from official documentation; do not infer it from blood pressure/pulse availability.
- Merge participant-level files with the documented participant identifier (SEQN) and check duplicate IDs and row counts.
- If a target is derived from blood-pressure measurements, assess target leakage before training.
- Do not commit raw data by default. Keep it local and document official download instructions.
- This is an educational project, not a clinical diagnostic tool.

## GitHub Project board

If a GitHub Projects board is available, create fields:
- **Status:** Todo, In Progress, Review, Done
- **Owner:** team member
- **Priority:** High, Medium, Low
- **Milestone:** Instructor check-in / Data validation / Modeling / Prototype

Create one Issue per task above if the team wants issue-level assignment and progress tracking.
