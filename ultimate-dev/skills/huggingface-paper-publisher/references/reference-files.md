<!-- Moved verbatim from huggingface-paper-publisher/SKILL.md, the
     'reference-files' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Reference files

These ship with the skill and are read on demand; none is needed to
use it. Each answers one question the sections above do not.

- [`references/quick_reference.md`](references/quick_reference.md)

### Integration with tfrere's Research Template

This skill complements [tfrere's research article template](https://huggingface.co/spaces/tfrere/research-article-template) by providing:

- Automated paper indexing workflows
- Repository linking capabilities
- Metadata management tools
- Citation generation utilities

You can use tfrere's template for writing, then use this skill to publish and link the paper on Hugging Face Hub.

### Common Patterns

**Pattern 1: New Paper Publication**
```bash
# Write → Publish → Index → Link
uv run scripts/paper_manager.py create --template modern --output paper.md
# (Submit to arXiv)
uv run scripts/paper_manager.py index --arxiv-id "2301.12345"
uv run scripts/paper_manager.py link --repo-id "user/model" --arxiv-id "2301.12345"
```

**Pattern 2: Existing Paper Discovery**
```bash
# Search → Check → Link
uv run scripts/paper_manager.py search --query "transformers"
uv run scripts/paper_manager.py check --arxiv-id "2301.12345"
uv run scripts/paper_manager.py link --repo-id "user/model" --arxiv-id "2301.12345"
```

**Pattern 3: Author Portfolio Management**
```bash
# Claim → Verify → Organize
uv run scripts/paper_manager.py claim --arxiv-id "2301.12345"
uv run scripts/paper_manager.py list-my-papers
uv run scripts/paper_manager.py toggle-visibility --arxiv-id "2301.12345" --show true
```

### API Integration

**Python Script Example:**
```python
from scripts.paper_manager import PaperManager

pm = PaperManager(hf_token="your_token")

# Index paper
pm.index_paper("2301.12345")

# Link to model
pm.link_paper(
    repo_id="username/model",
    repo_type="model",
    arxiv_id="2301.12345",
    citation="Full citation text"
)

# Check status
status = pm.check_paper("2301.12345")
print(status)
```

### Future Enhancements

Planned features for future versions:
- Support for non-arXiv papers (conference proceedings, journals)
- Automatic citation formatting from DOI
- Paper comparison and versioning tools
- Collaborative paper writing features
- Integration with LaTeX workflows
- Automated figure and table extraction
- Paper metrics and impact tracking
