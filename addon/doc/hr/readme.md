# Kretanje po riječima (WordNav) #

* Autor: Tony Malykh
* Preuzmi [stabilnu verziju][1]
* NVDA kompatibilnost: 2019.3 i novije

WordNav NVDA add-on improves built-in navigation by word, as well as adds
extra word navigation commands with different definition for the word. It
also provides word selection commands.

Većina programa za obradu teksta podržava naredbe „kontrol+strelica
lijevo/strelica desno” za kretanje po riječima. Međutim, programi ne
definiraju riječi jednako. To se posebno odnosi na moderne programe za
obradu teksta na internetu, poput programa Monaco. NVDA mora znati
definiciju riječi u datom programu kako bi se riječi pravilno
izgovorile. Ako NVDA ne zna točnu definiciju, tada će se riječi preskočiti
ili izgovoriti više puta. Štoviše, neki internetski programi za obradu
teksta postavljaju pokazivač na kraj riječi, umjesto na početak, što
slabovidnim korisnicima znatno otežava obradu teksta. U tu sam svrhu izradio
poboljšane naredbe za kretanje po riječima koje preuzimaju definiciju riječi
iz programa Notepad++ te se ne oslanjaju definiciju riječi pojedinačnog
programa, već raščlanjuju retke u riječi na razini NVDA čitača. Gesta
„kontrol+strelica lijevo/strelica desno” se ne šalje programu, čime se
osigurava dosljednost govora.

## Word navigation and word definitions

Currently WordNav supports five definitions of the word, assigned to
different gestures:

* Lijevi kontrol+strelice: Notepad++ definicija. Tretira alfanumeričke
  znakove kao riječi, a susjedni interpunkcijski znakovi također se
  tretiraju kao riječi. Ovo bi trebala biti najpovoljnija definicija riječi
  za većinu korisnika.
* Desni kontrol+strelice: Prepoznavanje riječi. Rastavlja riječi na osnovi
  velikih slova u sastavljenim riječima kao i sastavljene riječi s podvlakom
  u zasebne dijelove, omogućujući tako pokazivaču da uđe u dugačke
  identifikatore.
* `LeftControl+Windows+Arros`: Bulky word definition treats almost all
  punctuation symbols adjacent to text as part of a single word, therefore
  it would treat paths like `C:\directory\subdirectory\file.txt` as a single
  word.
* Desni kontrol+Windows+strelice: Grupiranje riječi. Grupira više riječi
  zajedno. Količina riječi je podesiva.
* Unassigned: custom regular expression word definition: allows user to
  define a custom regular expression for word boundaries.

Geste se mogu prilagoditi u ploči postavaka dodatka „Kretanje po riječima”.

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

## Napomene

* Ako želiš koristiti funkciju virtualne radne površine u sustavu Windows
  10, deaktiviraj tipkovne prečace „kontrol+Windows+strelice” na ploči
  postavaka dodatka „Kretanje po riječima” ili u dijaloškom okviru „Ulazne
  geste” NVDA čitača.
* Compatibility with VSCode requires NVDA add-on IndentNav v2.0 or later to
  be installed. Additionally, VSCode extension [Accessibility for NVDA
  IndentNav](https://marketplace.visualstudio.com/items?itemName=TonyMalykh.nvda-indent-nav-accessibility)
  must be installed in VSCode.

##  Downloads

Please install the latest version from NVDA add-on store.

[[!tag dev stable]]

[1]: https://www.nvaccess.org/addonStore/legacy?file=wordnav
