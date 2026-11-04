import json
from pathlib import Path
import posixpath
import re
import sys


HERE = Path(__file__).resolve().parent
PUBLIC_ID = re.compile(r"\b(?:FM|RV|SP|HL|FEAT|BUG)-\d+\b")
HOME_PATH = re.compile(r"(?i)(?:/(?:Users|home)/|[a-z]:[/\\]+Users[/\\]+|~[/\\]|%USERPROFILE%|\$(?:HOME\b|\{HOME\}))")
PUBLIC_ID_SCAN = ("plugins", ".claude-plugin", ".agents", ".github", "README.md", "CHANGELOG.md", "SECURITY.md")
HOME_PATH_SCAN = ("plugins", ".claude-plugin", ".agents", ".github")

NAME = "shoalmark"
PLUGIN = "plugins/shoalmark"
SKILLS = PLUGIN + "/skills"
DESCRIPTION = "Skills that find repository rules held only as prose, conflicting sources and obsolete guidance."
LICENSE = "Apache-2.0 OR MIT"
SCHEMA_URL = "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json"
SCHEMA_PROPERTIES = ("$schema", "name", "version", "description", "author", "homepage", "repository", "license",
                     "keywords", "extensions")
SCHEMA_NAME = re.compile(r"(?!.*(?:--|\.\.))[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?")
CODEX_INSTALLATION = ("AVAILABLE", "INSTALLED_BY_DEFAULT", "NOT_AVAILABLE")
SKILL_NAME = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
WORKS_ANYWHERE = "Any git repository. Uses shoalmark.toml when present; never runs shoalmark."
VERSION = re.compile(r"\d+(?:\.\d+)+(?:[-+][0-9A-Za-z.-]+)?")
ONE_HARNESS_TOOL = re.compile(
    r"\b(?:AskUserQuestion|EndConversation|TodoWrite|apply_patch|update_plan)\b"
    r"|\b(?:Bash|PowerShell|Skill|LSP)`?[ \t]+tools?\b")
SHOALMARK_COMMAND = re.compile(
    r"(?<![\w./-])(?:python[0-9.]*|pypy[0-9.]*|py|uv[ \t]+run|pipx[ \t]+run|sys\.executable|subprocess|os\.system)"
    r"(?![\w-])(?:(?![.;:]\s)[^\n]){0,80}?\bshoalmark\.py\b"
    r"|(?<![\w.-])\.{1,2}/(?:[\w.-]+/)*shoalmark\.py\b"
    r"|\bshoalmark\.py`?[ \t]+-{1,2}[A-Za-z]")
