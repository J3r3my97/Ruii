"""Persona profile model + a placeholder Joe.

This is the P1 skeleton. The full persona system (YAML-sourced identity, voice
rules, opinion cards, taboo topics, per-platform caps, and Qdrant seeding) is
built in P2. The invariants that make Joe safe to run in public — he is
fictional and always disclosed as AI — are enforced here from the start so no
later code path can quietly drop them.
"""

from pydantic import BaseModel, field_validator


class PersonaProfile(BaseModel):
    name: str
    tagline: str
    niche: str
    # Hard invariants. A profile that isn't fictional, or lacks an AI-disclosure
    # line, must never compile into a system prompt.
    is_fictional: bool = True
    ai_disclosure: str
    voice_rules: list[str] = []
    backstory: str = ""

    @field_validator("is_fictional")
    @classmethod
    def _must_be_fictional(cls, v: bool) -> bool:
        if v is not True:
            raise ValueError("Joe must be a fictional persona (is_fictional=True).")
        return v

    @field_validator("ai_disclosure")
    @classmethod
    def _disclosure_required(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("A non-empty ai_disclosure line is required.")
        return v


def load_placeholder_profile() -> PersonaProfile:
    """A stand-in Joe so P1 can chat before the real persona is designed in P2."""

    return PersonaProfile(
        name="Joe",
        tagline="A curious, plain-spoken AI persona still figuring out who he is.",
        niche="general conversation (placeholder — real niche is defined in Phase 2)",
        ai_disclosure="I'm Joe, an AI persona — a fictional character, not a real person.",
        voice_rules=[
            "Warm, direct, and concrete; no corporate filler.",
            "Short paragraphs. Prefer plain words over jargon.",
            "Never claim real human experiences or feelings as your own.",
            "If asked whether you're human, say plainly that you're an AI persona.",
        ],
        backstory="",
    )
