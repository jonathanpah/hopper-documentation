"""Tests for scripts/hopper_documentation.py. They call no model and install nothing.

Run: python3 -m unittest discover -s tests -v
"""
import base64
import contextlib
import errno
import hashlib
import importlib.util
import io
import json
import multiprocessing
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
PROGRAM = ROOT / "scripts" / "hopper_documentation.py"
spec = importlib.util.spec_from_file_location("hopper_documentation", PROGRAM)
hd = importlib.util.module_from_spec(spec)
sys.modules["hopper_documentation"] = hd
spec.loader.exec_module(hd)

CONTENT = {"sources": [], "summary": "Monthly report on Mondays", "state": "State text.", "topics": "P1 Report: waiting.",
           "decisions": "\"I decided the report goes out on Mondays.\"", "pending": "PD1 Tell the team.", "gaps": ""}
FAKE_EXECUTOR = r'''#!/usr/bin/env python3
import json, os, sys
from pathlib import Path
prompt = sys.stdin.read()
mode = os.environ.get("FAKE_MODE", "ok")
if mode == "fail":
    print('denied; password="secret with spaces"', file=sys.stderr)
    sys.exit(17)
if mode == "notlogged":
    print(json.dumps({"type": "result", "is_error": True, "result": "Not logged in · Please run /login"}))
    sys.exit(1)
if mode == "echo":
    print("header\nuser\n" + prompt + "\nERROR: model not supported\nERROR: model not supported", file=sys.stderr)
    sys.exit(1)
content = json.loads(os.environ["FAKE_CONTENT"])
if Path(sys.argv[0]).name == "claude":
    print(json.dumps({"type": "result", "is_error": False, "structured_output": content}))
else:
    print(json.dumps(content))
'''


def claude_record(session, kind, content, stamp, **extra):
    record = {"type": kind, "sessionId": session, "timestamp": stamp, "message": {"role": kind, "content": content}}
    record.update(extra)
    return record


def write_jsonl(path, records, tail=""):
    path.write_text("".join(json.dumps(r) + "\n" for r in records) + tail, encoding="utf-8")


class Environment(unittest.TestCase):
    """Each test gets its own configuration, log, cache, state, temporary folder and working directory."""

    def setUp(self):
        self.temp = Path(tempfile.mkdtemp(prefix="hd-test-"))
        self.cwd = self.temp / "project"
        self.cwd.mkdir()
        self.bin = self.temp / "bin"
        self.bin.mkdir()
        for name in ("claude", "codex"):
            (self.bin / name).write_text(FAKE_EXECUTOR)
            (self.bin / name).chmod(0o755)
        config = self.temp / "config.json"
        config.write_text(json.dumps({"claude": {"executable": str(self.bin / "claude")},
                                      "codex": {"executable": str(self.bin / "codex")}}))
        (self.temp / "tmp").mkdir()
        self.saved = dict(os.environ)
        self.saved_tempdir = tempfile.tempdir
        tempfile.tempdir = str(self.temp / "tmp")
        os.environ.update(HOPPER_DOCUMENTATION_CONFIG=str(config), HOPPER_DOCUMENTATION_LOG=str(self.temp / "log.jsonl"),
                          XDG_CACHE_HOME=str(self.temp / "cache"), XDG_STATE_HOME=str(self.temp / "state"),
                          TMPDIR=str(self.temp / "tmp"),
                          FAKE_CONTENT=json.dumps(CONTENT), FAKE_MODE="ok")
        os.environ.pop("HOPPER_DOCUMENTATION_RUN", None)

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self.saved)
        tempfile.tempdir = self.saved_tempdir
        shutil.rmtree(self.temp, ignore_errors=True)

    def claude_history(self, session="s-1", extra=()):
        path = self.temp / (session + ".jsonl")
        records = [
            {"type": "queue-operation", "operation": "enqueue"},
            claude_record(session, "user", "I decided the report goes out on Mondays.", "2026-09-28T10:00:00.000Z"),
            claude_record(session, "assistant", [{"type": "thinking", "thinking": "HIDDEN_THOUGHT"},
                                                 {"type": "tool_use", "name": "Bash", "input": {"command": "ls"}},
                                                 {"type": "text", "text": "Recorded."}], "2026-09-28T10:00:01.000Z"),
            claude_record(session, "user", [{"type": "tool_result", "content": "TOOL_OUTPUT"}], "2026-09-28T10:00:02.000Z"),
            claude_record(session, "user", "<command-name>/compact</command-name>", "2026-09-28T10:00:03.000Z"),
            claude_record(session, "user", "SUMMARY_OF_COMPACTION", "2026-09-28T10:00:04.000Z", isCompactSummary=True),
            claude_record(session, "assistant", [{"type": "text", "text": "SIDECHAIN"}], "2026-09-28T10:00:05.000Z", isSidechain=True),
            claude_record(session, "user", "Please <system-reminder>REMINDER</system-reminder>keep token=abc123", "2026-09-28T10:00:06.000Z"),
        ] + list(extra) + [{"type": "mode", "mode": "default"}]
        write_jsonl(path, records, tail='{"partial":')
        return path

    def codex_history(self, session="c-1", extra=()):
        path = self.temp / ("rollout-2026-09-28T10-00-00-" + session + ".jsonl")

        def item(role, text, stamp, kind="input_text"):
            return {"timestamp": stamp, "type": "response_item",
                    "payload": {"type": "message", "role": role, "content": [{"type": kind, "text": text}]}}
        records = [
            {"timestamp": "2026-09-28T10:00:00.000Z", "type": "session_meta", "payload": {"id": session, "cwd": str(self.cwd)}},
            item("user", "<environment_context>\n  <cwd>/x</cwd>\n</environment_context>", "2026-09-28T10:00:00.500Z"),
            item("user", "# AGENTS.md instructions for /x\nRULES", "2026-09-28T10:00:00.600Z"),
            item("user", "I decided the report goes out on Mondays.", "2026-09-28T10:00:01.000Z"),
            {"timestamp": "2026-09-28T10:00:01.500Z", "type": "response_item", "payload": {"type": "reasoning", "summary": [{"text": "HIDDEN_THOUGHT"}]}},
            {"timestamp": "2026-09-28T10:00:01.600Z", "type": "response_item", "payload": {"type": "function_call_output", "output": "TOOL_OUTPUT"}},
            item("assistant", "Recorded.", "2026-09-28T10:00:02.000Z", "output_text"),
            {"timestamp": "2026-09-28T10:00:02.500Z", "type": "event_msg", "payload": {"type": "user_message", "message": "DUPLICATE"}},
        ] + list(extra)
        write_jsonl(path, records)
        return path


def web_token(header, claims):
    """A fictional signed token built from the given JSON texts."""
    def encode(data):
        return base64.urlsafe_b64encode(data).rstrip(b"=").decode()
    signed = encode(header.encode()) + "." + encode(claims.encode())
    return signed + "." + encode(hashlib.sha256(signed.encode()).digest())


SPACED_TOKEN = web_token('{\n  "alg": "HS256",\n  "typ": "JWT"\n}', '{\n  "sub": "alice"\n}')
EMPTY_CLAIMS_TOKEN = web_token('{"alg":"HS256","typ":"JWT"}', "{}")


