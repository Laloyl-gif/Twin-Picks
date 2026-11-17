/* Outils partagés par l'écran hôte et les téléphones. */
const $ = (s, el = document) => el.querySelector(s);
const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}[c]));
const LETTRES = 'ABCDEFGHIJKL';

async function get(url) { const r = await fetch(url, {cache: 'no-store'}); return r.json(); }
async function post(url, data) {
  const r = await fetch(url, {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(data || {})});
  return r.json();
}
/* Met à jour un élément seulement si sa clé a changé, et sans tout reconstruire : on compare l'ancien et le
   nouveau HTML nœud par nœud (morph). Les éléments déjà affichés restent en place (pas de saccade, pas d'image
   rechargée, pas d'animation rejouée) ; seuls les nouveaux éléments apparaissent avec leur animation.
   data-k="…" : clé d'un élément, pour le retrouver même s'il change de place. */
function maj(el, cle, html, groupe) {
  if (el._cle === cle) return;
  el._cle = cle;
  if (typeof html === 'function') html = html();
  const neuf = groupe !== undefined && el._groupe !== groupe;        // nouvelle manche : on repart de zéro
  el._groupe = groupe;
  if (!el.firstChild || neuf) { el.innerHTML = html; return; }
  const t = document.createElement('template');
  t.innerHTML = html;
  morphEnfants(el, t.content);
}
function memeNoeud(a, b) {
  if (a.nodeType !== b.nodeType || a.nodeName !== b.nodeName) return false;
  return a.nodeType !== 1 || (a.getAttribute('data-k') || '') === (b.getAttribute('data-k') || '');
}
function morphNoeud(a, b) {
  if (a.nodeType !== 1) { if (a.nodeValue !== b.nodeValue) a.nodeValue = b.nodeValue; return; }
  for (const at of Array.from(a.attributes)) if (!b.hasAttribute(at.name)) a.removeAttribute(at.name);
  for (const at of Array.from(b.attributes)) if (a.getAttribute(at.name) !== at.value) a.setAttribute(at.name, at.value);
  if (a.nodeName === 'INPUT' || a.nodeName === 'TEXTAREA' || a.nodeName === 'SELECT') return;
  morphEnfants(a, b);
}
function morphEnfants(vieux, neuf) {
  const cles = new Map();
  for (const n of vieux.childNodes) if (n.nodeType === 1 && n.hasAttribute('data-k')) cles.set(n.getAttribute('data-k'), n);
  const neufs = Array.from(neuf.childNodes);
  neufs.forEach((n, i) => {
    const place = vieux.childNodes[i] || null;
    const k = n.nodeType === 1 && n.getAttribute('data-k');
    let a = k ? cles.get(k) : (place && memeNoeud(place, n) && !(place.nodeType === 1 && place.hasAttribute('data-k')) ? place : null);
    if (a) {
      if (k) cles.delete(k);
      if (a !== place) vieux.insertBefore(a, place);
      morphNoeud(a, n);
    } else {
      vieux.insertBefore(document.importNode(n, true), place);
    }
  });
  while (vieux.childNodes.length > neufs.length) vieux.removeChild(vieux.lastChild);
}
function initiale(nom) { return esc(String(nom || '?').trim().charAt(0).toUpperCase() || '?'); }
const urlAvatar = a => `/persos/avatars/${encodeURIComponent(a)}.jpg`;
/* Rond d'un joueur : sa photo de profil, sinon son initiale. */
function rond(j) {
  return j && j.avatar ? `<i class="av" style="background-image:url('${urlAvatar(j.avatar)}')"></i>` : `<i>${initiale(j && j.nom)}</i>`;
}
function puce(j, extra = '', cls = '') {
  return j ? `<span class="puce ${cls}" style="--c:${j.couleur}">${rond(j)}${esc(j.nom)}${extra}</span>` : '';
}
/* Tout le visuel tient dans la fenêtre, sans barre de défilement : son contenu est enveloppé dans .ajuste, puis
   réduit (zoom) s'il dépasse la place disponible. */
const enveloppe = f => () => `<div class="ajuste" data-k="aj">${typeof f === 'function' ? f() : f}</div>`;
function ajuster(vis, hauteurMax) {
  const a = vis.firstElementChild;
  if (!a || !a.classList.contains('ajuste')) return;
  /* On ne remesure que si le contenu a vraiment changé (nombre d'éléments, texte, images chargées, taille de la zone) :
     remettre le zoom à 1 relancerait les transitions (la bûche de la Log Lady sautait). */
  const imgs = a.getElementsByTagName('img');
  let charges = 0;
  for (const i of imgs) if (i.complete) charges++;
  const sig = [vis.clientWidth, vis.clientHeight, hauteurMax || 0, a.getElementsByTagName('*').length, a.textContent.length,
               imgs.length, charges].join('|');
  if (a._sig === sig) return;
  a._sig = sig;
  a.classList.add('mesure');                                  // .mesure * : pas de transition pendant la mesure
  a.style.zoom = 1;
  const cs = getComputedStyle(vis);
  const H = (hauteurMax || vis.clientHeight) - parseFloat(cs.paddingTop) - parseFloat(cs.paddingBottom);
  const W = vis.clientWidth - parseFloat(cs.paddingLeft) - parseFloat(cs.paddingRight);
  const z = Math.min(1, H / Math.max(1, a.scrollHeight), W / Math.max(1, a.scrollWidth));
  a.style.zoom = z < 0.995 ? Math.max(0.3, z).toFixed(3) : '';
  void a.offsetHeight;
  a.classList.remove('mesure');
  for (const i of imgs) if (!i.complete && !i._aj) { i._aj = 1; i.addEventListener('load', () => ajuster(vis, hauteurMax), {once: true}); }
}
/* Réussi / raté : Cooper (détouré) qui lève le pouce, ou qui laisse tomber son café. */
const COOPER = {ok: '/web/cooper_ok.png', rate: '/web/cooper_rate.png'};
function cooper(ok, cls = '') {
  return `<img class="cooper ${ok ? 'pouce' : 'cafe'} ${cls}" src="${ok ? COOPER.ok : COOPER.rate}" alt="${ok ? 'Réussi' : 'Raté'}">`;
}
/* 138 -> « 2 h 18 min » */
function hmJS(m) { m = Math.round(+m || 0); const h = Math.floor(m / 60), mn = m % 60; return h ? `${h} h ${String(mn).padStart(2, '0')} min` : `${mn} min`; }
function restant(v) { return Math.max(0, (v.duree || 0) - (v.ecoule || 0)); }

