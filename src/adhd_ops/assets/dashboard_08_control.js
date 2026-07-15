function controlValue(row){
  if(row.value===null||row.value===undefined||Number.isNaN(Number(row.value)))return '—';
  if(row.display_unit==='rate')return pct(row.value);
  if(row.display_unit==='days')return `${fmt(row.value,1)} d`;
  return fmt(row.value,0);
}
function renderControlTower(){
  const board=document.getElementById('serviceLevelBoard');if(!board)return;
  board.innerHTML=D.service_levels.map(x=>`<div class="slo-card ${esc(x.status)}"><div class="slo-top"><h4>${esc(x.control)}</h4><span class="status-chip ${esc(x.status)}">${esc(x.status)}</span></div><div class="slo-value">${controlValue(x)}</div><p><b>${esc(x.owner_role)}</b> · ${esc(x.response)}</p></div>`).join('');
  const alerts=D.weekly_anomalies.filter(x=>['amber','red'].includes(x.status)).sort((a,b)=>String(b.period_start).localeCompare(String(a.period_start))).slice(0,12);
  const table=document.getElementById('anomalyTable');if(!table)return;
  table.innerHTML=`<thead><tr><th>Period</th><th>Series</th><th>Observed</th><th>Expected</th><th>Robust z</th><th>Status</th></tr></thead><tbody>${alerts.length?alerts.map(x=>`<tr><td>${esc(String(x.period_start).slice(0,10))}</td><td>${esc(x.series.replaceAll('_',' '))}</td><td>${x.series.includes('rate')?pct(x.observed_value):fmt(x.observed_value,1)}</td><td>${x.series.includes('rate')?pct(x.expected_rolling_median):fmt(x.expected_rolling_median,1)}</td><td>${fmt(x.robust_z,2)}</td><td><span class="status-chip ${esc(x.status)}">${esc(x.status)}</span></td></tr>`).join(''):`<tr><td colspan="6">No amber or red anomaly in the current synthetic run.</td></tr>`}</tbody>`;
}