class Masking(unittest.TestCase):
    CASES = [
        ('denied; API_TOKEN=SIMPLE_123', ["SIMPLE_123"], ["denied"]),
        ('{"password":"P_123","api_key":"K_456","name":"visible"}', ["P_123", "K_456"], ["visible"]),
        ('senha="prefix COMPLEMENT_789" then', ["prefix", "COMPLEMENT_789"], ["then"]),
        ("password: 'a value with spaces' end", ["a value", "spaces"], ["end"]),
        ('{"secret":"a\\"b c","ok":"yes"}', ["b c"], ["yes"]),
        ('Authorization: Bearer abc.def.ghi', ["abc.def.ghi"], []),
        ('-----BEGIN RSA PRIVATE KEY-----\nMIIE\n-----END RSA PRIVATE KEY-----', ["MIIE"], []),
        ('-----BEGIN PGP PRIVATE KEY BLOCK-----\nlQOYBF\n-----END PGP PRIVATE KEY BLOCK----- after', ["lQOYBF"], ["after"]),
        ('-----BEGIN A PRIVATE KEY-----\nFIRST_PART\n-----BEGIN B PRIVATE KEY-----\nSECOND_PART\n-----END B PRIVATE KEY----- after',
         ["FIRST_PART", "SECOND_PART"], ["after"]),
        ('key sk-ant-FICTIONAL1234567890 used', ["FICTIONAL1234567890"], ["used"]),
        ('tokens used 5,958; next step to be defined', [], ["tokens used 5,958", "next step to be defined"]),
        ('password="open value FICTIONAL_OPEN', ["FICTIONAL_OPEN"], []),
        ('line one\\npassword=ESCAPED_VALUE and more', ["ESCAPED_VALUE"], ["line one", "and more"]),
        ('line one\\n--password "FICTIONAL_F6 x" --user x', ["FICTIONAL_F6"], ["line one", "--user x"]),
        ('line one\\nsenha é FICTIONAL_G7# hoje', ["FICTIONAL_G7"], ["line one", "hoje"]),
        ('C:\\token=WINDOWS_VALUE', ["WINDOWS_VALUE"], []),
        ('**jonathan**\n```text\nAb3dE5fG7hJ9kLmNpQrStUvWx12YzAaBbCc\n```', ["Ab3dE5fG7hJ9kLmNpQrStUvWx12YzAaBbCc"], ["jonathan"]),
        ('https://claude.ai/code/artifact/Ab3dE5fG7hJ9kLmNpQrStUvWx12 call_H1RCsaHAYoBs3Zm21btuoDPS '
         '20260928-HHMM-orchestration-tasks-module-spec', [],
         ["artifact/Ab3dE5fG7hJ9kLmNpQrStUvWx12", "call_H1RCsaHAYoBs3Zm21btuoDPS", "20260928-HHMM-orchestration-tasks-module-spec"]),
        ('token JWT eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0', ["eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"], ["token JWT"]),
        ('postgres://admin:S3cretPass@db.example.com:5432/app', ["S3cretPass"], ["postgres://admin:", "@db.example.com"]),
        ('Authorization: Basic dXNlcjpwYXNzd29yZA==', ["dXNlcjpwYXNzd29yZA"], ["Authorization: Basic"]),
        ('mysql --password Tr0ub4dor3 -u ana', ["Tr0ub4dor3"], ["-u ana"]),
        ('a senha é Tr0ub4dor&3 e o usuário é ana', ["Tr0ub4dor&3"], ["o usuário é ana"]),
        ('a senha é obrigatória para entrar', [], ["a senha é obrigatória para entrar"]),
        ('a senha do servidor é Pl4nt@d4#2026 hoje', ["Pl4nt@d4#2026"], ["a senha do servidor é", "hoje"]),
        ('a senha do servidor novo é obrigatória', [], ["a senha do servidor novo é obrigatória"]),
        ('tool --password "Alpha123 bravo456" --user reviewer', ["Alpha123", "bravo456"], ["--user reviewer"]),
        ('a senha do servidor é "Alpha123 bravo456" hoje', ["Alpha123", "bravo456"], ["hoje"]),
        ('tool --password "a\\"b c9x" --user x', ['a\\"b', "c9x"], ["--user x"]),
        ('the password is "sunflower" today', ["sunflower"], ["the password is", "today"]),
        ('password=D82504b0246DA7E7bb13dbd73588544E1a1810e2cfa8a2d4d2de01d733c1b462 --token aB12cD34-eF56-4789-aB12-cD34eF56aB78',
         ["D82504b0246DA7E7", "aB12cD34"], ["--token"]),
        ('unsigned eyJhbGciOiJub25lIn0.eyJzdWIiOiJyZXZpZXctdXNlciJ9. End', ["eyJhbGciOiJub25lIn0", "eyJzdWIiOiJyZXZpZXctdXNlciJ9"],
         [". End"]),
        ('jwt eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJyZXZpZXctdXNlciJ9.c2lnbmF0dXJlLWZpY3RpY2lh fim',
         ["eyJhbGciOiJIUzI1NiJ9", "eyJzdWIiOiJyZXZpZXctdXNlciJ9", "c2lnbmF0dXJlLWZpY3RpY2lh"], ["jwt", "fim"]),
        ('jwt eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJyZXZpZXctdXNlciIsIm5hbWUiOiJGaWN0aWNpbyIsImlhdCI6MTUxNjIzOTAyMn0.'
         'SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c fim', ["eyJzdWIiOiJyZXZpZXctdXNlciIsIm5hbWUiOiJGaWN0aWNpbyIsImlhdCI6MTUxNjIzOTAyMn0",
         "SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"], ["jwt", "fim"]),
        ('max_output_tokens: 4096; original_token_count=632; Tokens: 20 mil; tokens.css:12; desenhar: a; NOPASSWD: ALL', [],
         ["4096", "632", "20 mil", "tokens.css:12", "desenhar: a", "NOPASSWD: ALL"]),
        ('githubToken=Gh0_FICTIONAL1 clientSecret: CS_FICTIONAL2 XAI_API_KEY=xai-FICTIONAL3 password2=PW_FICTIONAL4',
         ["Gh0_FICTIONAL1", "CS_FICTIONAL2", "xai-FICTIONAL3", "PW_FICTIONAL4"], []),
        ('token_type: Bearer, Bearer tokens, "Bearer " + token', [], ["token_type: Bearer", "Bearer tokens", '"Bearer " + token']),
        ('digest SHAD82504b0246DA7E7bb13dbd73588544E1a1810e2cfa8a2d4d2de01d733c1b462 key SHA256:nThbg6kXUpJWGl7E1IGOCspRomTxdCARLviKw6E5SY8',
         [], ["SHAD82504b0246DA7E7bb13dbd73588544E1a1810e2cfa8a2d4d2de01d733c1b462", "SHA256:nThbg6kXUpJWGl7E1IGOCspRomTxdCARLviKw6E5SY8"]),
        ('APIToken=FICTIONAL_A1 DBPassword: FICTIONAL_B2 {"SQLPassword": "FICTIONAL_C3", "JWTToken": "FICTIONAL_D4", '
         '"CLIENTSecret": "FICTIONAL_E5"}', ["FICTIONAL_A1", "FICTIONAL_B2", "FICTIONAL_C3", "FICTIONAL_D4", "FICTIONAL_E5"], []),
        ('config.local.settings v1.2.3 com.example.app e30.jpg', [],
         ["config.local.settings", "v1.2.3", "com.example.app", "e30.jpg"]),
        ('session ' + SPACED_TOKEN + ' end', SPACED_TOKEN.split("."), ["session ", " end"]),
        ('cookie=' + EMPTY_CLAIMS_TOKEN + '; path=/', EMPTY_CLAIMS_TOKEN.split("."), ["cookie=", "; path=/"]),
        ('a.prefix.' + SPACED_TOKEN, SPACED_TOKEN.split("."), ["a.prefix."]),
        ('D82504b0246DA7E7bb13dbd73588544E1a1810e2cfa8a2d4d2de01d733c1b462 aB12cD34-eF56-4789-aB12-cD34eF56aB78', [],
         ["D82504b0246DA7E7bb13dbd73588544E1a1810e2cfa8a2d4d2de01d733c1b462", "aB12cD34-eF56-4789-aB12-cD34eF56aB78"]),
        ('aws key AKIAIOSFODNN7EXAMPLE usada', ["AKIAIOSFODNN7EXAMPLE"], ["usada"]),
        ('rollout-2026-09-25T15-10-28-01a0d9c2-f84a-71f1-af16-5544f7993679.jsonl d82504b0246da7e7bb13dbd73588544e1a1810e2 '
         'HOPPER_DOCUMENTATION_LOG test_manual_codex_reports_partial_when_next_part_fails', [],
         ["rollout-2026-09-25T15-10-28-01a0d9c2", "d82504b0246da7e7bb13dbd73588544e1a1810e2", "HOPPER_DOCUMENTATION_LOG",
          "test_manual_codex_reports_partial_when_next_part_fails"]),
    ]

    def test_cases(self):
        for text, hidden, kept in self.CASES:
            result = hd.mask(text)
            for fragment in hidden:
                self.assertNotIn(fragment, result, text)
            for fragment in kept:
                self.assertIn(fragment, result, text)

    def test_whole_web_tokens(self):
        compact = web_token('{"alg":"HS256","typ":"JWT"}', '{"sub":"alice","scope":"read:reports"}')
        for token in (compact, SPACED_TOKEN, EMPTY_CLAIMS_TOKEN):
            self.assertEqual(hd.mask(token), hd.TEXT["credential_hidden"], token)

    def test_nested_json(self):
        value = 'START "MIDDLE" END \\ tail'
        for depth in range(1, 5):
            text = {"password": value, "api_key": "K_" + str(depth), "note": "visible"}
            for _ in range(depth):
                text = json.dumps(text)
            result = hd.mask(text)
            for fragment in ("START", "MIDDLE", "END", "K_" + str(depth)):
                self.assertNotIn(fragment, result, depth)
            decoded = result
            for _ in range(depth):
                decoded = json.loads(decoded)
            self.assertEqual(decoded["note"], "visible")

    def test_linear_time(self):
        for text in ("A" * 200_000, "token" * 40_000, "\\" * 100_000 + '"', ("n" * 50 + "=") * 4_000,
                     "password" * 25_000 + "=v", "a." * 100_000, "eyJhIjoxfQ." * 20_000,
                     "-----BEGIN A PRIVATE KEY-----\n" * 7_000):
            start = time.monotonic()
            hd.mask(text)
            self.assertLess(time.monotonic() - start, 2, text[:20])