/* ---------- emblèmes (dessins au trait, couleur = currentColor) ---------- */
const TRAITS = {
  lil: '<path d="M32 30v26"/><path d="M32 44c-6 0-10-4-10-8 6 0 10 3 10 8zM32 40c6 0 9-3 9-7-6 0-9 3-9 7z"/>' +
       '<path d="M24 20c0-6 4-10 8-10s8 4 8 10-4 10-8 10-8-4-8-10z"/><path d="M28 18c2 3 6 3 8 0M30 22c1 2 3 2 4 0"/>',
  dougie: '<rect x="14" y="16" width="30" height="36" rx="4"/><path d="M18 26h22v14H18z"/><path d="M25.3 26v14M32.6 26v14"/>' +
          '<path d="M50 20v16"/><circle cx="50" cy="18" r="3"/><path d="M44 34h6"/><path d="M20 46h18"/>',
  mrc: '<rect x="16" y="10" width="30" height="44" rx="4"/><path d="M31 20c-6 6-10 10-10 14 0 3 3 5 6 4l3-2-2 8h6l-2-8 3 2c3 1 6-1 6-4 0-4-4-8-10-14z"/>',
  mike: '<path d="M14 18h14a4 4 0 1 1 8 0h14v14a4 4 0 1 0 0 8v14H36a4 4 0 1 0-8 0H14V40a4 4 0 1 1 0-8z"/>',
  pics: '<path d="M4 50 22 19l10 16 10-19 18 34"/><path d="m17 27 5 4 4-3M37 25l5 4 4-3"/><path d="M2 50h60"/>',
  cooper: '<path d="M14 28h30v9a14 14 0 0 1-14 14h-2a14 14 0 0 1-14-14z"/><path d="M44 31h3a5 5 0 0 1 0 10h-4"/>' +
          '<path d="M9 56h40"/><path d="M22 22c-2-3 2-5 0-8M29 22c-2-3 2-5 0-8M36 22c-2-3 2-5 0-8"/>',
  truman: '<circle cx="32" cy="32" r="24"/><path d="M32 15 27.2 23.8 17.3 23.5 22.5 32 17.3 40.5 27.3 40.2 32 49 36.7 40.2 ' +
          '46.7 40.5 41.5 32 46.7 23.5 36.8 23.8Z"/><circle cx="32" cy="32" r="3"/>',
  audrey: '<circle cx="21" cy="45" r="8"/><circle cx="41" cy="47" r="8"/><path d="M21 37c1-9 6-17 13-23M41 39c0-9-3-17-7-25"/>' +
          '<path d="M34 14c5-5 12-6 18-3-4 5-11 6-18 3z"/>',
  cole: '<path d="M22 27a12 12 0 1 1 23 6c-2 4-7 6-7 12a7 7 0 0 1-13 3"/><path d="M29 27a5 5 0 0 1 9 2c0 3-3 4-4 7"/>' +
        '<path d="M52 20c3 3 4 7 4 11s-1 8-4 11M48 24c2 2 2 4 2 7s0 5-2 7"/>',
  diane: '<rect x="7" y="15" width="50" height="34" rx="3"/><rect x="14" y="21" width="36" height="14" rx="2"/>' +
         '<circle cx="24" cy="28" r="4"/><circle cx="40" cy="28" r="4"/><path d="m18 49 3-7h22l3 7"/>',
  bob: '<path d="M32 55c-10 0-16-7-16-15 0-9 7-13 9-22 4 4 5 8 4 13 3-2 5-7 5-12 8 6 14 13 14 21 0 8-7 15-16 15z"/>' +
       '<path d="M32 55c-4 0-7-3-7-7 0-4 3-6 5-10 3 3 8 6 8 11 0 3-2 6-6 6z"/>',
  jacoby: '<circle cx="20" cy="34" r="9" fill="currentColor" fill-opacity=".28"/><circle cx="44" cy="34" r="9"/>' +
          '<path d="M29 33c2-2 4-2 6 0M11 32l-5-5M53 32l5-5"/>',
  laura: '<path d="M32 50C18 41 11 33 11 24a10 10 0 0 1 21-4"/>' +
         '<path d="M32 20a10 10 0 0 1 21 4c0 9-7 17-21 26" stroke-dasharray="2.5 3.5"/><path d="m32 20-3 7 4 5-4 6 3 6-0 6"/>',
  janey: '<path d="M18 22c0-6 6-9 14-9s14 3 14 9v16c0 9-6 16-14 16s-14-7-14-16z"/><path d="m18 22-4-8 9 4M46 22l4-8-9 4"/>' +
         '<circle cx="25" cy="29" r="6"/><circle cx="39" cy="29" r="6"/><circle cx="25" cy="29" r="1.6" fill="currentColor"/>' +
         '<circle cx="39" cy="29" r="1.6" fill="currentColor"/><path d="m29.5 37 2.5 4 2.5-4z"/><path d="m25 46 3.5 2 3.5-2 3.5 2 3.5-2"/>',
  norma: '<path d="M8 38h48l-4 12H12z"/><path d="M8 38c2-12 12-18 24-18s22 6 24 18"/><path d="M20 30l6 6M32 26v10M44 30l-6 6"/>' +
         '<circle cx="24" cy="16" r="2.5" fill="currentColor"/><path d="M24 13c1-4 4-6 7-6"/>',
  shelly: '<path d="M12 26h34v12a14 14 0 0 1-14 14h-6a14 14 0 0 1-14-14z"/><path d="M46 30h4a5 5 0 0 1 0 10h-5"/>' +
          '<path d="M8 56h44"/><path d="M22 20c-2-3 2-5 0-8M32 20c-2-3 2-5 0-8"/>',
  leland: '<circle cx="32" cy="32" r="24"/><circle cx="23" cy="26" r="2.5" fill="currentColor"/><circle cx="41" cy="26" r="2.5" fill="currentColor"/>' +
          '<path d="M17 36c5 9 25 9 30 0"/><path d="M21 38c4 4 18 4 22 0"/>',
  lucy: '<path d="M14 44c-4-8-2-20 6-26l6 8-4 6c2 6 6 10 12 12l6-4 8 6c-6 8-18 10-26 6z"/><path d="M40 10a14 14 0 0 1 14 14M40 18a6 6 0 0 1 6 6"/>',
  donna: '<rect x="10" y="10" width="44" height="44" rx="3"/><path d="M32 10v44M10 32h44"/><path d="m17 21 4 4 7-8M39 43l4 4 7-8"/>' +
         '<circle cx="43" cy="21" r="4"/>',
  bobby: '<path d="M32 8l6 13 14 2-10 10 2 14-12-7-12 7 2-14-10-10 14-2z"/><path d="M14 56h36M20 50h24"/>',
  manfrom: '<path d="M10 8v30M18 8v30M46 8v30M54 8v30"/><path d="M6 8h52"/>' +
           '<path d="M6 46l6 6 6-6 6 6 6-6 6 6 6-6 6 6 6-6 6 6"/><path d="M6 56l6-6 6 6 6-6 6 6 6-6 6 6 6-6 6 6 6-6"/>' +
           '<circle cx="32" cy="22" r="6"/><path d="M26 38c0-6 3-9 6-9s6 3 6 9"/>',
  pete: '<path d="M8 32c8-10 22-12 34-6l10-8v28l-10-8c-12 6-26 4-34-6z"/><circle cx="18" cy="30" r="1.8" fill="currentColor"/>' +
        '<path d="M28 26c2 4 2 8 0 12"/>',
  briggs: '<path d="M14 6h36v52H14z"/><path d="M10 6v52M54 6v52" stroke-dasharray="2 4"/>' +
          '<path d="M20 16h18M20 24h24M20 32h14M20 40h22M20 48h10"/>',
  nadine: '<path d="M6 12h52"/><circle cx="6" cy="12" r="2.5"/><circle cx="58" cy="12" r="2.5"/>' +
          '<path d="M12 12v40c4-2 6 0 8 0V12M24 12v40c3-2 5 0 7 0V12M42 12v40c3-2 5 0 7 0V12"/><path d="M50 12v40"/>' +
          '<circle cx="14" cy="12" r="1.8"/><circle cx="26" cy="12" r="1.8"/><circle cx="44" cy="12" r="1.8"/>',
  hawk: '<path d="M44 6C30 12 20 26 18 44l-4 14"/><path d="M44 6c-2 14-10 28-26 38"/>' +
        '<path d="M40 14l-8 2M37 20l-9 2M33 27l-9 1M28 33l-8 1M36 13l-1 9M31 19l-1 10M26 26l-1 9"/>',
  andy: '<path d="M12 10h30v30H12z"/><path d="M34 40l8-8"/><path d="M18 18h18M18 24h14M18 30h10"/>' +
        '<path d="M44 26l12 12-18 18-6 2 2-6z"/><path d="M40 30l12 12"/>',
  ben: '<path d="M8 38l40-14 6 4-40 14z"/><path d="M48 24l6 4"/><path d="M10 42c-3 1-4 4-2 6"/>' +
       '<path d="M52 20c2-4 0-7 3-10M57 22c2-4 0-7 3-10"/>',
  josie: '<rect x="10" y="14" width="44" height="36" rx="2"/><path d="M32 14v36"/>' +
         '<path d="M16 22h10M16 28h10M16 34h10M38 22h10M38 28h10M38 34h8"/><circle cx="32" cy="56" r="3"/><path d="M32 50v3"/>',
  maddy: '<circle cx="20" cy="34" r="10"/><circle cx="44" cy="34" r="10"/><path d="M30 33c1-2 3-2 4 0M10 30 6 24M54 30l4-6"/>' +
         '<path d="M14 18c4-8 32-8 36 0M12 22c-2 8-4 22 0 32M52 22c2 8 4 22 0 32"/>',
  james: '<rect x="8" y="14" width="48" height="32" rx="3"/><circle cx="22" cy="30" r="5"/><circle cx="42" cy="30" r="5"/>' +
         '<path d="M27 30h10M14 20h36M18 46l4-6h20l4 6"/><path d="M44 52c4-2 8 0 10-4"/>',
  ed: '<rect x="14" y="16" width="24" height="40" rx="3"/><rect x="18" y="21" width="16" height="10" rx="1"/>' +
      '<path d="M38 26h6c4 0 6 3 6 6v14c0 3 3 4 5 2V22l-5-6"/><path d="M10 56h32"/><path d="M22 40h8"/>',
  albert: '<circle cx="32" cy="26" r="7"/><path d="M32 33v23"/><path d="M32 19c-4-6-12-6-14 0 6 0 10 2 14 7 4-5 8-7 14-7-2-6-10-6-14 0z"/>' +
          '<path d="M32 44c-5 0-9-3-10-7M32 48c5 0 9-3 10-7"/>',
};
function embleme(cle, cls = '') {
  return `<svg class="embleme ${cls}" viewBox="0 0 64 64" fill="none" stroke="currentColor" stroke-width="1.6" ` +
    `stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${TRAITS[cle] || TRAITS.pics}</svg>`;
}
/* Portrait d'un jeu : image de web/persos/ si elle existe, sinon l'emblème (en petit : l'avatar du personnage). */
function portrait(cle, persos, cls = '') {
  const img = cls === 'mini' && (persos || {})[cle] ? urlAvatar(cle) : (persos || {})[cle];
  return `<div class="portrait ${cls}">${img ? `<img src="${esc(img)}" alt="">` : embleme(cle)}</div>`;
}
function logo(persos) {
  const img = (persos || {}).logo || (persos || {}).cooper;
  return `<div class="logo">${img ? `<img class="logo-perso" src="${esc(img)}" alt="">` : embleme('pics', 'logo-pics')}` +
    '<span>Twin <b>Picks</b></span></div>';
}

