# 🔐 BORSA ASİSTANI - HASSASİYETLER AYARLAMA REHBERİ

> ✅ **Bu rehber şu amaca hizmet eder:**
> - Şifreleri ve API anahtarlarını GitHub'dan gizlemek
> - Güvenli bir environment variables sistemi kurmak
> - Google Cloud sunucuda doğru şekilde yayınlamak

---

## 📋 ÖZET: 3 AŞAMALI GÜVENLİK SİSTEMİ

```
┌─────────────────────────────────────────────────────────────┐
│ 1️⃣ GELİŞTİRME (Bilgisayarında)                               │
│    └─ .env dosyası (.gitignore'da gizli)                    │
│    └─ Gerçek şifreleri yerel olarak depola                  │
│                                                              │
│ 2️⃣ GITHUB                                                    │
│    └─ .env.example (şablon, gerçek değer YOK)               │
│    └─ .gitignore (.env dosyasını dışla)                     │
│    └─ Kod tamamen güvenli yayınlanır                        │
│                                                              │
│ 3️⃣ GOOGLE CLOUD SUNUCUSU                                     │
│    └─ .env dosyasını sunucuda manuel oluştur                │
│    └─ Gerçek API anahtarlarını buraya yaz                   │
│    └─ .env dosyası asla GitHub'a gitmez                     │
└─────────────────────────────────────────────────────────────┘
```

---

## 🖥️ ADIM 1: YERİ (DEVELOPMENT) KURULUM

### 1.1 Python Dependencies Yükle

Eğer `python-dotenv` yüklü değilse:

```bash
pip install python-dotenv
```

### 1.2 `.env` Dosyası Oluştur (Bilgisayarında)

Kök dizinde `.env` dosyası oluştur (`.gitignore` tarafından otomatik korunur):

```env
# 📱 API SUNUCUSU AYARLARI (GELİŞTİRME)
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=4

# Eğer Flask/FastAPI çalıştırıyorsan:
# API için geliştirme:
FLASK_ENV=development
FLASK_DEBUG=1

# 💾 VERİTABANI AYARLARI (Yerel)
DATABASE_PATH=./borsa_terminali.db
DATABASE_URL=sqlite:///./borsa_terminali.db

# 🔐 GÜVENLİK (Geliştirme için rasgele değer)
SECRET_KEY=SuperGizliAnahtarGelistirmeIcin12345!@#$%

# 📲 FLUTTER AYARLARI (Geliştirme)
FLUTTER_API_ADDRESS=127.0.0.1:8000

# 🌍 ORTAM
ENVIRONMENT=development
```

### 1.3 `.env` Dosyasının Yüklü Olduğunu Doğrula

Python'da test et:

```python
from dotenv import load_dotenv
import os

load_dotenv()
print(f"API Host: {os.getenv('API_HOST')}")
print(f"Database: {os.getenv('DATABASE_URL')}")
```

---

## 🌐 ADIM 2: GITHUB PUSH (GÜVENLİ)

### ✅ GitHub'a İtileceк Dosyalar:
- ✅ `database.py` (environment variables kullanan)
- ✅ `api.py` (environment variables kullanan)
- ✅ `.env.example` (şablon, gerçek değer YOK)
- ✅ `.gitignore` (hassas dosyaları dışlayan)
- ✅ Tüm Dart dosyaları

### ❌ GitHub'a İTİLMEYECEK:
- ❌ `.env` (sadece bilgisayarında kalır)
- ❌ `borsa_terminali.db` (veritabanı dosyası)
- ❌ `__pycache__/`
- ❌ `venv/` ve diğer virtual environment dosyaları

### Git Komutları:

```bash
# Durum kontrol et (.env görmemeli)
git status

# Tüm dosyaları ekle
git add .

# Commit
git commit -m "🔐 Environment variables sistemi kuruldu"

# Push
git push origin main
```

---

## ☁️ ADIM 3:  GOOGLE CLOUD SUNUCUSU KURULUM

### 3.1 Sunucuya Bağlan

```bash
# SSH ile bağlan
gcloud compute ssh --zone=DİLİN_BÖLGESİ SUNUCU_İSMİ

# Örnek:
gcloud compute ssh --zone=us-central1-a borsa-server
```

### 3.2 Repository'i Klonla (GitHub'dan)

```bash
# Ev dizinine git
cd ~

# Repository'i klonla (sadece kod, .env yok)
git clone https://github.com/KULLANICIADI/finance_assistance.git

# Klasöre gir
cd finance_assistance
```

### 3.3 Python Ortamını Hazırla

```bash
# Python 3.9+ yüklü mü kontrol et
python3 --version

# Virtual environment oluştur
python3 -m venv venv

# Aktif et
source venv/bin/activate

# Dependencies yükle
pip install -r requirements.txt
```

**requirements.txt oluştur** (eğer yoksa):

```bash
pip freeze > requirements.txt
```

### 3.4 `.env` Dosyasını Sunucuda Manuel Oluştur

```bash
# .env dosyasını oluştur (nano editörü ile)
nano .env
```

Bunu yazı:

