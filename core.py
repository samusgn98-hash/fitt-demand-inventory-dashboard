"""Esperimento didattico FITT: nessun dato commerciale reale."""
from dataclasses import dataclass
import warnings
import numpy as np
import pandas as pd
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from statsmodels.tools.sm_exceptions import ConvergenceWarning

NAMES = {'PW01':'FITT Air Hose 10 m 6x11 mm',
         'PW02':'FITT NTS Master Plus 20 m 12,5 mm',
         'PW03':'FITT Kiuma 20 m 13 mm',
         'PW04':'FITT Cristallo Extra 5 m 10x14 mm'}
METHODS = ['Media mobile', 'Esponenziale semplice', 'Holt', 'Holt-Winters']

@dataclass(frozen=True)
class Scenario:
    noise: float = 1.0
    trend: float = 1.0
    season: float = 1.0
    lead: int = 1
    service: float = 0.95
    capacity: float = 1.25


def generate(s=Scenario(), seed=20261110):
    """48 mesi convenzionali. Gli shock futuri non entrano nel previsore."""
    if min(s.noise, s.trend, s.season) < 0:
        raise ValueError('Moltiplicatori non negativi richiesti')
    t = np.arange(48)
    wave = np.cos(2*np.pi*(t-5)/12)
    means = [np.full(48,80.), 120+60*s.season*wave,
             (45+1.5*s.trend*t)*(1+.2*s.season*wave),
             np.full(48,35.)]
    means[3][[7,18,32,43]] += 60
    streams = np.random.SeedSequence(seed).spawn(4)
    rows=[]
    for i, (code, name) in enumerate(NAMES.items()):
        noise=np.random.default_rng(streams[i]).normal(0,[8,12,7,15][i],48)
        y=np.maximum(0,np.rint(means[i]+s.noise*noise)).astype(int)
        for j,v in enumerate(y):
            rows.append((code,name,j+1,j%12+1,int(v)))
    return pd.DataFrame(rows,columns=['articolo','prodotto','periodo','mese','domanda'])


def forecast(y, method, horizon=1, window=3):
    y=np.asarray(y,dtype=float)
    if len(y)<2 or not np.isfinite(y).all() or (y<0).any():
        raise ValueError('Serie non valida')
    if method=='Media mobile':
        pred=np.repeat(y[-window:].mean(),horizon)
    else:
        trend='add' if method in ['Holt','Holt-Winters'] else None
        seasonal='add' if method=='Holt-Winters' else None
        if seasonal and len(y)<24:
            raise ValueError('Holt-Winters richiede almeno 24 mesi')
        with warnings.catch_warnings():
            warnings.simplefilter('ignore',RuntimeWarning)
            model=ExponentialSmoothing(y,trend=trend,seasonal=seasonal,
                seasonal_periods=12 if seasonal else None,
                initialization_method='estimated')
            with warnings.catch_warnings():
                warnings.simplefilter('ignore', ConvergenceWarning)
                fitted=model.fit(optimized=True)
                if not fitted.mle_retvals.get('success', True):
                    fitted=model.fit(optimized=True, method='Powell')
                if not fitted.mle_retvals.get('success', True):
                    raise RuntimeError('Stima non convergente: cambiare scenario')
            pred=fitted.forecast(horizon)
    return np.maximum(0,np.asarray(pred))


def metrics(actual,pred):
    e=np.asarray(actual)-np.asarray(pred)
    return float(np.mean(np.abs(e))),float(np.sqrt(np.mean(e**2)))


def fit_article(y,s=Scenario()):
    """Selezione M25-M36, verifica sequenziale M37-M48; nessuna fuga futura."""
    y=np.asarray(y,dtype=float)
    if len(y)!=48:
        raise ValueError('Sono richiesti 48 mesi')
    scores=[]; configs={}; histories={}
    for method in METHODS:
        best=None
        for window in ([3,6,12] if method=='Media mobile' else [3]):
            p=[forecast(y[:o],method,1,window)[0] for o in range(24,36)]
            mae,rmse=metrics(y[24:36],p)
            candidate=(mae,rmse,window)
            if best is None or candidate<best:
                best=candidate
        configs[method]=best[2]
        p=np.array([forecast(y[:o],method,1,best[2])[0] for o in range(36,48)])
        histories[method]=p
        test_mae,test_rmse=metrics(y[36:],p)
        scores.append([method,best[2],best[0],best[1],test_mae,test_rmse])
    scores=pd.DataFrame(scores,columns=['metodo','finestra','MAE_validazione',
                        'RMSE_validazione','MAE_test','RMSE_test'])
    winner=scores.sort_values(['MAE_validazione','RMSE_validazione']).iloc[0]['metodo']
    w=configs[winner]
    h=s.lead+1
    errors=[]
    for o in range(24,36-h+1):
        errors.append(y[o:o+h].sum()-forecast(y[:o],winner,h,w).sum())
    safety=float(max(0,np.quantile(errors,s.service,method='higher')))
    future=forecast(y,winner,12,w)
    # Capacita mensile ipotetica, ricavata SOLO dai mesi di sviluppo.
    cap=float(max(1,np.ceil(y[:36].mean()*s.capacity)))
    # Anticipo richiesto dai futuri eccessi cumulati oltre la capacita.
    def advance(p):
        return float(max(0,np.max(np.cumsum(p-cap))))
    anticipation=advance(future)
    composition={'Ciclica':float(future[0]/2), 'Sicurezza':safety,
                 'Anticipata':anticipation, 'Pipeline':float(future[:s.lead].sum())}
    # Simulazione mensile: arrivi, domanda, ordine a fine mese.
    # Inizializzazione comune a tutti i metodi, basata su M01-M36.
    initial=int(np.ceil(y[:36].mean()*(s.lead+1)))
    onhand=float(initial); backlog=0.; orders=[]; records=[]
    for t in range(36,48):
        incoming=sum(q for due,q in orders if due==t)
        orders=[(due,q) for due,q in orders if due!=t]
        before=onhand; onhand+=incoming
        old_served=min(onhand,backlog); onhand-=old_served; backlog-=old_served
        immediate=min(onhand,y[t]); onhand-=immediate; backlog+=y[t]-immediate
        pred=forecast(y[:t+1],winner,12,w)
        extra=advance(pred)
        position=onhand+sum(q for _,q in orders)-backlog
        target=float(pred[:h].sum()+safety+extra)
        order=float(min(cap,max(0,np.ceil(target-position))))
        if order>0: orders.append((t+s.lead,order))
        records.append([t+1,y[t],before,incoming,old_served,immediate,onhand,
                        backlog,order,sum(q for _,q in orders)])
    sim=pd.DataFrame(records,columns=['periodo','domanda','giacenza_iniziale',
        'arrivi','evasione_arretrati','evasione_immediata','giacenza_finale',
        'arretrati','ordine','pipeline'])
    return dict(scores=scores,winner=winner,window=w,future=future,
        test=histories[winner],safety=safety,n_errors=len(errors),cap=cap,
        composition=composition,simulation=sim,
        fill=float(sim.evasione_immediata.sum()/sim.domanda.sum()) if sim.domanda.sum() else 1.,
        average_stock=float(sim.giacenza_finale.mean()))


def experiment(s=Scenario()):
    data=generate(s)
    results={code:fit_article(data.loc[data.articolo==code,'domanda'].to_numpy(),s)
             for code in NAMES}
    return data,results
