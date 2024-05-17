# Kelime Dolaşımı #

* Yazar: Tony Malykh
* [kararlı sürümü][1] indir
* NVDA 2019.3 veya sonraki bir sürümü gerektirir

Kelime Dolaşımı NVDA eklentisi, yerleşik kelime dolaşımını geliştirmenin
yanı sıra, kelimenin farklı tanımıyla ekstra kelime dolaşımı komutları da
ekler. Ayrıca kelime seçme komutları da sağlar.

Çoğu metin düzenleyicisi, kelimeler arasında dolaşmak için Control+Sol
OK/Sağ Ok tuşlarını destekler. Ancak kelimenin ne olarak tanımlandığı bir
programdan diğerine değişiklik gösterebilir. Bu durum özellikle Monako gibi
modern web tabanlı metin düzenleyicileri için geçerlidir. NVDA, kelimeleri
doğru tanımlayabilmesi için verilen programdaki kelimenin tanımını
bilmelidir. NVDA tam tanımı bilmiyorsa, ya kelimeleri atlar, ya da
kelimeleri birçok kez tekrar eder. Ayrıca, bazı web tabanlı metin
düzenleyicileri, imleci kelimenin başına değil sonuna yerleştirir ve bu da
görme engelli kullanıcılar için düzenlemeyi çok daha zor hale getirir. Bu
sorunlara çözüm getirebilmek için kelimenin  tanımını Notepad++'dan alan ve
odaklanan programın kelime tanımını yoksayan, bunun yerine NVDA tarafından
satırları sözcüklere ayrıştıran gelişmiş kelime dolaşım komutları
oluşturdum. Control +sağ ve Sol ok tuşları kullanılan programa gönderilmez
ve böylece konuşma tutarlılığı sağlanır.

## Kelime dolaşımı ve kelime tanımları

Şu anda Kelime Dolaşımı, kelimenin farklı hareketlere atanmış beş tanımını
desteklemektedir:

* "SolKontrol+Ok tuşları": Alfanümerik karakterleri ve bitişik noktalama
  işaretleri de kelime olarak tanımlayan Notepad++ tanımı. Bu çoğu
  kullanıcının kullandığı genel kelime tanımıdır.
* "Sağ control+ ok tuşları": CamelCase tanımlayıcısının kullanıldığı veya
  alt çizgi karakteriyle ayrılan cümlecikleri bölünmesinden oluşan
  tanımdır.
  CamelCase: olarak adlandırılan bir bileşik kelimenin ikinci kelimesinin
  büyük harfle başlaması.
* `SolKontrol+Windows+ok tuşları`: Hacimli kelime tanımı, metne bitişik
  hemen hemen tüm noktalama işaretlerini tek bir kelimenin parçası olarak
  ele alır, bu nedenle yolları tek bir kelime gibi ele
  alır. C:\directory\subdirectory\\file.txt.
* "SağKontrol+Windows+Ok tuşları": Birkaç kelimeyi bir arada gruplayan çok
  kelimeli tanım. Kelime sayısı yapılandırılabilir.
* Atanmamış: özel normal ifade kelime tanımı: kullanıcının kelime sınırları
  için özel bir normal ifade tanımlamasına olanak tanır.

Hareketler, Kelime Dolaşımı ayarları  iletişim kutusundan
özelleştirilebilir.

## Kelime seçimi

Kelime seçimi, Kelime Dolaşımı v2.0'dan itibaren
desteklenmektedir. Kelimeleri seçmek için herhangi bir kelime dolaşım
hareketine "shift" değiştiricisini eklemeniz yeterlidir. Kelime seçimi için
ayrıca ekstra bir hareket daha vardır:

* `CTRL+shift+sayısal tuş takımı 1` ve `CTRL+windows+shift+sayısal tuş
  takımı 1`, `sağ ok` karşılıklarına benzer şekilde sağa doğru kelime seçer,
  ancak seçime sondaki boşlukları da eklerler.

