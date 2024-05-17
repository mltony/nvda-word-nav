# WordNav #

* Autor: Tony Malykh
* [Stabile Version herunterladen][1]
* NVDA-Kompatibilität: 2019.3 und neuer

WordNav NVDA add-on improves built-in navigation by word, as well as adds
extra word navigation commands with different definition for the word. It
also provides word selection commands.

Die meisten Texteditoren unterstützen die Befehle Strg+Pfeiltaste nach
links/rechts für die Wort-Navigation. Die Definition des Wortes ändert sich
jedoch von einem Programm zum anderen. Dies gilt insbesondere für moderne
webbasierte Text-Editoren wie Monaco. NVDA sollte die Definition des Wortes
im jeweiligen Programm kennen, um die Wörter korrekt aussprechen zu
können. Wenn NVDA die genaue Definition nicht kennt, werden Wörter entweder
übersprungen oder mehrfach ausgesprochen. Darüber hinaus positionieren
einige webbasierte Text-Editoren den Cursor am Ende des Wortes und nicht am
Anfang, was die Bearbeitung für sehbehinderte Benutzer erheblich
erschwert. Um dieses Problem zu bekämpfen, habe ich verbesserte
Wort-Navigationsbefehle entwickelt, die die Wortdefinition von Notepad++
übernehmen und sich nicht auf die Wortdefinition des Programms verlassen,
sondern die Zeilen auf der Seite von NVDA in Wörter zerlegen. Der
Tastenbefehl Strg+Pfeiltaste nach links/rechts wird nicht einmal an das
Programm gesendet, so dass die Konsistenz der Sprache gewährleistet ist.

## Word navigation and word definitions

Currently WordNav supports five definitions of the word, assigned to
different gestures:

* `Linke-Strg+Pfeiltasten`: Notepad++-Definition, die alphanumerische
  Zeichen als Wörter behandelt, und benachbarte Satzzeichen werden ebenfalls
  als Wörter behandelt. Dies sollte für die meisten Benutzer die bequemste
  Wortdefinition sein.
* `Rechte-Strg+Pfeiltasten`: Feine Wortdefinition teilt
  `camelCaseIdentifiers` und `underscore_separated_identifiers` in separate
  Teile auf, so dass der Cursor in lange Bezeichner gehen kann.
* `LeftControl+Windows+Arros`: Bulky word definition treats almost all
  punctuation symbols adjacent to text as part of a single word, therefore
  it would treat paths like `C:\directory\subdirectory\file.txt` as a single
  word.
* `Rechte-Strg+Windows+Pfeiltasten`: Mehrwortdefinition, die mehrere Wörter
  zusammenfasst. Die Anzahl der Wörter ist konfigurierbar.
* Unassigned: custom regular expression word definition: allows user to
  define a custom regular expression for word boundaries.

Die Tastenbefehle können in den Einstellungen von WordNav angepasst werden.

## Word selection

Word selection is supported starting with WordNav v2.0. Just add `shift`
modifier to any word navigation gestures to select words. There is also one
extra gesture for word selection:

* `control+shift+numpad1` and `control+windows+shift+numpad1` select word to
  the right similar to their `rightArrow` counterparts, but they also
  include trailing spaces into selection.

Please note, however, that currently used accessibility APIs have multiple
issues related to word selection. Please get yourself familiar with the
following list of issues and workarounds:

* UIA applications (e.g. Notepad, Visual Studio, Microsoft Word) don't
  support setting caret at the beginning of selection. In those applications
  caret location is stored on WordNav side. As an adverse side effect, word
  navigation commands might not play well with line and paragraph selection
  commands (`shift+up/downArrow`, `control+shift+up/downArrow`) and results
  might be unpredictable. For convenience, character selection commands
  (`shift+left/rightArrow`) have been updated in WordNav for UIA
  applications and should work well.
* Basic single line Windows edit controls also don't allow to set the caret
  in front of selection, so the previous point also applies to them. This
  affects all single line edit boxes within NVDA.
* IAccessible2 doesn't provide a way to set selection spanning across
  multiple paragraphs. There is no known workaround for this issue. This
  affects rich multiline edit boxes in Chrome and Firefox, such as compose
  email text area in GMail and compose email window in Thunderbird.
* In notepad++ selection update messages come unreasonably slow. As a
  workaround, WordNav announces selection on NVDA side for word selection
  commands and silences late notifications for the following 0.5 seconds. As
  a result, if you press word selection command followed by another
  (e.g. character) selection command in quick succession, you might miss
  selection notification for the latter one if it came within 0.5 seconds
  from the last word selection command.
* In multiline edit boxes supporting TOM interface NVDA incorrectly
  identifies cursor location when selection is present. This has been fixed
  in nvaccess/nvda#16455, which is scheduled to be included in NVDA v2024.2
  release. Before that release word selection commands won't work correctly
  in TOM edit boxes, such as NVDA log viewer.

## Anmerkungen

* Wenn Sie die Funktion der virtuellen Desktops von Windows 10 nutzen
  möchten, denken Sie bitte daran, die Tastenkombinationen
  Strg+Windows+Pfeiltasten entweder in den Einstellungen von WordNav oder im
  Dialogfeld für die Tastenbefehle zu deaktivieren.
* Compatibility with VSCode requires NVDA add-on IndentNav v2.0 or later to
  be installed. Additionally, VSCode extension [Accessibility for NVDA
  IndentNav](https://marketplace.visualstudio.com/items?itemName=TonyMalykh.nvda-indent-nav-accessibility)
  must be installed in VSCode.

##  Downloads

Please install the latest version from NVDA add-on store.

[[!tag dev stable]]

[1]: https://www.nvaccess.org/addonStore/legacy?file=wordnav
