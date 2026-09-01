# İnternet Bir Şeyi Kaç Günde Unutuyor?

*Barbenheimer'dan Ever Given'a on olay, 96,6 milyon Wikipedia görüntülenmesi ve
330 milyon parametreli bir modelin iki parametreli eğriyle imtihanı.*

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

Katalogda on olay var:

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

Her olay için bir ana sayfa ve dört ila altı komşu sayfa seçtim. Wikimedia'nın
herkese açık Pageviews API'sinden günlük görüntülenmeleri aldım.

Sonuçta on takımyıldızda, olaydan sonraki 60 günde sıradan gün seviyesinin
üzerinde toplam **96,6 milyon görüntülenme** oluştu. Trafikle ağırlıklandırınca
bunun **yüzde 77,5'i ana olay sayfalarının dışındaydı**.

![On olayda dikkatin ana sayfanın dışına taşan payı](../figures/catalog-spillover.png)

Bu sayı “internetin yüzde 77,5'i şöyledir” demiyor. Olayları rastgele seçmedim;
hepsi görünür dikkat patlamaları yaratmış, elle seçilmiş örnekler. Sayfa
takımyıldızlarını da ben kurdum. Yüzde 77,5 bu kataloğun betimsel sonucu.

Ama tek örnekte görülen yüzde 79'luk taşmanın tesadüf olmadığını söylemeye
yetecek kadar tutarlı bir desen var: Dünya Kupası finalinde yüzde 97,4, Ever
Given'da yüzde 86,1, *Straight Outta Compton*'da yüzde 79,0.

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
günlük olay-sonrası veri görüyor; tahmin sekizinci gün başlıyor. Bütün on olayda
aynı protokolü kullandım.

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

On olayın ortanca WAPE sonuçları şöyle:

| Yöntem | Ortanca olay WAPE'si (düşük daha iyi) |
|---|---:|
| TimesFM-3, bütün sayfalar birlikte | **0,261** |
| TimesFM-3, her sayfa bağımsız | 0,286 |
| Üstel sönüm | 0,472 |
| Power-law sönüm | 0,439 |
| Geçen haftayı tekrar et | 5,008 |

Yalnızca bu tabloya bakarsak multivariate TimesFM kazanmış gibi görünüyor. On
olayı tek tek eşleştirince hikâye zayıflıyor.

Multivariate model on olayın altısında daha iyi, dördünde daha kötüydü.
Multivariate eksi univariate WAPE farkının ortancası **−0,004**: pratikte çok
küçük. İki yönlü exact sign-test sonucu **p=0,754**. Bu katalogla “komşu sayfalar
tahmini iyileştiriyor” diyemiyorum; farkı sıfırdan ayıramıyorum.

![Her olay için multivariate eksi univariate WAPE](../figures/multivariate-delta-by-event.png)

Daha beklenmedik sonuç basit eğrilerden geldi. On olayın **beşinde**, üstel veya
power-law eğrilerinden en az biri her iki TimesFM koşulunu da geçti.

*Straight Outta Compton* örneğinde power-law WAPE 0,234; multivariate TimesFM
0,248; univariate TimesFM 0,251 verdi. Foundation model burada iki parametreli
eğriye kaybetti.

Barbenheimer'da ise multivariate TimesFM 0,246 ile en iyiydi. Univariate 0,269,
üstel sönüm 0,411, power-law 0,475 verdi. Tek bir vitrini seçip genellemek yerine
on olayı yan yana koymanın farkı burada ortaya çıkıyor: model bazen ilişkili
serilerden gerçekten yararlanıyor, bazen basit sönüm yeterli oluyor, bazen de
iki TimesFM modu birbirinden ayrılmıyor.

![Modellerin on olaydaki WAPE dağılımı](../figures/forecast-model-comparison.png)

Bu, “TimesFM işe yaramıyor” sonucu değil. Ortanca WAPE'de iki TimesFM modu da
iki sönüm ailesinden daha iyi. Daha dar sonuç şu: modelin multivariate olması
her olayda ek tahmin değeri sağlamıyor ve alan bilgisi taşıyan basit baseline'ı
atlamak modeli olduğundan güçlü gösteriyor.

## Coverage 1,000 neden iyi haber değil?

TimesFM yalnızca nokta tahmini değil, yüzde 10 ile yüzde 90 kuantilleri arasında
bir tahmin aralığı da veriyor. Bu nominal yüzde 80'lik aralığın, tekrarlanan
örneklerde gerçeklerin yaklaşık yüzde 80'ini kapsamasını bekleriz.

İlk *Straight Outta Compton* koşusunda multivariate coverage **1,000** çıktı.
Bu bir başarı puanı değil. Aralık her şeyi kapsayacak kadar geniş olabilir.

On olayın tamamında ortalama coverage multivariate için yüzde 88,9, univariate
için yüzde 88,1 oldu. Olaylar arasında dağılım çok genişti: multivariate
coverage Chandrayaan-3'te yüzde 57,3'e inerken üç olayda yüzde 100'e ulaştı.

Coverage'ın yanına bu yüzden *sharpness* koydum: ortalama bant genişliğini
ortalama gerçek trafikle böldüm. Olaylar arası ortanca oran multivariate için
**2,26**, univariate için **2,04**. En uç olayda 59,2'ye çıktı.

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

Katalogdaki on olayın tamamı zaten “patlamış” olaylar. Bu seçim betimsel atlas
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

Kod, olay kataloğu, yeniden üretme komutları ve bütün olay sonuçları:

**[github.com/meryemsakin/internet-half-life](https://github.com/meryemsakin/internet-half-life)**
