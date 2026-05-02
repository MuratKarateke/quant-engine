#!/bin/bash

# ═══════════════════════════════════════════════════════════════════════════════
# 🚀 GOOGLE CLOUD SUNUCUSU KURULUM SCRIPT'İ
# ═══════════════════════════════════════════════════════════════════════════════
# 
# Kullanım:
#   chmod +x setup_server.sh
#   ./setup_server.sh
#
# Bu script:
# ✅ Python ve pip yüklü mü kontrol eder
# ✅ Virtual environment oluşturur
# ✅ Dependencies yükler
# ✅ .env dosyasını kontrol eder
# ✅ API'yi başlatmaya hazırlar

set -e  # Herhangi bir hata oluşursa durdur

echo "╔═══════════════════════════════════════════════════════════════════════════════╗"
echo "║          🚀 BORSA ASİSTANI - SUNUCU KURULUM SCRIPT'İ                       ║"
echo "╚═══════════════════════════════════════════════════════════════════════════════╝"

# Renk kodları
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Adım 1: Python Sürümü Kontrol
echo -e "\n${BLUE}[1/5]${NC} Python sürümü kontrol ediliyor..."
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 bulunmadı! Lütfen install edin:${NC}"
    echo "  Ubuntu/Debian: sudo apt-get install python3-dev python3-venv"
    echo "  CentOS: sudo yum install python3-devel"
    exit 1
fi
PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
echo -e "${GREEN}✅ Python ${PYTHON_VERSION} bulundu${NC}"

# Adım 2: Virtual Environment Oluştur
echo -e "\n${BLUE}[2/5]${NC} Virtual environment oluşturuluyor..."
if [ -d "venv" ]; then
    echo -e "${YELLOW}⚠️  venv zaten var, atlaniyor...${NC}"
else
    python3 -m venv venv
    echo -e "${GREEN}✅ Virtual environment oluşturuldu${NC}"
fi

# Adım 3: Virtual Environment Aktif Et
echo -e "\n${BLUE}[3/5]${NC} Virtual environment aktif ediliyor..."
source venv/bin/activate
echo -e "${GREEN}✅ Virtual environment aktif${NC}"

# Adım 4: Dependencies Yükle
echo -e "\n${BLUE}[4/5]${NC} Python dependencies yükleniyor..."
pip install --upgrade pip > /dev/null 2>&1
pip install -r requirements.txt
echo -e "${GREEN}✅ Dependencies yüklendi${NC}"

# Adım 5: .env Dosyası Kontrol
echo -e "\n${BLUE}[5/5]${NC} .env dosyası kontrol ediliyor..."
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠️  .env dosyası bulunmadı!${NC}"
    echo ""
    echo -e "${YELLOW}ÖNEMLI: Sunucuda .env dosyasını manual oluşturmalısın!${NC}"
    echo ""
    echo "Aşağıdaki komutu çalıştır:"
    echo "  nano .env"
    echo ""
    echo "Ve .env.example dosyasındaki ayarları Google Cloud sunucun için düzenle:"
    echo ""
    echo "==============================================="
    cat .env.example | head -20
    echo "==============================================="
    echo ""
    echo -e "${YELLOW}⚠️  .env dosyasını oluşturduktan sonra tekrar dene${NC}"
    exit 1
else
    echo -e "${GREEN}✅ .env dosyası bulundu${NC}"
    # .env dosyasının izinlerini kontrol et
    FILE_PERM=$(stat -f "%OLp" .env 2>/dev/null || stat -c "%a" .env 2>/dev/null)
    if [ "$FILE_PERM" != "600" ]; then
        echo -e "${YELLOW}⚠️  .env dosyasının izinleri 600 olması öneriliyor${NC}"
        echo "  Düzeltiliyor..."
        chmod 600 .env
        echo -e "${GREEN}✅ İzinler düzeltildi${NC}"
    fi
fi

echo ""
echo "╔═══════════════════════════════════════════════════════════════════════════════╗"
echo "║                    ✅ KURULUM TAMAMLANDI!                                    ║"
echo "╚═══════════════════════════════════════════════════════════════════════════════╝"
echo ""
echo "🚀 API'yi başlatmak için şunu çalıştır:"
echo ""
echo "  # Eğer daha önce venv'i aktif etmediysen:"
echo "  source venv/bin/activate"
echo ""
echo "  # API'yi başlat:"
echo "  python api.py"
echo ""
echo "  # VEYA uvicorn ile:"
echo "  uvicorn api:app --host 0.0.0.0 --port 8000 --workers 4"
echo ""
echo "✅ API başladıktan sonra, başka bir terminal'de:"
echo "  python worker.py"
echo ""
echo "💡 IP adresini öğren:"
echo "  curl -s https://api.ipify.org"
echo ""
echo "📱 Flutter uygulamasında bu IP:8000 adresini kullan"
echo ""
