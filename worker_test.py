import yfinance as yf
import pandas_ta as ta
import pandas as pd
import numpy as np
import time
import concurrent.futures
from datetime import datetime
from database import SessionLocal, HisseAnaliz, SinyalGecmisi

import requests

# --- DİNAMİK BİST HİSSE LİSTESİ (Artık manuel ekleme yok!) ---
# İş Yatırım'dan anlık güncel liste çekilecek.

GLOBAL_HISSELER = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "TSLA", "META", "BRK-B", "TSM", "UNH",
    "V", "JNJ", "WMT", "JPM", "XOM", "MA", "PG", "AVGO", "HD", "CVX", "MRK",
    "COST", "PEP", "ABBV", "KO", "ADBE", "CSCO", "MCD", "TMO", "CRM", "PFE", "NFLX",
    "AMD", "INTC", "QCOM", "TXN", "AMAT", "IBM", "BA", "COIN", "PLTR", "MSTR", "UBER",
    "DIS", "GE", "F", "GM", "INTU", "CAT", "NKE", "VZ", "T", "ABNB", "SPOT",
    "SNOW", "ROKU", "PYPL", "HOOD", "RBLX", "SOFI", "PINS", "SNAP", "BABA",
    "JD", "PDD", "BIDU", "NIO", "XPEV", "LI", "BILI", "TME", "NTES", "ZM", "DOCU",
    "CRWD", "DDOG", "NET", "OKTA", "ZS", "PANW", "FTNT", "CHKP", "MDB", "NOW",
    "TEAM", "WDAY", "VEEV", "SHOP", "SE", "MELI", "CPNG", "GLBE", "AFRM", "UPST",
    "LCID", "RIVN", "PSNY", "QS", "CHPT", "BLNK", "RUN", "ENPH", "SEDG",
    "FSLR", "SPWR", "PLUG", "FCEL", "BLDP", "BE", "NVAX", "MRNA", "BNTX", 
    "GILD", "REGN", "VRTX", "BIIB", "ILMN", "CRSP", "NTLA", "EDIT", "BEAM",
    "EXAS", "TDOC", "ALGN", "ISRG", "MDT", "SYK", "BSX", "EW", "ZBH", "ABT", "DHR",
    "IQV", "A", "MTD", "WAT", "CRL", "BIO", "TECH", "BR", "WST", "CVS", 
    "CNC", "HUM", "ELV", "CI", "MOH", "CIG", "E", "BP", "SHEL", "TTE", "COP", "EOG", 
    "OXY", "MPC", "VLO", "PSX", "SLB", "HAL", "BKR", "FTI", "NOV", "RIG", "VALE",
    "RIO", "BHP", "FCX", "SCCO", "NEM", "GOLD", "AEM", "KGC", "AU", "GFI",
    "SBSW", "PAAS", "HL", "CDE", "AG", "FSM", "EXK", "WU", "SYF", "COF", "ALL", 
    "TRV", "PGR", "CB", "AON", "AJG", "BRO", "WTW", "AIG", "PRU", "MET", "MFC", "SLF", 
    "LNC", "PFG", "C", "BAC", "WFC", "GS", "MS", "SCHW", "BLK", "BX", "KKR", "APO",
    "CG", "ARES", "OWL", "STEP", "HLI", "LPLA", "SF", "RJF", "STT", "BK", "NTRS",
    "AMP", "TROW", "BEN", "IVZ", "AMG", "JHG", "FHI", "CNS", "VLY", "FNB", "TCBI", 
    "BOKF", "CFR", "PB", "HOMB", "ONB", "UBSI", "FHB", "WAL", "ZION", "FITB", "HBAN", 
    "KEY", "RF", "CFG", "GPN", "FIS", "FISV", "JKHY", "PAYX", "ADP", "PCTY", "PAYC", 
    "TYL", "TRMB"
]

