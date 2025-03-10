#!/bin/bash

# Carica le variabili dal file .env
source /home/dawit/Progetti/Capital.com-PythonTradingBot/.env

# Converti la stringa di EPIC in un array
IFS=',' read -r -a epic_array <<< "$EPICS"

# Lancia fetch_data.py per ciascun EPIC
for epic in "${epic_array[@]}"; do
    python3 fetch_data.py "$epic" &
done

# Aspetta la fine di tutti i processi
wait
