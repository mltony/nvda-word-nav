# Sananavigointi #

* Tekijä: Tony Malykh
* Lataa [vakaa versio][1]
* Yhteensopivuus: NVDA 2019.3 ja uudemmat

WordNav NVDA add-on improves built-in navigation by word, as well as adds
extra word navigation commands with different definition for the word. It
also provides word selection commands.

Useimmat tekstieditorit tukevat Ctrl+Nuoli vasemmalle/oikealle -komentoja
sananavigointia varten. Sanan määritelmä kuitenkin muuttuu ohjelmasta
toiseen. Tämä pätee erityisesti nykyaikaisiin verkkopohjaisiin
tekstieditoreihin, kuten Monaco. NVDA:n tulee tietää sanan määritelmä
tietyssä ohjelmassa voidakseen puhua sanat oikein. Jos NVDA ei tiedä tarkkaa
määritelmää, joko sanat ohitetaan tai ne puhutaan useita kertoja. Lisäksi
jotkin verkkopohjaiset tekstieditorit sijoittavat kohdistimen sanan loppuun
alun sijaan, mikä tekee muokkaamisesta paljon vaikeampaa näkövammaisille
käyttäjille. Tämän ongelman torjumiseksi olen luonut parannettuja
sananavigointikomentoja, jotka ottavat sanamääritelmän Notepad++:sta eivätkä
luota ohjelman sanamäärittelyyn, vaan jäsentävät rivit sanoiksi NVDA:n
sisällä. Ctrl+Nuoli vasemmalle/oikealle -komentoa ei edes lähetetä
ohjelmalle, mikä varmistaa puheen johdonmukaisuuden.

## Sananavigointi ja sanojen määritelmät

Currently WordNav supports five definitions of the word, assigned to
different gestures:

* Vasen Ctrl+nuolet: Notepad++-määritelmä, joka käsittelee aakkosnumeerisia
  merkkejä ja vierekkäisiä välimerkkejä sanoina. Tämän pitäisi olla kätevin
  sanamääritelmä suurimmalle osalle käyttäjistä.
* `Oikea Ctrl+nuolet`: Tarkka sanamääritelmä jakaa `karavaaniTyyliset`
  merkkijonot sekä `alaviivalla_erotetut_merkkijonot` erillisiin osiin, mikä
  mahdollistaa kohdistimen siirtämisen pitkiin merkkijonoihin.
* `LeftControl+Windows+Arros`: Bulky word definition treats almost all
  punctuation symbols adjacent to text as part of a single word, therefore
  it would treat paths like `C:\directory\subdirectory\file.txt` as a single
  word.
* `Oikea Ctrl+Win+nuolinäppäimet`: Usean sanan määritelmä, joka ryhmittelee
  useita sanoja yhteen. Sanojen määrä on säädettävissä.
* Unassigned: custom regular expression word definition: allows user to
  define a custom regular expression for word boundaries.

Näppäinkomennot ovat mukautettavissa Sananavigoinnin asetuspaneelissa.

## Sanan valitseminen

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

## Huomautuksia

* Jos haluat käyttää Windows 10:n virtuaalityöpöytäominaisuutta, muista
  poistaa käytöstä Ctrl+Win+nuolinäppäin-pikanäppäimet joko Sananavigoinnin
  asetuspaneelissa tai NVDA:n Näppäinkomennot-valintaikkunassa.
* Compatibility with VSCode requires NVDA add-on IndentNav v2.0 or later to
  be installed. Additionally, VSCode extension [Accessibility for NVDA
  IndentNav](https://marketplace.visualstudio.com/items?itemName=TonyMalykh.nvda-indent-nav-accessibility)
  must be installed in VSCode.

##  Downloads

Please install the latest version from NVDA add-on store.

[[!tag dev stable]]

[1]: https://www.nvaccess.org/addonStore/legacy?file=wordnav
