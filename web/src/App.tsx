import {useState} from 'react';
import {config} from './config';
import './style.css';

type Scalar=string|number|null|undefined;
type Provenance={mode:string;source_url:string|null;retrieved_at:string;sha256:string;cached:boolean};
type Day={date:string;temperature_c:number|null;rain_mm:number|null;wind_kmh:number|null;status:string};
type Series={country:string;status:string;series:{year:number;value:number}[];latest?:{year:number;value:number};trend?:string;slope_per_year?:number;r_squared?:number;missing_years:number[];provenance:Provenance};
type Result={snapshot_id?:string;site?:string;overall?:string;flagged_days?:number;days?:Day[];provenance?:Provenance;
 company?:Record<string,Scalar>;assessment?:{status:string;issues:{code:string;detail:string}[]};countries?:Series[];window?:number[];label?:string;unit?:string};
type Snapshot={id:string;created_at:string;data:Result};
const fmt=(x:Scalar,d=1)=>x===null||x===undefined?'—':typeof x==='number'?x.toLocaleString('pt-BR',{maximumFractionDigits:d}):x;

function Chart({series}:{series:{name:string;values:(number|null)[]}[]}){
 const vals=series.flatMap(s=>s.values).filter((v):v is number=>v!==null&&Number.isFinite(v));
 if(!vals.length)return <p>Sem valores para exibir.</p>;
 let min=Math.min(...vals),max=Math.max(...vals);if(min===max){min-=1;max+=1}
 const colors=['var(--accent)','#64aaff','#f18eae'];
 return <svg viewBox="0 0 700 220" role="img" aria-label="Séries observadas; lacunas não são interpoladas">
 {[0,1,2,3].map(i=><g key={i}><line x1="50" x2="680" y1={20+i*50} y2={20+i*50} stroke="#2a3742"/><text x="0" y={24+i*50} fill="#91a0b3" fontSize="10">{fmt(max-(max-min)*i/3)}</text></g>)}
 {series.map((s,j)=>{const groups:string[][]=[];let group:string[]=[];s.values.forEach((v,i)=>{if(v===null){if(group.length)groups.push(group);group=[]}else group.push(`${50+630*i/Math.max(s.values.length-1,1)},${20+150*(max-v)/(max-min)}`)});if(group.length)groups.push(group);return <g key={s.name}>{groups.map((points,i)=><g key={i}><polyline points={points.join(' ')} fill="none" stroke={colors[j%3]} strokeWidth="3"/>{points.map((p,k)=>{const [x,y]=p.split(',');return <circle key={k} cx={x} cy={y} r="3" fill={colors[j%3]}/>})}</g>)}<text x={50+j*180} y="207" fill={colors[j%3]} fontSize="11">{s.name}</text></g>})}
 </svg>
}
function Table({headers,rows}:{headers:string[];rows:Scalar[][]}){return <div className="scroll"><table><thead><tr>{headers.map(h=><th key={h}>{h}</th>)}</tr></thead><tbody>{rows.map((row,i)=><tr key={i}>{row.map((v,j)=><td key={j}>{fmt(v)}</td>)}</tr>)}</tbody></table></div>}

