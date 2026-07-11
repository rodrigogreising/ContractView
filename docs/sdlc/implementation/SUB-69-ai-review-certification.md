# SUB-69 AI Review And Executable Certification Evidence

Status: In Progress

## Purpose

SUB-69 corrects the REC-03 review policy so ContractView can execute the
backlog autonomously without treating human code review as a universal gate.
Applicable `cv-review-*` skills review the immutable PR diff, while executable
evidence proves the changed behavior or governing policy works.

## Change Boundary

- Branch: `codex/sub-69-ai-review-certification`
- Base SHA: `08ae4ffef3f2ef386473149b596b6a5abbc147d8`
- Controlling issue: `SUB-69`
- Project stage: `Design Review`
- Runtime application behavior, database schema, and Journey 11 behavior are
  unchanged.

## Certification Standard

Every issue manifest declares:

- whether runtime or user-visible behavior changed;
- the evidence kinds needed for that change;
- how each risk and gate label is covered;
- whether a clean runtime, Compose, or journey run is required;
- applicable `cv-review-*` AI skills and their immutable base/head decision;
- whether a separate human authority approval is explicitly required and why.

Tests that pass but do not exercise the affected behavior are insufficient.
Behavioral changes require evidence beyond policy or narrow unit checks.
Runtime-sensitive work must retain clean runtime evidence. Required human
authority decisions remain mandatory, but ordinary code review does not gain a
human gate merely because an issue is high risk.

## Validation

The policy and evidence validators must prove:

- AI code review succeeds without human review when no authority decision is
  required;
- risk/gate labels without evidence coverage fail;
- behavior changes without behavioral evidence fail;
- an explicitly required human authority decision cannot be omitted;
- Approved AI review cannot claim inadequate evidence;
- all existing branch, scope, prerequisite, mutation, merge, and post-merge
  controls continue to fail closed.

Exact commands, versions, artifact hashes, immutable PR SHAs, review decision,
merge SHA, and post-merge results are recorded in the machine-readable evidence
manifest and Linear handoff comments.
