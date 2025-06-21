# PythonTradingBot

Script usato per prendre delle informazioni di mercato e di notizie e salvarle in un Database locale (sqlite3).\
I dati sono presi da Capital.com e da NewsAPI.

L'obiettivo futuro di questo script è di creare un modello di AI per la predizione dei valori di trading usando le informazioni scaricate come dataset.

> [!IMPORTANT]
> La versione di Python usata è la [3.10.12](https://www.python.org/downloads/release/python-31012/).

## Installazione

1. Clona il repository:
    ```bash
    git clone https://github.com/tuo-username/Capital.com-PythonTradingBot.git
    cd Capital.com-PythonTradingBot
    ```

2. Crea un ambiente virtuale e attivalo:
    ```bash
    python -m venv venv
    source venv/bin/activate  # Su Windows usa `venv\Scripts\activate`
    ```

3. Installa le dipendenze:
    ```bash
    pip install -r requirements.txt
    ```

## Utilizzo

1. Configura le tue API keys per Capital.com e NewsAPI nel file `.env`. Un esempio è presente nel [.env.example](.env.example)

2. Esegui lo script principale:
    ```bash
    python3 src/app.py -e
    ```
3. I dati di mercato e le notizie verranno salvati nel database locale `localhost.db`.

4. Esegui api server
```bash
    uvicorn src.api:app --reload
```

5. Esegui webapp
```bash
streamlit run src/webapp.py
```

## Licenza

Questo progetto è distribuito sotto licenza Creative Commons Attribution-NonCommercial (CC BY-NC). Questa licenza permette ad altri di remixare, adattare e sviluppare il tuo lavoro per scopi non commerciali. Anche se le loro nuove opere devono riconoscerti e non possono essere utilizzate commercialmente, non devono concedere in licenza le loro opere derivate con gli stessi termini.

Per usi commerciali, è necessario contattare l'autore per ottenere un'autorizzazione esplicita.

Vedi il file [LICENSE](LICENSE.md) per maggiori dettagli.