/* ---------- visuels des manches ---------- */
/* Indices : le premier arrive avec une petite animation (il « monte ») ; les suivants s'ajoutent à la suite,
   sans que les précédents bougent (voir .indice dans style.css). */
/* Indices et titre à trous : leur place est réservée dès le début de la manche (rien ne saute quand ils arrivent). */
function indicesHTML(e) {
  if (!('indices' in e)) return '';
  const l = e.indices || [];
  return `<div class="indices${l.length ? '' : ' vide'}" data-k="indices">${l.map((i, k) =>
    `<span class="indice${k ? ' suivant' : ''}" data-k="i${k}">${esc(i)}</span>`).join('')}</div>`;
}
function trousHTML(e) {
  if (!('trous' in e)) return '';
  return `<div class="trous${e.trous ? '' : ' vide'}" data-k="trous">${e.trous ? esc(e.trous).replace(/_/g, '<i></i>') : '&nbsp;'}</div>`;
}
function cassette(joue) {
  return `<div class="cassette${joue ? ' joue' : ''}"><div class="k-etiquette"><span></span><span></span></div>` +
    '<div class="k-fenetre"><i class="bobine"></i><i class="bande"></i><i class="bobine"></i></div><div class="k-bas"></div></div>';
}

const LEGENDES_TRUMAN = ['Pièce n° 1 — à vérifier', 'Ghostwood ? 22 h 40', 'Le témoin dit vrai ?', 'Vu près de la scierie',
                         'Qui ? Pourquoi ?', 'Voir avec Hawk'];
