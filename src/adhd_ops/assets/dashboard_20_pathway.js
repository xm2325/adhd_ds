function renderPathway(){
  const cases=filteredCases(), counts=stageCounts(cases);
  const nodeLabels=[],nodeColors=[],links={source:[],target:[],value:[],color:[]};
  STAGES.forEach((s,i)=>{nodeLabels.push(humanStage(s));nodeColors.push(i===STAGES.length-1?COLORS.green:COLORS.blue);if(i<STAGES.length-1){nodeLabels.push(`Not progressed after ${humanStage(s).toLowerCase()}`);nodeColors.push('#cbd5e1');}});
  let stageNode=[];let dropoutNode=[];let idx=0;STAGES.forEach((s,i)=>{stageNode.push(idx++);if(i<STAGES.length-1)dropoutNode.push(idx++);});
  for(let i=0;i<STAGES.length-1;i++){links.source.push(stageNode[i],stageNode[i]);links.target.push(stageNode[i+1],dropoutNode[i]);links.value.push(counts[i+1],Math.max(counts[i]-counts[i+1],0));links.color.push('rgba(47,111,237,.35)','rgba(148,163,184,.35)');}
  plot('pathwaySankey',[{type:'sankey',arrangement:'snap',node:{label:nodeLabels,color:nodeColors,pad:13,thickness:16,line:{color:'#fff',width:1}},link:links}],{margin:{l:10,r:10,t:15,b:10},font:{size:10}});

  const groups={};cases.filter(x=>x.days_to_assessment!==null).forEach(x=>{const k=`${x.funding_route==='private'?'Private':'NHS RTC'} · ${x.service_group==='adult'?'Adult':'Under 18'}`;(groups[k]??=[]).push(x.days_to_assessment);});
  const boxTraces=Object.entries(groups).map(([k,v],i)=>({type:'box',name:k,y:v,boxpoints:'outliers',jitter:.25,marker:{size:3},line:{color:[COLORS.blue,COLORS.cyan,COLORS.orange,COLORS.red][i%4]},hovertemplate:`${k}<br>%{y:.1f} days<extra></extra>`}));
  plot('waitDistribution',boxTraces,{yaxis:{title:'Referral-to-assessment days',gridcolor:'#edf2f7',rangemode:'tozero'},xaxis:{tickangle:-12},showlegend:false});

  const months=[...new Set(cases.map(x=>x.referral_month))].sort();const horizons=[30,60,90];const z=horizons.map(h=>months.map(m=>{const g=cases.filter(x=>x.referral_month===m);return g.length?g.filter(x=>x.days_to_assessment!==null&&x.days_to_assessment<=h).length/g.length:null;}));
  plot('cohortHeatmap',[{type:'heatmap',x:months,y:horizons.map(x=>`${x} days`),z:z,zmin:0,zmax:1,colorscale:[[0,'#eef3f9'],[.5,'#7db3ff'],[1,'#168f5b']],colorbar:{title:'Completed',tickformat:'.0%'},hovertemplate:'Referral month %{x}<br>Within %{y}: %{z:.1%}<extra></extra>'}],{xaxis:{title:'Referral cohort',tickangle:-45},yaxis:{title:'Completion horizon'},margin:{l:65,r:30,t:15,b:80}});
  renderSegmentTable(cases);renderExceptionQueue(cases);
}

