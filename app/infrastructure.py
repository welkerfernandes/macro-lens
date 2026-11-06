"""Explicit identities, bounded HTTP, tenant-scoped snapshots and provenance."""
import hashlib
import hmac
import json
import logging
import os
import sqlite3
import threading
import time
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from fastapi import Header, HTTPException
import httpx

logger = logging.getLogger(__name__)

def tenant(x_api_key: str = Header(default='')):
    keys = json.loads(os.getenv('API_KEYS', '{"local-alpha":"alpha","local-beta":"beta"}'))
    for key, identity in keys.items():
        if hmac.compare_digest(key, x_api_key): return identity
    raise HTTPException(401, 'Invalid API key')

def now(): return datetime.now(timezone.utc).isoformat()

def digest(data):
    return hashlib.sha256(json.dumps(data,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()

@contextmanager
def database(path):
    db = sqlite3.connect(path, timeout=10)
    db.row_factory = sqlite3.Row
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

class Snapshots:
    def __init__(self,path):
        self.path=path
        with database(path) as db:
            db.execute('CREATE TABLE IF NOT EXISTS snapshots(tenant TEXT,id TEXT,created_at TEXT,kind TEXT,payload TEXT,PRIMARY KEY(tenant,id))')
            db.execute('CREATE INDEX IF NOT EXISTS snapshots_scope ON snapshots(tenant,created_at)')

    def save(self,identity,kind,payload):
        ident=str(uuid.uuid4())
        with database(self.path) as db:
            db.execute('INSERT INTO snapshots VALUES(?,?,?,?,?)',(identity,ident,now(),kind,json.dumps(payload,allow_nan=False)))
        return {'snapshot_id':ident,**payload}

    def history(self,identity):
        with database(self.path) as db:
            return [{'id':r['id'],'created_at':r['created_at'],'kind':r['kind'],'data':json.loads(r['payload'])}
                    for r in db.execute('SELECT * FROM snapshots WHERE tenant=? ORDER BY created_at DESC LIMIT 30',(identity,))]

    def delete(self,identity,ident):
        with database(self.path) as db:
            return db.execute('DELETE FROM snapshots WHERE tenant=? AND id=?',(identity,ident)).rowcount > 0

class PublicAPI:
    """GET-only adapter. Fixed provider hosts; no user-controlled URLs or redirects."""
    HOSTS={'api.open-meteo.com','brasilapi.com.br','api.worldbank.org'}

    def __init__(self,client=None,clock=time.monotonic,ttl=300):
        self.client=client or httpx.Client(timeout=httpx.Timeout(12,connect=5),follow_redirects=False,
                                          headers={'User-Agent':'PublicDataEngineering/1.0'},trust_env=False)
        self.clock=clock
        self.ttl=ttl
        self.cache={}
        self.lock=threading.Lock()

    def close(self): self.client.close()

    def get(self,url,params=None):
        request=httpx.Request('GET',url,params=params)
        if request.url.scheme!='https' or request.url.host not in self.HOSTS:
            raise ValueError('Provider URL not allowed')
        key=str(request.url)
        with self.lock:
            cached=self.cache.get(key)
            if cached and self.clock()-cached[0]<self.ttl:
                return json.loads(cached[1]),{**cached[2],'cached':True}
        for attempt in range(2):
            try:
                response=self.client.get(url,params=params)
                if response.status_code in (404,400): raise HTTPException(404,'Provider has no data for this request')
                if response.status_code==429: raise HTTPException(503,'Provider rate limit reached; retry later')
                if response.status_code>=500 and attempt==0: continue
                response.raise_for_status()
                data=response.json()
                encoded=json.dumps(data,allow_nan=False)
                metadata={'source_url':key,'retrieved_at':now(),'sha256':digest(data),'cached':False,'mode':'live'}
                with self.lock:
                    if len(self.cache)>=128: self.cache.pop(next(iter(self.cache)))
                    self.cache[key]=(self.clock(),encoded,metadata)
                return data,metadata
            except HTTPException: raise
            except (httpx.TimeoutException,httpx.NetworkError):
                if attempt==0: continue
                raise HTTPException(503,'Public data provider unavailable')
            except (httpx.HTTPError,ValueError,TypeError):
                logger.warning('Provider response rejected for host %s',request.url.host)
                raise HTTPException(502,'Invalid response from public data provider')

def demo_metadata(data):
    return {'mode':'demo','source_url':None,'retrieved_at':now(),'sha256':digest(data),'cached':False,
            'notice':'Synthetic fixture; not a live provider response'}
