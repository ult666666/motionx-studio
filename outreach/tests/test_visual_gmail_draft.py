#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Gmail draft adapter: draft ops only, never send.

Run: python3 outreach/tests/test_visual_gmail_draft.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _vco_bootstrap  # noqa: E402
import safety  # noqa: E402
from gmail_draft import GmailDraftBackend  # noqa: E402


class _Execable:
    def __init__(self, recorder, name, result):
        self.recorder = recorder
        self.name = name
        self.result = result

    def execute(self):
        self.recorder.append(self.name)
        return self.result


class _Drafts:
    def __init__(self, recorder, labels):
        self.recorder = recorder
        self.labels = labels

    def create(self, userId, body):
        assert "raw" in body["message"]
        return _Execable(self.recorder, "drafts.create",
                         {"id": "d1", "message": {"id": "m1", "threadId": "t1"}})

    def update(self, userId, id, body):
        assert "raw" in body["message"]
        return _Execable(self.recorder, "drafts.update",
                         {"id": id, "message": {"id": "m2", "threadId": "t2"}})

    def get(self, userId, id, format):
        return _Execable(self.recorder, "drafts.get",
                         {"id": id, "message": {"id": "m", "threadId": "t",
                                                "labelIds": self.labels}})

    # A send method that MUST never be reached through the adapter.
    def send(self, *a, **k):  # pragma: no cover
        raise AssertionError("drafts.send must never be called by the adapter")


class _Users:
    def __init__(self, recorder, labels, account):
        self._drafts = _Drafts(recorder, labels)
        self._account = account
        self.recorder = recorder

    def drafts(self):
        return self._drafts

    def getProfile(self, userId):
        return _Execable(self.recorder, "getProfile", {"emailAddress": self._account})


class FakeService:
    def __init__(self, recorder, labels=("DRAFT",), account="charles@madebymotionx.com"):
        self._users = _Users(recorder, list(labels), account)

    def users(self):
        return self._users


def test_create_calls_only_drafts_create():
    rec = []
    b = GmailDraftBackend(service=FakeService(rec))
    resp = b.create_draft("cmF3")
    assert resp["id"] == "d1"
    assert rec == ["drafts.create"], rec


def test_update_calls_only_drafts_update():
    rec = []
    b = GmailDraftBackend(service=FakeService(rec))
    resp = b.update_draft("d9", "cmF3")
    assert resp["id"] == "d9"
    assert rec == ["drafts.update"], rec


def test_send_attribute_is_forbidden():
    b = GmailDraftBackend(service=FakeService([]))
    for name in ("send", "send_draft", "drafts_send", "schedule_send", "delete_draft",
                 "trash"):
        try:
            getattr(b, name)
            raise AssertionError(f"{name} must be forbidden")
        except safety.SendForbiddenError:
            pass


def test_safety_assertions_reject_send_ops():
    for op in ("messages.send", "drafts.send", "send", "messages.insert",
               "drafts.delete", "messages.trash"):
        try:
            safety.assert_not_send(op)
            raise AssertionError(f"{op} must be rejected")
        except safety.SendForbiddenError:
            pass
    # allowed ops pass
    for op in ("drafts.create", "drafts.update", "drafts.get", "drafts.list"):
        safety.assert_allowed_draft_op(op)


def test_verify_draft_only_true_for_draft_label():
    b = GmailDraftBackend(service=FakeService([], labels=("DRAFT",)))
    v = b.verify_draft_only("d1")
    assert v["draft_only"] is True and v["is_sent"] is False


def test_verify_draft_only_false_when_sent():
    b = GmailDraftBackend(service=FakeService([], labels=("DRAFT", "SENT")))
    v = b.verify_draft_only("d1")
    assert v["draft_only"] is False and v["is_sent"] is True


def test_verify_account_matches_and_mismatch_raises():
    b_ok = GmailDraftBackend(service=FakeService([], account="charles@madebymotionx.com"),
                             expected_account="charles@madebymotionx.com")
    assert b_ok.verify_account() == "charles@madebymotionx.com"
    b_bad = GmailDraftBackend(service=FakeService([], account="someoneelse@gmail.com"),
                              expected_account="charles@madebymotionx.com")
    try:
        b_bad.verify_account()
        raise AssertionError("wrong account must raise")
    except safety.WrongAccountError:
        pass


TESTS = [v for k, v in sorted(globals().items()) if k.startswith("test_")]

if __name__ == "__main__":
    ok = 0
    for t in TESTS:
        t()
        print("PASS", t.__name__)
        ok += 1
    print(f"\n{ok}/{len(TESTS)} passed")
