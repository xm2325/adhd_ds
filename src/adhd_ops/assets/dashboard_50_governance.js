function renderGovernance(){
  const pass=D.validation.filter(x=>Number(x.failure_count)===0).length,fail=D.validation.length-pass;
  setKpi('g-pass',`${pass}/${D.validation.length}`,'Automated rules passing');setKpi('g-fail',fmt(fail),'Rules requiring review');setKpi('g-model',D.model_metrics[0].model.replaceAll('_',' '),`PR-AUC ${Number(D.model_metrics[0].pr_auc).toFixed(3)}`);setKpi('g-forecast',D.forecast[0].selected_model.replaceAll('_',' '),'Selected using rolling backtest');
  document.getElementById('qualityTable').innerHTML=`<thead><tr><th>Table</th><th>Rule</th><th>Severity</th><th>Failures</th><th>Status</th></tr></thead><tbody>${D.validation.map(x=>`<tr><td>${x.table}</td><td>${x.rule.replaceAll('_',' ')}</td><td>${x.severity}</td><td>${fmt(x.failure_count)}</td><td><span class="badge ${Number(x.failure_count)===0?'good':'risk'}">${Number(x.failure_count)===0?'Pass':'Review'}</span></td></tr>`).join('')}</tbody>`;
  plot('modelCompare',[{type:'bar',x:D.model_metrics.map(x=>x.model.replaceAll('_',' ')),y:D.model_metrics.map(x=>x.pr_auc),name:'PR-AUC',marker:{color:COLORS.blue},text:D.model_metrics.map(x=>Number(x.pr_auc).toFixed(3)),textposition:'outside'},{type:'bar',x:D.model_metrics.map(x=>x.model.replaceAll('_',' ')),y:D.model_metrics.map(x=>x.brier_score),name:'Brier score',marker:{color:COLORS.orange},text:D.model_metrics.map(x=>Number(x.brier_score).toFixed(3)),textposition:'outside'}],{barmode:'group',yaxis:{title:'Score',gridcolor:'#edf2f7'},legend:{orientation:'h',y:1.15}});
  plot('forecastCompare',[{type:'bar',x:D.forecast_performance.map(x=>x.model.replaceAll('_',' ')),y:D.forecast_performance.map(x=>x.mean_wape),marker:{color:D.forecast_performance.map((x,i)=>i===0?COLORS.green:COLORS.blue)},text:D.forecast_performance.map(x=>pct(x.mean_wape)),textposition:'outside',hovertemplate:'%{x}<br>Mean WAPE %{y:.1%}<extra></extra>'}],{yaxis:{title:'Mean WAPE (lower is better)',tickformat:'.0%',gridcolor:'#edf2f7'},showlegend:false});
  const am=D.attendance_monitoring;
  plot('attendanceMonitoring',[
    {x:am.map(x=>x.monitoring_month),y:am.map(x=>x.observed_dna_rate),type:'scatter',mode:'lines+markers',name:'Observed DNA',line:{color:COLORS.navy,width:3}},
    {x:am.map(x=>x.monitoring_month),y:am.map(x=>x.mean_predicted_probability),type:'scatter',mode:'lines+markers',name:'Mean predicted',line:{color:COLORS.cyan,width:3}},
    {x:am.map(x=>x.monitoring_month),y:am.map(()=>Number(D.meta.thresholds.attendance_calibration_gap)),type:'scatter',mode:'lines',name:'Gap review level',line:{color:COLORS.orange,dash:'dot'},visible:'legendonly'}
  ],{xaxis:{title:'Monitoring month',gridcolor:'#edf2f7'},yaxis:{title:'Rate / probability',tickformat:'.0%',gridcolor:'#edf2f7'},legend:{orientation:'h',y:1.16}});
  const selected=D.forecast[0].selected_model, fm=D.forecast_monitoring.filter(x=>x.model===selected);
  plot('forecastMonitoring',[
    {x:fm.map(x=>x.origin_week),y:fm.map(x=>x.wape),type:'scatter',mode:'lines+markers',name:'WAPE',line:{color:COLORS.blue,width:3}},
    {x:fm.map(x=>x.origin_week),y:fm.map(()=>Number(D.meta.thresholds.forecast_wape_review)),type:'scatter',mode:'lines',name:'Review level',line:{color:COLORS.red,dash:'dash'}}
  ],{xaxis:{title:'Forecast origin',gridcolor:'#edf2f7'},yaxis:{title:'WAPE',tickformat:'.0%',gridcolor:'#edf2f7'},legend:{orientation:'h',y:1.16}});
}
