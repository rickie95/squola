## Context

La generazione modella ogni assegnamento classe-materia-docente con una variabile booleana per giorno e ora. La pagina delle classi gia' carica gli assegnamenti della classe selezionata; i vincoli esistenti riguardano indisponibilita' docente, sovrapposizioni e monte ore. Vedere `proposal.md` per la motivazione e `specs/fixed-class-lessons/spec.md` per il comportamento richiesto.

## Goals / Non-Goals

**Goals:**

- Rendere persistenti e modificabili le lezioni predefinite per ogni classe.
- Garantire al salvataggio gli errori determinabili localmente o confrontando i vincoli fissi del workspace.
- Rendere impossibile per il solver spostare o omettere una lezione fissa.
- Conservare l'isolamento tra workspace in tutte le letture e validazioni.

**Non-Goals:**

- Modificare gli orari gia' generati o usarli come fonte di vincoli.
- Consentire di fissare materia e docente separatamente da un assegnamento esistente.
- Risolvere automaticamente configurazioni globalmente non realizzabili; il generatore continuera' a restituire il suo errore di non fattibilita'.
- Copiare i vincoli fissi nella clonazione di una classe.

## Decisions

### Entita' dedicata legata all'assegnamento

Viene introdotta una tabella `fixed_class_lessons` con `workspace_id`, `class_id`, `assignment_id`, `day_of_week` e `hour_slot`. Un vincolo univoco su `(class_id, day_of_week, hour_slot)` rappresenta l'unica lezione possibile in una cella.

L'assegnamento, anziche' materia e docente duplicati, e' il riferimento della lezione: preserva l'identita' della materia e del docente e assicura che ogni lezione fissa contribuisca alle ore dello stesso assegnamento. Il `class_id` resta denormalizzato per vincolo di unicita', interrogazioni della griglia e validazione rapida; l'API verifica sempre che corrisponda alla classe dell'assegnamento.

Alternativa considerata: memorizzare una matrice JSON nella classe. E' scartata perche' non permette vincoli di unicita', join, cancellazioni coerenti e controlli concorrenti affidabili.

### API CRUD annidata nelle classi

La risposta dettagliata di una classe includera' le sue lezioni fisse, complete delle informazioni dell'assegnamento necessarie alla griglia. Endpoint annidati permetteranno creazione, sostituzione e cancellazione di una singola cella sotto `/classes/{class_id}/fixed-lessons`.

La sostituzione riusa l'identita' della cella e passa attraverso la stessa validazione della creazione. Questo evita invii completi della griglia e riduce il rischio di sovrascrivere modifiche indipendenti.

Alternativa considerata: un endpoint `PUT` che sostituisce l'intera griglia. E' scartata perche' richiede validazioni aggregate e rende piu' probabili perdite di modifiche lato client.

### Validazione transazionale prima del salvataggio

La creazione o modifica contera' le lezioni gia' fissate dell'assegnamento, escludendo la risorsa in aggiornamento, e confrontera' il nuovo totale con `hours_per_week`. Verifichera' inoltre l'indisponibilita' del docente e le lezioni fisse di altri assegnamenti dello stesso docente nello stesso workspace, giorno e ora. Le query includeranno sempre `workspace_id`.

L'unicita' della cella di classe e' protetta anche a livello database. I conflitti tra docenti vengono controllati dall'applicazione per produrre un errore utile; il solver resta la protezione finale per le interazioni con i vincoli non fissi.

Quando un assegnamento viene eliminato, il servizio elimina prima le sue lezioni fisse nella stessa transazione. Quando le sue ore vengono ridotte, esegue il conteggio prima dell'aggiornamento e lo rifiuta se necessario. La clonazione non crea righe `fixed_class_lessons`.

### Vincoli CP-SAT espliciti

Il caricamento dati includera' le lezioni fisse con i relativi assegnamenti. Dopo la creazione delle variabili del solver, per ogni vincolo verrà aggiunto `x[assignment_id, day_of_week, hour_slot] == 1`, prima della risoluzione. Gli attuali vincoli di monte ore, non sovrapposizione e indisponibilita' continuano quindi a verificare la configurazione e possono rendere il modello non fattibile senza ammorbidire le lezioni fissate.

Alternativa considerata: preferenza ad alto peso nell'obiettivo. E' scartata perche' puo' essere sacrificata per produrre un risultato e non garantisce l'immobilita' richiesta.

### Griglia di configurazione nella scheda classe

`ClassesPage` riutilizzera' le stesse cinque colonne di giorni e sei righe orarie della visualizzazione dell'orario. Ogni cella vuota offrira' un controllo per scegliere un assegnamento della classe; una cella valorizzata mostrera' materia e docente e permettera' modifica o rimozione. Dopo una mutazione riuscita, il dettaglio della classe verra' aggiornato dalla sorgente server.

Alternativa considerata: un modal separato per ciascuna lezione. E' scartata perche' nasconde il contesto della settimana e non soddisfa l'interazione diretta richiesta.

## Risks / Trade-offs

- [I vincoli fissi passano i controlli locali ma rendono impossibile l'intero orario] -> Il solver restituisce il normale esito di non fattibilita'; la UI conserva i vincoli per poterli correggere.
- [Riduzione delle ore o rimozione di assegnamenti lascia riferimenti orfani] -> Le operazioni di aggiornamento e cancellazione gestiscono le lezioni fisse nella stessa transazione e sono coperte da test.
- [Due richieste concorrenti tentano di occupare la stessa cella] -> Il vincolo di unicita' database protegge la cella; il client ricarica il dettaglio dopo un errore o un salvataggio riuscito.
- [Nuove righe non isolate dal workspace] -> Tutte le query, endpoint e dati del solver filtrano per `workspace_id`, con test di isolamento dedicati.

## Migration Plan

1. Aggiungere la migrazione Alembic e distribuire la nuova tabella vuota senza modificare i dati esistenti.
2. Distribuire modello, API e interfaccia: le classi esistenti vedono inizialmente una griglia libera e mantengono invariato il comportamento di generazione se non configurano vincoli.
3. Distribuire il caricamento nel solver e i test; i nuovi vincoli diventano effettivi alla generazione successiva.
4. Per rollback applicativo, rimuovere prima l'uso della nuova API e del solver, quindi applicare il downgrade Alembic: non esiste conversione dei vincoli in dati dell'orario.
