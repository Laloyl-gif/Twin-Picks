/* Écran hôte Twin Picks : salon (jeux, listes, réglages, joueurs) puis affichage de la partie. */
const K = new URLSearchParams(location.search).get('k') || sessionStorage.getItem('k') || '';
if (K) sessionStorage.setItem('k', K);
const Q = '?k=' + encodeURIComponent(K);
/* ?tel=1 : l'écran hôte dans le panneau du téléphone administrateur (application Android) */
const TEL = new URLSearchParams(location.search).has('tel');
if (TEL) document.body.classList.add('tel');
const PRESETS = [['Facile', 2, 3], ['Normal', 3, 5], ['Difficile', 4, 7], ['Extrême', 6, 10]];
let CFG = null, E = {}, onglet = 'general', jeuListes = null, jetonTMDB = '', arret = false;
const R = () => CFG.reglages;
const action = (a, extra) => post('/api/hote/action' + Q, Object.assign({action: a}, extra || {}));

function interdit() {
  arret = true;
  document.body.innerHTML = '<div class="message">Clé de l\'écran hôte invalide.<br>' +
    '<small class="doux">Utilisez l\'adresse affichée dans la console.</small></div>';
}

/* ================= configuration ================= */
async function chargerConfig() {
  const c = await get('/api/hote/config' + Q);
  if (c.interdit) return interdit();
  CFG = c;
  dessinerConfig();
}
async function regler(partiel) {
  const c = await post('/api/hote/reglages' + Q, partiel);
  if (c.erreur) return alert(c.erreur);
  CFG = c;
  dessinerConfig();
}
function dessinerConfig() {
  if (!CFG) return;
  maj($('#logo'), JSON.stringify(CFG.persos), logo(CFG.persos));
  dessinerJeux();
  dessinerModes();
  if ($('#d-reglages').open) dessinerReglages();
  if ($('#d-listes').open) dessinerListes();
  if ($('#d-profils').open) dessinerProfils();
}

/* ---------- cartes des jeux ---------- */
const profilsActifs = () => R().profils_auto ? (E.profils_actifs || []) : [];
/* Sous la carte d'un jeu choisi : d'où viennent les films (rien de plus, sauf s'il y a un problème). */
function sourceJeu(g, d) {
  const actifs = profilsActifs();
  if (d.profils) {
    const n = (E.profils_actifs || []).length;
    return n >= d.profils ? `<button class="lien" data-profils="1">${n} profil${n > 1 ? 's' : ''}</button>`
      : `<button class="lien alerte" data-profils="1">${d.profils} profil${d.profils > 1 ? 's' : ''} requis</button>`;
  }
  if (!d.listes) return '';
  if (actifs.length) {
    const plus = (R().listes[g].plus || []).length;
    return `<button class="lien" data-listes="${g}" title="Films vus par ${actifs.map(esc).join(', ')}">` +
      `Films vus${plus ? ` + ${plus} liste${plus > 1 ? 's' : ''}` : ''}</button>`;
  }
  const s = R().listes[g];
  if (!s.inc.length) return `<button class="lien alerte" data-listes="${g}">Aucune liste</button>`;
  const connues = Object.fromEntries(R().listes_connues.map(l => [l.id, l]));
  const noms = s.inc.map(id => (connues[id] || {}).nom || id).join(', ');
  return `<button class="lien" data-listes="${g}" title="${esc(noms)}">${s.inc.length} liste${s.inc.length > 1 ? 's' : ''}</button>`;
}
function dessinerJeux() {
  const jeux = R().jeux;
  let total = 0, nbOn = 0;
  $('#jeux').innerHTML = Object.entries(CFG.jeux).map(([g, d]) => {
    const on = jeux[g].on, n = jeux[g].n;
    if (on) { total += n; nbOn++; }
    const source = sourceJeu(g, d);
    const bas = on && R().hasard ? `<div class="jeu-bas"><span class="jeu-source${TEL && !source.includes('alerte') ? ' discrete' : ''}">${source}</span></div>`
      : on ? `<div class="jeu-bas"><span class="jeu-source${TEL && !source.includes('alerte') ? ' discrete' : ''}">${source}` +
        `${g === 'pete' ? '<button class="lien prep" id="prep-pete" data-affiches="1"></button>' : ''}</span>` +
        `<div class="pas"><button data-pas="-1" title="Moins de manches">−</button><span>${n}</span>` +
        `<button data-pas="1" title="Plus de manches">+</button></div></div>` : '';
    // Menu : en grand le nom Twin Peaks (figé, voir CONSIGNES.md), en petit le nom technique du jeu.
    return `<div class="jeu ${on ? 'on' : ''}" data-g="${g}" title="${esc(d.nom + ' — ' + d.regle)}">${portrait(d.perso, CFG.persos)}
      <button class="jeu-image" data-image="1" title="Changer l'image de la carte">${OBJ_IMAGE}</button>
      <div class="jeu-txt"><small>${esc(d.nom)}</small><b>${esc(d.titre || d.nom)}</b></div>${bas}</div>`;
  }).join('');
  if (R().hasard) total = nbOn ? R().hasard_n : 0;
  $('#b-lancer').innerHTML = `Lancer <small>${total} manche${total > 1 ? 's' : ''}${R().hasard && nbOn ? ' au hasard' : ''}</small>`;
  $('#jeux-compte').textContent = `${nbOn} / ${Object.keys(CFG.jeux).length}`;
  paginerJeux();
  afficherPrep(true);
}

/* ---------- menu : TOUJOURS 3 cartes par ligne (figé, voir CONSIGNES.md), réparties en pages ----------
   Le nombre de lignes par page dépend de la hauteur disponible : les cartes gardent une forme d'affiche de cinéma
   large (≈ 16:9) et ne sont jamais coupées. On change de page avec les flèches, les points, la molette ou ←/→. */
const MENU_COLONNES = 3;
let pageJeux = 0;
function paginerJeux() {
  const cadre = $('#jeux-cadre'), grille = $('#jeux'), cartes = Array.from(grille.children);
  if (!cartes.length || !cadre.clientWidth) return;
  if (TEL) {                         // téléphone administrateur : toutes les cartes, sur deux colonnes, qui défilent
    cartes.forEach(c => { c.hidden = false; });
    $('#jeux-pages').hidden = true;
    $('#jeux-pages').dataset.pages = 1;
    return;
  }
  const gap = 12, larg = (cadre.clientWidth - gap * (MENU_COLONNES - 1)) / MENU_COLONNES;
  const ideal = larg * 0.5, H = cadre.clientHeight;
  let lignes = Math.max(1, Math.floor((H + gap) / (ideal * 0.82 + gap)));
  lignes = Math.min(lignes, Math.ceil(cartes.length / MENU_COLONNES));
  const haut = Math.floor((H - gap * (lignes - 1)) / lignes);
  const parPage = lignes * MENU_COLONNES, pages = Math.max(1, Math.ceil(cartes.length / parPage));
  pageJeux = Math.max(0, Math.min(pageJeux, pages - 1));
  grille.style.setProperty('--lignes', lignes);
  grille.style.setProperty('--haut', Math.min(haut, Math.round(larg * 0.62)) + 'px');
  cartes.forEach((c, i) => { c.hidden = Math.floor(i / parPage) !== pageJeux; });
  const nav = $('#jeux-pages');
  nav.hidden = pages < 2;
  nav.innerHTML = pages < 2 ? '' : `<button class="lien" data-page="${pageJeux - 1}" ${pageJeux ? '' : 'disabled'} title="Page précédente">‹</button>` +
    Array.from({length: pages}, (_, p) => `<button class="point ${p === pageJeux ? 'actif' : ''}" data-page="${p}" title="Page ${p + 1}"></button>`).join('') +
    `<button class="lien" data-page="${pageJeux + 1}" ${pageJeux < pages - 1 ? '' : 'disabled'} title="Page suivante">›</button>`;
  nav.dataset.pages = pages;
}
function allerPage(p) {
  const pages = Number($('#jeux-pages').dataset.pages || 1);
  const n = Math.max(0, Math.min(pages - 1, p));
  if (n !== pageJeux) { pageJeux = n; paginerJeux(); }
}
$('#jeux-pages').onclick = ev => { const b = ev.target.closest('[data-page]'); if (b && !b.disabled) allerPage(Number(b.dataset.page)); };
let molette = 0;
$('#jeux-cadre').addEventListener('wheel', ev => {
  if (TEL) return;
  ev.preventDefault();
  if (Date.now() - molette < 450 || Math.abs(ev.deltaY) < 8) return;
  molette = Date.now();
  allerPage(pageJeux + (ev.deltaY > 0 ? 1 : -1));
}, {passive: false});
let toucheX = null;
$('#jeux-cadre').addEventListener('touchstart', ev => { toucheX = ev.touches[0].clientX; }, {passive: true});
$('#jeux-cadre').addEventListener('touchend', ev => {
  if (toucheX === null) return;
  const dx = ev.changedTouches[0].clientX - toucheX;
  toucheX = null;
  if (Math.abs(dx) > 50 && !TEL) allerPage(pageJeux + (dx < 0 ? 1 : -1));
});
window.addEventListener('resize', () => { if (CFG && E.phase === 'lobby') paginerJeux(); });