def hisse_analiz_et(symbol):
    try:
        # SAHTE TARAYICIYI (REQUESTS) ÇÖPE ATTIK. DİREKT YFINANCE KULLANIYORUZ.
        import contextlib
        import io
        import sys
        
        # yfinance history hatalarını (possibly delisted) gizle
        f = io.StringIO()
        with contextlib.redirect_stderr(f):
            veri = hisse.history(period="1mo", interval="30m")
            
            # Eğer 30m boş dönerse (UMPAS, ISATR gibi sığ tahtalar), 1d ile tekrar dene
            if veri.empty:
                veri = hisse.history(period="1mo", interval="1d")
                
            # GERÇEK YAŞ TESPİTİ (Sığ tahtaları yeni arz sanmamak için)
            # 1 yıllık günlük (1d) veriyi çekip hissenin asıl yaşını buluyoruz
            is_truly_young = False
            gercek_mum_sayisi = 0
            if not veri.empty:
                veri_1y_1d = hisse.history(period="1y", interval="1d")
                gercek_mum_sayisi = len(veri_1y_1d)
                is_truly_young = gercek_mum_sayisi < 120
            
        if veri.empty: 
            # HAYALET HİSSE: Ne 30m ne 1d mum verisi yok ama güncel fiyatı çekmeyi dene
            borsa = "BIST" if symbol.endswith(".IS") else "US"
            try:
                guncel_fiyat = round(float(hisse.fast_info.get('lastPrice', 0) or hisse.fast_info.get('previousClose', 0)), 2)
            except:
                guncel_fiyat = 0.0
            return {
                "hisse_kodu": symbol.replace('.IS', ''),
                "fiyat": guncel_fiyat, "rsi": 0.0, "puan": 0,
                "karar": "YENİ ARZ ⏳", "risk_seviyesi": "BELİRSİZ",
                "zarar_kes": 0.0, "kar_al": 0.0,
                "genc_hisse": True, "borsa": borsa
            }
            
        veri = veri.dropna()
        veri = veri[veri['Volume'] > 0]
        borsa = "BIST" if symbol.endswith(".IS") else "US"
        
        if gercek_mum_sayisi < 20:
            # GERÇEK HAYALET HİSSE: Günlük mum bile 20'den az
            son_fiyat = round(float(veri['Close'].iloc[-1]), 2) if len(veri) > 0 else 0.0
            return {
                "hisse_kodu": symbol.replace('.IS', ''),
                "fiyat": son_fiyat, "rsi": 0.0, "puan": 0,
                "karar": "YENİ ARZ ⏳", "risk_seviyesi": "BELİRSİZ",
                "zarar_kes": 0.0, "kar_al": 0.0,
                "genc_hisse": True, "borsa": borsa
            }

        # Sadece GERÇEKTEN 120 günlük işlem görmemiş olanlar Genç Hisse sayılır
        if is_truly_young:
            return genc_hisse_analiz_et(symbol, veri, borsa)

        # Klasik teknik analiz kısmı
        if len(veri) < 20: 
            # İndikatör hesabı için çok az 30m veri var (sığ tahta), günlük veriyle (veri_1y_1d) analize devam et
            if gercek_mum_sayisi >= 20: 
                veri = veri_1y_1d.dropna()
                veri = veri[veri['Volume'] > 0]
                print(f"DEBUG: {symbol} falls back to 1y_1d. len={len(veri)}")
            else:
                print(f"DEBUG: {symbol} drops at gercek_mum_sayisi < 20. count={gercek_mum_sayisi}")
                return None 

        ta_data = veri.copy()
        if symbol == 'KSTUR.IS': print(f"DEBUG: {symbol} copies ta_data. len={len(ta_data)}")
        ta_data.ta.macd(append=True)
        ta_data.ta.rsi(length=14, append=True)
        ta_data.ta.bbands(length=20, std=2, append=True)
        ta_data.ta.kc(length=20, scalar=1.5, append=True) 
        ta_data.ta.adx(length=14, append=True)
        ta_data.ta.obv(append=True)
        ta_data.ta.vwap(append=True)
        
        ta_data = ta_data.dropna()
        if ta_data.empty: return None

        son_gun = ta_data.iloc[-1]
        close_val = float(son_gun['Close'])
        rsi_val = float(son_gun.get('RSI_14', 50))
        
        temel_puan = 0
        obv_lag5 = ta_data['OBV'].iloc[-6] if 'OBV' in ta_data.columns and len(ta_data) > 6 else 0
        if 'OBV' in ta_data.columns and pd.notna(son_gun['OBV']) and son_gun['OBV'] > obv_lag5: temel_puan += 10
        vwap_col = next((c for c in ta_data.columns if "VWAP" in c), None)
        if vwap_col and pd.notna(son_gun[vwap_col]) and close_val > son_gun[vwap_col]: temel_puan += 15
        macd_col = next((c for c in ta_data.columns if "MACD_12" in c), None)
        macds_col = next((c for c in ta_data.columns if "MACDs_12" in c), None)
        macdh_col = next((c for c in ta_data.columns if "MACDh_12" in c), None)
        if macd_col and macds_col and pd.notna(son_gun[macd_col]) and son_gun[macd_col] > son_gun[macds_col]: temel_puan += 10
        if pd.notna(rsi_val):
            if rsi_val < 35: temel_puan += 10
            elif rsi_val > 70: temel_puan -= 15
        adx_col = next((c for c in ta_data.columns if "ADX_14" in c), None)
        if adx_col and pd.notna(son_gun[adx_col]) and son_gun[adx_col] > 25: temel_puan += 5
        bbl_col = next((c for c in ta_data.columns if c.startswith("BBL_")), None)
        bbu_col = next((c for c in ta_data.columns if c.startswith("BBU_")), None)
        kcu_col = next((c for c in ta_data.columns if "KCU" in c), None)
        kcl_col = next((c for c in ta_data.columns if "KCL" in c), None)
        if len(ta_data) >= 30 and 'RSI_14' in ta_data.columns:
            w1 = ta_data.iloc[-30:-15]
            w2 = ta_data.iloc[-15:]
            idx_min1, idx_min2 = w1['Low'].idxmin(), w2['Low'].idxmin()
            if w2.loc[idx_min2, 'Low'] < w1.loc[idx_min1, 'Low'] and w2.loc[idx_min2, 'RSI_14'] > w1.loc[idx_min1, 'RSI_14']: temel_puan += 10

        firsat_puani = 0
        if bbu_col and bbl_col and kcu_col and kcl_col:
            bb_genislik = son_gun[bbu_col] - son_gun[bbl_col]
            kc_genislik = son_gun[kcu_col] - son_gun[kcl_col]
            if kc_genislik > 0:
                oran = bb_genislik / kc_genislik
                if oran < 1.2:
                    firsat_puani += int((1.2 - oran) * 100)
                    firsat_puani = min(30, max(10, firsat_puani)) 
                    if macdh_col and pd.notna(son_gun[macdh_col]) and son_gun[macdh_col] > 0:
                        firsat_puani = min(40, firsat_puani + 10)

        toplam_puan = min(100, temel_puan + firsat_puani)
        
        if firsat_puani >= 15 and toplam_puan >= 65: karar = "🚀 POTANSİYEL PATLAMA"
        elif toplam_puan >= 60: karar = "AL"
        elif toplam_puan <= 30: karar = "SAT"
        else: karar = "BEKLE"

        recent_high = float(ta_data['High'].tail(90).max())
        recent_low = float(ta_data['Low'].tail(90).min())
        fibo_fark = recent_high - recent_low
        if toplam_puan >= 50:
            kar_al = round(recent_high + (fibo_fark * 0.272), 2)
            zarar_kes = round(recent_high - (fibo_fark * 0.382), 2)
            if zarar_kes >= close_val: zarar_kes = round(close_val * 0.97, 2)
            if kar_al <= close_val: kar_al = round(close_val * 1.05, 2)
        else:
            kar_al = round(recent_low + (fibo_fark * 0.618), 2)
            zarar_kes = round(recent_low - (fibo_fark * 0.272), 2)
            if zarar_kes >= close_val: zarar_kes = round(close_val * 0.95, 2)
            if kar_al <= close_val: kar_al = round(close_val * 1.02, 2)

        risk = "DÜŞÜK" if toplam_puan > 50 else "YÜKSEK" if toplam_puan < 30 else "ORTA"

        return {
            "hisse_kodu": symbol.replace('.IS', ''),
            "fiyat": round(close_val, 2), "rsi": round(rsi_val, 2), "puan": int(toplam_puan),
            "karar": karar, "risk_seviyesi": risk, "zarar_kes": zarar_kes, "kar_al": kar_al,
            "genc_hisse": False, "borsa": borsa
        }
    except Exception as e:
        traceback.print_exc()
        return None

