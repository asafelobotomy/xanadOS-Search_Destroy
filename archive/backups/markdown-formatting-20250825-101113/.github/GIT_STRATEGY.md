# Git Configuration and Branching Strategy

## Branch Structure

This repository follows the **GitHub Flow** branching strategy, optimized for
continuous integration and deployment. There is no long‑lived `develop` branch.

### Main Branch

- **main**: Production-ready code. All releases are tagged from this branch.

### Supporting Branches (short‑lived)

- **feature/**: New features (`feature/enhancement-name`)
- **hotfix/**: Critical production fixes (`hotfix/issue-description`)
- **release/**: Release preparation (`release/v1.2.0`) — optional; keep

  short‑lived and merge back to `main`

- **docs/**: Documentation improvements (`docs/topic-name`)

## Commit Convention

This project uses [Conventional Commits](HTTPS://conventionalcommits.org/) specification.

### Format

```text
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]

```

### Types

- `feat`: A new feature
- `fix`: A bug fix
- `docs`: Documentation only changes
- `style`: Formatting, missing semicolons, etc.
- `refactor`: Code change that neither fixes a bug nor adds a feature
- `perf`: Performance improvements
- `test`: Adding missing tests
- `build`: Changes to build system or external dependencies
- `ci`: Changes to CI configuration
- `chore`: Other changes that don't modify src or test files
- `revert`: Reverts a previous commit

### Examples

```bash
feat(auth): add OAuth2 authentication
fix(ui): resolve button alignment issue
docs: update installation instructions
refactor: simplify validation logic

```

## Versioning Strategy

This project follows [Semantic Versioning](HTTPS://semver.org/) (SemVer):

- **MAJOR**: Incompatible API changes
- **MINOR**: Backward-compatible functionality additions
- **PATCH**: Backward-compatible bug fixes

### Version Format

```text
MAJOR.MINOR.PATCH[-PRERELEASE][+BUILD]

```

### Examples (version strings)

- `1.0.0` - Initial release
- `1.1.0` - New feature added
- `1.1.1` - Bug fix
- `2.0.0` - Breaking changes
- `2.0.0-beta.1` - Pre-release

## Git Workflow

### Feature Development

```bash

## Create and switch to feature branch

Git checkout -b feature/new-enhancement

## Make changes and commit

Git add .
Git commit -m "feat: add new enhancement functionality"

## Push to remote

Git push origin feature/new-enhancement

## Create Pull Request

## After review and approval, merge to main

```

### Hotfix Process

```bash

## Create hotfix branch from main

Git checkout main
Git checkout -b hotfix/critical-issue

## Fix the issue and commit

Git add .
Git commit -m "fix: resolve critical production issue"

## Push and create emergency PR

Git push origin hotfix/critical-issue

```

### Release Process

```bash

## Create release branch

Git checkout -b release/v1.2.0

## Update version numbers and changelog

## Commit version updates

Git commit -m "chore: bump version to 1.2.0"

## Merge to main and tag

Git checkout main
Git merge release/v1.2.0
Git tag -a v1.2.0 -m "Release version 1.2.0"
Git push origin main --tags

```

## Git Configuration

### Repository Setup

```bash

## Set commit message template

Git config commit.template .gitmessage

## Configure user information

Git config user.name "Your Name"
Git config user.email "your.email@company.com"

## Set default branch

Git config init.defaultBranch main

## Configure pull strategy

Git config pull.rebase false

## Set up GPG signing (recommended)

Git config commit.gpgsign true
Git config user.signingkey YOUR_GPG_KEY_ID

```

### Recommended Aliases

```bash

## Useful Git aliases

Git config alias.co checkout
Git config alias.br branch
Git config alias.ci commit
Git config alias.st status
Git config alias.unstage 'reset HEAD --'
Git config alias.last 'log -1 HEAD'
Git config alias.visual '!gitk'
Git config alias.lg \
        "log --color --graph --pretty=format:'%Cred%h%Creset -%C(yellow)%d%Creset %s \
        %Cgreen(%cr) %C(bold blue)<%an>%Creset' \

    --abbrev-commit"

```

## Pull Request Guidelines

### PR Template Requirements

- Clear title following conventional commit format
- Detailed description of changes
- Link to related issues
- Screenshots for UI changes
- Test coverage information
- Breaking changes documentation

### Review Checklist

- [ ] Code follows project style guidelines
- [ ] Tests pass and new tests added where appropriate
- [ ] Documentation updated
- [ ] No breaking changes (or properly documented)
- [ ] Performance impact considered
- [ ] Security implications reviewed

## Release Management

### Tagging Strategy

- Use annotated tags for releases: `Git tag -a v1.0.0 -m "Release v1.0.0"`
- Include release notes in tag messages
- Tag format: `v{MAJOR}.{MINOR}.{PATCH}`

### Release Notes

Each release should include:

- Summary of changes
- New features
- Bug fixes
- Breaking changes
- Migration instructions (if needed)
- Contributors acknowledgment

## Git Hooks (Recommended)

### Pre-commit Hook

```bash

## !/bin/sh

## Run linting and tests before commit

npm run lint
npm run test

```

### Commit Message Hook

```bash

## !/bin/sh 2

## Validate commit message format

commit_regex='^(feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert)(\(.+\))?: .{1,50}'
if ! grep -qE "$commit_regex" "$1"; then

    echo "Invalid commit message format!" >&2
    exit 1
fi

```

## Security Considerations

- Never commit secrets or sensitive data
- Use `.gitignore` to exclude environment files
- Sign commits with GPG keys (recommended)
- Regularly audit commit history for sensitive data
- Use GitHub security features (Dependabot, CodeQL)

## Collaboration Guidelines

### For Contributors

1. Fork the repository
2. Create feature branch from main
3. Make changes following coding standards
4. Write tests for new functionality
5. Update documentation
6. Submit pull request with clear description

### For Maintainers

1. Review code for quality and security
2. Ensure CI/CD pipelines pass
3. Verify documentation updates
4. Test functionality thoroughly
5. Merge using appropriate strategy (squash for features, merge for releases)

---

_This document should be reviewed and updated regularly to reflect evolving best
practices and project needs._
