from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd


def _records(frame: pd.DataFrame) -> list[dict[str, Any]]:
    clean = frame.copy()
    for column in clean.columns:
        if pd.api.types.is_datetime64_any_dtype(clean[column]):
            clean[column] = clean[column].dt.strftime("%Y-%m-%dT%H:%M:%S")
    clean = clean.where(pd.notna(clean), None)
    return clean.to_dict(orient="records")


AUDIT_CSS = r"""
/* v0.5 audit and service layer */
.api-cards{display:grid;grid-template-columns:1fr 1fr;gap:9px;padding:10px 16px 18px}.api-card{border:1px solid var(--line);border-radius:10px;padding:11px;background:#f8fafc}.api-card b{display:block;font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:10px;color:var(--navy);margin-bottom:5px}.api-card span{font-size:10px;color:var(--muted);line-height:1.45}.hash-cell{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:9px;max-width:180px;overflow:hidden;text-overflow:ellipsis}.run-id{font-family:ui-monospace,SFMono-Regular,Menlo,monospace}
@media(max-width:700px){.api-cards{grid-template-columns:1fr}}
"""

AUDIT_SECTION = r"""
<section class="view" id="view-audit">
  <h3 class="section-title">Audit, data contracts and service API</h3><p class="section-lead">This view shows whether a run can be replayed, which source contracts passed, how operational queues change under declared policies, and which incidents require triage. The API is a portfolio service layer, not production authentication.</p>
  <div class="kpis" style="grid-template-columns:repeat(4,1fr)"><div class="kpi positive" id="a-contract"><div class="k-label">Contract rules passed</div><div class="k-value"></div><div class="k-sub"></div></div><div class="kpi" id="a-sources"><div class="k-label">Source tables fingerprinted</div><div class="k-value"></div><div class="k-sub"></div></div><div class="kpi risky" id="a-incidents"><div class="k-label">Open / triage incidents</div><div class="k-value"></div><div class="k-sub"></div></div><div class="kpi" id="a-run"><div class="k-label">Run ID</div><div class="k-value run-id" style="font-size:13px;overflow-wrap:anywhere"></div><div class="k-sub"></div></div></div>
  <div class="grid equal"><div class="panel"><div class="panel-head"><div><div class="panel-title">Data contract gate</div><div class="panel-sub">Schema, key, row-count, type, nullability and allowed-value rules</div></div><span class="badge good">Blocking gate</span></div><div class="table-wrap"><table id="contractTable"></table></div></div><div class="panel"><div class="panel-head"><div><div class="panel-title">Source fingerprints</div><div class="panel-sub">Row counts, event range and SHA-256 content fingerprint for replay</div></div></div><div class="table-wrap"><table id="sourceProfileTable"></table></div></div></div>
  <div class="grid equal"><div class="panel"><div class="panel-head"><div><div class="panel-title">Operational queue-policy comparison</div><div class="panel-sub">Policies allocate the same weekly capacity; lower maximum remaining wait is better, while group gaps require review</div></div></div><div class="panel-body"><div id="queuePolicyChart" class="chart"></div></div><div class="table-wrap"><table id="queuePolicyTable"></table></div></div><div class="panel"><div class="panel-head"><div><div class="panel-title">Incident register</div><div class="panel-sub">Signals, owner, playbook and rollback trigger tied to this run ID</div></div><span class="badge warn">Synthetic triage</span></div><div class="table-wrap"><table id="incidentTable"></table></div></div></div>
  <div class="grid equal"><div class="panel"><div class="panel-head"><div><div class="panel-title">Data lineage</div><div class="panel-sub">Source-to-transformation-to-decision mapping</div></div></div><div class="table-wrap"><table id="lineageTable"></table></div></div><div class="panel"><div class="panel-head"><div><div class="panel-title">Controlled API surface</div><div class="panel-sub">Run locally with <code>adhd-ds-api</code>; patient-level queue requires an operational role header</div></div></div><div class="api-cards"><div class="api-card"><b>GET /health</b><span>Run ID and publication gates</span></div><div class="api-card"><b>GET /v1/summary</b><span>Aggregate synthetic run summary</span></div><div class="api-card"><b>GET /v1/contracts</b><span>Data-contract evidence</span></div><div class="api-card"><b>GET /v1/service-levels</b><span>Green / amber / red controls</span></div><div class="api-card"><b>GET /v1/budget-recommendation</b><span>Declared finite-grid recommendation</span></div><div class="api-card"><b>GET /v1/appointment-support</b><span>Requires X-Role: operations or patient_support</span></div><div class="api-card"><b>GET /v1/audit/manifest</b><span>Config and output hashes</span></div><div class="api-card"><b>GET /v1/audit/incidents</b><span>Run-linked incident register</span></div></div></div></div>
  <div class="governance-grid"><div class="gov-card"><b>Contract before metric</b><span>Schema drift and invalid keys stop publication before dashboard metrics are calculated.</span></div><div class="gov-card"><b>Replayable run</b><span>Config hashes, source fingerprints, package version and output hashes are written to the run manifest.</span></div><div class="gov-card"><b>Policy is not clinical priority</b><span>Queue-policy simulation allocates operational review capacity and must not determine clinical urgency.</span></div><div class="gov-card"><b>API role check is a demo</b><span>A request header demonstrates least-privilege behaviour; production requires identity, authorisation and audit infrastructure.</span></div></div>
</section>
"""


