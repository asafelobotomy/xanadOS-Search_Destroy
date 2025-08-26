---
applyTo: "**/*.rb"
priority: 70
category: "language-specific"
---

# Ruby-specific Copilot Instructions

## Technology Recommendations

- Use `RSpec` for testing with descriptive specs
- Use `RuboCop` for linting and code style
- Use `Bundler` for dependency management

## Error Handling

- Use exceptions for exceptional conditions
- Return nil or Result objects for expected failures
- Use structured logging with Rails logger or custom loggers

## Context-Aware Ruby Patterns

**Rails Projects**: Use Rails conventions (MVC, ActiveRecord, strong parameters)
**Sinatra/API Projects**: Focus on lightweight patterns, JSON serialization, middleware
**Gems/Libraries**: Implement proper gemspec, semantic versioning, comprehensive documentation
**CLI Tools**: Use Thor or OptionParser, implement proper exit codes, help documentation

- Write descriptive tests with clear describe/context/it blocks using RSpec's nested structure
- Follow Ruby style guide and existing RuboCop configuration (prefer community style guide)
- Prefer explicit return values for public methods, allow implicit returns for private methods

- Use blocks with descriptive variable names: `users.each { |user| ... }`not`users.each { |u| ... }`
- Keep methods under 10 lines, classes under 100 lines for maintainability

## ⚠️ SECURITY OVERRIDE: Always use strong parameters in Rails, validate all user input, avoid eval() and instance_eval() with user data
