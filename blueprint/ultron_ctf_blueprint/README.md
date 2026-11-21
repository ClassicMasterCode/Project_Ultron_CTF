# PROJECT ULTRON: Disengagement — CTF organiser blueprint

This package is a design and handover blueprint, not a running website or a finished challenge image.

## Package layout

- `participant/` — participant-facing challenge brief. Safe to publish after organiser review.
- `feedback/` — text snippets to be delivered to a team workspace when its corresponding milestone is genuinely reached.
- `organiser/` — build plan, challenge manifest and three paid hints.
- `organiser/private/` — organiser-only answer-key template, release checklist and detailed solution walkthrough. **Never publish this directory or mount it in a participant instance.**

## Recommended implementation

Use CTFd for registration, teams, challenge listing, submissions, hints and scoreboard. Run the ULTRON environment separately in a disposable, team-scoped sandbox. A small challenge controller should track milestones and publish the feedback text files into that team's workspace.

This blueprint deliberately models administrator privilege inside the challenge sandbox. It does not require host-root access, a container escape, or access to the organiser's infrastructure.

## Important setup rule

Generate a unique set of challenge credentials, TOTP secret, instance identifier and flag-delivery state for each team. Keep private values in the instance manager's secret store, not in Git, frontend assets, challenge downloads, public logs or this package's participant directory.
