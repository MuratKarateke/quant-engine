import sqlite3
import traceback

def run_migration():
    print("MIGRASYON BASLIYOR...")
    try:
        conn = sqlite3.connect('borsa_terminali.db', timeout=10)
        cursor = conn.cursor()
        
        columns = [
            ('tp1', 'FLOAT'),
            ('tp2', 'FLOAT'),
            ('initial_stop', 'FLOAT'),
            ('current_stop', 'FLOAT'),
            ('highest_high', 'FLOAT'),
            ('mfe_percent', 'FLOAT DEFAULT 0.0')
        ]
        
        for col_name, col_type in columns:
            try:
                cursor.execute(f'ALTER TABLE sinyal_gecmisi ADD COLUMN {col_name} {col_type}')
                print(f'- EKLENDI: {col_name}')
            except sqlite3.OperationalError as e:
                if 'duplicate column name' in str(e).lower():
                    print(f'- ZATEN VAR: {col_name}')
                else:
                    raise e
                    
        # Eski Bekliyor durumlari aktif olarak guncelleniyor
        cursor.execute('UPDATE sinyal_gecmisi SET durum = "ACTIVE" WHERE durum = "Bekliyor ⏳"')
        
        conn.commit()
        conn.close()
        print("\n✅ MIGRASYON BASARIYLA TAMAMLANDI! (Artik uvicorn ve worker.py'i calistirabilirsiniz.)")
    except sqlite3.OperationalError as e:
        if "database is locked" in str(e).lower():
            print("\n❌ HATA: Veritabani kilitli!")
            print("Lutfen terminalde calisan 'uvicorn' ve 'worker.py' sureclerini kapattiginizdan emin olun ve tekrar deneyin.")
        else:
            traceback.print_exc()
    except Exception as e:
        traceback.print_exc()

if __name__ == "__main__":
    run_migration()
