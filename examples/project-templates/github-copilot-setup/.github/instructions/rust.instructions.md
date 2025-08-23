---
applyTo: "**/*.rs"
priority: 70
category: "language-specific"
---

# Rust-specific Copilot Instructions

## Technology Recommendations

- Use Rust's built-in test framework with `#[test]` attributes
- Use `clippy` for linting and `rustfmt` for formatting
- Use `cargo` for dependency management and builds

## Error Handling

- Use Result<T, E> for recoverable errors
- Use panic! only for unrecoverable errors
- Use ? operator for error propagation
- Create custom error types using thiserror or anyhow crates for complex error handling

## Context-Aware Rust Patterns

**CLI Applications**: Use clap for argument parsing, anyhow for error handling, env_logger for logging
**Web Services**: Use axum/warp for APIs, tokio for async runtime, serde for serialization
**System Programming**: Use unsafe code sparingly, document safety invariants, prefer safe abstractions
**Libraries/Crates**: Implement comprehensive documentation, use semantic versioning, provide examples

- Follow Rust's ownership and borrowing principles with RAII patterns
- Use `cargo test` for running tests, place integration tests in `tests/` directory
- Prefer explicit error handling over unwrap() in production code (use expect() with descriptive messages)
- Use lifetimes explicitly when needed, prefer 'static or owned data when lifetime complexity is high
- Follow Rust naming conventions (snake_case for functions, PascalCase for types, SCREAMING_SNAKE_CASE for constants)
- Use traits for shared behavior, keep impl blocks focused (max 10 methods per impl block)

**⚠️ SECURITY OVERRIDE: Audit all unsafe code blocks, validate bounds checking, sanitize external inputs before FFI calls**