Ancak, şu anda kullanılan erişilebilirlik API'lerinin kelime seçimiyle
ilgili birden fazla sorunu olduğunu lütfen unutmayın. Lütfen aşağıdaki
sorunlar ve geçici çözümler listesini öğrenin:

* UIA uygulamaları (örneğin Notepad, Visual Studio, Microsoft Word) seçimin
  başında işaret ayarlamayı desteklemez. Bu uygulamalarda caret konumu
  Kelime Dolaşımı tarafında saklanır. Olumsuz bir yan etki olarak, kelime
  dolaşımı komutları satır ve paragraf seçme komutlarıyla
  (`shift+yukarı/aşağı Ok`, `CTRL+shift+yukarı/aşağı Ok`) iyi çalışmayabilir
  ve sonuçlar tahmin edilemez olabilir. Kolaylık sağlamak için, karakter
  seçim komutları (`shift+sol/sağ ok`) UIA uygulamaları için Kelime Dolaşımı
  eklentisinde güncellenmiştir ve iyi çalışması gerekir.
* Temel tek satırlı Windows düzenleme kontrolleri ayrıca düzeltme işaretinin
  seçimin önüne ayarlanmasına izin vermez, bu nedenle önceki nokta onlar
  için de geçerlidir. Bu, NVDA'daki tüm tek satırlı düzenleme kutularını
  etkiler.
* IAccessible2, seçimin birden çok paragrafa yayılmasını ayarlamanın bir
  yolunu sağlamaz. Bu sorun için bilinen bir geçici çözüm yoktur. Bu,
  GMail'deki e-posta metni oluşturma alanı ve Thunderbird'deki e-posta
  oluşturma penceresi gibi Chrome ve Firefox'taki zengin çok satırlı
  düzenleme kutularını etkiler.
* Notepad++ seçiminde güncelleme mesajları makul olmayan bir şekilde yavaş
  geliyor. Geçici bir çözüm olarak Kelime Dolaşımı, NVDA tarafında kelime
  seçimi komutları için seçimi duyurur ve sonraki 0,5 saniye boyunca geç
  bildirimleri susturur. Sonuç olarak, kelime seçme komutuna ve ardından
  hızlı bir şekilde art arda başka bir (örneğin karakter) seçim komutuna
  basarsanız, son kelime seçme komutundan 0,5 saniye sonra geldiyse
  sonuncuya ilişkin seçim bildirimini kaçırabilirsiniz.
* TOM arayüzünü destekleyen çok satırlı düzenleme kutularında NVDA, seçim
  mevcut olduğunda imleç konumunu yanlış tanımlıyor. Bu durum, NVDA v2024.2
  sürümüne dahil edilmesi planlanan nvaccess/nvda#16455'te düzeltildi. Bu
  sürümden önce, kelime seçimi komutları, NVDA günlük görüntüleyici gibi TOM
  düzenleme kutularında düzgün çalışmayacaktır.

## Notlar

* Windows 10'un sanal masaüstleri özelliğini kullanmak istiyorsanız, lütfen
  Kelime Dolaşımı Ayarları iletişim kutusundan veya NVDA Girdi hareketleri
  iletişim kutusunda Control+Windows+Oklar klavye kısayollarını devre dışı
  bırakmayı unutmayın.
* VSCode ile uyumluluk, NVDA eklentisi Girinti Dolaşımı v2.0 veya sonraki
  sürümlerinin kurulu olmasını gerektirir. Ayrıca, VSCode'a VSCode uzantısı
  [NVDA IndentNav için
  Erişilebilirlik](https://marketplace.visualstudio.com/items?itemName=TonyMalykh.nvda-indent-nav-accessibility)
  yüklenmelidir.

##  İndirin

Lütfen NVDA eklenti mağazasından en son sürümü yükleyin.

[[!tag dev stable]]

[1]: https://www.nvaccess.org/addonStore/legacy?file=wordnav
