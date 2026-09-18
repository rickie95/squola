## Context

Vedi `proposal.md - Why` per la motivazione. Qui contano tre fatti sul modello
attuale in `src/squola/scheduler.py`:

1. La funzione obiettivo e' una somma pesata piatta costruita in
   `_add_preference_objectives`, piu' un termine lessicografico di peso
   `preference_upper_bound + 1` per il giorno libero flessibile.
2. `MINIMIZE_GAPS` ha coefficiente `hour - 1` (cioe' e' `EARLY` traslato) e
   `MAXIMIZE_GAPS` penalizza le ore centrali. Nessuna variabile del modello
   rappresenta un buco: le due preferenze non descrivono cio' che il loro nome
   dice.
3. Diversi vincoli hard utili esistono gia' e non vanno toccati: no-overlap per
   docente e per classe, indisponibilita', lezioni fisse, carico giornaliero in
   `{0} U [2,5]`, e il giorno libero flessibile come `sum(works_on_day) <= 4`.

Il punto 3 e' rilevante per due conseguenze non ovvie: `sum(x)` su (docente,
classe, giorno, ora) e' gia' un'espressione 0/1 grazie ai due no-overlap, quindi
i termini di forma non richiedono variabili indicatrici aggiuntive per la
presenza; e il giorno libero e' gia' garantito senza alcun aiuto dall'obiettivo.

## Goals / Non-Goals

**Goals:**
- Una sola funzione obiettivo, con termini nominati e pesi come costanti di
  modulo tarabili, che descriva la forma della giornata di ogni docente.
- Formulazioni lineari: nessuna moltiplicazione fra variabili, nessuna
  reificazione dove un vincolo di sola minorazione basta.
- Pesi calibrati su casi reali riportati dagli utenti, non scelti a occhio.

**Non-Goals:**
- Buchi nella griglia delle **classi** (una classe con meno di 30 ore avra' ore
  libere; dove cadano non e' oggetto di questo change).
- Il caso in cui un docente insegna due materie nella stessa classe e accumula
  cosi' 6 ore contigue in quella classe: il tetto e' per assegnazione e i gruppi
  contigui sono contati per classe, quindi la combinazione non e' penalizzata.
  Ritenuto abbastanza raro da non giustificare un terzo livello di conteggio.
- Persistenza delle metriche di qualita' (registrata in `TODO.md`).
- Configurazione dei pesi per workspace.

## Decisions

### D1 - Contiguita' come conteggio di inizi di blocco, non di transizioni

Per ogni (docente `t`, classe `c`, giorno `d`, ora `h`) con
`y[t,c,d,h] = sum(x[a,d,h] for a in assegnazioni di t in c)`:

```
    start[t,c,d,h] >= y[t,c,d,h] - y[t,c,d,h-1]        (y[..,0] = 0)
    start in [0,1],  minimizzare sum(start)
```

Nessuna reificazione: la minimizzazione tiene `start` al suo limite inferiore.

**Alternativa scartata**: contare le transizioni fra coppie di classi adiacenti
richiede un termine per ogni coppia `(c, c')`, quadratico nel numero di classi
di un docente. Il conteggio degli inizi e' lineare e cattura le stesse
patologie.

Conseguenza voluta: minimizzando gli inizi *grezzi* (non l'eccesso rispetto al
minimo teorico) il solver e' spinto anche a concentrare la giornata di un docente
su meno classi distinte, cioe' meno cambi d'aula. E' un effetto desiderabile e
gratuito.

Granularita' **classe** e non assegnazione: `3A(ita) 3A(ita) 3A(sto)` e' un unico
blocco, perche' il docente non si sposta e la classe non cambia docente.

### D2 - Banda di bilanciamento derivata, non soglia fissa

Il feedback parla di "3/4 ore al giorno". Non lo codifichiamo come costante: la
banda e' `[floor(T/D), ceil(T/D)]` con `T` = ore settimanali del docente e `D` =
giorni lavorabili. Per un contratto da 18 ore su 5 giorni da' esattamente `[3,4]`,
ma si adatta da sola a chi insegna anche in un'altra scuola e a chi ha
indisponibilita' — cioe' alla clausola "al netto di" del feedback, senza casi
speciali.

```
    load[t,d]  = sum(x[a,d,h] for a in assegnazioni di t, for h)
    dev[t,d]  >= load[t,d] - ceil(T/D)
    dev[t,d]  >= floor(T/D) * works[t,d] - load[t,d]
```

`works[t,d]` e' il booleano gia' creato per i docenti con giorno libero
flessibile; per gli altri e' la costante 1 sui giorni non bloccati. Il secondo
vincolo moltiplicato per `works` evita di penalizzare il giorno libero come se
fosse un giorno sotto banda.

`D` e' calcolato staticamente: `5 - giorni interamente bloccati - (1 se
prefers_day_off)`. Renderlo variabile richiederebbe una divisione fra variabili;
il valore statico e' esatto in tutti i casi tranne quelli in cui il carico e'
troppo basso per riempire `D` giorni, dove la banda risulta semplicemente
leggermente lasca.

**Alternativa scartata**: minimizzare `max_d load - min_d load`. Richiede due
variabili di estremo per docente e non esprime un bersaglio, solo una dispersione:
`5,5,5,5,5` e `2,2,2,2,2` avrebbero entrambi dispersione 0.

### D3 - Tetto giornaliero per assegnazione, hard

```
    sum(x[a,d,h] for h) <= 3      per ogni assegnazione a, per ogni giorno d