/* ---------- affiches vidées (préparation en arrière-plan) ---------- */
let OUTILS_AFFICHES = null;
const affichesEtat = () => E.affiches || {};
function textePrep() {
  const a = affichesEtat();
  if (a.actif) return [`Affiches ${a.prets ?? 0}/${a.voulu || '…'}`, 'encours'];
  if (a.erreur) return ['Affiches ⚠', 'erreur'];
  if (a.prets !== null && a.prets !== undefined) return [`${a.prets} affiche${a.prets > 1 ? 's' : ''}`, ''];
  return ['', ''];
}
function afficherPrep(force) {
  const el = $('#prep-pete');
  if (el) {
    const [html, cls] = textePrep();
    if (force || el.innerHTML !== html) { el.innerHTML = html; el.className = 'lien prep ' + cls; }
    el.title = [affichesEtat().message, affichesEtat().etape].filter(Boolean).join(' — ') || 'Affiches vidées';
  }
  if ($('#d-reglages').open && onglet === 'pete') maj($('#bloc-affiches'), JSON.stringify([affichesEtat(), OUTILS_AFFICHES]), blocAffiches());
}
async function clicAffiches(action) {
  const a = action || null;
  if (!a) return ouvrirReglages('pete');
  const r = await post('/api/hote/affiches' + Q, {action: a});
  if (r.erreur) alert(r.erreur);
  if (r.etat) E.affiches = r.etat;
  if (r.outils) OUTILS_AFFICHES = r.outils;
  afficherPrep(true);
}
function blocAffiches() {
  const a = affichesEtat(), o = OUTILS_AFFICHES;
  const ligneOutil = (nom, liste, conseil) => `<div><span class="doux">${nom}</span> ${liste && liste.length ? esc(liste.join(', '))
    : '<span class="manque">aucun</span>'}${conseil && (!liste || !liste.length || liste[0] === 'opencv') ? ` <span class="doux">· ${conseil}</span>` : ''}</div>`;
  const outils = o ? `<div class="outils">${ligneOutil('Textes', o.texte, 'pip install rapidocr_onnxruntime')}` +
    `${ligneOutil('Personnages et sujets', o.personnages, 'pip install rembg')}${ligneOutil('Reconstruction', o.reconstruction)}</div>` : '';
  const pct = a.voulu ? Math.round(100 * (a.prets || 0) / a.voulu) : 0;
  return `<div class="ligne"><b>Affiches</b><span class="doux">${a.prets === null || a.prets === undefined ? '' : `${a.prets} prête${a.prets > 1 ? 's' : ''}`}${a.voulu ? ` sur ${a.voulu}` : ''}` +
    `${a.echecs ? ` · ${a.echecs} échec${a.echecs > 1 ? 's' : ''}` : ''}</span><span class="espace"></span>` +
    (a.actif ? '<button class="discret petit" data-aff="arreter">Arrêter</button>'
      : '<button class="primaire petit" data-aff="preparer">Préparer maintenant</button>') + '</div>' +
    (a.voulu ? `<div class="jauge-prep"><i style="width:${pct}%"></i></div>` : '') +
    `<div class="doux">${esc(a.message || 'Aucune préparation lancée depuis le démarrage.')}${a.etape ? ` — ${esc(a.etape)}` : ''}</div>` +
    (a.erreur ? `<div class="manque">${esc(a.erreur)}</div>` : '') + outils + (a.dossier ? `<code>${esc(a.dossier)}</code>` : '');
}
$('.raccourcis').onclick = ev => {
  const b = ev.target.closest('[data-tous]');
  if (!b) return;
  const on = b.dataset.tous === '1';
  regler({jeux: Object.fromEntries(Object.keys(CFG.jeux).map((g, i) => [g, {on: on || (!on && i === 0)}]))});
};
$('#jeux').onclick = ev => {
  const carte = ev.target.closest('.jeu');
  if (!carte) return;
  const g = carte.dataset.g, j = R().jeux[g];
  const pas = ev.target.closest('[data-pas]'), lst = ev.target.closest('[data-listes]');
  if (pas) return regler({jeux: {[g]: {n: j.n + Number(pas.dataset.pas)}}});
  if (lst) return ouvrirListes(g);
  if (ev.target.closest('[data-affiches]')) return clicAffiches();
  if (ev.target.closest('[data-profils]')) return ouvrirProfils();
  if (ev.target.closest('[data-image]')) return ouvrirImage(g);
  if (ev.target.closest('.jeu-bas')) return;
  regler({jeux: {[g]: {on: !j.on}}});
};

function dessinerModes() {
  $('#modes').innerHTML = Object.entries(CFG.modes)
    .map(([m, t]) => `<button class="${R().reponse === m ? 'actif' : ''}" data-m="${m}">${t}</button>`).join('');
  // Manches : le nombre de chaque jeu, ou des jeux au hasard parmi ceux choisis (juste un nombre de manches)
  const h = R().hasard;
  $('#tirage').innerHTML = `<button class="${h ? '' : 'actif'}" data-h="0">Par jeu</button><button class="${h ? 'actif' : ''}" data-h="1">Au hasard</button>` +
    (h ? `<span class="pas hasard-n"><button data-hn="-1" title="Moins de manches">−</button><span>${R().hasard_n}</span><button data-hn="1" title="Plus de manches">+</button></span>` : '');
}
$('#tirage').onclick = ev => {
  const b = ev.target.closest('[data-h]'), n = ev.target.closest('[data-hn]');
  if (b) regler({hasard: b.dataset.h === '1'});
  if (n) regler({hasard_n: Math.max(1, Math.min(200, R().hasard_n + Number(n.dataset.hn) * (ev.shiftKey ? 5 : 1)))});
};
$('#modes').onclick = ev => { const b = ev.target.closest('[data-m]'); if (b) regler({reponse: b.dataset.m}); };

/* ---------- réglages ---------- */
function ouvrirReglages(g) { onglet = g || onglet; dessinerReglages(); $('#d-reglages').showModal(); }
/* Réglages généraux rangés en rubriques. */
const RUBRIQUES = [['Partie', c => !/^(musique|profils_|sagas|films_uniques|realisateurs_)/.test(c)],
                   ['Films et profils', c => /^(profils_|sagas|films_uniques|realisateurs_)/.test(c)],
                   ['Musique', c => c.startsWith('musique')]];
function saisieChamp(p) {
  const v = R()[p.cle], id = 'p-' + p.cle;
  if (p.type === 'bool') {
    return `<label class="bascule"><input type="checkbox" id="${id}" data-cle="${p.cle}" ${v ? 'checked' : ''}><span></span></label>`;
  }
  if (p.type === 'choix') {
    return `<select id="${id}" data-cle="${p.cle}">${Object.entries(p.choix)
      .map(([k, t]) => `<option value="${k}" ${k === v ? 'selected' : ''}>${esc(t)}</option>`).join('')}</select>`;
  }
  if (p.type === 'joueur') {
    const noms = (E.classement || []).map(j => j.nom);
    if (v && !noms.includes(v)) noms.unshift(v);
    return `<select id="${id}" data-cle="${p.cle}"><option value="">— choisir un joueur —</option>${noms
      .map(n => `<option ${n === v ? 'selected' : ''}>${esc(n)}</option>`).join('')}</select>`;
  }
  if (p.type === 'texte') {
    return `<input type="text" id="${id}" data-cle="${p.cle}" value="${esc(v)}" spellcheck="false"` +
      ` placeholder="${esc(p.placeholder || 'ex. D:\\Films ou /mnt/nas/films')}">`;
  }
  return `<input type="number" id="${id}" data-cle="${p.cle}" value="${v}" min="${p.min}" max="${p.max}" step="${p.pas}" title="${p.min} – ${p.max}">`;
}
function champ(p) {
  const aide = p.aide ? `<small class="aide">${esc(p.aide)}</small>` : '';
  return `<div class="champ ${p.type}"><label for="p-${p.cle}">${esc(p.label)}${aide}</label><div>${saisieChamp(p)}</div></div>`;
}
function chips(titre, params) {
  return `<div class="bloc-chips"><h4>${esc(titre)}</h4><div class="chips">${params.map(p =>
    `<label class="chip-bascule"><input type="checkbox" data-cle="${p.cle}" ${R()[p.cle] ? 'checked' : ''}><span>${esc(p.label)}</span></label>`).join('')}</div></div>`;
}
function dessinerReglages() {
  const jeux = R().jeux;
  $('#r-onglets').innerHTML = Object.entries(CFG.groupes).map(([g, n]) => {
    const d = CFG.jeux[g];
    return `<button class="${g === onglet ? 'actif' : ''} ${d && !jeux[g].on ? 'eteint' : ''}" data-g="${g}">` +
      (d ? portrait(d.perso, CFG.persos, 'mini') : embleme('pics', 'mini')) + `<span>${esc(n)}</span></button>`;
  }).join('');
  const params = CFG.params.filter(p => p.groupe === onglet);
  let html = '';
  if (onglet === 'general') {
    html = `<div class="r-tete"><h3>Général</h3></div>` + `<h4 class="rubrique">TMDB</h4>` +
      `<div class="champ"><label for="p-api">Clé API TMDB (v3) ou jeton v4</label><div>` +
      `<input type="password" id="p-api" data-cle="api_key" value="${esc(R().api_key)}"></div></div>` +
      RUBRIQUES.map(([t, ok]) => { const l = params.filter(p => ok(p.cle)); return l.length ? `<h4 class="rubrique">${t}</h4>` + l.map(champ).join('') : ''; }).join('');
  } else {
    const d = CFG.jeux[onglet];
    html = `<div class="r-tete">${portrait(d.perso, CFG.persos, 'mini')}<div><small>${esc(d.qui)}</small><h3>${esc(d.nom)}</h3>` +
      `<p class="doux">${esc(d.regle)}</p></div></div>` + params.filter(p => !p.bloc).map(champ).join('');
    const blocs = [...new Set(params.filter(p => p.bloc).map(p => p.bloc))];
    html += blocs.map(b => chips(b, params.filter(p => p.bloc === b))).join('');
  }
  if (onglet === 'affiche') {
    html += `<div class="presets"><span class="doux">Difficulté</span>${PRESETS
      .map(([n, e, p]) => `<button data-preset="${e},${p}">${n}</button>`).join('')}</div>`;
  }
  if (onglet === 'pete') {
    html += '<div id="bloc-affiches" class="bloc-affiches"></div>';
    if (!OUTILS_AFFICHES) clicAffiches('outils');
  }
  $('#r-champs').innerHTML = html;
  if (onglet === 'pete') afficherPrep(true);
}
$('#r-onglets').onclick = ev => { const b = ev.target.closest('[data-g]'); if (b) { onglet = b.dataset.g; dessinerReglages(); $('#r-champs').scrollTop = 0; } };
$('#r-champs').onchange = ev => {
  const el = ev.target, cle = el.dataset.cle;
  if (cle) regler({[cle]: el.type === 'checkbox' ? el.checked : el.value});
};
$('#r-champs').onclick = ev => {
  const aff = ev.target.closest('[data-aff]');
  if (aff) return clicAffiches(aff.dataset.aff);
  const b = ev.target.closest('[data-preset]');
  if (!b) return;
  const [e, p] = b.dataset.preset.split(',').map(Number);
  regler({aff_effets: e, aff_puissance: p});
};

