---
name: prune-drift
description: "Prune recorded history from comments and unread docstrings in tracked code, using find-drift's report and a proof that code stays the same. Record missing reasons first, list rules that could become checks, and fix obsolete or conflicting prose only where a superseding source settles it. Work on a new branch; write the actions, proof and limits to the tracker folder's evidence/drift/. Use after find-drift or when asked to prune prose."
compatibility: "Any git repository. Uses shoalmark.toml when present; never runs shoalmark."
---

# Prune drift

Write the report's prose, and talk with the person, in their language: `lang` in this repository's
`<tracker folder>/brand/labels.yaml`, read from no other place, where its value fully matches
`[A-Za-z]{2,3}(-[A-Za-z0-9]{1,8})*`; where there is no such file, line or value, the language the person writes in;
section keys, ids, file names, front-matter keys, `find-drift` and `prune-drift` stay as written.

1. Snapshot: take [find-drift](../find-drift/SKILL.md)'s step 1 in full, including its clean-tree check, tracker
   folder and destination rules, and limits for parts not checked out. Create a new branch from HEAD; never work
   on the default branch. Apply owner-only path restrictions to every step: write out their fixes for the owner.
2. Report: read the newest find-drift report under `<tracker folder>/evidence/drift/` whose `<file>.sha256` matches
   its bytes. Check freshness with `git diff --quiet <snapshot> HEAD -- <its sources>`, both from its
   `## snapshot`: no listed source may have changed. Try reports newest first; if none is fresh, run find-drift in
   full first. Keep its snapshot and source hashes from `## snapshot` and its limits from `## limits`; a scoped
   report cannot replace a full report.
3. Sort every comment and docstring in tracked code that can be parsed, one row per part, with its `file:line`
   and the sha256 of its exact text. Name unparseable code as a limit. Use four classes: **history** (who decided,
   which review, when; cite the git, tracker or commit reference already holding it); **history not yet in the
   record** (a reason only this prose holds); **a rule** (something the code must keep); **keep** (an external
   quirk the code works around, or the reason a security refusal exists). Text that only states what code does
   is a rule where code must keep it, else keep; there is no fifth class.
4. Where two seats are available, each sorts separately with these same instructions, then checks the other's
   rows. Consolidate only history both agree on. A conflict keeps the text: history against a rule or keep stays;
   keep against a rule stays as prose. One seat alone deletes only history with a cited, checked reference:
   the commit is an ancestor of HEAD, or the tracker or review exists. Record the check on the row.
5. Record first: put each agreed reason not yet in the record in the tracker it concerns, or in a commit message,
   with its `file:line`. Commit that record on its own before deleting anything; cite the commit on its row.
6. Deletion: stage only the agreed history and the parts recorded in step 5, by file name. Use `git write-tree`
   and `git commit-tree <tree> -p HEAD` to make a temporary commit object of that tree. Run
   `python3 -I <this skill folder>/prose_only.py HEAD <temporary-commit>`; put its full output in the body of
   one deletion commit with that same tree, removing nothing else. The proof covers
   ordinary comments always, and docstrings only where nothing reads them. Directive comments are not prose;
   a module's bare `__doc__` blocks its module docstring, and `.__doc__`, `getdoc`, `doctest` or `docopt` readers
   block all docstrings. The proof scans tracked Python files at both revisions, even with explicit file paths.
   Every changed file must be covered and every result must be `prose-only`. Leave any file the proof
   cannot cover unchanged, and name it and why. It proves Python only; do not treat other code as covered.
7. Rules: never delete them. List each `file:line` as a candidate conversion, ranked by the report's layers:
   1 impossible to break; 2 the build fails; 3 a rule or a review; 4 a skill; 5 a style guide. A promotion is to a
   lower number; keep judgement rules apart, unranked. Build no check.
8. Obsolete text and disagreements, from the report's `## obsolete` and `## disagreements`: in separate commits,
   fix obsolete text only with its superseding source cited: rewrite to that source's rule, or delete an obsolete
   copy where that source already holds it. Edit directly only in documentation files and in Python files the
   step 6 proof shows prose-only; in any other code or configuration file, write the exact proposed fix for the
   person instead. Fix a disagreement only where one side cites a later ruling. Name every other disagreement for
   the person. Never remove a live rule or keep part. Never edit an owner-only path; write its exact proposed fix
   for the owner.
9. Report: write `<tracker folder>/evidence/drift/<date>-<short sha>-prune.md`, with date as `YYYY-MM-DD` and sha
   from the starting snapshot, or the agreed destination without a tracker folder. Include the sort (one row per
   part), each action and its commit, the proof's output, candidate conversions, what needs a look and why, and
   limits. Write its sha256 to `<file>.sha256` beside it, never inside it.
10. Never delete a rule, a keep part or history on one seat's unsupported word; push, merge or rewrite history;
    run a test suite, a browser or the repository's own gates; use the network; print a secret; or open a record
    on a security subject. The proof replaces a run; CI runs the suites. Stop when you meet a secret (a credential,
    key or token) or find a security weakness no record already names: write nothing about it, name only the
    class left out as a limit, and tell the person. A gap the repository already documents between a rule and
    its enforcement is not a stop.
11. Close: in your last message, not only in the report, list for the person each disagreement and each proposed
    fix that needs their decision, by id with one line, and ask whether to file them as asks. Name the repository's
    own verification, its test suites and CI, and ask whether to run them before anything merges. This skill runs
    none of them; the person's yes starts that run as a separate task.