```

Sostituisce `_add_at_most_three_hours_per_single_lesson_constraint`, che lo
**sussume**: 3 ore totali in un giorno non possono essere 4 consecutive. Netto:
un metodo in meno.

Hard e non soft: e' strettamente piu' forte del vincolo che sostituisce (oggi
`3 + buco + 1` passa), quindi introduce un rischio di infeasibility nuovo. Il
rischio e' accettato perche' romperlo richiederebbe un'assegnazione da oltre 15
ore settimanali, mentre il massimo osservato in esercizio e' 8. Soft avrebbe
significato un settimo peso da tarare per proteggersi da un caso che non esiste
nei dati.

### D4 - Buchi per appartenenza all'intervallo, non per span

Un buco e' uno slot libero che ha lezione sia prima sia dopo nella stessa
giornata:

```
    before[t,d,h] >= before[t,d,h-1]      before[t,d,1] = 0
    before[t,d,h] >= occ[t,d,h-1]
    after [t,d,h] >= after [t,d,h+1]      after [t,d,6] = 0
    after [t,d,h] >= occ[t,d,h+1]

    gap[t,d,h] >= before[t,d,h] + after[t,d,h] - occ[t,d,h] - 1
    extra_gap[t,d] >= sum(gap[t,d,h] for h) - 1
```

`before` e `after` sono monotoni e si costruiscono in catena: lineari nel numero
di ore, non quadratici.

**Alternativa scartata**: `first`/`last` con `add_min_equality`/
`add_max_equality` e `buchi = last - first + 1 - load`. Equivalente ma introduce
vincoli di min/max su interi, piu' pesanti da propagare del conteggio booleano.

`extra_gap` esiste perche' il feedback vuole due cose opposte: **una** ora di
stacco e' desiderabile nelle giornate lunghe, **due** ore di buco no. Un termine
lineare sulle ore di buco non puo' esprimerlo; la coppia
`gap` (peso basso) + `extra_gap` (peso alto) si'.

### D5 - Filate: un solo termine, convessita' gratuita

```
    run[t,d,w] >= sum(occ[t,d,h] for h in w) - 3      w = finestre di 4 ore
    run in [0,1]