/* ---------- listes TMDB ---------- */
const jeuxAvecListes = () => Object.keys(CFG.jeux).filter(g => CFG.jeux[g].listes);
function ouvrirListes(g) {
  jeuListes = g || jeuListes || jeuxAvecListes()[0];
  $('#l-filtre').value = '';
  dessinerListes();
  $('#d-listes').showModal();
}
function dessinerListes() {
  const actifs = profilsActifs(), presents = E.profils_presents || [], cle = actifs.length ? 'plus' : 'inc';
  $('#l-jeux').innerHTML = jeuxAvecListes().map(g => {
    const n = (R().listes[g][cle] || []).length;
    return `<button class="${g === jeuListes ? 'actif' : ''} ${R().jeux[g].on ? '' : 'eteint'}" data-g="${g}">` +
      `${portrait(CFG.jeux[g].perso, CFG.persos, 'mini')}<span>${esc(CFG.jeux[g].nom)}</span>` +
      `<small class="${n || actifs.length ? '' : 'alerte'}">${actifs.length ? (n ? '∩ + ' + n : '∩') : n}</small></button>`;
  }).join('');
  $('#l-compte').innerHTML = CFG.compte
    ? `<span>Compte <b>${esc(CFG.compte)}</b></span><button class="discret petit" data-a="actualiser">Actualiser</button>
       <button class="discret petit" data-a="deconnecter">Déconnecter</button>`
    : jetonTMDB
      ? `<span>Validez (Approve) sur TMDB, puis</span><button class="primaire petit" data-a="session">Continuer</button>`
      : `<button class="discret petit" data-a="token">Connecter mon compte TMDB</button>`;
  // Profils présents : la source « films vus en commun » (l'intersection), qu'on peut couper ; les listes incluses
  // s'y ajoutent alors (listes[g].plus), les listes exclues restent exclues.
  $('#l-commun').hidden = !presents.length;
  if (presents.length) {
    const qui = presents.map(esc).join(presents.length > 1 ? ' ∩ ' : '');
    $('#l-commun').innerHTML = `<label class="commun-bascule${actifs.length ? ' on' : ''}"><input type="checkbox" data-commun ${actifs.length ? 'checked' : ''}>` +
      `<span class="cb-rond"></span><span><b>${presents.length > 1 ? 'Films vus en commun' : 'Films vus'}</b> <small>${qui}</small></span></label>` +
      `<p class="aide">${actifs.length ? (presents.length > 1 ? 'L\'intersection des films vus' : 'Les films vus') +
        ', plus les listes incluses ci-dessous (pour ce jeu).' : 'Désactivé : seules les listes incluses comptent.'}</p>`;
  }
  const sel = R().listes[jeuListes], filtre = $('#l-filtre').value.trim().toLowerCase(), inc = sel[cle] || [];
  const lignes = R().listes_connues
    .filter(l => !filtre || l.nom.toLowerCase().includes(filtre) || String(l.id) === filtre)
    .sort((a, b) => (a.id > 0) - (b.id > 0) || a.nom.localeCompare(b.nom));
  $('#l-lignes').innerHTML = lignes.map(l => {
    const etat = inc.includes(l.id) ? 'inc' : sel.exc.includes(l.id) ? 'exc' : '';
    const bouton = (e, t) => `<button data-e="${e}" class="${etat === e ? 'actif' : ''}">${t}</button>`;
    return `<div class="ligne-liste ${etat}"><div><b>${esc(l.nom)}</b>${l.nb ? `<small>${l.nb} titres</small>` : ''}</div>
      <div class="tri" data-id="${l.id}">${bouton('inc', actifs.length ? 'Ajouter' : 'Inclure')}${bouton('exc', 'Exclure')}${bouton('', '–')}</div></div>`;
  }).join('') || '<p class="doux centre">Aucune liste</p>';
  $('#l-resume').textContent = (actifs.length ? `Films vus${inc.length ? ` + ${inc.length} liste${inc.length > 1 ? 's' : ''}` : ''}`
    : `${inc.length} incluse${inc.length > 1 ? 's' : ''}`) +
    (sel.exc.length ? ` · ${sel.exc.length} exclue${sel.exc.length > 1 ? 's' : ''}` : '');
}
$('#l-jeux').onclick = ev => { const b = ev.target.closest('[data-g]'); if (b) { jeuListes = b.dataset.g; dessinerListes(); } };
$('#l-filtre').oninput = dessinerListes;
$('#l-lignes').onclick = ev => {
  const b = ev.target.closest('[data-e]');
  if (!b) return;
  const id = Number(b.closest('.tri').dataset.id), s = R().listes[jeuListes], cle = profilsActifs().length ? 'plus' : 'inc';
  const inc = (s[cle] || []).filter(x => x !== id), exc = s.exc.filter(x => x !== id);
  if (b.dataset.e === 'inc') inc.push(id);
  if (b.dataset.e === 'exc') exc.push(id);
  regler({listes: {[jeuListes]: {[cle]: inc, exc}}});
};
$('#l-commun').onchange = ev => { if (ev.target.matches('[data-commun]')) regler({profils_auto: ev.target.checked}); };
$('#d-listes footer').onclick = ev => {
  const b = ev.target.closest('[data-tout]');
  if (!b) return;
  const s = R().listes[jeuListes], cle = profilsActifs().length ? 'plus' : 'inc';
  if (b.dataset.tout === 'copier') {
    regler({listes: Object.fromEntries(jeuxAvecListes().map(g => [g, {inc: [...s.inc], exc: [...s.exc], plus: [...(s.plus || [])]}]))});
  } else if (b.dataset.tout === 'inc') {
    regler({listes: {[jeuListes]: {[cle]: R().listes_connues.filter(l => l.id > 0).map(l => l.id), exc: []}}});
  } else {
    regler({listes: {[jeuListes]: {[cle]: [], exc: []}}});
  }
};
$('#l-compte').onclick = async ev => {
  const a = ev.target.closest('[data-a]')?.dataset.a;
  if (!a) return;
  if (a === 'token') {
    const fenetre = window.open('', '_blank');            // ouverte tout de suite : évite le bloqueur de pop-up
    const r = await post('/api/hote/tmdb' + Q, {action: 'token'});
    if (r.erreur) { if (fenetre) fenetre.close(); return alert(r.erreur); }
    jetonTMDB = r.token;
    if (fenetre) fenetre.location = r.url; else window.open(r.url, '_blank');
    return dessinerListes();
  }
  const r = await post('/api/hote/tmdb' + Q, {action: a, token: jetonTMDB});
  jetonTMDB = '';
  if (r.erreur) alert('TMDB : ' + r.erreur); else CFG = r;
  dessinerConfig();
};
async function ajouterListe() {
  const texte = $('#l-ajout').value.trim();
  if (!texte) return;
  const r = await post('/api/hote/tmdb' + Q, {action: 'ajouter', texte, jeu: jeuListes, plus: profilsActifs().length > 0});
  if (r.erreur) return alert(r.erreur);
  CFG = r;
  $('#l-ajout').value = '';
  dessinerConfig();
}
$('#l-ajouter').onclick = ajouterListe;
$('#l-ajout').onkeydown = ev => { if (ev.key === 'Enter') ajouterListe(); };