/* Visuel d'une manche : identique sur tous les écrans. */
function visuelHTML(v, opt = {}) {
  const src = i => `/img/${v.seq}/${i}${opt.q || ''}`, e = v.etat || {};
  if (v.vue === 'choix') return v.jeu === 'josie' ? josieHTML(v, src, opt) : choixHTML(v, src, opt);
  if (v.vue === 'ben') return benHTML(v, src, opt);
  if (v.vue === 'ed') return jaugeHTML(e, src, v.moteur || {}, v.phase === 'reponse') + indicesHTML(e);
  if (v.vue === 'note') {
    return `<div class="note-film" data-k="film"><img src="${src(e.img)}" alt=""><div><b>${esc(e.titre)}</b>` +
      `<small>${esc(e.genres || '')}</small></div></div>` + indicesHTML(e);
  }
  if (v.vue === 'chrono') {
    const mo = v.moteur || {}, c = mo.contrainte || e.contrainte;
    if (v.jeu === 'lucy') return lucyHTML(c);
    return `<div class="contrainte" data-k="c${mo.ci || 0}"><small>Condition</small><b>${esc(c)}</b></div>`;
  }
  if (v.vue === 'buche') return bucheHTML(v, src) + (v.phase === 'reponse' ? '' : indicesHTML(e));
  if (v.vue === 'duels') return duelsHTML(v, src, opt);
  if (v.vue === 'noeud') return noeudHTML(v, src) + (v.phase === 'reponse' ? '' : trousHTML(e) + indicesHTML(e));
  if (v.phase === 'reponse') return v.revelation ? `<img class="scene-img" src="${src('r')}" alt="">` : '';
  if (v.vue === 'image') {
    const img = `<img class="scene-img" src="${src(e.img)}" alt="">`;
    return v.jeu === 'affiche' ? preuveHTML(img) : img;
  }
  if (v.vue === 'videe') {
    return `<img class="scene-img affiche-videe" data-k="img" src="${src(e.img)}" alt="">` + trousHTML(e) + indicesHTML(e);
  }
  if (v.vue === 'miroir') return sosieHTML(e, src) + trousHTML(e) + indicesHTML(e);
  if (v.vue === 'tracklist') return tracklistHTML(e, src) + trousHTML(e) + indicesHTML(e);
  if (v.vue === 'geant') return geantHTML(e) + trousHTML(e);
  if (v.vue === 'titres') return titresHTML(e) + trousHTML(e);
  if (v.vue === 'identite') return identiteHTML(e);
  if (v.vue === 'complices') return complicesHTML(e, src) + trousHTML(e);
  if (v.vue === 'rebus') return rebusHTML(e) + trousHTML(e) + indicesHTML(e);
  if (v.vue === 'dominos') return dominosHTML(e, src) + trousHTML(e) + indicesHTML(e);
  if (v.vue === 'jackpot') return jackpotHTML(e, src) + trousHTML(e) + indicesHTML(e);
  if (v.vue === 'coordonnees') return coordonneesHTML(e) + trousHTML(e) + indicesHTML(e);
  if (v.vue === 'caravane') return caravaneHTML(e, src) + trousHTML(e) + indicesHTML(e);
  if (v.vue === 'briggs') return briggsHTML(e) + trousHTML(e) + indicesHTML(e);
  if (v.vue === 'pages') return pagesHTML(e) + trousHTML(e) + indicesHTML(e);
  if (v.vue === 'frise') return friseHTML(v, src, opt);
  if (v.vue === 'croquis') return croquisHTML(e, src) + trousHTML(e) + indicesHTML(e);
  if (v.vue === 'couleurs') {
    return `<div class="loge" data-k="loge"><span class="rideau g"></span><img class="scene-img couleurs-img" data-k="img" src="${src(e.img)}" alt="">` +
      '<span class="rideau d"></span><span class="loge-sol"></span></div>' +
      `<p class="sous-titre">${esc(citation('couleurs')[0])}</p>` + trousHTML(e) + indicesHTML(e);
  }
  if (v.vue === 'plans') {
    /* Truman's Files : chaque plan est une photo punaisée ; un fil rouge se tend d'une punaise à la suivante */
    const vus = e.plans || [], total = e.total || 3;
    let h = '';
    for (let i = 0; i < total; i++) {
      h += vus.includes(i)
        ? `<figure class="plan${i === vus.length - 1 ? ' apparait' : ''}" data-k="p${i}" style="--rot:${[-2, 1.5, -.8, 2, -1.4, .9][i % 6]}deg;--i:${i}">` +
          `<img src="${src(i)}" alt=""><figcaption>${LEGENDES_TRUMAN[i % LEGENDES_TRUMAN.length]}</figcaption></figure>`
        : `<figure class="plan vide" data-k="p${i}"><div></div></figure>`;
    }
    const x = i => (100 * (i % 3) / 3 + 100 / 6).toFixed(2), y = i => (Math.floor(i / 3) * 100 / Math.ceil(total / 3)).toFixed(2);
    let fils = '';
    for (let i = 1; i < vus.length; i++) {
      const a = i - 1, mx = (+x(a) + +x(i)) / 2, my = Math.max(+y(a), +y(i)) + 7;
      fils += `<path data-k="f${i}" class="${i === vus.length - 1 ? 'trace' : ''}" pathLength="1" d="M${x(a)} ${y(a)}Q${mx} ${my} ${x(i)} ${y(i)}"/>`;
    }
    return `<div class="tableau" data-k="tableau"><div class="plans"><svg class="fils" viewBox="0 0 100 100" ` +
      `preserveAspectRatio="none" aria-hidden="true">${fils}</svg>${h}</div></div>`;
  }
  if (v.vue === 'grille') {
    const cartes = e.cartes || [], total = e.total || cartes.length;
    const cols = Math.max(1, Math.min(opt.cols || 5, total > 5 ? Math.ceil(total / 2) : total));
    const cellules = [];
    for (let i = 0; i < total; i++) {
      const c = cartes[i];
      cellules.push(c ? `<div class="carte-img${i === cartes.length - 1 ? ' apparait' : ''}"><img src="${src(c.img)}" alt="">` +
               `<span>${esc(c.txt)}${c.sous ? `<em class="apparait">${esc(c.sous)}</em>` : ''}</span></div>`
             : '<div class="carte-img vide"><div class="ph"></div><span></span></div>');
    }
    if (v.jeu === 'filmo') return journalHTML(cellules, total) + trousHTML(e) + indicesHTML(e);
    if (v.jeu === 'casting') return audreyHTML(cellules, cols) + trousHTML(e) + indicesHTML(e);
    return `<div class="grille" data-k="grille" style="--cols:${cols}">${cellules.join('')}</div>` + trousHTML(e) + indicesHTML(e);
  }
  if (v.vue === 'noms') {
    const noms = (e.noms || []).map(n => typeof n === 'string' ? {n} : n);
    let h = '';
    for (let i = 0; i < (e.total || noms.length); i++) {
      const p = noms[i];
      h += p ? `<li class="apparait"><span>${i + 1}</span><div>${esc(p.n)}${p.sous ? `<em class="apparait">${esc(p.sous)}</em>` : ''}</div></li>`
             : `<li class="vide"><span>${i + 1}</span></li>`;
    }
    return `<ol class="noms" data-k="noms">${h}</ol>` + trousHTML(e) + indicesHTML(e);
  }
  if (v.vue === 'anagramme') {
    const mots = e.mots || [], n = Math.max(1, ...mots.map(m => m.length));
    const t = Math.max(16, Math.min(opt.tuile || 64, Math.floor((opt.largeur || 600) / n) - 6));
    const ana = `<div class="ana" style="--t:${t}px">` + mots.map(m =>
      `<div class="mot">${m.map(l => `<div class="tuile${l.ok ? ' ok' : ''}">${esc(l.c)}</div>`).join('')}</div>`).join('') +
      '</div>';
    return (v.jeu === 'anagramme' ? coleHTML(ana) : ana) + indicesHTML(e);
  }
  if (v.vue === 'texte') {
    return `<div class="synopsis">${esc(e.texte).replace(/▒+/g, m => `<span class="masque">${m}</span>`)}</div>` + indicesHTML(e);
  }
  if (v.vue === 'cassette') {
    const img = e.img !== undefined ? `<img class="blind-affiche apparait" src="${src(e.img)}" alt="">` : '';
    return `<div class="blind">${cassette(!v.pause && !v.main)}${img}</div>` + trousHTML(e) + indicesHTML(e);
  }
  if (v.vue === 'fiche') return ficheHTML(e);
  if (v.vue === 'bingo') return bingoHTML(e, (e.cases || []).map(c => ({txt: c})));
  return '';
}