def _audit_script(payload: dict[str, Any]) -> str:
    safe_json = json.dumps(payload, separators=(",", ":"), ensure_ascii=False).replace("</", "<\\/")
    return f"""
<script>
window.AUDIT_DATA={safe_json};
const CORE_RENDER_ACTIVE=renderActive;
const CORE_ACTIVATE_VIEW=activateView;
renderActive=function(){{if(activeView==='audit')renderAudit();else CORE_RENDER_ACTIVE();}};
activateView=function(view){{
  if(view!=='audit')return CORE_ACTIVATE_VIEW(view);
  activeView='audit';
  document.querySelectorAll('.view').forEach(x=>x.classList.toggle('active',x.id==='view-audit'));
  document.querySelectorAll('.nav-btn').forEach(x=>x.classList.toggle('active',x.dataset.view==='audit'));
  document.getElementById('pageHeading').textContent='Audit and service API';
  document.getElementById('pageSubheading').textContent='Data contracts, run replay, queue policy and incidents';
  setTimeout(()=>{{renderAudit();window.dispatchEvent(new Event('resize'));}},30);
  document.querySelector('.sidebar').classList.remove('open');
}};
function renderAudit(){{
  const A=window.AUDIT_DATA;
  const contractPass=A.contract_status.filter(x=>Number(x.failure_count)===0).length;
  const incidentOpen=A.incident_register.filter(x=>['open','triage'].includes(x.status)).length;
  setKpi('a-contract',`${{contractPass}}/${{A.contract_status.length}}`,A.contract_status.some(x=>Number(x.failure_count)>0)?'Publication blocked':'Blocking rules passed');
  setKpi('a-sources',fmt(A.source_profiles.length),'SHA-256 source profiles');
  setKpi('a-incidents',fmt(incidentOpen),'Run-linked operational triage');
  setKpi('a-run',A.run_context.run_id,`v${{A.run_context.package_version}} · ${{String(A.run_context.git_sha).slice(0,12)}}`);
  document.getElementById('contractTable').innerHTML=`<thead><tr><th>Table</th><th>Rule</th><th>Expected</th><th>Observed</th><th>Status</th></tr></thead><tbody>${{A.contract_status.map(x=>`<tr><td>${{esc(x.table)}}</td><td>${{esc(x.rule)}}</td><td>${{esc(x.expected)}}</td><td>${{esc(x.observed)}}</td><td><span class="badge ${{Number(x.failure_count)===0?'good':'risk'}}">${{esc(x.status)}}</span></td></tr>`).join('')}}</tbody>`;
  document.getElementById('sourceProfileTable').innerHTML=`<thead><tr><th>Table</th><th>Rows</th><th>Null cells</th><th>Event range</th><th>Fingerprint</th></tr></thead><tbody>${{A.source_profiles.map(x=>`<tr><td>${{esc(x.table)}}</td><td>${{fmt(x.row_count)}}</td><td>${{fmt(x.null_cells)}}</td><td>${{esc(String(x.min_event_time||'').slice(0,10))}}–${{esc(String(x.max_event_time||'').slice(0,10))}}</td><td class="hash-cell" title="${{esc(x.sha256_fingerprint)}}">${{esc(String(x.sha256_fingerprint).slice(0,16))}}…</td></tr>`).join('')}}</tbody>`;
  const qp=A.queue_policy_comparison;
  plot('queuePolicyChart',[{{type:'bar',x:qp.map(x=>x.policy.replaceAll('_',' ')),y:qp.map(x=>x.max_wait_remaining),name:'Max wait remaining',marker:{{color:COLORS.blue}},text:qp.map(x=>`${{fmt(x.max_wait_remaining,0)}}d`),textposition:'outside'}},{{type:'scatter',mode:'lines+markers',x:qp.map(x=>x.policy.replaceAll('_',' ')),y:qp.map(x=>x.funding_route_selection_gap),name:'Funding-route selection gap',yaxis:'y2',line:{{color:COLORS.orange,width:3}}}}],{{yaxis:{{title:'Maximum remaining wait (days)',gridcolor:'#edf2f7'}},yaxis2:{{title:'Selection-rate gap',tickformat:'.0%',overlaying:'y',side:'right'}},legend:{{orientation:'h',y:1.18}},margin:{{l:55,r:55,t:30,b:65}}}});
  document.getElementById('queuePolicyTable').innerHTML=`<thead><tr><th>Policy</th><th>Selected</th><th>Overdue cleared</th><th>Mean selected wait</th><th>Max wait remaining</th><th>Route gap</th><th>Service gap</th></tr></thead><tbody>${{qp.map(x=>`<tr><td>${{esc(x.policy.replaceAll('_',' '))}}</td><td>${{fmt(x.selected_count)}}</td><td>${{fmt(x.overdue_cases_cleared)}}</td><td>${{fmt(x.mean_wait_selected,1)}}d</td><td>${{fmt(x.max_wait_remaining,1)}}d</td><td>${{pct(x.funding_route_selection_gap)}}</td><td>${{pct(x.service_group_selection_gap)}}</td></tr>`).join('')}}</tbody>`;
  document.getElementById('incidentTable').innerHTML=`<thead><tr><th>Incident</th><th>Severity</th><th>Signal</th><th>Owner</th><th>Status</th><th>Playbook / rollback</th></tr></thead><tbody>${{A.incident_register.map(x=>`<tr><td>${{esc(x.incident_id)}}</td><td><span class="badge ${{x.severity==='critical'||x.severity==='high'?'risk':'warn'}}">${{esc(x.severity)}}</span></td><td>${{esc(x.signal)}}</td><td>${{esc(x.owner_role)}}</td><td>${{esc(x.status)}}</td><td title="${{esc(x.rollback_trigger)}}">${{esc(x.playbook)}}</td></tr>`).join('')}}</tbody>`;
  document.getElementById('lineageTable').innerHTML=`<thead><tr><th>Source</th><th>Transformation</th><th>Downstream products</th></tr></thead><tbody>${{A.data_lineage.map(x=>`<tr><td>${{esc(x.source)}}</td><td>${{esc(x.transformation)}}</td><td>${{esc(x.downstream_products)}}</td></tr>`).join('')}}</tbody>`;
}}
</script>
"""


