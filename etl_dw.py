import pandas as pd
import sqlite3

# Connessione al database relazionale locale SQLite (creato automaticamente se non esiste)
db_conn = sqlite3.connect('startup_dw.db')
db_cursor = db_conn.cursor()

# Abilitazione forzata dei vincoli di integrità referenziale (Foreign Keys)
db_cursor.execute("PRAGMA foreign_keys = ON;")

# Rigenerazione dello schema database (approccio batch distruttivo per il prototipo)
db_cursor.executescript("""
DROP TABLE IF EXISTS Fatto_Richieste;
DROP TABLE IF EXISTS Dim_Cliente;
DROP TABLE IF EXISTS Dim_Fornitore;
DROP TABLE IF EXISTS Dim_Operatore;
DROP TABLE IF EXISTS Dim_Tempo;

-- Creazione della tabella per la dimensione Cliente
CREATE TABLE Dim_Cliente (
    id_cliente TEXT PRIMARY KEY,
    zona TEXT,
    data_iscrizione TEXT
);

-- Creazione della tabella per la dimensione Fornitore
CREATE TABLE Dim_Fornitore (
    id_fornitore TEXT PRIMARY KEY,
    nome TEXT,
    categoria_servizio TEXT,
    zona TEXT
);

-- Creazione della tabella per la dimensione Operatore
CREATE TABLE Dim_Operatore (
    id_operatore TEXT PRIMARY KEY,
    zona TEXT,
    tipo_attivita TEXT
);

-- Creazione della tabella per la dimensione temporale cronologica
CREATE TABLE Dim_Tempo (
    id_tempo TEXT PRIMARY KEY,
    data TEXT,
    anno INTEGER,
    mese INTEGER,
    giorno_settimana TEXT,
    ora INTEGER
);

-- Creazione della tabella dei fatti centrale con relazioni esterne verso le dimensioni
CREATE TABLE Fatto_Richieste (
    id_richiesta TEXT PRIMARY KEY,
    id_cliente TEXT,
    id_fornitore TEXT,
    id_operatore TEXT,
    id_tempo TEXT,
    importo REAL,
    tempo_erogazione_min INTEGER,
    stato TEXT,
    FOREIGN KEY (id_cliente) REFERENCES Dim_Cliente(id_cliente),
    FOREIGN KEY (id_fornitore) REFERENCES Dim_Fornitore(id_fornitore),
    FOREIGN KEY (id_operatore) REFERENCES Dim_Operatore(id_operatore),
    FOREIGN KEY (id_tempo) REFERENCES Dim_Tempo(id_tempo)
);
""")

# --- FASE 1: ESTRAZIONE (Extraction) ---
# Caricamento dei dati dai file sorgenti piatti (CSV)
src_clienti = pd.read_csv('clienti.csv')
src_fornitori = pd.read_csv('fornitori.csv')
src_operatori = pd.read_csv('operatori.csv')
src_richieste = pd.read_csv('richieste.csv')

# --- FASE 2: TRASFORMAZIONE (Transformation) ---
# Gestione dei valori mancanti: i tempi di erogazione nulli (richieste annullate) vengono normalizzati a 0
src_richieste['tempo_erogazione_min'] = src_richieste['tempo_erogazione_min'].fillna(0).astype(int)

# Parsing dei timestamp operativi in oggetti datetime
src_richieste['datetime_parsed'] = pd.to_datetime(src_richieste['data_ora'])

# Generazione dei record per la dimensione temporale
df_dim_tempo = pd.DataFrame()
df_dim_tempo['id_tempo'] = src_richieste['datetime_parsed'].dt.strftime('%Y%m%d%H')
df_dim_tempo['data'] = src_richieste['datetime_parsed'].dt.strftime('%Y-%m-%d')
df_dim_tempo['anno'] = src_richieste['datetime_parsed'].dt.year
df_dim_tempo['mese'] = src_richieste['datetime_parsed'].dt.month
df_dim_tempo['giorno_settimana'] = src_richieste['datetime_parsed'].dt.day_name()
df_dim_tempo['ora'] = src_richieste['datetime_parsed'].dt.hour

# Rimozione dei duplicati temporali per rispettare il vincolo di chiave primaria univoca
df_dim_tempo = df_dim_tempo.drop_duplicates(subset=['id_tempo']).reset_index(drop=True)

# Calcolo della chiave di giunzione temporale (id_tempo) anche per la tabella dei fatti
src_richieste['id_tempo'] = src_richieste['datetime_parsed'].dt.strftime('%Y%m%d%H')

# Selezione e mappatura dei campi definitivi per la tabella dei fatti centrale
df_fact_richieste = src_richieste[[
    'id_richiesta', 'id_cliente', 'id_fornitore', 'id_operatore', 
    'id_tempo', 'importo', 'tempo_erogazione_min', 'stato'
]]

# --- FASE 3: CARICAMENTO (Loading) ---
# Popolamento delle tabelle del Data Warehouse
src_clienti.to_sql('Dim_Cliente', db_conn, if_exists='append', index=False)
src_fornitori.to_sql('Dim_Fornitore', db_conn, if_exists='append', index=False)
src_operatori.to_sql('Dim_Operatore', db_conn, if_exists='append', index=False)
df_dim_tempo.to_sql('Dim_Tempo', db_conn, if_exists='append', index=False)
df_fact_richieste.to_sql('Fatto_Richieste', db_conn, if_exists='append', index=False)

# Salvataggio delle modifiche e rilascio delle risorse di rete/connessione
src_clienti.to_csv("clienti.csv", index=False)
src_fornitori.to_csv("fornitori.csv", index=False)
src_operatori.to_csv("operatori.csv", index=False)
df_dim_tempo.to_csv("dim_tempo.csv", index=False)
df_fact_richieste.to_csv("fatto_richieste.csv", index=False)
# Conferma modifiche sul database e chiusura connesione
db_conn.commit()
db_conn.close()
print("[SUCCESS] Pipeline ETL completata. Data Warehouse relazionale 'startup_dw.db' e file CSV aggiornati!")