# ═══════════════════════════════════════════════════════════════════
#  GENÇ HİSSE QUANT MOTORU — PRICE DISCOVERY ALPHA (20-120 MUM)
# ═══════════════════════════════════════════════════════════════════

def _hesapla_rvi(ta_data):
    """Relative Volume Intensity — her mumun medyan hacme oranı."""
    median_vol = ta_data['Volume'].median()
    if median_vol == 0: median_vol = 1
    ta_data['RVI'] = ta_data['Volume'] / median_vol
    return ta_data

def _hesapla_ais(ta_data):
    """Accumulation Intensity Score — CLV ağırlıklı kümülatif hacim."""
    hl_range = ta_data['High'] - ta_data['Low']
    hl_range = hl_range.replace(0, 1e-10)
    clv = ((ta_data['Close'] - ta_data['Low']) - (ta_data['High'] - ta_data['Close'])) / hl_range
    ta_data['AIS'] = (clv * ta_data['Volume']).cumsum()
    if len(ta_data) >= 10:
        son_10 = ta_data['AIS'].tail(10).values
        slope = np.polyfit(range(10), son_10, 1)[0]
    else:
        slope = 0
    ta_data['AIS_Egim'] = slope
    return ta_data

def _hesapla_ed_atr(ta_data, span=10):
    """Exponential Decay ATR — üstel ağırlıklı True Range."""
    tr = ta_data[['High', 'Low', 'Close']].copy()
    tr['prev_close'] = tr['Close'].shift(1)
    tr['tr'] = tr.apply(lambda r: max(
        r['High'] - r['Low'],
        abs(r['High'] - r['prev_close']) if pd.notna(r['prev_close']) else r['High'] - r['Low'],
        abs(r['Low'] - r['prev_close']) if pd.notna(r['prev_close']) else r['High'] - r['Low']
    ), axis=1)
    ta_data['ED_ATR'] = tr['tr'].ewm(span=span, adjust=False).mean()
    return ta_data

