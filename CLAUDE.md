# PhotoSec — repository policy

## Commit authorship

Commits in this repository MUST be authored by `jeremylaratro <jlaratro24@gmail.com>`.

Always pass the author explicitly to every `git commit` command:

```bash
git commit --author="jeremylaratro <jlaratro24@gmail.com>" -m "<message>"
```

Do not run `git config user.name` or `git config user.email` — author identity is set per-commit via `--author`, never via the git config.

## Commit message policy

- Do NOT append `https://claude.ai/code/session_*` URLs to commit messages.
- Do NOT add `Co-Authored-By: Claude` trailers.
- Commit messages should describe the change only — no provenance trailers about which assistant produced them.

The `attribution.commit` and `attribution.pr` fields are set to `""` in `.claude/settings.json` so the Claude Code harness will not auto-append these trailers.

A `PreToolUse` hook in `.claude/settings.json` (script: `.claude/hooks/check-commit-policy.sh`) enforces the message policy as a backstop — any `git commit` command whose body contains `claude.ai/code/session` is blocked with exit code 2.

## Pull requests

Do not open pull requests unless the user explicitly requests one.
