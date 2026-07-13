function renderDemand(){
  const a=D.weekly_actuals,f=D.forecast;
  const p10=[...f].reverse();
  plot('demandForecast',[
    {x:a.map(x=>x.week_start),y:a.map(x=>x.referrals),type:'scatter',mode:'lines',name:'Observed synthetic referrals',line:{color:COLORS.navy,width:2}},
    {x:f.map(x=>x.week_start),y:f.map(x=>x.p90_referrals),type:'scatter',mode:'lines',name:'P10–P90 range',line:{width:0},showlegend:false,hoverinfo:'skip'},
    {x:p10.map(x=>x.week_start),y:p10.map(x=>x.p10_referrals),type:'scatter',mode:'lines',fill:'tonexty',fillcolor:'rgba(47,111,237,.15)',line:{width:0},name:'P10–P90 range',hoverinfo:'skip'},
    {x:f.map(x=>x.week_start),y:f.map(x=>x.predicted_referrals),type:'scatter',mode:'lines+markers',name:'Selected forecast',line:{color:COLORS.blue,width:3}}
  ],{xaxis:{title:'Week',gridcolor:'#edf2f7'},yaxis:{title:'Referrals',rangemode:'tozero',gridcolor:'#edf2f7'},legend:{orientation:'h',y:1.12,x:0}});
  const names=[...new Set(D.capacity_scenarios.map(x=>x.scenario))];
  const traces=names.map((name,i)=>{const g=D.capacity_scenarios.filter(x=>x.scenario===name);return {x:g.map(x=>x.week_start),y:g.map(x=>x.backlog_patients),type:'scatter',mode:'lines',name:name.replaceAll('_',' '),line:{width:name==='baseline'?4:2,dash:name==='baseline'?'solid':'dot',color:[COLORS.navy,COLORS.green,COLORS.orange,COLORS.cyan,COLORS.red][i%5]}};});
  plot('scenarioLines',traces,{xaxis:{title:'Planning week',gridcolor:'#edf2f7'},yaxis:{title:'Backlog patients',gridcolor:'#edf2f7'},legend:{orientation:'h',y:1.18,x:0}});
  renderScenarioTable();renderPlanner();
}
function renderScenarioTable(){
  const names=[...new Set(D.capacity_scenarios.map(x=>x.scenario))];const baseline=D.capacity_scenarios.filter(x=>x.scenario==='baseline').at(-1);
  const rows=names.map(name=>{const g=D.capacity_scenarios.filter(x=>x.scenario===name),end=g.at(-1);return {name,end:end.backlog_patients,wait:end.wait_days_proxy,minutes:end.available_minutes,dna:end.assumed_dna_rate,delta:end.backlog_patients-baseline.backlog_patients};}).sort((a,b)=>a.end-b.end);
  document.getElementById('scenarioTable').innerHTML=`<thead><tr><th>Scenario</th><th>End backlog</th><th>Change vs baseline</th><th>Wait proxy</th><th>Weekly minutes</th><th>Assumed DNA</th></tr></thead><tbody>${rows.map(r=>`<tr><td>${r.name.replaceAll('_',' ')}</td><td>${fmt(r.end,0)}</td><td style="color:${r.delta<0?COLORS.green:r.delta>0?COLORS.red:COLORS.muted}">${r.delta>0?'+':''}${fmt(r.delta,0)}</td><td>${fmt(r.wait,0)} d</td><td>${fmt(r.minutes,0)}</td><td>${pct(r.dna)}</td></tr>`).join('')}</tbody>`;
}
function renderPlanner(){
  const demandPct=Number(document.getElementById('planDemand').value),capacityPct=Number(document.getElementById('planCapacity').value),extra=Number(document.getElementById('planExtra').value),dnaReduction=Number(document.getElementById('planDna').value);
  document.getElementById('planDemandVal').textContent=`${demandPct>=0?'+':''}${demandPct}%`;document.getElementById('planCapacityVal').textContent=`${capacityPct>=0?'+':''}${capacityPct}%`;document.getElementById('planExtraVal').textContent=`${extra} min`;document.getElementById('planDnaVal').textContent=`${dnaReduction}%`;
  let backlog=D.meta.initial_backlog;const duration=D.meta.assessment_duration_minutes,conv=D.meta.assessment_conversion,baseMins=D.meta.base_available_minutes,baseDna=D.meta.base_dna_rate;const rows=[];
  D.forecast.forEach(w=>{const refs=Number(w.predicted_referrals)*(1+demandPct/100),arrivals=refs*conv,available=baseMins*(1+capacityPct/100)+extra,effectiveDna=baseDna*(1-dnaReduction/100),throughput=available/duration*(1-effectiveDna);backlog=Math.max(0,backlog+arrivals-throughput);rows.push({week:w.week_start,backlog,arrivals,throughput,wait:7*backlog/Math.max(throughput,1),available,effectiveDna});});
  const end=rows.at(-1),change=end.backlog-D.capacity_scenarios.filter(x=>x.scenario==='baseline').at(-1).backlog_patients;
  document.getElementById('planBacklog').textContent=fmt(end.backlog,0);document.getElementById('planWait').textContent=`${fmt(end.wait,0)} d`;document.getElementById('planThroughput').textContent=fmt(end.throughput,1);document.getElementById('planDelta').textContent=`${change>0?'+':''}${fmt(change,0)}`;
  document.getElementById('plannerMessage').innerHTML=change<-50?`<span class="badge good">Improves synthetic backlog</span> This setting reduces the end backlog by ${fmt(Math.abs(change),0)} patients versus the stored baseline.`:change>50?`<span class="badge risk">Worsens synthetic backlog</span> This setting adds ${fmt(change,0)} patients versus the stored baseline.`:`<span class="badge warn">Small change</span> The end backlog remains close to the stored baseline.`;
  plot('plannerChart',[{x:rows.map(x=>x.week),y:rows.map(x=>x.backlog),type:'scatter',mode:'lines+markers',name:'Custom scenario',line:{color:COLORS.blue,width:4},fill:'tozeroy',fillcolor:'rgba(47,111,237,.10)'},{x:D.capacity_scenarios.filter(x=>x.scenario==='baseline').map(x=>x.week_start),y:D.capacity_scenarios.filter(x=>x.scenario==='baseline').map(x=>x.backlog_patients),type:'scatter',mode:'lines',name:'Stored baseline',line:{color:COLORS.navy,width:2,dash:'dash'}}],{xaxis:{title:'Planning week',gridcolor:'#edf2f7'},yaxis:{title:'Backlog patients',gridcolor:'#edf2f7'},legend:{orientation:'h',y:1.12,x:0}});
}
