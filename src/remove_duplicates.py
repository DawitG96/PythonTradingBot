import os
import pandas as pd
import glob

def process_csv_files(root_dir='.'):
    """
    Elabora tutti i file CSV nella directory specificata e in tutte le sottodirectory,
    rimuovendo le righe duplicate.
    
    Args:
        root_dir (str): Directory di partenza per la ricerca dei file CSV
    """
    # Trova tutti i file CSV nella directory e nelle sottodirectory
    csv_files = glob.glob(os.path.join(root_dir, '**', '*.csv'), recursive=True)
    
    if not csv_files:
        print(f"Nessun file CSV trovato in {root_dir} e nelle sue sottocartelle.")
        return
    
    print(f"Trovati {len(csv_files)} file CSV da elaborare.")
    
    for csv_file in csv_files:
        try:
            # Leggi il file CSV
            print(f"Elaborazione di {csv_file}...")
            df = pd.read_csv(csv_file)
            
            # Conta le righe prima della rimozione dei duplicati
            rows_before = len(df)
            
            # Rimuovi le righe duplicate
            df = df.drop_duplicates()
            
            # Conta le righe dopo la rimozione dei duplicati
            rows_after = len(df)
            
            # Salva il file senza duplicati
            df.to_csv(csv_file, index=False)
            
            print(f"  Righe originali: {rows_before}")
            print(f"  Righe dopo rimozione duplicati: {rows_after}")
            print(f"  Righe duplicate rimosse: {rows_before - rows_after}")
            
        except Exception as e:
            print(f"Errore nell'elaborazione di {csv_file}: {str(e)}")
    
    print("Elaborazione completata.")

if __name__ == "__main__":
    import sys
    
    # Se viene fornita una directory come argomento, usala come punto di partenza
    if len(sys.argv) > 1:
        directory = sys.argv[1]
        process_csv_files(directory)
    else:
        # Altrimenti usa la directory corrente
        process_csv_files("datasets")