/* ---------- profils ---------- */
let PROFILS = null, realsOuvert = null;
/* Réalisateurs connus d'un profil : null = tous ceux de realisateurs.txt. */
function realsDe(p) { const tous = CFG.realisateurs || []; return p.realisateurs === null || p.realisateurs === undefined ? tous.slice() : p.realisateurs.filter(n => tous.includes(n)); }
function blocReals(p) {
  const tous = CFG.realisateurs || [], connus = realsDe(p), ouvert = realsOuvert === p.id;
  if (!tous.length) return '<div class="pc-reals"><span class="doux">Réalisateurs connus</span> <span class="manque">realisateurs.txt introuvable (Réglages › Général)</span></div>';
  const resume = connus.length === tous.length ? `tous (${tous.length})` : `${connus.length} / ${tous.length}`;
  let h = `<div class="pc-reals"><span class="doux">Réalisateurs connus</span> <b>${resume}</b>` +
    `<button class="lien" data-pa="reals">${ouvert ? 'Fermer' : 'Choisir…'}</button></div>`;
  if (ouvert) {
    h += `<div class="reals-panneau"><p class="aide">Chrono et Bingo ne poseront de conditions « réalisateur » que sur les noms cochés.</p>` +
      `<div class="reals-outils"><button class="lien" data-reals="tous">Tous</button><button class="lien" data-reals="aucun">Aucun</button></div>` +
      `<div class="chips">${tous.map(n => `<label class="chip-bascule"><input type="checkbox" data-real="${esc(n)}" ${connus.includes(n) ? 'checked' : ''}><span>${esc(n)}</span></label>`).join('')}</div></div>`;
  }
  return h;
}
async function ouvrirProfils() {
  $('#pr-msg').textContent = '';
  PROFILS = CFG.profils;
  dessinerProfils();
  $('#d-profils').showModal();
}
function dessinerProfils() {
  PROFILS = PROFILS || CFG.profils || [];
  const connues = R().listes_connues.slice().sort((a, b) => (a.id > 0) - (b.id > 0) || a.nom.localeCompare(b.nom));
  const avatars = CFG.avatars || [];
  $('#pr-liste').innerHTML = PROFILS.map(p => {
    const ids = p.listes.map(l => l.id);
    const options = connues.filter(l => !ids.includes(l.id)).map(l => `<option value="${l.id}">${esc(l.nom)}</option>`).join('');
    const stats = p.nb_films ? `${p.nb_films} films · ${p.nb_notes} notes${p.moyenne ? ` · moyenne ${String(p.moyenne).replace('.', ',')}` : ''}` +
      (p.source ? ` · ${esc(p.source)}${p.importe ? ` (${esc(p.importe)})` : ''}` : '') : 'Aucune note importée';
    return `<div class="pcarte" data-id="${esc(p.id)}">
      <div class="pc-tete">
        <span class="pc-avatar">${p.avatar ? `<i class="av" style="background-image:url('${urlAvatar(p.avatar)}')"></i>` : `<i>${initiale(p.nom)}</i>`}</span>
        <div class="pc-nom"><b>${esc(p.nom)}</b><small>${stats}</small></div>
        <select data-pa="avatar" title="Photo proposée au joueur"><option value="">Photo…</option>${avatars
          .map(a => `<option value="${esc(a)}" ${a === p.avatar ? 'selected' : ''}>${esc(a)}</option>`).join('')}</select>
        <button class="discret petit" data-pa="renommer">Renommer</button>
        <button class="lien danger" data-pa="supprimer">Supprimer</button>
      </div>
      <div class="pc-listes"><span class="doux">Listes</span>
        ${p.listes.map(l => `<span class="chip">${esc(l.nom)}${l.nb ? ` <small>${l.nb}</small>` : ''}<button data-retirer="${l.id}" title="Retirer">×</button></span>`).join('')}
        ${p.manquantes.map(n => `<span class="chip manquante" title="Liste introuvable : connectez votre compte TMDB (bouton Listes) ou ajoutez-la">${esc(n)} ?</span>`).join('')}
        <select data-pa="ajouter-liste"><option value="">+ liste…</option>${options}</select>
      </div>
      ${blocReals(p)}
      <div class="pc-import">
        <label class="fichier discret petit">Importer des notes (IMDb, TMDB, Letterboxd, Refract)<input type="file" data-import accept=".csv,.zip,.json,.txt"></label>
        ${p.nb_films ? '<button class="lien" data-pa="vider">Vider les notes</button>' : ''}
      </div>
    </div>`;
  }).join('') || '<p class="doux centre">Aucun profil</p>';
}
async function actionProfil(data, msg) {
  $('#pr-msg').textContent = msg || '';
  const r = await post('/api/hote/profils' + Q, data);
  if (r.erreur) { $('#pr-msg').textContent = r.erreur; return; }
  PROFILS = CFG.profils = r.profils;
  $('#pr-msg').textContent = r.msg || '';
  dessinerProfils();
  dessinerJeux();
}
const lireFichier = f => new Promise((ok, ko) => { const l = new FileReader(); l.onload = () => ok(l.result); l.onerror = ko; l.readAsDataURL(f); });
$('#pr-liste').onchange = async ev => {
  const carte = ev.target.closest('.pcarte');
  if (!carte) return;
  const id = carte.dataset.id, p = PROFILS.find(x => x.id === id), a = ev.target.dataset.pa;
  if (a === 'avatar') return actionProfil({action: 'avatar', id, avatar: ev.target.value});
  if (ev.target.matches('[data-real]')) {
    const nom = ev.target.dataset.real, connus = realsDe(p).filter(n => n !== nom);
    if (ev.target.checked) connus.push(nom);
    const tous = CFG.realisateurs || [];
    return actionProfil({action: 'realisateurs', id, realisateurs: connus.length === tous.length ? null : connus});
  }
  if (a === 'ajouter-liste' && ev.target.value) {
    return actionProfil({action: 'listes', id, listes: [...p.listes.map(l => l.id), Number(ev.target.value)]});
  }
  if (ev.target.matches('[data-import]') && ev.target.files[0]) {
    const f = ev.target.files[0];
    return actionProfil({action: 'importer', id, nom_fichier: f.name, data: await lireFichier(f)},
                        `Import de ${f.name}… (les films sans identifiant TMDB sont cherchés un par un)`);
  }
};
$('#pr-liste').onclick = ev => {
  const carte = ev.target.closest('.pcarte');
  if (!carte) return;
  const id = carte.dataset.id, p = PROFILS.find(x => x.id === id);
  const ret = ev.target.closest('[data-retirer]');
  if (ret) return actionProfil({action: 'listes', id, listes: p.listes.map(l => l.id).filter(x => x !== Number(ret.dataset.retirer))});
  const rb = ev.target.closest('[data-reals]');
  if (rb) return actionProfil({action: 'realisateurs', id, realisateurs: rb.dataset.reals === 'tous' ? null : []});
  const a = ev.target.closest('button[data-pa]')?.dataset.pa;
  if (a === 'reals') { realsOuvert = realsOuvert === id ? null : id; return dessinerProfils(); }
  if (a === 'supprimer' && confirm(`Supprimer le profil ${p.nom} ?`)) actionProfil({action: 'supprimer', id});
  if (a === 'vider' && confirm(`Effacer les notes importées de ${p.nom} ?`)) actionProfil({action: 'vider', id});
  if (a === 'renommer') {
    const nom = prompt('Nouveau nom (= pseudo du joueur) :', p.nom);
    if (nom && nom.trim()) actionProfil({action: 'renommer', id, nom});
  }
};
$('#pr-fichier').onchange = () => { const f = $('#pr-fichier').files[0]; $('#pr-fichier-nom').textContent = f ? f.name : 'Fichier de notes (facultatif)'; };
$('#pr-ajouter').onclick = async () => {
  const nom = $('#pr-nom').value.trim();
  if (!nom) return $('#pr-nom').focus();
  const f = $('#pr-fichier').files[0];
  const data = {action: 'ajouter', nom};
  if (f) Object.assign(data, {nom_fichier: f.name, data: await lireFichier(f)});
  await actionProfil(data, f ? `Création de ${nom} et import de ${f.name}…` : '');
  if (!$('#pr-msg').textContent.startsWith('Le profil')) { $('#pr-nom').value = ''; $('#pr-fichier').value = ''; $('#pr-fichier').onchange(); }
};
$('#b-profils').onclick = ouvrirProfils;
$('#b-historique').onclick = async () => {           // les dernières parties : joueurs, manches, films
  const r = await (await fetch('/api/hote/historique' + Q)).json();
  const ps = r.parties || [];
  $('#hi-corps').innerHTML = ps.length ? ps.map((p, k) => `<details class="hi-partie"${k ? '' : ' open'}><summary><b>${esc(p.date || '')}</b>` +
    `${p.inachevee ? ' <small>(interrompue)</small>' : ''} · ${(p.joueurs || []).map((j, i) => `<span style="color:${j.couleur}">${i ? '' : '🏆 '}${esc(j.nom)} ${j.score}</span>`).join(' · ')}</summary>` +
    `<ol>${(p.manches || []).map(m => `<li><b>${esc(m.jeu)}</b> — ${esc(m.solution)}${m.detail ? ` <small>${esc(m.detail).slice(0, 90)}</small>` : ''}` +
      ` <span class="${m.gagnants.length ? 'ok' : 'doux'}">${m.gagnants.length ? '✓ ' + m.gagnants.map(esc).join(', ') : 'personne'}</span></li>`).join('')}</ol></details>`).join('')
    : '<p class="aide">Aucune partie enregistrée pour l\'instant.</p>';
  $('#d-historique').showModal();
};
$('#b-palmares').onclick = async () => {               // le palmarès à vie, toutes parties confondues
  const r = await (await fetch('/api/hote/palmares' + Q)).json();
  const js = r.joueurs || [];
  $('#pa-corps').innerHTML = js.length ? `<p class="aide">${r.parties} partie${r.parties > 1 ? 's' : ''} terminée${r.parties > 1 ? 's' : ''}` +
    `${r.derniere ? ` · la dernière le ${esc(r.derniere)}` : ''}</p><table class="palmares"><thead><tr><th></th><th>Joueur</th><th>Victoires</th><th>Parties</th>` +
    `<th>Points</th><th>Moyenne</th><th>Record</th><th>Manches gagnées</th><th>Série</th><th>Jeu fétiche</th></tr></thead><tbody>` +
    js.map((j, k) => `<tr><td>${k < 3 ? ['🥇', '🥈', '🥉'][k] : k + 1}</td><td><b>${esc(j.nom)}</b></td><td>${j.victoires}</td><td>${j.parties}</td>` +
      `<td>${j.points}</td><td>${j.moyenne}</td><td>${j.record}</td><td>${j.manches}</td><td>${j.serie}</td><td>${esc(j.jeu)}</td></tr>`).join('') + '</tbody></table>'
    : '<p class="aide">Aucune partie terminée pour l\'instant : le palmarès se remplit à la fin de chaque partie.</p>';
  $('#d-palmares').showModal();
};

document.querySelectorAll('[data-fermer]').forEach(b => { b.onclick = () => b.closest('dialog').close(); });
$('#b-reglages').onclick = () => ouvrirReglages();
$('#b-listes').onclick = () => ouvrirListes();

/* ================= salon ================= */
$('#b-lancer').onclick = async () => {
  $('#erreur').textContent = '';
  const r = await action('lancer');
  if (r.erreur) $('#erreur').textContent = r.erreur;
};
$('#b-tunnel').onclick = () => action('tunnel');
$('#qr').onerror = () => { $('#qr').hidden = true; $('#qr-aide').hidden = false; };
$('#liste-joueurs').onclick = ev => {
  const b = ev.target.closest('[data-id]');
  if (b && confirm('Retirer ce joueur de la partie ?')) action('exclure', {id: b.dataset.id});
};

function rendreLobby() {
  const url = E.url || '';
  if ($('#url').textContent !== url) {
    $('#url').textContent = url;
    $('#qr').hidden = false;
    $('#qr-aide').hidden = true;
    $('#qr').src = '/qr.png' + Q + '&u=' + encodeURIComponent(url);
  }
  const t = E.tunnel || '';
  maj($('#code-partie'), [E.code, E.en_ligne, t].join('|'), E.code ? `<small>Code de la partie</small><b>${esc(E.code)}</b>` +
    `<span class="${E.en_ligne ? 'ok' : ''}">${E.en_ligne ? '● Joignable aussi par Internet' : t === 'connexion' ? 'Ouverture sur Internet…' : 'Sur ce Wi-Fi'}</span>` : '');
  $('#b-tunnel').textContent = t === 'connexion' ? 'Connexion…' : E.en_ligne ? 'Fermer l\'accès Internet' : 'Ouvrir sur Internet';
  $('#b-tunnel').disabled = t === 'connexion';
  $('#tunnel-info').textContent = t.startsWith('erreur:') ? t.slice(7) : '';
  const js = E.classement || [];
  $('#nb-joueurs').textContent = js.length || '';
  maj($('#liste-joueurs'), JSON.stringify(js.map(j => [j.id, j.nom, j.couleur, j.avatar, j.profil])), js.length
    ? js.map(j => `<div class="joueur-ligne">${puce(j)}${j.profil && j.profil.toLowerCase() !== j.nom.toLowerCase()
                  ? `<small class="tag-profil" title="Relié au profil ${esc(j.profil)}">${esc(j.profil)}</small>` : ''}` +
                  `<button class="retirer" data-id="${j.id}" title="Retirer">×</button></div>`).join('')
    : `<p class="doux centre attente-joueurs">${TEL ? 'Personne pour l\'instant' : 'Scannez le QR code pour rejoindre'}</p>`);
  afficherPrep(false);
  const cleProfils = JSON.stringify(E.profils_actifs || []);
  if (cleProfils !== rendreLobby.profils) { rendreLobby.profils = cleProfils; if (CFG) dessinerJeux(); }
  if (E.erreur && !$('#erreur').textContent) $('#erreur').textContent = E.erreur;
}

/* ================= partie ================= */
$('#b-pause').onclick = () => action('pause');
$('#b-passer').onclick = () => action('passer');
$('#b-rejouer-manche').onclick = () => {
  if (confirm('Relancer cette manche avec d\'autres films ? Les points de la manche sont annulés.')) action('rejouer');
};
$('#b-rejouer').onclick = () => action('lancer');
$('#b-menu').onclick = () => {
  if (E.phase === 'fin' || confirm('Revenir au menu ? La partie en cours sera arrêtée.')) action('menu');
};
document.addEventListener('keydown', ev => {
  if (document.querySelector('dialog[open]') || ['INPUT', 'SELECT', 'TEXTAREA'].includes(ev.target.tagName)) return;
  if (E.phase === 'lobby') {
    if (ev.key === 'ArrowRight' || ev.key === 'PageDown') allerPage(pageJeux + 1);
    if (ev.key === 'ArrowLeft' || ev.key === 'PageUp') allerPage(pageJeux - 1);
    return;
  }
  if (ev.code === 'Space') { ev.preventDefault(); action('pause'); }
  else if (ev.key === 'ArrowRight') action('passer');
  else if (ev.key === 'f' || ev.key === 'F') {
    if (document.fullscreenElement) document.exitFullscreen(); else document.documentElement.requestFullscreen();
  }
});

/* ---------- son du blind test (joué uniquement ici, calé sur le chrono) ---------- */
const SON = new Audio();
SON.loop = true;
let sonSeq = -1, sonPret = false;
$('#b-son').onclick = () => { $('#b-son').hidden = true; SON.play().catch(() => {}); };
async function gererSon(e) {
  if (!e.audio) {
    if (sonSeq !== -1) { SON.pause(); sonSeq = -1; sonPret = false; $('#b-son').hidden = true; }
    return;
  }
  if (sonSeq !== e.seq) {
    sonSeq = e.seq;
    sonPret = false;
    SON.pause();
    try {
      const b = await (await fetch(`/audio/${e.seq}${Q}`)).blob();
      if (sonSeq !== e.seq) return;
      if (SON.src) URL.revokeObjectURL(SON.src);
      SON.src = URL.createObjectURL(b);
      await new Promise(ok => { SON.onloadedmetadata = ok; setTimeout(ok, 1500); });
      SON.currentTime = (E.ecoule || 0) % (SON.duration || 30);
      sonPret = true;
    } catch (err) { console.error(err); return; }
  }
  if (!sonPret) return;
  const jouer = !E.pause && !E.main;
  if (jouer && SON.paused) SON.play().then(() => { $('#b-son').hidden = true; }).catch(() => { $('#b-son').hidden = false; });
  if (!jouer && !SON.paused) SON.pause();
}

