/* Téléphone d'un joueur Twin Picks. */
let pid = localStorage.getItem('pid'), S = null, COUL = {couleurs: [], prises: [], avatars: [], avatars_pris: []}, maCouleur = null;
let monAvatar = localStorage.getItem('avatar') || '';
let sel = -1, selCle = '', occupe = false, vuSeq = -1, etaitSaisie = false, minuteur = null, suggT = null;
let selCase = -1, suggN = 0;
let ordreTel = [], ordreSeq = -1;                    // La frise : films touchés dans l'ordre                                   // case sélectionnée (One-Eyed Donna's)
const lirePrefProfil = () => { const v = localStorage.getItem('profil'); return v === null ? null : v; };
let monProfil = lirePrefProfil();                   // profil choisi (null : celui qui porte le pseudo)

function montrer(id) { for (const v of ['v-rejoindre', 'v-jeu']) $('#' + v).hidden = v !== id; }

/* ================= rejoindre / profil ================= */
function palette(el, choisie, mienne) {
  el.innerHTML = COUL.couleurs.map(c => {
    const prise = COUL.prises.includes(c) && c !== mienne;
    return `<button class="pastille-c${c === choisie ? ' choisie' : ''}" data-c="${c}" style="--c:${c}" ${prise ? 'disabled title="Déjà prise"' : ''}></button>`;
  }).join('');
}
/* Photos de profil : « aucune » (initiale) puis les personnages ; celles des autres joueurs sont grisées. */
function photos(el, choisie, mienne) {
  el.innerHTML = `<button class="photo aucune${!choisie ? ' choisie' : ''}" data-a="" title="Aucune">${initiale($('#pseudo').value || S?.moi?.nom || '?')}</button>` +
    (COUL.avatars || []).map(a => {
      const prise = (COUL.avatars_pris || []).includes(a) && a !== mienne;
      return `<button class="photo${a === choisie ? ' choisie' : ''}" data-a="${esc(a)}" style="background-image:url('${urlAvatar(a)}')" ${prise ? 'disabled' : ''}></button>`;
    }).join('');
}
function apercu() {
  const a = $('#apercu');
  a.style.setProperty('--c', maCouleur);
  a.innerHTML = rond({nom: $('#pseudo').value || '?', avatar: monAvatar});
}
async function ecranRejoindre() {
  clearTimeout(minuteur);
  montrer('v-rejoindre');
  maj($('#logo-tel'), 'logo', logo());
  try { COUL = await get('/api/couleurs'); } catch (e) { /* hors ligne */ }
  if (!maCouleur || COUL.prises.includes(maCouleur)) {
    maCouleur = COUL.couleurs.find(c => !COUL.prises.includes(c)) || COUL.couleurs[0];
  }
  if (!$('#pseudo').value) $('#pseudo').value = localStorage.getItem('pseudo') || '';
  if (monAvatar && (!(COUL.avatars || []).includes(monAvatar) || COUL.avatars_pris.includes(monAvatar))) monAvatar = '';
  palette($('#palette'), maCouleur);
  photos($('#photos'), monAvatar);
  profilsTel();
  apercu();
}
/* « Je suis… » : le profil (listes, notes) est choisi à part du pseudo ; on peut jouer sous un autre nom.
   Sans choix, le joueur est relié au profil qui porte son pseudo. */
function profilActif(pseudo) {
  if (monProfil !== null) return monProfil;
  const p = (COUL.profils || []).find(x => x.nom.toLowerCase() === String(pseudo || '').trim().toLowerCase());
  return p ? p.nom : '';
}
function chipsProfils(el, pseudo, mien) {
  const l = COUL.profils || [], actif = profilActif(pseudo);
  el.innerHTML = l.length ? l.map(p => {
    const pris = (COUL.profils_pris || []).includes(p.nom) && p.nom !== mien;
    return `<button class="chip${actif === p.nom ? ' choisi' : ''}" data-profil="${esc(p.nom)}" data-av="${esc(p.avatar || '')}" ` +
      `${pris ? 'disabled title="Déjà pris"' : ''}>${esc(p.nom)}</button>`;
  }).join('') + `<button class="chip aucun${monProfil === '' ? ' choisi' : ''}" data-profil="">Aucun</button>` : '';
}
function profilsTel() { chipsProfils($('#profils-tel'), $('#pseudo').value); }
function choisirProfil(b, champ) {
  const nom = b.dataset.profil;
  monProfil = monProfil === nom ? null : nom;            // retoucher le profil choisi l'annule
  if (nom && monProfil !== null && !champ.value.trim()) champ.value = nom;
  const av = b.dataset.av;
  if (av && monProfil && !monAvatar && (COUL.avatars || []).includes(av) && !(COUL.avatars_pris || []).includes(av)) monAvatar = av;
}
$('#profils-tel').onclick = ev => {
  const b = ev.target.closest('[data-profil]');
  if (!b || b.disabled) return;
  choisirProfil(b, $('#pseudo'));
  photos($('#photos'), monAvatar);
  profilsTel();
  apercu();
};
$('#photos').onclick = ev => {
  const b = ev.target.closest('[data-a]');
  if (!b || b.disabled) return;
  monAvatar = b.dataset.a;
  photos($('#photos'), monAvatar);
  apercu();
};
$('#palette').onclick = ev => {
  const b = ev.target.closest('[data-c]');
  if (!b || b.disabled) return;
  maCouleur = b.dataset.c;
  palette($('#palette'), maCouleur);
  apercu();
};
$('#pseudo').oninput = () => { apercu(); profilsTel(); const a = $('#photos .aucune'); if (a) a.textContent = initiale($('#pseudo').value || '?'); };
$('#pseudo').onkeydown = ev => { if (ev.key === 'Enter') rejoindre(); };
$('#b-rejoindre').onclick = rejoindre;
async function rejoindre() {
  const nom = $('#pseudo').value.trim();
  if (!nom) return $('#pseudo').focus();
  localStorage.setItem('pseudo', nom);
  localStorage.setItem('avatar', monAvatar);
  if (monProfil === null) localStorage.removeItem('profil'); else localStorage.setItem('profil', monProfil);
  const r = await post('/api/rejoindre', Object.assign({nom, couleur: maCouleur, avatar: monAvatar},
                                                       monProfil === null ? {} : {profil: monProfil}));
  pid = r.pid;
  localStorage.setItem('pid', pid);
  boucle();
}

$('#b-profil').onclick = async () => {
  try { COUL = await get('/api/couleurs'); } catch (e) { return; }
  maCouleur = S.moi.couleur;
  monAvatar = S.moi.avatar || '';
  $('#p-nom').value = S.moi.nom;
  monProfil = S.moi.profil || (lirePrefProfil() === '' ? '' : null);
  palette($('#p-palette'), maCouleur, S.moi.couleur);
  photos($('#p-photos'), monAvatar, S.moi.avatar);
  chipsProfils($('#p-profils'), $('#p-nom').value, S.moi.profil);
  $('#d-profil').showModal();
};
$('#p-profils').onclick = ev => {
  const b = ev.target.closest('[data-profil]');
  if (!b || b.disabled) return;
  choisirProfil(b, $('#p-nom'));
  chipsProfils($('#p-profils'), $('#p-nom').value, S.moi.profil);
};
$('#p-photos').onclick = ev => {
  const b = ev.target.closest('[data-a]');
  if (!b || b.disabled) return;
  monAvatar = b.dataset.a;
  photos($('#p-photos'), monAvatar, S.moi.avatar);
};
$('#p-palette').onclick = ev => {
  const b = ev.target.closest('[data-c]');
  if (!b || b.disabled) return;
  maCouleur = b.dataset.c;
  palette($('#p-palette'), maCouleur, S.moi.couleur);
};
$('#p-ok').onclick = async () => {
  const r = await post('/api/profil', Object.assign({pid, nom: $('#p-nom').value, couleur: maCouleur, avatar: monAvatar},
                                                    monProfil === null ? {} : {profil: monProfil}));
  if (!r.ok) return alert(r.msg);
  if (monProfil === null) localStorage.removeItem('profil'); else localStorage.setItem('profil', monProfil);
  localStorage.setItem('pseudo', $('#p-nom').value.trim());
  localStorage.setItem('avatar', monAvatar);
  $('#d-profil').close();
  boucle();
};
$('#p-annuler').onclick = () => $('#d-profil').close();
$('#p-quitter').onclick = async () => {
  if (!confirm('Quitter la partie ? Votre score sera perdu.')) return;
  await post('/api/quitter', {pid});
  localStorage.removeItem('pid');
  pid = null;
  $('#d-profil').close();
  ecranRejoindre();
};