def _hesapla_vcr(ta_data, pencere=5):
    """Volatility Contraction Ratio — range daralma oranı."""
    if len(ta_data) < pencere * 2:
        ta_data['VCR'] = 1.0
        return ta_data
    ta_data['Mum_Range'] = ta_data['High'] - ta_data['Low']
    son_bolum = ta_data['Mum_Range'].tail(pencere).mean()
    onceki_bolum = ta_data['Mum_Range'].iloc[-(pencere*2):-pencere].mean()
    vcr = son_bolum / onceki_bolum if onceki_bolum > 0 else 1.0
    ta_data['VCR'] = vcr
    return ta_data

def _hesapla_ath_proximity(ta_data):
    """ATH'ye yakınlık yüzdesi."""
    ath = ta_data['High'].max()
    son_fiyat = ta_data['Close'].iloc[-1]
    ath_mesafe = ((son_fiyat - ath) / ath) * 100 if ath > 0 else 0
    ta_data['ATH_Proximity'] = round(ath_mesafe, 2)
    return ta_data

def _ipo_base_skoru(ta_data):
    """IPO Base Kalitesi: VCR + ATH + Hacim kurutma. (maks 30)"""
    vcr = ta_data['VCR'].iloc[-1] if 'VCR' in ta_data.columns else 1.0
    ath_prox = ta_data['ATH_Proximity'].iloc[-1] if 'ATH_Proximity' in ta_data.columns else -50
    son_rvi = ta_data['RVI'].tail(5).mean() if 'RVI' in ta_data.columns else 1.0
    puan = 0
    if vcr < 0.4: puan += 12
    elif vcr < 0.6: puan += 9
    elif vcr < 0.8: puan += 5
    if ath_prox > -5: puan += 10
    elif ath_prox > -15: puan += 7
    elif ath_prox > -25: puan += 3
    if son_rvi < 0.7: puan += 8
    elif son_rvi < 1.0: puan += 5
    elif son_rvi < 1.3: puan += 2
    return puan

def _dinamik_seviyeler(close_val, ed_atr, puan):
    """ED-ATR bazlı stop/profit (1:2 risk/ödül)."""
    if puan >= 50:
        zarar_kes = round(close_val - (ed_atr * 1.5), 2)
        kar_al = round(close_val + (ed_atr * 3.0), 2)
    else:
        zarar_kes = round(close_val - (ed_atr * 1.0), 2)
        kar_al = round(close_val + (ed_atr * 1.5), 2)
    return zarar_kes, kar_al

