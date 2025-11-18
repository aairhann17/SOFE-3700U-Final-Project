const VIEWS = [
  'ArtworkSummary',
  'v_artists_dominant_in_nationality',
  'ArtworkOrigins',
  'v_recent_artworks',
  'v_artists_zero_or_multiple',
  'v_full_objects_origins',
  'v_artworks_by_prolific_artists',
  'v_gallery_artwork_counts',
  'v_artist_artwork_titles',
  'v_multi_artist_artworks'
];
let currentView = null;
let currentPageView = 1;
const limitView = 25;

function initViewsMenu(){
  const list = document.getElementById('viewsList');
  VIEWS.forEach(v => {
    const a = document.createElement('a');
    a.href = '#';
    a.className = 'list-group-item list-group-item-action';
    a.textContent = v;
    a.onclick = (e)=>{
      e.preventDefault();
      // toggle active state
      [...list.querySelectorAll('a')].forEach(el=>el.classList.remove('active'));
      a.classList.add('active');
      loadView(v,1);
    };
    list.appendChild(a);
  });
}

function clearViewArea(){
  const thead = document.querySelector('#viewTable thead');
  const tbody = document.querySelector('#viewTable tbody');
  thead.innerHTML = '';
  tbody.innerHTML = '';
  document.getElementById('viewPager').innerHTML = '';
}

async function loadView(name,page){
  currentView = name; currentPageView = page;
  // clear stale data and show loading
  clearViewArea();
  document.getElementById('viewMeta').innerHTML = `<div class='small text-muted'>Loading ${name}...</div>`;
  const res = await fetch(`${API_BASE_URL}/views/${name}?page=${page}&limit=${limitView}`, {credentials:'same-origin'});
  if(!res.ok){
    let msg = `Failed to load view ${name}`;
    try {
      const err = await res.json();
      if(err && err.error){ msg += `: ${err.error}`; }
    } catch(e) {
      // ignore JSON parse errors
    }
    // ensure stale data is not displayed on error
    clearViewArea();
    document.getElementById('viewMeta').innerHTML = `<div class='alert alert-danger'>${msg}</div>`;
    return;
  }
  const data = await res.json();
  renderView(data);
}

function renderView(data){
  const thead = document.querySelector('#viewTable thead');
  const tbody = document.querySelector('#viewTable tbody');
  thead.innerHTML = '';
  tbody.innerHTML = '';
  if(!data.columns || data.columns.length===0){
    tbody.innerHTML = `<tr><td class='text-muted'>No rows</td></tr>`;
    return;
  }
  thead.innerHTML = `<tr>${data.columns.map(c=>`<th>${c}</th>`).join('')}</tr>`;
  data.records.forEach(row => {
    const tr = document.createElement('tr');
    tr.innerHTML = data.columns.map(c=>`<td>${row[c]!==null?row[c]:''}</td>`).join('');
    tbody.appendChild(tr);
  });
  document.getElementById('viewMeta').innerHTML = `<div class='small text-muted'>View: <strong>${data.view}</strong> | Page ${data.page}/${data.totalPages} | Rows: ${data.total}</div>`;
  renderPager(data.totalPages);
}

function renderPager(total){
  const pager = document.getElementById('viewPager');
  pager.innerHTML='';
  const prev = document.createElement('li');
  prev.className = `page-item ${currentPageView===1?'disabled':''}`;
  prev.innerHTML = `<a class='page-link' href='#'>Prev</a>`;
  prev.onclick = e=>{e.preventDefault(); if(currentPageView>1) loadView(currentView,currentPageView-1);};
  pager.appendChild(prev);
  for(let i=1;i<=total;i++){
    if(i>6 && i<total) { if(i===7){ const dots=document.createElement('li');dots.className='page-item disabled';dots.innerHTML='<span class="page-link">...</span>'; pager.appendChild(dots);} continue; }
    const li = document.createElement('li');
    li.className = `page-item ${i===currentPageView?'active':''}`;
    li.innerHTML = `<a class='page-link' href='#'>${i}</a>`;
    li.onclick = e=>{e.preventDefault(); loadView(currentView,i);};
    pager.appendChild(li);
  }
  const next = document.createElement('li');
  next.className = `page-item ${currentPageView===total?'disabled':''}`;
  next.innerHTML = `<a class='page-link' href='#'>Next</a>`;
  next.onclick = e=>{e.preventDefault(); if(currentPageView<total) loadView(currentView,currentPageView+1);};
  pager.appendChild(next);
}

document.addEventListener('DOMContentLoaded', ()=>{ initViewsMenu(); loadView(VIEWS[0],1); });
