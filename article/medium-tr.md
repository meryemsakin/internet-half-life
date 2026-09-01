# İnternet Bir Şeyi Kaç Günde Unutuyor?

Bir filmin vizyona girdiği günü düşünün. Önce filmin adı yükseliyor. Ardından
oyuncular, yönetmen, filmin dayandığı gerçek olay ve bazen yıllardır kimsenin
bakmadığı bir tarih sayfası hareketleniyor. Birkaç gün sonra çoğu normale
dönüyor. Bazıları dönmüyor.

Benim merak ettiğim şey şuydu: Bu hareketi yalnızca bir “trend” çizgisi olarak
değil, birbirine bağlı küçük bir sistem olarak görebilir miyiz? Daha basit
söylersem: İnternet bir şeyi unutmaya başladığında dikkat nereye gidiyor?

Bu sorudan **Internet Half-Life** çıktı. Proje, kültürel olayların çevresindeki
Wikipedia sayfalarını birlikte izliyor. İlk örnek 2015 yapımı *Straight Outta
Compton*: film sayfası, N.W.A, Dr. Dre, Ice Cube ve Eazy-E.

## Bir olay tek bir zaman serisi değil

Normalde böyle bir çalışma “Barbenheimer sayfası kaç kez görüntülendi?” diye
başlayıp tek çizgiyle biterdi. Oysa olayın ilginç kısmı ana sayfada değil,
çevresinde.

Birileri filmi izledikten sonra N.W.A'i mı araştırdı? Dr. Dre'ye yönelik ilgi
filmden önce mi, sonra mı zirve yaptı? Dikkatin ne kadarı film sayfasında kaldı,
ne kadarı grubun üyelerine dağıldı?

Bu nedenle her olayı küçük bir takımyıldız olarak tanımladım. Her düğüm bir
Wikipedia sayfası, her seri o sayfanın günlük görüntülenme sayısı. Veriler
Wikimedia'nın herkese açık Pageviews API'sinden geliyor.

Burada önemli bir sınır var: Wikipedia görüntülenmesi “insanların ne düşündüğü”
değil. Beğeni de değil, duygu da değil. Yalnızca İngilizce Wikipedia üzerinde
kayda geçen dikkat. Buna rağmen olayların yükselişini ve sönüşünü izlemek için
şaşırtıcı derecede temiz bir iz bırakıyor.

## “Yarı ömür” derken neyi kastediyorum?

Fizikteki yarı ömür kavramını burada gevşek ama ölçülebilir bir tanım olarak
kullandım.

Önce olaydan önceki 28 günün medyanını “sıradan gün” seviyesi kabul ediyorum.
Olaydan sonraki zirvenin bu seviyenin üzerinde kalan kısmına *excess attention*
diyorum. Seri, bu fazlalığın yarısının altında üç gün boyunca kaldığında yarı
ömrüne ulaşmış sayılıyor.

Üç gün şartı önemli. Tek günlük düşüşleri “unutma” olarak saymak istemedim.

Film 14 Ağustos 2015'te gösterime girdi. Beş sayfa da üç gün sonra zirve yaptı.
Film sayfası sıradan bir günün 10,4 katına, Dr. Dre 9,8 katına, Ice Cube 9,5
katına çıktı.

Sonraki 60 günde bu beş sayfada normalin üzerinde toplam **13,1 milyon**
görüntülenme oluştu. Bunun yalnızca yüzde 21'i film sayfasındaydı. Fazladan
dikkatin **yüzde 79'u çevredeki dört sayfaya dağıldı**.

Film, N.W.A, Ice Cube ve Eazy-E için ölçtüğüm yarı ömür üç gündü. Dr. Dre için
yedi gün. Aynı olayla yükselen sayfalar aynı hızda unutulmadı.

Tek bir yarı ömür rakamından daha ilginç olan şey, sayfaların aynı hızda
sönmemesi. Bir olay adı hızla kaybolurken olayın açtığı tarihsel merak daha uzun
sürebiliyor. Dikkat yalnızca azalmak zorunda değil; biçim değiştiriyor.

