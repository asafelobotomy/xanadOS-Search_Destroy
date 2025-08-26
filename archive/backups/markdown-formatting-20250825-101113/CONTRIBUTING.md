# Contributing

Thanks for contributing! This repository follows the Coding & Development Bible.

## Before you start

-

- Read `.GitHub/Copilot-instructions.md`and any`.GitHub/chatmodes/_.chatmode.md`or`.GitHub/prompts/_.prompt.md` that apply to your changes.
- Install linters/formatters per project configuration.

## Workflow

1. Create a feature branch.
2. Write or update tests under `tests/`mirroring`src/` paths.
3. Make focused code changes; avoid unrelated formatting.
4. Ensure `npm test`/`pytest` passes locally.
5. Open a PR with a concise description, assumptions, and tradeoffs.

## Notes

-

- Prefer reusing existing files/functions.
- Document public APIs with inputs/outputs and error modes.
