# ✅ GITHUB'A YÜKLEMEDEN ÖNCE KONTROL LİSTESİ

## 🔐 HASSAS BİLGİLER KONTROLü

- [ ] `.env` dosyasında **hiçbir gerçek şifre/API anahtarı yok** mu?
- [ ] Tüm hassas bilgiler `.gitignore`'da hariç tutuldu mu?
- [ ] `database.py`'da `load_dotenv()` var mı?
- [ ] `api.py`'da `load_dotenv()` var mı?
- [ ] `.env.example` template dosyası GitHub'da mı? (gerçek değer YOK)

## 📁 DOSYA DURUMU

```bash
# Bu komutu çalıştır:
git status

# Görmemesi gerekenler:
❌ .env
❌ *.db (veritabanları)
❌ __pycache__/
❌ venv/
❌ .vscode/settings.json (eğer şifre varsa)
```

## 🔍 GITHUB PUSH HAZIRLIĞI

```bash
# Son kontrol: .env görüyor mü?
git ls-files | grep -E "\.env$|\.db$|__pycache__|venv" && echo "⚠️ UYARI: Hassas dosyalar görülüyor!" || echo "✅ Güvenli"

# Dosya farkını kontrol et
git diff --cached

# Güvenli isen push et
git push origin main
```

## ☁️ GOOGLE CLOUD SUNUCUSU HAZIRLığı

### Sunucuya Bağlanmadan Önce El Kontrol

- [ ] `.env.example` dosyası GitHub'da mı?
- [ ] `SECURITY_SETUP_GUIDE.md` dosyası GitHub'da mı?
- [ ] `setup_server.sh` dosyası GitHub'da mı?
- [ ] `requirements.txt` dosyası GitHub'da mı ve güncel mi?

### Sunucuda Yapılacaklar

```bash
# 1. Repository'i klonla
git clone https://github.com/KULLANICIADI/finance_assistance.git
cd finance_assistance

# 2. Setup script'i çalıştır
chmod +x setup_server.sh
./setup_server.sh

# 3. .env dosyasını manuel oluştur
nano .env

# 4. .env.example'den kopyala ve gerçek değerleri yaz:
# - DATABASE_PATH: /home/user/finance_assistance/borsa_terminali.db
# - FLUTTER_API_ADDRESS: SUNUCU_DIŞ_IP:8000
# - SECRET_KEY: Uzun ve rasgele bir anahtar
# - ENVIRONMENT: production

# 5. API'yi başlat
source venv/bin/activate
python api.py
```

## 🧪 TEST

### Yerel (Geliştirme) Test
```bash
# Python ortamını test et
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print(f'API Host: {os.getenv(\"API_HOST\")}')"

# API'yi başlat ve test et
python api.py

# Başka terminalde:
curl http://127.0.0.1:8000/piyasa
```

### Sunucuda Test
```bash
# SSH ile bağlan
gcloud compute ssh --zone=BÖLGE SUNUCU_İSMİ

# API'yi başlat
python api.py

# Başka terminalde test et:
curl http://localhost:8000/piyasa

# Dış IP'den test et:
curl http://SUNUCU_DIŞ_IP:8000/piyasa
```

## 🚨 SON UYARILAR

1. **ASLA**: Gerçek şifreleri yorum satırlarında veya kod içinde bırakma
2. **ASLA**: `.env` dosyasını GitHub'a push etme
3. **ASLA**: Google Cloud console'da gösterilen dış IP'yi sürekli log'ta yazdırma
4. **DAIMA**: Sunucu `.env` dosyasının izinlerini 600 yap (`chmod 600 .env`)
5. **DAIMA**: Üretim ortamında `DEBUG=False` olduğunu kontrol et

## 📝 NOTLAR

- `.env` dosyası **sadece sunucu'da** olmalı
- `.env.example` **GitHub'da** olmalı
- İki gitmiş kombinasyon **ASLA** olmamalı
- Test etmeden sunucuya gitme!

---

**Tüm kontroller tamam? Güvenle push edin!** ✅
