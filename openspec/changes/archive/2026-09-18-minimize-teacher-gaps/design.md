## Context

Vedi `proposal.md` - Why per le motivazioni. Qui contano tre fatti del modello
attuale in `src/squola/scheduler.py`.

`_add_gap_terms` costruisce gia' la grandezza giusta. Due catene monotone
`before[h]` / `after[h]` per coppia docente-giorno individuano gli slot liberi
incastrati fra due lezioni, e una variabile intera raccoglie quelli oltre il
primo:

```
extra >= sum(day_gaps) - 1
```

I tre principi interni alla giornata - un buco va bene, due ore di buco no, due
buchi separati no - sono la stessa grandezza: `sum(day_gaps)`. Un intervallo da
due ore e due intervalli da un'ora valgono entrambi due ore di buco. Non serve
introdurre il concetto di intervallo, ne' contare gli intervalli separatamente:
la regola e' "al massimo un'ora di buco al giorno" e la variabile che la misura
esiste gia'. Questo change ricalibra e condiziona quella variabile, non ne
aggiunge una categoria nuova.

I pesi sono commentati come puramente relativi: il solver confronta alternative e
non legge mai un costo assoluto. Questo rende la dominanza esprimibile come
disuguaglianza fra costanti invece che come vincolo hard.

`ScheduleGenerator.__init__` popola gia' `self.unavailable` come insieme di
triple `(teacher_id, day, hour)`.

## Goals / Non-Goals

**Goals:**
- Rendere non acquistabile la seconda ora di buco di una giornata, per
  costruzione della funzione obiettivo e non per taratura empirica.
- Ottenere la proporzionalita' fra monte ore e buchi come conseguenza di una
  regola gia' presente, senza un secondo meccanismo da tenere sincronizzato.
- Lasciare il modello diagnosticabile: chi legge la risposta di generazione deve
  distinguere lo stacco voluto dal buco subito.

**Non-Goals:**
- Nessun vincolo hard sui buchi. La banda 2-5 ore giornaliere e' gia' stretta e i
  docenti sono accoppiati dal no-overlap sulle classi; un vincolo hard
  trasformerebbe un orario mediocre in un fallimento di generazione, che per
  l'utente e' peggio.
- Nessuna modifica all'enum `SchedulePreference`, quindi nessuna migrazione.
- Nessuna persistenza delle metriche: resta valido il requisito esistente.

## Decisions

### 1. Gli slot di indisponibilita' non generano buchi, ma non spezzano la giornata

La `gap` var non viene creata per gli slot in `self.unavailable`; le catene
`before` / `after` restano guidate dalle sole ore di lezione.

La conseguenza va notata perche' non e' neutra: se un docente insegna alla 1a e
alla 5a ora ed e' indisponibile dalla 2a alla 4a, la giornata ha zero buchi. Se
invece e' indisponibile alla 3a e libero alla 2a e alla 4a, le ore di buco sono
due e la giornata sfora la franchigia. La regola e' quindi "si conta solo il
tempo in cui il docente potrebbe insegnare e non insegna", che e' esattamente il
tempo che il docente percepisce come perso.

*Alternativa scartata*: trattare l'indisponibilita' come separatore di giornata,
valutando i segmenti prima e dopo in modo indipendente. Avrebbe reso possibile
una franchigia per segmento, cioe' due ore di buco in una giornata per la porta
di servizio, contro il principio assoluto.

### 2. La franchigia e' condizionata al carico della giornata, non al monte ore

Una bool `allowance[teacher, day]`, reificata su `sum(occupied) >= LONG_RUN_WINDOW`,
sostituisce la costante:

```
extra >= sum(day_gaps) - allowance[day]
```

La soglia riusa `LONG_RUN_WINDOW` invece di introdurne una propria: e' gia' la
definizione di "giornata che vale la pena spezzare", ed e' la soglia oltre la
quale il termine sulle filate lunghe comincia a spingere verso lo stacco. Due
soglie diverse metterebbero i due termini a litigare in un intervallo di
lunghezze.

La condizione e' sul carico della giornata, non sulla sua disposizione, quindi
non e' circolare: una giornata da quattro ore matura la franchigia sia disposta
`4` consecutive sia disposta `2 + buco + 2`, ed e' il confronto fra le due a
decidere.

*Alternativa scartata*: un budget settimanale di ore di buco proporzionale al
monte ore, del tipo `max_gap_hours = f(weekly_hours)`. Avrebbe richiesto una
funzione da tarare, una variabile di accumulo settimanale, e avrebbe lasciato al
solver la liberta' di spendere l'intero budget in una giornata sola - di nuovo
contro il principio assoluto. La regola per giornata produce la stessa
proporzionalita' come effetto emergente: chi ha poche ore ha giornate corte, chi
ha giornate corte non matura la franchigia, quindi non ha buchi. Il docente da 8
ore settimanali dell'esempio ha giornate da 2 ore e finisce a zero buchi senza
che nulla parli di 8 ore da nessuna parte.

