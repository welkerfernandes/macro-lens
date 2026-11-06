import httpx
import pytest
from fastapi.testclient import TestClient
from app.main import create_app
from app.infrastructure import PublicAPI

@pytest.fixture
def client(tmp_path):
    provider=PublicAPI(client=httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(500))))
    with TestClient(create_app(str(tmp_path/'test.db'),provider)) as client:
        client.headers['X-API-Key']='local-alpha'
        yield client
    provider.close()

def test_auth_and_openapi(client):
    assert client.get('/').status_code==200
    assert client.get('/openapi.json').status_code==200
    assert client.get('/health').json()=={'status':'ok'}
    client.headers['X-API-Key']='invalid'
    assert client.get('/api/history').status_code==401
    assert client.post('/api/analyze',json={'mode':'demo'}).status_code==401

def test_tenant_history_delete(client):
    response=client.post('/api/analyze',json={'mode':'demo'})
    assert response.status_code==200, response.text
    ident=response.json()['snapshot_id']
    assert len(client.get('/api/history').json())==1
    client.headers['X-API-Key']='local-beta'
    assert client.get('/api/history').json()==[]
    assert client.delete('/api/history/'+ident).status_code==404
    client.headers['X-API-Key']='local-alpha'
    assert client.delete('/api/history/'+ident).json()=={'deleted':True}
    assert client.get('/api/history').json()==[]

def test_provider_failure_no_fake_fallback(client):
    result=client.post('/api/analyze',json={'mode':'live'})
    assert result.status_code==502
    assert client.get('/api/history').json()==[]

def test_demo_comparison(client):
    result=client.post('/api/analyze',json={'mode':'demo'}).json()
    assert len(result['countries'])==2
    assert result['countries'][0]['trend']=='up'
    assert result['countries'][0]['provenance']['mode']=='demo'

def test_exact_linear_trend_and_missing():
    from app.domain import analyze
    result=analyze([{'date':'2020','value':10},{'date':'2021','value':None},{'date':'2022','value':14},{'date':'2023','value':16}])
    assert result['slope_per_year']==2 and result['r_squared']==1
    assert result['missing_years']==[2021]

def test_constant_and_insufficient():
    from app.domain import analyze
    assert analyze([{'date':str(y),'value':10} for y in range(2020,2024)])['trend']=='flat'
    assert analyze([{'date':'2020','value':None}])['status']=='insufficient_data'

def test_duplicate_years_and_nonfinite():
    from app.domain import analyze
    with pytest.raises(ValueError): analyze([{'date':'2020','value':1}]*3)
    with pytest.raises(ValueError): analyze([{'date':'2020','value':float('nan')}])

@pytest.mark.parametrize('fields',[{'countries':['BRA','BRA']},{'countries':['XXX']},{'start_year':2024,'end_year':2020},{'start_year':1960,'end_year':2024}])
def test_invalid_requests(client,fields):
    assert client.post('/api/analyze',json={'mode':'demo',**fields}).status_code==422

def test_live_country_identity_and_absent_years(tmp_path):
    def handler(request):
        return httpx.Response(200,json=[{'pages':1},[{'date':str(y),'value':v,'countryiso3code':'BRA',
              'indicator':{'id':'NY.GDP.PCAP.CD'}} for y,v in [(2020,10),(2022,14),(2023,16)]]])
    api=PublicAPI(httpx.Client(transport=httpx.MockTransport(handler)))
    with TestClient(create_app(str(tmp_path/'live.db'),api)) as c:
        response=c.post('/api/analyze',json={'mode':'live','countries':['BRA'],'start_year':2020,'end_year':2023},headers={'X-API-Key':'local-alpha'})
    assert response.status_code==200
    assert response.json()['countries'][0]['missing_years']==[2021]
    assert response.json()['countries'][0]['provenance']['mode']=='live'
    api.close()