```

Una filata da 5 ore contiene **due** finestre da 4 piene, quindi costa il doppio
di una da 4 senza scrivere un secondo termine. La gerarchia del feedback ("3
ottime, 4 ok, 5 tante") esce da sola: 0, 1, 2 unita' di penalita'.

**Alternativa scartata**: un termine separato per le finestre da 5. Raddoppia le
variabili per ottenere la stessa monotonia.

**Alternativa scartata**: vincolo hard "mai 5 ore consecutive". Con 6 slot al
giorno, un docente indisponibile all'ultima ora e con una giornata da 5 ore
sarebbe forzato su 5 slot contigui e quindi infeasible. Classe di infeasibility
nuova e non diagnosticabile: non ne vale la pena per una preferenza.

### D6 - Rimozione del termine lessicografico sul giorno libero

Il giorno libero e' garantito da `sum(works_on_day) <= 4`, che e' hard. Il termine
in obiettivo non lo creava: spingeva solo verso 4 giorni anziche' 3 o 2, cioe'
impediva l'iper-concentrazione. La banda D2 lo fa meglio — con `D=4` e `T=12` la
banda e' `[3,3]`, quindi `3,3,3,3` costa 0 mentre `5,5,2,0` costa 5.

Tenerlo significherebbe un peso `preference_upper_bound + 1` che deve ora dominare
sei termini invece di uno: cresce di un ordine di grandezza, degrada il
rilassamento LP e rallenta la ricerca proprio dove serve velocita'.

Trade-off registrato in `specs/teacher-workweek-distribution/spec.md`: la
massimizzazione dei giorni di lezione passa da garanzia lessicografica a
preferenza forte. Il giorno libero in se' resta una garanzia hard.

### D7 - Pesi, e il vincolo di calibrazione su EARLY/LATE

Cio' che conta non e' il totale di un termine ma il **margine** di uno scambio. Per
una giornata da 4 ore, scegliere `2 + stacco + 2` invece di 4 ore di fila fa
guadagnare `w_run` e costa `w_gap` piu' lo spostamento di due lezioni un'ora piu'
tardi, cioe' `2 * w_time`. Da cui il vincolo:

```
    w_run > w_gap + 2 * w_time
```

Senza questo, un docente con preferenza di fascia oraria si prende
sistematicamente le filate lunghe.

| costante | termine | peso |
|---|---|---|
| `W_DAILY_BALANCE` | `dev[t,d]` | 16 |
| `W_EXTRA_GAP` | `extra_gap[t,d]` | 12 |
| `W_CLASS_BLOCK` | `start[t,c,d,h]` | 10 |
| `W_LONG_RUN` | `run[t,d,w]` | 6 |
| `W_GAP` | `gap[t,d,h]` | 2 |
| `W_TIME_PREFERENCE` | `EARLY`/`LATE`, coefficiente `hour - 1` in `[0,5]` | 1 |

Costanti di modulo, non configurazione per workspace: app locale monoutente, si
modifica la costante e si riavvia. Il valore va tarato sui dati reali; i numeri
qui sono un punto di partenza verificato sui casi sotto.

### D8 - `MINIMIZE_GAPS` e `MAXIMIZE_GAPS` come modulatori

`MINIMIZE_GAPS` moltiplica per 2 i pesi `W_GAP`, `W_EXTRA_GAP`, `W_CLASS_BLOCK`
del docente; `MAXIMIZE_GAPS` li dimezza. Attenuazione, mai inversione: chiedere al
solver di frammentare una giornata contraddirebbe il resto del modello.

**Alternativa scartata**: cancellare i due valori dall'enum. Piu' pulito ma costa
una migrazione Alembic, una modifica al frontend e la perdita delle preferenze
gia' configurate dagli utenti, in cambio di nulla che l'utente percepisca.

### D9 - Diagnostica di qualita' in risposta

`GeneratedSchedule` calcola i totali per dimensione e le peggiori coppie
(docente, giorno) dai soli `slots` estratti, **non** leggendo i valori delle
variabili del solver. Cosi' la diagnostica e' una funzione pura dell'orario ed e'
verificabile in test senza costruire un modello.

## Risks / Trade-offs

**Il problema passa da soddisfacibilita' a ottimizzazione reale.** Oggi con tutti
i docenti a `NONE` l'obiettivo e' vuoto e CP-SAT chiude subito. Dopo, l'obiettivo
e' denso su ~5.000 variabili ausiliarie in piu' (stima per 20 docenti, 15 classi,
100 assegnazioni, su ~3.000 esistenti).
-> 120s e 4 worker sono gia' impostati; misurare su dati reali e salire a 8 worker
se il gap resta ampio.

**`OPTIMAL` diventera' raro, `FEASIBLE` la norma.** Un utente che oggi vede
`OPTIMAL` e domani `FEASIBLE` legge un peggioramento dove c'e' un miglioramento.
-> La diagnostica D9 e' la risposta: il numero da guardare diventa la metrica di
qualita', non l'etichetta di stato. Va comunicato in UI.

**I test esistenti passano `time_limit_seconds: 3`.** Con un obiettivo denso quel
budget puo' produrre esiti instabili e test a intermittenza.
-> Rileggere tutti e 39 i test, non solo rilanciarli: quelli che asseriscono
`OPTIMAL` vanno rivisti, quelli su fixture piccole probabilmente reggono.

**Il tetto hard D3 puo' rendere infeasible un workspace che oggi genera.**
-> Rischio accettato (vedi D3). `find_teachers_with_unsatisfiable_daily_workload`
non copre questo caso: e' un conflitto per assegnazione, non per docente. Se si
manifesta, la diagnosi va estesa.

**Pesi tarati su tre casi.** Sono i tre riportati dagli utenti, non un campione.
-> D9 esiste proprio per ritarare su dati veri senza rileggere le griglie a mano.

## Calibrazione verificata

Costi calcolati con i pesi di D7, sui tre casi riportati dagli utenti.

```
 Lami, lunedi (4 ore, 2 classi)
   [3C][2C][3C][2C]      4 inizi                          = 40
   [3C][3C][2C][2C]      2 inizi + 1 finestra da 4        = 26
   [3C][3C][ - ][2C][2C] 2 inizi + 1 ora di buco          = 22   <- scelto

 Grazia, mercoledi (5 ore, 3 classi)
   [3A][3A][2A][ - ][3A][1A]   4 inizi + 1 buco           = 42
   [3A][3A][3A][ - ][2A][1A]   3 inizi + 1 buco           = 32   <- scelto

 Ancarani, venerdi (2 ore, 1 classe)
   [3B][ - ][ - ][3B]    2 inizi + 2 buchi + 1 extra_gap  = 36
   [3B][3B]              1 inizio                         = 10   <- scelto
