# HyperPredict — Team Task Tracker

This is the initial task plan for the NHANES dataset review. Task owners are identified by their GitHub usernames where applicable. Update status only when there is evidence/output to review.

**Statuses:** Todo · In Progress · Review · Done

## Immediate milestone: dataset review for the instructor

| ID | Task | Owner | Status | Deliverable / acceptance check |
|---|---|---|---|---|
| HP-01 | Read the NHANES cycle documentation and confirm candidate files | @SaraMAlshaye | Review | Notes include cycle, source links, variable names, units, and limitations |
| HP-02 | Verify whether SpO₂ is available in the same cycle; do not assume it is | @mashaelalmojally | Review | Documented yes/no/uncertain result with official source |
| HP-03 | Download candidate files locally and inspect columns, row counts, and SEQN uniqueness | @saaraaldayel | Review | Data inventory; no raw data committed to GitHub |
| HP-04 | Define the proposed prediction target and identify possible target leakage | @SaraMAlshaye + @mashaelalmojally | Review | Written target definition and list of features to exclude/test |
| HP-05 | Merge selected files using SEQN and report row counts/missingness after merge | @mashaelalmojally + @saaraaldayel | Review | Reproducible script and summary table |
| HP-06 | Create initial EDA charts and a short findings note | @SaraMAlshaye | Review | At least target/measurement distributions where valid, missingness summary, limitations |
| HP-07 | Update README and keep this tracker current | @SaraMAlshaye | Review | Source and dataset status documented; tasks have owners/status |
| HP-08 | Prepare a brief progress summary for the instructor | All team members | Todo | Explain dataset choice, validation still needed, work completed, and next steps |
| HP-09 | Train and compare models; select one; connect the app | @SaraMAlshaye | Review | docs/MODEL.md, results/reports/model_evaluation.md, app loads the saved model |
| HP-10 | Prepare app for Arduino/ESP32 + MAX30102 (software side); remove income input | @SaraMAlshaye | Review | iot/README.md, 57 passing tests; hardware bring-up and pulse compatibility study still open |
| HP-11 | Remove waist circumference; retrain 3 models (model v3, 5 features) | @SaraMAlshaye | Review | docs/MODEL.md v3 results, 57 passing tests |

### Pipeline evidence for review (all in docs/DATASET.md)

- HP-01: sources, files, variables and units are documented in docs/DATASET.md §1.
- HP-02: SpO2 result is **No**. No NHANES 2021–2023 exam file contains it. Pulse comes from the BP cuff.
- HP-03: data_analysis/download_nhanes.py downloads the files. Row counts match the codebooks and there are 0 duplicate SEQN values.
- HP-04: target is the NCHS Data Brief 511 definition (BP ≥130/80 or BP medication). The leakage exclusion list is in §5.
- HP-05: data_analysis/merge_nhanes.py merges the files and writes the row log to results/reports/merge_log.json.
- HP-06: data_analysis/eda.py produces 8 figures and results/reports/eda_summary.md.

Each item moves to Done after another team member checks it.

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
