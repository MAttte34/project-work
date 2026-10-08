import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px

# Configurazione della pagina di Streamlit (Layout largo per visualizzazione a griglia)
st.set_page_config(page_title="BI Dashboard - Startup On-Demand", layout="wide")

# Titolo principale dell'applicazione
st.title("📊 Controllo Direzionale - Startup Servizi On-Demand")
st.markdown("Analisi delle prestazioni logistiche, dei ricavi operativi e della fidelizzazione dei clienti.")

# --- FUNZIONE DI RECUPERO DATI ---
def fetch_analytics_data():
    """
    Stabilisce una connessione con il Data Warehouse SQLite ed effettua una query 
    con JOIN per ricostruire il dataset informativo denormalizzato.
    """
    conn = sqlite3.connect('startup_dw.db')
    sql_query = """
    SELECT 
        f.id_richiesta, 
        f.importo, 
        f.tempo_erogazione_min, 
        f.stato, 
        c.zona AS zona_cliente, 
        c.id_cliente, 
        forn.nome AS nome_fornitore, 
        forn.categoria_servizio, 
        t.data, 
        t.mese, 
        t.giorno_settimana, 
        t.ora
    FROM Fatto_Richieste f
    JOIN Dim_Cliente c ON f.id_cliente = c.id_cliente
    JOIN Dim_Fornitore forn ON f.id_fornitore = forn.id_fornitore
    JOIN Dim_Tempo t ON f.id_tempo = t.id_tempo
    """
    df = pd.read_sql_query(sql_query, conn)
    conn.close()
    return df

# Caricamento del dataset di base
try:
    df_base = fetch_analytics_data()
except Exception as e:
    st.error(f"Errore nel caricamento del Data Warehouse: {e}")
    st.info("Assicurati di aver prima eseguito 'generator.py' e 'etl_dw.py' per creare il database.")
    st.stop()

# --- FILTRI NELLA BARRA LATERALE (SIDEBAR) ---
st.sidebar.header("Filtri di Analisi")

# Filtro Area Geografica Cliente
aree_selezionate = st.sidebar.multiselect(
    "Area Geografica Cliente", 
    options=list(df_base['zona_cliente'].unique()),
    default=list(df_base['zona_cliente'].unique())
)

# Filtro Categoria di Servizio
cat_selezionate = st.sidebar.multiselect(
    "Categoria Servizio", 
    options=list(df_base['categoria_servizio'].unique()),
    default=list(df_base['categoria_servizio'].unique())
)

# Applicazione reattiva dei filtri al dataframe di base
df_filtered = df_base[
    (df_base['zona_cliente'].isin(aree_selezionate)) & 
    (df_base['categoria_servizio'].isin(cat_selezionate))
]

# --- CALCOLO METRICHE PRINCIPALI (KPI) ---
# 1. Volume Richieste Totali
vol_richieste = df_filtered.shape[0]

# 2. Incassi Complessivi
val_incassi = df_filtered['importo'].sum()

# 3. Tempo Medio di Erogazione (calcolato solo per le richieste completate con successo)
df_completate = df_filtered[df_filtered['stato'] == 'Completata']
avg_tempo = df_completate['tempo_erogazione_min'].mean() if not df_completate.empty else 0

# 4. Customer Retention Rate (CRR)
# Calcoliamo la frequenza degli acquisti per ogni cliente unico nel campione filtrato
freq_acquisti = df_filtered['id_cliente'].value_counts()
utenti_ricorrenti = (freq_acquisti > 1).sum()
utenti_totali = df_filtered['id_cliente'].nunique()
crr_percentage = (utenti_ricorrenti / utenti_totali * 100) if utenti_totali > 0 else 0

# --- VISUALIZZAZIONE KPI IN COLONNE ---
col1, col2, col3, col4 = st.columns(4)
col1.metric("Richieste Totali", f"{vol_richieste}")
col2.metric("Incassi Complessivi", f"€ {val_incassi:,.2f}")
col3.metric("Tempo Medio Erogazione", f"{avg_tempo:.1f} min")
col4.metric("Retention Rate Clienti", f"{crr_percentage:.1f}%")

st.markdown("---")

# --- PRIMA RIGA DI GRAFICI ---
g_row1_c1, g_row1_c2 = st.columns(2)

with g_row1_c1:
    st.subheader("📈 Andamento Mensile delle Richieste")
    # Raggruppamento per mese e conteggio del volume di ordini
    df_trend = df_filtered.groupby('mese').size().reset_index(name='Conteggio')
    fig_line = px.line(
        df_trend, 
        x='mese', 
        y='Conteggio', 
        markers=True,
        labels={'mese': 'Mese dell\'Anno (2025)', 'Conteggio': 'Numero di Richieste'},
        template="plotly_white"
    )
    st.plotly_chart(fig_line, use_container_width=True)

with g_row1_c2:
    st.subheader("🏆 Top 5 Fornitori per Volume d'Affari")
    # Raggruppamento fornitori per incassi complessivi sulle sole transazioni completate
    df_top_forn = df_completate.groupby('nome_fornitore')['importo'].sum().reset_index()
    df_top_forn = df_top_forn.sort_values(by='importo', ascending=True).tail(5) # Ordine crescente per barre orizzontali
    fig_bar = px.bar(
        df_top_forn, 
        x='importo', 
        y='nome_fornitore', 
        orientation='h', 
        color='importo',
        labels={'importo': 'Fatturato (€)', 'nome_fornitore': 'Partner commerciale'},
        color_continuous_scale=px.colors.sequential.Viridis,
        template="plotly_white"
    )
    st.plotly_chart(fig_bar, use_container_width=True)

# --- SECONDA RIGA DI GRAFICI ---
g_row2_c1, g_row2_c2 = st.columns(2)

with g_row2_c1:
    st.subheader("🗺️ Quote Richieste per Area Geografica")
    # Distribuzione geografica delle richieste inoltrate
    df_zone = df_filtered.groupby('zona_cliente').size().reset_index(name='Volumi')
    fig_pie_zone = px.pie(
        df_zone, 
        values='Volumi', 
        names='zona_cliente', 
        hole=0.4,
        color_discrete_sequence=px.colors.qualitative.Pastel
    )
    st.plotly_chart(fig_pie_zone, use_container_width=True)

with g_row2_c2:
    st.subheader("🛠️ Distribuzione per Categoria di Servizio")
    # Suddivisione delle richieste per macro-categorie di attività
    df_cats = df_filtered.groupby('categoria_servizio').size().reset_index(name='Volumi')
    fig_pie_cats = px.pie(
        df_cats, 
        values='Volumi', 
        names='categoria_servizio', 
        hole=0.4,
        color_discrete_sequence=px.colors.qualitative.Safe
    )
    st.plotly_chart(fig_pie_cats, use_container_width=True)