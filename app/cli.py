"""Quick local test:  python -m app.cli "Savol..."   (or no args for interactive)."""
import asyncio
import logging
import sys

from .config import load_env

load_env()
from . import agent, llm  # noqa: E402


async def one(q: str):
    r = await agent.ask(q)
    print("=" * 80)
    print("Q:", q)
    print("A:", r.answer)
    print(f"-- {r.provider} · {r.seconds:.1f}s · ok={r.ok}")
    for x in r.queries:
        print("   >", (x["sql"] or "").replace("\n", " ")[:300], "| rows:", x["rows"], "| err:", (x["error"] or "")[:150])


def main():
    logging.basicConfig(level=logging.WARNING)
    print("providers:", llm.configured())
    if len(sys.argv) > 1:
        async def all_():
            for q in sys.argv[1:]:
                await one(q)
        asyncio.run(all_())
    else:
        while True:
            q = input("> ").strip()
            if q:
                asyncio.run(one(q))


if __name__ == "__main__":
    main()