class History(Environment):
    def test_claude_extraction(self):
        path = self.claude_history()
        messages = hd.extract_messages("claude", path, 1, 100)
        texts = [m["text"] for m in messages]
        self.assertEqual(texts[:2], ["I decided the report goes out on Mondays.", "Recorded."])
        self.assertEqual(len(messages), 3)
        joined = " ".join(texts)
        for hidden in ("HIDDEN_THOUGHT", "TOOL_OUTPUT", "/compact", "SUMMARY_OF_COMPACTION", "SIDECHAIN", "REMINDER", "abc123"):
            self.assertNotIn(hidden, joined)

    def test_codex_extraction(self):
        path = self.codex_history()
        messages = hd.extract_messages("codex", path, 1, 100)
        self.assertEqual([(m["role"], m["text"]) for m in messages],
                         [("user", "I decided the report goes out on Mondays."), ("assistant", "Recorded.")])

    def test_structured_answers_and_approved_plan(self):
        session = "s-9"
        answers = {"type": "user", "sessionId": session, "timestamp": "2026-09-28T10:00:10.000Z",
                   "message": {"role": "user", "content": [{"type": "tool_result", "tool_use_id": "q1", "content": "answered"}]},
                   "toolUseResult": {"questions": [], "answers": {"Which model?": "Luna"},
                                     "annotations": {"Which model?": {"notes": "only for now"}}}}
        plan = {"type": "user", "sessionId": session, "timestamp": "2026-09-28T10:00:11.000Z",
                "message": {"role": "user", "content": [{"type": "tool_result", "tool_use_id": "p1", "content": "approved"}]},
                "toolUseResult": {"plan": "# Plan\nStep one.", "filePath": "/p.md"}}
        rejected = {"type": "user", "sessionId": session, "timestamp": "2026-09-28T10:00:12.000Z",
                    "message": {"role": "user", "content": [{"type": "tool_result", "tool_use_id": "p2", "is_error": True, "content": "no"}]},
                    "toolUseResult": {"plan": "# Rejected plan"}}
        path = self.claude_history(session, extra=[answers, plan, rejected])
        texts = [m["text"] for m in hd.extract_messages("claude", path, 1, 100)]
        self.assertIn(hd.TEXT["answers"] + "\n- Which model? → Luna (only for now)", texts)
        self.assertIn(hd.TEXT["plan_approved"] + "\n# Plan\nStep one.", texts)
        self.assertFalse(any("Rejected plan" in text for text in texts))

    def test_codex_answers_after_the_resume_point(self):
        call = {"timestamp": "2026-09-28T10:00:03.000Z", "type": "response_item", "payload": {
            "type": "function_call", "name": "request_user_input", "call_id": "c9",
            "arguments": json.dumps({"questions": [{"id": "model", "question": "Which model?", "options": []}]})}}
        output = {"timestamp": "2026-09-28T10:00:04.000Z", "type": "response_item", "payload": {
            "type": "function_call_output", "call_id": "c9", "output": json.dumps({"answers": {"model": {"answers": ["Luna"]}}})}}
        path = self.codex_history("c-1", extra=[call, output])
        texts = [m["text"] for m in hd.extract_messages("codex", path, 10, 100)]
        self.assertEqual(texts, [hd.TEXT["answers"] + "\n- Which model? → Luna"])

    def test_codex_internal_texts_are_skipped(self):
        def item(text, stamp):
            return {"timestamp": stamp, "type": "response_item",
                    "payload": {"type": "message", "role": "user", "content": [{"type": "input_text", "text": text}]}}
        path = self.codex_history("c-1", extra=[
            item("<recommended_plugins>\nHere is a list of plugins.\n</recommended_plugins>", "2026-09-28T10:00:03.000Z"),
            item('<codex_internal_context source="daemon_recovery">\nThe server restarted.\n</codex_internal_context>',
                 "2026-09-28T10:00:04.000Z")])
        texts = [m["text"] for m in hd.extract_messages("codex", path, 1, 100)]
        self.assertEqual(texts, ["I decided the report goes out on Mondays.", "Recorded."])

    def test_messages_sent_while_the_assistant_works(self):
        queued = {"type": "attachment", "sessionId": "s-1", "timestamp": "2026-09-28T10:00:07.000Z",
                  "attachment": {"type": "queued_command", "prompt": "Also send it on Tuesdays.", "commandMode": "prompt",
                                 "origin": {"kind": "human"}}}
        listed = dict(queued, timestamp="2026-09-28T10:00:08.000Z",
                      attachment=dict(queued["attachment"], prompt=[{"type": "text", "text": "And keep it short."}]))
        notice = {"type": "attachment", "sessionId": "s-1", "timestamp": "2026-09-28T10:00:09.000Z",
                  "attachment": {"type": "queued_command", "prompt": "<task-notification>done</task-notification>",
                                 "commandMode": "task-notification"}}
        path = self.claude_history("s-1", extra=[queued, listed, notice])
        texts = [m["text"] for m in hd.extract_messages("claude", path, 1, 100) if m["role"] == "user"]
        self.assertIn("Also send it on Tuesdays.", texts)
        self.assertIn("And keep it short.", texts)
        self.assertFalse(any("task-notification" in text for text in texts))

    def test_fork_and_rewritten_records(self):
        original = claude_record("origin", "user", "Earlier decision: weekly report.", "2026-09-28T09:00:00.000Z", uuid="u-1")
        again = dict(original, timestamp="2026-09-28T09:00:01.000Z")
        own = claude_record("s-fork", "user", "New request in the fork.", "2026-09-28T10:00:00.000Z", uuid="u-2")
        fork = self.temp / "s-fork.jsonl"
        write_jsonl(fork, [original, again, own])
        copy = self.temp / "copy.jsonl"
        shutil.copyfile(fork, copy)
        hd.verify_identity("claude", fork, "s-fork")
        hd.verify_identity("claude", copy, "s-fork")
        misnamed = self.temp / "s-b.jsonl"
        write_jsonl(misnamed, [original])
        for path, session in ((fork, "origin"), (copy, "other"), (misnamed, "s-b")):
            with self.assertRaises(hd.Failure):
                hd.verify_identity("claude", path, session)
        texts = [m["text"] for m in hd.extract_messages("claude", fork, 1, 3)]
        self.assertEqual(texts, ["Earlier decision: weekly report.", "New request in the fork."])
        self.assertEqual(hd.extract_messages("claude", fork, 2, 2), [])

    def test_text_utf8_cannot_write_is_replaced(self):
        path = self.claude_history("s-1", extra=[claude_record("s-1", "user", "half emoji \ud83d here", "2026-09-28T10:00:07.000Z")])
        try:
            (self.cwd / os.fsdecode(b"relat\xf3rio.md")).write_text("report", encoding="utf-8")
        except OSError:  # file systems that only accept UTF-8 names
            pass
        job = hd.prepare_job("claude", "s-1", path, self.cwd, hd.TEXT["trigger_user"])
        job["prompt"].encode("utf-8")
        self.assertIn("half emoji ? here", job["prompt"])
        self.assertIsNotNone(hd.publish(job, CONTENT))

    def test_prompt_uses_local_times(self):
        path = self.codex_history("c-1")
        job = hd.prepare_job("codex", "c-1", path, self.cwd, hd.TEXT["trigger_user"])
        self.assertIn("[4 | {} | user]".format(hd.local_time("2026-09-28T10:00:01.000Z")), job["prompt"])
        self.assertNotIn("2026-09-28T10:00:01.000Z | user", job["prompt"])

    def test_identity(self):
        hd.verify_identity("claude", self.claude_history("s-1"), "s-1")
        hd.verify_identity("codex", self.codex_history("c-1"), "c-1")
        with self.assertRaises(hd.Failure):
            hd.verify_identity("claude", self.claude_history("s-2"), "other")
        with self.assertRaises(hd.Failure):
            hd.verify_identity("codex", self.codex_history("c-2"), "other")

    def test_limit_ignores_technical_and_partial_lines(self):
        path = self.claude_history()
        self.assertEqual(hd.history_limit(path), {"line": 8, "timestamp": "2026-09-28T10:00:06.000Z"})
        empty = self.temp / "empty.jsonl"
        empty.write_text('{"type": "mode"}\n')
        with self.assertRaises(hd.Failure):
            hd.history_limit(empty)

    def test_resume_point(self):
        path = self.claude_history()
        previous = {"name": "h.md", "b": 3, "tb": "2026-09-28T10:00:01Z"}
        self.assertEqual(hd.resume_point(path, previous), 3)
        moved = {"name": "h.md", "b": 5, "tb": "2026-09-28T07:00:01-03:00"}
        self.assertEqual(hd.resume_point(path, moved), 3)
        with self.assertRaises(hd.Failure):
            hd.resume_point(path, {"name": "h.md", "b": 3, "tb": "2020-01-01T00:00:00Z"})

    def test_parts(self):
        messages = [{"line": n, "timestamp": "t", "role": "user", "text": "x" * 60_000} for n in range(1, 6)]
        messages.append({"line": 6, "timestamp": "t", "role": "user", "text": "y" * (hd.PART_LIMIT + 10)})
        parts = hd.split_parts(messages)
        self.assertEqual([len(p) for p, _ in parts], [2, 2, 1, 1])
        self.assertTrue(parts[-1][1] and "6" in parts[-1][1][0])

    def test_blocks_of_one_line_stay_together(self):
        def line(stamp, *texts):
            return {"timestamp": stamp, "type": "response_item", "payload": {
                "type": "message", "role": "user", "content": [{"type": "input_text", "text": t} for t in texts]}}
        path = self.codex_history("c-1", extra=[line("2026-09-28T10:00:03.000Z", "FIRST " + "a" * 400, "SECOND " + "b" * 400),
                                                line("2026-09-28T10:00:04.000Z", "THIRD " + "c" * 900, "FOURTH " + "d" * 300)])
        prompts = []

        def writer(product, prompt, cwd):
            prompts.append(prompt)
            return dict(CONTENT)
        with mock.patch.object(hd, "PART_LIMIT", 1000), mock.patch.object(hd, "call_model", side_effect=writer):
            result = hd.document("codex", "c-1", path, self.cwd, hd.TEXT["trigger_user"])
        self.assertEqual((result["status"], len(prompts)), ("done", 2))
        joined = "\n".join(prompts)
        for marker in ("FIRST ", "SECOND ", "THIRD ", "FOURTH "):
            self.assertEqual(joined.count(marker), 1, marker)
        self.assertIn("SECOND ", prompts[0])
        texts = [h["text"] for h in hd.handoffs(self.cwd / hd.DOC_FOLDER)]
        self.assertTrue(any(hd.TEXT["gap_truncated"].format(n=1000, line=10) in text for text in texts))


