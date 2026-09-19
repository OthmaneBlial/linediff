# Five-user feedback trial after distribution

This is a **protocol**, not evidence that anyone has tried a published Linediff version. Start only after a tagged artifact has been published, downloaded and smoke-tested as required by the [release gate](RELEASING.md). Invite participants with a clear explanation of what will be observed. Do not request private source files, credentials, repository URLs, or screen recordings of confidential work.

## One session (about 15 minutes)

1. Record the distributed version, artifact name and SHA-256, OS, Python version if relevant, and whether the participant has used a terminal diff tool before.
2. Ask the participant to install or start **the downloaded artifact**, then run `linediff --help`. Observe where instructions are unclear; do not coach unless they are blocked.
3. Give them the two public `moved_function` fixture files from the matching repository tag as a small trial kit; the installed wheel and standalone executable do not bundle the test corpus. Ask them to compare the files, explain what changed in their own words, then check the underlying patch. Record whether they distinguish the heuristic move label from exact file changes.
4. Ask them to run the one-shot Git example in a disposable public test repository. Observe whether they understand how to return to native `git diff --no-ext-diff`.
5. Use the public `.txt` and final-newline fixture pairs from the same trial kit to show fallback and exact newline handling. Ask what output they expected and what they would do next.
6. Ask one open question: “What would make you use this again during a real review?” Then ask for the most confusing point and one missing capability. Avoid suggesting answers.

Participation is voluntary. Ask consent before taking notes; ask separately before quoting a comment publicly. Record an anonymous session code and only the minimal technical details above. A participant can stop at any time and ask for their notes to be discarded. Do not transmit notes or contact participants automatically from this repository.

## Evidence and triage

For each of at least five real sessions, record: anonymous code, date, artifact/hash, task completed or blocked, exact reproducible failure or confusion, and whether a proposed issue has the participant's permission to quote them. Separate observed behavior from the maintainer's interpretation. Aggregate only counts that can be traced back to these session records. If a problem is reproducible, add a small public fixture and a test without private data. Classify each finding as `fix before release`, `document`, `future scope`, or `no action`, with a reason. Re-run the task on the corrected distribution before closing a finding.

The protocol does not claim adoption, satisfaction, star growth, or usability validation. Those require the actual sessions and their recorded outcomes.
