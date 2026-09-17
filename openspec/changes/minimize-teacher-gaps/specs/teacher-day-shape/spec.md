## MODIFIED Requirements

### Requirement: I buchi oltre il primo sono fortemente penalizzati
Il sistema SHALL calcolare come buco ogni slot senza lezione compreso fra due slot
con lezione dello stesso docente nello stesso giorno, **escludendo gli slot in cui
il docente e' indisponibile**: in quelle ore il docente non e' a scuola e non sta
attendendo. Ogni giornata dispone di una franchigia di un'ora di buco alle
condizioni definite dal requisito sulla franchigia. Il sistema SHALL penalizzare
le ore di buco eccedenti la franchigia della giornata in misura superiore a quanto
ogni altro criterio sulla forma della giornata possa complessivamente guadagnare
in quella stessa giornata, cosi' che nessun altro criterio possa giustificare una
seconda ora di buco.

#### Scenario: Buco singolo contro buco doppio
- **WHEN** i vincoli hard consentono per un docente in un giorno sia una disposizione con un'ora di buco sia una con due ore di buco consecutive, a parita' di ogni altra dimensione
- **THEN** il sistema genera la disposizione con una sola ora di buco

#### Scenario: Due buchi separati nella stessa giornata
- **WHEN** i vincoli hard consentono per un docente in un giorno sia una disposizione con un solo intervallo libero fra le lezioni sia una con due intervalli liberi separati da lezioni
- **THEN** il sistema genera la disposizione con un solo intervallo libero

#### Scenario: Una seconda ora di buco non e' comprabile
- **WHEN** una disposizione con due ore di buco in una giornata migliorerebbe per quel docente la contiguita' delle classi, il bilanciamento del carico o la preferenza di fascia oraria
- **THEN** il sistema genera comunque una disposizione che non supera la franchigia di quella giornata

#### Scenario: Ore libere a inizio o fine giornata non sono buchi
- **WHEN** un docente ha ore libere prima della sua prima lezione o dopo la sua ultima lezione del giorno
- **THEN** il sistema non conteggia quelle ore come buchi

#### Scenario: Ora di indisponibilita' fra due lezioni
- **WHEN** un docente ha una lezione prima e una lezione dopo uno slot in cui e' indisponibile
- **THEN** il sistema non conteggia quello slot come buco e non lo somma alla franchigia della giornata

#### Scenario: Attesa reale accanto a un'indisponibilita'
- **WHEN** fra due lezioni di un docente ricadono sia uno slot di indisponibilita' sia uno slot libero in cui il docente potrebbe insegnare
- **THEN** il sistema conteggia come buco il solo slot libero

## ADDED Requirements

### Requirement: La franchigia di un'ora di buco spetta alle giornate lunghe
Il sistema SHALL riconoscere la franchigia di un'ora di buco alle sole giornate in
cui il docente svolge un numero di ore di lezione pari o superiore alla soglia
oltre la quale una filata continua di lezioni e' considerata troppo lunga. Nelle
giornate al di sotto di quella soglia la franchigia SHALL essere nulla e gia' la
prima ora di buco SHALL essere penalizzata come un'ora eccedente. Il sistema SHALL
derivare da questa regola la proporzionalita' fra monte ore e buchi, senza un
criterio separato sul monte ore settimanale.

#### Scenario: Giornata lunga
- **WHEN** un docente svolge in un giorno un numero di ore pari o superiore alla soglia di filata lunga e i vincoli hard consentono di collocarvi un'ora libera intermedia
- **THEN** il sistema puo' generare la giornata con quell'ora libera senza che questa sia trattata come un difetto

#### Scenario: Giornata corta
- **WHEN** un docente svolge in un giorno un numero di ore inferiore alla soglia di filata lunga
- **THEN** il sistema genera quelle ore senza alcuna ora libera intermedia, salvo che i vincoli hard non lo consentano

#### Scenario: Docente con monte ore ridotto
- **WHEN** un docente ha un monte ore settimanale che le sue giornate lavorabili distribuiscono tutte al di sotto della soglia di filata lunga
- **THEN** il sistema genera per quel docente una settimana priva di buchi, salvo che i vincoli hard non lo consentano

### Requirement: Le preferenze sui buchi agiscono sulla settimana
Il sistema SHALL applicare i criteri sulla forma della giornata a ogni docente,
qualunque sia la sua preferenza di scheduling, inclusa l'assenza di preferenza. Le
preferenze di raggruppamento e di distribuzione SHALL agire sul numero di giornate
della settimana che utilizzano la propria franchigia, non sull'intensita' dei
criteri interni alla giornata: la preferenza di raggruppamento SHALL ridurre il
numero di giornate con un'ora di buco, la preferenza di distribuzione SHALL
aumentarlo fino a una giornata lunga con il proprio stacco. Nessuna preferenza
SHALL consentire il superamento della franchigia di una giornata, ne' influire sul
criterio di contiguita' delle ore della stessa classe.

#### Scenario: Docente senza preferenza
- **WHEN** un docente non ha impostato alcuna preferenza di scheduling
- **THEN** il sistema applica comunque i criteri di contiguita', filata e buco alla sua giornata e mantiene contenuto il numero di giornate con un'ora di buco

#### Scenario: Preferenza di distribuzione
- **WHEN** un docente ha impostato la preferenza di distribuzione delle lezioni e i vincoli hard consentono di collocare un'ora libera in piu' di una delle sue giornate lunghe
- **THEN** il sistema gli assegna un'ora libera in ciascuna di quelle giornate anziche' concentrare piu' ore libere in una sola

#### Scenario: La preferenza di distribuzione non supera la franchigia
- **WHEN** un docente ha impostato la preferenza di distribuzione delle lezioni
- **THEN** il sistema non genera per lui alcuna giornata con piu' di un'ora di buco, ne' alcuna ora di buco in una giornata corta

#### Scenario: Preferenza di raggruppamento
- **WHEN** un docente ha impostato la preferenza di raggruppamento delle lezioni
- **THEN** il sistema riduce per lui il numero di giornate con un'ora di buco rispetto a un docente senza preferenza, a parita' di ogni altra condizione

#### Scenario: Le preferenze sui buchi non toccano la contiguita' delle classi
- **WHEN** due docenti con lo stesso orario di lezione hanno preferenze sui buchi diverse
- **THEN** il sistema applica a entrambi la stessa intensita' di criterio sulla contiguita' delle ore svolte in una stessa classe

## REMOVED Requirements

### Requirement: Le preferenze sui buchi modulano la forma della giornata
**Reason**: Le preferenze di raggruppamento e distribuzione agivano come
moltiplicatori sull'intensita' di tutti i criteri interni alla giornata, buchi e
contiguita' delle classi insieme. Questo consentiva a un docente con preferenza di
distribuzione di ottenere piu' ore di buco nella stessa giornata - esito che i
criteri assoluti sui buchi ora vietano a chiunque - e legava la contiguita' delle
classi a una preferenza che non la riguarda.

**Migration**: Sostituito da "Le preferenze sui buchi agiscono sulla settimana". I
valori dell'enum delle preferenze restano invariati e nessun dato utente viene
perso: cambia solo l'effetto che il sistema attribuisce loro. Un docente con
preferenza di distribuzione passa da giornate piu' frammentate a un'ora di stacco
distribuita su piu' giornate lunghe.