```

Controprova sulle giornate corte, dove la frammentazione sarebbe il difetto
opposto: giornata da 3 ore in una classe, `[L][L][L]` costa 10, `[L][L][ - ][L]`
costa 10 + 10 + 2 = 22. Il modello non frammenta chi lavora poche ore.

## Misure

Istanza realistica: 6 classi da 30 ore, 8 materie, 10 docenti da 18 ore, 48
assegnazioni, 180 ore totali, nessuna indisponibilita'. "Prima" e' il modello
attuale con i pesi di forma azzerati, cioe' l'obiettivo che vedeva un docente
senza preferenze.

| dimensione | prima | dopo |
|---|---|---|
| `class_blocks` | 26 | 1 |
| `gap_hours` | 53 | 32 |
| `long_runs` | 16 | 4 |
| `balance_deviation` | 14 | 5 |

Nessuna dimensione e' sacrificata: i pesi di D7 restano quelli tarati sui tre
casi utente, nessuna ritaratura necessaria. `gap_hours` e' la dimensione che
migliora di meno (-40%) ed e' atteso: la banda produce giornate da 3-4 ore, e una
giornata da 4 ore prende un'ora di stacco per costruzione. 32 ore di buco su 50
giornate-docente sono ~0,64 al giorno, cioe' il comportamento voluto.

Qualita' in funzione del budget di tempo, come somma pesata delle quattro
dimensioni (piu' basso e' meglio):

| budget | 15s | 30s | 60s | 120s |
|---|---|---|---|---|
| somma pesata | 302 | 208 | 204 | 176 |

La qualita' **non** e' in plateau a 120s: il limite attuale e' giustificato e non
va abbassato. Il plateau immediato osservato su una fixture di test da 6 classi
intercambiabili e' un effetto della sua simmetria, non del modello.

`num_search_workers` resta a **4**: su quattro esecuzioni a 120s con 8 worker la
somma pesata e' 222, 146, 200, 206 (media ~193) contro 178, 140, 176 (media ~165)
con 4 worker. La varianza fra esecuzioni e' ampia e gli intervalli si
sovrappongono, ma non c'e' alcuna evidenza che 8 worker aiutino.

Lo stato resta `FEASIBLE` in tutte le esecuzioni: CP-SAT non dimostra
l'ottimalita' entro il limite. Vedi la nota sui rischi.

## Migration Plan

Nessuna migrazione dati: nessuna modifica di schema, l'enum `SchedulePreference`
resta invariato (D8) e le metriche non sono persistite (D9).

Rollback: i termini sono additivi e indipendenti. Azzerare una costante di peso
disattiva il termine corrispondente senza toccare il resto. L'unica modifica non
reversibile per peso e' il tetto hard D3, che va rimosso ripristinando il metodo
precedente.
