# Using Prompt Files with Copilot in VS Code

This guide shows how to use prompt files (`.prompt.md`) for repeatable tasks.

## Why prompt files

- Keep common tasks consistent and discoverable.
- Reduce prompt drafting time and mistakes.
- Encourage team-wide reuse and improvements.

## Where they live

- Store reusable prompts in `.GitHub/prompts/`.
- Keep each prompt focused on one task and under ~200 lines.

## VS Code settings (optional)

Enable automatic inclusion of instruction and prompt files:

- `GitHub.Copilot.chat.codeGeneration.useInstructionFiles: true`
- `GitHub.Copilot.chat.promptFiles: true`

Open the Chat panel and attach a prompt file as needed.

## Example tasks

1. Testing sweep
- File: `.GitHub/prompts/tdd-implementation.prompt.md`
- Use: open relevant test files, attach prompt, then ask for test updates.
2. Security review
- File: `.GitHub/prompts/security-review.prompt.md`
- Use: attach prompt, point to changed files or PR diff.
3. Performance check
- File: `.GitHub/prompts/performance-optimization.prompt.md`
- Use: attach prompt, add context with the main file or profile output.

## Tips

- Keep prompts imperative and specific.
- Prefer linking to existing instructions over repeating them.
- Update prompts when standards change; keep a short index in `.GitHub/prompts/`.
