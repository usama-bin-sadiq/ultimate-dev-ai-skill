import json
import tempfile

from runtime.core.audit import AuditJournal, AuditJournalError


def test_audit_journal_detects_tampering():
    with tempfile.TemporaryDirectory() as tmp:
        journal = AuditJournal(tmp + "/events.jsonl")
        journal.append({"type": "one", "value": 1})
        journal.append({"type": "two", "value": 2})
        assert journal.verify() is True
        lines = journal.path.read_text().splitlines()
        record = json.loads(lines[0])
        record["event"]["value"] = 99
        lines[0] = json.dumps(record)
        journal.path.write_text("\n".join(lines) + "\n")
        try:
            journal.verify()
        except AuditJournalError:
            pass
        else:
            raise AssertionError("tampered journal was accepted")
