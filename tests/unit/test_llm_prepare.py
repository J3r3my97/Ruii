"""LLMClient._prepare injects the /no_think directive correctly."""

import joe.config as config
from joe.llm.client import LLMClient


def _prepare(messages, no_think):
    original = config.settings.LLM_NO_THINK
    config.settings.LLM_NO_THINK = no_think
    try:
        return LLMClient._prepare(messages)
    finally:
        config.settings.LLM_NO_THINK = original


def test_appends_to_existing_system_message():
    msgs = [{"role": "system", "content": "You are Joe."}, {"role": "user", "content": "hi"}]
    out = _prepare(msgs, no_think=True)
    assert out[0]["content"].endswith("/no_think")
    assert "You are Joe." in out[0]["content"]
    assert out[1] == {"role": "user", "content": "hi"}


def test_adds_system_message_when_absent():
    msgs = [{"role": "user", "content": "hi"}]
    out = _prepare(msgs, no_think=True)
    assert out[0] == {"role": "system", "content": "/no_think"}
    assert out[1] == {"role": "user", "content": "hi"}


def test_noop_when_disabled():
    msgs = [{"role": "system", "content": "You are Joe."}, {"role": "user", "content": "hi"}]
    out = _prepare(msgs, no_think=False)
    assert out == msgs


def test_does_not_mutate_input():
    msgs = [{"role": "system", "content": "You are Joe."}]
    _prepare(msgs, no_think=True)
    assert msgs[0]["content"] == "You are Joe."
