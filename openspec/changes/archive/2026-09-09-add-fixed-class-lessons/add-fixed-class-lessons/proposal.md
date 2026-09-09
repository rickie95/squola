## Why

La generazione automatica non consente di preservare lezioni gia' decise dalla scuola. Gli utenti devono poter fissare insegnamenti di una classe in specifici giorni e ore prima di generare l'orario, senza che il solver li possa spostare.

## What Changes

- Aggiungere una griglia settimanale modificabile nella scheda di ogni classe, con una selezione per cella limitata agli insegnamenti gia' assegnati alla classe.
- Persistire le lezioni fissate come vincoli associati all'assegnamento classe-materia-docente, giorno e ora.
- Validare immediatamente conflitti tra vincoli fissi, indisponibilita' del docente e sovra-assegnazione rispetto alle ore settimanali della materia.
- Imporre tutte le lezioni fissate come vincoli hard nel generatore CP-SAT.
- Mantenere vuota la griglia dei vincoli fissi quando una classe viene clonata.
- Eliminare i vincoli fissi collegati quando viene rimossa la relativa assegnazione materia dalla classe e rifiutare una riduzione delle ore settimanali sotto il numero di vincoli esistenti.

## Capabilities

### New Capabilities

- `fixed-class-lessons`: Definisce la configurazione, validazione e applicazione di lezioni fisse per una classe prima della generazione dell'orario.

### Modified Capabilities

<!-- Nessuna capacita' OpenSpec esistente richiede modifiche. -->

## Impact

- Modelli SQLAlchemy e migrazione Alembic per le lezioni fisse.
- Schemi Pydantic e API della risorsa classi per leggere, creare, aggiornare ed eliminare i vincoli.
- Pagina React di gestione classi, tipi frontend e client API.
- Caricamento dati e vincoli hard in `src/squola/scheduler.py`.
- Test di API, isolamento per workspace e comportamento del solver.
