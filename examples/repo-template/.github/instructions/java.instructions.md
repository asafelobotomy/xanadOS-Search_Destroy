---

# Java/Kotlin-specific Copilot Instructions


## Technology Recommendations

- Use `JUnit 5` for unit and integration tests
- Use `Spotless` with `Google Style` for formatting
- Use `Gradle` (preferred) or `Maven` for builds
- Use `Mockito` for test doubles

## Error Handling

- Use checked exceptions sparingly
- Prefer RuntimeExceptions for programming errors
- Use Optional for nullable values

- Respect the build tool in use (Gradle/Maven) and existing project layout (`src/main/java`, `src/test/java`).
- Keep unit tests fast and isolated; avoid over-mocking.
- Follow existing code style and formatters; don't reformat unrelated files.
- Prefer immutability and clear nullability; in Kotlin, use non-null types and `sealed`/`data` when appropriate.
- Avoid introducing new modules unless warranted by clear boundaries. "**/*.{java,kt,kts,gradle}"
---

# Java/Kotlin-specific Copilot Instructions

- Respect the build tool in use (Gradle/Maven) and existing project layout (`src/main/java`, `src/test/java`).
- Write tests with JUnit 5 (or the project’s chosen framework); keep unit tests fast and isolated.
- Use Mockito (or project standard) for doubles; avoid over-mocking.
- Follow existing code style and formatters (Spotless/Google Style); don’t reformat unrelated files.
- Prefer immutability and clear nullability; in Kotlin, use non-null types and `sealed`/`data` when appropriate.
- Avoid introducing new modules unless warranted by clear boundaries.
