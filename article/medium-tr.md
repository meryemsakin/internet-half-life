# İnternet Bir Şeyi Kaç Günde Unutuyor?

*Barbenheimer'dan Ever Given'a on altı olay, 176,4 milyon Wikipedia
görüntülenmesi ve 330 milyon parametreli bir modelin iki parametreli eğriyle
imtihanı.*

21 Temmuz 2023'te *Barbie* ve *Oppenheimer* aynı gün gösterime girdi. İki film
birlikte bir internet olayına dönüştü ve olayın bir adı oldu: Barbenheimer.

İngilizce Wikipedia'da Barbenheimer'ın yedi sayfalık takımyıldızı, sonraki 60 gün
boyunca sıradan günlerin toplam 41,1 milyon görüntülenme üzerine çıktı. Bunun
yalnızca yüzde 2,2'si “Barbenheimer” sayfasındaydı.

Fazladan dikkatin **yüzde 97,8'i başka yere gitti**: filmlere, oyunculara, gerçek
J. Robert Oppenheimer'a ve Manhattan Projesi'ne.

![Barbenheimer dikkat atlası](../figures/barbenheimer-atlas.png)

Projeye “İnternet bir şeyi kaç günde unutur?” sorusuyla başladım. İlk bulgu,
sorunun biraz yanlış olduğuydu.

**İnternet yalnızca unutmuyor. Önce dağılıyor.**

## Bir olay tek çizgi değil

Bir olayın internetteki ömrü genellikle kendi adıyla ölçülüyor. Filmin sayfası,
maçın sayfası, geminin adı. Oysa insanlar bir olayı duyunca yalnızca olayın ne
olduğunu okumuyor. Olayın açtığı kapılardan geçiyor.

Barbenheimer'dan Margot Robbie'ye, oradan *Barbie*'ye; Oppenheimer filminden
fizikçiye, oradan Manhattan Projesi'ne gidiyor. Bu yüzden her olayı tek zaman
serisi yerine küçük bir takımyıldız olarak tanımladım.

Katalogda on altı olay var:

- Barbenheimer
- *Straight Outta Compton*'ın vizyona girişi
- ChatGPT'nin halka açılması
- James Webb'in ilk tam renkli görüntüleri
- Ever Given'ın Süveyş Kanalı'nı kapatması
- 2022 Dünya Kupası finali
- Chandrayaan-3'ün Ay'a inişi
- İlk GTA VI fragmanı
- 2024 tam güneş tutulması
- *Inside Out 2*'nun vizyona girişi
- Paris 2024 açılış töreni
- *Deadpool & Wolverine*'in vizyona girişi
- 2024 ABD başkanlık seçimi
- Notre-Dame'ın yeniden açılışı
- Super Bowl LIX
- Papa Francis'in ölümü ve ardından gelen konklav

Son altısını sonradan ekledim. Nedenini yazının ilerleyen bölümünde
anlatacağım; kısaca, kataloğun tarih ekseninde tek yana yığılmış olması bir
soruyu sormamı engelliyordu.

Her olay için bir ana sayfa ve dört ila altı komşu sayfa seçtim. Wikimedia'nın
herkese açık Pageviews API'sinden günlük görüntülenmeleri aldım.

Sonuçta on altı takımyıldızda, olaydan sonraki 60 günde sıradan gün seviyesinin
üzerinde toplam **176,4 milyon görüntülenme** oluştu. Trafikle ağırlıklandırınca
bunun **yüzde 69,4'ü ana olay sayfalarının dışındaydı**.

Ağırlıklandırmanın kendisi de bir tercih ve sonucu değiştiriyor. Trafikle
ağırlıklandırınca yüzde 69,4; ortanca olayda ise yüzde 53,2. Dağılım yüzde
18,3 ile yüzde 97,8 arasında geziniyor. Yani dağılma kuralın kendisi, ama ne
kadar dağıldığı sabit değil ve büyük olaylar ortalamayı yukarı çekiyor.

