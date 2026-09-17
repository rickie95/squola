## 1. Tetto giornaliero per assegnazione

- [x] 1.1 Sostituire `_add_at_most_three_hours_per_single_lesson_constraint` con un vincolo `sum(x[a,d,h] for h) <= 3` per assegnazione e giorno (design D3), rimuovendo il metodo precedente; verificare che `build_model` non lo richiami piu'
- [x] 1.2 Aggiungere un test che una fixture in grado di produrre `3 + buco + 1` ore della stessa assegnazione in un giorno non generi piu' quella disposizione (scenario "Quattro ore della stessa materia separate da un'interruzione")
- [x] 1.3 Aggiungere un test che 3 ore della stessa assegnazione in un giorno, e 3 nel giorno successivo, restino ammesse

## 2. Struttura della funzione obiettivo

- [x] 2.1 Introdurre le costanti di peso `W_DAILY_BALANCE`, `W_EXTRA_GAP`, `W_CLASS_BLOCK`, `W_LONG_RUN`, `W_GAP`, `W_TIME_PREFERENCE` a livello di modulo con i valori della tabella D7; verificare che valga `W_LONG_RUN > W_GAP + 2 * W_TIME_PREFERENCE` con un assert o un test
- [x] 2.2 Riscrivere `_add_preference_objectives` come somma di termini nominati, ciascuno prodotto da un metodo dedicato che restituisce la propria espressione; verificare che con tutti i pesi a zero il modello resti risolvibile e produca gli stessi esiti di stato di oggi
- [x] 2.3 Portare `EARLY` e `LATE` al coefficiente `hour - 1` pesato `W_TIME_PREFERENCE`, rimuovendo i coefficienti attuali; verificare con un test che un docente `EARLY` riceva ancora le prime ore a parita' di ogni altra dimensione
- [x] 2.4 Rimuovere `_add_minimize_gaps_for_teacher` e `_add_maximize_gaps_for_teacher` e collegare `MINIMIZE_GAPS` e `MAXIMIZE_GAPS` come modulatori (x2 e /2) dei pesi `W_GAP`, `W_EXTRA_GAP`, `W_CLASS_BLOCK` del singolo docente (design D8); verificare che un docente senza preferenza riceva comunque i criteri di forma

## 3. Termini di forma della giornata

- [x] 3.1 Implementare le variabili `start[t,c,d,h]` e il vincolo `start >= y[h] - y[h-1]` con `y` aggregato per classe (design D1); verificare con il caso Lami che `3C 2C 3C 2C` non venga piu' generato quando `3C 3C ... 2C 2C` e' ammissibile
- [x] 3.2 Aggiungere un test che due materie diverse dello stesso docente nella stessa classe, consecutive, contino come un unico blocco e non siano penalizzate
- [x] 3.3 Implementare le catene `before`/`after`, le variabili `gap[t,d,h]` e `extra_gap[t,d]` (design D4); verificare con il caso Ancarani che `3B - - 3B` diventi `3B 3B`
- [x] 3.4 Aggiungere un test che le ore libere prima della prima lezione e dopo l'ultima non vengano conteggiate come buchi
- [x] 3.5 Implementare `run[t,d,w]` sulle finestre di 4 ore consecutive (design D5); verificare che una giornata da 4 ore venga generata come `2 + stacco + 2` e una da 3 ore resti contigua

## 4. Bilanciamento settimanale

- [x] 4.1 Calcolare per ogni docente `T` e `D` e derivarne la banda `[floor(T/D), ceil(T/D)]` (design D2); verificare con un test che un docente da 18 ore su 5 giorni ottenga banda `[3,4]` e uno da 12 ore su 4 giorni ottenga `[3,3]`
- [x] 4.2 Implementare `load[t,d]` e `dev[t,d]` con il termine inferiore moltiplicato per `works[t,d]`; verificare che un giorno libero non venga penalizzato come giorno sotto banda
- [x] 4.3 Aggiungere un test che una distribuzione `5,5,4,2,2` venga scartata in favore di `4,4,4,3,3` a parita' di vincoli hard
- [x] 4.4 Rimuovere il termine lessicografico `workday_weight * (len(flexible_workdays) - sum(flexible_workdays))` e il calcolo di `preference_upper_bound` (design D6); verificare che i test esistenti in `tests/test_teacher_flexible_day_off.py` continuino a passare, cioe' che il giorno libero resti garantito dal solo vincolo hard
- [x] 4.5 Aggiungere un test che un docente con giorno libero flessibile e carico compatibile ottenga la distribuzione sui 4 giorni residui senza iper-concentrazione

## 5. Diagnostica di qualita'

- [x] 5.1 Calcolare le metriche aggregate dai soli `slots` di `GeneratedSchedule`, senza leggere i valori del solver (design D9); verificare con un test che alimenta slot costruiti a mano, senza costruire un modello
- [x] 5.2 Aggiungere le peggiori coppie (docente, giorno) per dimensione; verificare che il caso Lami compaia in testa alla dimensione dei blocchi-classe
- [x] 5.3 Esporre le metriche nei metadata della risposta di `POST /api/scheduling/generate`; verificare che una generazione infeasible o senza dati non le includa
- [x] 5.4 Verificare che `save_schedule_to_db` e il recupero di un orario salvato non includano le metriche

## 6. Taratura e regressione

- [x] 6.1 Rileggere tutti e 39 i test esistenti alla ricerca di asserzioni su `OPTIMAL` e di budget `time_limit_seconds: 3` divenuti insufficienti; correggerli e verificare che la suite passi in modo stabile su tre esecuzioni consecutive
- [x] 6.2 Generare un orario su dati realistici e confrontare le metriche prima e dopo il change; verificare che ciascuna dimensione sia migliorata o invariata
- [x] 6.3 Misurare il tempo di risoluzione e lo stato finale su dati realistici; se il risultato resta lontano dall'ottimo entro 120s, portare `num_search_workers` a 8 e rimisurare
- [x] 6.4 Ritarare i pesi di D7 sui dati reali se le metriche mostrano una dimensione sistematicamente sacrificata, documentando i valori finali in `design.md`

## 7. Documentazione

- [x] 7.1 Aggiornare `docs/vincoli.md`: tetto giornaliero fra i vincoli hard, e la tabella delle preferenze soft riscritta per riflettere che i criteri di forma valgono per tutti e che `MINIMIZE_GAPS`/`MAXIMIZE_GAPS` sono modulatori
- [x] 7.2 Aggiornare `specs/07 - generation.md` con i nuovi vincoli hard, i termini di obiettivo e il formato delle metriche in risposta
- [x] 7.3 Comunicare in UI che `FEASIBLE` non indica un orario peggiore e mostrare le metriche di qualita' accanto allo stato; verificare che la pagina di scheduling le riporti dopo una generazione riuscita