/* ================= actions ================= */
function retour(r) {
  const el = $('#retour');
  el.textContent = r.msg || r.erreur || '';
  el.className = 'retour ' + (r.correct ? 'ok' : r.ok ? 'info' : 'err');
}
async function action(url, data) {
  if (occupe) return;
  occupe = true;
  try { retour(await post(url, data)); } finally { occupe = false; }
  boucle();
}
async function valider() {
  const texte = $('#saisie').value.trim();
  if (!texte || occupe) return;
  if (S && S.type === 'code') {                       // Desmond : l'indice et son nombre
    if (!codeN) return retour({ok: false, msg: 'Choisissez le nombre de films'});
    await action('/api/jouer', {pid, texte, n: codeN});
    if ((S.moteur || {}).indice === texte || !(S.moteur || {}).actif) { $('#saisie').value = ''; codeN = 0; }
    return;
  }
  clearTimeout(suggT);
  occupe = true;
  try {
    const r = await post('/api/repondre', {pid, texte, case: selCase});
    retour(r);
    $('#sugg').innerHTML = '';
    if (r.correct && (S.type === 'chrono' || S.type === 'bingo' || S.type === 'pendule')) { $('#saisie').value = ''; selCase = -1; }
    else if (!r.correct) $('#saisie').select();
  } finally { occupe = false; }
  boucle();
}
$('#b-valider').onclick = valider;
$('#saisie').onkeydown = ev => { if (ev.key === 'Enter') valider(); };
/* Big Ed : la durée comprise s'affiche en direct (au pavé numérique, « 140 » = 1 h 40, jamais 2 h 20) */
function lireDuree(t) {
  const brut = String(t).trim().toLowerCase(), u = brut.replace(/min|mn/g, '').trim();
  if (/^\d+$/.test(u) && /min|mn/.test(brut)) return +u;
  const m = u.match(/^(\d{1,2})\s*(?:h|:|\.|,)\s*(\d{0,2})$/);
  if (m) return +m[1] * 60 + +(m[2] || 0);
  if (!/^\d+$/.test(u)) return null;
  if (u.length === 1) return +u * 60;
  if (u.length === 2) return +u[0] * 60 + +u[1] * 10;
  if (u.length === 3 && +u.slice(1) < 60) return +u[0] * 60 + +u.slice(1);
  return +u;
}
function apercuDuree() {
  if (!S || S.type !== 'duree') return;
  const q = $('#saisie').value, n = q.trim() ? lireDuree(q) : null;
  $('#aide-saisie').innerHTML = n === null ? (q.trim() ? '<span class="err">Durée illisible</span>' : 'Au pavé : 140 = 1 h 40')
    : `<b class="duree-vue">${hmJS(n)}</b>`;
}
$('#saisie').oninput = () => {
  clearTimeout(suggT);
  apercuDuree();
  const q = $('#saisie').value;
  if (!S || !(S.type === 'titre' || S.suggestions) || !q.trim()) { $('#sugg').innerHTML = ''; return; }
  const n = ++suggN;
  suggT = setTimeout(async () => {
    const l = await get('/api/suggestions?q=' + encodeURIComponent(q));
    if (n !== suggN || $('#saisie').value !== q) return;     // une réponse plus ancienne arrive après : ignorée
    $('#sugg').innerHTML = l.map(s => `<button data-v="${esc(s.v)}">${esc(s.l)}</button>`).join('');
  }, 150);
};
$('#sugg').onclick = ev => {
  const b = ev.target.closest('[data-v]');
  if (!b) return;
  $('#saisie').value = b.dataset.v;
  $('#sugg').innerHTML = '';
  $('#saisie').focus();
};
$('#zone').onclick = ev => {
  const q = ev.target.closest('[data-q]');
  if (q) return action('/api/choisir', {pid, i: Number(q.dataset.q)});
  if (ev.target.closest('#b-jai')) return action('/api/buzz', {pid});
  if (ev.target.closest('#b-cval')) { if (sel >= 0) action('/api/choisir', {pid, i: sel}); return; }
  const n = ev.target.closest('[data-n]');
  if (n) return action('/api/choisir', {pid, i: Number(n.dataset.n)});
  const chg = ev.target.closest('[data-changer]');
  if (chg && S.type === 'bingo' && (S.moteur || {}).actif) {
    const mo = S.moteur, cible = chg.dataset.changer, sens = cible[0], i = Number(cible.slice(1));
    const txt = sens === 'l' ? mo.lignes[i] : sens === 'c' ? mo.colonnes[i] : (mo.cases[i] || {}).txt;
    const ou = sens === 'l' ? 'les cases de cette ligne' : sens === 'c' ? 'les cases de cette colonne' : 'cette case';
    confirmer(`Changer la condition « ${txt} » ?`, `Une autre condition la remplace ; ${ou} rapporteront ${mo.malus} % de moins.`)
      .then(oui => { if (oui) action('/api/jouer', {pid, type: 'changer', cible}); });
    return;
  }
  if (ev.target.closest('#b-changer')) return action('/api/jouer', {pid, type: 'changer'});
  const bc = ev.target.closest('.bcase[data-case]');
  if (bc && bc.classList.contains('libre')) {
    const i = Number(bc.dataset.case);
    selCase = selCase === i ? -1 : i;
    rendre();
    if (selCase >= 0) $('#saisie').focus();
    return;
  }
  const pan = ev.target.closest('.drape.actif');
  if (pan) {
    const i = Number(pan.dataset.i), k = ordreTel.indexOf(i);
    if (k >= 0) ordreTel.splice(k, 1); else ordreTel.push(i);
    return rendre();
  }
  const cd = ev.target.closest('.cd-case.actif');
  if (cd) return action('/api/jouer', {pid, i: Number(cd.dataset.cd)});
  const jf = ev.target.closest('.jumeaux.tel .jm-cadre');
  if (jf && (S.moteur || {}).actif) {
    const b = jf.getBoundingClientRect();
    return action('/api/jouer', {pid, pos: [(ev.clientX - b.left) / b.width, (ev.clientY - b.top) / b.height]});
  }
  const cn = ev.target.closest('[data-cdn]');
  if (cn) { codeN = Number(cn.dataset.cdn); return rendre(); }
  if (ev.target.closest('#b-cd-stop')) return action('/api/jouer', {pid, stop: 1});
  if (ev.target.closest('#b-cd-fin')) return action('/api/jouer', {pid, terminer: 1});
  const bjm = ev.target.closest('[data-bjmise]');
  if (bjm && !bjm.disabled) return action('/api/jouer', {pid, mise: Number(bjm.dataset.bjmise)});
  if (ev.target.closest('#b-bj-carte')) return action('/api/jouer', {pid, carte: 1});
  if (ev.target.closest('#b-bj-reste')) return action('/api/jouer', {pid, rester: 1});
  const ce = ev.target.closest('[data-ce]');
  if (ce && !ce.disabled) return action('/api/jouer', {pid, env: (S.moteur || {}).k, i: Number(ce.dataset.ce)});
  const cea = ev.target.closest('[data-cea]');
  if (cea) return action('/api/jouer', {pid, env: (S.moteur || {}).k, annee: Number(cea.dataset.cea)});
  const ctc = ev.target.closest('[data-ctc]');
  if (ctc && !ctc.disabled) return action('/api/jouer', {pid, choix: Number(ctc.dataset.ctc)});
  if (ev.target.closest('#b-cest-lui')) return action('/api/jouer', {pid, cest_lui: 1});
  const ach = ev.target.closest('[data-acheter]');
  if (ach) return action('/api/jouer', {pid, acheter: ach.dataset.acheter});
  const mi = ev.target.closest('[data-mise]');
  if (mi) return action('/api/jouer', {pid, mise: Number(mi.dataset.mise)});
  const fj = ev.target.closest('.fo-joueur.cible-ok');
  if (fj) { focusCible = focusCible === fj.dataset.cible ? null : fj.dataset.cible; return rendre(); }
  const fd = ev.target.closest('.fo-domino.actif');
  if (fd) {
    const f = Number(fd.dataset.f), mo = S.moteur || {};
    if (mo.mon_tour && !focusCible) return action('/api/jouer', {pid, retirer: f});
    if (focusCible) { const c = focusCible; focusCible = null; return action('/api/jouer', {pid, cible: c, i: f}); }
  }
  const mb = ev.target.closest('.mk-boite.actif');
  if (mb) { const k = Number(mb.dataset.b); pairesSel = pairesSel === k ? -1 : k; return rendre(); }
  const mf = ev.target.closest('.mk-affiche-p.actif');
  if (mf && pairesSel >= 0) {
    const f = Number(mf.dataset.f), autre = pairesTel_.indexOf(f);
    if (autre >= 0) pairesTel_[autre] = undefined;
    pairesTel_[pairesSel] = f;
    const libre = [0, 1, 2, 3].find(k => pairesTel_[k] === undefined || pairesTel_[k] === null);
    pairesSel = libre === undefined ? -1 : libre;
    return rendre();
  }
  if (ev.target.closest('#b-paires-effacer')) { pairesTel_ = []; pairesSel = 0; return rendre(); }
  if (ev.target.closest('#b-paires-ok')) return action('/api/jouer', {pid, paires: [0, 1, 2, 3].map(k => pairesTel_[k])});
  const bj = ev.target.closest('.bj-carte.actif');
  if (bj) {
    const i = Number(bj.dataset.i), k = ordreTel.indexOf(i);
    if (k >= 0) ordreTel.splice(k, 1); else if (ordreTel.length < 3) ordreTel.push(i);
    return rendre();
  }
  if (ev.target.closest('#b-brelan-ok')) return action('/api/jouer', {pid, cartes: ordreTel.slice()});
  if (ev.target.closest('#b-frise-effacer')) { ordreTel = []; return rendre(); }
  if (ev.target.closest('#b-frise-ok')) return action('/api/jouer', {pid, ordre: ordreTel.slice()});
  const df = ev.target.closest('.duel-film.actif');
  if (df) return action('/api/jouer', {pid, duel: Number(df.dataset.duel), i: Number(df.dataset.i)});
  const rl = ev.target.closest('.r-ligne.actif');
  if (rl) {
    const i = Number(rl.dataset.i);
    if (S.type === 'double') return action('/api/jouer', {pid, page: rl.dataset.page, i});
    return action('/api/choisir', {pid, i});
  }
  const f = ev.target.closest('.cfilm.actif');
  if (f) {
    const i = Number(f.dataset.i);
    if (S.type === 'choix') return action('/api/choisir', {pid, i});
    if (S.complice.confirmer) { sel = i; rendre(); } else action('/api/choisir', {pid, i});
  }
};

