import os
import sys
import time
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
import schedule

# Aggiungi il percorso src al PYTHONPATH
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import get_connection, get_all_epics
from downloaders import HistoricalDataDownloader
from providers import CapitalComProvider

# Configurazione logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('daily_update.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DailyDataUpdater:
    def __init__(self):
        self.provider = CapitalComProvider()
        self.downloader = HistoricalDataDownloader(self.provider)
        self.resolutions = ['MINUTE', 'MINUTE_5', 'MINUTE_15', 'HOUR', 'DAY']
        
    def get_yesterday_range(self) -> tuple:
        """Calcola il range temporale per ieri"""
        yesterday = datetime.now() - timedelta(days=1)
        start_time = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)
        end_time = yesterday.replace(hour=23, minute=59, second=59, microsecond=999000)
        
        return start_time, end_time
    
    def should_download_for_resolution(self, resolution: str, epic: str, yesterday: datetime) -> bool:
        """Determina se scaricare dati per una specifica resolution"""
        conn = get_connection()
        cursor = conn.cursor()
        
        # Controlla se abbiamo già dati per ieri
        yesterday_str = yesterday.strftime('%Y-%m-%d')
        
        query = """
        SELECT COUNT(*) FROM historicaldata 
        WHERE epic = %s AND resolution = %s 
        AND DATE(timestamp) = %s
        """
        
        cursor.execute(query, (epic, resolution, yesterday_str))
        count = cursor.fetchone()[0]
        
        cursor.close()
        conn.close()
        
        # Se abbiamo già dati per ieri, non scarichiamo di nuovo
        return count == 0
    
    def download_epic_yesterday(self, epic: str, resolution: str) -> bool:
        """Scarica i dati di ieri per un epic specifico"""
        try:
            start_time, end_time = self.get_yesterday_range()
            
            # Per DAY resolution, scarica solo se è un giorno lavorativo
            if resolution == 'DAY':
                # Lunedì = 0, Domenica = 6
                if start_time.weekday() >= 5:  # Sabato o Domenica
                    logger.info(f"⏭️ Saltato {epic} (DAY) - Weekend")
                    return True
            
            # Per HOUR e MINUTE, scarica solo nei giorni lavorativi
            elif resolution in ['HOUR', 'MINUTE', 'MINUTE_5', 'MINUTE_15']:
                if start_time.weekday() >= 5:  # Sabato o Domenica
                    logger.info(f"⏭️ Saltato {epic} ({resolution}) - Weekend")
                    return True
            
            logger.info(f"📊 Scaricando {epic} ({resolution}) per {start_time.strftime('%Y-%m-%d')}")
            
            # Scarica i dati
            success = self.downloader.download_and_store(
                epic=epic,
                resolution=resolution,
                start_time=start_time,
                end_time=end_time
            )
            
            if success:
                logger.info(f"✅ Completato {epic} ({resolution})")
                return True
            else:
                logger.warning(f"⚠️ Fallito {epic} ({resolution})")
                return False
                
        except Exception as e:
            logger.error(f"❌ Errore scaricando {epic} ({resolution}): {str(e)}")
            return False
    
    def run_daily_update(self):
        """Esegue l'aggiornamento giornaliero completo"""
        start_time = datetime.now()
        logger.info(f"🚀 Inizio aggiornamento giornaliero alle {start_time}")
        
        # Ottieni tutti gli epic dal database
        epics = get_all_epics()
        logger.info(f"📋 Trovati {len(epics)} epic da processare")
        
        yesterday = datetime.now() - timedelta(days=1)
        
        total_downloads = 0
        successful_downloads = 0
        failed_downloads = 0
        skipped_downloads = 0
        
        for epic in epics:
            for resolution in self.resolutions:
                # Controlla se dobbiamo scaricare
                if not self.should_download_for_resolution(resolution, epic, yesterday):
                    logger.info(f"⏭️ Saltato {epic} ({resolution}) - Già presente")
                    skipped_downloads += 1
                    continue
                
                total_downloads += 1
                
                # Scarica i dati
                success = self.download_epic_yesterday(epic, resolution)
                
                if success:
                    successful_downloads += 1
                else:
                    failed_downloads += 1
                
                # Pausa per evitare rate limiting
                time.sleep(2)
        
        end_time = datetime.now()
        duration = end_time - start_time
        
        # Report finale
        logger.info(f"🏁 Aggiornamento completato in {duration}")
        logger.info(f"📊 Statistiche:")
        logger.info(f"   - Totale processati: {total_downloads}")
        logger.info(f"   - Successi: {successful_downloads}")
        logger.info(f"   - Fallimenti: {failed_downloads}")
        logger.info(f"   - Saltati: {skipped_downloads}")

def run_scheduled_update():
    """Funzione chiamata dal cron job"""
    updater = DailyDataUpdater()
    updater.run_daily_update()

if __name__ == "__main__":
    # Esecuzione diretta per test
    run_scheduled_update()