export default function App(){
 const [fields,setFields]=useState<Record<string,string>>({...config.defaults,mode:'demo'});
 const [key,setKey]=useState('local-alpha'),[result,setResult]=useState<Result|null>(null),[history,setHistory]=useState<Snapshot[]>([]);
 const [error,setError]=useState(''),[busy,setBusy]=useState(false);
 const field=(name:string,value:string)=>setFields(old=>({...old,[name]:value}));
 async function request<T,>(path:string,method='GET',body?:unknown):Promise<T>{
  const response=await fetch(path,{method,headers:{'Content-Type':'application/json','X-API-Key':key},...(body===undefined?{}:{body:JSON.stringify(body)})});
  const data=await response.json();if(!response.ok)throw Error(typeof data.detail==='string'?data.detail:JSON.stringify(data.detail));return data as T;
 }
 async function refresh(){setHistory(await request<Snapshot[]>('/api/history'))}
 async function run(event:React.FormEvent){event.preventDefault();setError('');setBusy(true);try{
  const payload:Record<string,unknown>={mode:fields.mode};for(const f of config.fields){payload[f.name]=f.type==='number'?Number(fields[f.name]):f.name==='countries'?fields[f.name].split(','):fields[f.name]}
  setResult(await request<Result>('/api/analyze','POST',payload));await refresh();
 }catch(e){setError(e instanceof Error?e.message:String(e))}finally{setBusy(false)}}
 let cards:[string,Scalar][]=[['ESTADO','Pronto'],['FONTE','Demo'],['HISTÓRICO','Local']];
 let title='Resultado da análise',state='Aguardando',rows:Scalar[][]=[],headers:string[]=[],series:{name:string;values:(number|null)[]}[]=[],sources:Provenance[]=[];
 if(result?.days){cards=[['RISCO OPERACIONAL',result.overall?.toUpperCase()],['DIAS SINALIZADOS',result.flagged_days],['JANELA',result.days.length+' dias']];title=result.site+' · temperatura máxima (°C)';state=result.overall||'';headers=['Data UTC','Temp. °C','Chuva mm','Vento km/h','Estado'];rows=result.days.map(x=>[x.date,x.temperature_c,x.rain_mm,x.wind_kmh,x.status]);series=[{name:'Temperatura máxima °C',values:result.days.map(x=>x.temperature_c)}]}
 if(result?.company&&result.assessment){const c=result.company,a=result.assessment;cards=[['SITUAÇÃO',c.descricao_situacao_cadastral],['CONSISTÊNCIA',a.status.toUpperCase()],['PONTOS DE REVISÃO',a.issues.length]];title=String(c.razao_social||'Cadastro');state=a.status;headers=['Campo','Evidência'];rows=[['CNPJ',c.cnpj],['Razão social',c.razao_social],['Município',c.municipio],['UF',c.uf],['Porte',c.porte],['Início da atividade',c.data_inicio_atividade],['CNAE',c.cnae_fiscal],...a.issues.map(x=>[x.code,x.detail])]}
 if(result?.countries&&result.window){const years=Array.from({length:result.window[1]-result.window[0]+1},(_,i)=>result.window![0]+i);cards=result.countries.map(c=>[c.country+' · ÚLTIMO VALOR',c.latest?fmt(c.latest.value):'Sem série']);title=result.label+' · '+result.unit;state=result.window.join(' — ');headers=['País','Tendência','Inclinação/ano','R²','Anos ausentes'];rows=result.countries.map(c=>[c.country,c.trend||c.status,c.slope_per_year,fmt(c.r_squared,3),c.missing_years.join(', ')||'Nenhum']);series=result.countries.map(c=>({name:c.country,values:years.map(y=>c.series.find(p=>p.year===y)?.value??null)}));sources=result.countries.map(c=>c.provenance)}
 if(result?.provenance)sources=[result.provenance];
 return <><aside><div className="brand"><span className="mark">{config.symbol}</span>{config.title}</div><nav><a className="active" href="#">◈ &nbsp; Visão geral</a><a href="#history">◷ &nbsp; Histórico</a><a href="/docs">⌘ &nbsp; API Explorer</a><a href={config.source} target="_blank" rel="noopener">↗ &nbsp; Fonte de dados</a></nav><div className="aside-bottom">DATA INTELLIGENCE<br/>React · TypeScript · Python<br/>v1.0 / Engineering edition</div></aside>
 <main><header><span>Workspace / <b>{config.title}</b></span><span className="pill" id="mode-badge">{sources.length&&sources.every(p=>p.mode==='live')?'API PÚBLICA':'DEMONSTRAÇÃO SINTÉTICA'}</span></header><div className="hero"><div><span className="eyebrow">{config.subtitle}</span><h1>{config.headline}</h1><p>{config.description}</p></div><span className="pill">{config.provider}</span></div>{error&&<div role="alert" className="error">{error}</div>}
 <div className="grid"><form className="panel controls" onSubmit={run}><h2>Configurar análise</h2><label htmlFor="mode">Origem dos dados</label><select id="mode" value={fields.mode} onChange={e=>field('mode',e.target.value)}><option value="demo">Demonstração sintética</option><option value="live">Consultar API pública</option></select>
 {config.fields.map(f=><div key={f.name}><label htmlFor={f.name}>{f.label}</label>{f.options?<select id={f.name} value={fields[f.name]} onChange={e=>field(f.name,e.target.value)}>{f.options.map(o=><option key={o.value} value={o.value}>{o.label}</option>)}</select>:<input id={f.name} type={f.type||'text'} step={f.type==='number'?'any':undefined} value={fields[f.name]} onChange={e=>field(f.name,e.target.value)} required/>}</div>)}
 <label htmlFor="key">Chave do workspace</label><input id="key" type="password" value={key} onChange={e=>{setKey(e.target.value);setResult(null);setHistory([])}} autoComplete="off"/><button id="run" className="primary" disabled={busy}>{busy?'Consultando…':'Executar análise ↗'}</button><p className="caption">Demonstração usa dados sintéticos. O modo público consulta o provedor sem substituir falhas por exemplos.</p><p className="note">{config.notice}</p></form>
 <div className="workspace"><div className="metrics">{cards.map(([label,value])=><div className="metric" key={label}><small>{label}</small><strong>{fmt(value)}</strong></div>)}</div><section className="panel" aria-live="polite"><div className="section-head"><h2>{title}</h2><span className="status">{state}</span></div><div className="chartbox">{series.length?<Chart series={series}/>:result?.company?<div style={{padding:24}}><h2>{fmt(result.company.nome_fantasia||result.company.razao_social)}</h2><p>{fmt(result.company.municipio)} / {fmt(result.company.uf)}</p><p>{fmt(result.company.cnae_fiscal_descricao)}</p></div>:'Execute uma análise para explorar os dados.'}</div>{rows.length>0&&<Table headers={headers} rows={rows}/>}
 {sources.map((p,i)=><div className="source" key={i}>{p.mode==='demo'?'SYNTHETIC DEMO':<a href={p.source_url||'#'} target="_blank" rel="noopener">{p.source_url}</a>}<br/>{p.retrieved_at} · {p.cached?'cache':'new'}<br/>SHA-256 {p.sha256}</div>)}<details><summary>Inspecionar resposta estruturada</summary><pre>{result?JSON.stringify(result,null,2):'Aguardando análise.'}</pre></details></section></div></div>
 <section className="panel history" id="history"><div className="section-head"><h2>Histórico do workspace</h2><button className="quiet" onClick={()=>refresh().catch(e=>setError(String(e)))}>Atualizar</button></div><p className="caption">Últimas 30 análises. Excluir remove somente o snapshot local.</p>{history.map(item=><div className="history-item" key={item.id}><span>{new Date(item.created_at).toLocaleString('pt-BR')} · {item.id.slice(0,8)}</span><button onClick={()=>setResult(item.data)}>Abrir</button><button className="quiet" onClick={()=>request('/api/history/'+item.id,'DELETE').then(refresh).catch(e=>setError(String(e)))}>Excluir</button></div>)}</section></main></>
}
