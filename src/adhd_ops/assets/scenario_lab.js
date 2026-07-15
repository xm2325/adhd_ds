<script>
window.SCENARIO_DATA=__SCENARIO_DATA__;
const PRE_SCENARIO_RENDER=renderActive;
const PRE_SCENARIO_ACTIVATE=activateView;
renderActive=function(){if(activeView==='scenario')renderScenarioLab();else PRE_SCENARIO_RENDER();};
activateView=function(view){
  if(view!=='scenario')return PRE_SCENARIO_ACTIVATE(view);
  activeView='scenario';
  document.querySelectorAll('.view').forEach(x=>x.classList.toggle('active',x.id==='view-scenario'));
  document.querySelectorAll('.nav-btn').forEach(x=>x.classList.toggle('active',x.dataset.view==='scenario'));
  document.getElementById('pageHeading').textContent='Data scientist scenario lab';
  document.getElementById('pageSubheading').textContent='Questions, diagnostics, decisions and evidence boundaries';
  setTimeout(()=>{renderScenarioLab();window.dispatchEvent(new Event('resize'));},30);
  document.querySelector('.sidebar').classList.remove('open');
};
let scenarioInitialised=false;
function scenarioLabel(x){return String(x||'').replaceAll('_',' ').replace(/\b\w/g,c=>c.toUpperCase());}
function renderQuestionCard(){
  const S=window.SCENARIO_DATA;
  const id=document.getElementById('scenarioQuestion').value;
  const q=S.questions.find(x=>x.id===id)||S.questions[0];
  if(!q)return;
  document.getElementById('scenarioQuestionCard').innerHTML=`<div class="scenario-meta"><span class="badge info">${esc(q.category.replaceAll('_',' '))}</span><span class="badge synthetic">${esc(q.stakeholder)}</span></div><h3>${esc(q.id)} — ${esc(q.question)}</h3><div class="scenario-answer"><b>Current synthetic answer</b><br>${esc(q.current_synthetic_answer)}</div><div class="scenario-grid"><div class="scenario-box"><b>Why this is asked</b><span>${esc(q.why_asked)}</span></div><div class="scenario-box"><b>How to solve it</b><span>${esc(q.method)}</span></div><div class="scenario-box"><b>Inputs</b><span>${esc(q.required_inputs)}</span></div><div class="scenario-box"><b>Output</b><span>${esc(q.deliverable)}</span></div><div class="scenario-box"><b>Risk if wrong</b><span>${esc(q.risk_if_wrong)}</span></div><div class="scenario-box"><b>Next action</b><span>${esc(q.next_action)}</span></div></div>`;
}
function initScenarioControls(){
  if(scenarioInitialised)return;scenarioInitialised=true;
  const S=window.SCENARIO_DATA,category=document.getElementById('scenarioCategory'),question=document.getElementById('scenarioQuestion');
  const categories=[...new Set(S.questions.map(x=>x.category))];
  category.innerHTML='<option value="all">All categories</option>'+categories.map(x=>`<option value="${esc(x)}">${esc(scenarioLabel(x))}</option>`).join('');
  function fill(){const rows=category.value==='all'?S.questions:S.questions.filter(x=>x.category===category.value);question.innerHTML=rows.map(x=>`<option value="${esc(x.id)}">${esc(x.id+' — '+x.question)}</option>`).join('');renderQuestionCard();}
  category.addEventListener('change',fill);question.addEventListener('change',renderQuestionCard);fill();
}
function renderScenarioLab(){
  const S=window.SCENARIO_DATA;initScenarioControls();renderQuestionCard();
  const strengthOrder={strong_signal:0,moderate_signal:1,weak_or_no_signal:2};
  const roots=[...S.root_causes].sort((a,b)=>strengthOrder[a.signal_strength]-strengthOrder[b.signal_strength]);
  const topRoot=roots[0],topStage=[...S.stage_duration].sort((a,b)=>Number(b.share_of_complete_pathway_mean)-Number(a.share_of_complete_pathway_mean))[0];
  const defaultRows=S.threshold_grid.filter(x=>Number(x.weekly_capacity)===Number(S.default_capacity));
  const policy=[...defaultRows].sort((a,b)=>Number(b.expected_appointments_recovered)-Number(a.expected_appointments_recovered))[0];
  setKpi('s-questions',fmt(S.questions.length),'Run-specific workplace questions');
  setKpi('s-root',scenarioLabel(topRoot.hypothesis),topRoot.signal_strength.replaceAll('_',' '));
  setKpi('s-stage',topStage.stage_label,`${pct(topStage.share_of_complete_pathway_mean)} of complete-pathway mean`);
  setKpi('s-policy',`${fmt(policy.weekly_capacity)} @ ${pct(policy.minimum_probability)}`,`${pct(policy.precision)} precision · ${pct(policy.recall)} recall`);
  document.getElementById('rootCauseSignals').innerHTML=roots.map(x=>`<div class="signal-row ${x.signal_strength==='strong_signal'?'signal-strong':x.signal_strength==='moderate_signal'?'signal-moderate':'signal-weak'}"><strong>${esc(scenarioLabel(x.hypothesis))}</strong><span><b>${esc(x.signal_strength.replaceAll('_',' '))}</b><br>${esc(x.owner)}</span><span>${esc(x.evidence)}<br><b>Next:</b> ${esc(x.next_analysis)}</span></div>`).join('');
  const stages=[...S.stage_duration].reverse();
  plot('stageDurationChart',[{type:'bar',orientation:'h',y:stages.map(x=>x.stage_label),x:stages.map(x=>x.median_days),name:'Median days',marker:{color:COLORS.blue},text:stages.map(x=>`${fmt(x.median_days,1)}d · ${pct(x.share_of_complete_pathway_mean)}`),textposition:'outside'}],{xaxis:{title:'Median days',gridcolor:'#edf2f7'},margin:{l:185,r:70,t:20,b:45},showlegend:false});
  const dna=S.dna_decomposition.slice(0,12).reverse();
  plot('dnaContributionChart',[{type:'bar',orientation:'h',y:dna.map(x=>`${x.dimension}: ${x.segment}`),x:dna.map(x=>100*Number(x.total_contribution)),marker:{color:dna.map(x=>Number(x.total_contribution)>=0?COLORS.red:COLORS.green)},text:dna.map(x=>`${fmt(100*Number(x.total_contribution),2)}pp`),textposition:'outside'}],{xaxis:{title:'Contribution to observed DNA-rate change (percentage points)',zeroline:true,gridcolor:'#edf2f7'},margin:{l:190,r:65,t:20,b:50},showlegend:false});
  const capacities=[...new Set(S.threshold_grid.map(x=>Number(x.weekly_capacity)))].sort((a,b)=>a-b),thresholds=[...new Set(S.threshold_grid.map(x=>Number(x.minimum_probability)))].sort((a,b)=>a-b);
  const z=capacities.map(c=>thresholds.map(t=>{const r=S.threshold_grid.find(x=>Number(x.weekly_capacity)===c&&Math.abs(Number(x.minimum_probability)-t)<1e-8);return r?Number(r.precision):null;}));
  plot('thresholdHeatmap',[{type:'heatmap',x:thresholds,y:capacities,z:z,colorscale:'Blues',zmin:0,zmax:1,colorbar:{title:'Precision',tickformat:'.0%'},hovertemplate:'Threshold %{x:.0%}<br>Capacity %{y}<br>Precision %{z:.1%}<extra></extra>'}],{xaxis:{title:'Minimum predicted probability',tickformat:'.0%'},yaxis:{title:'Weekly outreach capacity'},margin:{l:60,r:30,t:20,b:55}});
  const topPolicies=[...S.threshold_grid].filter(x=>Number(x.selected_count)>0).sort((a,b)=>Number(b.expected_appointments_recovered)-Number(a.expected_appointments_recovered)).slice(0,10);
  document.getElementById('thresholdPolicyTable').innerHTML=`<thead><tr><th>Capacity</th><th>Threshold</th><th>Selected</th><th>Precision</th><th>Recall</th><th>Expected recovered</th><th>Route gap</th></tr></thead><tbody>${topPolicies.map(x=>`<tr><td>${fmt(x.weekly_capacity)}</td><td>${pct(x.minimum_probability)}</td><td>${fmt(x.selected_count)}</td><td>${pct(x.precision)}</td><td>${pct(x.recall)}</td><td>${fmt(x.expected_appointments_recovered,1)}</td><td>${pct(x.funding_route_selection_gap)}</td></tr>`).join('')}</tbody>`;
  const features=S.feature_effects.slice(0,12).reverse();
  plot('featureEffectChart',[{type:'bar',orientation:'h',y:features.map(x=>String(x.feature).replace('numeric__','').replace('categorical__','')),x:features.map(x=>Number(x.value)),marker:{color:features.map(x=>Number(x.value)>=0?COLORS.orange:COLORS.blue)},text:features.map(x=>fmt(x.value,2)),textposition:'outside'}],{xaxis:{title:'Model coefficient / importance',zeroline:true,gridcolor:'#edf2f7'},margin:{l:185,r:65,t:20,b:50},showlegend:false});
  document.getElementById('metricSensitivityTable').innerHTML=`<thead><tr><th>Definition</th><th>N</th><th>Median</th><th>P90</th><th>Difference</th><th>Decision use</th></tr></thead><tbody>${S.metric_sensitivity.map(x=>`<tr><td>${esc(x.label)}</td><td>${fmt(x.n)}</td><td>${fmt(x.median_days,1)}d</td><td>${fmt(x.p90_days,1)}d</td><td>${fmt(x.median_difference_vs_patient_experience,1)}d</td><td>${esc(x.decision_use)}</td></tr>`).join('')}</tbody>`;
  document.getElementById('periodComparisonTable').innerHTML=`<thead><tr><th>Metric</th><th>Previous</th><th>Recent</th><th>Absolute change</th><th>Relative change</th></tr></thead><tbody>${S.period_comparison.map(x=>`<tr><td>${esc(x.metric.replaceAll('_',' '))}</td><td>${x.unit==='rate'?pct(x.previous_value):fmt(x.previous_value,1)}</td><td>${x.unit==='rate'?pct(x.recent_value):fmt(x.recent_value,1)}</td><td>${x.unit==='rate'?pct(x.absolute_change):fmt(x.absolute_change,1)}</td><td>${pct(x.relative_change)}</td></tr>`).join('')}</tbody>`;
}
</script>
