"""Compile a persona profile (+ optional retrieved context) into a system prompt.

Kept small and single-purpose so it works well with an ~8B local model. In P2
this grows task-specific variants (chat vs. draft-post vs. classify) and folds
in retrieved persona knowledge; for now it produces the chat system prompt.
"""

from .profile import PersonaProfile


def build_system_prompt(profile: PersonaProfile, context: str | None = None) -> str:
    lines = [
        f"You are {profile.name}. {profile.tagline}",
        f"Your niche: {profile.niche}.",
        "",
        "Who you are:",
        f"- You are a fictional persona. {profile.ai_disclosure}",
        "- Never deny being an AI, and never claim first-hand human experiences as your own.",
    ]

    if profile.voice_rules:
        lines.append("")
        lines.append("How you speak:")
        lines.extend(f"- {rule}" for rule in profile.voice_rules)

    if profile.backstory:
        lines.append("")
        lines.append("Your backstory (fictional, keep it consistent):")
        lines.append(profile.backstory)

    if context:
        lines.append("")
        lines.append("Relevant things you know (use if helpful, don't force it):")
        lines.append(context)

    return "\n".join(lines)
