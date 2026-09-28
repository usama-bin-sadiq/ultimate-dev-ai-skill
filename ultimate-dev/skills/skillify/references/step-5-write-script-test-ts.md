<!-- Moved verbatim from skillify/SKILL.md, the
     'step-5-write-script-test-ts' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Step 5 — Write `script.test.ts`

Mirror `browser-skills/hackernews-frontpage/script.test.ts`. The test
must include at least one ★★ assertion — parsed output has the expected
shape AND non-empty key fields — not a smoke ★ assertion. Smoke tests
that only check `parseFromHtml` doesn't throw are insufficient.

```ts
import { describe, it, expect } from 'bun:test';
import * as fs from 'fs';
import * as path from 'path';
import { parseFromHtml } from './script';

describe('<name> parser', () => {
  const fixturePath = path.join(import.meta.dir, 'fixtures', '<host>-<date>.html');
  const html = fs.readFileSync(fixturePath, 'utf-8');
  const items = parseFromHtml(html);

  it('returns at least one item from the bundled fixture', () => {
    expect(items.length).toBeGreaterThan(0);
  });

  it('every item has the required shape', () => {
    for (const item of items) {
      expect(typeof item.<keyfield>).toBe('<keytype>');
      // ... assert on every required field
    }
  });
});
```