/* ================= rendu ================= */
const message = html => `<div class="message">${html}</div>`;
function banniere(cls, titre, texte) {
  const c = cls === 'ok' ? cooper(true, 'ban') : cls === 'ko' ? cooper(false, 'ban') : '';
  return `<div class="cban ${cls}${c ? ' avec-cooper' : ''}">${c}<div><span class="tag">${titre}</span><div>${texte}</div></div></div>`;
}
function miniClassement(tout) {
  const cl = S.classement || [];
  return `<ol class="mini-cl">${cl.slice(0, tout ? 50 : 8).map((j, i) => `<li class="${j.id === S.moi.id ? 'moi' : ''}" style="--c:${j.couleur}">` +
    `<span>${i + 1}</span>${rond(j)}<b>${esc(j.nom)}</b>` +
    `<em>${j.score}${j.gain && !tout ? ` <small>+${j.gain}</small>` : ''}</em></li>`).join('')}</ol>`;
}
function qcmHTML() {
  return `<div class="qcm">${(S.qcm || []).map((c, i) => `<button data-q="${i}"><b>${LETTRES[i]}</b>${esc(c)}</button>`).join('')}</div>`;
}
function buzzHTML() {
  const bl = S.moi.bloque, occ = S.main;
  return `<button id="b-jai" class="jai" ${occ || bl ? 'disabled' : ''}>Buzz</button>` +
    message(occ ? `${puce(occ)} a la main` : bl ? `Bloqué ${bl} s` : '');
}
function reponseHTML() {
  const m = S.moi;
  let detail = '';
  if (S.type === 'nombre' && m.reponse !== null && m.reponse !== undefined) {
    detail = `<p class="centre doux">Votre réponse : <b>${m.reponse}</b></p>`;
  }
  const gain = m.gain
    ? `+${m.gain}` + (m.bonus ? ` <small>dont rattrapage +${m.bonus}</small>` : '') + (m.serie > 1 ? ` <small>série ×${m.serie}</small>` : '')
    : '+0';
  return cooper(!!m.gain, 'grand') + `<div class="solution-tel"><b>${esc(S.solution)}</b>${S.detail ? `<small>${esc(S.detail)}</small>` : ''}</div>${detail}` +
    `<div class="gain ${m.gain ? 'positif' : ''}">${gain}</div>` + miniClassement(false);
}

function complTel() {
  const c = S.complice, rev = S.phase === 'reponse', src = i => `/img/${S.seq}/${i}`;
  const cle = S.seq + c.sous;
  if (selCle !== cle) { selCle = cle; sel = -1; }
  let ban;
  if (rev) {
    const r = c.resultats || {};
    if (r.aucun) {
      ban = banniere('', 'Résultat', 'Aucun film choisi');
    } else if (c.mode === 'tous') {
      const p = (r.paires || []).find(x => x.devineur.id === S.moi.id);
      ban = p ? banniere(p.ok ? 'ok' : 'ko', p.ok ? 'Trouvé' : 'Raté',
          `${puce(p.cible)} <b>${esc((c.films[p.film] || {}).txt || '?')}</b>` + (S.moi.gain ? `<br>+${S.moi.gain}` : ''))
        : banniere('', 'Résultats', '');
    } else {
      const moiMeneur = c.meneur && c.meneur.id === S.moi.id;
      const vote = r.films.flatMap(f => f.votes).find(v => v.id === S.moi.id);
      const titre = moiMeneur ? 'Votre film' : vote && vote.ok ? 'Trouvé' : vote ? 'Raté' : 'Résultat';
      ban = banniere(moiMeneur || (vote && vote.ok) ? 'ok' : 'ko', titre,
        `${puce(c.meneur)} <b>${esc((c.films[r.bonne] || {}).txt || '?')}</b>` + (S.moi.gain ? `<br>+${S.moi.gain}` : ''));
    }
  } else if (c.sous === 'choix') {
    if (c.moi_choisit) {
      ban = c.mon_choix >= 0
        ? banniere('ok', 'Choix verrouillé', '')
        : banniere('go', c.mode === 'tous' ? 'À vous' : 'Vous êtes le meneur', 'Votre film préféré');
    } else {
      ban = banniere('', 'Patientez', `${puce(c.meneur)} choisit`);
    }
  } else if (!c.moi_devine) {
    ban = banniere('ok', 'Vous êtes la cible', '');
  } else if (c.actif) {
    ban = banniere('go', 'À vous', `Le film préféré de ${puce(c.cible)} ?`);
  } else {
    const fait = (c.attente || []).filter(j => j.fait).length;
    ban = banniere('ok', 'Réponse verrouillée', `${fait} / ${(c.attente || []).length}`);
  }
  const moi = `--c:${S.moi.couleur}`;
  const grille = grilleFilms(c.films, src, i => {
    if (rev) return celluleRevelation(c, i);
    if (c.actif) return {cls: 'actif' + (i === sel ? ' sel' : ''), badge: i === sel ? 'Sélectionné' : ''};
    if (c.mon_choix >= 0) {
      return i === c.mon_choix ? {cls: 'verrou', style: moi, badge: c.sous === 'choix' ? 'Mon film' : 'Ma réponse'} : {cls: 'terne'};
    }
    if (c.sous === 'devine' && !c.moi_devine && c.mon_favori === i) return {cls: 'verrou', style: moi, badge: 'Mon film'};
    return {};
  }, c.films.length <= 4 ? 2 : 3);
  const bouton = c.actif && c.confirmer
    ? `<button id="b-cval" class="valider-film" ${sel < 0 ? 'disabled' : ''}>${sel < 0 ? 'Choisissez un film' : 'Valider'}</button>` : '';
  return ban + grille + bouton + (rev ? '<br>' + miniClassement(false) : '');
}