def genc_hisse_analiz_et(symbol, veri, borsa="BIST"):
    """20-120 mum arası hisseler için Smart Money Price Discovery motoru."""
    try:
        ta_data = veri.copy()

        # VWAP hesapla (genç hisselerde de geçerli)
        try:
            ta_data.ta.vwap(append=True)
        except: pass

        # 4 sütunlu hesaplama
        ta_data = _hesapla_rvi(ta_data)
        ta_data = _hesapla_ais(ta_data)
        ta_data = _hesapla_ed_atr(ta_data, span=min(10, len(ta_data)//2))
        ta_data = _hesapla_vcr(ta_data, pencere=min(5, max(3, len(ta_data)//4)))
        ta_data = _hesapla_ath_proximity(ta_data)

        son = ta_data.iloc[-1]
        close_val = float(son['Close'])
        toplam_puan = 0

        # ── SÜTUN 1: STEALTH VOLUME (maks 30) ──
        hacim_puan = 0
        ais_egim = ta_data['AIS_Egim'].iloc[-1] if 'AIS_Egim' in ta_data.columns else 0
        if ais_egim > 0: hacim_puan += 12

        son_5 = ta_data.tail(5)
        kurumsal_girisler = len(son_5[(son_5['RVI'] > 2.0) & (son_5['Close'] > son_5['Open'])])
        if kurumsal_girisler >= 2: hacim_puan += 10
        elif kurumsal_girisler == 1: hacim_puan += 5

        son_3_rvi = ta_data['RVI'].tail(3).mean() if 'RVI' in ta_data.columns else 1.0
        if ais_egim > 0 and son_3_rvi < 1.2: hacim_puan += 8

        toplam_puan += min(30, hacim_puan)

        # ── SÜTUN 2: IPO BASE QUALITY (maks 30) ──
        base_puan = _ipo_base_skoru(ta_data)
        toplam_puan += base_puan

        # ── SÜTUN 3: MOMENTUM (maks 20) ──
        momentum_puan = 0
        rsi_len = min(7, max(3, len(ta_data) // 3))
        try:
            ta_data.ta.rsi(length=rsi_len, append=True)
        except: pass
        rsi_col = next((c for c in ta_data.columns if 'RSI_' in c), None)
        rsi_val = 50.0
        if rsi_col and pd.notna(ta_data[rsi_col].iloc[-1]):
            rsi_val = float(ta_data[rsi_col].iloc[-1])
            if rsi_val < 40: momentum_puan += 10
            elif 40 <= rsi_val <= 60: momentum_puan += 5
            elif rsi_val > 70: momentum_puan -= 5

        vwap_col = next((c for c in ta_data.columns if 'VWAP' in c), None)
        if vwap_col and pd.notna(son[vwap_col]) and close_val > son[vwap_col]:
            momentum_puan += 10

        toplam_puan += max(0, min(20, momentum_puan))

        # ── SÜTUN 4: TREND YAPISI (maks 20) ──
        trend_puan = 0
        ema_len = min(8, max(3, len(ta_data) // 3))
        ta_data['EMA_short'] = ta_data['Close'].ewm(span=ema_len, adjust=False).mean()
        if close_val > ta_data['EMA_short'].iloc[-1]: trend_puan += 10

        son_3 = ta_data.tail(3)
        yesil_sayisi = len(son_3[son_3['Close'] > son_3['Open']])
        if yesil_sayisi >= 3: trend_puan += 10
        elif yesil_sayisi >= 2: trend_puan += 5

        toplam_puan += min(20, trend_puan)

        # ── FİNAL ──
        toplam_puan = max(0, min(100, toplam_puan))

        ed_atr = ta_data['ED_ATR'].iloc[-1] if 'ED_ATR' in ta_data.columns else close_val * 0.02
        zarar_kes, kar_al = _dinamik_seviyeler(close_val, ed_atr, toplam_puan)

        if toplam_puan >= 72: karar = "🚀 POTANSİYEL PATLAMA"
        elif toplam_puan >= 55: karar = "AL"
        elif toplam_puan <= 25: karar = "SAT"
        else: karar = "BEKLE"

        risk = "DÜŞÜK" if toplam_puan > 55 else "YÜKSEK" if toplam_puan < 30 else "ORTA"

        return {
            "hisse_kodu": symbol.replace('.IS', ''),
            "fiyat": round(close_val, 2), "rsi": round(rsi_val, 2), "puan": int(toplam_puan),
            "karar": karar, "risk_seviyesi": risk, "zarar_kes": zarar_kes, "kar_al": kar_al,
            "genc_hisse": True, "borsa": borsa
        }
    except Exception as e: 
        import traceback
        traceback.print_exc()
        return None

def guncel_bist_hisseleri_getir():
    try:
        url = "https://www.isyatirim.com.tr/tr-tr/analiz/hisse/Sayfalar/default.aspx"
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        if response.status_code == 200:
            import re
            # İş Yatırım sayfasından hisse kodlarını ayıkla: /tr-tr/analiz/hisse/Sayfalar/Hisse-Detay.aspx?hisse=GENKM
            matches = re.findall(r'hisse=([A-Z0-9]+)"', response.text)
            hisseler = list(set(matches))
            hisseler = [h + ".IS" for h in hisseler if len(h) >= 4 and len(h) <= 5]
            if len(hisseler) > 400:
                print(f"✅ Anlık BIST hisse listesi çekildi: {len(hisseler)} hisse bulundu (Örn: {hisseler[0]}, GENKM.IS vb.)")
                return hisseler
    except Exception as e:
        print(f"BIST listesi çekilirken hata: {e}")
    
    # Fallback listesi (Eğer site çökerse)
    print("⚠️ Dinamik liste çekilemedi, eski fallback listesi kullanılıyor.")
    return ["THYAO.IS", "EREGL.IS", "TUPRS.IS", "GARAN.IS", "AKBNK.IS", "YKBNK.IS", "ISCTR.IS", "SAHOL.IS", "KCHOL.IS", "BIMAS.IS"]

def taramayi_baslat():
    db = SessionLocal()
    while True:
        BIST_DINAMIK = guncel_bist_hisseleri_getir()
        TUM_HISSELER = BIST_DINAMIK + GLOBAL_HISSELER
        toplam = len(TUM_HISSELER)
        print(f"\n🚀 {toplam} HİSSELİK ÇİFT ÇEKİRDEKLİ TARAMA BAŞLIYOR...")
        
        baslangic = time.time()
        gecerli_sonuclar = []

        # İŞÇİ SAYISINI 5'E DÜŞÜRDÜK Kİ YAHOO BİZİ BANLAMASIN!
        with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
            future_to_symbol = {executor.submit(hisse_analiz_et, symbol): symbol for symbol in TUM_HISSELER}
            tamamlanan = 0
            for future in concurrent.futures.as_completed(future_to_symbol):
                tamamlanan += 1
                sonuc = future.result()
                if sonuc: gecerli_sonuclar.append(sonuc)
                yuzde = (tamamlanan / toplam) * 100
                print(f"🔄 Tarama: %{yuzde:.1f} ({tamamlanan}/{toplam})", end="\r")

        print("\n\n💾 Veritabanına yazılıyor ve Sinyal Karnesi kontrol ediliyor...")
        guncellenen = 0
        for sonuc in gecerli_sonuclar:
            
            # --- 1. PİYASA LİSTESİ GÜNCELLEMESİ ---
            mevcut = db.query(HisseAnaliz).filter(HisseAnaliz.hisse_kodu == sonuc["hisse_kodu"]).first()
            if mevcut:
                for key, value in sonuc.items(): setattr(mevcut, key, value)
            else:
                db.add(HisseAnaliz(**sonuc))
                
            # --- 2. SİNYAL HAFIZASI (KARNE) KONTROLÜ VE KAYDI ---
            aktif_sinyal = db.query(SinyalGecmisi).filter(
                SinyalGecmisi.hisse_kodu == sonuc["hisse_kodu"],
                SinyalGecmisi.durum == "Bekliyor ⏳"
            ).first()

            if aktif_sinyal:
                guncel_fiyat = sonuc["fiyat"]
                anlik_getiri = ((guncel_fiyat - aktif_sinyal.giris_fiyati) / aktif_sinyal.giris_fiyati) * 100
                if anlik_getiri > aktif_sinyal.max_getiri_yuzdesi:
                    aktif_sinyal.max_getiri_yuzdesi = round(anlik_getiri, 2)

                if guncel_fiyat >= aktif_sinyal.hedef_fiyat:
                    aktif_sinyal.durum = "Hedefe Ulaştı 🎯"
                    aktif_sinyal.kapanis_tarihi = datetime.utcnow()
                elif guncel_fiyat <= aktif_sinyal.stop_fiyat:
                    aktif_sinyal.durum = "Stop Oldu 🛑"
                    aktif_sinyal.kapanis_tarihi = datetime.utcnow()
            
            elif "🚀" in sonuc["karar"]:
                yeni_sinyal = SinyalGecmisi(
                    hisse_kodu=sonuc["hisse_kodu"],
                    giris_fiyati=sonuc["fiyat"],
                    hedef_fiyat=sonuc["kar_al"],
                    stop_fiyat=sonuc["zarar_kes"],
                    karar=sonuc["karar"],
                    durum="Bekliyor ⏳",
                    max_getiri_yuzdesi=0.0
                )
                db.add(yeni_sinyal)

            guncellenen += 1
        
        db.commit() 
        print(f"✅ TAMAMLANDI! {guncellenen} hisse güncellendi. Süre: {round(time.time() - baslangic, 1)} sn")
        time.sleep(180) 

if __name__ == "__main__":
    taramayi_baslat()