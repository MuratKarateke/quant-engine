from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
import yfinance as yf
import pandas_ta as ta
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from database import SessionLocal, HisseAnaliz, Portfoy , SinyalGecmisi # <-- SinyalGecmisi eklendi!
import os
from dotenv import load_dotenv

# ⚙️ .env dosyasını yükle
load_dotenv()

# 🎯 API AYARLARI
app = FastAPI(
    title="SuperAI Pro Terminal API",
    version="1.0.0",
    description="Borsa analiz ve sinyali sağlayan backend API"
)

def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()

def super_defensive_data_pull(hisse_obj, vade):
    if vade == "5y": 
        veri = hisse_obj.history(period="5y", interval="1wk")
    elif vade == "1o": # 1 year ("1y" is sometimes problematic in yfinance so we use 1y)
        veri = hisse_obj.history(period="1y", interval="1d")
    elif vade == "1y": 
        veri = hisse_obj.history(period="1y", interval="1d")
    elif vade == "1d": 
        veri = hisse_obj.history(period="1d", interval="5m", prepost=True)
    elif vade == "1h": 
        # yfinance doesn't easily support exactly 1 hour period, but we can do 1d with 1m interval 
        # and then trim the data in the flutter side or just return the last 60 minutes.
        veri = hisse_obj.history(period="1d", interval="1m", prepost=True)
        if not veri.empty:
            veri = veri.tail(60) # Last 60 minutes = 1 hour
    else: 
        # Fallback (orta)
        veri = hisse_obj.history(period="1mo", interval="30m", prepost=True)
        
    if not veri.empty:
        veri = veri.dropna()
        veri = veri[veri['Volume'] > 0]
    return veri

@app.get("/piyasa")
def tam_piyasa_taramasi(db: Session = Depends(get_db)):
    hisseler = db.query(HisseAnaliz).all()
    return {"sonuclar": [{"hisse": h.hisse_kodu, "fiyat": h.fiyat, "rsi": h.rsi, "risk_seviyesi": h.risk_seviyesi, "karar": h.karar, "zarar_kes": h.zarar_kes, "kar_al": h.kar_al, "genc_hisse": h.genc_hisse or False, "borsa": h.borsa or "BIST"} for h in hisseler]}

# === YENİ: GARANTİLİ FIRSAT RADARI ===
@app.get("/radar")
def radar_taramasi(db: Session = Depends(get_db)):
    # 1. ÖNCE "🚀 POTANSİYEL" damgası yiyen gerçek roketleri ara
    roket_hisseler = db.query(HisseAnaliz)\
                       .filter(HisseAnaliz.karar.like('%🚀%'))\
                       .order_by(HisseAnaliz.puan.desc())\
                       .limit(15)\
                       .all()
    
    # 2. Eğer piyasada şu an roket formasyonu YKOSA (veya çok azsa), 
    # boş ekran göstermek yerine en yüksek puanlı (AL veren) hisseleri ekle!
    if len(roket_hisseler) < 10:
        yedek_hisseler = db.query(HisseAnaliz)\
                           .filter(~HisseAnaliz.karar.like('%🚀%'))\
                           .filter(HisseAnaliz.puan >= 55)\
                           .order_by(HisseAnaliz.puan.desc())\
                           .limit(15 - len(roket_hisseler))\
                           .all()
        roket_hisseler.extend(yedek_hisseler)
        
    # Her ihtimale karşı listeyi tekrar puana göre sırala
    roket_hisseler = sorted(roket_hisseler, key=lambda x: x.puan, reverse=True)

    return {"sonuclar": [{"hisse": h.hisse_kodu, "fiyat": h.fiyat, "rsi": h.rsi, "risk_seviyesi": h.risk_seviyesi, "karar": h.karar, "zarar_kes": h.zarar_kes, "kar_al": h.kar_al, "puan": h.puan, "genc_hisse": h.genc_hisse or False, "borsa": h.borsa or "BIST"} for h in roket_hisseler]}
