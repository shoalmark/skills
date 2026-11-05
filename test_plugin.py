import datetime
import json
import os
from pathlib import Path
import posixpath
import re
import sys


HERE = Path(__file__).resolve().parent
PUBLIC_ID = re.compile(r"\b(?:FM|RV|SP|HL|FEAT|BUG)-\d+\b")
HOME_PATH = re.compile(r"(?i)(?:/(?:Users|home)/|[a-z]:[/\\]+Users[/\\]+|~[/\\]|%USERPROFILE%|\$(?:HOME\b|\{HOME\}))")
ROOT_TEXTS = ("README.md", "README.de.md", "CHANGELOG.md", "SECURITY.md")
PUBLIC_ID_SCAN = ("plugins", ".claude-plugin", ".agents", ".github") + ROOT_TEXTS
HOME_PATH_SCAN = ("plugins", ".claude-plugin", ".agents", ".github")
TWINS = ("README.md", "README.de.md")
REPOSITORY = "https://github.com/shoalmark/shoalmark"
FEEDBACK = "https://shoalmark.tools/feedback"
OWN_PAGES = {
    "README.md": ("https://shoalmark.tools/why-shoalmark.html", "https://shoalmark.tools/setup.html"),
    "README.de.md": ("https://shoalmark.tools/de/warum-shoalmark.html", "https://shoalmark.tools/de/setup.html"),
}
OWN_SITE = {"README.md": "https://shoalmark.tools/", "README.de.md": "https://shoalmark.tools/de/"}
INSTALL = re.compile(r"marketplace add|plugin install")
MARKETPLACE_ADD = "marketplace add"
PIN_SOURCE = "shoalmark/skills@v"
PLACEHOLDER = "<tag>"
REFERENCE = re.compile(r"(?i:shoalmark/skills)@([^\s`\"'\u201c\u201d\u201e\u2018\u2019\u00ab\u00bb>\[\]()]*)")

NAME = "shoalmark"
PLUGIN = "plugins/shoalmark"
SKILLS = PLUGIN + "/skills"
DESCRIPTION = "Skills that find repository rules held only as prose, conflicting sources and obsolete guidance."
LICENSE = "Apache-2.0 OR MIT"
AUTHOR = {"name": "the shoalmark authors"}
HOLDER_FILES = ("NOTICE", "LICENSE-MIT")
SCHEMA_URL = "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json"
SCHEMA_PROPERTIES = ("$schema", "name", "version", "description", "author", "homepage", "repository", "license",
                     "keywords", "extensions")
SCHEMA_NAME = re.compile(r"(?!.*(?:--|\.\.))[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?")
CODEX_INSTALLATION = ("AVAILABLE", "INSTALLED_BY_DEFAULT", "NOT_AVAILABLE")
SKILL_NAME = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
WORKS_ANYWHERE = "Any git repository. Uses shoalmark.toml when present; never runs shoalmark."
FRONT_MATTER = {
    "find-drift": (
        "Find every place in this repository where an agent could drift off track — rules kept only as prose, "
        "sources that disagree, and obsolete text that still reads as live — and rank what can become a check. "
        "Reads the repository; writes one report and its hash in the tracker folder's evidence/drift/, or where it is "
        "told when there is no tracker folder. Use before a release or before pruning prose; after a single rule or "
        "ruling changes, run steps 3 to 7 on the sources it touches.",
        WORKS_ANYWHERE),
    "prune-drift": (
        "Prune recorded history from comments and unread docstrings in tracked code, using find-drift's report and a "
        "proof that code stays the same. Record missing reasons first, list rules that could become checks, and fix "
        "obsolete or conflicting prose only where a superseding source settles it. Work on a new branch; write the "
        "actions, proof and limits to the tracker folder's evidence/drift/. Use after find-drift or when asked to "
        "prune prose.",
        WORKS_ANYWHERE),
}
REPORT_KEYS = ("snapshot", "rules", "breaks", "ranking", "disagreements", "obsolete", "limits")
REPORT_KEY = re.compile(r"`##[ ]([^`]*)`")
PRUNE_READS = {2: ("snapshot", "limits"), 8: ("disagreements", "obsolete")}
LANG_PATTERN = "[A-Za-z]{2,3}(-[A-Za-z0-9]{1,8})*"
LANGUAGE_CLAUSES = (
    "talk with the person, in their language:",
    "`lang` in this repository's `<tracker folder>/brand/labels.yaml`, read from no other place,",
    "where its value fully matches `" + LANG_PATTERN + "`;",
    "the language the person writes in;",
    "section keys, ids, file names, front-matter keys, `find-drift` and `prune-drift` stay as written.",
)
LANGUAGE_SENTENCE = {
    "find-drift": (
        "Write the prose of the report and the supplement, and talk with the person, in their language: `lang` in "
        "this repository's `<tracker folder>/brand/labels.yaml`, read from no other place, where its value fully "
        "matches `[A-Za-z]{2,3}(-[A-Za-z0-9]{1,8})*`; where there is no such file, line or value, the language the "
        "person writes in; section keys, ids, file names, front-matter keys, `find-drift` and `prune-drift` stay as "
        "written."
    ),
    "prune-drift": (
        "Write the report's prose, and talk with the person, in their language: `lang` in this repository's `<tracker "
        "folder>/brand/labels.yaml`, read from no other place, where its value fully matches "
        "`[A-Za-z]{2,3}(-[A-Za-z0-9]{1,8})*`; where there is no such file, line or value, the language the person "
        "writes in; section keys, ids, file names, front-matter keys, `find-drift` and `prune-drift` stay as written."
    ),
}
REPORT_SPANS = tuple("## " + key for key in REPORT_KEYS)
BACKTICK_SPAN = re.compile(r"`([^`]*)`")
VERSION = re.compile(r"\d+(?:\.\d+)+(?:[-+][0-9A-Za-z.-]+)?")
RELEASE = re.compile(r"\d+\.\d+\.\d+", re.ASCII)
RELEASE_HEADING = re.compile(r"## (\d+\.\d+\.\d+) \u2014 (\d{4}-\d{2}-\d{2})", re.ASCII)
ONE_HARNESS_TOOL = re.compile(
    r"\b(?:AskUserQuestion|EndConversation|TodoWrite|apply_patch|update_plan)\b"
    r"|\b(?:Bash|PowerShell|Skill|LSP)`?[ \t]+tools?\b")
