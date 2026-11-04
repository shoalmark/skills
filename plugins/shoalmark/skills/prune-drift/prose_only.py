import argparse
import ast
import io
from pathlib import Path
import re
import subprocess
import sys
import tokenize


SCOPES = (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)
READERS = {"getdoc", "doctest", "docopt"}
DIRECTIVES = ("type:", "noqa", "pragma", "fmt:", "pylint:", "isort:")


def git(root, *args):
    result = subprocess.run(["git", *args], cwd=root, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode:
        raise ValueError("git " + args[0] + " failed (exit " + str(result.returncode) + ")")
    return result.stdout


def revision(root, name):
    value = git(root, "rev-parse", "--verify", "--end-of-options", name + "^{commit}").decode("ascii").strip()
    if not re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", value):
        raise ValueError("expected a commit id")
    return value


def python_path(path):
    return path.lower().endswith((".py", ".pyw"))


def snapshot(root, rev):
    files = {}
    for entry in git(root, "ls-tree", "-rz", "--full-tree", rev).split(b"\0"):
        if not entry:
            continue
        header, raw_path = entry.split(b"\t", 1)
        mode, kind, _ = header.decode("ascii").split()
        path = raw_path.decode("utf-8", errors="surrogateescape")
        data, tree = None, None
        if python_path(path) and kind == "blob" and mode in ("100644", "100755"):
            data = git(root, "show", rev + ":" + path)
            try:
                tree = ast.parse(data, filename=path)
            except (SyntaxError, ValueError, UnicodeError):
                pass
        files[path] = (mode, data, tree)
    return files


def readers(files):
    own, any_doc, unknown = {}, [], []
    for path, (_, data, tree) in sorted(files.items()):
        if not python_path(path):
            continue
        if tree is None:
            unknown.append(path)
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Name) and node.id == "__doc__":
                own.setdefault(path, []).append(node.lineno)
            names = []
            if isinstance(node, ast.Name):
                names = [node.id]
            elif isinstance(node, ast.Attribute):
                names = [node.attr]
                if node.attr == "__doc__":
                    any_doc.append((path, node.lineno, ".__doc__"))
            elif isinstance(node, ast.Import):
                names = [part for alias in node.names for part in alias.name.split(".") + [alias.asname]]
            elif isinstance(node, ast.ImportFrom):
                names = (node.module or "").split(".")
                names += [part for alias in node.names for part in (alias.name, alias.asname)]
            for name in sorted(READERS.intersection(names)):
                any_doc.append((path, node.lineno, name))
    return own, sorted(set(any_doc)), unknown


def directives(data):
    activation = (data.startswith(b"#!"), data.startswith(b"\xef\xbb\xbf#!"))
    line, newline, _ = data.partition(b"\n")
    shebang = line + newline if activation[0] else None
    found, position = [], 0
    for token in tokenize.tokenize(io.BytesIO(data).readline):
        if token.type == tokenize.COMMENT:
            text = token.string[1:].lstrip()
            header = token.start[0] <= 2 and (
                token.string.startswith("#!") or re.search(r"coding[:=]\s*[-\w.]+", text)
            )
            if header or text.lower().startswith(DIRECTIVES) or "SPDX-License-Identifier" in token.string:
                prefix = token.line[:token.start[1]]
                attachment = ("inline" if prefix.strip() else "own-line", prefix)
                found.append((position, token.string, attachment))
        elif token.type not in (tokenize.ENCODING, tokenize.NL, tokenize.ENDMARKER):
            position += 1
    return activation, shebang, found


def strip_docstrings(tree):
    records, had_docstring, emptied = [], set(), set()

    def visit(node, path):
        if isinstance(node, SCOPES) and ast.get_docstring(node, clean=False) is not None:
            records.append((path, node.body[0].value.value))
            had_docstring.add(id(node))
            del node.body[0]
            if not node.body:
                emptied.add(id(node))
        for field, value in ast.iter_fields(node):
            if isinstance(value, ast.AST):
                visit(value, path + "." + field)
            elif isinstance(value, list):
                for index, child in enumerate(value):
                    if isinstance(child, ast.AST):
                        visit(child, path + "." + field + "[" + str(index) + "]")

    visit(tree, "Module")
    return records, had_docstring, emptied


