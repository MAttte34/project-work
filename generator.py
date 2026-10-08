import pandas as pd 
import numpy as np 
from datetime import datetime, timedelta 
import random

np.random.seed(42) 
random.seed(42) 

zone_geo = ['LOMBARDIA', 'LAZIO', 'CALABRIA', 'SARDENA'] 
cat_servizio = ['Consegne', 'Manutenzione', 'Pulizie', 'Assistenza Tecnica'] 
tipo_att = ['Driver', 'Tecnico', 'Operatore Pulizie', 'Specialista'] 
stati_req = ['Completata', 'Completata', 'Completata', 'Annullata'] 
data_start = datetime(2025, 1, 1) 

clienti = [] 
for i in range(1, 401): 
    giorni_offset = random.randint(0, 300) 
    clienti.append({ 
        'id_cliente': f'CLI_{i:03d}', 
        'zona': random.choice(zone_geo), 
        'data_iscrizione': (data_start + timedelta(days=giorni_offset)).strftime('%Y-%m-%d') 
    }) 
df_clienti = pd.DataFrame(clienti) 

df_fornitori = pd.DataFrame([{ 
    'id_fornitore': f'FOR_{i:02d}', 
    'nome': f'Partner Network {i}', 
    'categoria_servizio': random.choice(cat_servizio), 
    'zona': random.choice(zone_geo)} for i in range(1, 51)
]) 

df_operatori = pd.DataFrame([{ 
    'id_operatore': f'OPE_{i:02d}', 
    'zona': random.choice(zone_geo), 
    'tipo_attivita': random.choice(tipo_att) } for i in range(1, 61)
]) 

richieste = []
for i in range(1, 501): 
    stato = random.choice(stati_req) 
    giorni_casuali = random.randint(0, 365) 
    fasce_orarie = [8, 9, 10, 11, 12, 12, 13, 14, 15, 16, 17, 18, 18, 19, 20, 21, 22] 
    ora = random.choice(fasce_orarie) 
    minuto = random.randint(0, 59) 
    dt_richiesta = data_start + timedelta(days=giorni_casuali, hours=ora, minutes=minuto) 
    
    if stato == 'Completata': 
        importo = round(random.uniform(22.50, 189.90), 2) 
        tempo = int(np.random.exponential(scale=28) + 12) 
    else:
        importo = 0.0 
        tempo = np.nan 
        
    richieste.append({ 
        'id_richiesta': f'REQ_{i:04d}', 
        'id_cliente': random.choice(df_clienti['id_cliente'].values), 
        'id_fornitore': random.choice(df_fornitori['id_fornitore'].values), 
        'id_operatore': random.choice(df_operatori['id_operatore'].values), 
        'data_ora': dt_richiesta.strftime('%Y-%m-%d %H:%M:%S'), 
        'importo': importo, 
        'tempo_erogazione_min': tempo, 
        'stato': stato 
    }) 

df_richieste = pd.DataFrame(richieste) 
df_clienti.to_csv('clienti.csv', index=False) 
df_fornitori.to_csv('fornitori.csv', index=False) 
df_operatori.to_csv('operatori.csv', index=False) 
df_richieste.to_csv('richieste.csv', index=False) 
print("[SUCCESS] Dataset CSV sorgenti creati correttamente nella directory locale.")
