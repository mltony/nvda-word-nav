# Kelime Dolaşımı #

* Yazar: Tony Malykh
* [kararlı sürümü][1] indir
* NVDA 2019.3 veya sonraki bir sürümü gerektirir

Kelime Dolaşımı NVDA eklentisi, NVDA'nın kelime dolaşım özelliğini
iyileştirir ve farklı kelime tanımlarına farklı gezinme komutları ekler.

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

Önemli: Kelime Dolaşımı eklentisinin ilk sürümü daha önce [Tony
geliştirmeleri](https://github.com/mltony/nvda-tonys-enhancements/)
eklentisinin bir parçası olduğunu unutmayın. Çakışmaları önlemek için lütfen
eski eklentiy kaldırın veya [Tony geliştirmeleri eklentisinin son kararlı
sürümüne](https://github.com/mltony/nvda-tonys-enhancements/releases/latest/download/tonysEnhancements.nvda-addon)
yükseltin.

Şu anda Kelime Dolaşımı, kelimenin farklı hareketlere atanmış dört tanımını
desteklemektedir:

* "SolKontrol+Ok tuşları": Alfanümerik karakterleri ve bitişik noktalama
  işaretleri de kelime olarak tanımlayan Notepad++ tanımı. Bu çoğu
  kullanıcının kullandığı genel kelime tanımıdır.
* "Sağ control+ ok tuşları": CamelCase tanımlayıcısının kullanıldığı veya
  alt çizgi karakteriyle ayrılan cümlecikleri bölünmesinden oluşan
  tanımdır.
  CamelCase: olarak adlandırılan bir bileşik kelimenin ikinci kelimesinin
  büyük harfle başlaması.
* "SolControl+Windows+Ok tuşları": karmaşık kelime tanımı, metin le bitişik
  tüm noktalama işaretlerinin bulunduğu yapıları tek bir kelime gibi
  algılar. Örneğin c:\klasör\altklasör\dosya.txt yapısını tek bir kelime
  olarak algılar.
* "SağKontrol+Windows+Ok tuşları": Birkaç kelimeyi bir arada gruplayan çok
  kelimeli tanım. Kelime sayısı yapılandırılabilir.

Hareketler, Kelime Dolaşımı ayarları  iletişim kutusundan
özelleştirilebilir.

## Notlar

* Kelime Dolaşımı, kelime seçimi için kullanılan kontrol shift sağ sol ok
  tuşları kısayollarını kullanmaz.
* Windows 10'un sanal masaüstleri özelliğini kullanmak istiyorsanız, lütfen
  Kelime Dolaşımı Ayarları iletişim kutusundan veya NVDA Girdi hareketleri
  iletişim kutusunda Control+Windows+Oklar klavye kısayollarını devre dışı
  bırakmayı unutmayın.
* Kelime Dolaşımı, VSCode'da düzgün bir şekilde çalışmaz. Bunun sebebi,
  VSCode dahili optimizasyonları nedeniyle bir seferde yalnızca birkaç satır
  dosya içeriği sunar. Bu durum ise dinamik olarak değişir ve zaman zaman
  WordNav algoritmasıyla çakışabilir.

[[!tag dev stable]]

[1]: https://www.nvaccess.org/addonStore/legacy?file=wordnav
