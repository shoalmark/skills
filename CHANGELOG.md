# Changelog

## Unreleased

- find-drift and prune-drift, moved from [shoalmark at c02ca26](https://github.com/shoalmark/shoalmark/commit/c02ca26ffdf8fa24781a4943148725880552703f)
  into `plugins/shoalmark/skills/`, each marked as a works-anywhere skill.
- Manifests for both harnesses: Claude Code's marketplace and plugin manifests, and Codex's marketplace and portable
  Agent Plugins manifest.
- The tests: `test_prune_drift.py`, moved, and `test_plugin.py`, moved and extended to check the manifests and their
  agreement, the skills' front matter, the two groups, the public-text scans and CI's own rules.
- CI: both tests on ubuntu with Python 3.9 and 3.12, macOS with 3.12, and Windows with 3.9 and 3.12.
- Dependabot: weekly updates for the pinned GitHub Actions.
- The report's language: both skills write the report's prose, and talk with the person, in `lang` from the
  repository's `<tracker folder>/brand/labels.yaml` where that file sets a valid one, else in the language the person
  writes in.
- Fixed section keys: find-drift's report begins each part with `## snapshot`, `## rules`, `## breaks`, `## ranking`,
  `## disagreements`, `## obsolete` or `## limits`, prune-drift reads the parts by those keys, and `test_plugin.py`
  pins both, with the language rule and each skill's description and compatibility.
- README.de.md, the German README, and the way to shoalmark at the end of both READMEs and nowhere under `plugins/`;
  `test_plugin.py` checks that the two READMEs agree in headings, code blocks, install commands and closing links.
