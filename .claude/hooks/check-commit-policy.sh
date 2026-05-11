#!/bin/bash
# Block git commits whose message contains a Claude session URL.
# Hook input: JSON on stdin with .tool_input.command for Bash tool calls.
# Exit 2 = block; exit 0 = allow.

input=$(cat)
cmd=$(printf '%s' "$input" | jq -r '.tool_input.command // empty')

if printf '%s' "$cmd" | grep -qE 'git[[:space:]]+commit' \
   && printf '%s' "$cmd" | grep -qE 'https?://claude\.ai/code/session_'; then
  cat >&2 <<'MSG'
POLICY VIOLATION: commit messages in this repo must not include
claude.ai/code/session URLs. Use:
  git commit --author="jeremylaratro <jlaratro24@gmail.com>" -m "<message>"
and omit any Claude session trailer. See CLAUDE.md for details.
MSG
  exit 2
fi
exit 0
