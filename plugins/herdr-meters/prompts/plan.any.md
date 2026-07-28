<!-- key: plan.any — decomposition. Mirrors plan.py's contract; kept here so the
     wording is versioned and A/B-testable like every other template. -->
Decompose this task for the repository.

{task}

Output ONLY a JSON object: {task, subtasks[], integration_check, risky_seams[]}.
Each subtask: {id, goal, depends_on[], files_touched[], parallelizable, acceptance_check}.

CRITICAL: every `acceptance_check` and the `integration_check` must be a RUNNABLE
shell command that exits 0 iff the work is complete. Not prose. If a subtask
cannot be reduced to a runnable check, set its acceptance_check to "MANUAL: <why>"
and a human will handle it.

Keep stages small and ordered. Mark parallelizable true only when genuinely
file-disjoint. Name the seams where independently-built stages could disagree.
