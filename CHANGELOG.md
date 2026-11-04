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