## TimesFM-3 burada neden var?

Google, TimesFM-3'ü 31 Ağustos 2026'da yayımladı. Önceki sürümler ağırlıklı
olarak tek bir serinin geçmişinden tahmin yaparken, TimesFM-3 ilişkili serileri
aynı anda görebiliyor. Zaman boyunca attention ile seriler arasındaki attention
katmanlarını dönüşümlü kullanıyor.

Bu proje için ilginç soru “model Wikipedia'yı tahmin edebiliyor mu?” değildi.
Daha dar bir soru sordum:

> Bir olayın ilk yedi gününü gösterirsem, ilişkili sayfalar kalan otuz günü
> tahmin etmeye yardım ediyor mu?

Bunu üç tahminle karşılaştırdım:

1. Bütün sayfaları birlikte gören TimesFM-3.
2. Her sayfayı bağımsız gören TimesFM-3.
3. Geçen haftayı tekrar eden basit bir baseline.

Bu karşılaştırma projeyi model demosu olmaktan çıkarıyor. Multivariate tahmin
gerçekten faydalıysa birinci koşul ikinciden daha iyi olmalı. Değilse güzel bir
ilişki grafiği üretmiş, fakat tahmin için kullanışlı bir bağlam bulamamışız
demektir.

Genel WAPE sonuçları şöyleydi:

| Yöntem | WAPE (düşük daha iyi) |
|---|---:|
| TimesFM-3, bütün sayfalar birlikte | **0,248** |
| TimesFM-3, her sayfa bağımsız | 0,251 |
| Geçen haftayı tekrar eden baseline | 1,514 |

Multivariate koşul kazandı ama fark yalnızca 0,003. Üstelik sayfa bazında sonuç
aynı değildi. İlişkili seriler Dr. Dre ve Eazy-E tahminlerini iyileştirirken film
sayfası ile N.W.A tahminlerini kötüleştirdi. Ice Cube'da neredeyse hiçbir şey
değişmedi.

Bu sonucu sevdim çünkü fazla düzgün değil. “Birbiriyle ilişkili daha çok veri
verince tahmin iyileşir” cümlesi bu örnekte tam olarak doğru değil. Birlikte
hareket etmek, her zaman yararlı tahmin bilgisi taşımak anlamına gelmiyor.

## Grafikteki oklar ne anlama gelmiyor?

Takımyıldızı görselindeki oklar sayfalar arasındaki en güçlü lead/lag
birlikteliğini gösteriyor. Örneğin bir sayfa diğerinden bir gün önce hareket
ediyorsa ok o yönde çiziliyor.

Bu bir nedensellik grafiği değil. “Margot Robbie sayfası Barbie ilgisine sebep
oldu” gibi bir sonuç çıkarmak mümkün değil. İki sayfa aynı haber, aynı ana sayfa
yerleşimi veya aynı dış bağlantı yüzünden birlikte hareket etmiş olabilir.

Görselin işi kanıt sunmak değil; dikkat dalgasının tek çizgiden daha büyük
olduğunu görünür hale getirmek.

## Benim için asıl sonuç

Bir olayın ne kadar büyük olduğu çoğu zaman zirvesiyle anlatılıyor: kaç izlenme,
kaç arama, kaç paylaşım. Oysa kültürel etkisinin daha ilginç kısmı zirveden
sonra başlıyor.

Ne kadar hızlı söndü? Hangi komşu fikirlere taşındı? Bir hafta sonra geriye ne
kaldı? Aynı olay yeniden canlandı mı?

Internet Half-Life'ın cevaplamak istediği soru bu. TimesFM-3 ise cevabın
kendisi değil; bu küçük dikkat sistemlerinin geleceğini birlikte okuyup
okuyamayacağımızı sınamak için kullandığım araç.

Kod, olay kataloğu ve tekrar üretme adımları GitHub reposunda:

> **[Repo bağlantısı yayınlandıktan sonra eklenecek.]**