function renderSegmentTable(cases){
  const keys=[['nhs_right_to_choose','adult'],['nhs_right_to_choose','under_18'],['private','adult'],['private','under_18']];
  const rows=keys.map(([route,service])=>{const g=cases.filter(x=>x.funding_route===route&&x.service_group===service),accepted=g.filter(x=>x.accepted).length,completed=g.filter(x=>x.completed).length,wait=g.map(x=>x.days_to_assessment);return {segment:`${route==='private'?'Private':'NHS RTC'} / ${service==='adult'?'Adult':'Under 18'}`,n:g.length,accept:accepted/Math.max(g.length,1),complete:completed/Math.max(accepted,1),median:median(wait),p90:quantile(wait,.9)};});
  document.getElementById('segmentTable').innerHTML=`<thead><tr><th>Segment</th><th>Referrals</th><th>Accepted</th><th>Completed / accepted</th><th>Median wait</th><th>P90 wait</th></tr></thead><tbody>${rows.map(r=>`<tr><td>${r.segment}</td><td>${fmt(r.n)}</td><td>${pct(r.accept)}</td><td>${pct(r.complete)}</td><td>${fmt(r.median,1)} d</td><td>${fmt(r.p90,1)} d</td></tr>`).join('')}</tbody>`;
}
function ownerAction(stage){return {referral_accepted:['Referral operations','Complete first contact'],first_contact:['Scheduling','Offer an assessment slot'],assessment_booked:['Patient support','Confirm attendance or reschedule'],assessment_attended:['Clinical team','Complete and record assessment'],assessment_completed:['Clinical operations','Review next-step status']}[stage]||['Referral operations','Review referral status'];}
function renderExceptionQueue(cases){
  const table=document.getElementById('exceptionTable');
  if(!hasPatientAccess()){
    table.innerHTML='<tbody><tr><td><div class="restricted"><b>Patient-level queue hidden for this role.</b><br>Switch to Operations or Patient support to demonstrate a restricted workflow. In production, access must be enforced outside the browser.</div></td></tr></tbody>';
    return;
  }
  const open=cases.filter(x=>x.accepted&&!x.treatment).sort((a,b)=>(b.days_open||0)-(a.days_open||0)).slice(0,25);
  table.innerHTML=`<thead><tr><th>Referral</th><th>Route</th><th>Service</th><th>Current stage</th><th>Days open</th><th>Suggested owner</th><th>Next check</th></tr></thead><tbody>${open.map(x=>{const oa=ownerAction(x.current_stage);return `<tr class="clickable-row" data-referral="${x.referral_id}"><td>${x.referral_id}</td><td>${x.funding_route==='private'?'Private':'NHS RTC'}</td><td>${x.service_group==='adult'?'Adult':'Under 18'}</td><td>${humanStage(x.current_stage)}</td><td class="cell-risk">${fmt(x.days_open,0)}</td><td>${oa[0]}</td><td>${oa[1]}</td></tr>`}).join('')}</tbody>`;
  table.querySelectorAll('[data-referral]').forEach(row=>row.addEventListener('click',()=>openCaseModal(row.dataset.referral)));
}
function timelineDate(value){return value?new Date(value).toLocaleDateString('en-GB'):'Not recorded';}
function openCaseModal(referralId){
  if(!hasPatientAccess())return;
  const c=D.cases.find(x=>x.referral_id===referralId);if(!c)return;
  const events=[
    ['Referral received',c.referral_received_at,'referral_received'],
    ['Accepted',c.accepted_at,'referral_accepted'],
    ['First contact',c.first_contact_at,'first_contact'],
    ['Assessment booked',c.scheduled_start,'assessment_booked'],
    ['Assessment completed',c.assessment_completed_at,'assessment_completed'],
    ['Treatment started',c.treatment_started_at,'treatment_started'],
  ];
  const currentIndex=Math.max(0,events.findIndex(x=>x[2]===c.current_stage));
  document.getElementById('caseModalSub').textContent=`${c.referral_id} · ${c.funding_route==='private'?'Private':'NHS RTC'} · ${c.service_group==='adult'?'Adult':'Under 18'} · ${fmt(c.days_open,0)} days open`;
  document.getElementById('caseTimeline').innerHTML=events.map((e,i)=>`<div class="timeline-step ${e[1]?'done':i===currentIndex?'current':''}"><b>${e[0]}</b><span>${timelineDate(e[1])}</span></div>`).join('');
  const oa=ownerAction(c.current_stage);
  document.getElementById('caseChecks').innerHTML=`<b>Operational review</b><br>Current recorded stage: ${humanStage(c.current_stage)}.<br>Suggested owner: ${oa[0]}.<br>Next check: ${oa[1]}.<br><br><b>Boundary:</b> this is a synthetic service-process drill-down, not a clinical record or clinical priority score.`;
  const modal=document.getElementById('caseModal');modal.classList.add('open');modal.setAttribute('aria-hidden','false');
}
function closeCaseModal(){const modal=document.getElementById('caseModal');modal.classList.remove('open');modal.setAttribute('aria-hidden','true');}