def augment_dashboard(
    path: str | Path,
    *,
    contract_status: pd.DataFrame,
    source_profiles: pd.DataFrame,
    queue_policy_comparison: pd.DataFrame,
    incident_register: pd.DataFrame,
    data_lineage: pd.DataFrame,
    run_context: dict[str, Any],
) -> None:
    target = Path(path)
    html = target.read_text(encoding="utf-8")
    nav = '<button class="nav-btn" data-view="audit"><span class="nav-icon">⌘</span>Audit & service API</button>'
    if nav not in html:
        html = html.replace(
            '<button class="nav-btn" data-view="governance"><span class="nav-icon">◫</span>Data & model controls</button>',
            '<button class="nav-btn" data-view="governance"><span class="nav-icon">◫</span>Data & model controls</button>\n  ' + nav,
        )
    html = html.replace("</style>", AUDIT_CSS + "\n</style>", 1)
    html = html.replace("</main>", AUDIT_SECTION + "\n</main>", 1)
    payload = {
        "contract_status": _records(contract_status),
        "source_profiles": _records(source_profiles),
        "queue_policy_comparison": _records(queue_policy_comparison),
        "incident_register": _records(incident_register),
        "data_lineage": _records(data_lineage),
        "run_context": run_context,
    }
    html = html.replace("</body>", _audit_script(payload) + "\n</body>", 1)
    target.write_text(html, encoding="utf-8")