function gainTel() {
  const m = S.moi;
  return `<div class="gain ${m.gain ? 'positif' : ''}">${m.gain < 0 ? m.gain : '+' + (m.gain || 0)}` +
    (m.bonus ? ` <small>dont rattrapage +${m.bonus}</small>` : '') + '</div>' + miniClassement(false);
}
function choixTel() {
  const rev = S.phase === 'reponse', m = S.moi, actif = !rev && !m.repondu && !S.pause;
  const n = ((S.etat || {}).items || []).length;
  const grille = (S.jeu === 'josie' ? josieHTML : choixHTML)(S, i => `/img/${S.seq}/${i}`, {colsChoix: S.jeu === 'maddy' || S.jeu === 'mike' ? n : S.jeu === 'annie' || S.jeu === 'hank' || (S.jeu === 'sarah' && n > 6) ? 4 : n > 4 && !(S.etat || {}).paire ? 3 : 2, sansVotes: true, sansSolution: true, cellule: i =>
    actif ? {cls: 'actif'} : m.reponse === i ? {cls: 'verrou', badge: 'Ma réponse'} : {cls: rev ? '' : 'terne'}});
  if (!rev) return grille + (m.repondu ? message('<span class="doux">Réponse envoyée</span>') : '');
  const bon = m.reponse === (S.choix || {}).bonne;
  return banniere(bon ? 'ok' : 'ko', bon ? 'Trouvé' : m.repondu ? 'Raté' : 'Pas de réponse', esc(S.solution)) +
    (S.detail ? `<p class="centre doux">${esc(S.detail)}</p>` : '') + grille + gainTel();
}
function duelsTel() {
  const mo = S.moteur || {}, rev = S.phase === 'reponse', mien = mo.ma_reponse || {};
  const d = duelsHTML(S, i => `/img/${S.seq}/${i}`, {sansVotes: true, cellule: (k, i) =>
    mien[k] === i ? {cls: 'sel', badge: 'Mon pari'} : mo.actif && mien[k] === undefined ? {cls: 'actif'} : {cls: rev ? '' : 'terne'}});
  if (!rev) {
    const k = Object.keys(mien).length;
    return d + message(`<span class="doux">${k === mo.n ? 'Tous les paris sont faits' : `Touchez un film par duel (${k}/${mo.n})`}</span>`);
  }
  const nb = Object.values(mo.mes_justes || {}).filter(Boolean).length;
  return banniere(nb === mo.n ? 'ok' : nb ? '' : 'ko', `${nb}/${mo.n} paris gagnés`, '') + d + gainTel();
}
function benTel() {
  const mo = S.moteur || {}, rev = S.phase === 'reponse', mien = mo.ma_reponse || {};
  const reg = benHTML(S, i => `/img/${S.seq}/${i}`, {sansVotes: true, cellule: (page, i) =>
    mien[page] === i ? {cls: 'sel', badge: ''} : mo.actif && mien[page] === undefined ? {cls: 'actif'} : {cls: rev ? '' : 'terne'}});
  if (!rev) {
    const k = Object.keys(mien).length;
    return reg + message(k === 2 ? '<span class="doux">Registre signé</span>' : k ? '<span class="doux">Cochez aussi l\'autre page</span>'
      : '<span class="doux">Cochez un montant sur chaque page</span>');
  }
  const j = mo.mes_justes || {}, nb = Object.values(j).filter(Boolean).length;
  return banniere(nb === 2 ? 'ok' : nb ? '' : 'ko', nb === 2 ? 'Les deux !' : nb ? 'La moitié' : Object.keys(j).length ? 'Raté' : 'Pas de réponse',
    esc(S.solution)) + reg + gainTel();
}
function noteTel() {
  const mo = S.moteur || {}, rev = S.phase === 'reponse';
  const mienne = mo.ma_note ? `<p class="centre doux">Votre note : <b>${mo.ma_note}/10</b> — les autres la devinent</p>` : '';
  if (rev) {
    const r = (mo.resultats || []).find(x => x.devineur && x.devineur.id === S.moi.id);
    const ban = r ? banniere(r.ecart === 0 ? 'ok' : 'ko', r.ecart === 0 ? 'Exact !' : r.ecart === null ? 'Pas de réponse' : `Raté de ${r.ecart} point${r.ecart > 1 ? 's' : ''}`,
      `Note de ${puce(r.cible)} : <b>${r.note}/10</b>` + (r.reponse ? ` · vous : ${r.reponse}` : '')) : banniere('', 'Résultats', '');
    return ban + gainTel();
  }
  if (mo.actif) {
    return banniere('go', 'À vous', `Quelle note ${puce(mo.cible)} a donnée à ce film ?`) +
      `<div class="notes10">${[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map(n => `<button data-n="${n}">${n}</button>`).join('')}</div>` + mienne;
  }
  if (mo.ma_reponse) return banniere('ok', 'Réponse verrouillée', `${mo.ma_reponse}/10 pour ${puce(mo.cible)}`) + mienne;
  return banniere('', 'Patientez', 'Vous ne devinez pas cette manche') + mienne;
}
function chronoTel() {
  const mo = S.moteur || {}, mes = mo.mes_films || [], ch = mo.changer || {};
  const liste = `<h3 class="etiquette">Vos films (${mes.length})${mo.avant ? ` <small>+ ${mo.avant} avant le changement</small>` : ''}</h3>` +
    `<ul class="mes-films">${mes.slice().reverse().map(f => `<li>${esc(f)}</li>`).join('')}</ul>`;
  if (S.phase !== 'reponse') {
    const bas = ch.possible ? `<div class="pied-discret"><button id="b-changer" class="discret-bas${ch.moi ? ' vote' : ''}">` +
      `${ch.moi ? 'Vous voulez changer' : 'Changer de condition'}${ch.votes ? ` · ${ch.votes}/${ch.total}` : ''}</button></div>` : '';
    return liste + bas;
  }
  return liste + ((mo.oublies || []).length ? `<p class="doux">Personne n'a trouvé : ${mo.oublies.map(esc).join(' · ')}</p>` : '') + gainTel();
}
function bingoTel() {
  const mo = S.moteur || {}, cases = mo.cases || [], rev = S.phase === 'reponse';
  if (selCase >= 0 && (!cases[selCase] || cases[selCase].film || !mo.actif)) selCase = -1;
  const g = bingoHTML({taille: mo.taille, mode: mo.mode, lignes: mo.lignes, colonnes: mo.colonnes, rel_l: mo.rel_l, rel_c: mo.rel_c},
    cases, {cls: 'tel', changer: mo.actif && mo.mode === 'lignes', cellule: (i, c) => {
      const libre = !c.film && mo.actif;
      return {cls: `${libre ? 'libre' : ''} ${i === selCase ? 'sel' : ''}`,
              html: c.film ? cooper(true, 'b-ok') : `<small class="b-pts">${c.valeur} pts</small>`};
    }});
  if (rev) return g + gainTel();
  let bas = '';
  if (mo.actif && selCase >= 0) {
    const c = cases[selCase], conds = mo.mode === 'lignes'
      ? [mo.lignes[Math.floor(selCase / mo.taille)], mo.colonnes[selCase % mo.taille]] : [c.txt];
    const changer = mo.mode === 'cases'
      ? `<button class="discret-bas" data-changer="k${selCase}">↻ Changer cette condition (−${mo.malus} %)</button>` : '';
    bas = `<div class="b-action"><small>Case choisie · ${c.valeur} pts</small><b>${conds.map(esc).join('<i> et </i>')}</b>${changer}</div>`;
  } else if (mo.actif) {
    bas = `<p class="centre doux b-aide">Touchez une case, puis tapez un film${mo.mode === 'lignes'
      ? '<br><small>Une condition impossible ? Touchez-la pour la changer (−' + mo.malus + ' %)</small>' : ''}</p>`;
  }
  return g + bas;
}

/* Nadine's Silent Drape Runners : toucher les affiches du plus ancien au plus récent, puis « Accrocher ». */
function friseTel() {
  const mo = S.moteur || {}, rev = S.phase === 'reponse', src = i => `/img/${S.seq}/${i}`;
  if (ordreSeq !== S.seq) { ordreSeq = S.seq; ordreTel = []; }
  const n = ((S.etat || {}).items || []).length;
  if (rev) {
    const o = mo.ma_reponse, justes = (mo.mes_justes || []).filter(Boolean).length;
    const frise = friseHTML(S, src, {cellule: i => {
      if (!o) return {};
      const pos = o.indexOf(i);
      return {cls: mo.ordre[pos] === i ? 'juste' : 'faux', badge: pos + 1};
    }});
    const ban = o ? banniere(justes === n ? 'ok' : 'ko', justes === n ? 'Frise parfaite' : `${justes} / ${n} à leur place`, '')
      : banniere('ko', 'Pas de frise envoyée', '');
    return ban + frise + gainTel();
  }
  if (!mo.actif) {
    const o = mo.ma_reponse;
    if (!o) return friseHTML(S, src) + message('<span class="doux">Patientez</span>');
    return friseHTML(S, src, {place: i => o.indexOf(i), cellule: i => ({cls: 'choisi', badge: o.indexOf(i) + 1})}) +
      message('<span class="doux">Frise accrochée</span>');
  }
  const frise = friseHTML(S, src, {cellule: i => {
    const k = ordreTel.indexOf(i);
    return {cls: 'actif' + (k >= 0 ? ' choisi' : ''), badge: k >= 0 ? k + 1 : ''};
  }});
  const complet = ordreTel.length === n;
  return frise + `<p class="centre doux">${esc(((S.etat || {}).consigne || 'Du plus ancien au plus récent'))} : touchez-les dans l'ordre (${ordreTel.length}/${n})</p>` +
    `<div class="boutons-frise"><button id="b-frise-effacer" class="discret" ${ordreTel.length ? '' : 'disabled'}>Effacer</button>` +
    `<button id="b-frise-ok" class="primaire" ${complet ? '' : 'disabled'}>Accrocher</button></div>`;
}

