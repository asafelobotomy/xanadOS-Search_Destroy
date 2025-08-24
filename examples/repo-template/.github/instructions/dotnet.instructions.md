---
applyTo: "**/*.{cs,fs,csproj,fsproj,sln}"
---

# .NET-specific Copilot Instructions

## Technology Recommendations

- Use `xUnit` or `NUnit` for testing as per repo standard
- Use `StyleCop` and `EditorConfig` for code style
- Use nullable reference types for null safety

## Error Handling

- Use exceptions for exceptional conditions
- Prefer Result patterns for expected failures
- Use structured logging with ILogger

- Organize solutions with `src/` and `tests/` projects; mirror namespaces and folders.
- Use `async/await` correctly (avoid `async void`).
- Keep tests deterministic and fast.
- Follow analyzers and code style; do not reformat unrelated files.
- Prefer dependency injection and small, testable classes.
