# Ultimate-Dev Runtime 2.5

A small, dependency-free durable execution core.

```python
from runtime.engine import Runtime
rt = Runtime("/path/to/project")
task = rt.start({"goal": "Implement feature X", "acceptance_criteria": ["tests pass"]})
rt.checkpoint(task["task_id"])
```

State is stored in `.memory/ultimate-dev/tasks/<task-id>/`.
The runtime can reconstruct a task from state files without the previous conversation.