def accept_empty_pass(before, after, emptied, after_docstrings):
    if type(before) is not type(after):
        return
    if (id(before) in emptied and id(after) not in after_docstrings
            and len(after.body) == 1 and isinstance(after.body[0], ast.Pass)):
        after.body = []
    for field, value in ast.iter_fields(before):
        other = getattr(after, field)
        if isinstance(value, ast.AST) and isinstance(other, ast.AST):
            accept_empty_pass(value, other, emptied, after_docstrings)
        elif isinstance(value, list) and isinstance(other, list):
            for child, peer in zip(value, other):
                if isinstance(child, ast.AST) and isinstance(peer, ast.AST):
                    accept_empty_pass(child, peer, emptied, after_docstrings)


def first_difference(before, after, path="Module"):
    if type(before) is not type(after):
        return path + " (node type)"
    if isinstance(before, ast.AST):
        for field, value in ast.iter_fields(before):
            result = first_difference(value, getattr(after, field), path + "." + field)
            if result:
                return result
    elif isinstance(before, list):
        for index, (child, peer) in enumerate(zip(before, after)):
            result = first_difference(child, peer, path + "[" + str(index) + "]")
            if result:
                return result
        if len(before) != len(after):
            return path + " (length)"
    elif before != after:
        return path
    return ""


def compare(path, before, after, own_readers, any_readers, unknown_readers):
    if before is None or after is None:
        return "file added or deleted"
    old_mode, old_data, old_tree = before
    new_mode, new_data, new_tree = after
    if old_mode != new_mode:
        return "file mode changed"
    if not python_path(path):
        return "not a Python file; outside the proof"
    if old_tree is None or new_tree is None:
        return "cannot parse Python at one or both revisions"
    try:
        if directives(old_data) != directives(new_data):
            return "directive comments differ"
    except (tokenize.TokenError, SyntaxError, UnicodeError):
        return "cannot tokenize Python at one or both revisions"
    module_changed = ast.get_docstring(old_tree, clean=False) != ast.get_docstring(new_tree, clean=False)
    old_docs, _, emptied = strip_docstrings(old_tree)
    new_docs, after_docstrings, _ = strip_docstrings(new_tree)
    if old_docs != new_docs:
        if any_readers or unknown_readers:
            return "docstring changed with a repository reader or an unreadable reader source"
        if module_changed and path in own_readers:
            return "module docstring changed with its own __doc__ reader"
    accept_empty_pass(old_tree, new_tree, emptied, after_docstrings)
    if ast.dump(old_tree, include_attributes=False) != ast.dump(new_tree, include_attributes=False):
        return "AST differs at " + first_difference(old_tree, new_tree)
    return "prose-only"


def main(argv=None):
    parser = argparse.ArgumentParser(description="Compare Python prose at two commits without writing files.")
    parser.add_argument("before_rev")
    parser.add_argument("after_rev")
    parser.add_argument("paths", nargs="*", help="literal repository-relative file paths; default: all changed files")
    args = parser.parse_args(argv)
    try:
        root = Path(git(None, "rev-parse", "--show-toplevel").decode("utf-8", errors="surrogateescape").strip())
        before_rev, after_rev = revision(root, args.before_rev), revision(root, args.after_rev)
        before, after = snapshot(root, before_rev), snapshot(root, after_rev)
        own_readers, any_readers, unknown_readers = {}, [], []
        for label, files in (("before", before), ("after", after)):
            own, any_doc, unknown = readers(files)
            for path, lines in sorted(own.items()):
                own_readers.setdefault(path, []).extend(lines)
                for line in sorted(set(lines)):
                    print("reader " + label + " " + path + ":" + str(line) + ": own __doc__")
            for path, line, name in any_doc:
                print("reader " + label + " " + path + ":" + str(line) + ": " + name)
            for path in unknown:
                print("reader scan " + label + " " + path + ": cannot parse tracked Python")
            any_readers.extend(any_doc)
            unknown_readers.extend(unknown)
        if args.paths:
            paths = sorted(set(args.paths))
        else:
            changed = git(root, "diff-tree", "-r", "--no-commit-id", "--no-renames", "--name-only", "-z",
                          before_rev, after_rev, "--")
            paths = sorted(path.decode("utf-8", errors="surrogateescape") for path in changed.split(b"\0") if path)
        failed = False
        for path in paths:
            result = compare(path, before.get(path), after.get(path), own_readers, any_readers, unknown_readers)
            print(path + ": " + result)
            failed = failed or result != "prose-only"
        if not paths:
            print("no changed files: prose-only")
        return 1 if failed else 0
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        print("not prose-only: " + str(error), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