/* Jean Renault : le marché noir des preuves (sur le téléphone de chacun, en secret). */
function marcheHTML(mo, fige) {
  const src = i => `/img/${S.seq}/${i}`;
  return `<div class="marche"><p class="mk-tete">Le marché noir de Jean <span>dépensé : <b>${mo.depense || 0}</b> · rançon ${mo.ma_mise || 0}</span></p>` +
    (mo.marche || []).map(c => `<div class="mk-preuve${c.achete ? ' achete' : ''}"><span class="mk-nom">${esc(c.nom)}</span>` +
      (c.achete || c.texte !== undefined || c.img !== undefined
        ? (c.img !== undefined ? `<img src="${src(c.img)}" alt="">` : `<b class="mk-val">${esc(c.texte || '')}</b>`)
        : fige ? `<span class="mk-prix">${c.prix}</span>` : `<button class="mk-acheter" data-acheter="${esc(c.id)}">${c.prix}</button>`) + '</div>').join('') +
    '</div>';
}

/* Mike's Shoe Samples : toucher une boîte (un personnage), puis l'affiche de son film ; « Envoyer » quand les quatre
   boîtes ont leur film. Une affiche déjà donnée à une autre boîte change de boîte. */
let codeN = 0, pairesTel_ = [], pairesSel = -1, pairesSeq = -1, focusCible = null, focusSeq = -1;
function pairesTel() {
  const mo = S.moteur || {}, rev = S.phase === 'reponse', src = i => `/img/${S.seq}/${i}`;
  if (pairesSeq !== S.seq) { pairesSeq = S.seq; pairesTel_ = []; pairesSel = 0; }
  if (rev) {
    const j = mo.mes_justes, nb = (j || []).filter(Boolean).length;
    const ban = mo.ma_reponse ? banniere(nb === 4 ? 'ok' : nb ? '' : 'ko', nb === 4 ? 'Toutes les paires !' : `${nb} paire${nb > 1 ? 's' : ''} sur 4`, '')
      : banniere('ko', 'Pas de paires envoyées', '');
    return ban + pairesHTML(S, src, {justes: j || null}) + gainTel();
  }
  if (!mo.actif) {
    return pairesHTML(S, src, {affect: mo.ma_reponse || []}) +
      message(`<span class="doux">${mo.ma_reponse ? 'Paires envoyées' : 'Patientez'}</span>`);
  }
  const n = pairesTel_.filter(x => x !== undefined && x !== null).length;
  return pairesHTML(S, src, {affect: pairesTel_, sel: pairesSel, actif: true}) +
    `<p class="centre doux">${pairesSel >= 0 ? 'Touchez maintenant son film' : 'Touchez un personnage'}</p>` +
    `<div class="boutons-frise"><button id="b-paires-effacer" class="discret" ${n ? '' : 'disabled'}>Effacer</button>` +
    `<button id="b-paires-ok" class="primaire" ${n === 4 ? '' : 'disabled'}>Envoyer (${n}/4)</button></div>`;
}

/* Jacques Renault's Card Table : toucher les trois cartes du brelan, puis « Miser ». */
function brelanTel() {
  const mo = S.moteur || {}, rev = S.phase === 'reponse', src = i => `/img/${S.seq}/${i}`;
  if (ordreSeq !== S.seq) { ordreSeq = S.seq; ordreTel = []; }
  if (rev) {
    const o = mo.ma_reponse || [], bons = mo.bons || [], justes = o.filter(i => bons.includes(i)).length;
    const jeu = brelanHTML(S, src, {cellule: i => o.includes(i) ? {cls: bons.includes(i) ? 'juste choisi' : 'faux'} : {}});
    const ban = mo.ma_reponse ? banniere(justes === 3 ? 'ok' : justes ? '' : 'ko', justes === 3 ? 'Brelan !' : `${justes} carte${justes > 1 ? 's' : ''} sur 3`, '')
      : banniere('ko', 'Pas de mise', '');
    return ban + jeu + gainTel();
  }
  if (!mo.actif) {
    const o = mo.ma_reponse;
    return brelanHTML(S, src, {cellule: i => o && o.includes(i) ? {cls: 'choisi'} : {}}) +
      message(`<span class="doux">${o ? 'Mise posée' : 'Patientez'}</span>`);
  }
  const jeu = brelanHTML(S, src, {cellule: i => ({cls: 'actif' + (ordreTel.includes(i) ? ' choisi' : '')})});
  return jeu + `<div class="boutons-frise"><button id="b-frise-effacer" class="discret" ${ordreTel.length ? '' : 'disabled'}>Effacer</button>` +
    `<button id="b-brelan-ok" class="primaire" ${ordreTel.length === 3 ? '' : 'disabled'}>Miser (${ordreTel.length}/3)</button></div>`;
}

/* Fenêtre de confirmation (changer une condition du bingo) : renvoie une promesse vraie si l'on confirme. */
function confirmer(titre, texte) {
  const d = $('#d-confirmer');
  $('#c-titre').textContent = titre;
  $('#c-texte').textContent = texte || '';
  return new Promise(ok => {
    const fin = v => { d.close(); $('#c-oui').onclick = $('#c-non').onclick = null; ok(v); };
    $('#c-oui').onclick = () => fin(true);
    $('#c-non').onclick = () => fin(false);
    d.oncancel = () => fin(false);
    d.showModal();
  });
}

