"""Least-squares descriptive trend with transparent missing-data accounting."""
from math import isfinite
from statistics import mean

def analyze(rows):
    valid=[]
    missing=[]
    for row in rows:
        year=int(row['date'])
        value=row['value']
        if value is None: missing.append(year)
        elif isinstance(value,(int,float)) and not isinstance(value,bool) and isfinite(value): valid.append((year,float(value)))
        else: raise ValueError('Non-numeric indicator value')
    if len({year for year,_ in valid})!=len(valid): raise ValueError('Duplicate years')
    valid.sort()
    series=[{'year':year,'value':value} for year,value in valid]
    if len(valid)<3: return {'status':'insufficient_data','series':series,'missing_years':sorted(missing),'model':'ols-descriptive-v1'}
    xs,ys=zip(*valid)
    xmean,ymean=mean(xs),mean(ys)
    slope=sum((x-xmean)*(y-ymean) for x,y in valid)/sum((x-xmean)**2 for x in xs)
    fitted=[ymean+slope*(x-xmean) for x in xs]
    residual=sum((y-f)**2 for y,f in zip(ys,fitted))
    total=sum((y-ymean)**2 for y in ys)
    r2=1-residual/total if total else 1.0
    # Missing years are not interpolated; regression uses actual year coordinates.
    return {'status':'ok','series':series,'missing_years':sorted(missing),'slope_per_year':slope,
            'r_squared':r2,'latest':series[-1],'trend':'up' if slope>0 else 'down' if slope<0 else 'flat',
            'fitted':[{'year':x,'value':y} for x,y in zip(xs,fitted)],'model':'ols-descriptive-v1'}