class Publication(Environment):
    def job(self, conversation="Claude s-1", a=1, b=8):
        return {"product": "claude", "conversation": conversation, "transcript": "/h.jsonl", "cwd": str(self.cwd),
                "folder": str(self.cwd / hd.DOC_FOLDER), "trigger": hd.TEXT["trigger_user"], "previous": None,
                "range": {"a": a, "b": b, "ta": "2026-09-28T10:00:00Z", "tb": "2026-09-28T10:00:06Z"},
                "gap_notes": [], "last_part": True}

    def test_no_overwrite_and_index(self):
        folder = self.cwd / hd.DOC_FOLDER
        folder.mkdir()
        now = hd.dt.datetime.now().astimezone()
        for seconds in range(0, 3):
            name = "handoff-{}.md".format((now + hd.dt.timedelta(seconds=seconds)).strftime("%Y%m%d-%H%M%S"))
            (folder / name).write_text("KEEP\n")
        name = hd.publish(self.job(), CONTENT)
        for existing in folder.glob("handoff-*.md"):
            if existing.name != name:
                self.assertEqual(existing.read_text(), "KEEP\n")
        index = (folder / "index.md").read_text().splitlines()
        self.assertEqual(len(index), 4)
        self.assertIn(name + " | Monthly report on Mondays | ", "\n".join(index))
        self.assertEqual(sum(hd.TEXT["no_summary"] in line for line in index), 3)
        text = (folder / name).read_text()
        self.assertIn("\n## " + hd.TEXT["sections"][0] + "\n", text)

    def test_empty_section_placeholder(self):
        name = hd.publish(self.job(), CONTENT)
        text = (self.cwd / hd.DOC_FOLDER / name).read_text()
        self.assertTrue(text.rstrip().endswith("## " + hd.TEXT["sections"][-1] + "\n\n" + hd.TEXT["empty"]))

    def test_outdated_same_base(self):
        self.assertIsNotNone(hd.publish(self.job(), CONTENT))
        self.assertIsNone(hd.publish(self.job(), CONTENT))

    def test_concurrent_conversations(self):
        jobs = [self.job(conversation="Claude s-{}".format(n)) for n in range(8)]
        with multiprocessing.get_context("fork").Pool(8) as pool:
            names = pool.starmap(hd.publish, [(job, CONTENT) for job in jobs])
        self.assertEqual(len(set(names)), 8)
        index = (self.cwd / hd.DOC_FOLDER / "index.md").read_text().splitlines()
        self.assertEqual(len(index), 8)

    def test_concurrent_same_conversation(self):
        with multiprocessing.get_context("fork").Pool(6) as pool:
            names = pool.starmap(hd.publish, [(self.job(), CONTENT)] * 6)
        self.assertEqual(sum(n is not None for n in names), 1)

    def test_malformed_handoff_does_not_block(self):
        folder = self.cwd / hd.DOC_FOLDER
        folder.mkdir()
        (folder / "handoff-20260101-000000.md").write_text("# Handoff\n\n## Extra\nbroken\n")
        name = hd.publish(self.job(), CONTENT)
        self.assertIsNotNone(name)
        self.assertIn("handoff-20260101-000000.md | " + hd.TEXT["no_summary"], (folder / "index.md").read_text())
        self.assertIn("handoff-20260101-000000.md", (folder / name).read_text())

    def test_summary_is_masked(self):
        folder = self.cwd / hd.DOC_FOLDER
        name = hd.publish(self.job(), dict(CONTENT, summary="password=TEST_ONLY_MARKER"))
        self.assertNotIn("TEST_ONLY_MARKER", (folder / name).read_text())
        self.assertNotIn("TEST_ONLY_MARKER", (folder / "index.md").read_text())
        label = "- {}: ".format(hd.TEXT["labels"]["summary"])
        older = folder / "handoff-20260101-000000.md"
        text = (folder / name).read_text()
        start = text.index(label) + len(label)
        older.write_text(text[:start] + "token=OLDER_MARKER" + text[text.index("\n", start):])
        hd.rebuild_index(folder)
        self.assertNotIn("OLDER_MARKER", (folder / "index.md").read_text())
        self.assertIn("OLDER_MARKER", older.read_text())

    def test_publication_without_hard_links(self):
        folder = self.cwd / hd.DOC_FOLDER
        real_replace = os.replace

        def full_disk(source, target):
            if Path(target).name.startswith("handoff-"):
                raise OSError(errno.ENOSPC, "disk full")
            return real_replace(source, target)
        with mock.patch.object(hd.os, "link", side_effect=OSError(errno.EOPNOTSUPP, "no hard links")):
            name = hd.publish(self.job(), CONTENT)
            self.assertIn(CONTENT["state"], (folder / name).read_text())
            with mock.patch.object(hd.os, "replace", side_effect=full_disk), self.assertRaises(OSError):
                hd.publish(self.job(a=9, b=12), CONTENT)
        self.assertEqual(sorted(p.name for p in folder.iterdir()), sorted([name, "index.md"]))
        self.assertEqual(hd.last_handoff(folder, "Claude s-1")["b"], 8)

    def test_failed_index_leaves_no_temporary_file(self):
        folder = self.cwd / hd.DOC_FOLDER
        (folder / "index.md").mkdir(parents=True)
        with self.assertRaises(hd.IndexFailure):
            hd.publish(self.job(), CONTENT)
        self.assertEqual(list(folder.glob(".*.tmp")), [])

    def test_repeated_section_title_is_removed(self):
        title = hd.TEXT["sections"][0]
        name = hd.publish(self.job(), dict(CONTENT, state="## {}\n\nState text.".format(title)))
        text = (self.cwd / hd.DOC_FOLDER / name).read_text()
        self.assertEqual(text.count(title), 1)

    def test_text_escaped_again_by_the_model(self):
        content = dict(CONTENT, summary="Monthly report\\non Mondays", state='Stopped at "step 2".\\n\\nNext: step 3.',
                       decisions='\\"I decided.\\"\\n- Keep `a\\nb` as is.',
                       gaps="Line one.\nThe literal \\n stays in a field with real line breaks.")
        name = hd.publish(self.job(), content)
        handoff = hd.read_handoff(self.cwd / hd.DOC_FOLDER / name)
        self.assertEqual(handoff["summary"], "Monthly report on Mondays")
        self.assertIn('Stopped at "step 2".\n\nNext: step 3.', handoff["text"])
        self.assertIn('"I decided."\n- Keep `a\\nb` as is.', handoff["text"])
        self.assertIn("The literal \\n stays", handoff["text"])
        # Undoing the escape must not remove the delimiters of a value before it is masked.
        secret = dict(CONTENT, summary='Note\\n--password "FICTIONAL_START \\"FICTIONAL_MIDDLE\\" FICTIONAL_END"',
                      state='Note\\npassword="FICTIONAL_START \\"FICTIONAL_MIDDLE\\" FICTIONAL_END"',
                      gaps='Note\\n{"password":"FICTIONAL_START \\"FICTIONAL_MIDDLE\\" FICTIONAL_END"}')
        name = hd.publish(self.job(a=9, b=10), secret)
        text = (self.cwd / hd.DOC_FOLDER / name).read_text()
        for fragment in ("FICTIONAL_START", "FICTIONAL_MIDDLE", "FICTIONAL_END"):
            self.assertNotIn(fragment, text)

    def test_summary_is_shortened(self):
        long_content = dict(CONTENT, summary="word " * 30)
        name = hd.publish(self.job(), long_content)
        handoff = hd.read_handoff(self.cwd / hd.DOC_FOLDER / name)
        self.assertLessEqual(len(handoff["summary"]), 60)
        self.assertIn(hd.TEXT["gap_summary_cut"], handoff["text"])


