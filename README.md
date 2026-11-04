# shoalmark skills

[Deutsch](README.de.md)

Two agent skills from [shoalmark](https://github.com/shoalmark/shoalmark), packaged as one plugin for Claude Code and
Codex.

No release is tagged yet.

## The skills

- **find-drift** finds every place in a repository where an agent could drift off track: rules kept only as prose,
  sources that disagree, and obsolete text that still reads as live. It ranks what can become a check. It reads the
  repository and writes one report and its hash. Use it before a release or before pruning prose.
- **prune-drift** prunes recorded history from comments and unread docstrings in tracked code, using find-drift's
  report and a proof that the code stays the same. It records missing reasons first, lists rules that could become
  checks, and fixes obsolete or conflicting prose only where a superseding source settles it. It works on a new
  branch. Use it after find-drift.

## Two groups

- **Works-anywhere skills** live in `plugins/shoalmark/`. They work in any git repository, read `shoalmark.toml` when
  the repository has one, and never run shoalmark. Both skills here are in this group.
- **Needs-shoalmark skills** go into a second plugin, made with its first such skill. Each starts by finding the
  repository's pinned copy of shoalmark and running its `--version` and `--check`. There is no such skill yet.

## Install and pin

No release is tagged yet, so `<tag>` below stands for a release tag to come.

The manifests carry no version string, so an install pinned to a tag stays on that tag's commit
([Release a new version](https://code.claude.com/docs/en/plugins/host-marketplace#release-a-new-version)).

**Claude Code:**

```text
/plugin marketplace add shoalmark/skills@<tag>
/plugin install shoalmark@shoalmark
```

**Codex:**

```text
codex plugin marketplace add shoalmark/skills@<tag>
```

Then restart the ChatGPT desktop app, open the Plugins Directory, choose the shoalmark marketplace and install
shoalmark from it
([Build your own curated plugin list](https://developers.openai.com/plugins/build/plugins#build-your-own-curated-plugin-list)).

## Use

- **Claude Code:** `/shoalmark:find-drift` and `/shoalmark:prune-drift`.
- **Codex:** type `$` to mention a skill: `$find-drift` and `$prune-drift`
  ([How ChatGPT and Codex use skills](https://developers.openai.com/codex/skills#how-codex-uses-skills)).

The report and the conversation follow your language: that of shoalmark's Board, `lang` in the repository's
`<tracker folder>/brand/labels.yaml`, where that file sets a valid one; else the language you write in. The report's
section keys and its ids stay English. The skills read only that file, so where the Board takes `lang` from the
`brand/labels.yaml` beside the vendored `shoalmark.py` or from `~/.config/shoalmark/labels.yaml`, the report's
language can differ from the Board's.

## Copy the skills without the plugin

Copy both folders, `plugins/shoalmark/skills/find-drift/` and `plugins/shoalmark/skills/prune-drift/`, side by side
into one skills folder: prune-drift links to find-drift by a relative path and runs its own `prose_only.py`.

- **Codex:** `.agents/skills/` in the repository, or `$HOME/.agents/skills` in your home folder
  ([Where Codex loads local skills](https://developers.openai.com/codex/skills#where-to-save-skills)).
- **Claude Code:** `.claude/skills/` for one project, or `~/.claude/skills/` for your personal skills
  ([Choose where skills load](https://code.claude.com/docs/en/skills#choose-where-skills-load)).

Copied skills carry no plugin prefix, so Claude Code runs them as `/find-drift` and `/prune-drift`.

## More

- [SECURITY.md](SECURITY.md) to report a vulnerability, and [CHANGELOG.md](CHANGELOG.md) for changes.
- Licensed under Apache-2.0 or MIT, at your option: [LICENSE-APACHE](LICENSE-APACHE), [LICENSE-MIT](LICENSE-MIT) and
  [NOTICE](NOTICE).

## Where these skills come from

These skills come from shoalmark. *A workbench for your agents. Your decisions on record.* For one person in charge
and their agent fleet. See where the work stands, what waits for your word, and what the next session picks up. Your
agents keep that record in your repository; your decisions go into it as your own commits, beside the evidence behind
the work.

- [Why shoalmark?](https://shoalmark.tools/why-shoalmark.html)
- [Set up in ten minutes](https://shoalmark.tools/setup.html)
- [shoalmark's repository](https://github.com/shoalmark/shoalmark)
- [Send feedback](https://shoalmark.tools/feedback)