PROMOTION = re.compile(r"(?i)shoalmark\.tools|github\.com/shoalmark/shoalmark")
# Stripped lines that may mention shoalmark.py in the works-anywhere plugin; any other such line fails.
ALLOWED_SHOALMARK_MENTIONS = ()
PIN = "<40 hex> # <tag>"
PINNED = re.compile(r"[0-9a-f]{40} # [0-9A-Za-z][0-9A-Za-z._-]*")
CI_YML = """name: ci

on:
  push:
    branches: [main]
  pull_request:

permissions: {contents: read}

jobs:
  tests:
    name: tests (${{ matrix.system }}, ${{ matrix.python }})
    runs-on: ${{ matrix.image }}
    timeout-minutes: 10
    strategy:
      fail-fast: false
      matrix:
        include:
          - {system: ubuntu, image: ubuntu-24.04, python: "3.9"}
          - {system: ubuntu, image: ubuntu-24.04, python: "3.12"}
          - {system: macos, image: macos-26, python: "3.12"}
          - {system: windows, image: windows-2025-vs2026, python: "3.9"}
          - {system: windows, image: windows-2025-vs2026, python: "3.12"}
    steps:
      - uses: actions/checkout@<40 hex> # <tag>
        with:
          persist-credentials: false
      - uses: actions/setup-python@<40 hex> # <tag>
        with:
          python-version: "${{ matrix.python }}"
      - name: git identity
        run: git config --global user.email ci@example.invalid && git config --global user.name ci && git config --global init.defaultBranch main
      - name: test_plugin.py
        run: python -u test_plugin.py
      - name: test_prune_drift.py
        run: python -u test_prune_drift.py
"""
DEPENDABOT_YML = """version: 2
updates:
  - package-ecosystem: github-actions
    directory: "/"
    schedule: {interval: weekly}
"""


def _front_matter(text):
    lines = text.splitlines()
    if not lines or lines[0] != "---" or "---" not in lines[1:]:
        raise ValueError("expected front matter between --- lines")
    fields = {}
    for line in lines[1:lines.index("---", 1)]:
        if not line.strip() or line.startswith("#"):
            continue
        match = re.fullmatch(r"([a-z][a-z0-9-]*):[ ]+(.+)", line)
        if not match:
            raise ValueError("front matter must use flat, single-line string fields")
        key, value = match.groups()
        if key in fields:
            raise ValueError("duplicate front-matter key: " + key)
        value = value.strip()
        if value.startswith('"'):
            value = json.loads(value)
        elif value.startswith("'"):
            if not re.fullmatch(r"'(?:[^']|'')*'", value):
                raise ValueError("invalid single-quoted string: " + key)
            value = value[1:-1].replace("''", "'")
        elif (not re.fullmatch(r"[A-Za-z][^\t\r\n]*", value)
              or re.search(r":(?:\s|$)|\s#", value)
              or value.lower() in {"true", "false", "yes", "no", "on", "off", "null"}):
            raise ValueError("use a quoted string for: " + key)
        if not isinstance(value, str):
            raise ValueError("expected a string for: " + key)
        fields[key] = value
    return fields


