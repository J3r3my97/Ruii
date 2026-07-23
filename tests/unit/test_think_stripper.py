"""The streaming ThinkStripper must match the batch stripper for every chunking."""

import pytest

from joe.llm.think import ThinkStripper, strip_thinking


def _stream(text: str, chunk_size: int) -> str:
    stripper = ThinkStripper(enabled=True)
    out = []
    for i in range(0, len(text), chunk_size):
        out.append(stripper.feed(text[i : i + chunk_size]))
    out.append(stripper.flush())
    return "".join(out)


CASES = [
    "Hello there, how are you?",
    "<think>reasoning here</think>Actual answer.",
    "  <think>multi\nline\nreasoning</think>  Answer after whitespace.",
    "<think>a</think>",
    "No think block but a stray < in the middle.",
    "<not-think>keep this</not-think> intact",
    "Answer with <think> the word think but no tags really",
]


@pytest.mark.parametrize("text", CASES)
@pytest.mark.parametrize("chunk_size", [1, 2, 3, 5, 7, 100])
def test_streaming_matches_batch(text: str, chunk_size: int) -> None:
    assert _stream(text, chunk_size) == strip_thinking(text)


def test_disabled_passes_through() -> None:
    stripper = ThinkStripper(enabled=False)
    assert stripper.feed("<think>x</think>y") == "<think>x</think>y"
    assert stripper.flush() == ""


def test_token_by_token_think_block() -> None:
    # Tags split across single-character chunks must still be stripped.
    text = "<think>secret</think>visible"
    assert _stream(text, 1) == "visible"