# ====================================

@app.get("/portfoy")
def portfoy_getir(db: Session = Depends(get_db)):
    favoriler = db.query(Portfoy).all()
    favori_kodlari = [f.hisse_kodu for f in favoriler]
    hisseler = db.query(HisseAnaliz).filter(HisseAnaliz.hisse_kodu.in_(favori_kodlari)).all()
    kayitli_kodlar = [h.hisse_kodu for h in hisseler]
    sonuclar = [{"hisse": h.hisse_kodu, "fiyat": h.fiyat, "rsi": h.rsi, "risk_seviyesi": h.risk_seviyesi, "karar": h.karar, "zarar_kes": h.zarar_kes, "kar_al": h.kar_al, "genc_hisse": h.genc_hisse or False, "borsa": h.borsa or "BIST"} for h in hisseler]
    for kod in favori_kodlari:
        if kod not in kayitli_kodlar:
            sonuclar.append({"hisse": kod, "fiyat": 0.0, "rsi": 0.0, "risk_seviyesi": "N/A", "karar": "GÜNCELLENİYOR", "zarar_kes": 0.0, "kar_al": 0.0, "genc_hisse": False, "borsa": "BIST"})
    return {"sonuclar": sonuclar, "favori_kodlari": favori_kodlari}

@app.get("/karne")
def karne_getir(db: Session = Depends(get_db)):
    # Sinyal geçmişini getir (Profit Maximizer alanları dahil)
    sinyaller = db.query(SinyalGecmisi).order_by(SinyalGecmisi.sinyal_tarihi.desc()).limit(100).all()
    sonuclar = []
    
    for s in sinyaller:
        sonuclar.append({
            "hisse": s.hisse_kodu,
            "tarih": s.sinyal_tarihi.strftime("%d/%m/%Y %H:%M"),
            "giris": s.giris_fiyati,
            "hedef": s.hedef_fiyat,
            "stop": s.stop_fiyat,
            "kapanis_tarihi": s.kapanis_tarihi.strftime("%d/%m/%Y %H:%M") if s.kapanis_tarihi else None,
            "karar": s.karar,
            "durum": s.durum,
            "max_getiri": s.max_getiri_yuzdesi,
            "tp1": s.tp1,
            "tp2": s.tp2,
            "initial_stop": s.initial_stop,
            "current_stop": s.current_stop,
            "highest_high": s.highest_high,
            "mfe_percent": s.mfe_percent
        })
        
    return {"sonuclar": sonuclar}

@app.get("/portfoy/kontrol/{hisse_kodu}")
def portfoy_kontrol(hisse_kodu: str, db: Session = Depends(get_db)):
    mevcut = db.query(Portfoy).filter(Portfoy.hisse_kodu == hisse_kodu.upper()).first()
    return {"favori": mevcut is not None}

@app.post("/portfoy/{hisse_kodu}")
def portfoye_ekle(hisse_kodu: str, db: Session = Depends(get_db)):
    hisse_kodu = hisse_kodu.upper()
    mevcut = db.query(Portfoy).filter(Portfoy.hisse_kodu == hisse_kodu).first()
    if not mevcut:
        yeni_favori = Portfoy(hisse_kodu=hisse_kodu)
        db.add(yeni_favori)
        db.commit()
    return {"mesaj": f"{hisse_kodu} portföye eklendi."}

@app.delete("/portfoy/{hisse_kodu}")
def portfoyden_cikar(hisse_kodu: str, db: Session = Depends(get_db)):
    hisse_kodu = hisse_kodu.upper()
    mevcut = db.query(Portfoy).filter(Portfoy.hisse_kodu == hisse_kodu).first()
    if mevcut:
        db.delete(mevcut)
        db.commit()
    return {"mesaj": f"{hisse_kodu} portföyden çıkarıldı."}

