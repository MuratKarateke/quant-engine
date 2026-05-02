import yfinance as yf
import pandas_ta as ta
import pandas as pd

# 1. Hisseyi Belirle ve Veriyi Çek
hisse_kodu = "THYAO.IS"
print(f"--- {hisse_kodu} Verileri Çekiliyor... Lütfen bekleyin ---")

hisse = yf.Ticker(hisse_kodu)
veri = hisse.history(period="6mo")

# 2. İndikatörleri Hesapla (RSI, MACD ve ATR)
veri.ta.rsi(length=14, append=True)
veri.ta.macd(append=True)
veri.ta.atr(length=14, append=True) # ATR: Günlük dalgalanma (TL cinsinden)

# 3. Risk Hesaplama (Günlük Yüzdelik Değişimlerin Sapması)
veri['Getiri'] = veri['Close'].pct_change()
# Son 30 günün ortalama oynaklığını (yüzde olarak) hesaplıyoruz
gunluk_oynaklik = veri['Getiri'].tail(30).std() * 100 

# 4. Son Günün Verilerini Al
son_gun = veri.iloc[-1]
guncel_fiyat = float(son_gun['Close'])
guncel_rsi = float(son_gun['RSI_14'])
macd_cizgisi = float(son_gun['MACD_12_26_9'])
sinyal_cizgisi = float(son_gun['MACDs_12_26_9'])
guncel_atr = float(son_gun['ATRr_14'])

# 5. Risk Seviyesini Belirle
if gunluk_oynaklik < 1.5:
    risk_seviyesi = "🟢 DÜŞÜK (Güvenli Liman)"
elif gunluk_oynaklik < 3.0:
    risk_seviyesi = "🟡 ORTA (Dengeli)"
else:
    risk_seviyesi = "🔴 YÜKSEK (Agresif / Çok Hareketli)"

# 6. Zarar Kes ve Kâr Al Seviyelerini Hesapla
# Kural: ATR'nin 1.5 katı kadar zarara tahammül et, 3 katı kadar kâr hedefle
zarar_kes_fiyati = guncel_fiyat - (1.5 * guncel_atr)
kar_al_fiyati = guncel_fiyat + (3.0 * guncel_atr)

# ----- EKRAN ÇIKTISI -----
print(f"\n📊 --- ÖZET RAPOR ---")
print(f"Güncel Fiyat: {guncel_fiyat:.2f} TL")
print(f"Risk Seviyesi: {risk_seviyesi} (Günlük Oynaklık: %{gunluk_oynaklik:.2f})")
print(f"RSI: {guncel_rsi:.2f} | MACD: {macd_cizgisi:.2f}")

print("\n🎯 --- İŞLEM PLANI ---")
print(f"Olası Zarar Kes (Stop-Loss): {zarar_kes_fiyati:.2f} TL")
print(f"Olası Kâr Al (Take-Profit):  {kar_al_fiyati:.2f} TL")

print("\n🤖 --- ASİSTANIN KARARI ---")
if guncel_rsi < 45 and macd_cizgisi > sinyal_cizgisi:
    print("🟢 GÜÇLÜ AL: Hisse uygun fiyatta ve trend yukarı yönlü!")
elif guncel_rsi > 70 and macd_cizgisi < sinyal_cizgisi:
    print("🔴 GÜÇLÜ SAT: Hisse aşırı alım bölgesinde, düşüş trendi başlamış!")
elif macd_cizgisi > sinyal_cizgisi:
    print("🟡 YÖN YUKARI: Trend pozitif. Elde tutulabilir.")
elif macd_cizgisi < sinyal_cizgisi:
    print("🟠 YÖN AŞAĞI: Trend negatif. Beklemede kalınmalı.")
else:
    print("⏳ BEKLE: Piyasa kararsız, net bir yön görünmüyor.")
print("-" * 40)