/* Major Briggs' Deep Space Monitor Printouts : un vrai relevé qui s'imprime petit à petit. Papier listing (bandes
   vertes, perforations d'entraînement), caractères d'imprimante matricielle ; entre deux éléments, du code binaire
   comme sur le relevé de la série. Chaque nouvel élément fait avancer le papier puis s'imprime lettre à lettre ;
   les lignes déjà imprimées ne bougent plus (data-k + morph). */
function binaire(graine, n) {
  let x = (graine * 2654435761) >>> 0, out = '';
  for (let i = 0; i < n; i++) {
    x ^= x << 13; x >>>= 0; x ^= x >>> 17; x ^= x << 5; x >>>= 0;
    out += (i && i % 8 === 0 ? ' ' : '') + (x & 1);
  }
  return out;
}
function briggsHTML(e) {
  const mots = e.mots || [], cats = e.cats || [], total = Math.max(e.total || 0, mots.length);
  let h = `<div class="imp-ligne imp-tete" data-k="t0">DEEP SPACE MONITOR — PRINTOUT</div>` +
    `<div class="imp-ligne imp-tete" data-k="t1">STATION ${esc(e.station || '7-238')} · RELEVÉ EN COURS</div>` +
    `<div class="imp-ligne bin" data-k="t2">${binaire(7, 48)}</div>`;
  mots.forEach((m, i) => {
    const txt = String(m).toUpperCase(), cat = cats[i] ? `${esc(cats[i])} ▸ ` : '';
    h += `<div class="imp-ligne bin avance" data-k="b${i}">${binaire(i * 31 + 3, 40)}</div>` +
      `<div class="imp-ligne mot avance" data-k="m${i}"><span class="imp-num">${String(i + 1).padStart(2, '0')}</span>` +
      `<span class="imp-txt" style="--n:${(cat.length ? cats[i].length + 3 : 0) + txt.length}">${cat}${esc(txt)}</span></div>`;
  });
  if (mots.length && mots.length === total) h += `<div class="imp-ligne bin avance" data-k="fin">${binaire(99, 48)}</div>`;
  return `<div class="imprimante" data-k="imprimante"><div class="papier" data-k="papier">${h}</div>` +
    `<div class="imp-fente" data-k="fente"><span>${mots.length} / ${total}</span></div></div>`;
}

