# Kurulum ve Çalıştırma Dokümanı

Modüler Bilgisayar Toplama ve Sipariş Sistemi — EBLG443 Tasarım Kalıpları dönem projesi.

## 1. Gereksinimler

| Gereksinim | Sürüm | Not |
|---|---|---|
| Python | 3.10 veya üzeri | Zorunlu. `abc`, `dataclasses`, `X \| None` tip sözdizimi kullanılır. |
| Git | herhangi bir güncel sürüm | Depoyu klonlamak için. |
| `anthropic` paketi | 2.8 veya üzeri | **İsteğe bağlı.** Yalnızca AI asistanını gerçek Claude modeliyle kullanmak için. |
| Anthropic API anahtarı | — | **İsteğe bağlı.** Tanımlı değilse asistan çevrimdışı modelle çalışır. |

Temel uygulama ve tüm testler yalnızca Python standart kütüphanesiyle çalışır; başka bir
paket kurmak gerekmez.

Python sürümünü kontrol etmek için:

```bash
python --version
```

Windows'ta `python` komutu tanınmıyorsa `py` kullanın (`py --version`). Python yüklü
değilse [python.org](https://www.python.org/downloads/) adresinden indirip kurulum sırasında
**"Add python.exe to PATH"** seçeneğini işaretleyin.

## 2. Projeyi İndirme

```bash
git clone https://github.com/kamurangenc/pc-siparis-sistemi.git
cd pc-siparis-sistemi
```

Klasör adı veya yolu Türkçe karakter ya da boşluk içeriyorsa `cd` komutunda yolu tırnak
içine alın, örneğin `cd "C:\Users\...\tasarim_kalipları"`.

## 3. Uygulamayı Çalıştırma

Tüm komutlar proje kök klasöründe (`main.py` dosyasının bulunduğu yerde) çalıştırılmalıdır.

### 3.1 Konsol arayüzü

```bash
python main.py
```

1. Uygulama adınızı sorar.
2. Ana menüden bir işlem seçilir:
   - `[1]` Kendi sistemini topla: temel kasa seçilir, ek donanımlar tek tek eklenir.
   - `[2]` Hazır paket seç: öğrenci, yayıncı veya pro paketlerinden biri seçilir; istenirse donanım eklenir.
   - `[3]` AI asistanından öneri al: ihtiyaç ve bütçe yazılır, asistan katalogdan bir sistem önerir.
   - `[0]` Çıkış.
3. Ödeme yöntemi seçilir: havale (%5 indirim) veya kredi kartı (tek çekim ya da taksit).
4. Sipariş aşamaları (ödeme, montaj, test, kargo) müşteri ve teknik servis panellerinde görüntülenir.

Her adımda köşeli parantez içindeki kod yazılıp Enter'a basılır. Geçersiz bir seçim
yapılırsa uygulama aynı soruyu tekrar sorar.

### 3.2 Pencere arayüzü

```bash
python gui.py
```

Pencere dört bölümden oluşur:

1. **Ürün Seçimi:** "Temel Kasa" veya "Hazır Paket" sekmesinden seçim yapılıp **Seç ve Üret**'e
   basılır. "AI Asistanı" sekmesinde ihtiyaç ve bütçe yazılıp **Öneri Al**'a basılır.
2. **Sistem ve Ek Donanım:** Seçilen sistemin parçaları ve liste fiyatı görünür; **+** düğmeleriyle
   donanım eklenir, **Ek donanımları kaldır** ile temel sisteme dönülür.
3. **Ödeme:** Havale veya kredi kartı (taksit sayısıyla) seçilir; ödenecek tutar anında güncellenir.
   **Siparişi Tamamla** ile sipariş verilir.
4. **Sipariş Takibi:** Aşama göstergesi, müşteri bildirimleri ve teknik servis paneli sipariş
   ilerledikçe güncellenir.

Üstteki "Müşteri adı" alanına yazılan ad bildirimlerde kullanılır. Hata ve bilgi mesajları
pencerenin altındaki durum çubuğunda gösterilir.

### 3.3 Etkileşimsiz örnek senaryo

Hiç girdi istemeden iki örnek siparişi baştan sona çalıştırır:

```bash
python demo.py
```

## 4. AI Asistanını Gerçek Modelle Kullanma (İsteğe Bağlı)

API anahtarı olmadan menüdeki `[3]` seçeneği **çevrimdışı kural tabanlı modelle** çalışır
ve ekranda bunu belirten bir uyarı gösterilir. Gerçek Claude modelini (`claude-opus-5-5`)
kullanmak için:

1. Bağımlılığı kurun:

   ```bash
   pip install -r requirements.txt
   ```

2. [Anthropic Console](https://console.anthropic.com/) üzerinden bir API anahtarı oluşturun.
   API kullanımı ücretlidir.

3. Anahtarı **aynı terminal penceresinde** ortam değişkeni olarak tanımlayın:

   | Terminal | Komut |
   |---|---|
   | PowerShell | `$env:ANTHROPIC_API_KEY = "anahtarınız"` |
   | Komut İstemi (cmd) | `set ANTHROPIC_API_KEY=anahtarınız` |
   | macOS / Linux | `export ANTHROPIC_API_KEY="anahtarınız"` |

4. Uygulamayı başlatın (`python main.py`) ve menüden `[3]`'ü seçin. Ekranda
   "(Claude modeli kullanılıyor)" yazısı görünmelidir.

> Anahtarı koda, README'ye veya Git deposuna yazmayın. Ortam değişkeni yalnızca o terminal
> penceresi açık kaldığı sürece geçerlidir.

## 5. Testleri Çalıştırma

```bash
python -m unittest discover -s tests -v
```

Beklenen son satırlar:

```
Ran 49 tests in ...s

OK
```

Testler ağ erişimi veya API anahtarı gerektirmez. Ayrıntılar için [TEST.md](TEST.md).

## 6. Proje Yapısı

```
main.py              Konsol uygulamasının giriş noktası
gui.py               Pencere uygulamasının giriş noktası
demo.py              Etkileşimsiz örnek senaryo
requirements.txt     İsteğe bağlı bağımlılık (anthropic)
pc_siparis/          Uygulama kodu (her kalıp ayrı modülde)
  ai/                AI donanım öneri asistanı
tests/               Otomatik testler (unittest)
docs/                Kalıp Haritası, tasarım raporu, UML diyagramları, bu doküman
```

## 7. Sık Karşılaşılan Sorunlar

| Belirti | Neden | Çözüm |
|---|---|---|
| `can't open file 'main.py'` | Terminal proje klasöründe değil. | `cd` ile `main.py`'nin bulunduğu klasöre geçin. |
| `'python' is not recognized` | Python PATH'te değil. | `py main.py` kullanın veya Python'u PATH seçeneğiyle yeniden kurun. |
| `ModuleNotFoundError: No module named 'tkinter'` | Python tkinter olmadan kurulmuş (bazı Linux dağıtımları). | Windows/macOS'ta Python'u python.org'dan yeniden kurun; Linux'ta `sudo apt install python3-tk`. |
| `SyntaxError` veya `TypeError: unsupported operand type(s) for \|` | Python sürümü 3.10'dan eski. | Python 3.10+ kurun. |
| Türkçe karakterler bozuk görünüyor | Konsol kod sayfası UTF-8 değil. | Önce `chcp 65001` çalıştırın. |
| AI seçeneğinde "çevrimdışı model kullanılıyor" uyarısı | `ANTHROPIC_API_KEY` tanımlı değil. | Bölüm 4'teki adımları uygulayın. |
| "anthropic paketi kurulu değil" uyarısı | Anahtar tanımlı ama paket kurulu değil. | `pip install -r requirements.txt` |
| "API anahtarı geçersiz veya tanımlı değil" | Anahtar hatalı yazılmış veya iptal edilmiş. | Anahtarı Console'dan kontrol edip yeniden tanımlayın. |
| "İstek sınırı aşıldı" | Kısa sürede çok fazla istek gönderildi. | Bir süre bekleyip tekrar deneyin. |
