---
name: find-drift
description: "Find every place in this repository where an agent could drift off track — rules kept only as prose, sources that disagree, and obsolete text that still reads as live — and rank what can become a check. Reads the repository; writes one report and its hash in the tracker folder's evidence/drift/, or where it is told when there is no tracker folder. Use before a release or before pruning prose; after a single rule or ruling changes, run steps 3 to 7 on the sources it touches."
---

# Find drift

Read the repository; write only the report and its hash, or the private supplement below. Commit nothing.

1. Snapshot: print `git rev-parse HEAD`, `date`, `git status --porcelain --untracked-files=all` and `git submodule
   status`. Stop if the tree is not clean, except for untracked reports and their hash files in `<tracker
   folder>/evidence/drift/`; ignore nothing else. The tracker folder is `tracker_dir` in `shoalmark.toml`, or
   `docs/work-tracker` where the file sets none. Without `shoalmark.toml`, ask where to write; never write into the
   repository unasked. Name every part not checked out: it bounds steps 2 to 8.
2. Sources: list the files whose text binds an agent — the agents' document and every file it names as binding,
   contributing and security guides, triage rules, seat definitions, skills, CI workflows, hooks with the scripts
   and configuration they run. Leave lookup-only files out; name them and why. Read `drift_sources` where set in
   `shoalmark.toml`: repository-relative paths or globs that add to these defaults, never remove them. Name missing
   sources, including unmatched globs; list every source read with its sha256 and origin (defaults or the key).
   Without `shoalmark.toml`, use the defaults and say so. A rule cited to a place outside the repository is listed
   with that place, marked unreadable, and not hashed.
3. Rules: one row per obligation — one actor, one act, one condition — that a reviewer can grade alone. Combine
   repeats across files, with every source's file:line. Group by subject; give each row an id for references.
4. Enforcement: each gate, hook, test or CI step's file:line; where it runs (local hook, command run by hand,
   pull-request workflow, forge); whole or partial coverage. Write "none" where nothing refuses a break and
   "not readable" where it would live in a part you cannot read. Compare a source's enforcement claim with the code.
5. Grade on five layers, strongest first: 1 impossible to break (the forge, operating system, schema or generator
   refuses or writes it); 2 the build fails (local hook, command run by hand, or pull-request check; say whether
   required, or unknown where settings are unreadable); 3 a rule or a review; 4 a skill; 5 a style guide. Give the
   layer now and strongest reachable, how, and size (S/M/L). A promotion is to a lower number. Mark "judgement"
   where only a reviewer can decide; a judgement rule is never ranked.
6. Disagreements: the same subject stated differently between sources, or a source and its enforcing code; cite
   both by file:line. Change neither. A stale number is obsolete text, not a disagreement, unless two sources give
   different numbers; then cross-reference both lists and the affected rows.
7. Obsolete text: revoked or superseded, still written as live — cite it and what superseded it by file:line, with
   the affected rows. Dated history is not obsolete. Name it; delete nothing.
8. Breaks: from the commit log, trackers and review findings only, each with a reference. A break is an act after
   the rule came into force: date the rule by the commit that wrote it, a gate by its merge onto the default branch.
   Count only what every source agrees is a break; explain exclusions. Counts are lower bounds, with their
   definition and the query or record that gives them. Search hits find candidates, not counts.
9. Rank what can be promoted — a stronger reachable layer, not judgement — by breaks, then whether a break reached
   the default branch or a release, then size. Flag rules whose breaks are their practice or that a disagreement
   touches: settle their text before their check. Top 10; the rest, including zero-break rules, in one line;
   judgement rules apart.
10. Report: write `<tracker folder>/evidence/drift/<date>-<short snapshot sha>.md` (date as `YYYY-MM-DD`, sha from
    `git rev-parse --short HEAD`), or the agreed destination without a tracker folder. In order: snapshot sha and
    sources' hashes; table with a legend; breaks and references; top 10, rest and judgement rules; disagreements;
    obsolete text; definitions and limits. A scoped run takes step 1 in full, lists and hashes only the sources it
    reads, and marks steps 8 and 9 not run. Write its sha256 to `<file>.sha256` beside it, never inside it. Never
    read private notes unless the person names their folder for this run; then write only a supplement there, in
    their private records under version control. Use the existing public report's snapshot sha and hash as its key:
    counts only for its existing rule ids, with private references; it may rank again privately. Add no rule or
    sentence to the public report, and never quote the supplement in it.
11. Close: in your last message, not only in the report, tell the person each disagreement and each obsolete text by
    id with one line, and ask whether to file them as asks. Then name the next step:
    [prune-drift](../prune-drift/SKILL.md) records and removes history and fixes obsolete text from this report. It
    needs a report whose sources have not changed since its snapshot, so run this skill again first if they have.

Never run a test suite, a browser or the repository's own gates, use the network, print a secret, or rule on what you
find. Open no record on a security subject and name the class left out as a limit. Stop when you meet a secret
(a credential, key or token) or find a security weakness no record already names: write nothing about it and tell
the person. A gap the repository already documents between a rule and its enforcement is drift, not a stop:
report it like any other row.
