function renderCommand(){
  const cases=filteredCases(), appts=filteredAppointments(), counts=stageCounts(cases);
  const accepted=counts[1], completed=counts[5], treated=counts[6];
  const waits=cases.map(x=>x.days_to_assessment).filter(x=>x!==null);
  const eligible=appts.filter(x=>['attended','did_not_attend'].includes(x.appointment_status));
  const eligibleCount=eligible.reduce((s,x)=>s+Number(x.appointment_count||0),0);
  const attended=eligible.filter(x=>x.appointment_status==='attended').reduce((s,x)=>s+Number(x.appointment_count||0),0);
  const dqPass=D.validation.filter(x=>Number(x.failure_count)===0).length;
  setKpi('k-referrals',fmt(cases.length),`${selectedFilters().start} to ${selectedFilters().end}`);
  setKpi('k-accepted',pct(accepted/Math.max(cases.length,1)),`${fmt(accepted)} accepted referrals`);
  setKpi('k-completed',pct(completed/Math.max(accepted,1)),`${fmt(completed)} completed assessments`);
  setKpi('k-treated',pct(treated/Math.max(completed,1)),`${fmt(treated)} treatment starts`);
  setKpi('k-median',`${fmt(median(waits),1)} days`,'Referral receipt to completed assessment');
  setKpi('k-p90',`${fmt(quantile(waits,.9),1)} days`,'Long-wait tail');
  setKpi('k-attendance',pct(attended/Math.max(eligibleCount,1)),`${fmt(eligibleCount)} eligible appointments`);
  setKpi('k-data',`${dqPass}/${D.validation.length}`,'Automated data checks passing');

  const weekly=weeklyCounts(cases);
  plot('commandTrend',[{x:weekly.map(x=>x[0]),y:weekly.map(x=>x[1]),type:'scatter',mode:'lines',name:'Referrals',line:{color:COLORS.blue,width:3},fill:'tozeroy',fillcolor:'rgba(47,111,237,.10)'}],{xaxis:{title:'Referral week',gridcolor:'#edf2f7'},yaxis:{title:'Referrals',rangemode:'tozero',gridcolor:'#edf2f7'},showlegend:false});
  plot('commandFunnel',[{type:'funnel',y:STAGES.map(humanStage),x:counts,textinfo:'value+percent initial',marker:{color:['#2f6fed','#3d7af0','#4b86ef','#5a92ed','#28aeb4','#14a878','#168f5b']},connector:{line:{color:'#cbd5e1'}}}],{margin:{l:150,r:20,t:20,b:20}});

  const endpoints={};D.capacity_scenarios.forEach(r=>{endpoints[r.scenario]=r;});
  const scen=Object.values(endpoints).sort((a,b)=>a.backlog_patients-b.backlog_patients);
  plot('scenarioOutcome',[{type:'bar',x:scen.map(x=>x.backlog_patients),y:scen.map(x=>x.scenario.replaceAll('_',' ')),orientation:'h',marker:{color:scen.map(x=>x.scenario==='baseline'?COLORS.navy:(x.backlog_patients<endpoints.baseline.backlog_patients?COLORS.green:COLORS.orange))},text:scen.map(x=>fmt(x.backlog_patients,0)),textposition:'outside',hovertemplate:'%{y}<br>End backlog: %{x:.0f}<extra></extra>'}],{xaxis:{title:'Patients at end of planning horizon',gridcolor:'#edf2f7'},yaxis:{automargin:true},margin:{l:175,r:55,t:15,b:45},showlegend:false});
  renderDecisions({cases,counts,waits,dqPass});
}

function renderDecisions({cases,counts,waits,dqPass}){
  const p90=quantile(waits,.9), accepted=counts[1], completed=counts[5];
  const baseline=D.capacity_scenarios.filter(x=>x.scenario==='baseline').at(-1);
  const items=[];
  if(p90!==null&&p90>Number(D.meta.thresholds.p90_assessment_wait_days))items.push({level:'high',title:'Long-wait tail needs an owner',text:`Filtered P90 is ${fmt(p90,1)} days. Review the longest open cases and confirm the service threshold before escalation.`,owner:'Operations lead',due:'This week'});
  if(baseline&&baseline.backlog_patients>Number(D.meta.thresholds.backlog_review_patients))items.push({level:'high',title:'Capacity review required',text:`The baseline synthetic horizon ends with ${fmt(baseline.backlog_patients)} patients in backlog. Compare added-clinic and absence scenarios before roster sign-off.`,owner:'Clinical operations',due:'Planning meeting'});
  if(accepted>0&&completed/accepted<Number(D.meta.thresholds.completed_per_accepted_review_rate))items.push({level:'medium',title:'Pathway conversion below review level',text:`${pct(completed/accepted)} of accepted referrals reached a completed assessment in the selected cohort. Check booking, attendance and still-open cases separately.`,owner:'Pathway manager',due:'Next huddle'});
  if(dqPass===D.validation.length)items.push({level:'low',title:'Data gate passed',text:'All automated checks pass for this synthetic run. Metric ownership and source reconciliation would still be required before production use.',owner:'Data team',due:'Recorded'});
  document.getElementById('decisionList').innerHTML=items.map(x=>`<div class="decision ${x.level==='medium'?'':x.level}"><div class="rail"></div><div><h4>${x.title}</h4><p>${x.text}</p></div><div class="owner"><b>${x.owner}</b>${x.due}</div></div>`).join('');
}
