# Python Trading Bot

Un bot progettato per raccogliere dati di mercato da **Capital.com** e notizie finanziarie da **NewsAPI**, per poi archiviarli in un database locale SQLite.

L'obiettivo finale è utilizzare i dati raccolti come dataset per addestrare un modello di Intelligenza Artificiale in grado di prevedere le tendenze del mercato.

> [!IMPORTANT]
> È richiesta una versione di Python `3.10.12` o superiore. Puoi scaricarla da [python.org](https://www.python.org/downloads/release/python-31012/).

## Funzionalità Principali

-   **Raccolta Dati**: Automatizza il download di dati di mercato e notizie.
-   **Archiviazione Locale**: Salva tutte le informazioni in un database SQLite (`localhost.db`) per un facile accesso.
-   **API Server**: Espone i dati raccolti tramite un'API RESTful costruita con FastAPI.
-   **Web App**: Fornisce un'interfaccia web interattiva, basata su Streamlit, per visualizzare i dati.

## Installazione

1.  **Clona il repository**
    ```bash
    git clone https://github.com/tuo-username/Capital.com-PythonTradingBot.git
    cd Capital.com-PythonTradingBot
    ```

2.  **Crea e attiva un ambiente virtuale**
    ```bash
    # Crea l'ambiente
    python -m venv venv

    # Attivalo (Linux/macOS)
    source venv/bin/activate

    # Attivalo (Windows)
    # venv\Scripts\activate
    ```

3.  **Installa le dipendenze**
    ```bash
    pip install -r requirements.txt
    ```

## Configurazione

Prima di eseguire l'applicazione, è necessario configurare le proprie chiavi API.

1.  Crea una copia del file di esempio `.env.example` e rinominala in `.env`.
    ```bash
    cp .env.example .env
    ```
2.  Apri il file `.env` e inserisci le tue chiavi API per Capital.com e NewsAPI.

## Utilizzo

L'applicazione è suddivisa in tre componenti principali che possono essere eseguiti separatamente.

1.  **Raccolta Dati**
    Esegui lo script principale per avviare la raccolta dei dati. Le informazioni verranno salvate nel database `localhost.db`.
    ```bash
    python3 src/app.py -e
    ```

2.  **Avvio dell'API Server**
    Per accedere ai dati tramite API, avvia il server Uvicorn.
    ```bash
    uvicorn src.api:app --reload
    ```
    L'API sarà disponibile all'indirizzo `http://127.0.0.1:8000`.

3.  **Avvio della Web App**
    Per visualizzare i dati attraverso un'interfaccia grafica, esegui l'app Streamlit.
    ```bash
    streamlit run src/webapp.py
    ```
    L'applicazione web sarà accessibile nel tuo browser.

## Licenza

Questo progetto è distribuito sotto la licenza **Creative Commons Attribution-NonCommercial (CC BY-NC)**.

Questa licenza consente di remixare, adattare e sviluppare l'opera per scopi non commerciali, a condizione che l'autore originale venga riconosciuto. Per qualsiasi uso commerciale, è necessario ottenere un'autorizzazione esplicita.

Per maggiori dettagli, consulta il file [LICENSE](LICENSE.md).
