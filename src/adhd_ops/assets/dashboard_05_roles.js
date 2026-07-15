let currentRole = localStorage.getItem('adhdDsRole') || 'operations';
function roleProfile(){return D.meta.role_profiles[currentRole] || D.meta.role_profiles.operations;}
function hasPatientAccess(){return Boolean(roleProfile().patient_level_access);}
function applyRole(){
  const profile=roleProfile(),allowed=new Set(profile.allowed_views);
  document.querySelectorAll('.nav-btn').forEach(btn=>{btn.hidden=!allowed.has(btn.dataset.view);});
  document.querySelectorAll('[data-patient-level]').forEach(el=>el.classList.toggle('access-hidden',!profile.patient_level_access));
  document.getElementById('roleFilter').value=currentRole;
  localStorage.setItem('adhdDsRole',currentRole);
  const roleText=document.getElementById('roleContext');if(roleText)roleText.textContent=`${profile.label} view`;
  if(!allowed.has(activeView))activateView(profile.default_view);
  else renderActive();
}
function initRoles(){
  const select=document.getElementById('roleFilter');
  select.value=currentRole;
  select.addEventListener('change',()=>{currentRole=select.value;applyRole();});
  applyRole();
}
