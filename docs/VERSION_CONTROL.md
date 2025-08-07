# Development Workflow and Version Control Guidelines

## Branching Strategy

We follow a **Git Flow** branching model for organized development:

### Branch Types

- **`master`** - Production-ready code, stable releases
- **`develop`** - Integration branch for features
- **`feature/*`** - New features (e.g., `feature/dashboard-improvements`)
- **`hotfix/*`** - Critical bug fixes (e.g., `hotfix/scan-crash-fix`)
- **`release/*`** - Release preparation (e.g., `release/2.1.0`)

### Workflow Steps

1. **Feature Development**

   ```bash
   git checkout develop
   git pull origin develop
   git checkout -b feature/your-feature-name
   # Make changes
   git add .
   git commit -m "feat: add feature description"
   git push origin feature/your-feature-name
   # Create pull request to develop
   ```

2. **Bug Fixes**

   ```bash
   git checkout develop
   git checkout -b bugfix/issue-description
   # Fix the bug
   git commit -m "fix: resolve issue description"
   ```

3. **Hotfixes** (Critical production issues)
   ```bash
   git checkout master
   git checkout -b hotfix/critical-issue
   # Fix the issue
   git commit -m "hotfix: resolve critical issue"
   # Merge to both master and develop
   ```

## Commit Message Convention

We use **Conventional Commits** for clear, semantic commit messages:

### Format

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

### Types

- **feat**: New feature
- **fix**: Bug fix
- **docs**: Documentation changes
- **style**: Code formatting (no logic changes)
- **refactor**: Code refactoring (no new features or bug fixes)
- **test**: Adding or updating tests
- **chore**: Maintenance tasks (dependencies, build tools)
- **perf**: Performance improvements
- **ci**: CI/CD pipeline changes

### Examples

```bash
feat(dashboard): add clickable Last Scan card functionality
fix(reports): resolve duplicate scan reports issue
docs(readme): update installation instructions
refactor(scanner): optimize file scanning performance
test(gui): add unit tests for dashboard components
```

## Version Control Commands

### Daily Development

```bash
# Check status
git status

# View changes
git diff

# Stage changes
git add .
# or stage specific files
git add path/to/file.py

# Commit with conventional message
git commit -m "feat(component): description of changes"

# Push to remote
git push origin branch-name

# Pull latest changes
git pull origin branch-name
```

### Release Process

1. **Create Release Branch**

   ```bash
   git checkout develop
   git checkout -b release/2.1.0
   ```

2. **Update Version Files**

   ```bash
   echo "2.1.0" > VERSION
   # Update CHANGELOG.md with release notes
   git add VERSION CHANGELOG.md
   git commit -m "chore(release): bump version to 2.1.0"
   ```

3. **Merge to Master and Tag**

   ```bash
   git checkout master
   git merge release/2.1.0
   git tag -a v2.1.0 -m "Release version 2.1.0"
   git push origin master --tags
   ```

4. **Merge Back to Develop**
   ```bash
   git checkout develop
   git merge release/2.1.0
   git push origin develop
   ```

## Code Review Process

1. **Create Pull Request**
   - Target the appropriate base branch (`develop` for features)
   - Include descriptive title and detailed description
   - Reference any related issues

2. **Review Checklist**
   - [ ] Code follows project conventions
   - [ ] Tests pass (if applicable)
   - [ ] Documentation updated
   - [ ] No security vulnerabilities
   - [ ] Performance considerations addressed

3. **Approval and Merge**
   - Require at least one reviewer approval
   - Use "Squash and merge" for clean history
   - Delete feature branch after merge

## Tag Strategy

### Version Tags

- Use semantic versioning: `v2.1.0`
- Tag stable releases on master branch
- Include release notes in tag description

### Pre-release Tags

- Alpha: `v2.1.0-alpha.1`
- Beta: `v2.1.0-beta.1`
- Release Candidate: `v2.1.0-rc.1`

## Git Configuration

### Set up user info

```bash
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

### Useful aliases

```bash
git config --global alias.co checkout
git config --global alias.br branch
git config --global alias.ci commit
git config --global alias.st status
git config --global alias.lg "log --oneline --graph --decorate"
```

## Best Practices

1. **Commit Often**: Make small, focused commits
2. **Write Clear Messages**: Use conventional commit format
3. **Test Before Commit**: Ensure code works before committing
4. **Keep Branches Updated**: Regularly merge/rebase from develop
5. **Review Your Changes**: Use `git diff` before committing
6. **Use .gitignore**: Keep repository clean of build artifacts
7. **Backup Work**: Push branches regularly to remote

## Repository Maintenance

### Cleanup Commands

```bash
# Remove merged branches
git branch --merged | grep -v master | xargs git branch -d

# Clean up remote tracking branches
git remote prune origin

# Remove untracked files (be careful!)
git clean -fd
```

### Repository Statistics

```bash
# View commit history
git log --oneline --graph --decorate --all

# See who contributed what
git shortlog -sn

# View file changes over time
git log --stat --oneline
```
