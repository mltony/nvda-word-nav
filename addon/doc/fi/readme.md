# Sananavigointi #

* Tekijä: Tony Malykh
* Lataa [vakaa versio][1]
* Yhteensopivuus: NVDA 2019.3 ja uudemmat

Sananavigointi-lisäosa parantaa sisäänrakennettua sananavigointia sekä lisää
ylimääräisiä komentoja, joilla voi siirtyä eri tavalla määriteltyjen sanojen
välillä. Lisäosassa on myös sananvalintakomentoja.

Useimmat tekstieditorit tukevat Ctrl+Nuoli vasemmalle/oikealle -komentoja
sananavigointia varten. Sanan määritelmä kuitenkin muuttuu ohjelmasta
toiseen. Tämä pätee erityisesti nykyaikaisiin verkkopohjaisiin
tekstieditoreihin, kuten Monaco. NVDA:n tulee tietää sanan määritelmä
tietyssä ohjelmassa voidakseen puhua sanat oikein. Jos NVDA ei tiedä tarkkaa
määritelmää, sanat joko ohitetaan tai ne puhutaan useita kertoja. Lisäksi
jotkin verkkopohjaiset tekstieditorit sijoittavat kohdistimen sanan loppuun
alun sijaan, mikä tekee muokkaamisesta paljon vaikeampaa näkövammaisille
käyttäjille. Tämän ongelman torjumiseksi on luotu parannettuja
sananavigointikomentoja, jotka ottavat sanamääritelmän Notepad++:sta eivätkä
luota ohjelman sanamäärittelyyn vaan jäsentävät rivit sanoiksi NVDA:n
sisällä. Ctrl+Nuoli vasemmalle/oikealle -komentoa ei edes lähetetä
ohjelmalle, mikä varmistaa puheen johdonmukaisuuden.

## Sananavigointi ja sanojen määritelmät

Sananavigointi-lisäosa tukee tällä hetkellä viittä sanamääritelmää, joille
on määritetty eri näppäinkomennot:

* Vasen Ctrl+nuolet: Notepad++-määritelmä, joka käsittelee aakkosnumeerisia
  merkkejä ja vierekkäisiä välimerkkejä sanoina. Tämän pitäisi olla kätevin
  sanamääritelmä suurimmalle osalle käyttäjistä.
* `Oikea Ctrl+Nuolet`: Tarkka sanamääritelmä jakaa `karavaaniTyyliset`
  merkkijonot sekä `alaviivalla_erotetut_merkkijonot` erillisiksi osiksi,
  mikä mahdollistaa kohdistimen siirtämisen pitkiin merkkijonoihin.
* `Vasen Ctrl+Windows+Nuolet`: Laaja sanamäärittely käsittelee lähes kaikkia
  tekstin perässä olevia välimerkkejä osana yhtä sanaa, joten se käsittelee
  polut, kuten `C:\hakemisto\alihakemisto\tiedosto.txt` yhtenä sanana.
* `Oikea Ctrl+Windows+Nuolet`: Monisanamääritelmä, joka ryhmittelee useita
  sanoja yhteen. Sanojen määrä on muutettavissa.
* Ei määritetty: Mukautetun sääntölausekkeen sanamääritelmällä käyttäjä voi
  määritellä sanan rajat mukautetun sääntölausekkeen avulla.

Näppäinkomennot ovat mukautettavissa Sananavigoinnin asetuspaneelissa.

## Sanan valitseminen

Sananvalintaa tuetaan lisäosan versiosta 2.0 lähtien. Valitse sanoja
lisäämällä mihin tahansa sananavigointikomentoon
`Vaihto`-muokkausnäppäin. Sananvalintaa varten on myös yksi lisäkomento:

* `Ctrl+Vaihto+Laskinnäppäimistön 1` ja
  `Ctrl+Windows+Vaihto+Laskinnäppäimistön 1` valitsevat sanan oikealta
  samalla tavalla kuin vastaavat `Oikea nuoli` -komennot, mutta ne
  sisällyttävät valintaan myös loppuvälilyönnit.

