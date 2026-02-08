# Pull Request Guidelines

Guidelines for creating and reviewing pull requests in the Nirvana project.

## Before Creating a PR

### 1. Ensure Your Branch is Up to Date
```bash
git checkout main
git pull origin main
git checkout your-feature-branch
git rebase main
```

### 2. Run Tests Locally
```bash
# Backend tests
docker-compose exec backend pytest

# Frontend tests  
cd frontend && npm test

# Linting
cd frontend && npm run lint
```

### 3. Update Documentation
- Update relevant files in `docs/` if needed
- Add/update inline code comments
- Update `docs/project/changelog.md` with your changes

## Creating a Pull Request

### PR Title Format
Use conventional commit format:
```
type(scope): brief description

Examples:
feat(auth): add session-based authentication
fix(api): handle missing stock symbol gracefully  
docs(readme): update installation instructions
refactor(db): optimize watchlist queries
```

### PR Description Template
```markdown
## Description
Brief summary of changes and motivation.

## Type of Change
- [ ] Bug fix (non-breaking change that fixes an issue)
- [ ] New feature (non-breaking change that adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update
- [ ] Refactoring (no functional changes)

## Changes Made
- Specific change 1
- Specific change 2
- Specific change 3

## Testing
- [ ] Tests pass locally
- [ ] New tests added for new functionality
- [ ] Manual testing completed

## Screenshots (if applicable)
Include screenshots for UI changes.

## Checklist
- [ ] Code follows project style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] Tests added/updated
- [ ] No console errors or warnings
```

### Branch Naming
```bash
# Feature branches
feature/user-authentication
feature/stock-price-alerts
feature/portfolio-analytics

# Bug fixes
fix/login-redirect-loop
fix/price-update-delay
fix/memory-leak-charts

# Documentation
docs/api-documentation
docs/deployment-guide

# Refactoring
refactor/auth-middleware
refactor/database-queries
```

## Code Review Process

### For Authors

#### Before Requesting Review
1. **Self-review your code**
   - Read through every line of your changes
   - Check for console.log statements or debug code
   - Ensure consistent formatting and style

2. **Test thoroughly**
   - Test happy path scenarios
   - Test error conditions and edge cases
   - Test on different screen sizes (for UI changes)

3. **Write clear commit messages**
   ```bash
   # Good commit messages
   feat(watchlist): add drag-and-drop reordering
   fix(auth): prevent session timeout during active use
   
   # Poor commit messages  
   fix stuff
   update code
   wip
   ```

#### Responding to Feedback
- Address all reviewer comments
- Ask questions if feedback is unclear
- Push additional commits (don't force push during review)
- Mark conversations as resolved when addressed

### For Reviewers

#### What to Look For

**Code Quality**
- [ ] Code is readable and well-structured
- [ ] Functions are focused and not too long
- [ ] Variable and function names are descriptive
- [ ] No duplicate code or logic

**Functionality**
- [ ] Code does what the PR description says
- [ ] Edge cases are handled appropriately
- [ ] Error handling is comprehensive
- [ ] Performance implications considered

**Testing**
- [ ] Adequate test coverage for new code
- [ ] Tests are meaningful and test behavior
- [ ] Tests pass and are not flaky
- [ ] Manual testing scenarios covered

**Documentation**
- [ ] Code is self-documenting or has appropriate comments
- [ ] Public APIs have docstrings/JSDoc
- [ ] README or docs updated if needed
- [ ] Breaking changes documented

**Security**
- [ ] No sensitive data exposed
- [ ] Input validation where appropriate
- [ ] Authentication/authorization handled correctly
- [ ] SQL injection and XSS prevention

#### Review Guidelines

**Be Constructive**
```markdown
# Good feedback
Consider extracting this logic into a separate function for better testability.

The error handling here could be more specific. What happens if the API returns a 500 error?

# Less helpful feedback
This is wrong.
Bad code.
```

**Be Specific**
```markdown
# Good
Line 45: This function is doing too many things. Consider splitting the validation logic into a separate function.

# Less helpful  
This function is too complex.
```

**Suggest Solutions**
```markdown
# Good
Consider using a Map instead of an array for O(1) lookups:
```javascript
const userMap = new Map(users.map(u => [u.id, u]))
```

# Less helpful
This is inefficient.
```

## Merging Guidelines

### Requirements for Merge
- [ ] All CI checks pass
- [ ] At least one approval from code owner
- [ ] All conversations resolved
- [ ] Branch is up to date with main
- [ ] No merge conflicts

### Merge Strategy
- **Squash and merge** for feature branches
- **Merge commit** for release branches
- **Rebase and merge** for small, clean commits

### After Merge
1. Delete the feature branch
2. Update local main branch
3. Update project status if applicable
4. Deploy to staging/production if ready

## Common Issues and Solutions

### Large PRs
**Problem:** PR has too many changes, hard to review

**Solutions:**
- Break into smaller, focused PRs
- Use draft PRs for work-in-progress
- Create separate PRs for refactoring vs new features

### Merge Conflicts
**Problem:** Branch conflicts with main

**Solutions:**
```bash
# Rebase approach (preferred)
git checkout your-branch
git rebase main
# Resolve conflicts
git add .
git rebase --continue

# Merge approach
git checkout your-branch  
git merge main
# Resolve conflicts
git add .
git commit
```

### Failed CI Checks
**Problem:** Tests or linting fail in CI

**Solutions:**
- Run tests locally first
- Check CI logs for specific errors
- Ensure all dependencies are properly installed
- Verify environment variables are set correctly

### Stale Reviews
**Problem:** PR sits without review for too long

**Solutions:**
- Tag specific reviewers
- Mention in team chat/standup
- Break into smaller PRs
- Provide more context in description

## PR Templates

### Feature PR Template
```markdown
## Feature: [Feature Name]

### Description
What does this feature do and why is it needed?

### Implementation Details
- Key technical decisions made
- Any trade-offs or limitations
- Dependencies added/removed

### Testing Strategy
- Unit tests added
- Integration tests updated
- Manual testing scenarios

### Documentation Updates
- [ ] API documentation updated
- [ ] User guide updated  
- [ ] Code comments added
```

### Bug Fix PR Template
```markdown
## Bug Fix: [Issue Description]

### Problem
What was the bug and how did it manifest?

### Root Cause
What caused the issue?

### Solution
How does this fix address the root cause?

### Testing
- [ ] Reproducer test added
- [ ] Regression tests updated
- [ ] Manual verification completed

### Risk Assessment
- Impact: [Low/Medium/High]
- Areas affected: [List components]
- Rollback plan: [How to revert if needed]
```