@app.get("/canli_detay/{hisse_kodu}")
def canli_hisse_detayi(hisse_kodu: str, vade: str = "orta"):
    try:
        now = datetime.now()
        market_closed = now.weekday() >= 5 or now.hour < 10 or (now.hour >= 18 and now.minute > 15)

        symbol = hisse_kodu.upper()
        
        import contextlib
        import io
        import sys
        
        f = io.StringIO()
        with contextlib.redirect_stderr(f):
            hisse = yf.Ticker(symbol)
            veri = super_defensive_data_pull(hisse, vade)
            
            is_bist = False
            if veri.empty:
                symbol = f"{hisse_kodu.upper()}.IS"
                hisse = yf.Ticker(symbol)
                veri = super_defensive_data_pull(hisse, vade)
                is_bist = True
            else:
                is_bist = symbol.endswith(".IS")
            
        if veri.empty: return {"hata": "Hisse bulunamadı."}

        info = hisse.info
        para_birimi = "₺" if is_bist else "$"
        if info.get("currency") == "USD": para_birimi = "$"
        elif info.get("currency") == "TRY": para_birimi = "₺"

        temel_veriler = {
            "fk": round(info.get('trailingPE', 0), 2) if info.get('trailingPE') else 0,
            "pddd": round(info.get('priceToBook', 0), 2) if info.get('priceToBook') else 0,
            "net_kar_marji": round(info.get('profitMargins', 0) * 100, 2) if info.get('profitMargins') else 0,
            "borc_durumu": "DÜŞÜK" if info.get('debtToEquity', 100) < 100 else "YÜKSEK"
        }

        ta_data = veri.copy()
        try:
            ta_data.ta.macd(append=True); ta_data.ta.rsi(length=14, append=True)
            ta_data.ta.bbands(length=20, std=2, append=True); ta_data.ta.adx(length=14, append=True)
            ta_data.ta.obv(append=True); ta_data.ta.atr(length=14, append=True)
            ta_data.ta.vwap(append=True)
        except: pass

        ta_data = ta_data.dropna()
        if ta_data.empty: return {"hata": "İndikatör hesaplaması için yeterli veri yok."}
        
        son_gun = ta_data.iloc[-1]
        close_val = son_gun['Close']

        try:
            hizli_veri = hisse.history(period="1d", interval="1m", prepost=True)
            if not hizli_veri.empty:
                guncel_1m_fiyat = hizli_veri['Close'].iloc[-1]
                close_val = guncel_1m_fiyat
        except: pass

        puan = 0
        puanDetay = {}

        obv_lag5 = ta_data['OBV'].iloc[-6] if 'OBV' in ta_data.columns and len(ta_data) > 6 else 0
        if 'OBV' in ta_data.columns and pd.notna(son_gun['OBV']):
            if son_gun['OBV'] > obv_lag5: puan += 15; puanDetay['Para_Akisi'] = "GİRİŞ VAR (+15)"
            else: puanDetay['Para_Akisi'] = "ÇIKIŞ/NÖTR (+0)"
        else: puanDetay['Para_Akisi'] = "NÖTR (+0)"

        vwap_col = next((c for c in ta_data.columns if "VWAP" in c), None)
        if vwap_col and pd.notna(son_gun[vwap_col]):
            if close_val > son_gun[vwap_col]: puan += 20; puanDetay['Kurumsal_Durum'] = "VWAP ÜSTÜ (GÜÇLÜ) (+20)"
            else: puanDetay['Kurumsal_Durum'] = "VWAP ALTI (BASKI) (+0)"
        else: puanDetay['Kurumsal_Durum'] = "NÖTR (+0)"

        macd_col = next((c for c in ta_data.columns if "MACD_12" in c), None)
        macds_col = next((c for c in ta_data.columns if "MACDs_12" in c), None)
        macdh_col = next((c for c in ta_data.columns if "MACDh_12" in c), None)
        
        if macd_col and macds_col and pd.notna(son_gun[macd_col]):
            if son_gun[macd_col] > son_gun[macds_col]:
                if macdh_col and pd.notna(son_gun[macdh_col]) and son_gun[macdh_col] > 0 and son_gun[macdh_col] > ta_data[macdh_col].iloc[-2]:
                    puan += 15; puanDetay['Trend'] = "SERT YUKARI (+15)"
                else: puan += 10; puanDetay['Trend'] = "YUKARI (YORULAN) (+10)"
            else: puanDetay['Trend'] = "AŞAĞI (+0)"
        else: puanDetay['Trend'] = "NÖTR (+0)"

        rsi_val = son_gun.get('RSI_14', 50)
        if pd.notna(rsi_val):
            if rsi_val < 30: puan += 15; puanDetay['Momentum'] = "AŞIRI DİP (+15)"
            elif rsi_val < 45: puan += 10; puanDetay['Momentum'] = "UCUZ (+10)"
            elif rsi_val > 75: puan -= 15; puanDetay['Momentum'] = "AŞIRI ŞİŞKİN (-15)"
            else: puanDetay['Momentum'] = "NÖTR (+0)"
        else: puanDetay['Momentum'] = "N/A"

        adx_col = next((c for c in ta_data.columns if "ADX_14" in c), None)
        if adx_col and pd.notna(son_gun[adx_col]):
            if son_gun[adx_col] > 30: puan += 10; puanDetay['Trend_Gucu'] = "ÇOK GÜÇLÜ (+10)"
            elif son_gun[adx_col] > 20: puan += 5; puanDetay['Trend_Gucu'] = "ORTA GÜÇLÜ (+5)"
            else: puanDetay['Trend_Gucu'] = "YATAY (+0)"
        else: puanDetay['Trend_Gucu'] = "N/A"

        bbl_col = next((c for c in ta_data.columns if c.startswith("BBL_")), None)
        bbm_col = next((c for c in ta_data.columns if c.startswith("BBM_")), None)
        bbu_col = next((c for c in ta_data.columns if c.startswith("BBU_")), None)

        if bbl_col and pd.notna(son_gun[bbl_col]):
            if close_val < son_gun[bbl_col]: puan += 10; puanDetay['Fiyat_Konumu'] = "DİPTE (+10)"
            elif bbm_col and close_val < son_gun[bbm_col]: puan += 5; puanDetay['Fiyat_Konumu'] = "UCUZ (+5)"
            elif bbu_col and close_val > son_gun[bbu_col]: puan -= 10; puanDetay['Fiyat_Konumu'] = "ZİRVEDE (-10)"
            else: puanDetay['Fiyat_Konumu'] = "NÖTR (+0)"
        else: puanDetay['Fiyat_Konumu'] = "N/A"

        div_text = "YOK (+0)"
        if len(ta_data) >= 30 and 'RSI_14' in ta_data.columns:
            try:
                w1 = ta_data.iloc[-30:-15]
                w2 = ta_data.iloc[-15:]
                idx_min1, idx_min2 = w1['Low'].idxmin(), w2['Low'].idxmin()
                min_p1, min_p2 = w1.loc[idx_min1, 'Low'], w2.loc[idx_min2, 'Low']
                rsi_min1, rsi_min2 = w1.loc[idx_min1, 'RSI_14'], w2.loc[idx_min2, 'RSI_14']
                idx_max1, idx_max2 = w1['High'].idxmax(), w2['High'].idxmax()
                max_p1, max_p2 = w1.loc[idx_max1, 'High'], w2.loc[idx_max2, 'High']
                rsi_max1, rsi_max2 = w1.loc[idx_max1, 'RSI_14'], w2.loc[idx_max2, 'RSI_14']
                
                if min_p2 < min_p1 and rsi_min2 > rsi_min1 and rsi_min2 < 50:
                    puan += 25; div_text = "POZİTİF (GİZLİ AL) (+25)"
                elif max_p2 > max_p1 and rsi_max2 < rsi_max1 and rsi_max2 > 50:
                    puan -= 25; div_text = "NEGATİF (GİZLİ SAT) (-25)"
            except: pass
        
        puanDetay['RSI_Uyumsuzlugu'] = div_text
        puan = max(0, min(100, puan))

        recent_high = ta_data['High'].tail(90).max() 
        recent_low = ta_data['Low'].tail(90).min()
        fibo_fark = recent_high - recent_low
        pivot = round(float(recent_low + (fibo_fark * 0.5)), 2)
        direnc = round(float(recent_high), 2)
        destek = round(float(recent_low), 2)

        otomatik_cizgiler = [
            {"deger": direnc, "isim": "Ana Direnç (Tepe)", "renk": "kirmizi"},
            {"deger": destek, "isim": "Ana Destek (Dip)", "renk": "yesil"},
            {"deger": pivot, "isim": "Pivot (Karar Noktası)", "renk": "mavi"}
        ]

        if puan >= 50:
            kar_al = round(float(recent_high + (fibo_fark * 0.272)), 2)
            zarar_kes = round(float(recent_high - (fibo_fark * 0.382)), 2)
            if zarar_kes >= close_val: zarar_kes = round(float(close_val * 0.97), 2)
            if kar_al <= close_val: kar_al = round(float(close_val * 1.05), 2)
        else:
            kar_al = round(float(recent_low + (fibo_fark * 0.618)), 2)
            zarar_kes = round(float(recent_low - (fibo_fark * 0.272)), 2)
            if zarar_kes >= close_val: zarar_kes = round(float(close_val * 0.95), 2)
            if kar_al <= close_val: kar_al = round(float(close_val * 1.02), 2)

        ai_yorum_dict = {"genel": "", "pozitif": "", "negatif": "", "ekstra": ""}
        fiyat_durumu = round(float(close_val), 2)
        
        genel = f"Hisse şu an {para_birimi}{fiyat_durumu} seviyesinde işlem görmektedir. "
        if close_val >= pivot: genel += f"Fiyat, {para_birimi}{pivot} seviyesindeki karar (pivot) noktasının üzerinde tutunarak güçlü bir duruş sergilemektedir."
        else: genel += f"Fiyat, {para_birimi}{pivot} seviyesindeki karar (pivot) noktasının altında kalarak satış baskısı hissetmektedir."
        ai_yorum_dict["genel"] = genel

        pozitif = ""
        if close_val < direnc: pozitif += f"Alım dalgasının güçlenmesi durumunda öncelikli hedef {para_birimi}{direnc} ana direnç seviyesidir. Bu direncin hacimli kırılması formasyon hedefini {para_birimi}{kar_al} seviyesine taşıyacaktır."
        else: pozitif += f"Hisse tarihi zirvelerinde fiyatlanmaktadır. Yükseliş momentumunun devamı halinde orta vadeli formasyon katlama hedefi {para_birimi}{kar_al} olarak izlenebilir."
        ai_yorum_dict["pozitif"] = pozitif
            
        negatif = ""
        if close_val > destek: negatif += f"Olası kâr satışlarında {para_birimi}{pivot} seviyesi ilk destektir. Bu bölgenin kırılması satışları {para_birimi}{destek} ana dip seviyesine kadar derinleştirebilir. Grafik formasyonunun iptal olacağı kesin zarar kes (stop) noktası {para_birimi}{zarar_kes} seviyesidir."
        else: negatif += f"Hisse ana desteğini kaybetmiştir. Mevcut düşüş eğilimine karşı korunmak adına {para_birimi}{zarar_kes} seviyesi kesin stop-loss (zarar kes) noktası olarak değerlendirilmelidir."
        ai_yorum_dict["negatif"] = negatif

        if "POZİTİF" in div_text: ai_yorum_dict["ekstra"] = "Göstergelerde 'Pozitif Uyumsuzluk' tespit edildi. Fiyat yeni dipler oluşturmasına rağmen momentum güçleniyor. Bu bir ayı tuzağı olabilir, yukarı yönlü sert tepki ihtimali mevcuttur."
        elif "NEGATİF" in div_text: ai_yorum_dict["ekstra"] = "Göstergelerde 'Negatif Uyumsuzluk' tespit edildi. Fiyat yeni tepeler yapmasına rağmen alım gücü azalıyor. Boğa tuzağı riskine karşı kâr realizasyonu değerlendirilebilir."

        # Vadeye göre gösterilecek mum sayısını ayarla
        if vade == "5y": mum_sayisi = 260
        elif vade == "1y": mum_sayisi = 260
        elif vade == "1d": mum_sayisi = 120
        elif vade == "1h": mum_sayisi = 60
        else: mum_sayisi = 60
            
        display_data = ta_data.tail(mum_sayisi)
        grafik_verisi = []
        for index, row in display_data.iterrows():
            hour = index.hour
            minute = index.minute
            time_val = hour + (minute / 60.0)
            session_type = "regular"

            if is_bist:
                if time_val < 9.9: session_type = "pre"
                elif time_val >= 18.16: session_type = "post"
            else:
                if time_val < 9.5: session_type = "pre"
                elif time_val >= 16.0: session_type = "post"

            if vade == "uzun": session_type = "regular"

            c_val = round(float(row['Close']), 2)
            h_val = round(float(row['High']), 2)
            l_val = round(float(row['Low']), 2)
            
            if index == display_data.index[-1]:
                c_val = round(float(close_val), 2)
                h_val = max(h_val, c_val)
                l_val = min(l_val, c_val)

            grafik_verisi.append({"x": index.timestamp() * 1000, "o": round(float(row['Open']), 2), "h": h_val, "l": l_val, "c": c_val, "v": round(float(row['Volume']), 0), "session": session_type})

        tahmin_verisi = []
        tahmin_verisi.append({"x": display_data.index[-1].timestamp() * 1000, "y": round(float(close_val), 2), "zaman": "ŞİMDİ"})

        atr_col = next((c for c in ta_data.columns if "ATRr_14" in c), None)
        oynaklik = son_gun[atr_col] if atr_col and pd.notna(son_gun[atr_col]) else close_val * 0.015
        egilim = (puan - 50) / 50 
        
        for i in range(1, 11):
            kavis_carpani = np.sqrt(i) * 1.2
            t_fiyat = close_val + (oynaklik * kavis_carpani * egilim)
            gelecek_zaman = display_data.index[-1] + timedelta(minutes=15*i if vade=="kisa" else 30*i if vade=="orta" else 1440*i)
            tahmin_verisi.append({"x": gelecek_zaman.timestamp() * 1000, "y": round(float(t_fiyat), 2), "zaman": f"+{i} periyot"})

        return {
            "hisse": symbol, 
            "anlik_fiyat": round(float(close_val), 2),
            "para_birimi": para_birimi,
            "anlik_rsi": round(float(rsi_val), 2), 
            "puan": int(puan),
            "karar": "GUCLU AL" if puan >= 80 else "AL" if puan >= 60 else "BEKLE",
            "risk_seviyesi": "DUSUK" if puan > 50 else "ORTA",
            "market_closed": market_closed, 
            "son_guncelleme": son_gun.name.strftime('%d/%m %H:%M'),
            "temel_veriler": temel_veriler,
            "grafik_verisi": grafik_verisi, 
            "tahmin_verisi": tahmin_verisi, 
            "otomatik_cizgiler": otomatik_cizgiler, 
            "ai_yorum": ai_yorum_dict, 
            "zarar_kes": zarar_kes, "kar_al": kar_al,
            "puan_detay": puanDetay
        }
    except Exception as e: return {"hata": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)