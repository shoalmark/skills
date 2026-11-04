# shoalmark-Skills

[English](README.md)

Zwei Agent-Skills aus [shoalmark](https://github.com/shoalmark/shoalmark), als ein Plugin für Claude Code und Codex
verpackt.

Noch ist kein Release getaggt.

## Die Skills

- **find-drift** findet jede Stelle in einem Repository, an der ein Agent vom Kurs abkommen könnte: Regeln, die nur
  als Prosa festgehalten sind, Quellen, die einander widersprechen, und veralteter Text, der sich noch liest, als
  gälte er. Es ordnet nach Rang, was zu einer Prüfung werden kann. Es liest das Repository und schreibt einen Bericht
  und seine Prüfsumme. Nutze es vor einem Release oder bevor du Prosa ausdünnst.
- **prune-drift** entfernt schon belegte Historie aus Kommentaren und ungelesenen Docstrings in versioniertem Code,
  gestützt auf den Bericht von find-drift und einen Beweis, dass der Code gleich bleibt. Es hält zuerst fehlende
  Begründungen fest, listet Regeln auf, die zu Prüfungen werden könnten, und korrigiert veraltete oder
  widersprüchliche Prosa nur dort, wo eine Quelle, die sie ablöst, es entscheidet. Es arbeitet auf einem neuen
  Branch. Nutze es nach find-drift.

## Zwei Gruppen

- **Überall einsetzbare Skills** liegen in `plugins/shoalmark/`. Sie funktionieren in jedem git-Repository, lesen
  `shoalmark.toml`, wenn das Repository eine hat, und führen shoalmark nie aus. Beide Skills hier gehören zu dieser
  Gruppe.
- **Skills, die shoalmark brauchen,** kommen in ein zweites Plugin, das mit dem ersten solchen Skill entsteht. Jeder
  beginnt damit, die festgeschriebene Kopie von shoalmark im Repository zu finden und mit ihr `--version` und
  `--check` auszuführen. Einen solchen Skill gibt es noch nicht.

## Installieren und festschreiben

Noch ist kein Release getaggt, also steht `<tag>` unten für einen kommenden Release-Tag.

Die Manifeste tragen keine Versionsangabe, also bleibt eine Installation, die auf einen Tag festgeschrieben ist, auf
dem Commit dieses Tags
([Eine neue Version veröffentlichen](https://code.claude.com/docs/en/plugins/host-marketplace#release-a-new-version)).

**Claude Code:**

```text
/plugin marketplace add shoalmark/skills@<tag>
/plugin install shoalmark@shoalmark
```

**Codex:**

```text
codex plugin marketplace add shoalmark/skills@<tag>
```

Starte dann die ChatGPT-Desktop-App neu, öffne das Plugins Directory, wähle den Marketplace shoalmark und installiere
shoalmark daraus
([Eine eigene kuratierte Plugin-Liste bauen](https://developers.openai.com/plugins/build/plugins#build-your-own-curated-plugin-list)).

## Aufrufen

- **Claude Code:** `/shoalmark:find-drift` und `/shoalmark:prune-drift`.
- **Codex:** Tippe `$`, um einen Skill zu erwähnen: `$find-drift` und `$prune-drift`
  ([Wie ChatGPT und Codex Skills nutzen](https://developers.openai.com/codex/skills#how-codex-uses-skills)).

Der Bericht und das Gespräch folgen deiner Sprache: der des Boards von shoalmark, `lang` in
`<tracker folder>/brand/labels.yaml` des Repositorys, wo diese Datei eine gültige setzt; sonst der Sprache, in der du
schreibst. Die Abschnittsschlüssel des Berichts und seine IDs bleiben englisch. Die Skills lesen nur diese Datei;
darum kann die Sprache des Berichts von der des Boards abweichen, wo das Board `lang` aus der `brand/labels.yaml`
neben dem `shoalmark.py` der festgeschriebenen Kopie oder aus `~/.config/shoalmark/labels.yaml` nimmt.

## Die Skills ohne das Plugin kopieren

Kopiere beide Ordner, `plugins/shoalmark/skills/find-drift/` und `plugins/shoalmark/skills/prune-drift/`,
nebeneinander in einen Skills-Ordner: prune-drift verlinkt find-drift über einen relativen Pfad und führt sein
eigenes `prose_only.py` aus.

- **Codex:** `.agents/skills/` im Repository oder `$HOME/.agents/skills` in deinem Home-Ordner
  ([Wo Codex lokale Skills lädt](https://developers.openai.com/codex/skills#where-to-save-skills)).
- **Claude Code:** `.claude/skills/` für ein Projekt oder `~/.claude/skills/` für deine persönlichen Skills
  ([Wählen, wo Skills geladen werden](https://code.claude.com/docs/en/skills#choose-where-skills-load)).

Kopierte Skills tragen kein Plugin-Präfix, also führt Claude Code sie als `/find-drift` und `/prune-drift` aus.

## Mehr

- [SECURITY.md](SECURITY.md), um eine Schwachstelle zu melden, und [CHANGELOG.md](CHANGELOG.md) für Änderungen.
- Lizenziert unter Apache-2.0 oder MIT, nach deiner Wahl: [LICENSE-APACHE](LICENSE-APACHE),
  [LICENSE-MIT](LICENSE-MIT) und [NOTICE](NOTICE).

## Woher diese Skills kommen

Diese Skills kommen aus shoalmark. *Eine Werkbank für deine Agenten. Deine Entscheidungen belegt.* Für eine Person,
die das Sagen hat, und ihre Agentenflotte. Sieh, wo die Arbeit steht, was auf dein Wort wartet und was die nächste
Session aufgreift. Deine Agenten halten das in deinem Repository fest; deine Entscheidungen kommen als deine eigenen
Commits hinzu, neben den Belegen für die Arbeit.

- [Warum shoalmark?](https://shoalmark.tools/de/warum-shoalmark.html)
- [In zehn Minuten eingerichtet](https://shoalmark.tools/de/setup.html)
- [Das Repository von shoalmark](https://github.com/shoalmark/shoalmark)
- [Feedback senden](https://shoalmark.tools/feedback)