/* Hawk's Missing Pages : le slogan de l'affiche réapparaît mot à mot sur des pages de journal déchirées. */
function pagesHTML(e) {
  const mots = e.mots || [], longs = e.longs || [], masques = e.masques || [];
  const h = mots.map((m, i) => m
    ? `<span class="mot-page vu${masques[i] ? ' masque' : ''}" data-k="w${i}">${esc(m)}</span>`
    : `<span class="mot-page cache" data-k="w${i}" style="--l:${longs[i] || 4}"></span>`).join(' ');
  return `<div class="pages-hawk" data-k="pages"><span class="hk-plume">${OBJ.plume}</span><div class="page-dechiree"><small>Pages retrouvées${e.langue === 'en' ? ' · en anglais' : ''}</small>` +
    `<p>${h}</p></div></div>`;
}

/* Andy's Police Sketch : le portrait-robot, posé sur la feuille d'Andy, avec ses post-it (de vraies répliques). */
const NOTES_ANDY = [['À montrer au shérif Truman', ''], ['Lucy ♥', 'A.']];
function croquisHTML(e, src) {
  return `<div class="croquis-cadre" data-k="croquis"><div class="croquis-feuille">` +
    `<img class="croquis-img" data-k="img" src="${src(e.img)}" alt=""><div class="croquis-signe">A. Brennan</div></div>` +
    NOTES_ANDY.map(([t, s], i) => `<span class="postit p${i}">${esc(t)}${s ? `<small>${esc(s)}</small>` : ''}</span>`).join('') + '</div>';
}

/* Nadine's Silent Drape Runners : les affiches pendent à une tringle ; à la réponse, elles glissent sans bruit à
   leur place (du plus ancien au plus récent). Pendant la manche, opt.cellule(i) rend les affiches touchables. */
function friseHTML(v, src, opt = {}) {
  const e = v.etat || {}, items = e.items || [], n = items.length, mo = v.moteur || {};
  const rev = v.phase === 'reponse' && mo.ordre;
  const annees = rev ? mo.annees : null;
  const drapes = items.map((it, i) => {
    const x = rev ? mo.ordre.indexOf(i) : (opt.place ? opt.place(i) : i);
    const c = opt.cellule ? opt.cellule(i) || {} : {};
    const an = annees ? annees[i] : (e.annees || {})[String(i)];
    return `<figure class="drape ${c.cls || ''}" data-i="${i}" data-k="p${i}" style="--x:${x};--d:${x}">` +
      `<span class="anneau"></span><span class="crochet"></span>` +
      `<div class="toile"><img src="${src(it.img)}" alt="">${c.badge ? `<b class="badge-ordre">${c.badge}</b>` : ''}</div>` +
      `<figcaption>${esc(it.txt)}</figcaption><em class="annee ${an ? 'vue' : ''}">${an ? esc(an) : '&nbsp;'}</em></figure>`;
  }).join('');
  return `<div class="frise${rev ? ' revelee' : ''}" style="--n:${n}" data-k="frise"><div class="tringle"><i></i><i></i></div>` +
    `<div class="drapes"><figure class="drape gabarit" data-k="gab" aria-hidden="true"><span class="anneau"></span>` +
    `<span class="crochet"></span><div class="toile"><div class="vide23"></div></div><figcaption>&nbsp;<br>&nbsp;</figcaption>` +
    `<em class="annee">&nbsp;</em></figure>${drapes}</div>${rev ? '' : `<p class="frise-aide">Du plus ancien au plus récent</p>`}</div>` +
    (rev ? '' : indicesHTML(e));
}

