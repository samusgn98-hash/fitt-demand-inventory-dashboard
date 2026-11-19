import numpy as np
import pytest
from core import *

def test_reproducibility_and_shape():
    a=generate(); b=generate()
    assert a.equals(b) and len(a)==192
    assert (a.domanda>=0).all()
    assert not a.duplicated(['articolo','periodo']).any()

def test_constant_forecasts():
    for m in METHODS:
        assert np.allclose(forecast(np.repeat(80.,36),m,4),80.,atol=.01)

def test_invalid_series():
    with pytest.raises(ValueError): forecast([1,np.nan],'Holt')
    with pytest.raises(ValueError): forecast([1,2],'Holt-Winters')

def test_temporal_isolation():
    y=generate().query("articolo=='PW03'").domanda.to_numpy()
    a=fit_article(y); y2=y.copy(); y2[36:]+=100
    b=fit_article(y2)
    assert a['winner']==b['winner']
    assert a['safety']==b['safety']
    assert np.allclose(a['scores'].MAE_validazione,b['scores'].MAE_validazione)
    assert a['test'][0]==b['test'][0]

def test_inventory_balance():
    for s in [Scenario(),Scenario(noise=2,season=2,lead=3,capacity=.8)]:
        _,results=experiment(s)
        for r in results.values():
            z=r['simulation']
            assert np.allclose(z.giacenza_iniziale+z.arrivi-z.evasione_arretrati-z.evasione_immediata,z.giacenza_finale)
            assert (z[['giacenza_finale','arretrati','ordine','pipeline']]>=0).all().all()
            assert (z.ordine<=r['cap']).all()
            previous=0.
            for row in z.itertuples():
                assert np.isclose(previous+row.domanda-row.evasione_arretrati-row.evasione_immediata,row.arretrati)
                previous=row.arretrati
            assert 0<=r['fill']<=1

def test_streamlit_controls():
    from streamlit.testing.v1 import AppTest
    at=AppTest.from_file('app.py',default_timeout=120).run()
    assert not at.exception
    at.slider[0].set_value(1.5)
    at.slider[3].set_value(2)
    at.selectbox[0].select('PW03')
    at.run(timeout=120)
    assert not at.exception
    assert 'Metodo selezionato' in at.subheader[0].value
