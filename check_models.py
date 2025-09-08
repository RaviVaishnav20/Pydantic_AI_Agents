import os
import sys
import asyncio
from typing import Optional, Tuple

from dotenv import load_dotenv

from pydantic_ai import Agent
from pydantic_ai.models.groq import GroqModel
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.models.google import GoogleModel


async def try_run(agent: Agent, label: str) -> Tuple[str, bool, Optional[str]]:
    try:
        _ = await agent.run("Say 'ok' only.")
        return label, True, None
    except Exception as exc:  # noqa: BLE001 - surface provider errors to user
        return label, False, str(exc)


async def amain() -> int:
    load_dotenv()

    checks: list[Tuple[str, bool, Optional[str]]] = []

    # Groq
    if os.getenv("GROQ_API_KEY"):
        groq_agent = Agent(GroqModel("llama-3.1-8b-instant"))
        checks.append(await try_run(groq_agent, "Groq llama-3.1-8b-instant"))
    else:
        checks.append(("Groq", False, "GROQ_API_KEY not set"))

    # OpenAI
    if os.getenv("OPENAI_API_KEY"):
        openai_agent = Agent(OpenAIChatModel("gpt-5-nano"))
        checks.append(await try_run(openai_agent, "OpenAI gpt-5-nano"))
    else:
        checks.append(("OpenAI", False, "OPENAI_API_KEY not set"))

    # # Google / Gemini
    if os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY"):
        google_agent = Agent(GoogleModel("gemini-2.5-flash"))
        checks.append(await try_run(google_agent, "Google Gemini 2.5-flash"))
    else:
        checks.append(("Google/Gemini", False, "GOOGLE_API_KEY/GEMINI_API_KEY not set"))

    ok = True
    print("\nModel check:")
    for name, success, error in checks:
        status = "OK" if success else "FAIL"
        print(f"- {name}: {status}")
        if error and not success:
            print(f"  reason: {error}")
        ok = ok and success

    return 0 if ok else 1


def main() -> int:
    return asyncio.run(amain())


if __name__ == "__main__":
    sys.exit(main())