def _entries(marketplace):
    entries = marketplace.get("plugins")
    return entries if isinstance(entries, list) else []


def _versions(label, manifest):
    holders = [(label, manifest), (label + " metadata", manifest.get("metadata"))]
    holders += [(label + " entry " + str(index), entry) for index, entry in enumerate(_entries(manifest))]
    return [(where, holder["version"]) for where, holder in holders if isinstance(holder, dict) and "version" in holder]


def _text(path):
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, ValueError):
        return ""


def _real_date(text):
    try:
        datetime.date.fromisoformat(text)
    except ValueError:
        return False
    return True


def _local_path(source):
    if isinstance(source, dict):
        source = source.get("path")
    if not isinstance(source, str) or not source.startswith("./"):
        return None
    return posixpath.normpath(source)


def _same(values):
    return len({json.dumps(value, sort_keys=True) for value in values}) == 1


def _files(path):
    if path.is_file():
        return [path]
    return sorted(item for item in path.rglob("*") if item.is_file()) if path.is_dir() else []


def _is_link(path):
    return os.path.islink(path) or (hasattr(os.path, "isjunction") and os.path.isjunction(path))


def _walk(folder):
    files, links, stack = [], [], [folder]
    while stack:
        current = stack.pop()
        if _is_link(current):
            links.append(current)
        elif current.is_dir():
            with os.scandir(current) as entries:
                stack += [Path(entry.path) for entry in entries]
        elif current.is_file():
            files.append(current)
    return sorted(files), sorted(links)


def _mentions(folder):
    found = []
    for path in _walk(folder)[0]:
        lines = path.read_bytes().decode("utf-8", errors="replace").splitlines()
        for number, line in enumerate(lines, 1):
            if "shoalmark.py" in line.lower() and line.strip() not in ALLOWED_SHOALMARK_MENTIONS:
                found.append(path.relative_to(HERE).as_posix() + ":" + str(number) + ": " + line.strip())
    return found


def _differs(expected, path):
    try:
        actual = path.read_bytes().decode("utf-8").replace("\r\n", "\n").split("\n")
    except (OSError, ValueError) as error:
        return str(error)
    wanted = expected.split("\n")
    for number, (want, have) in enumerate(zip(wanted, actual), 1):
        prefix, pinned, _ = want.partition(PIN)
        if pinned:
            ok = have.startswith(prefix) and PINNED.fullmatch(have[len(prefix):]) is not None
        else:
            ok = have == want
        if not ok:
            return "line " + str(number) + ": " + repr(have)
    if len(actual) != len(wanted):
        number = min(len(actual), len(wanted))
        return "line " + str(number + 1) + ": " + (repr(actual[number]) if len(actual) > number else "missing")
    return ""


def _raw_steps(text):
    steps, number = {}, None
    for line in text.splitlines():
        match = re.match(r"(\d+)\. ", line)
        if match:
            number = int(match.group(1))
            steps[number] = [line]
        elif number is not None and line.startswith(" ") and line.strip():
            steps[number].append(line)
        else:
            number = None
    return {number: "\n".join(lines) for number, lines in steps.items()}


def _steps(text):
    return {number: " ".join(step.split()) for number, step in _raw_steps(text).items()}


def _sentence(text, clause):
    return next((sentence for sentence in re.split(r"(?<=\.)\s+", text) if clause in sentence), "")


def _key_spans(text):
    return [span for span in BACKTICK_SPAN.findall(text) if "##" in span]


def _paragraphs(text):
    found, lines = [], []
    for line in text.split("\n") + [""]:
        if line.strip():
            lines.append(re.sub(r"^[ \t]+", "", line))
        elif lines:
            found.append(" ".join(lines))
            lines = []
    return found