Huomioithan kuitenkin, että tällä hetkellä käytössä olevissa
saavutettavuusrajapinnoissa on useita sananvalintaan liittyviä
ongelmia. Tutustu seuraavaan luetteloon ongelmista ja niiden kiertotavoista:

* UIA-sovellukset (esim. Muistio, Visual Studio ja Microsoft Word) eivät tue
  kohdistimen siirtämistä valinnan alkuun. Näissä sovelluksissa kohdistimen
  sijainti tallennetaan Sananavigoinnin puolella. Haittavaikutuksena
  sananavigointikomennot eivät välttämättä toimi saumattomasti rivin- ja
  kappaleenvalintakomentojen kanssa (`Vaihto+Ylä/alanuoli`,
  `Ctrl+Vaihto+Ylä/alanuoli`), ja tulokset voivat olla
  ennakoimattomia. Käytännön syistä merkinvalintakomennot
  (`Vaihto+Vasen/oikea nuoli`) on päivitetty Sananavigoinnissa
  UIA-sovelluksia varten ja niiden pitäisi toimia hyvin.
* Yksiriviset Windowsin perusmuokkaussäätimet eivät myöskään salli
  kohdistimen siirtämistä valinnan eteen, joten aiempi huomautus pätee myös
  niihin. Tämä vaikuttaa NVDA:ssa kaikkiin yksirivisiin muokkausruutuihin.
* IAccessible2 ei tarjoa tapaa asettaa valintaa, joka ulottuu useisiin
  kappaleisiin. Tälle ongelmalle ei ole tunnettua kiertotapaa. Tämä
  vaikuttaa Chromessa ja Firefoxissa rikastekstiä sisältäviin monirivisiin
  muokkausruutuihin, kuten sähköpostin kirjoitusalueeseen GMailissa ja
  viestinkirjoitusikkunaan Thunderbirdissä.
* Notepad++:ssa valinnanpäivitysilmoitukset tulevat kohtuuttoman
  hitaasti. Ongelman kiertämiseksi Sananavigointi ilmoittaa valinnasta
  NVDA:n puolella sananvalintakomentojen yhteydessä ja hiljentää
  myöhästyneet ilmoitukset seuraavan 0,5 sekunnin ajaksi. Tämän seurauksena,
  jos painat sananvalintakomentoa ja sen jälkeen nopeasti toista komentoa
  (esim. merkin valitsemiseksi), saatat jäädä ilman valinnan ilmoitusta
  jälkimmäisestä komennosta, jos se tuli 0,5 sekunnin sisällä edellisestä
  sananvalintakäskystä.
* NVDA tunnistaa virheellisesti kohdistimen sijainnin TOM-rajapintaa
  tukevissa monirivisissä muokkausruuduissa, kun tekstiä on valittuna. Tämä
  on korjattu nvaccess/nvda#16455:ssa, joka on suunniteltu sisällytettäväksi
  NVDA:n 2024.2-versioon. Ennen tätä julkaisua sananvalintakomennot eivät
  toimi oikein TOM-muokkausruuduissa, kuten NVDA:n lokintarkastelussa.

## Huomautuksia

* Jos haluat käyttää Windows 10:n virtuaalityöpöytäominaisuutta, muista
  poistaa käytöstä Ctrl+Windows+Nuoli-pikanäppäimet joko Sananavigoinnin
  asetuspaneelissa tai NVDA:n Näppäinkomennot-valintaikkunassa.
* Yhteensopivuus VSCoden kanssa edellyttää, että
  Sisennysnavigointi-lisäosasta on asennettu versio 2.0 tai uudempi. Lisäksi
  VSCodeen on asennettava [Accessibility for NVDA
  IndentNav](https://marketplace.visualstudio.com/items?itemName=TonyMalykh.nvda-indent-nav-accessibility)
  -laajennus.

##  Lataukset

Asenna uusin versio NVDA:n lisäosakaupasta.

[[!tag dev stable]]

[1]: https://www.nvaccess.org/addonStore/legacy?file=wordnav
