import httpx
import pytest
from fastapi import HTTPException
from app.infrastructure import PublicAPI

def test_cache_ttl_and_caller_mutation():
    calls=[]
    def handler(request):
        calls.append(request)
        return httpx.Response(200,json={'items':[1,2]})
    clock=[0]
    api=PublicAPI(httpx.Client(transport=httpx.MockTransport(handler)),clock=lambda:clock[0],ttl=10)
    first,meta=api.get('https://api.open-meteo.com/v1/forecast')
    first['items'].append(3)
    second,other=api.get('https://api.open-meteo.com/v1/forecast')
    assert second=={'items':[1,2]} and other['cached'] and not meta['cached']
    assert len(calls)==1
    clock[0]=11
    api.get('https://api.open-meteo.com/v1/forecast')
    assert len(calls)==2
    api.close()

@pytest.mark.parametrize('status,expected',[(404,404),(429,503),(500,502),(301,502)])
def test_provider_error_contract(status,expected):
    api=PublicAPI(httpx.Client(transport=httpx.MockTransport(lambda r:httpx.Response(status,json={}))))
    with pytest.raises(HTTPException) as failure: api.get('https://api.worldbank.org/v2/test')
    assert failure.value.status_code==expected
    api.close()

def test_timeout_bounded_retry():
    calls=[]
    def handler(request):
        calls.append(request)
        raise httpx.ReadTimeout('timeout',request=request)
    api=PublicAPI(httpx.Client(transport=httpx.MockTransport(handler)))
    with pytest.raises(HTTPException) as failure: api.get('https://brasilapi.com.br/api/test')
    assert failure.value.status_code==503 and len(calls)==2
    api.close()

def test_no_arbitrary_url_or_http():
    api=PublicAPI()
    for url in ['http://api.worldbank.org/v2/test','https://localhost/','https://api.worldbank.org.attacker.test/']:
        with pytest.raises(ValueError): api.get(url)
    api.close()

def test_invalid_json_rejected():
    api=PublicAPI(httpx.Client(transport=httpx.MockTransport(lambda r:httpx.Response(200,text='not-json'))))
    with pytest.raises(HTTPException) as failure: api.get('https://api.worldbank.org/v2/test')
    assert failure.value.status_code==502
    api.close()
