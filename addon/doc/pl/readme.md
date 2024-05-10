# WordNav #

* Autor: Tony Malykh
* Pobierz [Wersja stabilna][1]
* Zgodność z NVDA: 2019.3 i nowsze

Dodatek WordNav NVDA poprawia wbudowaną nawigację po słowie, a także dodaje
dodatkowe polecenia nawigacji słownej z inną definicją słowa.

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

Należy pamiętać, że prototyp WordNav był wcześniej częścią dodatku [Tony's
enhancements]
(https://github.com/mltony/nvda-tonys-enhancements/). Odinstaluj go lub
uaktualnij do [Najnowsza stabilna wersja ulepszeń Tony'ego]
(https://github.com/mltony/nvda-tonys-enhancements/releases/latest/download/tonysEnhancements.nvda-addon),
aby uniknąć konfliktów.

Obecnie WordNav obsługuje cztery definicje słowa, przypisane do różnych
gestów:

* "Lewy Control + Strzałki": Definicja Notepad ++, która traktuje znaki
  alfanumeryczne jako słowa, a sąsiednie znaki interpunkcyjne są również
  traktowane jako słowa. Powinna to być najwygodniejsza definicja słowa dla
  większości użytkowników.
* "RightControl+Arrows": Definicja precyzyjnego słowa dzieli
  "camelCaseIdentifiers" i "underscore_separated_identifiers" na oddzielne
  części, umożliwiając w ten sposób kursorowi przejście do długich
  identyfikatorów.
* "LeftControl+ Windows+Arrows": Nieporęczna definicja słów traktuje prawie
  wszystkie symbole interpunkcyjne sąsiadujące z tekstem jako część jednego
  słowa, dlatego traktowałaby ścieżki takie jak
  "C:\directory\subdirectory\file.txt" jako pojedyncze słowo.
* "RightControl+Windows+Arros": definicja wielowyrazowa, która grupuje kilka
  słów razem. Ilość słów jest konfigurowalna.

Gesty można dostosować w panelu ustawień WordNav.

## Notatki

* W tej chwili WordNav nie modyfikuje gestów "Control + Shift + LeftArrow /
  RightArrow" do wybierania słów, ponieważ implementacja takich poleceń jest
  znacznie bardziej skomplikowana.
* Jeśli chcesz korzystać z funkcji wirtualnych pulpitów systemu Windows 10,
  pamiętaj, aby wyłączyć skróty klawiaturowe Control + Windows + Strzałki w
  panelu Ustawienia WordNav lub w oknie dialogowym Gesty wejściowe NVDA.
* WordNav nie działa niezawodnie w VSCode, ponieważ ze względu na wewnętrzne
  optymalizacje VSCode prezentuje tylko kilka linii zawartości pliku na raz,
  które zmieniają się dynamicznie, a to czasami zakłóca algorytm WordNav.

[[!tag dev stable]]

[1]: https://www.nvaccess.org/addonStore/legacy?file=wordnav
