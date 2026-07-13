const D = window.DASHBOARD_DATA;
const COLORS = {navy:'#102a43',blue:'#2f6fed',cyan:'#14b8a6',orange:'#f59e0b',red:'#dc4c64',green:'#168f5b',muted:'#94a3b8',light:'#dbeafe'};
const STAGES = D.stage_order;
const LABELS = D.stage_labels;
const plotCfg = {responsive:true, displaylogo:false, modeBarButtonsToRemove:['lasso2d','select2d','toggleSpikelines']};
const baseLayout = {paper_bgcolor:'rgba(0,0,0,0)',plot_bgcolor:'rgba(0,0,0,0)',font:{family:'Inter, system-ui, sans-serif',color:'#334155',size:11},margin:{l:48,r:18,t:25,b:42},hoverlabel:{bgcolor:'#102a43',font:{color:'#fff'}}};
let activeView = 'command';

function fmt(n,d=0){ if(n===null||n===undefined||Number.isNaN(Number(n))) return '—'; return Number(n).toLocaleString(undefined,{minimumFractionDigits:d,maximumFractionDigits:d}); }
function pct(n,d=1){ return n===null||n===undefined||Number.isNaN(Number(n))?'—':`${(Number(n)*100).toFixed(d)}%`; }
function median(values){const x=values.filter(v=>v!==null&&Number.isFinite(Number(v))).map(Number).sort((a,b)=>a-b);if(!x.length)return null;const m=Math.floor(x.length/2);return x.length%2?x[m]:(x[m-1]+x[m])/2;}
function quantile(values,q){const x=values.filter(v=>v!==null&&Number.isFinite(Number(v))).map(Number).sort((a,b)=>a-b);if(!x.length)return null;const p=(x.length-1)*q,b=Math.floor(p),r=p-b;return x[b+1]!==undefined?x[b]+r*(x[b+1]-x[b]):x[b];}
function humanStage(s){return LABELS[s] || s.replaceAll('_',' ');}
function selectedFilters(){return {route:document.getElementById('routeFilter').value,service:document.getElementById('serviceFilter').value,start:document.getElementById('startMonth').value,end:document.getElementById('endMonth').value};}
function filteredCases(){const f=selectedFilters();return D.cases.filter(x=>(f.route==='all'||x.funding_route===f.route)&&(f.service==='all'||x.service_group===f.service)&&(!f.start||x.referral_month>=f.start)&&(!f.end||x.referral_month<=f.end));}
function filteredAppointments(){const f=selectedFilters();return D.appointments.filter(x=>(f.route==='all'||x.funding_route===f.route)&&(f.service==='all'||x.service_group===f.service)&&(!f.start||x.scheduled_month>=f.start)&&(!f.end||x.scheduled_month<=f.end));}
function filteredQueue(){const f=selectedFilters();return D.support_queue.filter(x=>(f.route==='all'||x.funding_route===f.route)&&(f.service==='all'||x.service_group===f.service));}
function stageCounts(cases){return STAGES.map(s=>cases.filter(x=>s==='referral_received'||x[{referral_accepted:'accepted',first_contact:'contacted',assessment_booked:'booked',assessment_attended:'attended',assessment_completed:'completed',treatment_started:'treatment'}[s]]).length);}
function setKpi(id,value,sub){document.querySelector(`#${id} .k-value`).textContent=value;if(sub!==undefined)document.querySelector(`#${id} .k-sub`).textContent=sub;}
function plot(id,traces,layout={}){Plotly.react(id,traces,{...baseLayout,...layout},plotCfg);}
function groupCount(rows,key){const out={};rows.forEach(r=>{const k=r[key]??'Unknown';out[k]=(out[k]||0)+1;});return out;}
function monthlyCounts(cases){const out={};cases.forEach(x=>out[x.referral_month]=(out[x.referral_month]||0)+1);return Object.entries(out).sort((a,b)=>a[0].localeCompare(b[0]));}
function weeklyCounts(cases){const out={};cases.forEach(x=>out[x.referral_week]=(out[x.referral_week]||0)+1);return Object.entries(out).sort((a,b)=>a[0].localeCompare(b[0]));}
