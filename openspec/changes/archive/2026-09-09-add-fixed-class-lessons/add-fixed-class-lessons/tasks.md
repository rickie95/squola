## 1. Persistenza e API dei vincoli fissi

- [x] 1.1 Creare la migrazione Alembic per `fixed_class_lessons`, con riferimenti a workspace, classe e assegnamento e unicita' della cella classe-giorno-ora; verificare che `uv run alembic upgrade head` completi correttamente su un database vuoto.
- [x] 1.2 Aggiungere il modello SQLAlchemy, le relazioni e gli schemi Pydantic per leggere e scrivere una lezione fissa, includendola nel dettaglio della classe; verificare con test di serializzazione e recupero del dettaglio classe.
- [x] 1.3 Implementare endpoint annidati per creare, sostituire e rimuovere una lezione fissa di una classe, con controlli di appartenenza a classe e workspace, range di giorno/ora e unicita' della cella; verificare con test API per creazione, aggiornamento, cancellazione e isolamento tra workspace.
- [x] 1.4 Validare nelle mutazioni i conflitti con indisponibilita' e vincoli fissi dello stesso docente, nonche' il limite di slot fissi rispetto a `hours_per_week`; verificare con test API che gli errori non alterino i vincoli esistenti.
- [x] 1.5 Rendere coerenti aggiornamento, eliminazione e clonazione degli assegnamenti: rifiutare la riduzione del monte ore incompatibile, eliminare i relativi vincoli e non copiarli nella classe clonata; verificare ogni caso con test API.

## 2. Integrazione nel generatore

- [x] 2.1 Caricare le lezioni fisse del workspace nei dati di scheduling con le relazioni necessarie; verificare con un test unitario che siano disponibili al generatore.
- [x] 2.2 Aggiungere per ogni lezione fissa il vincolo hard CP-SAT sul corrispondente assegnamento, giorno e ora; verificare con un test del solver che due ore fisse consecutive compaiano nello stesso slot dell'orario generato.
- [x] 2.3 Verificare che i vincoli fissi continuino a rispettare i vincoli esistenti e che una combinazione globalmente non realizzabile restituisca lo stato di non fattibilita'; verificare con test mirati del solver e dell'endpoint di generazione.

## 3. Interfaccia di configurazione classe

- [x] 3.1 Estendere tipi TypeScript e client API per le lezioni fisse e le rispettive mutazioni; verificare con `cd frontend && npm run build`.
- [x] 3.2 Aggiungere nella scheda classe una griglia Lunedi'-Venerdi' e sei slot orari, con selezione limitata agli assegnamenti materia-docente della classe; verificare manualmente che una cella vuota offra solo tali assegnamenti.
- [x] 3.3 Collegare selezione, sostituzione e rimozione delle celle alle mutazioni API, aggiornando il dettaglio della classe dopo il risultato; verificare manualmente che gli errori di conflitto siano visibili e che la griglia resti sincronizzata.

## 4. Verifica complessiva

- [x] 4.1 Eseguire `uv run pytest tests/` e `cd frontend && npm run build`, correggendo eventuali regressioni nelle funzioni di classi e generazione orario.
