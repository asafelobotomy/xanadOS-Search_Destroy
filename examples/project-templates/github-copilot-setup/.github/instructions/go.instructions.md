---
applyTo: "**/*.go"

---

# Go-specific Copilot Instructions

## Technology Recommendations

- Use Go's built-in testing package with table-driven tests
- Use `golangci-lint`for linting and`gofmt` for formatting
- Use Go modules for dependency management

## Error Handling

- Handle errors explicitly; never ignore errors
- Wrap errors with context using `%w` verb
- Return errors as the last return value
- Use Go modules; respect existing module structure.
- Place tests in `*_test.go` using subtests for organization.
- Prefer contexts for cancellable operations; pass `context.Context` as first param when appropriate.
- Follow standard layout: keep packages cohesive; avoid stuttered names (`foo.Foo`).
- Use `golangci-lint`/`staticcheck` if configured; do not mass-reformat unrelated files.
- Be concurrency-safe; avoid shared mutable state; use channels or sync primitives judiciously.
