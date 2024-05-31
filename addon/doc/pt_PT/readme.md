# WordNav #

* Autor: Tony Malykh
* Descarregar [versão estável][1]
* Compatibilidade com o NVDA: 2019.3 e posteriores

WordNav NVDA add-on improves built-in navigation by word, as well as adds
extra word navigation commands with different definition for the word. It
also provides word selection commands.

A maioria dos editores de texto suporta os comandos Control+Seta para a
esquerda/Seta para a direita para navegar nas palavras. No entanto, a
definição da palavra muda de um programa para outro. Isto é especialmente
verdade nos editores de texto modernos baseados na Web, como o Monaco. O
NVDA deve conhecer a definição da palavra num determinado programa para
poder dizer as palavras correctamente. Se o NVDA não souber a definição
exacta, então as palavras serão ignoradas ou pronunciadas várias vezes. Além
disso, alguns editores de texto baseados na Web posicionam o cursor no fim
da palavra, em vez de no início, tornando a edição muito mais difícil para
os utilizadores com deficiência visual. Para combater este problema, criei
comandos de navegação de palavras melhorados, que utilizam a definição de
palavras do Notepad++ e não dependem da definição de palavras do programa,
mas analisam as linhas em palavras do lado do NVDA. O gesto Control+Seta
para a esquerda/Seta para a direita nem sequer é enviado para o programa,
garantindo assim a consistência do discurso.

## Word navigation and word definitions

Currently WordNav supports five definitions of the word, assigned to
different gestures:

* `Controlo esquerdo+Setas`: Definição do Notepad++, que trata os caracteres
  alfanuméricos como palavras, e os sinais de pontuação adjacentes também
  são tratados como palavras. Esta deve ser a definição de palavra mais
  conveniente para a maioria dos utilizadores.
* `Controlo direito+Setas`: A definição de palavra fina divide
  `camelCaseIdentifiers` e `underscore_separated_identifiers` em partes
  separadas, permitindo assim que o cursor vá para identificadores longos.
* `LeftControl+Windows+Arros`: Bulky word definition treats almost all
  punctuation symbols adjacent to text as part of a single word, therefore
  it would treat paths like `C:\directory\subdirectory\file.txt` as a single
  word.
* `Controlo direito+Windows+Setas`: Definição multipalavra, que agrupa
  várias palavras. A quantidade de palavras é configurável.
* Unassigned: custom regular expression word definition: allows user to
  define a custom regular expression for word boundaries.

Os atalhos podem ser personalizados no painel de configurações do WordNav.

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

## Notas

* Se pretender utilizar a funcionalidade de ambientes de trabalho virtuais
  do Windows 10, lembre-se de desactivar os atalhos de teclado
  Control+Windows+Setas no painel de configurações do WordNav ou no diálogo
  definir comandos, no NVDA.
* Compatibility with VSCode requires NVDA add-on IndentNav v2.0 or later to
  be installed. Additionally, VSCode extension [Accessibility for NVDA
  IndentNav](https://marketplace.visualstudio.com/items?itemName=TonyMalykh.nvda-indent-nav-accessibility)
  must be installed in VSCode.

##  Downloads

Please install the latest version from NVDA add-on store.

[[!tag dev stable]]

[1]: https://www.nvaccess.org/addonStore/legacy?file=wordnav