/* Ce qu'il faut afficher sous le visuel : [clé, html] ; html null = zone de saisie. */
function vueZone() {
  const m = S.moi;
  if (S.phase === 'lobby') {
    return ['lobby' + JSON.stringify(S.classement.map(j => [j.nom, j.couleur])),
      `<div class="attente-tel">${embleme('pics')}<p>En attente du lancement…</p></div>` +
      `<div class="presents">${S.classement.map(j => puce(j)).join('')}</div>` +
      `<button class="secondaire large code-autre" data-code="1"><b>#</b> Rejoindre une autre partie avec un code</button>`];
  }
  if (S.phase === 'chargement') return ['charg', message('<div class="spinner"></div>')];
  if (S.phase === 'fin') {
    const r = S.mon_recap;
    const mien = r ? `<ul class="rp-moi">${r.meilleur_jeu ? `<li>Votre meilleur jeu : <b>${esc(r.meilleur_jeu)}</b></li>` : ''}` +
      `${r.meilleure_manche ? `<li>Plus beau coup : <b>+${r.meilleure_manche}</b> (${esc(r.meilleure_manche_jeu)})</li>` : ''}` +
      `<li>${r.trouves} manche${r.trouves > 1 ? 's' : ''} gagnée${r.trouves > 1 ? 's' : ''}${r.serie > 1 ? ` · série de ${r.serie}` : ''}</li></ul>` : '';
    return ['fin' + JSON.stringify([S.classement, r]), '<h2 class="fin-titre">Classement final</h2>' + miniClassement(true) + mien];
  }
  if (S.type === 'complice' && S.complice) {
    return ['c' + JSON.stringify([S.phase, S.seq, S.pause, sel, S.complice]), complTel()];
  }
  if (S.type === 'choix') return ['ch' + JSON.stringify([S.phase, S.seq, S.etat, m.reponse, S.pause, S.choix, S.classement]), choixTel()];
  if (S.type === 'note') return ['no' + JSON.stringify([S.phase, S.seq, S.moteur, S.classement]), noteTel()];
  if (S.type === 'chrono') return ['cr' + JSON.stringify([S.phase, S.seq, S.moteur, S.classement]), chronoTel()];
  if (S.type === 'bingo') return ['bi' + JSON.stringify([S.phase, S.seq, S.moteur, selCase, S.classement]), bingoTel()];
  if (S.type === 'duels') return ['de' + JSON.stringify([S.phase, S.seq, S.etat, S.moteur, S.classement]), duelsTel()];
  if (S.type === 'double') return ['do' + JSON.stringify([S.phase, S.seq, S.etat, S.moteur, S.classement]), benTel()];
  if (S.type === 'ordre') return ['or' + JSON.stringify([S.phase, S.seq, S.etat, S.moteur, ordreTel, S.classement]), friseTel()];
  if (S.type === 'rancon') {                        // Jean Renault : la rançon et le marché noir
    const mo = S.moteur || {};
    if (S.phase === 'reponse') {
      const r = (mo.resultats || []).find(x => x.id === m.id) || {};
      return ['rc' + S.seq + JSON.stringify(S.classement), banniere(r.trouve ? 'ok' : 'ko', r.trouve ? 'Otage libéré !' : 'Rançon perdue',
        `<b>${esc(S.solution)}</b>`) + marcheHTML(mo, true) + gainTel()];
    }
    if (mo.etape === 'mise') {
      if (!mo.actif) return ['rc-m' + S.seq + mo.ma_mise, message(`<span class="doux">Rançon misée : <b>${mo.ma_mise ?? 0}</b></span>`)];
      return ['rc-mm' + S.seq, `<p class="centre doux">Votre rançon ? Trouvé : vous la doublez. Raté : vous la perdez.</p>` +
        `<div class="rc-boutons">${(mo.mises || []).map(x => `<button class="mise-b" data-mise="${x}">${x ? x : 'Rien'}</button>`).join('')}</div>`];
    }
    if (mo.trouve) return ['rc-ok' + S.seq, message(cooper(true, 'grand') + '<span class="ok">Otage libéré !</span>') + marcheHTML(mo, true)];
    return ['rc-mk' + JSON.stringify([S.seq, mo.marche, mo.actif, mo.depense]), marcheHTML(mo, !mo.actif)];
  }
  if (S.type === 'code') {                          // Desmond : le code (règles de Codenames)
    const mo = S.moteur || {}, src = i => `/img/${S.seq}/${i}`;
    if (S.phase === 'reponse') {
      const r = (mo.resultats || []).find(x => x.id === m.id) || {};
      return ['cd' + S.seq + JSON.stringify(S.classement), banniere(r.gain > 0 ? 'ok' : 'ko', r.gain > 0 ? `+${r.gain}` : r.gain < 0 ? `${r.gain}` : 'Pas de points', '') +
        codeHTML(S, src, {joueur: true}) + gainTel()];
    }
    let aide = '', bas = '';
    if (mo.donneur_moi) {
      if (mo.actif) {
        const nb = Math.max(1, mo.reste_or || 1);
        if (codeN > nb) codeN = 0;
        bas = `<div class="cd-nombres">${Array.from({length: nb}, (_, k) => `<button class="cd-n${codeN === k + 1 ? ' choisi' : ''}" data-cdn="${k + 1}">${k + 1}</button>`).join('')}</div>` +
          (mo.indices && mo.indices.length ? '<button id="b-cd-fin" class="discret">Terminer la manche</button>' : '');
        aide = 'Tapez votre indice, choisissez le nombre, puis Valider';
      } else aide = 'Les autres cherchent…';
    } else if (mo.elimine) aide = '☠ Le film noir : éliminé pour cette manche';
    else if (!mo.indice) aide = 'Attendez l\'indice…';
    else if (mo.actif) {
      aide = `<b>${esc(mo.indice)} · ${mo.nb}</b> — touchez un film (encore ${mo.essais} au plus)`;
      bas = '<button id="b-cd-stop" class="discret">Je m\'arrête là</button>';
    } else aide = 'Tour fini : attendez l\'indice suivant';
    return ['cd' + JSON.stringify([S.seq, mo.indices, mo.mes, mo.actif, mo.essais, mo.elimine, codeN]),
      `<p class="fo-aide">${aide}</p>` + codeHTML(S, src, {joueur: true}) + bas];
  }
  if (S.type === 'differences') {                   // Mr. C : le double
    const mo = S.moteur || {}, src = i => `/img/${S.seq}/${i}`;
    if (S.phase === 'reponse') {
      const r = (mo.resultats || []).find(x => x.id === m.id) || {};
      return ['jm' + S.seq + JSON.stringify(S.classement), banniere(r.n === mo.n ? 'ok' : r.n ? '' : 'ko', `${r.n || 0} différence${r.n > 1 ? 's' : ''} sur ${mo.n}`,
        `<b>${esc(S.solution)}</b>`) + jumeauxHTML(S, src, {joueur: true}) + gainTel()];
    }
    const n = (mo.mes || []).length;
    return ['jm' + JSON.stringify([S.seq, mo.mes, mo.erreurs, mo.actif]), jumeauxHTML(S, src, {joueur: true, mes: mo.mes}) +
      `<p class="centre doux">${mo.actif ? `Touchez les différences (${n}/${mo.n}) · erreurs ${mo.erreurs}/${mo.max_erreurs}` : n === mo.n ? 'Toutes trouvées !' : 'Plus de touches'}</p>`];
  }
  if (S.type === 'contrat') {                       // Mitchum : les contrats et les questions éclair
    const mo = S.moteur || {}, src = i => `/img/${S.seq}/${i}`;
    if (S.phase === 'reponse') {
      const moi = (mo.joueurs || []).find(j => j.id === m.id) || {};
      return ['ct' + S.seq + JSON.stringify(S.classement), banniere(moi.perte ? 'ko' : 'ok', moi.perte ? `Les contrats ont éclaté sur vous (−${moi.perte})` : 'Vous vous en sortez',
        '') + gainTel()];
    }
    const q = mo.question;
    if (mo.mes_contrats && q) {
      const pen = mo.penalite > 0;
      const reste = Math.max(0, Math.ceil((mo.duree || 0) - (mo.ecoule || 0)));
      return ['ct-q' + JSON.stringify([S.seq, q.k, mo.mes_contrats, pen, reste]), `<div class="ct-alerte"><b>${mo.mes_contrats > 1 ? `${mo.mes_contrats} contrats` : 'Un contrat'} sur vous !</b><small> 💣 ${reste} s</small>` +
        `<p>${esc(q.q)}</p>${q.img !== null && q.img !== undefined ? `<img class="ct-img" src="${src(q.img)}" alt="">` : ''}</div>` +
        `<div class="ct-choix${pen ? ' bloque' : ''}">${q.choix.map((c, i) => `<button data-ctc="${i}"${pen ? ' disabled' : ''}>${esc(c)}</button>`).join('')}</div>` +
        (pen ? '<p class="centre doux">Pénalité…</p>' : '')];
    }
    return ['ct' + JSON.stringify([S.seq, (mo.joueurs || []).map(j => j.contrats)]), contratHTML(S, {joueur: true}) +
      '<p class="centre doux">Pas de contrat… pour l\'instant. Il peut vous tomber dessus !</p>'];
  }
  if (S.type === 'blackjack') {                     // Jean Renault : le blackjack
    const mo = S.moteur || {}, src = i => `/img/${S.seq}/${i}`;
    const mes = (mo.mes_cartes || []).map(c => carteBJ(c, src, 'tel')).join('');
    if (S.phase === 'reponse') {
      const r = (mo.resultats || []).find(x => x.id === m.id) || {};
      const T = {gagne: 'Vous battez Jean !', perd: 'Jean gagne', egal: 'Égalité', saute: 'Sauté : plus de 21'};
      return ['bj' + S.seq + JSON.stringify(S.classement), banniere(r.res === 'gagne' ? 'ok' : r.res === 'egal' ? '' : 'ko', T[r.res] || '',
        `Vous : <b>${totalBJ(r.total)}</b> · Jean : <b>${totalBJ(mo.jean_total)}</b>`) + `<div class="bj-main tel">${mes}</div>` + gainTel()];
    }
    if (mo.etape === 'mise') {
      if (!mo.actif) return ['bj-m' + S.seq + mo.ma_mise, message(`<span class="doux">Mise : <b>${mo.ma_mise || 'aucune'}</b></span>`)];
      return ['bj-mm' + S.seq, `<p class="centre doux">Votre mise ? Battez Jean : elle double. Perdez : elle part.</p>` +
        `<div class="rc-boutons">${(mo.mises_possibles || []).map(x => `<button class="mise-b" data-bjmise="${x}">${x ? x : 'Rien'}</button>`).join('')}</div>`];
    }
    return ['bj' + JSON.stringify([S.seq, mo.mes_cartes, mo.reste, mo.actif]), blackjackHTML(S, src, {joueur: true}) +
      `<p class="bj-vous">Vos cartes${mo.ma_mise ? ` · mise ${mo.ma_mise}` : ''}</p><div class="bj-main tel">${mes}</div>` +
      (mo.actif ? '<div class="bj-boutons"><button id="b-bj-carte" class="primaire">Carte !</button><button id="b-bj-reste">Je reste</button></div>'
        : '<p class="centre doux">Vous restez. Jean va jouer…</p>')];
  }
  if (S.type === 'pendule') {                       // Windom Earle : la pendule
    const mo = S.moteur || {}, src = i => `/img/${S.seq}/${i}`;
    const moi = (mo.pendules || []).find(j => j.id === m.id) || {};
    if (S.phase === 'reponse') {
      const r = (mo.resultats || []).find(x => x.id === m.id) || {};
      return ['pd' + S.seq + JSON.stringify(S.classement), banniere(r.mat ? 'ko' : 'ok', r.mat ? 'Échec et mat' : 'Dernier en lice !',
        `${r.coups || 0} film${r.coups > 1 ? 's' : ''} cité${r.coups > 1 ? 's' : ''}`) + gainTel()];
    }
    if (mo.mon_tour) return ['pd-moi' + JSON.stringify([S.seq, mo.n, Math.ceil(moi.reste || 0)]),
      `<p class="pd-a-vous">À vous ! <b>${Math.ceil(moi.reste || 0)} s</b></p>` + penduleHTML(S, src, {joueur: true})];
    const a = (mo.pendules || []).find(j => j.actif);
    return ['pd' + JSON.stringify([S.seq, mo.n, a && a.id, mo.mat]), penduleHTML(S, src, {joueur: true}) +
      `<p class="centre doux">${mo.mat ? '♚ Échec et mat : vous regardez la fin' : a ? `Au tour de <b style="color:${a.couleur}">${esc(a.nom)}</b> · votre pendule : ${Math.ceil(moi.reste || 0)} s` : ''}</p>`];
  }
  if (S.type === 'enveloppes') {                    // Dick Tremayne, Dwayne Milford : les enveloppes
    const mo = S.moteur || {}, src = i => `/img/${S.seq}/${i}`, q = mo.ma_q;
    if (S.phase === 'reponse') {
      const r = (mo.resultats || []).find(x => x.id === m.id) || {};
      return ['ce' + S.seq + JSON.stringify(S.classement), banniere(r.gain ? 'ok' : 'ko', r.gain ? `+${r.gain}` : 'Pas de points', '') + gainTel()];
    }
    if (!q) return ['ce-att' + S.seq, message('<span class="doux">La cérémonie commence…</span>')];
    const devoile = mo.ma_bonne !== null && mo.ma_bonne !== undefined;
    const items = q.items.map((it, i) => `<button class="ce-choix${mo.mon_choix === i ? ' choisi' : ''}${devoile && i === mo.ma_bonne ? ' bon' : ''}" ` +
      `data-ce="${i}"${mo.mon_choix !== null && mo.mon_choix !== undefined || !mo.actif ? ' disabled' : ''}><img src="${src(it.img)}" alt=""><span>${esc(it.txt)}</span></button>`).join('');
    const annees = q.annees ? `<p class="centre"><b>Bonus expert :</b> la cérémonie de quelle année ?</p><div class="ce-annees">${q.annees.map((a, i) =>
      `<button data-cea="${i}">${a}</button>`).join('')}</div>` : '';
    const ok = devoile && mo.mon_choix === mo.ma_bonne;
    return ['ce' + JSON.stringify([S.seq, mo.k, mo.mon_choix, mo.mon_annee, devoile, !!q.annees]),
      `<p class="ce-q">${esc(q.question)}${q.sous ? `<small>${esc(q.sous)}</small>` : ''}${mo.expert && q.mode === 'experts' ? '<em>expert</em>' : ''}</p>` +
      (devoile ? `<p class="centre ${ok ? 'ok' : 'err'}">${ok ? 'Bien vu !' : mo.mon_choix === null || mo.mon_choix === undefined ? 'Pas de réponse' : 'Raté'}</p>` : '') +
      `<div class="ce-grille${q.items.length > 4 ? ' serree' : ''}">${items}</div>${devoile ? '' : annees}`];
  }
  if (S.type === 'lumiere') {                       // Woodsman : la lumière au bout du doigt
    const mo = S.moteur || {};
    if (S.phase === 'reponse') return ['lu' + S.seq + JSON.stringify(S.classement), banniere(mo.trouve ? 'ok' : 'ko',
      mo.trouve ? 'C\'était lui !' : 'Raté', `<b>${esc(S.solution)}</b>`) + gainTel()];
    const notes = (mo.notes || []).map(n => `<li>${esc(n.texte)}</li>`).join('');
    if (mo.fini) return ['lu-f' + S.seq + mo.trouve, message(mo.trouve ? cooper(true, 'grand') + '<span class="ok">Trouvé !</span>'
      : '<span class="doux">Hors jeu pour cette manche</span>')];
    return ['lu' + JSON.stringify([S.seq, mo.actif, notes]), padLumiereHTML(mo) +
      `<button id="b-cest-lui" class="primaire large">C'est lui !</button>` +
      (notes ? `<ul class="lu-notes">${notes}</ul>` : '<p class="centre doux">Cherchez les indices avec votre lumière</p>')];
  }
  if (S.type === 'focus') {                         // Hank : les dominos (façon Focus)
    const mo = S.moteur || {}, src = i => `/img/${S.seq}/${i}`;
    if (focusSeq !== S.seq) { focusSeq = S.seq; focusCible = null; }
    if (S.phase === 'reponse') {
      const g = (mo.resultats || []).find(x => x.id === m.id) || {};
      return ['fo' + S.seq + JSON.stringify(S.classement), banniere(g.gain > 0 ? 'ok' : 'ko', g.gain > 0 ? `+${g.gain}` : 'Pas de points', '') +
        focusHTML(S, src, {joueur: true, moi: m.id}) + gainTel()];
    }
    const aide = mo.mon_tour ? `<b>À vous :</b> retirez un film proche du vôtre (${Math.ceil(mo.reste_tour || 0)} s)`
      : focusCible ? 'Touchez le film que vous lui prêtez' : 'Pour deviner : touchez un joueur, puis son film';
    return ['fo' + JSON.stringify([S.seq, mo, focusCible]), `<p class="fo-aide${mo.mon_tour ? ' tour' : ''}">${aide}</p>` +
      focusHTML(S, src, {joueur: true, moi: m.id, cible: focusCible})];
  }
  if (S.type === 'paires') return ['pr' + JSON.stringify([S.phase, S.seq, S.etat, S.moteur, pairesTel_, pairesSel, S.classement]), pairesTel()];
  if (S.type === 'brelan') return ['bj' + JSON.stringify([S.phase, S.seq, S.etat, S.moteur, ordreTel, S.classement]), brelanTel()];
  if (S.type === 'plusieurs' || S.type === 'paire') {     // Carl : les deux films ; Dougie : le jackpot
    const mo = S.moteur || {}, miens = mo.mes_films || [], n = mo.n || 2;
    if (S.phase === 'reponse') {
      const r = (mo.resultats || []).find(x => x.id === m.id) || {n: 0};
      return ['pa' + S.seq + JSON.stringify(S.classement), banniere(r.n === n ? 'ok' : r.n ? '' : 'ko',
        r.n === n ? (n === 2 ? 'Les deux !' : 'Tous trouvés !') : r.n ? `${r.n} sur ${n}` : 'Aucun', `<b>${esc(S.solution)}</b>`) + gainTel()];
    }
    if (!mo.actif) return ['pa-ok' + S.seq + miens.length, message(miens.length === n
      ? cooper(true, 'grand') + `<span class="ok">${n === 2 ? 'Les deux films !' : 'Les ' + n + ' films !'}</span>` : '<span class="doux">Plus d\'essais</span>')];
    return ['saisie', null];
  }
  if (S.type === 'duree') {
    const mo = S.moteur || {};
    if (S.phase === 'reponse') {
      const r = (mo.resultats || []).find(x => x.id === m.id);
      return ['du' + S.seq + JSON.stringify(S.classement), banniere(r && r.trouve ? 'ok' : r && r.gain ? '' : 'ko',
        r ? (r.trouve ? (r.ecart ? `Le plus proche (à ${hmJS(r.ecart)}) !` : 'Pile !') : `À ${hmJS(r.ecart)}`) : 'Pas de réponse', `<b>${esc(S.solution)}</b>` + (r ? ` · vous : ${r.reponse_hm || hmJS(r.reponse)}` : '')) + gainTel()];
    }
    return mo.ma_reponse ? ['du-ok' + S.seq, message(`<b>${mo.ma_reponse_hm || hmJS(mo.ma_reponse)}</b><br><span class="doux">Le plein est fait</span>`)] : ['saisie', null];
  }
  if (S.phase === 'reponse') return ['r' + S.seq + JSON.stringify(S.classement), reponseHTML()];
  if (S.type === 'nombre') return m.repondu ? ['n-ok' + S.seq, message(`<b>${m.reponse}</b>`)] : ['saisie', null];
  if (m.trouve) return ['ok' + S.seq, message(cooper(true, 'grand') + `<span class="ok">Trouvé</span><br><b>+${m.gain}</b>` + (m.serie > 1 ? `<br><small class="doux">série ×${m.serie}</small>` : ''))];
  if (S.mode === 'qcm') return m.repondu ? ['q-ok' + S.seq, message('<span class="doux">Réponse envoyée</span>')] : ['qcm' + S.seq, qcmHTML()];
  if (S.mode === 'buzzer') return m.moi_main ? ['saisie', null] : ['buzz' + JSON.stringify([S.main, m.bloque]), buzzHTML()];
  return m.essais > 0 ? ['saisie', null] : ['fini' + S.seq, message(cooper(false, 'grand') + '<span class="doux">Plus d\'essais</span>')];
}

