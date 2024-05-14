# Kretanje po riječima (WordNav) #

* Autor: Tony Malykh
* Preuzmi [stabilnu verziju][1]
* NVDA kompatibilnost: 2019.3 i novije

NVDA dodatak „Kretanje po riječima” poboljšava ugrađeno kretanje po riječima
te dodaje dodatne naredbe za kretanje po riječima s različitim definicijama
za riječ.

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

Napomena: prototip dodatka „Kretanje po riječima” ranije je bio dio dodatka
[Tonijeva
poboljšanja](https://github.com/mltony/nvda-tonys-enhancements/).
Deinstaliraj ga ili ga nadogradi na [najnoviju stabilnu
verziju](https://github.com/mltony/nvda-tonys-enhancements/releases/latest/download/tonysEnhancements.nvda-addon)
kako bi se izbjegli problemi.

Dodatak „Kretanje po riječima” trenutačno podržava četiri definicije za
riječ, koje su dodijeljene različitim gestama:

* Lijevi kontrol+strelice: Notepad++ definicija. Tretira alfanumeričke
  znakove kao riječi, a susjedni interpunkcijski znakovi također se
  tretiraju kao riječi. Ovo bi trebala biti najpovoljnija definicija riječi
  za većinu korisnika.
* Desni kontrol+strelice: Prepoznavanje riječi. Rastavlja riječi na osnovi
  velikih slova u sastavljenim riječima kao i sastavljene riječi s podvlakom
  u zasebne dijelove, omogućujući tako pokazivaču da uđe u dugačke
  identifikatore.
* Lijevi kontrol+Windows+strelice: Sastavljanje riječi u cjelinu. Tretira
  gotovo sve interpunkcijske znakove uz tekst kao dio jedne riječi, stoga bi
  staze poput `C:\direktorij\poddirektorij\datoteka.txt` tretirala kao jednu
  riječ.
* Desni kontrol+Windows+strelice: Grupiranje riječi. Grupira više riječi
  zajedno. Količina riječi je podesiva.

Geste se mogu prilagoditi u ploči postavaka dodatka „Kretanje po riječima”.

## Napomene

* Dodatak „Kretanje po riječima” trenutačno ne mijenja geste
  „Kontrol+šift+strelica lijevo/strelica desno” za biranje riječi, jer je
  implementacija takvih naredbi znatno složenija.
* Ako želiš koristiti funkciju virtualne radne površine u sustavu Windows
  10, deaktiviraj tipkovne prečace „kontrol+Windows+strelice” na ploči
  postavaka dodatka „Kretanje po riječima” ili u dijaloškom okviru „Ulazne
  geste” NVDA čitača.
* Dodatak „Kretanje po riječima” ne radi pouzdano u VSCodeu, jer zbog
  interne optimizacije, VSCode istovremeno predstavlja samo nekoliko redaka
  sadržaja datoteke koji se dinamički mijenjaju, a to povremeno ometa
  algoritam dodatka „Kretanje po riječima”.

[[!tag dev stable]]

[1]: https://www.nvaccess.org/addonStore/legacy?file=wordnav