function classementHTML(e) {
  return (e.classement || []).map((j, i) => `<div class="rang" data-k="j${j.id}" style="--c:${j.couleur}"><span class="pos">${i + 1}</span>` +
    `<span class="pastille">${rond(j)}</span><span class="nom">${esc(j.nom)}</span>` +
    `<span class="statut ${(j.statut || {}).c || ''}">${esc((j.statut || {}).t || '')}</span><span class="pts">${j.score}</span></div>`
  ).join('') || '<p class="doux">Aucun joueur</p>';
}
function podium(cl) {
  const top = cl.slice(0, 3);
  if (!top.length) return '<div class="message">Partie terminée</div>';
  return `<div class="podium">${[1, 0, 2].filter(i => top[i]).map(i => `<div class="marche m${i + 1}" style="--c:${top[i].couleur}">
    <div class="avatar-grand" style="--c:${top[i].couleur}">${rond(top[i])}</div>
    <b>${esc(top[i].nom)}</b><span>${top[i].score}</span><div class="socle">${['I', 'II', 'III'][i]}</div></div>`).join('')}</div>`;
}
/* Le récap de fin : pour chacun, son meilleur jeu, sa meilleure manche, sa plus longue série ; les films qui ont
   résisté ; et une image à partager (dessinée dans un canvas, téléchargée en PNG). */
function recapHTML(r) {
  if (!r || !r.manches) return '';
  const cartes = (r.joueurs || []).map((j, k) => `<div class="rp-carte" style="--c:${j.couleur}"><p class="rp-nom"><b>${k + 1}.</b> ${esc(j.nom)} <span>${j.score}</span></p>` +
    `<ul>${j.meilleur_jeu ? `<li>Meilleur jeu : <b>${esc(j.meilleur_jeu)}</b> (+${j.meilleur_jeu_pts})</li>` : ''}` +
    `${j.meilleure_manche ? `<li>Plus beau coup : <b>+${j.meilleure_manche}</b> à ${esc(j.meilleure_manche_jeu)}</li>` : ''}` +
    `<li>${j.trouves} manche${j.trouves > 1 ? 's' : ''} gagnée${j.trouves > 1 ? 's' : ''}${j.serie > 1 ? ` · série de ${j.serie}` : ''}</li></ul></div>`).join('');
  const rates = (r.rates || []).length ? `<p class="rp-rates">Ils ont résisté à tout le monde : ${r.rates.map(esc).join(' · ')}</p>` : '';
  return `<div class="recap" data-k="recap"><div class="rp-cartes">${cartes}</div>${rates}` +
    `<p class="rp-bas">${r.manches} manches${r.jeu_or ? ` · le jeu le plus payant : <b>${esc(r.jeu_or)}</b>` : ''} ` +
    `<button id="b-recap-image" class="discret">📷 Image à partager</button></p></div>`;
}
function imageRecap(r) {
  const js = (r && r.joueurs) || [], W = 1080, H = 360 + js.length * 150 + ((r.rates || []).length ? 120 : 0);
  const c = document.createElement('canvas'); c.width = W; c.height = H;
  const g = c.getContext('2d');
  g.fillStyle = '#0d0c10'; g.fillRect(0, 0, W, H);
  for (let x = 0; x < W; x += 60) {                              // le sol de la Black Lodge, en bas
    g.fillStyle = '#f1e8d6'; g.beginPath(); g.moveTo(x, H - 60); g.lineTo(x + 30, H - 30); g.lineTo(x + 60, H - 60); g.lineTo(x + 60, H); g.lineTo(x, H); g.fill();
  }
  g.fillStyle = '#ffd24a'; g.font = '800 64px Georgia, serif'; g.textAlign = 'center';
  g.fillText('Twin Picks', W / 2, 110);
  g.fillStyle = '#c9bfae'; g.font = 'italic 30px Georgia, serif';
  g.fillText(`${r.manches} manches · ${new Date().toLocaleDateString('fr-FR')}`, W / 2, 160);
  js.forEach((j, k) => {
    const y = 230 + k * 150;
    g.fillStyle = j.couleur || '#888'; g.beginPath(); g.arc(110, y + 40, 40, 0, 7); g.fill();
    g.fillStyle = '#111'; g.font = '800 36px sans-serif'; g.fillText(String(k + 1), 110, y + 53);
    g.textAlign = 'left'; g.fillStyle = '#f1e3c4'; g.font = '800 44px sans-serif'; g.fillText(j.nom, 180, y + 40);
    g.fillStyle = '#ffd24a'; g.textAlign = 'right'; g.fillText(String(j.score), W - 70, y + 40);
    g.textAlign = 'left'; g.fillStyle = '#c9bfae'; g.font = '28px sans-serif';
    g.fillText([j.meilleur_jeu ? `Meilleur jeu : ${j.meilleur_jeu}` : '', j.serie > 1 ? `série de ${j.serie}` : '', `${j.trouves} gagnée(s)`]
      .filter(Boolean).join(' · '), 180, y + 88);
    g.textAlign = 'center';
  });
  if ((r.rates || []).length) {
    g.fillStyle = '#c9bfae'; g.font = 'italic 28px Georgia, serif';
    g.fillText('Ils ont résisté : ' + r.rates.join(' · ').slice(0, 70), W / 2, H - 110);
  }
  const a = document.createElement('a');
  a.href = c.toDataURL('image/png'); a.download = 'twin-picks-recap.png';
  document.body.appendChild(a); a.click(); a.remove();
}
document.addEventListener('click', ev => { if (ev.target.closest('#b-recap-image')) imageRecap((E || {}).recap); });
function bandeau(e) {
  if (e.phase === 'chargement') return e.erreur ? `<div class="erreur">${esc(e.erreur)}</div>` : '';
  if (e.phase === 'manche' && e.type !== 'complice') {
    if (e.main) return `<div class="avancement">${puce(e.main, '', 'grande')} a la main</div>`;
    const qcm = e.qcm ? `<div class="qcm-hote">${e.qcm.map((c, i) => `<div><b>${LETTRES[i]}</b>${esc(c)}</div>`).join('')}</div>` : '';
    return qcm + `<div class="avancement">${esc(e.avancement || '')}</div>`;
  }
  if (e.phase === 'reponse' && ['note', 'chrono', 'bingo'].includes(e.type)) return '';
  if (e.phase === 'reponse' && e.type === 'ordre') return `<div class="detail">${esc(e.detail || '')}</div>`;
  if (e.phase === 'reponse' && ['plusieurs', 'paire', 'brelan', 'paires', 'focus', 'rancon', 'dessin', 'contrat', 'differences', 'code', 'duels', 'double', 'duree', 'blackjack', 'pendule', 'enveloppes', 'pluie', 'mensonges', 'tableau', 'poker', 'diapason', 'entremots', 'enquete'].includes(e.type)) {
    // les résultats de chacun sont déjà sous le jeu : ici, la solution seule
    return `<div class="solution">${esc(e.solution)}</div>` + (e.detail ? `<div class="detail">${esc(e.detail)}</div>` : '');
  }
  if (e.phase === 'reponse' && e.type !== 'complice') {
    const r = e.resultats || [];
    const puces = r.map(x => puce(x, (e.type === 'nombre' ? ` ${x.reponse}` : '') + (x.gain ? ` <em>+${x.gain}</em>` : ''),
                                  x.gain ? 'juste' : 'faux')).join('');
    const gagnants = `<div class="gagnants">${puces || '<span class="doux">Personne</span>'}</div>`;
    if (e.type === 'choix') return gagnants;            // la solution est déjà en tête de la grille
    // Blind test (ordinateur) : ouvrir le morceau dans YouTube Music, pour l'ajouter à une playlist en un clic
    const ytm = e.morceau && !TEL ? ` <a class="lien ytm" target="_blank" rel="noopener" href="https://music.youtube.com/search?q=` +
      `${encodeURIComponent(e.morceau)}">▶ Ouvrir dans YouTube Music</a>` : '';
    return `<div class="solution">${cooper(r.some(x => x.gain), 'sol')}${esc(e.solution)}</div>` + (e.detail ? `<div class="detail">${esc(e.detail)}${ytm}</div>` : '') +
      gagnants;
  }
  return '';
}
const colsComplice = n => n <= 6 ? n : Math.ceil(n / 2);
function complHote(e) {
  const c = e.complice, src = i => `/img/${e.seq}/${i}${Q}`;
  const grille = cellule => grilleFilms(c.films, src, cellule, colsComplice(c.films.length));
  if (e.phase !== 'reponse') {
    let tete;
    if (c.sous === 'choix') {
      tete = c.mode === 'tous' ? 'Chacun choisit son film préféré' : `${puce(c.meneur, '', 'grande')} choisit son film préféré`;
    } else {
      tete = c.mode === 'tous' ? 'Retrouvez le film préféré de votre cible' : `Le film préféré de ${puce(c.meneur, '', 'grande')} ?`;
    }
    const paires = c.sous === 'devine' && c.mode === 'tous'
      ? `<div class="paires">${(c.paires || []).map(p => `<span>${puce(p.devineur)} → ${puce(p.cible)}</span>`).join('')}</div>` : '';
    const attente = `<div class="attente">${(c.attente || []).map(j => puce(j, '', j.fait ? 'juste' : 'attend')).join('')}</div>`;
    return `<h2 class="cbanniere">${tete}</h2>${paires}${attente}` + grille(() => ({}));
  }
  const r = c.resultats || {};
  if (r.aucun) return '<h2 class="cbanniere">Aucun film choisi</h2>' + grille(() => ({cls: 'terne'}));
  let tete;
  if (c.mode === 'tous') return revelationCroisee(e, r.paires || [], r.pas, p => {
    const f = c.films[p.film] || {}, vote = c.films[p.vote];
    return {qui: `Choix de ${puce(p.cible, '', 'grande')}`, img: f.img !== undefined ? src(f.img) : '', titre: f.txt || '?',
            ok: p.ok, verdict: p.ok ? `Trouvé par ${puce(p.devineur, p.gain ? ` <em>+${p.gain}</em>` : '', 'juste')}`
              : vote ? `${puce(p.devineur, '', 'faux')} a répondu <img class="mini-aff" src="${src(vote.img)}" alt=""> ${esc(vote.txt)}`
              : `${puce(p.devineur, '', 'faux')} n'a pas répondu`};
  });
  {
    tete = `<h2 class="cbanniere">${puce(c.meneur, '', 'grande')} préfère <span class="or">${esc((c.films[r.bonne] || {}).txt || '?')}</span></h2>` +
      (r.gain_meneur ? `<p class="doux centre">${esc(c.meneur.nom)} +${r.gain_meneur}</p>` : '');
  }
  return tete + grille(i => celluleRevelation(c, i));
}
/* Lignes qui apparaissent une à une : « Choix de Louison ✓ trouvé par Lily », puis « Choix de Lily ✗ … ».
   Toutes les lignes ont la même taille ; une nouvelle ligne s'ajoute sans que les autres bougent (maj = morph). */