function rendre() {
  montrer('v-jeu');
  const m = S.moi, enManche = S.phase === 'manche' || S.phase === 'reponse';
  document.documentElement.style.setProperty('--moi', m.couleur);
  maj($('#b-profil'), m.nom + m.couleur + m.avatar, `${rond(m)}<span>${esc(m.nom)}</span>`);
  $('#score').innerHTML = `<b>${m.score}</b> <span class="doux">${m.rang}<sup>${m.rang === 1 ? 'er' : 'e'}</sup>/${S.nb}</span>`;
  $('#manche').textContent = enManche ? `${S.manche}/${S.total}` : '';
  const ch = $('#chrono');
  ch.hidden = S.phase !== 'manche';
  if (S.phase === 'manche') {
    const r = restant(S);
    ch.firstElementChild.style.width = (100 * r / Math.max(1, S.duree)) + '%';
    ch.classList.toggle('urgent', r <= 5);
  }
  $('#titre-jeu').innerHTML = enManche ? `${S.pause ? '<span class="pause">pause</span>' : ''}<small>${esc(S.jeu_nom)}</small><b>${esc(S.jeu_titre || S.jeu_nom)}</b>` : '';
  if (S.seq !== vuSeq) {                         // nouvelle manche : on remet la saisie à zéro
    vuSeq = S.seq;
    selCase = -1;
    $('#saisie').value = '';
    $('#sugg').innerHTML = '';
    $('#retour').textContent = '';
  }
  document.body.dataset.jeu = enManche ? (S.jeu || '') : '';                      // décor du jeu (style.css)
  GRAINE_DECOR = S.seq || 0;
  const vis = $('#visuel'), avecVisuel = enManche && !['complice', 'choix', 'bingo', 'ordre', 'double', 'duels', 'brelan', 'paires', 'focus', 'lumiere', 'contrat', 'differences', 'code', 'blackjack', 'pendule', 'enveloppes'].includes(S.type);
  vis.hidden = !avecVisuel;
  if (avecVisuel) {
    maj(vis, `${S.phase}|${S.seq}|${S.revelation}|${JSON.stringify(S.etat)}|${S.vue === 'cassette' ? S.pause || !!S.main : ''}|${(S.moteur || {}).contrainte || ''}|${S.type === 'duree' || S.type === 'plusieurs' || S.type === 'rancon' ? JSON.stringify(S.moteur) : ''}`,
        enveloppe(() => visuelHTML(S, {largeur: vis.clientWidth || 340, tuile: 44, cols: 4, joueur: true, moi: S.moi.id})), S.seq);
    ajuster(vis, Math.round(window.innerHeight * 0.5));
  }
  let [cle, html] = vueZone();
  const zt = $('#zone-texte'), z = $('#zone'), mo = S.moteur || {};
  const apres = S.type === 'bingo';                 // Bingo : la saisie sous la grille, à côté de la case choisie
  if (apres !== (zt.compareDocumentPosition(z) === Node.DOCUMENT_POSITION_PRECEDING)) {
    if (apres) z.after(zt); else z.before(zt);
  }
  // saisie : réponse texte classique (html null), ou en plus de la zone pour Lucy (chrono) et Donna (bingo)
  const saisie = html === null || (S.phase === 'manche' && ((S.type === 'chrono' && mo.actif) ||
                                                              (S.type === 'bingo' && mo.actif && selCase >= 0) ||
                                                              (S.type === 'rancon' && mo.etape === 'marche' && mo.actif) ||
                                                              (S.type === 'code' && mo.donneur_moi && mo.actif) ||
                                                              (S.type === 'pendule' && mo.mon_tour && mo.actif)));
  zt.hidden = !saisie;
  z.hidden = html === null;
  if (saisie) {
    const annee = S.type === 'nombre' || S.type === 'duree';
    $('#saisie').placeholder = S.type === 'pendule' ? 'Un film lié au précédent…' : S.type === 'contrat' ? 'Un film…' : S.type === 'code' ? 'Votre indice (1 à 4 mots)' : S.type === 'duree' ? 'Durée : 140 = 1 h 40' : annee ? 'Année' : (S.jeu === 'filmo' || (S.etat || {}).acteur) ? 'Acteur' : S.type === 'chrono' ? 'Un film…'
      : S.type === 'bingo' ? (((mo.cases || [])[selCase] || {}).txt ? `Film : ${mo.cases[selCase].txt}` : 'Un film pour cette case…')
      : 'Titre';
    $('#saisie').inputMode = S.type === 'nombre' ? 'numeric' : S.type === 'duree' ? 'decimal' : 'text';
    $('#aide-saisie').textContent = annee || S.type === 'chrono' || S.type === 'bingo' ? ''
      : ['paire', 'plusieurs', 'rancon', 'contrat', 'code', 'differences', 'pendule'].includes(S.type) ? '' : S.mode === 'buzzer' ? 'À vous' : `${m.essais} essai${m.essais > 1 ? 's' : ''}`;
    if (S.type === 'duree') apercuDuree();
    if (S.type === 'paire' || S.type === 'plusieurs') {
      const miens = mo.mes_films || [], n = mo.n || 2;
      $('#aide-saisie').innerHTML = `<span class="paire-tel">${Array.from({length: n}, (_, k) => miens[k]
        ? `<b class="ok">✓ ${esc(miens[k])}</b>` : '<i>?</i>').join('')}</span>`;
    }
    if (!etaitSaisie) $('#saisie').focus();
  }
  if (html !== null) maj(z, cle, html, S.seq + S.type);
  etaitSaisie = saisie;
}

