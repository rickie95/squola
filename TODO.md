# TODO
- [X] traduzione in italiano
- [X] giorni blacklist per insegnante (es insegnanti in COE)
- [ ] preferenze/vincoli multipli per singolo insegnante
- [ ] giorno libero a caso
- [ ] ottimizzazione a partire da bozza
- [ ] supporto classi con ore aggiuntive
- [ ] persistere i metadata dell'orario in db
      Oggi `save_schedule_to_db` (`src/squola/scheduler.py`) salva solo
      `schedule_dict["schedule"]` in `SavedSchedule.schedule_data`: i metadata
      restituiti da `GeneratedSchedule.to_dict()` vivono solo nella risposta HTTP.
      `SavedSchedule` ha gia' colonne per `status`, `solve_time_seconds` e
      `total_slots`, ma non per le metriche di qualita' dell'orario
      (cambi di classe, ore di buco, scostamento dal bilanciamento giornaliero).
      Serve per confrontare fra loro orari salvati e capire se una nuova taratura
      dei pesi del solver ha migliorato o peggiorato i risultati.
      Rimandato: per la sola taratura basta il breakdown nella risposta.
      Quando si fa: migrazione Alembic con le colonne delle metriche, non
      infilarle dentro il JSON di `schedule_data`.