def _markdown(text):
    parts = {"levels": [], "blocks": [], "installs": [], "last": "", "fenced": set()}
    prose, block, fence, last = [], [], "", 0

    def spans():
        found = re.findall(r"`([^`]+)`", "\n".join(prose))
        parts["installs"].extend(" ".join(span.split()) for span in found if INSTALL.search(span))
        del prose[:]

    lines = text.split("\n")
    for number, line in enumerate(lines):
        stripped = line.lstrip(" ")
        indented = len(line) - len(stripped) > 3
        if fence:
            block.append(line)
            parts["fenced"].add(number)
            if not indented and re.fullmatch(re.escape(fence[0]) + "{" + str(len(fence)) + r",}[ \t]*", stripped):
                parts["blocks"].append("\n".join(block))
                block, fence = [], ""
            elif INSTALL.search(line):
                parts["installs"].append(" ".join(line.split()))
            continue
        opening = re.match(r"`{3,}|~{3,}", stripped)
        heading = re.match(r"(#{1,6})(?:[ \t]|$)", stripped)
        if opening and not indented:
            spans()
            fence, block = opening.group(0), [line]
        elif heading and not indented:
            spans()
            parts["levels"].append(len(heading.group(1)))
            last = number if len(heading.group(1)) <= 2 else last
        else:
            prose.append(line)
    spans()
    if fence:
        parts["blocks"].append("\n".join(block))
    parts["last"] = "\n".join(lines[last:])
    return parts


def _commands(text, fenced):
    commands, unread = [], []
    for number, line in enumerate(text.split("\n")):
        if not INSTALL.search(line):
            continue
        if number in fenced:
            commands.append(" ".join(line.split()))
            continue
        spans = list(BACKTICK_SPAN.finditer(line))
        commands += [" ".join(span.group(1).split()) for span in spans if INSTALL.search(span.group(1))]
        outside = [match for match in INSTALL.finditer(line)
                   if not any(span.start() < match.start() and match.end() < span.end() for span in spans)]
        expanded = line.expandtabs(4)
        if outside and len(expanded) - len(expanded.lstrip(" ")) >= 4:
            commands.append(" ".join(line.split()))
        elif outside:
            unread.append(number + 1)
    return commands, unread


def _references(text):
    return [re.sub(r"[.,]$", "", match.group(0)) for match in REFERENCE.finditer(text)]


def _links(text):
    return re.findall(r"\]\((\S+?)\)", text)


def _hits(pattern, folder):
    found = []
    for path in _files(folder):
        text = path.read_bytes().decode("utf-8", errors="replace")
        for match in pattern.finditer(text):
            line = text.count("\n", 0, match.start()) + 1
            found.append(path.relative_to(HERE).as_posix() + ":" + str(line) + ": " + match.group(0))
    return found


