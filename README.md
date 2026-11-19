# Domanda e scorte FITT
Prototipo universitario: prodotti reali, domanda e approvvigionamenti simulati.
Nessun collegamento con sistemi aziendali. Python 3.12 consigliato.

## Avvio
Aprire un terminale nella cartella estratta:

    python -m venv .venv
    .venv\Scripts\activate
    python -m pip install -r requirements.txt
    python -m streamlit run app.py

Su macOS/Linux attivare con `source .venv/bin/activate`.
Streamlit mostra l'indirizzo locale da aprire nel browser.

## Riproduzione risultati e verifiche
    python run_report.py
    python -m pytest -q test_app.py

I CSV in output documentano il riferimento e lo scenario alternativo.
requirements.txt contiene le dipendenze dirette verificate.

## Convenzioni
- 48 mesi, seme 20261110. PW01-PW04 sono codici didattici.
- Validazione M25-M36, verifica M37-M48, previsione finale M49-M60.
- Il vincitore minimizza MAE di validazione, RMSE risolve parita'.
- Gli shock futuri non sono noti al previsore.
- Scenario alternativo: variabilita' 1.5, tendenza 1.2, stagionalita' 1.2, lead 2.
- Le componenti prospettiche non si sommano: ciclica media, riserve obiettivo,
  pipeline prevista. Il registro riporta separatamente la pipeline effettiva.
- Anticipo = massimo deficit cumulato rispetto alla capacita' sui 12 mesi previsti.
  Non viene creato automaticamente stock: e' un fabbisogno teorico.
- Sicurezza empirica: quantile superiore di 9-11 errori cumulati, campione ridotto.
- Giacenza iniziale e capacita' dipendono solo dai primi 36 mesi.
- Ordini a fine mese, arrivi dopo lead periodi, arretrati evasi prima della domanda.
- Nessun costo monetario o promessa di servizio effettivo.

## File
core.py: motore; app.py: dashboard; run_report.py: esportazioni e figura;
test_app.py: sei verifiche; output/: dati, indicatori e registri.
Il rapporto Word include i due moduli principali, i criteri e i risultati.

## Documentazione e caricamento
Il rapporto universitario non viene pubblicato nella repository per tutelare i dati personali.
Caricare in Git i contenuti di questa cartella, mantenendo la struttura.
Il file .gitignore esclude ambienti virtuali e file temporanei.
I risultati in output sono inclusi come evidenze riproducibili.
run_report.py aggiorna CSV, JSON e figura, ma non i registri run_log.txt e test_results.txt.

## Avvio Windows senza attivazione
    py -3.12 -m venv .venv
    .venv\Scripts\python.exe -m pip install -r requirements.txt
    .venv\Scripts\python.exe -m streamlit run app.py
