from pathlib import Path
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd
from core import *
OUT=Path(__file__).parent/'output'; OUT.mkdir(exist_ok=True)
rows=[]; payload={}
for label,s in [('Base',Scenario()),('Alternativo',Scenario(noise=1.5,trend=1.2,season=1.2,lead=2))]:
    data,results=experiment(s)
    data.to_csv(OUT/f'domanda_{label}.csv',index=False)
    payload[label]={}
    for code,r in results.items():
        r['scores'].to_csv(OUT/f'{label}_{code}_errori.csv',index=False)
        r['simulation'].to_csv(OUT/f'{label}_{code}_magazzino.csv',index=False)
        row=r['scores'].set_index('metodo').loc[r['winner']]
        rec={'articolo':code,'scenario':label,'metodo':r['winner'],
             'MAE':float(row.MAE_test),'RMSE':float(row.RMSE_test),
             'evasione':r['fill'],'giacenza':r['average_stock'],
             'arretrati':float(r['simulation'].arretrati.iloc[-1]),
             'componenti':r['composition'],'n_errori':r['n_errors']}
        rows.append({k:v for k,v in rec.items() if k!='componenti'})
        payload[label][code]=rec
    if label=='Base':
        fig,axs=plt.subplots(2,2,figsize=(10,6))
        for ax,(code,r) in zip(axs.flat,results.items()):
            y=data[data.articolo==code]
            ax.plot(y.periodo,y.domanda,label='Domanda simulata',color='#315571')
            ax.plot(range(37,49),r['test'],label='Verifica a un mese',color='#d58a28')
            ax.plot(range(49,61),r['future'],'--',label='Previsione',color='#48806a')
            ax.axvline(36.5,color='grey',lw=.6)
            ax.set_title(f"{code} • {r['winner']}",fontsize=10)
            ax.set_xlabel('Mese'); ax.set_ylabel('Confezioni'); ax.grid(alpha=.2)
        handles,labels=axs.flat[0].get_legend_handles_labels()
        fig.legend(handles,labels,loc='lower center',ncol=3)
        fig.tight_layout(rect=(0,.06,1,1));fig.savefig(OUT/'domanda.png',dpi=180);plt.close(fig)
(OUT/'risultati.json').write_text(json.dumps(payload,indent=2),encoding='utf8')
pd.DataFrame(rows).to_csv(OUT/'riepilogo.csv',index=False)
print(pd.DataFrame(rows).to_string(index=False))