/* Shelly's Cherry Pie : la moyenne des notes en parts de cherry pie (10 parts = 10/10), l'étendue en dessous. */
const virgule = x => String(x).replace('.', ',');
function tarteMoyenne(m) {
  const f = Math.max(0, Math.min(1, (m || 0) / 10)), a = 2 * Math.PI * f - Math.PI / 2;
  const x = (100 + 84 * Math.cos(a)).toFixed(1), y = (100 + 84 * Math.sin(a)).toFixed(1);
  const part = f >= 0.999 ? '<circle cx="100" cy="100" r="84"/>' : f <= 0 ? '' : `<path d="M100 100L100 16A84 84 0 ${f > 0.5 ? 1 : 0} 1 ${x} ${y}z"/>`;
  const traits = Array.from({length: 10}, (_, i) => {
    const b = 2 * Math.PI * i / 10 - Math.PI / 2;
    return `<path d="M100 100L${(100 + 92 * Math.cos(b)).toFixed(1)} ${(100 + 92 * Math.sin(b)).toFixed(1)}"/>`;
  }).join('');
  return `<svg class="tarte-moy" viewBox="0 0 200 200" aria-hidden="true"><defs><clipPath id="tm-c">${part}</clipPath>` +
    '<radialGradient id="tm-f" cx=".5" cy=".5" r=".55"><stop offset="0" stop-color="#b3121f"/><stop offset="1" stop-color="#6d0711"/></radialGradient></defs>' +
    '<circle cx="100" cy="100" r="98" fill="#efe9de"/><circle cx="100" cy="100" r="86" fill="#e2dccf"/>' +
    '<g clip-path="url(#tm-c)"><circle cx="100" cy="100" r="88" fill="#c8843b"/><circle cx="100" cy="100" r="78" fill="url(#tm-f)"/>' +
    '<g stroke="#ecb46a" stroke-width="7" stroke-linecap="round"><path d="M40 60l120 80M30 100l110 74M70 30l110 74M60 170l80-140M30 130l80-110M100 180l70-120"/></g>' +
    '<circle cx="100" cy="100" r="82" fill="none" stroke="#e0a457" stroke-width="9"/></g>' +
    `<g stroke="#00000033" stroke-width="1.5">${traits}</g></svg>`;
}
function ficheHTML(e) {
  const j = e.jauge || {};
  const sous = j.nb > 1
    ? (j.ecart ? `${j.nb} notes, de ${j.min} à ${j.max} · ${j.ecart} point${j.ecart > 1 ? 's' : ''} d'écart`
               : `${j.nb} notes identiques : tout le monde est d'accord`)
    : 'une seule note';
  const ind = (e.indices || []).map((x, i) => `<li class="apparait" data-k="f${i}">${esc(x)}</li>`).join('');
  return `<div class="fiche" data-k="fiche"><div class="jauge">${tarteMoyenne(j.moyenne)}<div class="j-txt"><small>Moyenne des joueurs</small>` +
    `<b>${virgule(j.moyenne ?? '?')}<span>/10</span></b><p>${sous}</p></div></div>` +
    `<ol class="fiche-indices" data-k="find">${ind}</ol>${trousHTML(e)}</div>`;
}

/* Grille de bingo. cases : [{txt, film, valeur, relances}] ; e : {taille, mode, lignes, colonnes, rel_l, rel_c}.
   opt.cellule(i) -> {cls, html} pour les téléphones ; en mode « lignes », les conditions sont en en-têtes.
   opt.changer : les en-têtes se touchent pour changer la condition (data-changer="l0" / "c1"). */
function bingoHTML(e, cases, opt = {}) {
  const n = e.taille || Math.round(Math.sqrt(cases.length)) || 2, lignes = e.mode === 'lignes';
  const tete = (sens, i, txt) => {
    const rel = ((sens === 'l' ? e.rel_l : e.rel_c) || [])[i] || 0;
    const ch = opt.changer ? ` data-changer="${sens}${i}" title="Toucher pour changer cette condition"` : '';
    return `<div class="b-tete ${sens === 'l' ? 'lig' : 'col'}${opt.changer ? ' changeable' : ''}${rel ? ' changee' : ''}" data-k="${sens}${i}"${ch}>` +
      `<span>${esc(txt || '')}</span>${opt.changer ? '<i class="b-chg">↻</i>' : ''}</div>`;
  };
  let h = '';
  if (lignes) h += '<div class="b-coin"></div>' + (e.colonnes || []).map((c, i) => tete('c', i, c)).join('');
  for (let r = 0; r < n; r++) {
    if (lignes) h += tete('l', r, (e.lignes || [])[r]);
    for (let c = 0; c < n; c++) {
      const i = r * n + c, x = cases[i] || {}, cell = opt.cellule ? opt.cellule(i, x) || {} : {};
      const film = x.film ? `<b class="b-film">${esc(x.film)}</b>` : '';
      h += `<div class="bcase ${x.film ? 'remplie' : ''} ${cell.cls || ''}" data-case="${i}" data-k="b${i}">` +
        (x.txt ? `<span class="b-cond">${esc(x.txt)}</span>` : '') + film + (cell.html || '') + '</div>';
    }
  }
  return `<div class="bingo n${n} ${lignes ? 'lignes' : 'cases'} ${opt.cls || ''}" style="--n:${n}">${h}</div>`;
}

/* Choix d'une image parmi plusieurs (Leland : l'intrus ; Bobby : le mieux noté). Pendant la manche, cellule(i)
   rend les cases touchables (téléphone) ; à la réponse : la bonne case, les infos et les votes. */
