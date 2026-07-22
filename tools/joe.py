"""Joe agent CLI.

P1 ships the ``chat`` command: a terminal REPL that streams replies from the
local model in Joe's (placeholder) voice. Later phases add ``serve`` and
``seed-persona`` here.
"""

import asyncio

import click
from loguru import logger

from joe.config import settings
from joe.llm import LLMClient
from joe.persona import build_system_prompt, load_placeholder_profile


async def _chat_loop() -> None:
    profile = load_placeholder_profile()
    client = LLMClient()
    system_prompt = build_system_prompt(profile)

    messages: list[dict[str, str]] = [{"role": "system", "content": system_prompt}]

    click.echo(f"Chatting with {profile.name} via {settings.LLM_MODEL} ({settings.LLM_BASE_URL}).")
    click.echo("Type your message and press Enter. Ctrl-C or 'exit' to quit.\n")

    while True:
        try:
            user_text = click.prompt("you", prompt_suffix="> ")
        except (EOFError, KeyboardInterrupt):
            click.echo("\nbye.")
            return

        if user_text.strip().lower() in {"exit", "quit"}:
            click.echo("bye.")
            return

        messages.append({"role": "user", "content": user_text})

        click.echo(f"{profile.name.lower()}> ", nl=False)
        reply_parts: list[str] = []
        try:
            async for token in client.stream_chat(messages):
                reply_parts.append(token)
                click.echo(token, nl=False)
        except Exception as e:
            click.echo(f"\n[error talking to the model: {e}]")
            messages.pop()  # drop the unanswered user turn
            continue
        click.echo("\n")

        messages.append({"role": "assistant", "content": "".join(reply_parts)})


@click.group()
def cli() -> None:
    """Joe — autonomous persona agent."""


@cli.command()
def chat() -> None:
    """Chat with Joe in the terminal (streams from the local model)."""

    try:
        asyncio.run(_chat_loop())
    except KeyboardInterrupt:
        logger.info("Chat interrupted.")


if __name__ == "__main__":
    cli()
