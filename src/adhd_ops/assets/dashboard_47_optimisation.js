function feasibleOptimPlans(budget){return D.resource_optimisation.filter(x=>Number(x.horizon_cost_proxy_gbp)<=budget).sort((a,b)=>Number(a.end_backlog)-Number(b.end_backlog)||Number(a.horizon_cost_proxy_gbp)-Number(b.horizon_cost_proxy_gbp));}
function renderOptimisation(){
  const budget=Number(document.getElementById('optimBudget').value);document.getElementById('optimBudgetValue').textContent=gbp(budget,0);
  const feasible=feasibleOptimPlans(budget),best=feasible[0]||D.resource_optimisation[0];
  setKpi('o-plan',best.plan_id,`${gbp(best.horizon_cost_proxy_gbp,0)} used`);setKpi('o-backlog',fmt(best.end_backlog,0),`${fmt(best.backlog_patients_avoided,0)} avoided vs baseline`);setKpi('o-minutes',fmt(best.extra_assessment_minutes_per_week,0),'Per week');setKpi('o-outreach',fmt(best.outreach_contacts_per_week,0),'Per week');
  const grid=D.resource_optimisation,pareto=grid.filter(x=>x.pareto_efficient);
  plot('optimisationPareto',[
    {type:'scatter',mode:'markers',x:grid.map(x=>x.horizon_cost_proxy_gbp),y:grid.map(x=>x.end_backlog),name:'Enumerated plans',marker:{color:'#cbd5e1',size:8},text:grid.map(x=>`${x.plan_id}<br>${x.extra_assessment_minutes_per_week} min + ${x.outreach_contacts_per_week} contacts`),hovertemplate:'%{text}<br>Cost %{x:£,.0f}<br>End backlog %{y:.0f}<extra></extra>'},
    {type:'scatter',mode:'lines+markers',x:pareto.map(x=>x.horizon_cost_proxy_gbp),y:pareto.map(x=>x.end_backlog),name:'Pareto frontier',marker:{color:COLORS.blue,size:10},line:{color:COLORS.blue,width:3}},
    {type:'scatter',mode:'markers',x:[best.horizon_cost_proxy_gbp],y:[best.end_backlog],name:'Budget recommendation',marker:{color:COLORS.red,size:15,symbol:'star'}}
  ],{xaxis:{title:'12-week cost proxy (£)',gridcolor:'#edf2f7'},yaxis:{title:'End backlog (lower is better)',gridcolor:'#edf2f7'},legend:{orientation:'h',y:1.14}});
  document.getElementById('budgetTable').innerHTML=`<thead><tr><th>Budget</th><th>Plan</th><th>Extra min/wk</th><th>Contacts/wk</th><th>End backlog</th><th>Avoided</th></tr></thead><tbody>${D.budget_recommendations.map(x=>`<tr class="${x.plan_id===best.plan_id?'pareto-plan':''}"><td>${gbp(x.budget_gbp,0)}</td><td>${esc(x.plan_id)}</td><td>${fmt(x.extra_assessment_minutes_per_week)}</td><td>${fmt(x.outreach_contacts_per_week)}</td><td>${fmt(x.end_backlog,0)}</td><td>${fmt(x.backlog_patients_avoided,0)}</td></tr>`).join('')}</tbody>`;
  const drivers=D.backlog_drivers.filter(x=>x.scenario!=='baseline').sort((a,b)=>a.backlog_difference_vs_baseline-b.backlog_difference_vs_baseline);
  plot('driverChart',[{type:'bar',orientation:'h',y:drivers.map(x=>x.driver),x:drivers.map(x=>x.backlog_difference_vs_baseline),marker:{color:drivers.map(x=>Number(x.backlog_difference_vs_baseline)>0?COLORS.red:COLORS.green)},text:drivers.map(x=>`${Number(x.backlog_difference_vs_baseline)>0?'+':''}${fmt(x.backlog_difference_vs_baseline,0)}`),textposition:'outside'}],{xaxis:{title:'End-backlog difference vs baseline',zeroline:true,zerolinecolor:'#64748b',gridcolor:'#edf2f7'},yaxis:{automargin:true},margin:{l:190,r:45,t:20,b:45},showlegend:false});
  renderPilot();renderExperimentTables();
}
function renderPilot(){
  const effect=Number(document.getElementById('pilotEffect').value)/100,weekly=Number(document.getElementById('pilotCapacity').value);document.getElementById('pilotEffectValue').textContent=pct(effect,0);document.getElementById('pilotCapacityValue').textContent=fmt(weekly);
  const design=D.experiment_design.reduce((a,b)=>Math.abs(Number(b.assumed_relative_reduction)-effect)<Math.abs(Number(a.assumed_relative_reduction)-effect)?b:a,D.experiment_design[0]);
  setKpi('p-total',fmt(design.total_sample_size),`α ${design.alpha}, power ${pct(design.power,0)}`);setKpi('p-arm',fmt(design.n_per_arm),'Two equal arms');setKpi('p-weeks',fmt(Math.max(Number(D.meta.experimentation.minimum_pilot_weeks),Math.ceil(Number(design.total_sample_size)/weekly))),'At selected recruitment capacity');setKpi('p-absolute',pct(design.absolute_reduction,1),`${pct(design.baseline_dna_rate,1)} to ${pct(design.assumed_treatment_dna_rate,1)}`);
}
function renderExperimentTables(){
  document.getElementById('experimentTable').innerHTML=`<thead><tr><th>Relative reduction</th><th>Absolute reduction</th><th>N/arm</th><th>Total N</th><th>Weeks</th></tr></thead><tbody>${D.experiment_design.map(x=>`<tr><td>${pct(x.assumed_relative_reduction,0)}</td><td>${pct(x.absolute_reduction,1)}</td><td>${fmt(x.n_per_arm)}</td><td>${fmt(x.total_sample_size)}</td><td>${fmt(x.weeks_at_recruitment_capacity)}</td></tr>`).join('')}</tbody>`;
  document.getElementById('guardrailTable').innerHTML=`<thead><tr><th>Metric</th><th>Direction</th><th>Why monitor</th><th>Decision rule</th></tr></thead><tbody>${D.experiment_guardrails.map(x=>`<tr><td>${esc(x.metric.replaceAll('_',' '))}</td><td>${esc(x.direction.replaceAll('_',' '))}</td><td>${esc(x.purpose)}</td><td>${esc(x.decision_rule)}</td></tr>`).join('')}</tbody>`;
}
