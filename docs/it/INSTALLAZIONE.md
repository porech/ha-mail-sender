# Installazione e uso

HA Mail Sender salva mail precompilate e le invia tramite Gmail, con un limite
indipendente per ciascuna mail e un pulsante collegabile ad Alexa.

## 1. Collegare Gmail a Home Assistant

In **Impostazioni → Dispositivi e servizi**, cerca **Google Mail**. Se manca,
aggiungilo seguendo la [guida ufficiale](https://www.home-assistant.io/integrations/google_mail/):
servono un progetto Google Cloud con Gmail API abilitata, credenziali OAuth e
l'autorizzazione del tuo account. Essere collegati a Gmail nel browser non basta.

La configurazione OAuth richiede un intervento iniziale nell'account Google.
HA Mail Sender riutilizza quel collegamento: non richiede password Gmail, password
per app o credenziali SMTP aggiuntive.

Per un mittente personalizzato, configuralo e verificalo prima in Gmail, in
**Impostazioni → Visualizza tutte le impostazioni → Account e importazione →
Invia messaggio come**. La scelta del mittente non cambia l'account autenticato.

## 2. Installare HA Mail Sender

Richiede Home Assistant 2026.2.3 o successivo.

1. In HACS apri **⋮ → Repository personalizzati**.
2. Inserisci `https://github.com/porech/ha-mail-sender`, categoria **Integrazione**.
3. Scarica HA Mail Sender (abilita le versioni beta, se richiesto per questa prima
   versione) e riavvia Home Assistant.
4. In **Impostazioni → Dispositivi e servizi → Aggiungi integrazione**, cerca
   **HA Mail Sender**.
5. Dai un nome alla mail, seleziona l'account Google Mail e scegli un mittente
   verificato dall'elenco.
6. Inserisci destinatari, Cc/Ccn facoltativi, oggetto, testo e limite.

Durante la configurazione non viene inviata alcuna mail. Per aggiungerne un'altra,
aggiungi una nuova voce dell'integrazione. Per modificarla usa **Configura →
Modifica la mail**. Gli indirizzi sono separati da virgole, senza nomi visualizzati.
Il testo è semplice, anche su più righe; non viene interpretato come Jinja.

## 3. Collegare il comando vocale

Ogni mail crea un pulsante **Invia** e un sensore **Stato**. Esponi il pulsante
attraverso il collegamento Alexa che già utilizzi e crea una routine nell'app Alexa:
la frase scelta deve attivare la scena corrispondente al pulsante.

Se il pulsante non compare, crea uno **script di Home Assistant** che esegue
`button.press`, esponi quello ad Alexa e selezionalo come scena nella routine.
Gli [esempi](../../examples) usano nomi generici: seleziona le tue entità reali.
La frase si configura nell'app Alexa, gli altri campi in Home Assistant.

## 4. Evitare doppioni

Puoi scegliere una richiesta per giorno di calendario (fuso orario di Home
Assistant), un intervallo minimo in ore o nessun limite. Le richieste ripetute
vengono ignorate, senza invii differiti. Gli invii contemporanei vengono bloccati
anche quando il limite è disattivato.

Il blocco viene salvato prima dell'invio e conservato nei normali riavvii e nelle
ricariche dell'integrazione. Modificare la mail non azzera il blocco: viene applicata
la nuova regola alla data dell'ultimo tentativo.

Un errore o timeout può verificarsi dopo che Gmail ha accettato la mail. Per questo
anche gli errori consumano l'intervallo, senza ritentare automaticamente. Controlla
prima la cartella **Posta inviata**. Se serve, usa **Configura → Sblocca un invio
fallito o incerto** e conferma: lo sblocco permette un nuovo tentativo ma non invia
nulla. Un invio accettato non si può sbloccare con questa funzione.

Lo stato **Accettata da Gmail** indica che l'API ha restituito un identificativo,
non una conferma di consegna al destinatario. La risposta generica di Alexa non è
una conferma dell'invio: consulta il sensore. I dettagli di instradamento del tuo
alias restano quelli configurati in Gmail.

Questa prima versione ha test automatici con risposte Gmail simulate. L'invio
reale con il tuo account e il comando Alexa vanno ancora verificati sul tuo impianto.
