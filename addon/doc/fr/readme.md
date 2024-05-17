# WordNav #

* Auteur : Tony Malykh
* Télécharger [version stable][1]
* Compatibilité NVDA : 2019.3 et ultérieurs

WordNav NVDA add-on improves built-in navigation by word, as well as adds
extra word navigation commands with different definition for the word. It
also provides word selection commands.

La plupart des éditeurs de texte prennent en charge les commandes
Contrôle+FlècheGauche/FlècheDroite pour la navigation dans les
mots. Cependant la définition du mot change d'un programme à l'autre. Cela
est particulièrement vrai des éditeurs de texte modernes basés sur le Web,
tels que Monaco. NVDA doit connaître la définition du mot dans un programme
donné afin de prononcer les mots correctement. Si NVDA ne connaît pas la
définition exacte, alors les mots seront ignorés ou prononcés plusieurs
fois. De plus, certains éditeurs de texte basés sur le Web positionnent le
curseur à la fin du mot, au lieu du début, ce qui rend l'édition beaucoup
plus difficile pour les utilisateurs malvoyants. Afin de lutter contre ce
problème, j'ai créé des commandes de navigation de mots améliorées, qui
prennent la définition de mot de Notepad ++ et ne reposent pas sur la
définition des mots du programme, mais analysent plutôt les lignes en mots
du côté de NVDA. Le geste Contrôle+FlècheGauche/FlècheDroite n'est même pas
envoyé au programme, assurant ainsi la cohérence du discours.

## Word navigation and word definitions

Currently WordNav supports five definitions of the word, assigned to
different gestures:

* « Contrôle gauche + flèches » : définition de Notepad++, qui traite les
  caractères alphanumériques comme des mots, et les signes de ponctuation
  adjacents sont également traités comme des mots. Cela devrait être la
  définition de mot la plus pratique pour la majorité des utilisateurs.
* `ContrôleDroit+Flèches` : la définition fine des mots divise
  `identifiantsCamelCase` et `identifiants_séparés_par_souligné` en parties
  séparées, permettant ainsi au curseur d'entrer dans de longs identifiants.
* `LeftControl+Windows+Arros`: Bulky word definition treats almost all
  punctuation symbols adjacent to text as part of a single word, therefore
  it would treat paths like `C:\directory\subdirectory\file.txt` as a single
  word.
* `ContrôleDroit+Windows+Flèches` : définition de plusieurs mots, qui
  regroupe plusieurs mots. Le nombre de mots est configurable.
* Unassigned: custom regular expression word definition: allows user to
  define a custom regular expression for word boundaries.

Les gestes peuvent être personnalisés dans le panneau des paramètres de
WordNav.

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

## Notes

* Si vous souhaitez utiliser la fonctionnalité de bureaux virtuels de
  Windows 10, n'oubliez pas de désactiver les raccourcis clavier
  Ctrl+Windows+Flèches soit dans le panneau Paramètres WordNav, soit dans le
  dialogue Gestes dde commande de NVDA.
* Compatibility with VSCode requires NVDA add-on IndentNav v2.0 or later to
  be installed. Additionally, VSCode extension [Accessibility for NVDA
  IndentNav](https://marketplace.visualstudio.com/items?itemName=TonyMalykh.nvda-indent-nav-accessibility)
  must be installed in VSCode.

##  Downloads

Please install the latest version from NVDA add-on store.

[[!tag dev stable]]

[1]: https://www.nvaccess.org/addonStore/legacy?file=wordnav