```env
# 📱 API SUNUCUSU (SUNUCUDA ÇALIŞACAK)
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=4

# 💾 VERİTABANI
DATABASE_PATH=/home/SUNUCU_KULLANICISI/finance_assistance/borsa_terminali.db
DATABASE_URL=sqlite:////home/SUNUCU_KULLANICISI/finance_assistance/borsa_terminali.db

# 🔐 GÜVENLİK (ÜRETIM İÇİN UZUN BİR ANAHTAR)
SECRET_KEY=SupKomplikeFOKAD-1@#$%^&*()_+{}|:"<>?[]\\;',./1234567890SuperGuzliFOKA

# 📲 FLUTTER AYARLARI (SUNUCU IP'SİNİ BURAYA YAZ)
# Kend Controlul Panelde sunucunun dış IP'sini bul
FLUTTER_API_ADDRESS=34.123.45.67:8000
# ÖRNEK: google cloud console'dan external IP'yi kopyala ve buraya yapıştır

# Diğer hassas bilgiler
NOTIFICATION_EMAIL=your_email@gmail.com
NOTIFICATION_PASSWORD=APP_PASSWORD_BURAYA_YAZILACAK

# 🌍 ORTAM (SUNUCUDA PRODUCTION)
ENVIRONMENT=production
LOG_LEVEL=INFO
```

**Kaydet ve çık:**
- Ctrl+O (save)
- Enter
- Ctrl+X (exit)

### 3.5 `.env` Dosyasının Korunduğunu Doğrula

```bash
# .env dosyasının izinlerini değiştir (sadece sahip okuyabilir)
chmod 600 .env

# Doğrula
ls -la .env
# Çıktı: -rw------- (sadece sahip okuyabilir)
```

### 3.6 API'yi Sunucuda Başlat

```bash
# Virtual environment aktif mi kontrol et
which python  # Eğer venv/bin/python gösteriyorsa iyidir

# FastAPI/Uvicorn'ı çalıştır
python api.py

# Veya uvicorn ile
uvicorn api:app --host 0.0.0.0 --port 8000 --workers 4
```

### 3.7 Sunucunun Harici IP'sini Bul

```bash
# Dış IP'yi öğren
curl -s https://cloud.google.com/compute/docs/instances/detecting-compute-environment | grep EXTERNAL_IP

# VEYA Google Cloud Console'dan:
# VM Instances -> İnstan adına tıkla -> "External IP" kısmını kopyala
```

### 3.8 Flutter Uygulamasını  Güncellemek

Dart dosyasında, derleme sırasında:

```bash
# Android
flutter build apk --dart-define=API_ADDRESS=34.SUNUCU_IP:8000

# iOS
flutter build ios --dart-define=API_ADDRESS=34.SUNUCU_IP:8000

# Web
flutter build web --dart-define=API_ADDRESS=34.SUNUCU_IP:8000
```

---

## 🔍 KONTROL LİSTESİ

### Güvenlik Kontrolleri

- [ ] `.env` dosyası `.gitignore`'da mı?
- [ ] `.env.example` GitHub'da mı? (gerçek değer YOK)
- [ ] `database.py` `load_dotenv()` kullanıyor mu?
- [ ] Sunucuda `.env` dosyası oluşturuldu mu?
- [ ] Sunucuda `.env` izinleri `600` mı? (`chmod 600 .env`)
- [ ] API sunucusu `localhost` yerine `0.0.0.0` dinliyor mu?
- [ ] Flutter API adresi şifrelenmiş mi (--dart-define)?

### Test Komutları

```bash
# Bilgisayarında (development)
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print(os.getenv('API_HOST'))"

# Sunucuda
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print(os.getenv('API_HOST'))"

# API sağlıklı mı?
curl http://DİŞ-IP:8000/piyasa
```

---

## ⚠️ YAYGIIN HATALAR VE ÇÖZÜMLERI

### Hata 1: ".env dosyası bulunmadı"
```python
# ❌ Yanlış
DATABASE_URL = "sqlite:///borsa.db"

# ✅ Doğru
import os
from dotenv import load_dotenv
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///borsa.db")
```

### Hata 2: "GitHub'da .env dosyası görülüyor"
```bash
# Kontrol et
git ls-files | grep .env

# Eğer görülürse (yapma!):
git rm --cached .env
git commit -m "Remove .env from tracking"
```

### Hata 3: "Flutter sunucuya bağlanamıyor"
```dart
// Doğru adresi kullandığını kontrol et
const String apiAdresi = String.fromEnvironment(
  'API_ADDRESS',
  defaultValue: '127.0.0.1:8000',
);

// Sunucuda port açık mı?
# Sunucuda test et:
curl -X GET http://localhost:8000/piyasa
```

### Hata 4: "Sunucuda database locked"
```bash
# Bir tane worker_process varsa, bitmesini bekle
killall python  # Tüm Python süreçlerini kapat

# Sonra tekrar başlat
python api.py &
python worker.py &
```

---

## 🔒 ÜRÜN GÜVENLIĞI EN İYİ PRATİKLERİ

### Kripto Kuralları

1. **Environment'da Sakla:** `.env` dosyasında
2. **Git'te Gizle:** `.gitignore` ile hariç tut
3. **GitHub'da Gösterme:** `.env.example` şablonunu kullan
4. **Sunucuda Koruma:** `chmod 600 .env`
5. **Döndür:** 3-6 ayda bir anahtarları değiştir
6. **Log'a Yazmamı Hazırla:** Şifrelerı asla terminal çıktısına yazdırma

### Shell Script (Otomatik Başlatma)

`start_api.sh` oluştur:

```bash
#!/bin/bash
source .env  # .env dosyasını yükle
export API_HOST
export API_PORT
export DATABASE_URL
python api.py
```

Yetki ver:
```bash
chmod +x start_api.sh
./start_api.sh
```

---

## ✅ SONUÇ

Artık:
- ✅ GitHub'da şifreler yok
- ✅ `.env` güvenle saklanan
- ✅ Sunucu `.env` ile çalışan
- ✅ Her ortam kendi ayarlarını kullanan
- ✅ Daha güvenli ve profesyonel

**Sorular?** Rehberi tekrar okur veya Google Cloud docs'u kontrol etebilirsin!
