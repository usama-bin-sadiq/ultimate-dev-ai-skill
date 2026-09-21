# Git Hooks for Quality Gates

## Setup
```bash
# Install hooks
npm install husky --save-dev
npx husky install

# Add hooks
npx husky add .husky/pre-commit "npm run lint"
npx husky add .husky/commit-msg "npx commitlint --edit $1"
npx husky add .husky/pre-push "npm test"
```

## Package.json Configuration
```json
{
  "scripts": {
    "prepare": "husky install"
  },
  "devDependencies": {
    "husky": "^9.0.0",
    "@commitlint/cli": "^19.0.0",
    "@commitlint/config-conventional": "^19.0.0"
  }
}
```

## Commitlint Config (commitlint.config.js)
```javascript
module.exports = {
  extends: ['@commitlint/config-conventional'],
  rules: {
    'type-enum': [2, 'always', [
      'feat', 'fix', 'docs', 'style', 'refactor',
      'perf', 'test', 'build', 'ci', 'chore', 'revert'
    ]],
    'subject-case': [2, 'never', ['start-case', 'pascal-case', 'upper-case']],
    'subject-max-length': [2, 'always', 72],
    'body-max-line-length': [1, 'always', 72]
  }
};
```

## Pre-commit Hook
```bash
#!/bin/sh
# .husky/pre-commit

# Run linter
npm run lint

# Run formatter check
npm run format:check

# Run type check
npm run typecheck

# Run tests (quick)
npm run test:unit -- --passWithNoTests
```

## Commit-msg Hook
```bash
#!/bin/sh
# .husky/commit-msg

# Validate commit message format
npx commitlint --edit $1
```

## Pre-push Hook
```bash
#!/bin/sh
# .husky/pre-push

# Run full test suite
npm test

# Run build
npm run build
```

## Post-merge Hook
```bash
#!/bin/sh
# .husky/post-merge

# Install dependencies if package.json changed
if git diff-tree -r --name-only --no-commit-id ORIG_HEAD HEAD | grep -q "package.json"; then
  echo "📦 package.json changed, running npm install..."
  npm install
fi
```

## Lint-staged Config (.lintstagedrc)
```json
{
  "*.{js,jsx,ts,tsx}": [
    "eslint --fix",
    "prettier --write"
  ],
  "*.{json,md,yml,yaml}": [
    "prettier --write"
  ],
  "*.{css,scss}": [
    "stylelint --fix",
    "prettier --write"
  ]
}
```

## Setup Commands
```bash
# Full setup
npm install husky lint-staged @commitlint/cli @commitlint/config-conventional --save-dev

# Initialize husky
npx husky init

# Add hooks
npx husky add .husky/pre-commit "npx lint-staged"
npx husky add .husky/commit-msg "npx commitlint --edit \$1"
npx husky add .husky/pre-push "npm test"

# Make hooks executable
chmod +x .husky/*
```