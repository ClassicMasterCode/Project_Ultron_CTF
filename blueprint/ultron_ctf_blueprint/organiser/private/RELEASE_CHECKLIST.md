# Organiser-only release checklist

## Scope and safety
- [ ] Written rules list the exact challenge hosts, ports and allowed protocols.
- [ ] Every test is confined to the disposable challenge environment.
- [ ] No real accounts, real passwords, personal MFA devices or third-party systems are involved.
- [ ] No host escape or organiser infrastructure compromise is needed or rewarded.

## Challenge correctness
- [ ] Username is discoverable from at least two consistent artefacts.
- [ ] Password recovery has a reproducible intended path.
- [ ] Correct TOTP backup is distinguishable from decoys.
- [ ] Operator login succeeds with the recovered three factors.
- [ ] Operator is not administrator by default.
- [ ] The intended maintenance flaw grants only sandbox administrator rights.
- [ ] Protected artifact is not accessible before the admin milestone.
- [ ] Exact flag matches byte-for-byte.

## Isolation
- [ ] Per-team workspaces are separated.
- [ ] No host directory or Docker socket is mounted.
- [ ] Challenge network cannot reach CTFd database/admin interfaces or cloud metadata.
- [ ] CPU, memory, PID, disk and runtime limits are configured.
- [ ] Instance teardown removes ephemeral secrets and data.

## Abuse resistance
- [ ] Authentication has rate limits and cooldowns.
- [ ] Failure messages do not disclose whether an account exists.
- [ ] TOTP replay is rejected.
- [ ] Team-specific credentials and flags are enforced.
- [ ] Paid hint behaviour is tested with teams and alternate accounts.
- [ ] Feedback files trigger only on server-verified milestones.

## Playtesting
- [ ] Author solve completed from a fresh instance.
- [ ] At least two blind human playtests completed.
- [ ] Tool-enabled AI benchmark performed and recorded.
- [ ] Intended solution is the shortest fair path; no unintended shortcuts remain.
- [ ] Difficulty and point value reviewed after playtesting.