/* ================= boucle ================= */
async function boucle() {
  clearTimeout(minuteur);
  if (!pid) return ecranRejoindre();
  try {
    const s = await get('/api/etat?pid=' + encodeURIComponent(pid));
    if (s.inconnu) { pid = null; localStorage.removeItem('pid'); return ecranRejoindre(); }
    S = s;
    rendre();
  } catch (e) { console.error(e); }
  minuteur = setTimeout(boucle, S && S.phase === 'manche' && S.mode === 'buzzer' ? 300 : 600);
}
boucle();

/* Woodsman : le pavé. La position part au serveur au plus toutes les 120 ms (sans attendre la réponse). */
let luEnvoi = 0, luAttente = null;
document.addEventListener('pointerdown', ev => { if (ev.target.closest('#lu-pad')) { ev.target.closest('#lu-pad').setPointerCapture(ev.pointerId); luBouge(ev); } });
document.addEventListener('pointermove', ev => { if (ev.buttons && ev.target.closest && ev.target.closest('#lu-pad')) luBouge(ev); });
function luBouge(ev) {
  const pad = $('#lu-pad');
  if (!pad) return;
  ev.preventDefault();
  const b = pad.getBoundingClientRect();
  const x = Math.min(1, Math.max(0, (ev.clientX - b.left) / b.width)), y = Math.min(1, Math.max(0, (ev.clientY - b.top) / b.height));
  const moi = pad.querySelector('.lu-moi');
  if (moi) { moi.style.left = x * 100 + '%'; moi.style.top = y * 100 + '%'; }
  const envoyer = () => { luEnvoi = Date.now(); luAttente = null; post('/api/jouer', {pid, pos: [x, y]}).catch(() => {}); };
  clearTimeout(luAttente);
  if (Date.now() - luEnvoi > 120) envoyer(); else luAttente = setTimeout(envoyer, 120);
}
