import os
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from .infrastructure import PublicAPI, Snapshots, tenant
from .service import Command, execute

def create_app(path=None, provider=None):
    own_provider=provider is None
    api=provider or PublicAPI()
    store=Snapshots(path or os.getenv('DATABASE_PATH','macro-lens.db'))

    @asynccontextmanager
    async def lifespan(app):
        yield
        if own_provider: api.close()

    app=FastAPI(title='Macro Lens',version='1.0.0',lifespan=lifespan)

    frontend=Path(__file__).with_name('frontend')
    if (frontend/'assets').exists(): app.mount('/assets',StaticFiles(directory=frontend/'assets'),name='assets')

    @app.get('/',response_class=HTMLResponse)
    def dashboard():
        page=frontend/'index.html' if (frontend/'index.html').exists() else Path(__file__).with_name('dashboard.html')
        return page.read_text(encoding='utf-8')

    @app.get('/health')
    def health(): return {'status':'ok'}

    @app.post('/api/analyze')
    def analyze(command: Command, identity: str=Depends(tenant)):
        result=execute(command,api)
        return store.save(identity,'analysis',result)

    @app.get('/api/history')
    def history(identity: str=Depends(tenant)): return store.history(identity)

    @app.delete('/api/history/{ident}')
    def delete(ident: str,identity: str=Depends(tenant)):
        if not store.delete(identity,ident): raise HTTPException(404,'Snapshot not found')
        return {'deleted':True}

    return app

app=create_app()
