import streamlit as st
import requests
import pandas as pd

st.set_page_config(layout="wide")
st.title("Trading Bot Dashboard")

# URL della tua API FastAPI
API_URL = "http://127.0.0.1:8000"

epic_input = st.text_input("Inserisci un EPIC (es. GOLD, EURUSD):", "GOLD").upper()

if st.button("Analizza"):
    if epic_input:
        try:
            response = requests.get(f"{API_URL}/analysis/{epic_input}")
            response.raise_for_status()  # Controlla se la richiesta ha avuto successo
            data = response.json()

            st.header(f"Analisi per {data['epic']}")
            
            signal = data.get('latest_signal')
            if signal == "BUY":
                st.success(f"Segnale: **{signal}**")
            elif signal == "SELL":
                st.error(f"Segnale: **{signal}**")
            else:
                st.info(f"Segnale: **{signal}**")

            st.subheader("Dettagli Ultima Candela")
            st.json(data.get('details'))

        except requests.exceptions.RequestException as e:
            st.error(f"Impossibile contattare l'API: {e}")
        except Exception as e:
            st.error(f"Errore durante l'analisi: {e}")