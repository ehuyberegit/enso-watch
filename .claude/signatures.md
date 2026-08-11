# Signature registry: enso-watch

> The living registry of THIS project's frictions. A signature = a terminal
> cause + a faulty behavior + a mechanism + an occurrence counter.
> We only HARDEN the harness on a mechanism that RECURS (counter >= 2).
> The SYSTEM (format, the mine/propose/validate/prune loop) lives in the
> `engine` crew plugin (skill `the-loop`); only this project's concrete signatures
> live here. Empty at start: it fills up run after run.

<!-- entry format:
## S1: [short title]
- Cause      : [the terminal cause exposed by the reviewer / the machine gate]
- Behavior   : [what went wrong, observable]
- Mechanism  : [the reusable abstract mechanism, not the one-off incident]
- Occurrences: 1 · Status: open · Witness: [held-in / held-out]
-->

## S1: background isolation guard deadlocks a new nested ignored repo
- Cause      : in a background session, the write isolation guard blocks the shared checkout and offers only EnterWorktree, but a worktree of the SESSION repo (Atlas) does not contain a new project folder that Atlas ignores, and the off switch (worktree.bgIsolation none) is itself a guarded write.
- Behavior   : every write of the project's first files (roadmap, chef) was rejected; git init, a project local settings flag, and EnterWorktree all failed to unblock; only setting worktree.bgIsolation none in the SESSION repo's gitignored .claude/settings.local.json cleared it (re read at runtime, no restart).
- Mechanism  : background session plus a brand new project nested in a path the session repo ignores, so the isolation guard has no valid worktree to offer, a deadlock.
- Occurrences: 1 · Status: open · Witness: held-in