![On altı olayda dikkatin ana sayfanın dışına taşan payı](../figures/catalog-spillover.png)

Bu sayı “internetin yüzde 69,4'ü şöyledir” demiyor. Olayları rastgele seçmedim;
hepsi görünür dikkat patlamaları yaratmış, elle seçilmiş örnekler. Sayfa
takımyıldızlarını da ben kurdum. Yüzde 69,4 bu kataloğun betimsel sonucu.

Ama tek örnekte görülen yüzde 79'luk taşmanın tesadüf olmadığını söylemeye
yetecek kadar tutarlı bir desen var: Dünya Kupası finalinde yüzde 97,4, Ever
Given'da yüzde 86,1, Paris 2024 açılışında yüzde 97,4, *Straight Outta
Compton*'da yüzde 79,0.

## “Sıradan gün” ve “yarı ömür” ne demek?

Bir sayfanın olaydan hemen önceki 28 gününün medyanını sıradan gün seviyesi
olarak aldım. Ortalama yerine medyan kullanmamın nedeni, olaydan önceki tek
günlük sıçramaların baseline'ı yukarı çekmesini önlemek.

Yeni açılmış veya daha önce hiç okunmamış bir sayfanın medyanı sıfır
olabiliyor. Sıfıra bölmemek için tabanı bir görüntülenmede sabitledim. Bu yüzden
yeni sayfalardaki “peak lift” çok büyük çıkabiliyor; atlasın dikey ekseni tam da
bu nedenle logaritmik.

Sonra olaydan sonraki zirvenin baseline üzerindeki kısmına *fazladan dikkat*
dedim. Seri bu fazlalığın yarısının altında üç gün üst üste kaldığında yarı
ömrüne ulaşmış sayılıyor. Üç gün şartı hafta içi/hafta sonu oynaklığını tek
başına “unutma” diye saymamak için var.

Barbenheimer ana sayfasının yarı ömrü üç gündü. *Barbie*, *Oppenheimer*, J.
Robert Oppenheimer ve Manhattan Projesi dört günde yarıya indi. Margot Robbie
sekiz gün sürdü.

Yani aynı dalgayla yükselen sayfalar aynı hızda sönmedi. Bir olayın adı
kaybolurken açtığı merak yaşamaya devam edebiliyor.

## TimesFM-3 hikâyeye nereden girdi?