def run_checks(results=None):
    if results is None:
        results = []

    def check(label, ok, detail=""):
        results.append((label, bool(ok), detail))

    def read_json(relative):
        try:
            value = json.loads((HERE / relative).read_text(encoding="utf-8"))
            check(relative + " is a JSON object", isinstance(value, dict))
            return value if isinstance(value, dict) else {}
        except (OSError, ValueError) as error:
            check(relative + " is a JSON object", False, str(error))
            return {}

    claude_market = read_json(".claude-plugin/marketplace.json")
    claude_plugin = read_json(PLUGIN + "/.claude-plugin/plugin.json")
    codex_plugin = read_json(PLUGIN + "/plugin.json")
    codex_market = read_json(".agents/plugins/marketplace.json")
    claude_entries, codex_entries = _entries(claude_market), _entries(codex_market)
    claude_entry = claude_entries[0] if len(claude_entries) == 1 and isinstance(claude_entries[0], dict) else {}
    codex_entry = codex_entries[0] if len(codex_entries) == 1 and isinstance(codex_entries[0], dict) else {}

    check("Claude marketplace name is shoalmark", claude_market.get("name") == NAME)
    owner = claude_market.get("owner")
    check("Claude marketplace owner name is shoalmark", isinstance(owner, dict) and owner.get("name") == NAME)
    check("Claude marketplace lists only shoalmark from ./plugins/shoalmark", len(claude_entries) == 1
          and claude_entry.get("name") == NAME and claude_entry.get("source") == "./" + PLUGIN)
    check("Claude plugin name is shoalmark", claude_plugin.get("name") == NAME)
    check("Claude plugin carries shoalmark's description", claude_plugin.get("description") == DESCRIPTION)
    check("Claude plugin carries the repository's license", claude_plugin.get("license") == LICENSE)

    check("Codex plugin.json names the Agent Plugins schema", codex_plugin.get("$schema") == SCHEMA_URL)
    codex_name = codex_plugin.get("name")
    check("Codex plugin.json name meets the schema's pattern and length", isinstance(codex_name, str)
          and 1 <= len(codex_name) <= 64 and SCHEMA_NAME.fullmatch(codex_name) is not None)
    extra = sorted(set(codex_plugin) - set(SCHEMA_PROPERTIES))
    check("Codex plugin.json carries only the schema's properties", not extra, "outside the schema: " + ", ".join(extra))
    check("Codex plugin.json sets no skills field", "skills" not in codex_plugin)
    check("Codex marketplace name is shoalmark", codex_market.get("name") == NAME)
    interface = codex_market.get("interface")
    check("Codex marketplace has an interface.displayName", isinstance(interface, dict)
          and isinstance(interface.get("displayName"), str) and bool(interface["displayName"].strip()))
    codex_source = codex_entry.get("source")
    check("Codex marketplace lists only shoalmark from ./plugins/shoalmark", len(codex_entries) == 1
          and codex_entry.get("name") == NAME and isinstance(codex_source, dict)
          and codex_source.get("source") == "local" and codex_source.get("path") == "./" + PLUGIN)
    policy = codex_entry.get("policy")
    check("Codex marketplace entry carries its install policy and category", isinstance(policy, dict)
          and policy.get("installation") in CODEX_INSTALLATION
          and isinstance(policy.get("authentication"), str) and bool(policy["authentication"].strip())
          and isinstance(codex_entry.get("category"), str) and bool(codex_entry["category"].strip()))

    names = [claude_plugin.get("name"), claude_entry.get("name"), codex_plugin.get("name"), codex_entry.get("name")]
    check("Claude and Codex agree on the plugin name", isinstance(names[0], str) and _same(names))
    check("Claude and Codex agree on the marketplace name", isinstance(claude_market.get("name"), str)
          and _same([claude_market.get("name"), codex_market.get("name")]))
    descriptions = [claude_plugin.get("description"), codex_plugin.get("description")]
    descriptions += [entry["description"] for entry in claude_entries + codex_entries
                     if isinstance(entry, dict) and "description" in entry]
    check("Claude and Codex agree on the description, entries included", isinstance(descriptions[0], str)
          and _same(descriptions))
    check("Claude and Codex agree on the licence", isinstance(claude_plugin.get("license"), str)
          and _same([claude_plugin.get("license"), codex_plugin.get("license")]))
    claude_root, codex_root = _local_path(claude_entry.get("source")), _local_path(codex_source)
    claude_skills = claude_plugin.get("skills", "./skills/")
    claude_skills = claude_skills if isinstance(claude_skills, list) else [claude_skills]
    claude_folder = claude_root + "/skills" if claude_root and claude_skills in (["./skills/"], ["./skills"]) else None
    codex_folder = codex_root + "/skills" if codex_root and "skills" not in codex_plugin else None
    check("Claude and Codex both resolve the skills folder to plugins/shoalmark/skills/",
          claude_folder == codex_folder == SKILLS and (HERE / SKILLS).is_dir(),
          "Claude: " + str(claude_folder) + ", Codex: " + str(codex_folder))

    versions = []
    for label, manifest in (("Claude marketplace", claude_market), ("Claude plugin.json", claude_plugin),
                            ("Codex plugin.json", codex_plugin), ("Codex marketplace", codex_market)):
        versions += [(where, json.dumps(value)) for where, value in _versions(label, manifest)]
    changelog = HERE / "CHANGELOG.md"
    if changelog.is_file():
        headings = re.findall(r"(?m)^##[ \t]+(.+?)[ \t]*$", changelog.read_text(encoding="utf-8"))
        released = [VERSION.search(heading) for heading in headings if heading.strip("[] ").lower() != "unreleased"]
        released = [match.group(0) for match in released if match]
        if released:
            versions.append(("CHANGELOG.md newest release", json.dumps(released[0])))
    check("every version present agrees across the manifests and the CHANGELOG (" + str(len(versions)) + " found)",
          len({value for _, value in versions}) <= 1, "; ".join(where + ": " + value for where, value in versions))
    check("Claude plugin.json and its marketplace entry do not both set version",
          not ("version" in claude_plugin and "version" in claude_entry))

    plugin_versions = [manifest["version"] for manifest in (claude_plugin, codex_plugin) if "version" in manifest]
    release = plugin_versions[0] if plugin_versions and _same(plugin_versions) else None
    release = release if isinstance(release, str) else None
    check("Claude and Codex plugin manifests both set version to the same X.Y.Z",
          len(plugin_versions) == 2 and release is not None and RELEASE.fullmatch(release) is not None,
          "Claude: " + json.dumps(claude_plugin.get("version")) + ", Codex: " + json.dumps(codex_plugin.get("version")))
    markets = (("Claude marketplace", claude_market), ("Codex marketplace", codex_market))
    in_markets = [where for label, market in markets for where, _ in _versions(label, market)]
    check("neither marketplace sets version: not at its top level, in metadata or in an entry", not in_markets,
          "set in: " + ", ".join(in_markets))
    headings = re.findall(r"(?m)^(##[ \t]+(.+?)[ \t]*)$", _text(changelog))
    newest = next((line for line, title in headings if title.strip("[] ").lower() != "unreleased"), "")
    heading = RELEASE_HEADING.fullmatch(newest)
    check("CHANGELOG.md's newest released heading is exactly ## X.Y.Z, an em dash and a real YYYY-MM-DD date, "
          "at the plugin manifests' version",
          heading is not None and _real_date(heading.group(2)) and heading.group(1) == release,
          "heading: " + repr(newest) + ", plugin manifests: " + json.dumps(release))
    unnamed = [relative for relative in HOLDER_FILES
               if not re.search(r"(?m)^Copyright .+ " + re.escape(AUTHOR["name"]) + "$", _text(HERE / relative))]
    check("both plugin manifests carry the author " + json.dumps(AUTHOR) + ", the holder "
          + " and ".join(HOLDER_FILES) + " name",
          claude_plugin.get("author") == AUTHOR and codex_plugin.get("author") == AUTHOR and not unnamed,
          "Claude: " + json.dumps(claude_plugin.get("author")) + ", Codex: " + json.dumps(codex_plugin.get("author"))
          + ("; no Copyright line names it in: " + ", ".join(unnamed) if unnamed else ""))
    check("Claude marketplace carries shoalmark's description at its top level",
          claude_market.get("description") == DESCRIPTION)

    skills = HERE / SKILLS
    check("plugins/shoalmark/skills contains skills", skills.is_dir() and any(path.is_dir() for path in skills.iterdir()))
    plugins = sorted(path for path in (HERE / "plugins").iterdir() if path.is_dir()) if (HERE / "plugins").is_dir() else []
    for plugin in plugins:
        folders = (plugin / "skills").iterdir() if (plugin / "skills").is_dir() else ()
        for folder in sorted(path for path in folders if path.is_dir()):
            path = folder / "SKILL.md"
            relative = path.relative_to(HERE).as_posix()
            check(relative + " exists", path.is_file())
            if not path.is_file():
                continue
            text = path.read_text(encoding="utf-8")
            try:
                fields = _front_matter(text)
            except (OSError, ValueError) as error:
                check(relative + " front matter parses", False, str(error))
                continue
            check(relative + " front matter parses", True)
            name = fields.get("name", "")
            check(relative + " name matches its folder", name == folder.name)
            check(relative + " name meets the Agent Skills rules", len(name) <= 64 and SKILL_NAME.fullmatch(name) is not None)
            description = fields.get("description", "")
            check(relative + " description has 1 to 1024 characters", 0 < len(description) <= 1024)
            compatibility = fields.get("compatibility")
            check(relative + " compatibility has 1 to 500 characters when present",
                  compatibility is None or 0 < len(compatibility) <= 500)
            if plugin.name == NAME:
                check(relative + " carries the works-anywhere compatibility wording", compatibility == WORKS_ANYWHERE)
                check(relative + " keeps its description and compatibility as written, in English",
                      (description, compatibility) == FRONT_MATTER.get(folder.name))
            else:
                check(relative + " carries a needs-shoalmark compatibility wording",
                      bool(compatibility) and compatibility != WORKS_ANYWHERE)
            hits = _hits(ONE_HARNESS_TOOL, folder)
            check(folder.relative_to(HERE).as_posix() + " names no tool only one harness has", not hits,
                  "\n        ".join(hits))
    links = [path.relative_to(HERE).as_posix() for path in _walk(HERE / "plugins")[1]]
    check("plugins/ holds no symbolic link", not links, "\n        ".join(links))
    mentions = _mentions(HERE / PLUGIN)
    check(PLUGIN + " mentions shoalmark.py on no line outside ALLOWED_SHOALMARK_MENTIONS", not mentions,
          "\n        ".join(mentions))
    promotions = []
    for path in _walk(HERE / "plugins")[0]:
        text = path.read_bytes().decode("utf-8", errors="replace")
        promotions += [path.relative_to(HERE).as_posix() + ":" + str(text.count("\n", 0, match.start()) + 1) + ": "
                       + match.group(0) for match in PROMOTION.finditer(text)]
    check("plugins/ names neither shoalmark's site nor its repository; the way to shoalmark is in the READMEs",
          not promotions, "\n        ".join(promotions))
    others = [path.name for path in plugins if path.name != NAME]
    check("plugins/ holds no plugin folder but shoalmark; the lane that adds a second plugin writes its gate check",
          not others, "found: " + ", ".join(others))

    for relative in ROOT_TEXTS:
        check(relative + " exists", (HERE / relative).is_file())
    for relative in PUBLIC_ID_SCAN:
        for path in _files(HERE / relative):
            text = path.read_bytes().decode("utf-8", errors="replace")
            check(path.relative_to(HERE).as_posix() + " has no tracker or review id", PUBLIC_ID.search(text) is None)
    for relative in HOME_PATH_SCAN:
        for path in _files(HERE / relative):
            text = path.read_bytes().decode("utf-8", errors="replace")
            check(path.relative_to(HERE).as_posix() + " has no home folder path", HOME_PATH.search(text) is None)

    twins = {}
    for relative in TWINS:
        try:
            twins[relative] = (HERE / relative).read_text(encoding="utf-8")
        except (OSError, ValueError):
            twins[relative] = ""
    english, german = (_markdown(twins[relative]) for relative in TWINS)
    pair = " and ".join(TWINS)
    check(pair + " have the same sequence of heading levels", english["levels"] == german["levels"],
          " | ".join(relative + ": " + " ".join("#" * level for level in parts["levels"])
                     for relative, parts in zip(TWINS, (english, german))))
    differ = [str(index + 1) for index in range(max(len(english["blocks"]), len(german["blocks"])))
              if english["blocks"][index:index + 1] != german["blocks"][index:index + 1]]
    check(pair + " have every fenced code block equal, in order", not differ,
          "blocks that differ: " + ", ".join(differ))
    check(pair + " have every install command equal, in order",
          english["installs"] == german["installs"] and bool(english["installs"]),
          " | ".join(relative + ": " + "; ".join(parts["installs"])
                     for relative, parts in zip(TWINS, (english, german))))
    closing = []
    for relative, parts in zip(TWINS, (english, german)):
        wanted = (REPOSITORY, FEEDBACK) + OWN_PAGES[relative]
        closing += [relative + " last section lacks " + link for link in wanted if link not in _links(parts["last"])]
        for link in _links(twins[relative]):
            site = max((path for path in OWN_SITE.values() if link.startswith(path)), key=len, default=None)
            if link != FEEDBACK and site not in (None, OWN_SITE[relative]):
                closing.append(relative + " links " + link + ", a page in another language")
    check(pair + " end with the repository, the feedback form and their own language's Why and setup pages",
          not closing, "; ".join(closing))
    unpinned = []
    for relative, parts in zip(TWINS, (english, german)):
        commands, unread = _commands(twins[relative], parts["fenced"])
        adds = [command for command in commands if MARKETPLACE_ADD in command]
        unpinned += [relative + ": " + add for add in adds if add.split()[-1] != PIN_SOURCE + str(release)]
        unpinned += [] if adds else [relative + ": no " + MARKETPLACE_ADD]
        unpinned += [relative + ": reference " + reference for reference in _references(twins[relative])
                     if reference.split("@", 1)[1] != "v" + str(release)]
        unpinned += [relative + ":" + str(number) + ": an install command in a form the checks do not read"
                     for number in unread]
    check(pair + " pin every " + MARKETPLACE_ADD + " and every shoalmark/skills@ reference, in code or prose, to "
          + PIN_SOURCE + "<the plugin manifests' version>, and leave no install command unread",
          release is not None and not unpinned,
          "plugin manifests: " + json.dumps(release) + "; " + " | ".join(unpinned))
    placeholders = [relative for relative in TWINS if PLACEHOLDER in twins[relative]]
    check(pair + " hold no " + PLACEHOLDER, not placeholders, "found in: " + ", ".join(placeholders))

    workflows = HERE / ".github" / "workflows"
    found = sorted(path.name for path in workflows.iterdir()) if workflows.is_dir() else []
    check(".github/workflows holds exactly one file, ci.yml", found == ["ci.yml"] and (workflows / "ci.yml").is_file(),
          "found: " + ", ".join(found))
    problem = _differs(CI_YML, workflows / "ci.yml")
    check(".github/workflows/ci.yml equals the expected text but for its two pin values", not problem, problem)
    problem = _differs(DEPENDABOT_YML, HERE / ".github" / "dependabot.yml")
    check(".github/dependabot.yml equals the expected text", not problem, problem)

    find_folder = skills / "find-drift"
    find_raw = (find_folder / "SKILL.md").read_text(encoding="utf-8")
    prune_raw = (skills / "prune-drift" / "SKILL.md").read_text(encoding="utf-8")
    find_text, prune_text = " ".join(find_raw.split()), " ".join(prune_raw.split())
    check("find-drift closing paragraph: secrets and unrecorded weaknesses stop; documented gaps are drift",
          all(clause in find_text for clause in (
              "Stop when you meet a secret",
              "write nothing about it and tell the person",
              "drift, not a stop"))
          and "Open no record on a security subject; name the class left out as a limit, "
              "and stop on a secret or weakness met." not in find_text)

    find_close = find_text.partition("11. Close:")[2].split(" Never run a test suite,", 1)[0]
    prune_link = re.search(r"\[prune-drift\]\(([^)]+)\)", find_close)
    check("find-drift step 11: close with decisions and the prune-drift link",
          all(clause in find_text for clause in (
              "11. Close:",
              "in your last message, not only in the report",
              "ask whether to file them as asks"))
          and 0 <= find_text.find("10. ") < find_text.find("11. Close:")
          and prune_link is not None and (find_folder / prune_link.group(1)).is_file())

    check("prune-drift step 8: limit direct edits and propose other fixes",
          all(clause in prune_text for clause in (
              "Edit directly only in documentation files",
              "write the exact proposed fix for the person instead")))
    check("prune-drift step 10: secrets and unrecorded weaknesses stop; documented gaps do not",
          all(clause in prune_text for clause in (
              "Stop when you meet a secret",
              "name only the class left out as a limit, and tell the person",
              "is not a stop"))
          and "Stop on a secret or weakness met and name only the class left out as a limit." not in prune_text)
    check("prune-drift step 11: ask about verification as a separate task",
          all(clause in prune_text for clause in (
              "11. Close:",
              "ask whether to run them before anything merges",
              "This skill runs none of them"))
          and 0 <= prune_text.find("10. ") < prune_text.find("11. Close:"))

    find_keys, prune_keys = REPORT_KEY.findall(find_text), REPORT_KEY.findall(prune_text)
    written = REPORT_KEY.findall(_steps(find_raw).get(10, ""))
    check("find-drift step 10 names the report's seven section keys, each as `## <key>`, in order",
          written == list(REPORT_KEYS), "step 10 names: " + ", ".join(written))
    check("find-drift names no other `## <key>`", set(find_keys) <= set(REPORT_KEYS),
          "unknown: " + ", ".join(sorted(set(find_keys) - set(REPORT_KEYS))))
    check("prune-drift names only `## <key>` that find-drift's step 10 writes",
          set(prune_keys) <= set(REPORT_KEYS) and set(prune_keys) <= set(written),
          "unknown: " + ", ".join(sorted(set(prune_keys) - (set(REPORT_KEYS) & set(written)))))
    prune_steps = _steps(prune_raw)
    unread = ["step " + str(number) + ": ## " + key for number, keys in sorted(PRUNE_READS.items()) for key in keys
              if key not in REPORT_KEY.findall(prune_steps.get(number, ""))]
    check("prune-drift names each key it reads at the step that reads it", not unread, "missing: " + ", ".join(unread))

    for skill, text in (("find-drift", find_text), ("prune-drift", prune_text)):
        sentence = _sentence(text, "the language the person writes in")
        missing = [clause for clause in LANGUAGE_CLAUSES if clause not in sentence]
        check(skill + " carries the language rule in one sentence", not missing, "missing: " + " | ".join(missing))

    for skill, raw in (("find-drift", find_raw), ("prune-drift", prune_raw)):
        found = [paragraph for paragraph in _paragraphs(raw) if "in their language" in paragraph]
        check(skill + " holds its language sentence exactly as pinned, as its own paragraph",
              LANGUAGE_SENTENCE[skill] in _paragraphs(raw), "found: " + (repr(found[0]) if found else "nothing"))

    spans = {"find-drift": _key_spans(find_raw), "prune-drift": _key_spans(prune_raw)}
    step10 = _key_spans(_raw_steps(find_raw).get(10, ""))
    check("find-drift step 10 holds exactly the seven `## <key>` spans as written, in order",
          step10 == list(REPORT_SPANS), "step 10 holds: " + ", ".join(repr(span) for span in step10))
    for skill, found in sorted(spans.items()):
        unknown = [span for span in found if span not in REPORT_SPANS]
        check(skill + " holds no `##` span but the seven, as written", not unknown,
              "unknown: " + ", ".join(repr(span) for span in unknown))
    raw_steps = _raw_steps(prune_raw)
    unread = ["step " + str(number) + ": ## " + key for number, keys in sorted(PRUNE_READS.items()) for key in keys
              if "## " + key not in _key_spans(raw_steps.get(number, ""))]
    check("prune-drift holds each key it reads, as written, at the step that reads it", not unread,
          "missing: " + ", ".join(unread))
    return results


if __name__ == "__main__":
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8", errors="replace")
    checks = run_checks()
    for label, ok, detail in checks:
        print(("  ok    " if ok else "  FAIL  ") + label)
        if not ok and detail:
            print("        " + detail)
    failures = sum(not ok for _, ok, _ in checks)
    print("\n" + ("FAILED: " + str(failures) if failures else "all green"))
    sys.exit(1 if failures else 0)
