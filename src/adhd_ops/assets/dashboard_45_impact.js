const DECISION_KEY='adhdDsDecisionRegisterV03';
function decisionRows(){
  const saved=localStorage.getItem(DECISION_KEY);if(!saved)return D.action_queue.map(x=>({...x}));
  try{const parsed=JSON.parse(saved);return Array.isArray(parsed)?parsed:D.action_queue.map(x=>({...x}));}catch{return D.action_queue.map(x=>({...x}));}
}
function saveDecisionRows(rows){localStorage.setItem(DECISION_KEY,JSON.stringify(rows));}
function renderImpact(){
  const select=document.getElementById('impactScenario');
  if(!select.options.length){D.scenario_impact.filter(x=>x.scenario!=='baseline').forEach(x=>select.add(new Option(x.scenario.replaceAll('_',' '),x.scenario)));select.value=D.scenario_impact.filter(x=>x.scenario!=='baseline').sort((a,b)=>a.end_backlog-b.end_backlog)[0]?.scenario||'';}
  const chosen=D.scenario_impact.find(x=>x.scenario===select.value)||D.scenario_impact[0];
  setKpi('i-backlog',`${chosen.backlog_change_vs_baseline>0?'+':''}${fmt(chosen.backlog_change_vs_baseline,0)}`,'Patients at horizon versus baseline');
  setKpi('i-wait',`${chosen.wait_change_vs_baseline>0?'+':''}${fmt(chosen.wait_change_vs_baseline,0)} d`,'Queue wait proxy versus baseline');
  setKpi('i-cost',gbp(chosen.horizon_cost_proxy_gbp,0),'Configured clinician-time proxy');
  setKpi('i-unit',gbp(chosen.cost_per_backlog_patient_avoided_gbp,0),'Only shown when scenario improves backlog');
  const base=D.scenario_impact.find(x=>x.scenario==='baseline');
  plot('impactScenarioChart',[
    {type:'bar',x:['End backlog','End wait proxy'],y:[base.end_backlog,base.end_wait_days_proxy],name:'Baseline',marker:{color:COLORS.muted},text:[fmt(base.end_backlog,0),`${fmt(base.end_wait_days_proxy,0)} d`],textposition:'outside'},
    {type:'bar',x:['End backlog','End wait proxy'],y:[chosen.end_backlog,chosen.end_wait_days_proxy],name:'Selected scenario',marker:{color:COLORS.blue},text:[fmt(chosen.end_backlog,0),`${fmt(chosen.end_wait_days_proxy,0)} d`],textposition:'outside'}
  ],{barmode:'group',yaxis:{title:'Patients / days proxy',gridcolor:'#edf2f7'},legend:{orientation:'h',y:1.15},margin:{l:55,r:20,t:25,b:45}});
  const outreach=D.outreach_impact;
  plot('outreachImpactChart',[
    {type:'bar',x:outreach.map(x=>x.outreach_capacity),y:outreach.map(x=>x.expected_appointments_recovered),name:'Expected appointments recovered',marker:{color:COLORS.green},yaxis:'y'},
    {type:'scatter',x:outreach.map(x=>x.outreach_capacity),y:outreach.map(x=>x.net_value_proxy_gbp),name:'Net value proxy',mode:'lines+markers',line:{color:COLORS.navy,width:3},yaxis:'y2'}
  ],{xaxis:{title:'Weekly outreach capacity',gridcolor:'#edf2f7'},yaxis:{title:'Expected recovered appointments',gridcolor:'#edf2f7'},yaxis2:{title:'Net value proxy (£)',overlaying:'y',side:'right',gridcolor:'rgba(0,0,0,0)'},legend:{orientation:'h',y:1.15}});
  renderDecisionRegister();renderRoleMatrix();
}
function renderDecisionRegister(){
  const rows=decisionRows(),table=document.getElementById('decisionRegister');
  table.innerHTML=`<thead><tr><th>Action</th><th>Priority</th><th>Signal / evidence</th><th>Owner</th><th>Due</th><th>Status</th><th>Decision note</th><th>Escalation</th></tr></thead><tbody>${rows.map((x,i)=>`<tr class="${x.priority==='high'?'row-high':x.status==='recorded'?'row-recorded':''}" data-index="${i}"><td>${esc(x.action_id)}</td><td><span class="badge ${x.priority==='high'?'risk':x.priority==='medium'?'warn':'good'}">${esc(x.priority)}</span></td><td><b>${esc(x.signal.replaceAll('_',' '))}</b><br><small>${esc(x.evidence)}</small></td><td><input class="decision-owner" type="text" value="${esc(x.owner_role)}"></td><td><input class="decision-due" type="date" value="${esc(x.due_on)}"></td><td><select class="decision-status"><option value="open" ${x.status==='open'?'selected':''}>Open</option><option value="in_progress" ${x.status==='in_progress'?'selected':''}>In progress</option><option value="blocked" ${x.status==='blocked'?'selected':''}>Blocked</option><option value="decided" ${x.status==='decided'?'selected':''}>Decided</option><option value="recorded" ${x.status==='recorded'?'selected':''}>Recorded</option></select></td><td><input class="decision-note" type="text" value="${esc(x.decision_note||'')}" placeholder="Rationale / next step"></td><td>${esc(x.escalation_route)}</td></tr>`).join('')}</tbody>`;
  table.querySelectorAll('tbody tr').forEach(row=>{
    const i=Number(row.dataset.index);
    ['decision-owner','decision-due','decision-status','decision-note'].forEach(cls=>row.querySelector(`.${cls}`).addEventListener('change',()=>{
      const current=decisionRows();current[i].owner_role=row.querySelector('.decision-owner').value;current[i].due_on=row.querySelector('.decision-due').value;current[i].status=row.querySelector('.decision-status').value;current[i].decision_note=row.querySelector('.decision-note').value;saveDecisionRows(current);
    }));
  });
}
function exportDecisions(){
  const rows=decisionRows();if(!rows.length)return;const cols=['action_id','priority','signal','source_metric','evidence','owner_role','due_on','status','decision_note','escalation_route','synthetic'];downloadCsv(rows,cols,'synthetic_operational_decision_register.csv');
}
function resetDecisions(){localStorage.removeItem(DECISION_KEY);renderDecisionRegister();}
function downloadCsv(rows,cols,name){const csv=[cols.join(','),...rows.map(r=>cols.map(c=>`"${String(r[c]??'').replaceAll('"','""')}"`).join(','))].join('\n');const blob=new Blob([csv],{type:'text/csv'}),url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download=name;a.click();URL.revokeObjectURL(url);}
function renderRoleMatrix(){
  const holder=document.getElementById('roleMatrix');holder.innerHTML=Object.entries(D.meta.role_profiles).map(([key,p])=>`<div class="role-row ${key===currentRole?'current':''}"><strong>${esc(p.label)}</strong><span>${p.allowed_views.map(v=>v.replaceAll('_',' ')).join(' · ')}</span><span class="badge ${p.patient_level_access?'warn':'good'}">${p.patient_level_access?'Patient queue':'Aggregate only'}</span></div>`).join('');
}