function choixHTML(v, src, opt = {}) {
  const e = v.etat || {}, items = e.items || [], rev = v.phase === 'reponse' && v.choix;
  const cols = opt.colsChoix || (items.length <= 4 ? items.length : 3);
  const tete = rev && opt.sansSolution ? '' : rev ? `<h2 class="cbanniere" data-k="tete">${esc(v.solution || '')}</h2>` +
    `<p class="csous" data-k="sous">${esc(v.detail || '')}</p>`
    : `<h2 class="cbanniere" data-k="tete">${esc(e.question || '')}</h2><p class="csous" data-k="sous">` +
      `${e.question_petit ? `« ${esc(e.question_petit)} »` : '&nbsp;'}</p>`;
  const casesL = items.map((it, i) => {
    const c = opt.cellule ? opt.cellule(i) || {} : {};
    let cls = (e.personnes ? 'personne ' : '') + (c.cls || ''),
      dessous = `<em class="${it.sous ? 'note-indice apparait' : 'vide'}">${it.sous ? esc(it.sous) : '&nbsp;'}</em>`;
    if (rev) {
      const ok = i === v.choix.bonne, votes = (v.choix.votes || {})[i] || [];
      cls += ok ? ' bonne' : ' terne';
      dessous = `<em class="${ok ? 'ok' : ''}">${esc((v.choix.infos || [])[i] || '')}</em>` +
        (votes.length && !opt.sansVotes ? `<div class="votes">${votes.map(j => puce(j, '', j.ok ? 'juste' : 'faux')).join('')}</div>` : '');
    }
    const texte = it.img === undefined || it.img === null;
    if (texte) cls += ' texte';
    if (it.barre && !rev) cls += ' barre';
    return `<div class="cfilm ${cls}" data-i="${i}"><b class="badge">${rev && i === v.choix.bonne ? cooper(true, 'mini') : c.badge || ''}</b>` +
      (texte ? '' : `<img src="${src(it.img)}" alt="">`) + `<span>${esc(it.txt)}</span>${dessous}</div>`;
  });
  let colsVues = cols;
  if (v.jeu === 'maddy' && casesL.length >= 2) {        // Maddy : ses grosses lunettes, au milieu des personnages
    casesL.splice(Math.floor(casesL.length / 2), 0, `<div class="maddy-lunettes" aria-hidden="true">${OBJ.grosses_lunettes}</div>`);
    if (cols >= casesL.length - 1) colsVues = cols + 1;
  }
  const cases = casesL.join('');
  const imgSeul = e.film && v.jeu === 'mike' && rev ? src('r') : e.film ? src(e.film.img) : '';     // Mike : l'affiche entière
  const seul = e.film ? `<div class="film-seul" data-k="film"><img src="${imgSeul}" alt=""><div><b>${esc(e.film.txt)}</b>` +
    (e.film.sous ? `<small>${esc(e.film.sous)}</small>` : '') + '</div></div>' : '';
  if (e.robe) {                                                        // Lil : la robe et les dix affiches
    return tete + `<div class="lil-jeu" data-k="lil">${robeHTML(e)}<div class="cgrille choix" data-k="grille" style="--cols:5">${cases}</div></div>`;
  }
  if (v.jeu === 'leland') {               // Leland : le portrait de Laura (reine du lycée), sa carte d'avocat, les films à côté
    return `<div class="palmer" data-k="palmer"><figure class="pa-portrait"><div class="pa-cadre"><img src="/web/laura_bal.jpg" alt=""></div>` +
      `<span class="pa-carte">${OBJ.carte_leland}</span></figure><div class="pa-droite">${tete}` +
      `<div class="cgrille choix" data-k="grille" style="--cols:${cols}">${cases}</div>${rev ? '' : indicesHTML(e)}</div></div>`;
  }
  if (v.jeu === 'bobby') {                // Bobby (saison 3) : la capsule du major Briggs, bien en vue, puis les films
    return `<div class="bureau-bobby" data-k="bureau"><div class="bb-capsule">${OBJ.capsule}</div>` + tete +
      `<div class="cgrille choix" data-k="grille" style="--cols:${cols}">${cases}</div></div>` + (rev ? '' : indicesHTML(e));
  }
  return tete + seul + (e.paire ? paireHTML(e, src) : '') +
    `<div class="cgrille choix${items.length && items[0].img === undefined ? ' textes' : ''}" data-k="grille" style="--cols:${colsVues}">${cases}</div>` +
    (rev ? '' : indicesHTML(e));
}
/* Albert : les deux films à relier (et, en indice, un troisième qui partage le même lien). */
function paireHTML(e, src) {
  const film = (f, cls) => `<figure class="${cls}"><img src="${src(f.img)}" alt=""><figcaption>${esc(f.txt)}</figcaption></figure>`;
  const [a, b] = e.paire;
  return `<div class="paire" data-k="paire">${film(a, 'p-film')}<div class="p-lien">${ROSE_BLEUE}</div>${film(b, 'p-film')}` +
    (e.tiers ? `<div class="p-tiers apparait" data-k="tiers"><small>Même lien</small>${film(e.tiers, 'p-film petit')}</div>` : '') +
    '</div>';
}

/* Révélation pas à pas (Complicité en devinettes croisées, Norma) : une ligne par joueur, toutes les `pas` s. */
function etapesRevelation(v, n, pas) {
  return Math.min(n, Math.floor((v.rev_t || 0) / (pas || 3.5)) + 1);
}

/* Grille des films de Complicité. cellule(i) -> {cls, style, badge, dessous} */
function grilleFilms(films, src, cellule, cols) {
  return `<div class="cgrille" style="--cols:${cols}">` + films.map((f, i) => {
    const c = cellule(i) || {};
    return `<div class="cfilm ${c.cls || ''}" data-i="${i}" style="${c.style || ''}"><b class="badge">${c.badge || ''}</b>` +
      `<img src="${src(f.img)}" alt=""><span>${esc(f.txt)}</span>${c.dessous || ''}</div>`;
  }).join('') + '</div>';
}

/* Révélation d'un film de Complicité : de qui c'est le préféré, qui l'a proposé (juste / faux). */
function celluleRevelation(c, i) {
  const r = c.resultats || {};
  if (!r.films) return {};
  const f = r.films[i], fav = f.favori_de;
  const votes = f.votes.map(v => puce(v,
    (c.mode === 'tous' && v.cible ? ' → ' + esc(v.cible.nom) : '') + (v.ok && v.gain ? ` <em>+${v.gain}</em>` : ''),
    v.ok ? 'juste' : 'faux')).join('');
  return {cls: fav.length ? 'favori' : 'terne', style: fav.length ? `--c:${fav[0].couleur}` : '',
          badge: fav.length ? fav.map(j => esc(j.nom)).join(', ') : '',
          dessous: votes ? `<div class="votes">${votes}</div>` : ''};
}