class Sources(Environment):
    """The model quotes the sources of its critical statements; the program checks them before publishing."""

    def job(self, extra=()):
        path = self.claude_history("s-1", extra=extra)
        return hd.prepare_job("claude", "s-1", path, self.cwd, hd.TEXT["trigger_user"])

    def source(self, line, quote, **changes):
        return dict({"ref": str(line), "quote": quote}, **changes)

    def text_of(self, job, line):
        spans = {str(s[0]): s for s in job["sources_index"]["messages"]}
        _, _, _, a, b = spans[str(line)]
        return job["prompt"][a:b]

    def assert_rejected(self, job, source, reason):
        with self.assertRaises(hd.Failure) as raised:
            hd.publish(job, dict(CONTENT, sources=[source]))
        self.assertIn(hd.TEXT[reason], str(raised.exception))
        return str(raised.exception)

    def test_index_points_to_each_message_and_block(self):
        job = self.job()
        for line, time, role, a, b in job["sources_index"]["messages"]:
            self.assertEqual(job["prompt"][a - len("[{} | {} | {}] ".format(line, time, role)):a], "[{} | {} | {}] ".format(line, time, role))
        self.assertEqual(self.text_of(job, 2), "I decided the report goes out on Mondays.")
        self.assertIn("<{}>".format(hd.TEXT["tag_previous"]), hd.TEXT["previous"])
        self.assertIn("<{}>".format(hd.TEXT["tag_documents"]), hd.TEXT["documents"])

    def test_invalid_sources_publish_nothing_and_keep_the_resume_point(self):
        job = self.job()
        good = self.source(2, "I decided the report goes out on Mondays.")
        cases = {"source_missing": dict(good, ref="99"), "source_quote": dict(good, quote="I decided the report goes out on Fridays."),
                 "source_incomplete": dict(good, quote=" ")}
        for reason, source in cases.items():
            with self.subTest(reason):
                self.assert_rejected(job, source, reason)
        self.assert_rejected(job, dict(good, quote="I decided the report goes out on Mondays. … keep token"), "source_quote")
        self.assertEqual(list((self.cwd / hd.DOC_FOLDER).glob("handoff-*.md")), [])
        self.assertEqual(self.job()["range"], job["range"])
        cut = dict(good, quote="I decided … on Mondays.")
        self.assertIsNotNone(hd.publish(job, dict(CONTENT, sources=[good, cut])))

    def test_quote_with_a_literal_backslash_n_matches(self):
        said = "I authorized documenting the meaning of \\n without running commands."
        job = self.job(extra=[claude_record("s-1", "user", said, "2026-09-28T10:05:00.000Z")])
        line = job["sources_index"]["messages"][-1][0]
        self.assertEqual(self.text_of(job, line), said)
        self.assertTrue(hd.quoted("line one\\nline two", "line one\nline two"))
        self.assertIsNotNone(hd.publish(job, dict(CONTENT, sources=[self.source(line, said)])))

    def test_quote_ignores_only_recognized_formatting(self):
        accepted = [
            ("**On this machine**, there are 51 sessions. To restore it:\n\n```bash\ncodex unarchive 01a0\n```\n\nEnd.",
             "On this machine, there are 51 sessions. To restore it: `codex unarchive 01a0`"),
            ("Yes. **`codex resume` is the equivalent of `claude --resume`**. See.", "Yes. codex resume is the equivalent of claude --resume. See."),
            ("- **Simulated:** `systemctl`, ports and health.", "Simulated:** `systemctl`, ports and health."),
            ("The global file is intact (`4fc377b1…`); the Mac was not accessed.", "The global file is intact (`4fc377b1…`); the Mac was not accessed."),
            ("I authorized changing only `foo_bar`.", "I authorized changing only foo_bar."),
        ]
        rejected = [
            ("I authorized changing only foo_bar.", "I authorized changing only foobar."),
            ("I authorized removing only data_*.csv.", "I authorized removing only data.csv."),
            ("Use the expression 2**3.", "Use the expression 23."),
            ("I authorized changing only `foo_bar`.", "I authorized changing only `foobar`."),
            ("I authorized changing only `foo_bar`.", "I authorized changing only foobar."),
            ("**On this machine**, there are 51 sessions.", "On this machine, there are 52 sessions."),
            ("No, I authorized reading only.", "No I authorized reading only."),
        ]
        for source, quote in accepted:
            self.assertTrue(hd.quoted(quote, source), quote)
        for source, quote in rejected:
            self.assertFalse(hd.quoted(quote, source), quote)

    def test_reserved_characters_are_compared_literally(self):
        marked = "A" + chr(0xE001) + "B"
        held = "A" + chr(0xE000) + "0" + chr(0xE000) + "B"
        self.assertFalse(hd.quoted("AB", marked))
        self.assertTrue(hd.quoted(marked, marked))
        self.assertFalse(hd.quoted("A0B", held))
        self.assertTrue(hd.quoted(held, held))

    def test_labeled_line_reference_only_on_its_own(self):
        job = self.job()
        quote = "I decided the report goes out on Mondays."
        for ref in ("line 2", "Linha 2", "[line 2]"):
            hd.verify_sources(job, dict(CONTENT, sources=[{"ref": ref, "quote": quote}]))
        refused = {"line 2 or 8": "source_missing", "lines 2-8": "source_missing", "linha 2 e 8": "source_missing",
                   "the user said 2": "source_missing", "line 99": "source_missing", "line 8": "source_quote",
                   True: "source_incomplete"}
        for ref, reason in refused.items():
            with self.subTest(ref):
                self.assert_rejected(job, {"ref": ref, "quote": quote}, reason)

    def test_masked_secret_cannot_be_quoted_back(self):
        job = self.job()
        masked = self.text_of(job, 8)
        self.assertIn(hd.TEXT["hidden"], masked)
        message = self.assert_rejected(job, self.source(8, masked.replace(hd.TEXT["hidden"], "abc123")), "source_quote")
        self.assertNotIn("abc123", message)
        self.assertIsNotNone(hd.publish(job, dict(CONTENT, sources=[self.source(8, masked)])))

    def test_previous_handoff_is_a_source(self):
        first = self.job()
        hd.publish(first, dict(CONTENT, decisions='Authorized: "send the report on Mondays" (user, 2026-09-28).'))
        later = claude_record("s-1", "user", "Also add the chart.", "2026-09-28T10:05:00.000Z")
        second = self.job(extra=[later])
        self.assertEqual(second["range"]["a"], first["range"]["b"] + 1)
        inherited = {"ref": hd.TEXT["tag_previous"], "quote": '"send the report on Mondays"'}
        self.assert_rejected(second, dict(inherited, quote='"send the report on Fridays"'), "source_quote")
        self.assertIsNotNone(hd.publish(second, dict(CONTENT, sources=[inherited])))

    def test_manual_codex_publish_checks_sources(self):
        path = self.codex_history("c-1")
        out = self.temp / "job.json"
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(hd.main(["prepare", "codex", "--session", "c-1", "--transcript", str(path),
                                      "--cwd", str(self.cwd), "--out", str(out)]), 0)
        job = json.loads(out.read_text())
        bad = {"ref": "4", "quote": "an invented passage"}
        Path(job["content_path"]).write_text(json.dumps(dict(CONTENT, sources=[bad])))
        with contextlib.redirect_stdout(io.StringIO()) as buffer:
            self.assertEqual(hd.main(["publish", "--job", str(out)]), 1)
        self.assertIn(hd.TEXT["source_quote"], buffer.getvalue())
        self.assertNotIn("an invented passage", buffer.getvalue())
        self.assertTrue(out.exists())
        self.assertEqual(hd.handoffs(self.cwd / hd.DOC_FOLDER), [])
        good = dict(bad, ref=4, quote="I decided the report goes out on Mondays.")
        Path(job["content_path"]).write_text(json.dumps(dict(CONTENT, sources=[good])))
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(hd.main(["publish", "--job", str(out)]), 0)
        self.assertEqual(len(hd.handoffs(self.cwd / hd.DOC_FOLDER)), 1)


