from .native import invoke
from typing import Literal
from fastapi import HTTPException
from pydantic import BaseModel,Field,model_validator
from .domain import analyze
from .infrastructure import demo_metadata

INDICATORS={
 'NY.GDP.PCAP.CD':{'label':'GDP per capita','unit':'current US$'},
 'FP.CPI.TOTL.ZG':{'label':'Consumer price inflation','unit':'annual %'},
 'SL.UEM.TOTL.ZS':{'label':'Unemployment','unit':'% of total labor force, modeled ILO estimate'},
}
class Command(BaseModel):
    mode: Literal['demo','live']='live'
    countries: list[Literal['BRA','USA','PRT','DEU','CHL']]=Field(default=['BRA','PRT'],min_length=1,max_length=3)
    indicator: Literal['NY.GDP.PCAP.CD','FP.CPI.TOTL.ZG','SL.UEM.TOTL.ZS']='NY.GDP.PCAP.CD'
    start_year: int=Field(default=2015,ge=1960,le=2026)
    end_year: int=Field(default=2024,ge=1960,le=2026)

    @model_validator(mode='after')
    def valid_range(self):
        if self.start_year>self.end_year: raise ValueError('Invalid year range')
        if self.end_year-self.start_year>30: raise ValueError('Maximum window is 31 years')
        if len(set(self.countries))!=len(self.countries): raise ValueError('Duplicate countries')
        return self

def execute(command,api):
    reports=[]
    for index,country in enumerate(command.countries):
        if command.mode=='demo':
            # Explicitly synthetic for every indicator; not a saved World Bank series.
            rows=[{'date':str(year),'value':100+index*30+(year-command.start_year)*5+((year%3)-1)*2,
                   'countryiso3code':country,'indicator':{'id':command.indicator}}
                  for year in range(command.start_year,command.end_year+1)]
            data=[{'pages':1},rows]
            metadata=demo_metadata(data)
        else:
            data,metadata=api.get(f'https://api.worldbank.org/v2/country/{country}/indicator/{command.indicator}',
                 {'format':'json','date':f'{command.start_year}:{command.end_year}','per_page':100})
        try:
            if not isinstance(data,list) or len(data)!=2 or not isinstance(data[1],list): raise ValueError('Missing series')
            if int(data[0].get('pages',1))>1: raise ValueError('Incomplete page')
            rows=data[1]
            for row in rows:
                if row.get('countryiso3code')!=country or row.get('indicator',{}).get('id')!=command.indicator: raise ValueError('Mismatched series')
                if not command.start_year<=int(row['date'])<=command.end_year: raise ValueError('Out-of-window year')
            analysis=analyze(rows)
            analysis['engine']='python'
            if analysis['status']=='ok':
                native=invoke(''.join(str(p['year'])+'\t'+str(p['value'])+'\n' for p in analysis['series']))
                if native is not None: analysis.update(native)
            observed={int(r['date']) for r in rows}
            analysis['missing_years']=sorted(set(analysis['missing_years']) | (set(range(command.start_year,command.end_year+1))-observed))
        except (ValueError,KeyError,TypeError,AttributeError): raise HTTPException(502,'Economic provider schema mismatch')
        reports.append({'country':country,**analysis,'provenance':metadata})
    return {'indicator':command.indicator,**INDICATORS[command.indicator],
            'window':[command.start_year,command.end_year],'countries':reports,
            'notice':'Descriptive trends; not forecasts or investment recommendations'}
