# WordNav #

* Autor: Tony Malykh
* [Stabile Version herunterladen][1]
* NVDA-Kompatibilität: 2019.3 und neuer

Die NVDA-Erweiterung "WordNav" verbessert die integrierte Navigation nach
Wörtern und fügt zusätzliche Wortnavigationsbefehle mit unterschiedlichen
Definitionen für das Wort hinzu.

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

Bitte beachten Sie, dass ein Prototyp von WordNav früher Teil von [Tony's
enhancements](https://github.com/mltony/nvda-tonys-enhancements/) add-on
war. Bitte deinstallieren Sie es oder aktualisieren Sie auf [Tonys
Verbesserungen der letzten stabilen
Version](https://github.com/mltony/nvda-tonys-enhancements/releases/latest/download/tonysEnhancements.nvda-addon),
um Konflikte zu vermeiden.

Derzeit unterstützt WordNav vier Definitionen des Wortes, die verschiedenen
Tastenbefehlen zugeordnet sind:

* `Linke-Strg+Pfeiltasten`: Notepad++-Definition, die alphanumerische
  Zeichen als Wörter behandelt, und benachbarte Satzzeichen werden ebenfalls
  als Wörter behandelt. Dies sollte für die meisten Benutzer die bequemste
  Wortdefinition sein.
* `Rechte-Strg+Pfeiltasten`: Feine Wortdefinition teilt
  `camelCaseIdentifiers` und `underscore_separated_identifiers` in separate
  Teile auf, so dass der Cursor in lange Bezeichner gehen kann.
* `Linke-Strg+Windows+Pfeiltasten`: Bei der Definition von sperrigen Wörtern
  werden fast alle Satzzeichen, die an Text angrenzen, als Teil eines
  einzigen Worts behandelt, so dass Pfade wie
  "C:\Verzeichnis\Unterverzeichnis\Datei.txt" als ein einziges Wort
  behandelt werden würden.
* `Rechte-Strg+Windows+Pfeiltasten`: Mehrwortdefinition, die mehrere Wörter
  zusammenfasst. Die Anzahl der Wörter ist konfigurierbar.

Die Tastenbefehle können in den Einstellungen von WordNav angepasst werden.

## Anmerkungen

* Zur Zeit verändert WordNav nicht die Tastenbefehle
  "Strg+Umschalt+Pfeiltaste nach links/rechts", um Wörter auszuwählen, da
  die Implementierung solcher Befehle wesentlich komplizierter ist.
* Wenn Sie die Funktion der virtuellen Desktops von Windows 10 nutzen
  möchten, denken Sie bitte daran, die Tastenkombinationen
  Strg+Windows+Pfeiltasten entweder in den Einstellungen von WordNav oder im
  Dialogfeld für die Tastenbefehle zu deaktivieren.
* WordNav funktioniert in VS Code nicht zuverlässig, da VSCode aufgrund
  seiner internen Optimierungen nur wenige Zeilen des Dateiinhalts auf
  einmal darstellt, die sich dynamisch ändern, was gelegentlich den
  WordNav-Algorithmus stört.

[[!tag dev stable]]

[1]: https://www.nvaccess.org/addonStore/legacy?file=wordnav