class Commands(Environment):
    def hook(self, event, env=None):
        environment = dict(os.environ, **(env or {}))
        return subprocess.run([sys.executable, str(PROGRAM), "hook"], input=json.dumps(event), text=True,
                              capture_output=True, env=environment, cwd=str(self.cwd))

    def event(self, path, session):
        return {"hook_event_name": "PreCompact", "session_id": session, "transcript_path": str(path), "cwd": str(self.cwd)}

    def test_hook_claude_success_then_nothing_new(self):
        path = self.claude_history("s-1")
        first = self.hook(self.event(path, "s-1"))
        self.assertEqual(first.returncode, 0, first.stderr)
        folder = self.cwd / hd.DOC_FOLDER
        self.assertEqual(len(list(folder.glob("handoff-*.md"))), 1)
        second = self.hook(self.event(path, "s-1"))
        self.assertEqual(second.returncode, 0)
        self.assertEqual(len(list(folder.glob("handoff-*.md"))), 1)
        handoff = hd.read_handoff(next(folder.glob("handoff-*.md")))
        self.assertEqual((handoff["a"], handoff["b"]), (1, 8))
        self.assertEqual(handoff["conversation"], "Claude s-1")

    def test_hook_failures_by_product(self):
        environment = {"FAKE_MODE": "fail"}
        claude = self.hook(self.event(self.claude_history("s-1"), "s-1"), environment)
        self.assertEqual(claude.returncode, 2)
        self.assertNotIn("secret with spaces", claude.stderr)
        codex = self.hook(self.event(self.codex_history("c-1"), "c-1"), environment)
        self.assertEqual(codex.returncode, 1)
        self.assertIn("systemMessage", codex.stdout)
        self.assertNotIn("secret with spaces", codex.stdout + codex.stderr)
        log = Path(os.environ["HOPPER_DOCUMENTATION_LOG"]).read_text()
        self.assertNotIn("secret with spaces", log)

    def test_hook_without_history_file(self):
        result = self.hook({"hook_event_name": "PreCompact", "session_id": "c-1", "transcript_path": None,
                            "cwd": str(self.cwd), "turn_id": "t"})
        self.assertEqual((result.returncode, result.stdout.strip()), (0, "{}"))
        self.assertFalse((self.cwd / hd.DOC_FOLDER).exists())

    def test_codex_failure_reason_without_the_echoed_prompt(self):
        environment = {"FAKE_MODE": "echo"}
        result = self.hook(self.event(self.codex_history("c-1"), "c-1"), environment)
        record = json.loads(Path(os.environ["HOPPER_DOCUMENTATION_LOG"]).read_text().splitlines()[-1])
        self.assertEqual(result.returncode, 1)
        self.assertIn("ERROR: model not supported", record["reason"])
        self.assertEqual(record["reason"].count("ERROR"), 1)
        self.assertNotIn("I decided the report goes out on Mondays", record["reason"])

    def test_claude_error_reported_in_its_json_output(self):
        result = self.hook(self.event(self.claude_history("s-1"), "s-1"), {"FAKE_MODE": "notlogged"})
        record = json.loads(Path(os.environ["HOPPER_DOCUMENTATION_LOG"]).read_text().splitlines()[-1])
        self.assertEqual(result.returncode, 2)
        self.assertIn("Not logged in", record["reason"])
        self.assertIn("Not logged in", result.stderr)

    def test_hook_reentry_and_invalid_event(self):
        guarded = self.hook({"anything": 1}, {"HOPPER_DOCUMENTATION_RUN": "1"})
        self.assertEqual((guarded.returncode, guarded.stdout.strip()), (0, "{}"))
        invalid = self.hook({"hook_event_name": "PreCompact"})
        self.assertEqual(invalid.returncode, 2)

    def test_codex_detection_and_existing_documents(self):
        (self.cwd / "README.md").write_text("# Project\nOld decision.\n")
        (self.cwd / "node_modules").mkdir()
        (self.cwd / "node_modules" / "README.md").write_text("DEPENDENCY_MARKER")
        (self.cwd / ".hidden").mkdir()
        (self.cwd / ".hidden" / "notes.md").write_text("HIDDEN_MARKER")
        path = self.codex_history("c-1")
        job = hd.prepare_job("codex", "c-1", path, self.cwd, hd.TEXT["trigger_user"])
        self.assertIn("Old decision.", job["prompt"])
        self.assertNotIn("DEPENDENCY_MARKER", job["prompt"])
        self.assertNotIn("HIDDEN_MARKER", job["prompt"])
        result = self.hook(self.event(path, "c-1"))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("systemMessage", result.stdout)

    def test_index_failure_is_reported_and_repaired(self):
        path = self.codex_history("c-1")
        with mock.patch.object(hd, "call_model", return_value=dict(CONTENT)), \
                mock.patch.object(hd, "rebuild_index", side_effect=OSError("index write failure")):
            first = hd.document("codex", "c-1", path, self.cwd, hd.TEXT["trigger_user"])
        self.assertEqual((first["status"], len(first["files"])), ("partial", 1))
        with mock.patch.object(hd, "call_model", side_effect=AssertionError("the model must not be called")):
            second = hd.document("codex", "c-1", path, self.cwd, hd.TEXT["trigger_user"])
        self.assertEqual(second["status"], "nothing_new")
        index = (self.cwd / hd.DOC_FOLDER / "index.md").read_text().splitlines()
        self.assertEqual([line.split(" | ")[0] for line in index], first["files"])

    def test_manual_codex_covers_every_part(self):
        def line(n, text):
            return {"timestamp": "2026-09-28T10:00:{:02d}.000Z".format(n), "type": "response_item", "payload": {
                "type": "message", "role": "user", "content": [{"type": "input_text", "text": text}]}}
        path = self.codex_history("c-1", extra=[line(n, "PART{} ".format(n) + "x" * 700) for n in (3, 4, 5)])
        out = self.temp / "job.json"
        prompts, outputs = [], []
        with mock.patch.object(hd, "PART_LIMIT", 1000):
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(hd.main(["prepare", "codex", "--session", "c-1", "--transcript", str(path),
                                          "--cwd", str(self.cwd), "--out", str(out)]), 0)
            with open(path, "a", encoding="utf-8") as history:
                history.write(json.dumps(line(9, "LATER_MESSAGE")) + "\n")
            while out.exists() and len(prompts) < 10:
                job = json.loads(out.read_text())
                prompts.append(job["prompt"])
                Path(job["content_path"]).write_text(json.dumps(CONTENT))
                with contextlib.redirect_stdout(io.StringIO()) as buffer:
                    code = hd.main(["publish", "--job", str(out)])
                outputs.append(buffer.getvalue())
                self.assertEqual(code, 0, buffer.getvalue())
        self.assertEqual(len(prompts), 3)
        joined = "\n".join(prompts)
        for n in (3, 4, 5):
            self.assertEqual(joined.count("PART{} ".format(n)), 1)
        self.assertNotIn("LATER_MESSAGE", joined)
        self.assertTrue(all(str(out) in text for text in outputs[:-1]))
        self.assertNotIn(str(out), outputs[-1])
        self.assertFalse(Path(job["content_path"]).exists())
        recorded = hd.handoffs(self.cwd / hd.DOC_FOLDER)
        self.assertEqual((len(recorded), max(h["b"] for h in recorded)), (3, 11))

    @unittest.skipIf(os.geteuid() == 0, "root writes every file")
    def test_manual_codex_reports_partial_when_next_part_fails(self):
        def line(n, text):
            return {"timestamp": "2026-09-28T10:00:{:02d}.000Z".format(n), "type": "response_item", "payload": {
                "type": "message", "role": "user", "content": [{"type": "input_text", "text": text}]}}
        path = self.codex_history("c-1", extra=[line(n, "PART{} ".format(n) + "x" * 700) for n in (3, 4, 5)])
        out = self.temp / "job.json"
        with mock.patch.object(hd, "PART_LIMIT", 1000):
            with contextlib.redirect_stdout(io.StringIO()):
                hd.main(["prepare", "codex", "--session", "c-1", "--transcript", str(path), "--cwd", str(self.cwd),
                         "--out", str(out)])
            job = json.loads(out.read_text())
            Path(job["content_path"]).write_text(json.dumps(CONTENT))
            out.chmod(0o400)
            with contextlib.redirect_stdout(io.StringIO()) as buffer:
                code = hd.main(["publish", "--job", str(out)])
        line_reached = job["range"]["b"]
        self.assertEqual(code, 1)
        self.assertTrue(buffer.getvalue().startswith(hd.TEXT["result_partial"].format(line=line_reached, reason="")))
        record = json.loads(Path(os.environ["HOPPER_DOCUMENTATION_LOG"]).read_text().splitlines()[-1])
        recorded = hd.handoffs(self.cwd / hd.DOC_FOLDER)
        self.assertEqual((record["status"], record["files"], record["line"]), ("partial", [recorded[0]["name"]], line_reached))
        self.assertEqual((len(recorded), recorded[0]["b"]), (1, line_reached))
        self.assertIn(recorded[0]["name"], (self.cwd / hd.DOC_FOLDER / "index.md").read_text())
        self.assertFalse(out.exists())
        self.assertFalse(Path(job["content_path"]).exists())
        with mock.patch.object(hd, "PART_LIMIT", 1000):
            again = hd.prepare_job("codex", "c-1", path, self.cwd, hd.TEXT["trigger_user"])
        self.assertEqual(again["range"]["a"], line_reached + 1)

    def test_model_commands_turn_off_tools(self):
        calls = []

        environments = []

        def fake_run(command, **kwargs):
            calls.append(command)
            environments.append(kwargs.get("env") or {})
            output = {"type": "result", "is_error": False, "structured_output": CONTENT} if "-p" in command else CONTENT
            return subprocess.CompletedProcess(command, 0, json.dumps(output), "")
        with mock.patch.object(hd.subprocess, "run", side_effect=fake_run):
            hd.call_model("claude", "prompt", str(self.cwd))
            hd.call_model("codex", "prompt", str(self.cwd))
        claude, codex = calls
        self.assertEqual(claude[claude.index("--tools") + 1], "")
        self.assertIn("--strict-mcp-config", claude)
        self.assertEqual(claude[claude.index("--system-prompt") + 1], hd.TEXT["system"])
        self.assertEqual(claude[claude.index("--append-system-prompt") + 1], hd.THINK_FIRST)
        for flag in ("read-only", "--ignore-user-config", 'web_search="disabled"', "features.apps=false", "project_doc_max_bytes=0"):
            self.assertIn(flag, codex)
        for name in ("CLAUDE_CODE_SAFE_MODE", "CLAUDE_CODE_DISABLE_CLAUDE_MDS", "CLAUDE_CODE_DISABLE_AUTO_MEMORY"):
            self.assertEqual(environments[0].get(name), "1")

    @unittest.skipIf(os.geteuid() == 0, "root reads every file")
    def test_unreadable_documentation_is_reported(self):
        denied = self.cwd / "README.md"
        denied.write_text("DENIED_MARKER")
        closed = self.cwd / "closed"
        closed.mkdir()
        (closed / "notes.md").write_text("CLOSED_MARKER")
        (self.cwd / "empty.md").write_text(" \n")
        denied.chmod(0)
        closed.chmod(0)
        try:
            body, unread, failed = hd.existing_documents(self.cwd)
            job = hd.prepare_job("codex", "c-1", self.codex_history("c-1"), self.cwd, hd.TEXT["trigger_user"])
        finally:
            denied.chmod(0o600)
            closed.chmod(0o700)
        reason = hd.TEXT["reason_denied"]
        self.assertEqual(failed, [(str(denied), reason), (str(closed), reason)])
        paths = "{} ({}), {} ({})".format(denied, reason, closed, reason)
        self.assertIn(hd.TEXT["gap_docs_unreadable"].format(n=2, paths=paths), job["gap_notes"])
        self.assertNotIn("DENIED_MARKER", job["prompt"])
        self.assertNotIn("empty.md", job["prompt"])

    def test_existing_documents_limits(self):
        (self.cwd / "README.md").write_text("R" * 30)
        (self.cwd / "empty.md").write_text("\n\n")
        (self.cwd / "docs").mkdir()
        (self.cwd / "docs" / "a.md").write_text("A" * 40)
        (self.cwd / "docs" / "b.md").write_text("B" * 40)
        nested = self.cwd / "docs" / "sub" / hd.DOC_FOLDER
        nested.mkdir(parents=True)
        (nested / "handoff-20260101-000000.md").write_text("NESTED_HANDOFF")
        os.utime(self.cwd / "docs" / "b.md", (1_000_000_000, 1_000_000_000))
        body, unread, failed = hd.existing_documents(self.cwd)
        self.assertIn("NESTED_HANDOFF", body)
        self.assertNotIn("empty.md", body)
        self.assertEqual((unread, failed), ([], []))
        with mock.patch.object(hd, "DOCS_BUDGET", 50), mock.patch.object(hd, "DOCS_LISTED", 2):
            body, unread, failed = hd.existing_documents(self.cwd)
            job = hd.prepare_job("codex", "c-1", self.codex_history("c-1"), self.cwd, hd.TEXT["trigger_user"])
        self.assertIn("A" * 20, body)
        self.assertNotIn("A" * 21, body)
        expected = [str(self.cwd / "docs" / "a.md"), str(self.cwd / "docs" / "b.md"),
                    str(nested / "handoff-20260101-000000.md")]
        self.assertEqual(unread, expected)
        self.assertIn(hd.TEXT["gap_docs_budget"].format(n=3, paths=", ".join(expected[:2]) + ", ..."), job["gap_notes"])

    def test_existing_documents_recent_first(self):
        (self.cwd / "old.md").write_text("OLD_DOCUMENT")
        (self.cwd / "new.md").write_text("NEW_DOCUMENT")
        os.utime(self.cwd / "old.md", (1_000_000_000, 1_000_000_000))
        with mock.patch.object(hd, "DOCS_BUDGET", 12):
            body, unread, failed = hd.existing_documents(self.cwd)
        self.assertIn("NEW_DOCUMENT", body)
        self.assertEqual(unread, [str(self.cwd / "old.md")])

    def test_prepare_and_publish(self):
        secret = 'tool --password "Alpha123 bravo456" --user reviewer; a senha é "Alpha123 bravo456" hoje; ' + SPACED_TOKEN
        path = self.codex_history("c-1", extra=[{"timestamp": "2026-09-28T10:00:03.000Z", "type": "response_item",
                                                  "payload": {"type": "message", "role": "user",
                                                              "content": [{"type": "input_text", "text": secret}]}}])
        out = self.temp / "job.json"
        prepared = subprocess.run([sys.executable, str(PROGRAM), "prepare", "codex", "--session", "c-1",
                                   "--transcript", str(path), "--cwd", str(self.cwd), "--out", str(out)],
                                  text=True, capture_output=True)
        self.assertEqual(prepared.returncode, 0, prepared.stderr)
        job = json.loads(out.read_text())
        self.assertIn("--user reviewer", job["prompt"])
        Path(job["content_path"]).write_text(json.dumps(dict(CONTENT, state=secret)))
        self.assertIn(job["content_path"], job["prompt"])
        published = subprocess.run([sys.executable, str(PROGRAM), "publish", "--job", str(out)], text=True, capture_output=True)
        self.assertEqual(published.returncode, 0, published.stdout + published.stderr)
        self.assertFalse(out.exists())
        handoffs = [p.read_text() for p in (self.cwd / hd.DOC_FOLDER).glob("handoff-*.md")]
        self.assertIn("--user reviewer", handoffs[0])
        for fragment in ["Alpha123", "bravo456"] + SPACED_TOKEN.split("."):
            self.assertNotIn(fragment, job["prompt"])
            self.assertNotIn(fragment, handoffs[0])
        again = subprocess.run([sys.executable, str(PROGRAM), "prepare", "codex", "--session", "c-1",
                                "--transcript", str(path), "--cwd", str(self.cwd), "--out", str(out)],
                               text=True, capture_output=True)
        self.assertEqual(again.stdout.strip(), hd.TEXT["result_nothing"])

    def test_run_and_config(self):
        path = self.claude_history("s-1")
        run = subprocess.run([sys.executable, str(PROGRAM), "run", "claude", "--session", "s-1", "--transcript", str(path),
                              "--cwd", str(self.cwd)], text=True, capture_output=True)
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        config = subprocess.run([sys.executable, str(PROGRAM), "config", "codex"], text=True, capture_output=True)
        self.assertEqual(json.loads(config.stdout), {"model": "gpt-6-luna", "effort": "xhigh"})

    def test_log_falls_back_to_the_lock_folder(self):
        blocked = self.temp / "file"
        blocked.write_text("")
        with mock.patch.object(hd, "log_path", return_value=blocked / "log.jsonl"):
            hd.write_log({"status": "done"})
        fallback = Path(tempfile.gettempdir()) / "hopper-documentation-{}".format(os.getuid()) / "log.jsonl"
        self.assertEqual(json.loads(fallback.read_text())["status"], "done")

    def test_zone_label(self):
        now = hd.dt.datetime(2026, 9, 28, 10, tzinfo=hd.dt.timezone(hd.dt.timedelta(hours=5, minutes=30)))
        self.assertTrue(hd.zone_label(now).endswith("UTC+5:30"))
        now = hd.dt.datetime(2026, 9, 28, 10, tzinfo=hd.dt.timezone(hd.dt.timedelta(hours=-3)))
        self.assertTrue(hd.zone_label(now).endswith("UTC-3"))


if __name__ == "__main__":
    unittest.main()