### 3. Il peso sull'eccedenza si calcola, non si tara

`W_EXCESS_GAP` viene derivato dagli altri pesi invece di essere un numero scelto
a mano, cosi' che non possa scollarsi da loro quando uno degli altri cambia:

```
W_EXCESS_GAP = 1 + DAYS_OF_WEEK * (
      HOURS_PER_DAY * W_CLASS_BLOCK
    + (HOURS_PER_DAY - LONG_RUN_WINDOW + 1) * W_LONG_RUN
    + HOURS_PER_DAY * W_DAILY_BALANCE
    + sum(W_TIME_PREFERENCE * (h - 1) for h in 1..HOURS_PER_DAY)
    + W_BREAK_DAY
)
```

Ogni addendo e' il massimo che quel termine puo' valere in una giornata per un
docente; il fattore `DAYS_OF_WEEK` estende il limite alla settimana e l'`1` finale
rende la disuguaglianza stretta. Con i pesi attuali vale circa 950.

Il fattore settimanale non e' prudenza eccessiva: spostare una lezione per creare
un buco nel giorno D cambia anche il giorno E, quindi un limite calcolato sulla
sola giornata D non sarebbe una dimostrazione ma una stima. Il costo di un
coefficiente piu' grande e' un intero piu' largo nel modello, non tempo di
soluzione.

Il valore va lasciato come espressione leggibile nel modulo, non come letterale:
il numero in se' non significa nulla, la sua derivazione si'.

*Alternativa scartata*: vincolo hard `sum(day_gaps) <= allowance`. Piu' semplice
da leggere, ma un orario con un buco di troppo diventa `INFEASIBLE` e l'utente
perde l'intero orario invece di vedere un difetto localizzato. Con il peso
dominante il difetto resta visibile nelle metriche, che e' la forma di fallimento
che questo progetto ha gia' scelto altrove.

### 4. Le preferenze diventano un termine proprio e `_shape_weight` sparisce

`_shape_weight` scalava contemporaneamente `W_GAP`, `W_EXTRA_GAP` e
`W_CLASS_BLOCK`. Viene rimosso e sostituito da un solo termine per coppia
docente-giorno, definito sulla franchigia:

```
NONE           penalizza  break_day                    peso W_BREAK_DAY
MINIMIZE_GAPS  penalizza  break_day                    peso W_BREAK_DAY_STRICT
MAXIMIZE_GAPS  penalizza  allowance AND NOT break_day  peso W_BREAK_DAY
```

`break_day` e' la bool "questa giornata usa la sua franchigia". La somma di questo
termine e' settimanale per costruzione, che e' la semantica corretta: la
preferenza di distribuzione chiede uno stacco al giorno su tutta la settimana, e
non puo' chiedere altro perche' la seconda ora di buco e' fuori portata per
chiunque.

La calibrazione dei due pesi non e' libera. Nelle sole giornate che maturano la
franchigia lo stacco elimina sempre almeno una filata lunga, perche' quattro ore
senza buco in sei slot sono necessariamente consecutive:

```
  4 ore senza stacco -> 1 finestra = W_LONG_RUN      guadagno dello stacco:  6
  5 ore senza stacco -> 2 finestre = 2 * W_LONG_RUN  guadagno dello stacco: 12
```

`W_BREAK_DAY` deve quindi restare sotto il guadagno minore, altrimenti nessun
docente prenderebbe mai lo stacco e la franchigia sarebbe lettera morta.
`W_BREAK_DAY_STRICT` si colloca invece **fra i due guadagni**: il docente con
preferenza di raggruppamento tiene le quattro ore consecutive e spezza solo la
giornata da cinque. Con `W_TIME_PREFERENCE = 1` e uno spostamento di fascia di al
piu' due unita':

```
  W_BREAK_DAY        + 2 <  6      ->  W_BREAK_DAY = 1
  6 <  W_BREAK_DAY_STRICT + 2 < 12  ->  W_BREAK_DAY_STRICT = 8
```

Questa e' l'unica banda in cui la preferenza di raggruppamento produce un effetto
osservabile: sotto il guadagno minore si comporta come l'assenza di preferenza,
sopra il maggiore elimina lo stacco anche dalle giornate da cinque ore, che
nessuno ha chiesto. Il requisito sulle filate lunghe viene modificato di
conseguenza, per esentare quella preferenza dalla giornata da quattro ore.

Ancorare il ramo `MAXIMIZE_GAPS` ad `allowance` fa doppio lavoro: nelle giornate
corte il termine e' identicamente zero, quindi la preferenza non spinge verso un
buco che costerebbe `W_EXCESS_GAP`, e non serve una regola esplicita per il caso.

La rimozione della modulazione su `W_CLASS_BLOCK` e' un effetto voluto e non
collaterale: la contiguita' delle ore di una stessa classe non ha rapporto con la
preferenza sui buchi, e legarla produceva orari sistematicamente diversi fra
docenti per una ragione che nessuno aveva chiesto.

