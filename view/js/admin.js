// Admin specific JS
// Reuses some utilities from user index.js concept but kept isolated

const ADMIN_API_BASE = 'http://127.0.0.1:8000/api/v1';
const ADMIN_TOKEN_KEY = 'access_token'; // reuse same token so switching works

function adminGetToken(){ return localStorage.getItem('access_token') || localStorage.getItem('auth_token'); }
function adminClearToken(){ localStorage.removeItem('access_token'); localStorage.removeItem('auth_token'); }

async function adminApi(endpoint, opts={}){
  const token = adminGetToken();
  const headers = Object.assign({'Accept':'application/json','Content-Type':'application/json'}, opts.headers||{});
  if(token) headers['Authorization'] = 'Bearer ' + token;
  const res = await fetch(ADMIN_API_BASE + endpoint, { ...opts, headers });
  if(res.status === 401) throw new Error('Unauthorized');
  let data = null;
  try { data = await res.json(); } catch{ /* ignore */ }
  if(!res.ok) throw new Error(data?.detail || 'Request failed ' + res.status);
  return data;
}

async function adminRequireAuth({requireAdmin=true}={}){
  const token = adminGetToken();
  if(!token){ window.location.href='/admin/login'; return null; }
  try {
    const me = await adminApi('/auth/me');
    if(requireAdmin && !me.is_admin){ window.location.href='/admin/login'; return null; }
    return me;
  } catch(e){
    adminClearToken();
    window.location.href='/admin/login';
    return null;
  }
}

// Track if layout has been injected to prevent multiple calls
let layoutInjected = false;

async function injectAdminLayout(active){
  // Prevent multiple injections
  if(layoutInjected) {
    console.info('[admin-layout] Already injected, skipping');
    highlightActiveNav(active);
    return;
  }
  
  const mountNav = document.getElementById('navbarMount');
  const mountFooter = document.getElementById('footerMount');
  
  // If mount points don't exist, we're not on an admin page
  if(!mountNav && !mountFooter) {
    console.warn('[admin-layout] Mount points not found, skipping injection');
    return;
  }
  
  // Reordered & cleaned: absolute stable paths first, remove duplicating relative 'admin/partials'
  const paths = [
    '/admin/partials/layout.html',             // authoritative dynamic route
    '/admin-static/partials/layout.html',      // direct static mount
    '/static/admin/partials/layout.html',      // via /static root
    '/view/admin/partials/layout.html',        // unified /view mount
    'partials/layout.html',                    // relative (when inside /admin root page)
    './partials/layout.html'                   // explicit relative
  ];
  let injected = false;
  for(const p of paths){
    try {
      const r = await fetch(p, {cache:'no-store'});
      if(!r.ok) throw new Error(String(r.status));
      const html = await r.text();
      const doc = new DOMParser().parseFromString(html,'text/html');
      const nav = doc.getElementById('adminNavbar');
      const footer = doc.getElementById('adminFooter');
      if(nav && mountNav) mountNav.replaceWith(nav);
      if(footer && mountFooter) mountFooter.replaceWith(footer);
      injected = true;
      console.info('[admin-layout] injected from', p);
      break;
    } catch(e){
      console.warn('[admin-layout] path failed', p, e.message);
    }
  }
  if(!injected){
    console.warn('[admin-layout] All attempts failed. Using fallback elements.');
    if(mountNav){
      mountNav.outerHTML = `
        <header id="adminNavbar" class="bg-white border-b border-gray-border px-4 py-3 flex items-center justify-between">
          <a href="/admin/dashboard" class="text-lg font-semibold text-gray-800">Admin Portal</a>
          <div class="flex items-center gap-3">
            <button id="mobileNavToggle" class="md:hidden p-2 border border-gray-border rounded">☰</button>
            <button id="logoutBtn" class="hidden md:inline-block text-sm bg-gray-100 hover:bg-gray-200 px-3 py-1.5 rounded-md">Logout</button>
          </div>
        </header>`;
    }
    if(mountFooter){
      mountFooter.outerHTML = `
        <footer id="adminFooter" class="mt-16 py-6 text-center text-xs text-gray-500 border-t border-gray-100">&copy; <span data-year></span> UniRecommend Admin Suite</footer>`;
    }
  }
  
  layoutInjected = true;
  highlightActiveNav(active);
  bindAdminLayoutEvents();
}

function highlightActiveNav(active){
  document.querySelectorAll('[data-link]')
    .forEach(a=>{
      if(a.getAttribute('data-link')===active){
        a.classList.add('text-primary','font-medium');
        a.classList.remove('text-gray-600');
      }
    });
  document.querySelectorAll('[data-year]').forEach(e=> e.textContent = new Date().getFullYear());
}

// Track if events have been bound to prevent duplicates
let eventsAlreadyBound = false;