Google Research, [TimesFM-3'ü 31 Ağustos
2026'da](https://www.research.google/blog/timesfm-3-a-zero-shot-foundation-model-for-multivariate-forecasting/)
yayımladı. Model 330 milyon parametreli; bir trilyondan fazla gerçek ve sentetik
zaman noktası üzerinde önceden eğitilmiş. Önceki TimesFM sürümlerinden farklı
olarak birden çok ilişkili seriyi birlikte tahmin etmek üzere eğitilmiş.

Bu yetenek atlas için doğal bir deney üretti:

> Olay gününü ve onu izleyen yedi günü gösterirsem, komşu sayfalar sonraki 30
> günü tahmin etmeye yardım ediyor mu?

Buradaki kesim noktası önemli: model olay gününden yedinci güne kadar sekiz
günlük olay-sonrası veri görüyor; tahmin sekizinci gün başlıyor. Bütün on altı
olayda aynı protokolü kullandım.

Her takımyıldızı beş şekilde tahmin ettim:

1. Bütün sayfaları birlikte gören TimesFM-3.
2. Her sayfayı bağımsız gören TimesFM-3.
3. Zirveden sonraki fazlalığa uydurulmuş iki parametreli üstel sönüm.
4. Aynı veriye uydurulmuş iki parametreli power-law sönüm.
5. Son haftayı tekrar eden seasonal-naive.

Sonuncusu gerekli ama zayıf bir korkuluk. Bir sıçramadan hemen sonra son haftayı
tekrarlamak, tepeyi geleceğe kopyalayıp duruyor. Bu yüzden asıl baseline'lar
sönüm eğrileri. “Dikkat azalıyor” diyorsam modelin aşması gereken ilk açıklama
da “dikkat basit bir eğriyle azalıyor” olmalı.

## 330 milyon parametre, iki parametreye karşı

On altı olayın ortanca WAPE sonuçları şöyle:

| Yöntem | Ortanca olay WAPE'si (düşük daha iyi) |
|---|---:|
| TimesFM-3, bütün sayfalar birlikte | **0,294** |
| TimesFM-3, her sayfa bağımsız | 0,332 |
| Üstel sönüm | 0,502 |
| Power-law sönüm | 0,467 |
| Geçen haftayı tekrar et | 2,902 |

Yalnızca bu tabloya bakarsak multivariate TimesFM kazanmış gibi görünüyor. On
altı olayı tek tek eşleştirince hikâye zayıflıyor.

Multivariate model on olayda daha iyi, altısında daha kötüydü. Multivariate eksi
univariate WAPE farkının ortancası **−0,008**: pratikte çok küçük. İki yönlü
exact sign-test sonucu **p=0,454**. Bu katalogla “komşu sayfalar tahmini
iyileştiriyor” diyemiyorum; farkı sıfırdan ayıramıyorum.

Aynı farkın **ortalaması** ise −0,755. Bu sayı kesin bir zafer gibi duruyor ve
değil: tamamı tek bir olaydan geliyor. Ever Given'da univariate TimesFM 12,43
WAPE verdi, multivariate 0,78. Kalan on beş olayın hepsi −0,451 ile +0,212
arasında. Burada ortalamayı raporlamak, bir modelin tek bir çöküşünü on altı
olaya yaymak olurdu.

O çöküşün kendisi yine de bir satırı hak ediyor, ama ortalamanın ima ettiği
satırı değil: komşu sayfalar doğruluğu güvenilir biçimde artırmadı; buna karşılık
univariate modun tamamen dağıldığı tek olayda birlikte bakan model dağılmadı.

![Her olay için multivariate eksi univariate WAPE](../figures/multivariate-delta-by-event.png)

Daha beklenmedik sonuç basit eğrilerden geldi. On altı olayın **altısında**,
üstel veya power-law eğrilerinden en az biri her iki TimesFM koşulunu da geçti.

*Straight Outta Compton* örneğinde power-law WAPE 0,234; multivariate TimesFM
0,248; univariate TimesFM 0,251 verdi. Foundation model burada iki parametreli
eğriye kaybetti.

Barbenheimer'da ise multivariate TimesFM 0,246 ile en iyiydi. Univariate 0,269,
üstel sönüm 0,411, power-law 0,475 verdi. Tek bir vitrini seçip genellemek yerine
bütün olayları yan yana koymanın farkı burada ortaya çıkıyor: model bazen ilişkili
serilerden gerçekten yararlanıyor, bazen basit sönüm yeterli oluyor, bazen de
iki TimesFM modu birbirinden ayrılmıyor.

![Modellerin on altı olaydaki WAPE dağılımı](../figures/forecast-model-comparison.png)

Bu, “TimesFM işe yaramıyor” sonucu değil. Ortanca WAPE'de iki TimesFM modu da
iki sönüm ailesinden daha iyi. Daha dar sonuç şu: modelin multivariate olması
her olayda ek tahmin değeri sağlamıyor ve alan bilgisi taşıyan basit baseline'ı
atlamak modeli olduğundan güçlü gösteriyor.

## Modele cevabı önceden söylemiş olabilir miyim?

Yukarıdaki tabloda TimesFM sönüm eğrilerini ortanca WAPE'de geçiyor. Bu sonucu
yazdıktan sonra [resmî model
kartını](https://huggingface.co/google/timesfm-3.0-pytorch/blob/main/README.md)
yeniden okudum ve eğitim verisi listesinde şu satıra takıldım:

> Wikipedia Pageviews, **cutoff Nov 2023**.

Google modelin Wikipedia görüntülenme verisini Kasım 2023'te kestiğini kendisi
yazmış. Bu, tahmin etmek zorunda olmadığım bir sınır demek. Bu tarihten önceki
olaylar eğitim korpusunda olabilir; sonrakiler olamaz.

Kataloğu ilk kurduğumda on olayın yedisi kesimden önceydi, yalnızca üçü
sonrasında. Üç olayla hiçbir şey ölçülemez. Bu yüzden altı olay daha ekledim,
hepsi Kasım 2023'ten sonra: Paris açılışı, *Deadpool & Wolverine*, ABD seçimi,
Notre-Dame, Super Bowl LIX, Papa Francis. Katalog yediye dokuz oldu.

Ham hatayı karşılaştırmak burada işe yaramaz. Kesim sonrası olaylar aynı zamanda
daha yeni ve Wikipedia trafiği bu modelle hiç ilgisi olmayan sebeplerle değişti.
Onun yerine, TimesFM'in hatasını **aynı olayda iki sönüm baseline'ından daha
düşük WAPE verene** böldüm. Bu, sonucu gördükten sonra daha iyi baseline'ı seçen
oracle-normalize edilmiş keşifsel bir karşılaştırma; nedensel test değil. İki
parametreli bir eğrinin eğitim korpusu yok ve hiçbir şey ezberlemiş olamaz.
Dönem gerçekten zorlaştıysa ikisi birden bozulacağı için oran ham hatadan daha
kararlı kalabilir.

| | olay | ortanca WAPE | TimesFM ÷ en iyi sönüm |
|---|---:|---:|---:|
| kesimden önce | 7 | 0,248 | **0,737** |
| kesimden sonra | 9 | 0,418 | **0,943** |

Görmüş olabileceği olaylarda TimesFM iki parametreli eğriyi yüzde 26 farkla
geçiyor. Göremeyeceği olaylarda fark yüzde 6'ya iniyor. Yön, kontaminasyonun
üreteceği yönün tam kendisi.

Ve anlamlı değil. 11.440 olası grup ayrımının tamamını deneyen exact iki yönlü
permütasyon testi **p=0,467** veriyor. On altı elle seçilmiş olay bu büyüklükte
bir etkiyi çözemiyor; kesim sonrası grup da yalnızca üç yıl genişliğinde.

Bu yüzden bunu bir bulgu diye sunmuyorum. Bir yön, ve testin koşulup gücünün
yetmediğinin kaydı. Yanıtlanabilir hale getirmenin en ucuz yolu kesim sonrası
tarafı büyütmek: her olay `catalog/events.json` içinde tek bir kayıt.

Buradaki asıl mesele şu: zaman serisi foundation modelleri “zero-shot” diye
pazarlanıyor ve benchmark'ların çoğu 2023 öncesi veriden oluşuyor. Google'ın
kesim tarihini açıkça yazmış olması nadir bir cömertlik. Diğer modellerin
çoğunda bu satır yok, dolayısıyla bu soru sorulamıyor bile.

## Coverage 1,000 neden iyi haber değil?

TimesFM yalnızca nokta tahmini değil, yüzde 10 ile yüzde 90 kuantilleri arasında
bir tahmin aralığı da veriyor. Bu nominal yüzde 80'lik aralığın, tekrarlanan
örneklerde gerçeklerin yaklaşık yüzde 80'ini kapsamasını bekleriz.

İlk *Straight Outta Compton* koşusunda multivariate coverage **1,000** çıktı.
Bu bir başarı puanı değil. Aralık her şeyi kapsayacak kadar geniş olabilir.

On altı olayın tamamında ortalama coverage multivariate için yüzde 84,3,
univariate için yüzde 81,7 oldu. Olaylar arasında dağılım çok genişti:
multivariate coverage Chandrayaan-3'te yüzde 57,3'e inerken üç olayda yüzde
100'e ulaştı.

Coverage'ın yanına bu yüzden *sharpness* koydum: ortalama bant genişliğini
ortalama gerçek trafikle böldüm. Olaylar arası ortanca oran multivariate için
**2,16**, univariate için **1,89**. En uç olayda 59,2'ye çıktı.

Başka bir deyişle, bantlar çoğu zaman hedeflenenden fazla gözlemi kapsıyor ama
bunu çok genişleyerek yapıyor. Aralığı olmayan baseline'lara da coverage=0
yazmadım; karşılaştırılabilir bir aralıkları olmadığı için hücreyi boş bıraktım.

![TimesFM kuantil coverage ve bant genişliği](../figures/interval-calibration.png)

Kuantil kalibrasyonu bu projenin yan bulgusu olarak kaldı. Aslında tek başına
başka bir deney: zaman serisi foundation modellerinin güven bantları rejim
kırılmalarında ve dikkat sıçramalarında ne kadar güvenilir?

## Bu atlas neyi kanıtlamıyor?

Wikipedia görüntülenmesi insan değil; beğeni, duygu veya niyet hiç değil.
İngilizce Wikipedia da internetin tamamı değil. Arama motorları, haber akışı,
ana sayfa yerleşimi, yönlendirmeler ve sayfanın açıldığı tarih seriyi
değiştirebilir.

Takımyıldızdaki oklar güçlü lead/lag birlikte hareketini gösteriyor; nedensellik
göstermiyor. Bir sayfanın diğerinden önce yükselmesi, onu yükselttiği anlamına
gelmez.

Katalogdaki on altı olayın tamamı zaten “patlamış” olaylar. Bu seçim betimsel atlas
için sorun değil, ama tahmin sonuçları bu seçime koşullu. Sessiz geçen olayları,
başarısız lansmanları ve hiçbir yere taşmayan gündemleri eklemeden evrensel bir
dikkat yasası kuramam.

Ayrıca TimesFM-3 kaynak kodu ile model ağırlıkları aynı lisansa sahip değil.
Kullandığım 3.0 checkpoint'i Google'ın [ticari olmayan ve production dışı
kullanım lisansı](https://huggingface.co/google/timesfm-3.0-pytorch/blob/main/LICENSE)
altında. Bu çalışma araştırma ve yayın deneyi; ağırlıkları bir ürün önerisi
olarak sunmuyorum.

## Geriye kalan soru

“İnternet bir şeyi kaç günde unutur?” sorusunun tek bir cevabı yok. Barbenheimer
üç günde yarıya indi; Margot Robbie sekiz gün sürdü. Bazı olaylarda ilgi ana
sayfada, bazılarında filmlere, insanlara, tarihe veya altyapıya taşındı.

Bu yüzden benim için projenin en iyi cümlesi model tablosunda değil:

> Bir olayın yarattığı dikkatin büyük kısmı, olayın kendi sayfasında
> yaşamayabilir.

TimesFM-3 cevabın kendisi değil. Dağılmış bu küçük sistemlerin geleceğini
birlikte okuyup okuyamadığımızı sınamanın yolu. Şimdilik cevap: bazen; ama iki
parametreli eğriyi geçmeden etkilenmemek lazım.

Bir de şunu sormadan: modele o cevabı zaten göstermiş miydik? Bu yazıda o soruya
kesin bir yanıt veremedim. Ama sorulabilir bir soru olduğunu ve sormanın tek bir
tarih satırını okumaktan ibaret olduğunu göstermek, bulduğum en kullanışlı şey
oldu.

Kod, olay kataloğu, yeniden üretme komutları ve bütün olay sonuçları:

**[github.com/meryemsakin/internet-half-life](https://github.com/meryemsakin/internet-half-life)**
