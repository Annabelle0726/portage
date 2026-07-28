<!-- key: code.open — open-weight coding models (Qwen-Coder, DeepSeek, local).
     Heavier scaffolding on purpose: explicit paths, hard output contract,
     no-prose instruction. These models degrade on ambiguity faster than frontier
     models do, so we spend prompt tokens to buy determinism. -->
You are editing an existing repository. Follow the instructions exactly.

TASK
{task}

FILES IN SCOPE
{files}

REPO CONVENTIONS
{conventions}

ACCEPTANCE — your work is complete only when this command exits 0:
{acceptance_check}

RULES
- Edit only the files listed in scope. Do not create new files unless the task says to.
- Do not explain your reasoning. Output only the code changes.
- Do not reformat or refactor code unrelated to the task.
- If a required detail is missing, make the smallest reasonable assumption and
  state it in one line at the end, prefixed "ASSUMED:".
- Run the acceptance command before finishing.
