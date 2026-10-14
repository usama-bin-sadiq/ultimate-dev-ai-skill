# GitHub Actions Templates

**The versions below are the current stable majors, not an exact pin to copy.**
A major tag floats forward to the newest patch on its own, so `@v7` tracks 7.0.x
without any edit. They still go stale when a new major lands: an old major keeps
running but stops getting fixes, and an action retired outright fails the run
rather than warning. Check the action's releases page for a newer major instead
of trusting the number written here. Prefer a major tag to `@latest`, which
crosses majors and can break a working pipeline with no change of your own.

## Node.js Baseline

```yaml
name: Node CI
on: [push, pull_request]

jobs:
  ci:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v7
      - uses: actions/setup-node@v7
        with:
          node-version: '20'
          cache: 'npm'
      - run: npm ci
      - run: npm run lint
      - run: npm test
      - run: npm run build
```

## Python Baseline

```yaml
name: Python CI
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v7
      - uses: actions/setup-python@v7
        with:
          python-version: '3.12'
      - run: python3 -m pip install -U pip
      - run: python3 -m pip install -r requirements.txt
      - run: python3 -m pytest
```