Questo inverte il segno sulla prima ora di buco per `MAXIMIZE_GAPS` e quindi
rimuove il requisito esistente che lo vietava. L'invariante che resta - e che
conta - e' che nessuna preferenza puo' superare la franchigia.

### 5. L'assert si riformula sul peso effettivo

`assert W_LONG_RUN > W_GAP + 2 * W_TIME_PREFERENCE` confronta il peso base con
una soglia, ma il modello applicava il peso modulato. Per un docente
`MINIMIZE_GAPS` con preferenza oraria vale `6 > 2*2 + 2`, cioe' `6 > 6`, falso:
lo stacco nella giornata da quattro ore non veniva mai comprato e l'assert
passava lo stesso.

Con `_shape_weight` rimosso il peso e' uniforme e il confronto torna
significativo, ma la relazione va riscritta sulle costanti nuove e sdoppiata,
perche' i due pesi sullo stacco hanno ora soglie diverse:

```
W_LONG_RUN     > W_BREAK_DAY        + 2 * W_TIME_PREFERENCE
2 * W_LONG_RUN > W_BREAK_DAY_STRICT + 2 * W_TIME_PREFERENCE > W_LONG_RUN
```

La prima riga garantisce lo stacco nella giornata da quattro ore a chi non ha
preferenza di raggruppamento; la seconda colloca `W_BREAK_DAY_STRICT` nella banda
in cui quella preferenza agisce sulle sole giornate da cinque ore. Entrambe vanno
verificate da un assert di modulo, cosi' che una futura ritaratura di
`W_LONG_RUN` non le rompa in silenzio.

### 6. `compute_quality_metrics` riceve le indisponibilita'

La funzione calcola le metriche dai soli slot per poterle asserire nei test senza
costruire un modello. Le indisponibilita' non sono ricostruibili dagli slot, come
gia' non lo erano i giorni lavorabili: prendono la stessa strada, un argomento
esplicito, con la stessa motivazione gia' documentata nella docstring. Senza,
la diagnostica conterebbe buchi che il solver non penalizza.

## Risks / Trade-offs

**Il peso dominante irrigidisce una sola dimensione e rallenta la convergenza**
-> Misurato su 18 docenti, 15 classi, 108 assegnazioni, 360 ore. La costruzione
del modello non cambia (0,25s prima, 0,27s dopo) e l'esito resta `FEASIBLE` in
entrambi i casi, ma il resto dell'obiettivo converge piu' lentamente perche' il
solver spende il budget sulla dimensione dominante:

```
                     prima      dopo @30s   dopo @120s
  ore di buco          74            -            -
  excess_gap_hours      -            0            0
  class_blocks          6           11            6
  long_runs            17           36           25
```

A 30 secondi la qualita' sulle dimensioni minori e' visibilmente peggiore; a 120
secondi `class_blocks` torna al valore precedente e `long_runs` recupera in gran
parte. La differenza residua sulle filate lunghe e' in parte voluta: i docenti con
preferenza di raggruppamento ora tengono le quattro ore consecutive per
costruzione. Chi genera con un budget breve va avvisato che la resa peggiora, il
che rende la scomposizione delle metriche non solo utile ma necessaria.

**I test esistenti usano `time_limit_seconds: 3`** -> Con un termine dominante il
solver puo' impiegare piu' tempo a chiudere il gap e restituire soluzioni
diverse fra esecuzioni. I test che asserivano la vecchia curva di costo vanno
riscritti su proprieta' - "nessuna giornata supera la franchigia" - e non su
disposizioni esatte.

**Orari oggi accettabili diventano diversi** -> E' l'obiettivo del change, ma
l'utente lo percepira' come contiguita' o bilanciamento peggiorati in cambio di
buchi rimossi. Le metriche scomposte servono anche a questo: rendono visibile
cosa e' stato scambiato con cosa.

**Un docente con indisponibilita' frammentate puo' restare infeasible di fatto**
-> Il buco resta soft, quindi non c'e' infeasibility; l'orario sfora la
franchigia e la coppia docente-giorno compare fra le peggiori. E' il
comportamento voluto: il difetto e' dei dati in ingresso e va mostrato, non
nascosto.

## Migration Plan

1. Archiviare `improve-schedule-quality` (28/28 task completi) per sincronizzare
   `teacher-day-shape` e `schedule-quality-metrics` in `openspec/specs/`.
   `openspec validate minimize-teacher-gaps --strict` lo segnala gia': i `MODIFIED`
   di questo change non trovano oggi il requisito da modificare.
2. Applicare questo change.
3. Nessun rollback dei dati necessario: il change tocca solo la costruzione del
   modello e la diagnostica. Tornare indietro significa ripristinare il codice e
   rigenerare gli orari; quelli salvati restano leggibili perche' le metriche non
   sono persistite.