function bindAdminLayoutEvents(){
  // Prevent duplicate event binding
  if(eventsAlreadyBound) {
    console.info('[admin-layout] Events already bound, skipping');
    return;
  }
  
  const toggle = document.getElementById('mobileNavToggle');
  const mobileNav = document.getElementById('mobileNav');
  if(toggle && mobileNav && !toggle.dataset.bound){
    toggle.addEventListener('click', () => {
      const open = !mobileNav.classList.contains('hidden');
      mobileNav.classList.toggle('hidden');
      toggle.setAttribute('aria-expanded', String(!open));
      const bars = toggle.querySelectorAll('span');
      if(!open){
        bars[0].style.transform='translateY(6px) rotate(45deg)';
        bars[1].style.opacity='0';
        bars[2].style.transform='translateY(-6px) rotate(-45deg)';
      } else {
        bars.forEach(b=>{ b.style.transform=''; b.style.opacity='1'; });
      }
    });
    toggle.dataset.bound='1';
  }
  
  // More specific and safer logout binding
  const logoutBtn = document.getElementById('logoutBtn');
  const mobileLogoutBtn = document.getElementById('mobileLogoutBtn');
  
  const doLogout = async (e) => { 
    e.preventDefault();
    e.stopPropagation();
    
    // Add confirmation to prevent accidental logout
    if (!confirm('Are you sure you want to logout?')) {
      return;
    }
    
    try { 
      await adminApi('/auth/logout', {method:'POST'}); 
    } catch(err) {
      console.warn('Logout API call failed:', err.message);
    } 
    adminClearToken(); 
    window.location.href='/admin/login'; 
  };
  
  // Only bind to actual logout buttons with more specific selectors
  if(logoutBtn && logoutBtn.textContent.toLowerCase().includes('logout') && !logoutBtn.dataset.bound){ 
    logoutBtn.addEventListener('click', doLogout); 
    logoutBtn.dataset.bound='1'; 
  }
  if(mobileLogoutBtn && mobileLogoutBtn.textContent.toLowerCase().includes('logout') && !mobileLogoutBtn.dataset.bound){ 
    mobileLogoutBtn.addEventListener('click', doLogout); 
    mobileLogoutBtn.dataset.bound='1'; 
  }
  
  // Prevent navbar navigation links from triggering logout
  document.querySelectorAll('[data-link]').forEach(link => {
    if (!link.dataset.navBound) {
      link.addEventListener('click', (e) => {
        // Only allow navigation, don't trigger any other handlers
        e.stopPropagation();
      });
      link.dataset.navBound = '1';
    }
  });
  
  eventsAlreadyBound = true;
}

// Dashboard specific loader (called from page inline or we can auto-detect path)
async function loadAdminDashboard(){
  const me = await adminRequireAuth();
  if(!me) return;
  const nameEl = document.getElementById('adminName');
  if(nameEl) nameEl.textContent = me.first_name || 'Admin';
  // Load KPIs (best-effort)
  try {
    const [userStats, programCounts, appStats, recentApps] = await Promise.all([
      adminApi('/users/stats'),
      adminApi('/programs/count'),
      adminApi('/applications/stats'),
      adminApi('/applications?page=1&per_page=5')
    ]);
    setText('totalUsers', userStats.total ?? '—');
    setText('usersDelta', (userStats.admins ?? 0) + ' admins');
    const activePrograms = programCounts.active ?? 0;
    const totalPrograms = programCounts.total ?? activePrograms;
    setText('totalPrograms', activePrograms);
    setText('programsDelta', `${activePrograms}/${totalPrograms}`);
    const totalApps = appStats.total ?? 0;
    setText('totalApplications', totalApps);
    setText('applicationsDelta', (appStats.submitted ?? 0) + ' submitted');
    const lr = document.getElementById('lastRefresh');
    if(lr) lr.textContent = new Date().toLocaleString();
    renderRecentActivity(recentApps);
  } catch(e){
    console.warn('[admin-dashboard] failed KPIs', e.message);
  }
}

// Helpers copied from inline original for reuse
function setText(id,value){ const el=document.getElementById(id); if(el) el.textContent=(value===undefined||value===null)?'—':value; }
function renderRecentActivity(applications){
  const list=document.getElementById('activityList');
  if(!list) return;
  if(!Array.isArray(applications) || !applications.length){
    list.innerHTML='<li class="p-4 text-sm text-gray-500">No recent applications</li>';
    return;
  }
  list.innerHTML='';
  applications.forEach(a=>{
    const li=document.createElement('li');
    const status=a.status ? a.status.toLowerCase().replace('_',' ') : 'unknown';
    const color = a.status==='SUBMITTED'?'bg-primary':a.status==='ACCEPTED'?'bg-success':a.status==='REJECTED'?'bg-danger':'bg-gray-300';
    li.className='p-4 text-sm flex items-start gap-3';
    li.innerHTML=`<span class="w-2 h-2 mt-1 rounded-full ${color}"></span>
      <span class="text-gray-700">App #${a.id} <span class="text-gray-500">(${status})</span> - ${(a.user && a.user.email)||'user'} → ${(a.program && a.program.name)||'program'}</span>`;
    list.appendChild(li);
  });
}

// NOTE: Auto-initialization removed to prevent conflicts.
// Each page now handles its own initialization using injectAdminLayout() and page-specific init functions.