PINNED_USES = re.compile(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+@[0-9a-f]{40}[ \t]+#[ \t]*\S+")
JOB_NAMES = ("tests (ubuntu, 3.9)", "tests (ubuntu, 3.12)", "tests (macos, 3.12)", "tests (windows, 3.9)",
             "tests (windows, 3.12)")


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


def _starts_with_gate(text):
    lines = text.splitlines()
    body = "\n".join(lines[lines.index("---", 1) + 1:])
    match = re.search(r"(?ms)^1\.[ \t]+(.*?)(?=^\d+\.[ \t]|\Z)", body)
    if match:
        step = match.group(1)
    else:
        paragraphs = [part for part in re.split(r"\n[ \t]*\n", body) if part.strip() and not part.lstrip().startswith("#")]
        step = paragraphs[0] if paragraphs else ""
    step = " ".join(step.split())
    return all(word in step for word in ("pinned", "shoalmark.py", "--version", "--check")) and (
        step.index("pinned") < step.index("--version") < step.index("--check"))


def _entries(marketplace):
    entries = marketplace.get("plugins")
    return entries if isinstance(entries, list) else []


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


def _yaml_lines(text):
    lines = []
    for line in text.splitlines():
        content = re.sub(r"(?:^|\s)#.*$", "", line).rstrip()
        if content.strip():
            lines.append((len(content) - len(content.lstrip(" ")), content.strip()))
    return lines


def _children(lines, index):
    children = []
    for depth, text in lines[index + 1:]:
        if depth <= lines[index][0]:
            break
        children.append((depth, text))
    return children


def _compact(text):
    return re.sub(r"[\s\"']+", "", text)


def _triggers_ok(lines):
    tops = [index for index, (depth, text) in enumerate(lines) if depth == 0 and re.match(r"[\"']?on[\"']?:", text)]
    if len(tops) != 1 or _compact(lines[tops[0]][1].split(":", 1)[1]):
        return False
    children = _children(lines, tops[0])
    events = {}
    for index, (depth, text) in enumerate(children):
        if depth == children[0][0]:
            key, _, value = text.partition(":")
            events[_compact(key)] = (_compact(value), [_compact(item) for _, item in _children(children, index)])
    if set(events) != {"push", "pull_request"}:
        return False
    return (events["push"] == ("", ["branches:[main]"]) or events["push"] == ("", ["branches:", "-main"])) and (
        events["pull_request"][0] in ("", "{}", "null", "~") and not events["pull_request"][1])


def _permissions_ok(lines):
    found = [index for index, (_, text) in enumerate(lines) if re.match(r"[\"']?permissions[\"']?:", text)]
    if len(found) != 1 or lines[found[0]][0] != 0:
        return False
    value = _compact(lines[found[0]][1].split(":", 1)[1])
    children = [_compact(text) for _, text in _children(lines, found[0])]
    return (value == "{contents:read}" and not children) or (value == "" and children == ["contents:read"])


def _job_names(lines):
    tops = [index for index, (depth, text) in enumerate(lines) if depth == 0 and text == "jobs:"]
    jobs = _children(lines, tops[0]) if len(tops) == 1 else []
    names = []
    for index, (depth, text) in enumerate(jobs):
        if depth != jobs[0][0]:
            continue
        body = _children(jobs, index)
        template, rows = text.rstrip(":"), []
        for position, (inner, line) in enumerate(body):
            if inner == body[0][0] and line.startswith("name:"):
                template = line[len("name:"):].strip().strip("\"'")
            if line == "include:":
                for _, row in _children(body, position):
                    match = re.fullmatch(r"-\s*\{(.*)\}", row)
                    pairs = [part.split(":", 1) for part in match.group(1).split(",") if ":" in part] if match else []
                    rows.append({key.strip(): value.strip().strip("\"'") for key, value in pairs})
        for row in rows or [{}]:
            names.append(re.sub(r"\$\{\{\s*matrix\.([\w-]+)\s*\}\}",
                                lambda match: row.get(match.group(1), "(no " + match.group(1) + ")"), template))
    return names


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
        holders = [(label, manifest), (label + " metadata", manifest.get("metadata"))]
        holders += [(label + " entry " + str(index), entry) for index, entry in enumerate(_entries(manifest))]
        for where, holder in holders:
            if isinstance(holder, dict) and "version" in holder:
                versions.append((where, json.dumps(holder["version"])))
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

    skills = HERE / SKILLS
    check("plugins/shoalmark/skills contains skills", skills.is_dir() and any(path.is_dir() for path in skills.iterdir()))
    plugins = sorted(path for path in (HERE / "plugins").iterdir() if path.is_dir()) if (HERE / "plugins").is_dir() else []
    gated = []
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
                hits = _hits(SHOALMARK_COMMAND, folder)
                check(folder.relative_to(HERE).as_posix() + " never names shoalmark.py as a command", not hits,
                      "\n        ".join(hits))
            else:
                check(relative + " carries a needs-shoalmark compatibility wording",
                      bool(compatibility) and compatibility != WORKS_ANYWHERE)
                gated.append((relative, _starts_with_gate(text)))
            hits = _hits(ONE_HARNESS_TOOL, folder)
            check(folder.relative_to(HERE).as_posix() + " names no tool only one harness has", not hits,
                  "\n        ".join(hits))
    check("each needs-shoalmark skill starts with the gate (" + str(len(gated)) + " found)",
          all(ok for _, ok in gated), "without the gate: " + ", ".join(relative for relative, ok in gated if not ok))

    for relative in PUBLIC_ID_SCAN:
        for path in _files(HERE / relative):
            text = path.read_bytes().decode("utf-8", errors="replace")
            check(path.relative_to(HERE).as_posix() + " has no tracker or review id", PUBLIC_ID.search(text) is None)
    for relative in HOME_PATH_SCAN:
        for path in _files(HERE / relative):
            text = path.read_bytes().decode("utf-8", errors="replace")
            check(path.relative_to(HERE).as_posix() + " has no home folder path", HOME_PATH.search(text) is None)

    workflows = HERE / ".github" / "workflows"
    job_names = []
    for path in sorted(workflows.glob("*.yml")) + sorted(workflows.glob("*.yaml")) if workflows.is_dir() else []:
        relative = path.relative_to(HERE).as_posix()
        text = path.read_text(encoding="utf-8")
        lines = _yaml_lines(text)
        uses = [re.sub(r"^\s*(?:-\s+)?uses:", "", line).strip() for line in text.splitlines()
                if re.match(r"\s*(?:-\s+)?uses:", line)]
        check(relative + " pins every uses: to owner/repo@<40 hex> # <tag>",
              all(PINNED_USES.fullmatch(value) for value in uses), "\n        ".join(uses))
        check(relative + " grants only contents: read, at the top level", _permissions_ok(lines))
        check(relative + " triggers on push to main and pull_request only", _triggers_ok(lines))
        check(relative + " has no pull_request_target and no secrets.",
              "pull_request_target" not in text and "secrets." not in text)
        job_names += _job_names(lines)
    check(".github/workflows job names are exactly the five tests (<os>, <python>)",
          sorted(job_names) == sorted(JOB_NAMES), "found: " + "; ".join(job_names))
    dependabot = HERE / ".github" / "dependabot.yml"
    check(".github/dependabot.yml names the github-actions ecosystem", dependabot.is_file() and re.search(
        r"(?m)^[ \t]*(?:-[ \t]+)?package-ecosystem:[ \t]*[\"']?github-actions[\"']?[ \t]*$",
        dependabot.read_text(encoding="utf-8")) is not None)

    find_folder = skills / "find-drift"
    find_text = " ".join((find_folder / "SKILL.md").read_text(encoding="utf-8").split())
    prune_text = " ".join((skills / "prune-drift" / "SKILL.md").read_text(encoding="utf-8").split())
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
