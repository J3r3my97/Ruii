"""Strip a reasoning ``<think>...</think>`` block from model output.

Some open-weights models (Qwen3, DeepSeek-R1, ...) prepend a chain-of-thought
block to their reply. Output-side stripping is the portable way to remove it —
it works identically whether the backend is Ollama, vLLM, or a hosted API, and
regardless of whether that backend honours a "disable thinking" request flag.

Canonical behaviour (both the batch and streaming strippers agree on this):
  * a leading run of whitespace, then at most one well-formed ``<think>...</think>``
    block, then more whitespace, is removed from the front of the reply;
  * an unclosed leading ``<think>`` (a truncated generation) drops everything —
    partial reasoning is never surfaced to users;
  * the remaining reply is left-trimmed and emitted verbatim.
Think blocks only ever appear at the very start of a reply, so mid-text ``<think>``
text is left untouched.
"""

import re

OPEN = "<think>"
CLOSE = "</think>"

_LEADING_CLOSED = re.compile(r"^\s*" + re.escape(OPEN) + r".*?" + re.escape(CLOSE) + r"\s*", re.DOTALL)
_LEADING_UNCLOSED = re.compile(r"^\s*" + re.escape(OPEN) + r".*\Z", re.DOTALL)


def strip_thinking(text: str) -> str:
    """Remove a leading think block from a fully-materialised string."""

    text = _LEADING_CLOSED.sub("", text, count=1)
    text = _LEADING_UNCLOSED.sub("", text, count=1)

    return text.lstrip()


class ThinkStripper:
    """Incremental equivalent of :func:`strip_thinking` for streamed output.

    A think block arrives split across arbitrarily-sized chunks, and the
    ``<think>`` / ``</think>`` tags themselves can straddle a chunk boundary.
    ``feed`` emits only the user-facing text resolved so far; ``flush`` releases
    anything still buffered once the stream ends.
    """

    def __init__(self, enabled: bool = True) -> None:
        self.enabled = enabled
        self._buf = ""
        self._pos = 0  # chars of _buf already emitted or consumed
        self._state = "lead"  # lead (deciding) | think (inside block) | body (emit verbatim)

    def feed(self, chunk: str) -> str:
        if not self.enabled:
            return chunk

        self._buf += chunk
        out = ""

        while True:
            if self._state == "body":
                out += self._buf[self._pos :]
                self._pos = len(self._buf)
                return out

            if self._state == "think":
                idx = self._buf.find(CLOSE, self._pos)
                if idx == -1:
                    return out  # close tag may span the next chunk; keep buffering
                self._pos = idx + len(CLOSE)
                self._state = "lead"
                continue

            # state == "lead": skip leading whitespace, then decide.
            while self._pos < len(self._buf) and self._buf[self._pos].isspace():
                self._pos += 1
            if self._pos >= len(self._buf):
                return out  # only whitespace so far — wait for a real token
            rest = self._buf[self._pos :]
            if rest.startswith(OPEN):
                self._pos += len(OPEN)
                self._state = "think"
                continue
            if OPEN.startswith(rest):
                return out  # e.g. "<th" — ambiguous, wait for more
            self._state = "body"
            continue

    def flush(self) -> str:
        if not self.enabled:
            return ""
        if self._state == "lead":
            while self._pos < len(self._buf) and self._buf[self._pos].isspace():
                self._pos += 1
            out = self._buf[self._pos :]
            self._pos = len(self._buf)
            return out
        return ""  # think: drop dangling reasoning; body: already fully emitted
