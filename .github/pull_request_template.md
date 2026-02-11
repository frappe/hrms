
# Description
*Brief description of this PR*

# Issue(s): 
*Add the link(s) to issues that this PR closes*

# Type of change
*task-contribution*

# Task Contribution Checklist

This checklist must be completed by task contributors before submitting a pull request.  
Each item should be answerable with **Yes**. If not, explain why in the PR description.

---

## A. Task Definition & Specification

- [ ] I used `task_template.json` as the baseline for this task.
- [ ] The task instruction is written in natural language and does not reference internal tool names, code keys, or evaluator logic.
- [ ] All behaviors required for successful task completion are explicitly described in the task instruction.
- [ ] All behaviors described in the task instruction are intended to be evaluated.
- [ ] For self-service tasks, the instruction refers to the user’s own data (e.g., “my salary”, “my time off”).
- [ ] For non–self-service tasks, the instruction is written in the third person.

---

## B. Output Format & Schema

- [ ] The expected output format and data types are clearly specified.
- [ ] If the task requires structured output, the exact schema is fully described in `task.yaml` or a referenced file.
- [ ] Any examples included in the task description do not match evaluator ground truth values.

---

## C. Accounts & Execution Context

- [ ] The task uses the least-privilege account required to complete it.
- [ ] Self-service tasks execute using the actual user’s account.
- [ ] Non–self-service tasks execute using an HR account distinct from the referenced user.
- [ ] The task does not rely on Administrator-level permissions unless strictly necessary and documented.

---

## D. Evaluators & Tests

- [ ] Every behavior described in the task instruction is verified by at least one evaluator.
- [ ] Every evaluator verifies behavior that is explicitly described in the task instruction.
- [ ] For structured outputs, evaluators verify:
  - [ ] Key existence
  - [ ] Key content correctness
- [ ] All evaluators are deterministic when the correct answer is deterministic.
- [ ] For non-deterministic tasks, evaluation uses an explicit strategy (e.g., LLM-as-judge or range-based checks).
- [ ] All custom evaluators have corresponding test cases in the test suite (Important: not optional for writing tasks).
- [ ] Test cases include informative docstrings describing the behavior they verify.

---

## E. State & Environment Integrity

- [ ] I used the correct container image version to develop and test all state scripts and tasks.
- [ ] Any database or demo-state modifications follow existing script patterns and ordering constraints.
- [ ] Read-only tasks rely only on the predefined demo state unless explicitly documented.
- [ ] Writing tasks include an explicit cleanup step.
- [ ] All environment changes introduced by the task are fully reverted after evaluation.

---

## F. Anti-cheating & Robustness

- [ ] The agent cannot trivially solve the task by inspecting files, fixtures, or evaluator logic.
- [ ] The task does not expose solution strings, labels, or ground truth values in accessible files.
- [ ] The task cannot be solved by memorizing static outputs or training on the test set.
- [ ] The task specification was written by a human.
- [ ] Any solution logic or scripts were written by a human, with at most minimal assistance from a language model.
- [ ] I ran the full local task checks and all checks pass.

## G. Spec file

- [ ] I confirm that tasks use existing tools defined in the spec file, adding new tools only when necessary.

- [ ] Only verify the following points if new tools added to the MCP spec file, otherwise ignore.
  - [ ] Tool descriptions are clear without being overly prescriptive about which tool the agent should use.
  - [ ] Page limit attribute is set to return all records (*)
  - [ ] The task explicitly defines all required fields, provides adequate descriptions, and includes only general (non–task-specific) examples.
  - [ ] The tool returns all keys for the entities it operates on (*).
