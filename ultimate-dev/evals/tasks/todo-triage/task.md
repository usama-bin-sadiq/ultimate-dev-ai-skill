`sample.py` contains five comments of the form `# TODO(n): text`, numbered
1 to 5.

Classify each with this rule and nothing else:

- **BLOCKER** if the text describes a security problem, loss/corruption of data
  or user files, or a correctness defect.
- **NIT** if it is about naming, formatting, typing, or comments.

Write `out/todos.csv` with a header line `id,severity` and then one line per
TODO in ascending id order, e.g. `1,BLOCKER`. Use uppercase severity. Include
every TODO exactly once and no others.
