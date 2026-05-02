import yfinance as yf
import pandas_ta as ta
import pandas as pd
import numpy as np
import time
import concurrent.futures
from datetime import datetime
from database import SessionLocal, HisseAnaliz, SinyalGecmisi

import requests
import traceback

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

def get_hisse_veri(df, symbol):
    if df is None or df.empty: return pd.DataFrame()
    if isinstance(df.columns, pd.MultiIndex):
        if symbol in df.columns.levels[0]:
            try:
                return df[symbol].dropna(how='all')
            except: pass
    elif len(df.columns) > 0 and 'Close' in df.columns:
        return df.dropna(how='all')
    return pd.DataFrame()

def hisse_analiz_et_bulk(symbol, df_30m, df_1d):
    try:
        veri_30m = get_hisse_veri(df_30m, symbol)
        veri_1d = get_hisse_veri(df_1d, symbol)
        
        veri = veri_30m.copy()
        
        realtime_price = 0.0
        if not veri.empty and 'Close' in veri.columns:
            realtime_price = float(veri['Close'].iloc[-1])
            
        is_truly_young = False
        gercek_mum_sayisi = 0
        if not veri_1d.empty:
            gercek_mum_sayisi = len(veri_1d)
            is_truly_young = gercek_mum_sayisi < 120
            
        borsa = "BIST" if symbol.endswith(".IS") else "US"

        if veri.empty: 
            return {
                "hisse_kodu": symbol.replace('.IS', ''),
                "fiyat": round(realtime_price, 2), "rsi": 0.0, "puan": 0,
                "karar": "YENİ ARZ ⏳", "risk_seviyesi": "BELİRSİZ",
                "zarar_kes": 0.0, "kar_al": 0.0,
                "genc_hisse": True, "borsa": borsa
            }
            
        veri = veri.dropna()
        if 'Volume' in veri.columns:
            veri = veri[veri['Volume'] > 0]
        
        if gercek_mum_sayisi < 20:
            son_fiyat = round(float(veri['Close'].iloc[-1]), 2) if len(veri) > 0 else 0.0
            return {
                "hisse_kodu": symbol.replace('.IS', ''),
                "fiyat": son_fiyat, "rsi": 0.0, "puan": 0,
                "karar": "YENİ ARZ ⏳", "risk_seviyesi": "BELİRSİZ",
                "zarar_kes": 0.0, "kar_al": 0.0,
                "tp1": 0.0, "tp2": 0.0, "initial_stop": 0.0,
                "genc_hisse": True, "borsa": borsa
            }

        if is_truly_young:
            return genc_hisse_analiz_et(symbol, veri, borsa, realtime_price=realtime_price)
            
        # Klasik teknik analiz kısmı
        if len(veri) < 20: 
            if gercek_mum_sayisi >= 20: 
                veri = veri_1d.dropna()
                if 'Volume' in veri.columns: veri = veri[veri['Volume'] > 0]
            else:
                return None

        ta_data = veri.copy()
        ta_data.ta.macd(append=True)
        ta_data.ta.rsi(length=14, append=True)
        ta_data.ta.bbands(length=20, std=2, append=True)
        ta_data.ta.kc(length=20, scalar=1.5, append=True) 
        ta_data.ta.adx(length=14, append=True)
        ta_data.ta.obv(append=True)
        ta_data.ta.vwap(append=True)
        ta_data.ta.atr(length=14, append=True)
        
        # ─── SNIPER FILTER: MODULE A (Regime) + MODULE B (Flow) ───
        ta_data.ta.chop(length=14, append=True)   # CHOP < 50 = Trending market
        ta_data.ta.cmf(length=20, append=True)    # CMF > 0.05 = Institutional accumulation
        
        ta_data = ta_data.dropna()
        if ta_data.empty: return None

        son_gun = ta_data.iloc[-1]
        close_val = float(son_gun['Close'])
        rsi_val = float(son_gun.get('RSI_14', 50))
        
        # ─── SNIPER GATE DEĞERLERI ───
        chop_col = next((c for c in ta_data.columns if c.startswith("CHOP_")), None)
        cmf_col  = next((c for c in ta_data.columns if c.startswith("CMF_")),  None)
        
        chop_val = float(son_gun[chop_col]) if chop_col and pd.notna(son_gun[chop_col]) else 60.0  # Yoksa default choppy
        cmf_val  = float(son_gun[cmf_col])  if cmf_col  and pd.notna(son_gun[cmf_col])  else 0.0
        
        is_trending    = chop_val < 50       # Module A: Piyasa trend halinde mi?
        has_inst_flow  = cmf_val  > 0.05     # Module B: Kurumsal para girişi var mı?
        
        temel_puan = 0
        # CMF temelli kurumsal akış puanı (OBV'nin yerini aldı)
        if cmf_val > 0.10: temel_puan += 20   # Güçlü kurumsal alım
        elif cmf_val > 0.05: temel_puan += 12
        elif cmf_val > 0.0: temel_puan += 5
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
        
        # ════════════════════════════════════════════════════════
        #  SNIPER GATE: 3-WAY MANDATORY CONFIRMATION
        #  Kurallar ÇOK KATIYDI: 3 ü de olması lazım, biri eksikse RET.
        #  Squeeze (Engine 2) + CHOP (Regime) + CMF (Flow)
        # ════════════════════════════════════════════════════════
        if firsat_puani >= 15 and toplam_puan >= 65 and is_trending and has_inst_flow:
            karar = "🚀 POTANSİYEL PATLAMA"
        elif toplam_puan >= 60 and cmf_val > 0.0:  # 'AL' de CMF pozitif olsun
            karar = "AL"
        elif toplam_puan <= 30: karar = "SAT"
        else: karar = "BEKLE"

        atr_col = next((c for c in ta_data.columns if "ATRr_14" in c), None)
        current_atr = float(son_gun[atr_col]) if atr_col and pd.notna(son_gun[atr_col]) else float(close_val * 0.02)
        
        # Dinamik ATR Bazlı Kâr/Zarar Seviyeleri (Profit Maximizer)
        tp1 = round(close_val + (current_atr * 1.5), 2)
        tp2 = round(close_val + (current_atr * 3.0), 2)
        initial_stop = round(close_val - (current_atr * 2.0), 2)
        
        # Risk kontrolü (Çok yakın veya uzak olmasını engelle)
        if initial_stop >= close_val: initial_stop = round(close_val * 0.97, 2)
        if tp1 <= close_val: tp1 = round(close_val * 1.02, 2)
        if tp2 <= close_val: tp2 = round(close_val * 1.05, 2)
        
        # Geriye dönük uyumluluk için eski değişkenlere atama
        kar_al = tp2
        zarar_kes = initial_stop

        risk = "DÜŞÜK" if toplam_puan > 50 else "YÜKSEK" if toplam_puan < 30 else "ORTA"

        # Gerçek zamanlı fiyatı tercih et (yoksa mum kapanışı)
        final_fiyat = round(realtime_price, 2) if realtime_price > 0 else round(close_val, 2)
        
        return {
            "hisse_kodu": symbol.replace('.IS', ''),
            "fiyat": final_fiyat, "rsi": round(rsi_val, 2), "puan": int(toplam_puan),
            "karar": karar, "risk_seviyesi": risk, "zarar_kes": zarar_kes, "kar_al": kar_al,
            "tp1": tp1, "tp2": tp2, "initial_stop": initial_stop,
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
    """ED-ATR bazlı Profit Maximizer hedefleri (TP1, TP2, Stop)."""
    tp1 = round(close_val + (ed_atr * 1.5), 2)
    tp2 = round(close_val + (ed_atr * 3.0), 2)
    initial_stop = round(close_val - (ed_atr * 2.0), 2)
    
    if initial_stop >= close_val: initial_stop = round(close_val * 0.97, 2)
    if tp1 <= close_val: tp1 = round(close_val * 1.02, 2)
    if tp2 <= close_val: tp2 = round(close_val * 1.05, 2)
    
    return tp1, tp2, initial_stop

def genc_hisse_analiz_et(symbol, veri, borsa="BIST", realtime_price=0.0):
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
        tp1, tp2, initial_stop = _dinamik_seviyeler(close_val, ed_atr, toplam_puan)
        
        kar_al = tp2
        zarar_kes = initial_stop

        # ─── SNIPER GATE: Genç Hisse Motoruna da uygula ───
        cmf_val = 0.0
        try:
            ta_data.ta.cmf(length=min(14, max(5, len(ta_data)-1)), append=True)
            cmf_col = next((c for c in ta_data.columns if c.startswith("CMF_")), None)
            if cmf_col and pd.notna(ta_data[cmf_col].iloc[-1]):
                cmf_val = float(ta_data[cmf_col].iloc[-1])
        except: pass

        has_inst_flow = cmf_val > 0.03

        if toplam_puan >= 72 and has_inst_flow:
            karar = "\U0001f680 POTANSİYEL PATLAMA"
        elif toplam_puan >= 55 and cmf_val > 0.0: karar = "AL"
        elif toplam_puan <= 25: karar = "SAT"
        else: karar = "BEKLE"

        risk = "DÜŞÜK" if toplam_puan > 55 else "YÜKSEK" if toplam_puan < 30 else "ORTA"

        # Gerçek zamanlı fiyatı tercih et (yoksa mum kapanışı)
        final_fiyat = round(realtime_price, 2) if realtime_price > 0 else round(close_val, 2)

        return {
            "hisse_kodu": symbol.replace('.IS', ''),
            "fiyat": final_fiyat, "rsi": round(rsi_val, 2), "puan": int(toplam_puan),
            "karar": karar, "risk_seviyesi": risk, "zarar_kes": zarar_kes, "kar_al": kar_al,
            "tp1": tp1, "tp2": tp2, "initial_stop": initial_stop,
            "genc_hisse": True, "borsa": borsa
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return None

def guncel_bist_hisseleri_getir():
    try:
        url = "https://www.isyatirim.com.tr/tr-tr/analiz/hisse/Sayfalar/default.aspx"
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
        if response.status_code == 200:
            import re
            # SADECE Hisse-Detay.aspx?hisse=XXXX veya hisse=XXXX patternlarını yakala
            # Regex iyileştirildi: Sadece kodları (4-5 haneli büyük harf/sayı) alacak
            matches = re.findall(r'hisse=([A-Z0-9]{4,5})', response.text)
            hisseler = list(set(matches))
            hisseler = [h + ".IS" for h in hisseler]
            
            # BIST'te şu an ~550-650 arası hisse var. 
            # 40'tan fazla hisse bulduysa başarılı sayalım (limitleri esnettik)
            if len(hisseler) >= 40:
                print(f"[OK] BIST listesi cekildi: {len(hisseler)} hisse")
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
        TUM_HISSELER = list(set(BIST_DINAMIK + GLOBAL_HISSELER))
        toplam = len(TUM_HISSELER)
        print(f"\n[SCAN] {toplam} HISSELIK BULK TARAMA BASLIYOR...")
        
        baslangic = time.time()
        
        print("[-] 30 Dakikalik veriler indiriliyor...")
        df_30m = yf.download(TUM_HISSELER, period="1mo", interval="30m", group_by="ticker", threads=True, progress=False)
        print("[-] Gunluk veriler indiriliyor...")
        df_1d = yf.download(TUM_HISSELER, period="1y", interval="1d", group_by="ticker", threads=True, progress=False)
        
        gecerli_sonuclar = []

        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
            future_to_symbol = {executor.submit(hisse_analiz_et_bulk, symbol, df_30m, df_1d): symbol for symbol in TUM_HISSELER}
            tamamlanan = 0
            for future in concurrent.futures.as_completed(future_to_symbol):
                tamamlanan += 1
                sonuc = future.result()
                if sonuc: gecerli_sonuclar.append(sonuc)
                
                yuzde = (tamamlanan / toplam) * 100
                print(f"[PROG] Analiz: %{yuzde:.1f} ({tamamlanan}/{toplam})", end="\r")

        print("\n\n[SAVE] Veritabanina yaziliyor...")
        guncellenen = 0
        for sonuc in gecerli_sonuclar:
            
            # --- 1. PİYASA LİSTESİ GÜNCELLEMESİ ---
            mevcut = db.query(HisseAnaliz).filter(HisseAnaliz.hisse_kodu == sonuc["hisse_kodu"]).first()
            if mevcut:
                for key, value in sonuc.items(): setattr(mevcut, key, value)
            else:
                db.add(HisseAnaliz(**sonuc))
                
            # --- 2. SİNYAL HAFIZASI (PROFIT MAXIMIZER) KONTROLÜ VE KAYDI ---
            aktif_sinyaller = db.query(SinyalGecmisi).filter(
                SinyalGecmisi.hisse_kodu == sonuc["hisse_kodu"],
                SinyalGecmisi.durum.in_(["ACTIVE", "TP1_HIT_RISK_FREE"])
            ).all()

            for aktif_sinyal in aktif_sinyaller:
                guncel_fiyat = sonuc["fiyat"]
                
                # MFE ve Highest High Güncellemesi
                if aktif_sinyal.highest_high is None or guncel_fiyat > aktif_sinyal.highest_high:
                    aktif_sinyal.highest_high = guncel_fiyat
                    
                anlik_getiri = ((aktif_sinyal.highest_high - aktif_sinyal.giris_fiyati) / aktif_sinyal.giris_fiyati) * 100
                if anlik_getiri > aktif_sinyal.mfe_percent:
                    aktif_sinyal.mfe_percent = round(anlik_getiri, 2)
                aktif_sinyal.max_getiri_yuzdesi = aktif_sinyal.mfe_percent # Uyumluluk
                
                # ATR tahminini hedef fiyatlardan tersine mühendislikle bul
                if aktif_sinyal.tp1 and aktif_sinyal.giris_fiyati:
                    atr_tahmini = (aktif_sinyal.tp1 - aktif_sinyal.giris_fiyati) / 1.5
                else: 
                    atr_tahmini = aktif_sinyal.giris_fiyati * 0.02
                    
                # State Machine Mantığı
                if aktif_sinyal.durum == "ACTIVE":
                    if aktif_sinyal.tp1 and guncel_fiyat >= aktif_sinyal.tp1:
                        aktif_sinyal.durum = "TP1_HIT_RISK_FREE"
                        # Stop'u başabaş (risk-free) seviyesine çek (komisyon maliyeti dahil %0.5)
                        aktif_sinyal.current_stop = round(aktif_sinyal.giris_fiyati * 1.005, 2)
                    elif aktif_sinyal.current_stop and guncel_fiyat <= aktif_sinyal.current_stop:
                        aktif_sinyal.durum = "STOPPED_OUT"
                        aktif_sinyal.kapanis_tarihi = datetime.utcnow()
                        
                elif aktif_sinyal.durum == "TP1_HIT_RISK_FREE":
                    # İzleyen Stop (Trailing Stop) hesaplaması: Zirveden 2 ATR aşağısı
                    izleyen_stop_adayi = round(aktif_sinyal.highest_high - (atr_tahmini * 2.0), 2)
                    if not aktif_sinyal.current_stop or izleyen_stop_adayi > aktif_sinyal.current_stop:
                        aktif_sinyal.current_stop = izleyen_stop_adayi
                        
                    if aktif_sinyal.tp2 and guncel_fiyat >= aktif_sinyal.tp2:
                        aktif_sinyal.durum = "TP2_HIT_WIN"
                        aktif_sinyal.kapanis_tarihi = datetime.utcnow()
                    elif aktif_sinyal.current_stop and guncel_fiyat <= aktif_sinyal.current_stop:
                        aktif_sinyal.durum = "TRAILING_STOP_HIT"
                        aktif_sinyal.kapanis_tarihi = datetime.utcnow()
            
            # Yeni bir Roket Sinyali geldiyse (eğer zaten o hissede aktif 🚀 yoksa)
            if "🚀" in sonuc["karar"]:
                zaten_aktif_var = [s for s in aktif_sinyaller if s.durum in ["ACTIVE", "TP1_HIT_RISK_FREE"]]
                if not zaten_aktif_var:
                    yeni_sinyal = SinyalGecmisi(
                        hisse_kodu=sonuc["hisse_kodu"],
                        giris_fiyati=sonuc["fiyat"],
                        tp1=sonuc.get("tp1"),
                        tp2=sonuc.get("tp2"),
                        hedef_fiyat=sonuc.get("tp2", sonuc["kar_al"]),
                        initial_stop=sonuc.get("initial_stop"),
                        current_stop=sonuc.get("initial_stop"),
                        stop_fiyat=sonuc.get("initial_stop", sonuc["zarar_kes"]),
                        karar=sonuc["karar"],
                        durum="ACTIVE",
                        mfe_percent=0.0,
                        highest_high=sonuc["fiyat"]
                    )
                    db.add(yeni_sinyal)

            guncellenen += 1
        
        db.commit() 
        print(f"[DONE] {guncellenen} hisse guncellendi. Sure: {round(time.time() - baslangic, 1)} sn")
        time.sleep(90)  # Dongu bekleme: 90sn

if __name__ == "__main__":
    taramayi_baslat()