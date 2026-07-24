# Git Rules

## Commit Style

```text
<type>(<scope>): <short imperative summary>
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`.

## Do

- Check `git status --short` before editing and before final response.
- Keep commits focused and reviewable.
- Mention verification in commit bodies for non-trivial changes.
- Preserve user changes in a dirty worktree.

## Do Not

- Commit `.env`, cache, build, or generated artifact files.
- Revert unrelated changes.
- Force-push protected branches.
- Mix docs/tooling imports with runtime product changes unless requested.