function revelationCroisee(e, paires, pas, ligne) {
  const n = etapesRevelation(e, paires.length, pas), lignes = paires.map(ligne);
  const avecImg = lignes.some(l => l.img);
  return `<div class="revelation${avecImg ? '' : ' sans-img'}">` + lignes.slice(0, n).map((l, k) => {
    return `<div class="rligne apparait ${l.ok ? 'ok' : 'ko'}" data-k="r${k}">` +
      `<div class="r-qui">${l.qui}</div>` + (avecImg ? (l.img ? `<img class="r-aff" src="${l.img}" alt="">` : '<span></span>') : '') +
      `<div class="r-titre">${l.titre}</div><div class="r-symbole">${cooper(l.ok, 'ligne')}</div>` +
      `<div class="r-verdict">${l.verdict}</div></div>`;
  }).join('') + '</div>';
}

/* Jeux à moteur : Norma (note), Lucy (chrono), Donna (bingo). */
function moteurHote(e) {
  const mo = e.moteur || {}, rev = e.phase === 'reponse', src = i => `/img/${e.seq}/${i}${Q}`;
  if (e.type === 'note') {
    const film = visuelHTML(e, {q: Q});
    if (rev) {
      const res = mo.resultats || [];
      return film + revelationCroisee(e, res, mo.pas, r => ({
        qui: `Note de ${puce(r.cible, '', 'grande')}`, titre: `<span class="grosse-note">${r.note}<small>/10</small></span>`,
        ok: r.ecart === 0,
        verdict: r.reponse === null || r.reponse === undefined ? `${puce(r.devineur, '', 'faux')} n'a pas répondu`
          : `${puce(r.devineur, r.gain ? ` <em>+${r.gain}</em>` : '', r.ecart === 0 ? 'juste' : 'faux')} a dit <b>${r.reponse}</b>` +
            (r.ecart === 0 ? ' — exact !' : ` (à ${r.ecart} point${r.ecart > 1 ? 's' : ''})`)}));
    }
    return film + `<div class="paires">${(mo.paires || []).map(p => `<span>${puce(p.devineur)} → ${puce(p.cible)}</span>`).join('')}</div>` +
      `<div class="attente">${(mo.attente || []).map(j => puce(j, '', j.fait ? 'juste' : 'attend')).join('')}</div>`;
  }
  if (e.type === 'chrono') {
    const haut = visuelHTML(e, {q: Q}) + (mo.croisees ? `<div class="paires">${(mo.paires || [])
      .map(p => `<span>${puce(p.devineur)} → ${p.cible ? `les 8+ de <b>${esc(p.cible)}</b>` : '—'}</span>`).join('')}</div>` : '');
    if (rev) {
      return haut + `<div class="chrono-res">${(mo.resultats || []).map(r => `<div class="cr-col">${puce(r, ` <em>${r.films.length}</em>`, r.films.length ? 'juste' : 'faux')}` +
        `<ul>${r.films.map(f => `<li>${esc(f)}</li>`).join('') || '<li class="doux">—</li>'}</ul>${r.bonus ? `<small class="ok">bonus du classement +${r.bonus}</small>` : ''}</div>`).join('')}</div>` +
        ((mo.oublies || []).length ? `<p class="oublies"><span class="doux">Personne n'a trouvé :</span> ${mo.oublies.map(esc).join(' · ')}</p>` : '');
    }
    const max = Math.max(1, ...(mo.compteurs || []).map(c => c.n)), ch = mo.changer || {};
    const changer = ch.possible && ch.votes ? `<p class="votes-changer">Changer de condition : ${ch.votes}/${ch.total}</p>` : '';
    return haut + changer + `<div class="compteurs">${(mo.compteurs || []).map(c => `<div class="compteur" style="--c:${c.couleur}" data-k="${c.id}">` +
      `${puce(c)}<div class="barre-c"><div style="width:${100 * c.n / max}%"></div></div><b>${c.n}</b></div>`).join('')}</div>`;
  }
  if (e.type === 'duels') {
    const d = duelsHTML(e, src);
    if (!rev) return d;
    return d + `<div class="frise-res">${(mo.resultats || []).map(r => puce(r, ` ${r.justes}/${mo.n}` + (r.gain ? ` <em>+${r.gain}</em>` : ''),
      r.justes === mo.n ? 'juste' : r.justes ? '' : 'faux')).join('')}</div>`;
  }
  if (e.type === 'rancon') {                             // Jean Renault : la rançon
    const v = visuelHTML(e, {q: Q, hote: true});
    if (!rev) return v;
    return v + `<div class="frise-res">${(mo.resultats || []).map(r => puce(r, ` mise ${r.mise} · preuves ${r.depense}` + (r.gain ? ` <em>${r.gain > 0 ? '+' : ''}${r.gain}</em>` : ''),
      r.trouve ? 'juste' : 'faux')).join('')}</div>`;
  }
  if (e.type === 'contrat') return contratHTML(e);         // Mitchum : le contrat
  if (e.type === 'blackjack') {                          // Jean Renault : le blackjack
    const d = blackjackHTML(e, src);
    if (!rev) return d;
    return d + `<div class="frise-res">${(mo.resultats || []).map(r => puce(r, ` ${String(r.total).replace('.', ',')}` + (r.gain ? ` <em>${r.gain > 0 ? '+' : ''}${r.gain}</em>` : ''),
      r.res === 'gagne' ? 'juste' : r.res === 'egal' ? '' : 'faux')).join('')}</div>`;
  }
  if (e.type === 'pendule') {                            // Windom Earle : la pendule
    const d = penduleHTML(e, src);
    if (!rev) return d;
    return d + `<div class="frise-res">${(mo.resultats || []).map(r => puce(r, ` ${r.coups} film${r.coups > 1 ? 's' : ''}` + (r.gain ? ` <em>+${r.gain}</em>` : ''),
      r.mat ? 'faux' : 'juste')).join('')}</div>`;
  }
  if (e.type === 'pluie') return pluieHTML(e, src);
  if (['diapason', 'entremots', 'enquete'].includes(e.type)) {   // Gersten, Naido, Tammy
    const d = e.type === 'diapason' ? diapasonHTML(e, src) : e.type === 'entremots' ? entremotsHTML(e, src) : enqueteHTML(e, src);
    if (!rev) return d;
    return d + `<div class="frise-res">${(mo.resultats || []).map(r => puce(r, r.gain ? ` <em>+${r.gain}</em>` : '', r.gain ? 'juste' : 'faux')).join('')}</div>`;
  }
  if (e.type === 'poker') {                              // Bernard Renault : le poker
    const d = pokerHTML(e, src);
    if (!rev) return d;
    return d + `<div class="frise-res">${(mo.resultats || []).map(r => puce(r, ` ${esc(r.main || '')}` + (r.gain ? ` <em>${r.gain > 0 ? '+' : ''}${r.gain}</em>` : ''),
      r.gagne ? 'juste' : r.gain >= 0 ? '' : 'faux')).join('')}</div>`;
  }
  if (e.type === 'tableau') {                            // Mrs. Tremond : le tableau
    const d = tableauHTML(e, src);
    if (!rev) return d;
    return d + `<div class="frise-res">${(mo.resultats || []).map(r => puce(r, r.gain ? ` <em>+${r.gain}</em>` : '', r.gain ? 'juste' : 'faux')).join('')}</div>`;
  }
  if (e.type === 'mensonges') {                          // Lana : les mensonges
    const d = mensongesHTML(e);
    if (!rev) return d;
    return d + `<div class="frise-res">${(mo.resultats || []).map(r => puce(r, r.gain ? ` <em>+${r.gain}</em>` : '', r.gain ? 'juste' : 'faux')).join('')}</div>`;
  }          // Bushnell : la pluie d'affiches
  if (e.type === 'enveloppes') {                         // Dick Tremayne, Dwayne Milford : les enveloppes
    const d = ceremonieHTML(e, src);
    if (!rev) return d;
    return d + `<div class="frise-res">${(mo.resultats || []).map(r => puce(r, r.gain ? ` <em>+${r.gain}</em>` : '', r.gain ? 'juste' : 'faux')).join('')}</div>`;
  }
  if (e.type === 'code') {                               // Desmond : le code
    const d = codeHTML(e, src);
    if (!rev) return d;
    return d + `<div class="frise-res">${(mo.resultats || []).map(r => puce(r, (r.donneur ? ' (donneur)' : '') + (r.gain ? ` <em>${r.gain > 0 ? '+' : ''}${r.gain}</em>` : ''),
      r.gain > 0 ? 'juste' : 'faux')).join('')}</div>`;
  }
  if (e.type === 'differences') {                        // Mr. C : le double
    const d = jumeauxHTML(e, src);
    if (!rev) return d;
    return d + `<div class="frise-res">${(mo.resultats || []).map(r => puce(r, ` ${r.n}/${mo.n}` + (r.gain ? ` <em>${r.gain > 0 ? '+' : ''}${r.gain}</em>` : ''),
      r.n === mo.n ? 'juste' : r.n ? '' : 'faux')).join('')}</div>`;
  }
  if (e.type === 'dessin') {                             // Woodsman : le dessin de lumière
    const d = dessinHTML(e, src);
    if (!rev) return d + `<div class="frise-res">${(mo.trouves || []).map(r => puce(r, '', 'juste')).join('')}</div>`;
    return d + `<div class="frise-res">${(mo.resultats || []).map(r => puce(r, (r.dessine ? ' (dessin)' : '') +
      (r.gain ? ` <em>+${r.gain}</em>` : ''), r.gain > 0 ? 'juste' : 'faux')).join('')}</div>`;
  }
  if (e.type === 'focus') {                              // Hank : les dominos (façon Focus)
    const d = focusHTML(e, src);
    if (!rev) return d;
    return d + `<div class="frise-res">${(mo.resultats || []).map(r => puce(r, r.gain ? ` <em>${r.gain > 0 ? '+' : ''}${r.gain}</em>` : '',
      r.gain > 0 ? 'juste' : 'faux')).join('')}</div>`;
  }
  if (e.type === 'paires') {                             // Mike : les paires
    const pr = pairesHTML(e, src);
    if (!rev) return pr;
    return pr + `<div class="frise-res">${(mo.resultats || []).map(r => puce(r, ` ${r.justes}/4` + (r.gain ? ` <em>+${r.gain}</em>` : ''),
      r.justes === 4 ? 'juste' : r.justes ? '' : 'faux')).join('')}</div>`;
  }
  if (e.type === 'brelan') {                             // Jacques : le brelan
    const b = brelanHTML(e, src);
    if (!rev) return b;
    return b + `<div class="frise-res">${(mo.resultats || []).map(r => puce(r, ` ${r.justes}/3` + (r.gain ? ` <em>+${r.gain}</em>` : ''),
      r.justes === 3 ? 'juste' : r.justes ? '' : 'faux')).join('')}</div>`;
  }
  if (e.type === 'plusieurs' || e.type === 'paire') {     // Carl : les deux films ; Dougie : le jackpot
    const v = visuelHTML(e, {q: Q, hote: true}), n = mo.n || 2;
    if (!rev) return v;
    return v + `<div class="frise-res">${(mo.resultats || []).map(r => puce(r, ` ${r.n}/${n}` + (r.gain ? ` <em>+${r.gain}</em>` : ''),
      r.n === n ? 'juste' : r.n ? '' : 'faux')).join('')}</div>`;
  }
  if (e.type === 'duree') {
    const v = visuelHTML(e, {q: Q});
    if (!rev) return v;
    return v + `<div class="frise-res">${(mo.resultats || []).map(r => puce(r, ` ${r.reponse_hm || r.reponse + ' min'} · ${r.ecart ? `à ${hmJS(r.ecart)}` : 'pile !'}` +
      (r.gain ? ` <em>+${r.gain}</em>` : ''), r.trouve ? 'juste' : r.gain ? '' : 'faux')).join('')}</div>`;
  }
  if (e.type === 'double') {
    const reg = benHTML(e, src);
    if (!rev) return reg;
    return reg + `<div class="frise-res">${(mo.resultats || []).map(r => puce(r, ` ${r.justes}/2` + (r.gain ? ` <em>+${r.gain}</em>` : ''),
      r.justes === 2 ? 'juste' : r.justes ? '' : 'faux')).join('')}</div>`;
  }
  if (e.type === 'ordre') {
    const frise = friseHTML(e, src);
    if (!rev) return frise;
    return frise + `<div class="frise-res">${(mo.resultats || []).map(r => puce(r, ` ${r.reponse ? `${r.justes}/${mo.ordre.length}` : '—'}` +
      (r.gain ? ` <em>+${r.gain}</em>` : ''), r.parfait ? 'juste' : r.reponse ? '' : 'faux')).join('')}</div>`;
  }
  if (e.type === 'bingo') {
    const g = Object.assign({}, e.etat, {taille: mo.taille, mode: mo.mode, lignes: mo.lignes || e.etat.lignes, colonnes: mo.colonnes || e.etat.colonnes});
    if (rev) {
      return `<div class="bingo-res">${(mo.resultats || []).map(r => `<div class="br-joueur" data-k="${r.id}">` +
        `${puce(r, r.bingo ? ' <em>bingo !</em>' : '', r.bingo ? 'juste' : '')}` +
        bingoHTML({taille: mo.taille, mode: mo.mode, lignes: r.lignes, colonnes: r.colonnes, rel_l: r.rel_l, rel_c: r.rel_c},
          r.cases.map(c => Object.assign({}, c, {film: c.film || ''})), {cls: 'petit', cellule: (i, c) => ({
            html: c.film ? '' : '<b class="b-film vide">—</b>'})}) + '</div>').join('')}</div>`;
    }
    const progres = cls => `<div class="progres ${cls}">${(mo.progres || []).map(j => `<span class="pg" data-k="${j.id}">` +
      `${puce(j, '', j.bingo ? 'juste' : '')}<span class="mini-grille" style="--n:${g.taille}">` +
      `${j.cases.map(x => `<i class="${x ? 'on' : ''}"></i>`).join('')}</span>` +
      (j.rang ? `<small class="rang-fin">${j.rang === 1 ? '1er' : j.rang + 'e'} à finir</small>` : '') + '</span>').join('')}</div>`;
    if (mo.par_joueur) {
      return `<h2 class="bingo-chacun">Chacun sa grille</h2><p class="doux centre">${g.taille} × ${g.taille} · ` +
        `${g.mode === 'lignes' ? 'une condition par ligne et par colonne' : 'une condition par case'} · sur vos téléphones</p>` + progres('grand');
    }
    const cases = g.mode === 'lignes' ? Array.from({length: g.taille * g.taille}, () => ({})) : (e.etat.cases || []).map(t => ({txt: t}));
    return bingoHTML(g, cases, {cls: 'hote'}) + progres('');
  }
  return '';
}
function titreJeu(e) {
  if (e.phase === 'chargement') return '<div><b>Chargement</b></div>';
  if (e.phase === 'fin') return `${embleme('pics', 'mini')}<div><b>Fin de partie</b></div>`;
  return portrait(e.perso, CFG.persos, 'mini') + `<div><small>${esc(e.jeu_nom || '')}</small><b>${esc(e.jeu_titre || e.jeu_nom || '')}</b></div>`;
}
function rendreJeu() {
  const e = E, vis = $('#j-visuel'), t = $('#j-timer');
  const jeuDecor = ['manche', 'reponse'].includes(e.phase) ? (e.jeu || '') : '';
  GRAINE_DECOR = e.seq || 0;
  $('#jeu').dataset.jeu = jeuDecor;                                   // décor du jeu (style.css, decor.js)
  maj($('#j-decor'), 'd' + jeuDecor + '|' + (e.seq || 0), () => decorHTML(jeuDecor));
  maj($('#j-titre'), e.phase + e.jeu, titreJeu(e));
  $('#j-manche').innerHTML = e.total && e.phase !== 'fin'
    ? `${Math.min(e.manche, e.total)}<span>/${e.total}</span>` : '';
  $('#b-pause').textContent = e.pause ? 'Reprendre' : 'Pause';
  $('#b-pause').hidden = $('#b-passer').hidden = e.phase === 'fin';
  $('#b-rejouer-manche').hidden = !['manche', 'reponse'].includes(e.phase);
  $('#b-rejouer').hidden = e.phase !== 'fin';
  $('#code-jeu').innerHTML = e.code ? `Partie <b>${esc(e.code)}</b>` : '';
  t.hidden = e.phase !== 'manche';
  const r = restant(e);
  $('#j-barre').style.width = e.phase === 'manche' ? (100 * r / Math.max(1, e.duree)) + '%' : '0';
  $('#j-barre').className = e.pause || e.main ? 'gele' : r <= 5 ? 'urgent' : '';
  if (e.phase === 'manche') {
    t.className = 'timer' + (e.pause ? ' pause' : e.main ? ' gele' : r <= 5 ? ' urgent' : '');
    t.textContent = e.pause ? 'pause' : Math.ceil(r);
  }
  if (e.phase === 'chargement') {
    maj(vis, 'charg' + e.message, enveloppe(`<div class="chargement"><div class="spinner"></div><p>${esc(e.message || '')}</p></div>`), 'charg');
  } else if (e.phase === 'fin') {
    maj(vis, 'fin' + JSON.stringify([e.classement, e.recap]), enveloppe(podium(e.classement || []) + recapHTML(e.recap)), 'fin');
  } else if (e.type === 'complice' && e.complice) {
    const pas = e.phase === 'reponse' ? etapesRevelation(e, 99, (e.complice.resultats || {}).pas) : 0;
    maj(vis, JSON.stringify([e.phase, e.seq, e.pause, e.complice, pas]), enveloppe(() => complHote(e)), e.seq);
  } else if (e.moteur) {
    const pas = e.phase === 'reponse' ? etapesRevelation(e, 99, e.moteur.pas) : 0;
    maj(vis, JSON.stringify([e.phase, e.seq, e.etat, e.moteur, pas]), enveloppe(() => moteurHote(e)), e.seq);
  } else {
    const arret = e.vue === 'cassette' ? String(e.pause || !!e.main) : '';
    const n = ((e.etat || {}).items || []).length;
    maj(vis, `${e.phase}|${e.seq}|${e.revelation}|${JSON.stringify(e.etat)}|${arret}|${JSON.stringify(e.choix || '')}`,
        enveloppe(() => visuelHTML(e, {q: Q, hote: true, largeur: vis.clientWidth - 40, tuile: 80, cols: 5,
                             colsChoix: (e.etat || {}).paire ? (n <= 4 ? 2 : 3) : (e.etat || {}).echarpes ? 8 : e.jeu === 'hank' ? 6 : n <= 6 ? n : Math.ceil(n / 2)})), e.seq);
  }
  ajuster(vis);
  placerColles(e);
  maj($('#j-info'), JSON.stringify([e.phase, e.seq, e.main, e.avancement, e.resultats, e.qcm, e.erreur]), bandeau(e));
  maj($('#j-classement'), JSON.stringify(e.classement), classementHTML(e));
}

