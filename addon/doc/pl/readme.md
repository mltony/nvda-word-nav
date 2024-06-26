# WordNav #

* Autor: Tony Malykh
* Pobierz [Wersja stabilna][1]
* Zgodność z NVDA: 2019.3 i nowsze

WordNav NVDA add-on improves built-in navigation by word, as well as adds
extra word navigation commands with different definition for the word. It
also provides word selection commands.

Większość edytorów tekstu obsługuje polecenia Control+LeftArrow/RightArrow
do nawigacji po słowach. Jednak definicja słowa zmienia się z jednego
programu na drugi. Dotyczy to zwłaszcza nowoczesnych internetowych edytorów
tekstu, takich jak Monako. NVDA powinna znać definicję słowa w danym
programie, aby poprawnie wypowiadać słowa. Jeśli NVDA nie zna dokładnej
definicji, to albo słowa zostaną pominięte, albo wymawiane wiele razy. Co
więcej, niektóre internetowe edytory tekstu umieszczają kursor na końcu
słowa, zamiast na początku, co znacznie utrudnia edycję użytkownikom
niedowidzącym. Aby zwalczyć ten problem, stworzyłem ulepszone polecenia
nawigacji po słowach, które pobierają definicję słowa z Notepad ++ i nie
opierają się na definicji słów programu, ale raczej analizują linie na słowa
po stronie NVDA. Gest Control+LeftArrow/RightArrow nie jest nawet wysyłany
do programu, zapewniając w ten sposób spójność mowy.

## Word navigation and word definitions

Currently WordNav supports five definitions of the word, assigned to
different gestures:

* "Lewy Control + Strzałki": Definicja Notepad ++, która traktuje znaki
  alfanumeryczne jako słowa, a sąsiednie znaki interpunkcyjne są również
  traktowane jako słowa. Powinna to być najwygodniejsza definicja słowa dla
  większości użytkowników.
* "RightControl+Arrows": Definicja precyzyjnego słowa dzieli
  "camelCaseIdentifiers" i "underscore_separated_identifiers" na oddzielne
  części, umożliwiając w ten sposób kursorowi przejście do długich
  identyfikatorów.
* `LeftControl+Windows+Arros`: Bulky word definition treats almost all
  punctuation symbols adjacent to text as part of a single word, therefore
  it would treat paths like `C:\directory\subdirectory\file.txt` as a single
  word.
* "RightControl+Windows+Arros": definicja wielowyrazowa, która grupuje kilka
  słów razem. Ilość słów jest konfigurowalna.
* Unassigned: custom regular expression word definition: allows user to
  define a custom regular expression for word boundaries.

Gesty można dostosować w panelu ustawień WordNav.

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

## Notatki

* Jeśli chcesz korzystać z funkcji wirtualnych pulpitów systemu Windows 10,
  pamiętaj, aby wyłączyć skróty klawiaturowe Control + Windows + Strzałki w
  panelu Ustawienia WordNav lub w oknie dialogowym Gesty wejściowe NVDA.
* Compatibility with VSCode requires NVDA add-on IndentNav v2.0 or later to
  be installed. Additionally, VSCode extension [Accessibility for NVDA
  IndentNav](https://marketplace.visualstudio.com/items?itemName=TonyMalykh.nvda-indent-nav-accessibility)
  must be installed in VSCode.

##  Downloads

Please install the latest version from NVDA add-on store.

[[!tag dev stable]]

[1]: https://www.nvaccess.org/addonStore/legacy?file=wordnav
