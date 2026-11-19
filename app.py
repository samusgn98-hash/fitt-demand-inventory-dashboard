"""Avvio: python -m streamlit run app.py"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from core import Scenario, NAMES, experiment

st.set_page_config(page_title='Domanda e scorte FITT',layout='wide')
st.title('Previsione della domanda e pianificazione delle scorte')
st.caption('Caso didattico FITT • prodotti reali, domanda e rifornimenti simulati')
with st.sidebar:
    st.header('Scenario alternativo')
    noise=st.slider('Variabilità (moltiplicatore)',0.0,3.0,1.0,.1)
    trend=st.slider('Tendenza (moltiplicatore)',0.0,2.0,1.0,.1)
    season=st.slider('Stagionalità (moltiplicatore)',0.0,2.0,1.0,.1)
    lead=st.slider('Tempo di reintegro (mesi)',1,3,1)
    service=st.select_slider('Quantile di protezione',options=[.80,.90,.95,.99],value=.95)
    capacity=st.slider('Capacità / domanda media di sviluppo',.8,2.,1.25,.05)
    st.caption('La modifica della domanda rigenera tutti i 48 mesi mantenendo le stesse perturbazioni standardizzate.')
@st.cache_data(show_spinner=False)
def run(s):
    return experiment(s)
with st.spinner('Calcolo e confronto dei quattro articoli...'):
    base,br=run(Scenario())
    alt,ar=run(Scenario(noise,trend,season,lead,service,capacity))
code=st.selectbox('Articolo',list(NAMES),format_func=lambda c:f'{c} — {NAMES[c]}')
r=ar[code]; b=br[code]
st.subheader(f"Metodo selezionato: {r['winner']}")
st.caption('Scelta sul MAE di M25–M36. M37–M48: verifica indipendente con aggiornamento mensile; M49–M60: previsione finale.')
fig=go.Figure()
for label,data,res in [('Base',base,b),('Alternativo',alt,r)]:
    y=data[data.articolo==code]
    fig.add_scatter(x=y.periodo,y=y.domanda,name=f'Domanda {label}')
    fig.add_scatter(x=list(range(37,49)),y=res['test'],name=f'Verifica {label}',line=dict(dash='dot'))
    fig.add_scatter(x=list(range(49,61)),y=res['future'],name=f'Previsione {label}',line=dict(dash='dash'))
fig.update_layout(xaxis_title='Mese convenzionale',yaxis_title='Confezioni')
st.plotly_chart(fig,use_container_width=True)
st.subheader('Accuratezza dei metodi')
st.dataframe(r['scores'],hide_index=True)
st.plotly_chart(px.bar(r['scores'],x='metodo',y=['MAE_test','RMSE_test'],barmode='group',labels={'value':'Confezioni'}),use_container_width=True)
st.subheader('Componenti di pianificazione al termine di M48')
comp=pd.DataFrame([{'scenario':label,'componente':k,'confezioni':v}
    for label,res in [('Base',b),('Alternativo',r)] for k,v in res['composition'].items()])
st.plotly_chart(px.bar(comp,x='componente',y='confezioni',color='scenario',barmode='group'),use_container_width=True)
st.info('Le componenti NON si sommano: ciclica = media teorica nel ciclo; sicurezza e anticipo = riserve obiettivo; pipeline = domanda attesa durante il tempo di reintegro. Gli ordini realmente in transito sono nel registro sottostante.')
st.caption(f"Scorta di sicurezza calibrata su {r['n_errors']} errori cumulati. Quantile indicativo, non garanzia di servizio. Capacità ipotetica: {r['cap']:.0f} confezioni/mese.")
summary=pd.DataFrame([{'Scenario':label,'Evasione immediata (%)':100*v['fill'],
    'Giacenza finale media':v['average_stock'],'Arretrati a M48':v['simulation'].arretrati.iloc[-1]}
    for label,v in [('Base',b),('Alternativo',r)]])
st.dataframe(summary,hide_index=True)
st.subheader('Registro del magazzino M37–M48')
st.dataframe(r['simulation'],hide_index=True)
st.plotly_chart(px.line(r['simulation'],x='periodo',y=['giacenza_finale','arretrati','pipeline']),use_container_width=True)
st.download_button('Scarica domanda simulata CSV',alt.to_csv(index=False).encode(), 'domanda_simulata.csv','text/csv')
st.download_button('Scarica registro articolo CSV',r['simulation'].to_csv(index=False).encode(),f'{code}_registro.csv','text/csv')
st.caption('Nessuna integrazione con sistemi FITT. Nessuna stima di risparmio economico. Il mese non rappresenta la sequenza giornaliera delle richieste.')

if r['future'].sum()>12*r['cap']:
    st.warning('Fabbisogno previsto annuo superiore alla capacità. La scorta anticipata è un fabbisogno teorico iniziale, non merce già disponibile. La capacità va riesaminata.')