/* ================= boucle ================= */
function rendre() {
  const enJeu = E.phase !== 'lobby';
  const etaitCache = $('#lobby').hidden;
  $('#lobby').hidden = enJeu;
  $('#jeu').hidden = !enJeu;
  if (!enJeu && etaitCache && CFG) paginerJeux();
  if (enJeu) rendreJeu(); else rendreLobby();
}
async function boucle() {
  if (arret) return;
  try {
    const e = await get('/api/hote/etat' + Q + (TEL ? '&tel=1' : ''));
    if (e.interdit) return interdit();
    E = e;
    if (CFG) rendre();
    gererSon(e);
    if (CFG && typeof majMusique === 'function') majMusique(e);
  } catch (err) { console.error(err); }
  setTimeout(boucle, E && E.type === 'dessin' && E.phase === 'manche' ? 150 : 400);   // le dessin : plus fluide
}
if (!K) interdit(); else { chargerConfig(); boucle(); }


/* ---------- les objets « post-it » : posés par-dessus l'interface de la manche, à cheval sur ses bords ----------
   Le calque #j-colles (hors de la zone redessinée et zoomée) prend la taille et la place du bloc principal. */
function placerColles(e) {
  const L = $('#j-colles');
  if (!L) return;
  const jeu = e.phase === 'manche' ? (e.jeu || '') : '';
  maj(L, `c${jeu}|${e.seq || 0}`, () => jeu ? colles(jeu) : '');
  let cible = null, aire = 0;
  const blocs = [];
  for (const c of ($('#j-visuel .ajuste') || {children: []}).children) {
    const r = c.getBoundingClientRect();
    if (r.width && r.height) blocs.push(r);
    if (r.width * r.height > aire) { aire = r.width * r.height; cible = r; }
  }
  if (!jeu || !cible || !L.firstChild) { L.style.display = 'none'; return; }
  const p = L.parentElement.getBoundingClientRect();
  Object.assign(L.style, {display: '', left: (cible.left - p.left) + 'px', top: (cible.top - p.top) + 'px',
                          width: cible.width + 'px', height: cible.height + 'px'});
  /* Un objet qui sortirait de la scène est ramené dedans. S'il finit alors en grande partie sur l'interface (pas la
     place à côté), on le pose au-dessus du coin ; s'il gêne encore, on ne le montre pas : il ne cache jamais le jeu.
     Une réplique (post-it) ne passe jamais sur l'interface. */
  const recouvre = q => blocs.reduce((t, b) => t + Math.max(0, Math.min(q.right, b.right) - Math.max(q.left, b.left)) *
    Math.max(0, Math.min(q.bottom, b.bottom) - Math.max(q.top, b.top)), 0) / Math.max(1, q.width * q.height);
  const caser = o => {
    o.style.translate = '';
    const r = o.getBoundingClientRect(), m = 6;
    const dx = Math.max(0, p.left + m - r.left) - Math.max(0, r.right - (p.right - m));
    const dy = Math.max(0, p.top + m - r.top) - Math.max(0, r.bottom - (p.bottom - m));
    if (dx || dy) o.style.translate = `${dx}px ${dy}px`;
    return recouvre(o.getBoundingClientRect());
  };
  for (const o of L.children) {
    if (o.classList.contains('tache')) continue;
    o.classList.remove('repli');
    o.style.visibility = '';
    const limite = o.classList.contains('postit-c') ? 0.02 : 0.4;
    if (caser(o) > limite) {
      o.classList.add('repli');
      if (caser(o) > limite) o.style.visibility = 'hidden';
    }
  }
}
addEventListener('resize', () => E && placerColles(E));


/* ================= image d'une carte du menu ================= */
/* On choisit une image, on la cadre (glisser, molette ou curseur pour zoomer) et l'on voit tout de suite ce qui sera
   affiché : la carte choisie et non choisie, le petit portrait rond (en-tête de la partie, photo de profil). */
const OBJ_IMAGE = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><rect x="3" y="5" width="18" height="14" rx="2"/>' +
  '<circle cx="9" cy="10" r="1.8"/><path d="M4 17l5-5 4 4 3-3 4 4"/></svg>';
const IMG = {g: null, im: null, data: '', carte: {z: 1, cx: .5, cy: .4}, rond: {z: 1, cx: .5, cy: .3}, cible: 'carte'};
const RATIO_CARTE = 900 / 474;
function cadre(c, ratio) {               // le rectangle découpé (en parts de l'image) pour un cadrage {z, cx, cy}
  const W = IMG.im.naturalWidth, H = IMG.im.naturalHeight;
  let l = W, h = W / ratio;
  if (h > H) { h = H; l = H * ratio; }
  l /= c.z; h /= c.z;
  const x = Math.max(0, Math.min(W - l, c.cx * W - l / 2)), y = Math.max(0, Math.min(H - h, c.cy * H - h / 2));
  return {x: x / W, y: y / H, l: l / W, h: h / H, px: [x, y, l, h]};
}
function dessinerApercus() {
  if (!IMG.im) return;
  const d = CFG.jeux[IMG.g];
  for (const [id, c, ratio] of [['#im-carte', IMG.carte, RATIO_CARTE], ['#im-rond', IMG.rond, 1]]) {
    const cv = $(id), x = cv.getContext('2d'), r = cadre(c, ratio);
    x.clearRect(0, 0, cv.width, cv.height);
    x.drawImage(IMG.im, ...r.px, 0, 0, cv.width, cv.height);
  }
  const url = $('#im-carte').toDataURL('image/jpeg', .85), rond = $('#im-rond').toDataURL('image/jpeg', .85);
  const carte = on => `<div class="jeu ${on ? 'on' : ''} apercu-carte"><div class="portrait"><img src="${url}" alt=""></div>` +
    `<div class="jeu-txt"><small>${esc(d.nom)}</small><b>${esc(d.titre || d.nom)}</b></div>` +
    (on ? '<div class="jeu-bas"><span class="jeu-source"><span class="lien">1 liste</span></span><div class="pas"><button>−</button><span>2</span><button>+</button></div></div>' : '') + '</div>';
  $('#im-apercus').innerHTML = `<div class="im-col"><small>Carte choisie</small>${carte(true)}</div>` +
    `<div class="im-col"><small>Carte non choisie</small>${carte(false)}</div>` +
    `<div class="im-col"><small>En-tête de la partie</small><div class="im-entete"><div class="portrait mini"><img src="${rond}" alt=""></div>` +
    `<div><small>${esc(d.nom)}</small><b>${esc(d.titre)}</b></div></div>` +
    `<small>Photo de profil</small><span class="puce"><i class="av" style="background-image:url('${rond}')"></i>Joueur</span></div>`;
  $('#im-zoom').value = IMG[IMG.cible].z;
}
function ouvrirImage(g) {
  const d = CFG.jeux[g];
  IMG.g = g; IMG.im = null; IMG.data = '';
  IMG.carte = {z: 1, cx: .5, cy: .4}; IMG.rond = {z: 1.6, cx: .5, cy: .3}; IMG.cible = 'carte';
  let dlg = $('#d-image');
  if (!dlg) {
    dlg = document.createElement('dialog');
    dlg.id = 'd-image';
    dlg.className = 'dialogue large';
    dlg.innerHTML = '<header><h2>Image de la carte</h2><button data-fermer class="discret petit">Fermer</button></header>' +
      '<div class="im-corps"><div class="im-gauche">' +
      '<label class="im-depot" id="im-depot"><input type="file" id="im-fichier" accept="image/*" hidden>' +
      '<span>Choisir une image<br><small class="doux">ou la glisser ici</small></span></label>' +
      '<div class="im-cadrage" hidden><div class="segments" id="im-cibles"><button data-c="carte" class="actif">Carte</button>' +
      '<button data-c="rond">Portrait rond</button></div>' +
      '<div class="im-toiles"><canvas id="im-carte" width="450" height="237"></canvas><canvas id="im-rond" width="160" height="160"></canvas></div>' +
      '<label class="im-zoom">Zoom <input type="range" id="im-zoom" min="1" max="4" step="0.02" value="1"></label>' +
      '<p class="aide">Glissez l\'image pour la cadrer. La molette zoome.</p></div></div>' +
      '<div class="im-droite"><div id="im-apercus" class="im-apercus"><p class="doux">L\'aperçu apparaîtra ici.</p></div></div></div>' +
      '<footer><button id="im-retirer" class="lien danger">Remettre l\'image d\'origine</button><span class="espace"></span>' +
      '<button id="im-enregistrer" class="primaire" disabled>Enregistrer</button></footer>';
    document.body.append(dlg);
    dlg.querySelector('[data-fermer]').onclick = () => dlg.close();
    const charger = f => {
      if (!f || !f.type.startsWith('image/')) return;
      const lec = new FileReader();
      lec.onload = () => {
        const im = new Image();
        im.onload = () => {                          // image réduite (2000 px au plus) avant l'envoi
          const k = Math.min(1, 2000 / Math.max(im.naturalWidth, im.naturalHeight));
          const cv = document.createElement('canvas');
          cv.width = Math.round(im.naturalWidth * k); cv.height = Math.round(im.naturalHeight * k);
          cv.getContext('2d').drawImage(im, 0, 0, cv.width, cv.height);
          IMG.data = cv.toDataURL('image/jpeg', .92);
          const im2 = new Image();
          im2.onload = () => { IMG.im = im2; dlg.querySelector('.im-cadrage').hidden = false; $('#im-enregistrer').disabled = false; dessinerApercus(); };
          im2.src = IMG.data;
        };
        im.src = lec.result;
      };
      lec.readAsDataURL(f);
    };
    $('#im-fichier').onchange = ev => charger(ev.target.files[0]);
    const depot = $('#im-depot');
    depot.ondragover = ev => { ev.preventDefault(); depot.classList.add('survol'); };
    depot.ondragleave = () => depot.classList.remove('survol');
    depot.ondrop = ev => { ev.preventDefault(); depot.classList.remove('survol'); charger(ev.dataTransfer.files[0]); };
    $('#im-cibles').onclick = ev => {
      const b = ev.target.closest('[data-c]');
      if (!b) return;
      IMG.cible = b.dataset.c;
      for (const x of $('#im-cibles').children) x.classList.toggle('actif', x === b);
      $('#im-zoom').value = IMG[IMG.cible].z;
    };
    $('#im-zoom').oninput = ev => { IMG[IMG.cible].z = Number(ev.target.value); dessinerApercus(); };
    for (const [id, c] of [['#im-carte', 'carte'], ['#im-rond', 'rond']]) {
      const cv = $(id);
      let dep = null;
      cv.onpointerdown = ev => { IMG.cible = c; for (const x of $('#im-cibles').children) x.classList.toggle('actif', x.dataset.c === c);
        dep = [ev.clientX, ev.clientY, IMG[c].cx, IMG[c].cy]; cv.setPointerCapture(ev.pointerId); };
      cv.onpointermove = ev => {
        if (!dep || !IMG.im) return;
        const r = cadre(IMG[c], c === 'carte' ? RATIO_CARTE : 1), k = cv.getBoundingClientRect();
        IMG[c].cx = Math.max(0, Math.min(1, dep[2] - (ev.clientX - dep[0]) / k.width * r.l));
        IMG[c].cy = Math.max(0, Math.min(1, dep[3] - (ev.clientY - dep[1]) / k.height * r.h));
        dessinerApercus();
      };
      cv.onpointerup = () => { dep = null; };
      cv.onwheel = ev => { ev.preventDefault(); IMG[c].z = Math.max(1, Math.min(4, IMG[c].z * (ev.deltaY < 0 ? 1.08 : 1 / 1.08))); dessinerApercus(); };
    }
    $('#im-enregistrer').onclick = async () => {
      if (!IMG.im) return;
      const ca = cadre(IMG.carte, RATIO_CARTE), ro = cadre(IMG.rond, 1);
      const r = await post('/api/hote/image_menu' + Q, {perso: CFG.jeux[IMG.g].perso, data: IMG.data,
        carte: {x: ca.x, y: ca.y, l: ca.l, h: ca.h}, portrait: {x: ro.x, y: ro.y, l: ro.l, h: ro.h}});
      if (r.erreur) return alert(r.erreur);
      CFG = r; dessinerConfig(); dlg.close();
    };
    $('#im-retirer').onclick = async () => {
      const r = await post('/api/hote/image_menu' + Q, {perso: CFG.jeux[IMG.g].perso, action: 'retirer'});
      if (r.erreur) return alert(r.erreur);
      CFG = r; dessinerConfig(); dlg.close();
    };
  }
  dlg.querySelector('h2').textContent = `Image de la carte · ${d.titre}`;
  dlg.querySelector('.im-cadrage').hidden = true;
  $('#im-enregistrer').disabled = true;
  $('#im-fichier').value = '';
  $('#im-apercus').innerHTML = `<p class="doux">Choisissez une image : l'aperçu montre la carte telle qu'elle sera dans le menu.</p>` +
    `<div class="im-col"><small>Aujourd'hui</small><div class="jeu on apercu-carte">${portrait(d.perso, CFG.persos)}` +
    `<div class="jeu-txt"><small>${esc(d.nom)}</small><b>${esc(d.titre)}</b></div></div></div>`;
  dlg.showModal();
}
