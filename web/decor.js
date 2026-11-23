/* Décors des jeux : des objets dessinés (SVG) posés autour de la manche, jamais un fond qui dénote.
   Écran hôte : decorHTML(jeu) remplit le calque #j-decor (derrière la manche, dans les coins).
   Les deux écrans : casqueHTML (Cole), journalHTML (Laura), ROSE_BLEUE (Albert), registreHTML (Ben, Josie),
   jaugeHTML (Ed), tracklistHTML (James). */

/* Post-it et notes manuscrites */
const postit = (texte, cls = '', signe = '') =>
  `<div class="postit-d ${cls}"><span>${texte}</span>${signe ? `<small>${signe}</small>` : ''}</div>`;

/* Le décor de chaque jeu (écran hôte) : des objets (objets.js) dans les coins, derrière la manche. */
/* un objet du décor (dans un coin de l'écran hôte, là où rien ne le cache) */
const ob = (cls, svg) => `<div class="dc ${cls}">${svg}</div>`;
const DECORS = {
  complice: () => ob('d-bg petit', OBJ.bougie) + ob('d-bd petit', OBJ.bougie) + '<div class="dc d-hd ecrit-feu">Fire walk with me</div>',
  synopsis: () => `<div class="dc d-bd pelle-dc">${OBJ.pelle}<div class="pub-amp"><b>“Shovel your way out of the shit!”</b>` +
    '<small>— Dr. Amp</small></div></div>',
  persos: () => [[6, 12], [92, 18], [12, 70], [88, 64], [4, 40], [95, 42], [20, 90], [80, 92]]
    .map(([x, y], i) => `<div class="dc etoile-d" style="left:${x}%;top:${y}%;--i:${i}">${OBJ.etoile}</div>`).join(''),
  norma: () => ob('d-hd grand', OBJ.enseigne_rr) + ob('d-bg', OBJ.tasse),
  shelly: () => ob('d-bd grand', OBJ.tarte_entiere),
  donna: () => ob('d-hd grand', OBJ.one_eyed_jack) + jetonsHTML(),
  couleurs: () => ob('d-bg haut', OBJ.lampadaire) + ob('d-bd haut', OBJ.venus),
  pete: () => { const c = citation('pete'); return postit(`“${c[0]}”`, 'dc d-hd', '— ' + c[1]) + ob('d-bd grand', OBJ.percolateur); },
  ben: () => ob('d-bd', OBJ.cigare),
  josie: () => ob('d-hd petit-moyen', OBJ.bouton),
  ed: () => ob('d-bg grand', OBJ.pompe),
  phillip: () => ob('d-bd', OBJ.telephone_noir),
  jerry: () => ob('d-bd grand', OBJ.baguette),
};

/* Les vraies répliques de la série, tirées au hasard à chaque manche (sur un post-it, par-dessus l'interface). */
/* Les répliques de la série, en VO, tirées au hasard à chaque manche (le même tirage sur tous les écrans).
   Toutes ne sont pas des post-it : beaucoup sont intégrées à l'interface (sous-titre, néon, carton, griffonnage…). */
const REPLIQUES = {
  plans: [['There\'s a sort of evil out there. Something very, very strange in these old woods.', 'Sheriff Harry S. Truman'],
          ['It takes many forms, but it\'s been out there for as long as anyone can remember.', 'Sheriff Harry S. Truman'],
          ['Harry, I\'m going to let you in on a little secret. Every day, once a day, give yourself a present.', 'Agent Dale Cooper']],
  anagramme: [['Fix your hearts or die.', 'Gordon Cole'],
              ['We are like the dreamer who dreams and then lives inside the dream.', 'Monica Bellucci, in Gordon Cole\'s dream']],
  casting: [['Isn\'t it too dreamy?', 'Audrey Horne'], ['What story is that, Charlie?', 'Audrey Horne']],
  hawk: [['It\'s not about the bunny!', 'Deputy Hawk'],
         ['Hawk, something is missing and you have to find it.', 'The Log Lady'],
         ['We laid everything out, Hawk, and we can\'t find anything that\'s missing.', 'Deputy Andy Brennan']],
  geant: [['It is happening again.', 'The Giant'], ['The owls are not what they seem.', 'The Giant'],
          ['There\'s a man in a smiling bag.', 'The Giant'], ['Without chemicals, he points.', 'The Giant'],
          ['I will tell you three things.', 'The Giant']],
  loglady: [['My log has a message for you.', 'The Log Lady'], ['One day my log will have something to say about this.', 'The Log Lady']],
  filmo: [['I\'ll see you again in 25 years.', 'Laura Palmer'], ['I am dead. Yet I live.', 'Laura Palmer']],
  phillip: [['We\'re not gonna talk about Judy at all.', 'Phillip Jeffries'], ['Who do you think that is there?', 'Phillip Jeffries'],
            ['This is where you\'ll find Judy.', 'Phillip Jeffries']],
  jerry: [['You\'re not my foot!', 'Jerry Horne']],
  leo: [['New shoes.', 'Leo Johnson']],
  carl: [['I\'ve already gone places. I just want to stay where I am.', 'Carl Rodd']],
  couleurs: [['Let\'s rock.', 'The Man From Another Place'],
             ['Where we\'re from, the birds sing a pretty song, and there\'s always music in the air.', 'The Man From Another Place']],
  pete: [['She\'s dead. Wrapped in plastic.', 'Pete Martell'], ['There was a fish in the percolator!', 'Pete Martell'],
         ['Diane, never drink coffee that has been anywhere near a fish.', 'Agent Dale Cooper']],
  andy: [['We laid everything out, Hawk, and we can\'t find anything that\'s missing.', 'Deputy Andy Brennan']],
  dougie: [['Hellooo!', 'Dougie Jones'], ['Call for help.', 'Dougie Jones']],
  mike: [['Is it future, or is it past?', 'Mike, the one-armed man'],
         ['Through the darkness of future past, the magician longs to see.', 'Mike, the one-armed man'],
         ['Fire walk with me.', 'Mike, the one-armed man']],
  annie: [['The good Dale is in the Lodge, and he can\'t leave.', 'Annie Blackburn']],
};
let GRAINE_DECOR = 0;                                   // le numéro de manche : le même tirage sur tous les écrans
const hasard = (n, sel = 0) => n ? ((GRAINE_DECOR * 2654435761 + sel * 40503) >>> 0) % n : 0;
/* [texte, qui] tiré au hasard pour ce jeu (null s'il n'y en a pas) */
function citation(jeu) {
  const r = REPLIQUES[jeu];
  return r ? r[hasard(r.length, 7)] : null;
}
/* une réplique posée près de l'interface : post-it, fiche épinglée, griffonnage ou bulle */
function replique(jeu, pos = 'hg', style = 'postit') {
  const c = citation(jeu);
  if (!c) return '';
  return `<div class="colle postit-c c-${pos} st-${style}"><span>“${esc(c[0])}”</span><small>— ${esc(c[1])}</small></div>`;
}
/* Des objets posés PAR-DESSUS l'interface, à cheval sur ses bords, comme des post-it (jamais cachés). */
const col = (pos, svg, cls = '') => `<div class="colle c-${pos} ${cls}">${svg}</div>`;
const COLLES = {
  affiche: () => col('bd', OBJ.tasse, 'large') + col('hd', OBJ.dictaphone, 'etroit') +
    (hasard(2, 3) ? col('tache', OBJ.tache_cafe, 'tache') : '') + (hasard(3, 5) === 0 ? col('tache2', OBJ.tache_cafe, 'tache') : ''),
  plans: () => col('bg', OBJ.chapeau, 'large') + col('hd', OBJ.ecusson_sherif, 'moyen') + replique('plans', 'sous', 'fiche'),
  anagramme: () => col('d', OBJ.ecouteurs, 'moyen') + col('bd', OBJ.boitier, 'etroit'),
  hawk: () => col('hg', OBJ.ecusson_sherif, 'moyen') + col('d', OBJ.plume, 'plume') + replique('hawk', 'sous', 'griffe'),
  leland: () => '',
  bobby: () => col('hd', OBJ.insigne_deputy, 'etroit'),
  james: () => col('bg', OBJ.moto, 'moto'),
  geant: () => col('bg', OBJ.bague, 'moyen') + col('hd', OBJ.noeud_pap, 'moyen'),
  phillip: () => replique('phillip', 'bg', 'griffe'),
  jerry: () => replique('jerry', 'bd', 'bulle'),
  leo: () => replique('leo', 'sous', 'griffe'),
  andy: () => replique('andy', 'bd', 'postit'),
  annie: () => replique('annie', 'sous', 'fiche'),
  mike: () => replique('mike', 'bd', 'griffe'),
  maddy: () => '',
};
function colles(jeu) { return (COLLES[jeu] || (() => ''))(); }
function decorHTML(jeu) { return (DECORS[jeu] || (() => ''))(); }

/* Donna : des jetons vus de haut, étalés sur la table */
function jetonsHTML() {
  const pos = [[3, 70, '#b3121f'], [8, 82, '#141414'], [12, 74, '#1f6b3f'], [5, 90, '#2a5bd7'], [90, 78, '#b3121f'],
               [94, 88, '#141414'], [86, 90, '#f2c230'], [96, 70, '#1f6b3f']];
  return pos.map(([x, y, c], i) => `<span class="jeton-haut" style="left:${x}%;top:${y}%;--c:${c};--r:${i * 37}deg"></span>`).join('');
}

/* ---------------- objets qui portent la manche (les deux écrans) ---------------- */
const ROSE_BLEUE = OBJ.rose;

/* Cole's Hearing Aid : les lettres, et sous elles un vumètre qui bouge à peine (l'appareil auditif est posé à côté) */
function coleHTML(contenu) {
  const barres = Array.from({length: 28}, (_, i) => `<i style="--i:${i}"></i>`).join('');
  const c = citation('anagramme');
  return `<div class="cole" data-k="cole">${contenu}<div class="vumetre">${barres}</div>` +
    `<p class="cole-voix">“${esc(c[0])}” <small>— ${esc(c[1])}</small></p></div>`;
}

/* Laura's Secret Diary : la filmographie collée dans le journal intime, quatre films par page, le ruban par-dessus */
function journalHTML(cartes, total) {
  const moitie = Math.ceil(total / 2);
  const page = (deb, fin) => `<div class="jl-page"><div class="grille" style="--cols:2">${cartes.slice(deb, fin).join('')}</div></div>`;
  return `<div class="journal" data-k="journal"><div class="j-pages">` +
    `<div class="jl-titre">Journal intime — <i>Laura Palmer</i><small>“${esc(citation('filmo')[0])}”</small></div>` + page(0, moitie) + page(moitie, total) +
    `<span class="j-ruban"></span></div><span class="j-coeur">${OBJ.demicoeur}</span></div>`;
}

/* Cooper's Investigation : l'affiche dans un sachet de pièce à conviction ; dessous, toujours la réplique du café (VO).
   Les objets (tasse, dictaphone, taches de café renversé) sont posés par-dessus (decor.js : COLLES). */
function preuveHTML(img) {
  return `<figure class="preuve sachet" data-k="preuve"><div class="pv-photo">${img}</div>` +
    '<span class="pv-plastique"></span><span class="pv-zip"></span>' + (hasard(2, 11) ? '<span class="pv-tache"></span>' : '') +
    '<figcaption>« Black as midnight on a moonless night. »<small>— Agent Dale Cooper</small></figcaption></figure>';
}

/* Lucy's Hotline : le téléphone du bureau du shérif ; sur l'écran, à la place du numéro, la condition */
function lucyHTML(texte) {
  const touches = '123456789*0#'.split('').map(c => `<i>${c}</i>`).join('');  // clavier 3 × 4
  const combine = '<svg viewBox="0 0 800 110" preserveAspectRatio="none" aria-hidden="true"><defs><linearGradient id="tl-c" x1="0" y1="0" x2="0" y2="1">' +
    '<stop offset="0" stop-color="#b7425a"/><stop offset="1" stop-color="#6d1d2f"/></linearGradient></defs>' +
    '<path d="M30 70C20 40 50 10 110 10h580c60 0 90 30 80 60l-14 30c-6 10-20 10-40 10h-60c-20 0-30-8-28-24l4-22H178l4 22c2 16-8 24-28 24H94c-20 0-34 0-40-10z" fill="url(#tl-c)"/>' +
    '<path d="M120 22h560" stroke="#fff" stroke-opacity=".25" stroke-width="6" stroke-linecap="round"/></svg>';
  return `<div class="tel-lucy" data-k="tel"><div class="tl-combine">${combine}</div><div class="tl-corps">` +
    `<div class="tl-ecran"><small>LIGNE 1 · APPEL ENTRANT</small><b>${esc(texte)}</b></div>` +
    `<div class="tl-bas"><div class="tl-touches">${touches}</div><div class="tl-lignes"><i class="on"></i><i></i><i></i>` +
    '<span>— Lucy</span></div></div></div></div>';
}

/* The Log Lady's Rings : l'affiche posée près de la bûche ; à la réponse, l'année gravée au cœur des cernes */
function bucheHTML(v, src) {
  const e = v.etat || {}, rev = v.phase === 'reponse';
  const an = rev ? esc(String(v.solution || '').replace(/\D/g, '')) : '?';
  const cernes = Array.from({length: 9}, (_, i) => `<ellipse cx="100" cy="100" rx="${12 + i * 10}" ry="${11 + i * 9.4}"/>`).join('');
  return `<div class="buche-jeu" data-k="buche"><img class="bj-affiche" src="${src(e.img)}" alt="">` +
    `<div class="bj-tranche"><svg viewBox="0 0 200 200" aria-hidden="true"><defs><radialGradient id="bj-b" cx=".5" cy=".5" r=".55">` +
    '<stop offset="0" stop-color="#e9cf9c"/><stop offset=".85" stop-color="#c99f63"/><stop offset="1" stop-color="#7a5a32"/></radialGradient></defs>' +
    '<ellipse cx="100" cy="100" rx="98" ry="94" fill="#4a3220"/><ellipse cx="100" cy="100" rx="92" ry="88" fill="url(#bj-b)"/>' +
    `<g fill="none" stroke="#8d6a3c" stroke-width="1.6" opacity=".8">${cernes}</g><path d="M100 100l70-40" stroke="#6d4f2c" stroke-width="2" opacity=".6"/></svg>` +
    `<b class="bj-annee ${rev ? 'vue' : ''}">${an}</b></div></div><p class="bj-voix">« Ma bûche a un message pour vous. »</p>`;
}

/* Leo's New Shoes : les duels (deux affiches, la paire de chaussures neuves entre les deux). opt.cellule(k, i) -> {cls, badge} */
function duelsHTML(v, src, opt = {}) {
  const e = v.etat || {}, mo = v.moteur || {}, rev = v.phase === 'reponse' && mo.duels;
  return `<div class="duels" data-k="duels">` + (e.duels || []).map((du, k) => {
    const film = (f, i) => {
      const c = opt.cellule ? opt.cellule(k, i) || {} : {};
      let cls = c.cls || '', sous = '';
      if (rev) {
        const ok = mo.duels[k].bonne === i, votes = ((mo.votes || [])[k] || [[], []])[i] || [];
        cls += ok ? ' bonne' : ' terne';
        sous = `<em>${esc(mo.duels[k].valeurs[i])}</em>` +
          (votes.length && !opt.sansVotes ? `<div class="votes">${votes.map(j => puce(j, '', j.ok ? 'juste' : 'faux')).join('')}</div>` : '');
      }
      return `<figure class="duel-film ${cls}" data-duel="${k}" data-i="${i}" title="${esc(f.txt)}"><img src="${src(f.img)}" alt="${esc(f.txt)}">` +
        `${sous}${c.badge ? `<b class="badge">${c.badge}</b>` : ''}</figure>`;
    };
    return `<div class="duel" data-k="d${k}" style="--k:${k}"><div class="duel-q"><span>${esc(du.question)}</span></div>` +
      `<div class="duel-ring">${film(du.a, 0)}<span class="dl-chaussures">${OBJ.chaussures}<b>ou</b></span>${film(du.b, 1)}</div></div>`;
  }).join('') + '</div>';
}

/* The Giant's Three Clues : trois cartons numérotés, qui arrivent l'un après l'autre */
function geantHTML(e) {
  const ind = e.indices3 || [];
  const cache = t => esc(t).replace(/▒+/g, m => `<i class="cache">${m}</i>`);
  const rep = x => typeof x === 'string' ? {t: x, p: ''} : x || {};
  const cg = citation('geant');
  return `<div class="geant" data-k="geant"><p class="gt-voix">“${esc(cg[0])}” — ${esc(cg[1])}</p><ol class="gt-cartes">` +
    [0, 1, 2].map(i => {
      const r = rep(ind[i]);
      return `<li class="${ind[i] ? 'vue apparait' : 'cachee'}" data-k="g${i}"><span>${['I', 'II', 'III'][i]}</span>` +
        (ind[i] ? `<div><b>« ${cache(r.t)} »</b>${r.p ? `<small>« ${cache(r.p)} »</small>` : ''}</div>` : '') + '</li>';
    }).join('') + '</ol></div>';
}

/* The Log Lady's Knothole : l'image vue par le trou d'un nœud, qui se promène et s'agrandit (unités cqw : tout est
   proportionnel au cadre, le trou montre la bonne portion de l'image) */
function noeudHTML(v, src) {
  const e = v.etat || {}, t = e.trou || {x: 50, y: 50, r: 10, d: 1.6};
  if (v.phase === 'reponse') {
    return `<figure class="nd-reponse" data-k="ndr"><img src="${src(e.img || 0)}" alt=""></figure>`;   // le titre : dans le bandeau
  }
  return `<div class="noeud" data-k="noeud"><div class="nd-cadre">` +
    `<div class="nd-trou" style="--x:${t.x};--y:${t.y};--r:${t.r};--d:${t.d || 1.6}s;background-image:url('${src(e.img || 0)}')"></div></div>` +
    `<p class="nd-voix">“${esc(citation('loglady')[0])}” — ${esc(citation('loglady')[1])}</p></div>`;
}

/* Maddy's Look-Alike : la bande et son reflet, dans le miroir de la coiffeuse */
function sosieHTML(e, src) {
  return `<div class="sosie" data-k="sosie"><div class="ss-miroir"><img data-k="img" src="${src(e.img)}" alt="">` +
    '<i class="ss-axe"></i></div></div>';
}

/* Ben (budget + box-office) et Josie (le vrai et le faux) : un registre ouvert sur deux pages.
   pages : [{titre, items: [{txt, cls, badge, sous}], cle}] ; milieu : HTML posé sur la reliure. */
function registreHTML(classe, entete, pages, milieu) {
  return `<div class="registre ${classe}" data-k="registre">${entete}<div class="r-livre">` +
    pages.map((p, k) => `<div class="r-page ${k ? 'droite' : 'gauche'}"><h4>${p.titre}</h4><ol>` +
      p.items.map((it, i) => `<li class="r-ligne ${it.cls || ''}" data-page="${p.cle}" data-i="${i}">` +
        `<span class="r-case">${it.badge || ''}</span><span class="r-txt">${esc(it.txt)}</span>` +
        (it.sous ? `<em>${it.sous}</em>` : '') + (it.votes ? `<div class="r-votes">${it.votes}</div>` : '') + '</li>').join('') + '</ol></div>').join('') +
    (milieu ? `<div class="r-milieu">${milieu}</div>` : '') + '</div></div>';
}

/* Big Ed's Gas Farm : la jauge d'essence (vide = 1 h, plein = 4 h) et le compteur de la pompe */
function jaugeHTML(e, src, mo, rev) {
  const mini = 60, maxi = 240, angle = m => -90 + 180 * Math.max(0, Math.min(1, (m - mini) / (maxi - mini)));
  const vrai = rev && mo.duree ? mo.duree : null;
  const marques = rev ? (mo.resultats || []).filter(r => r.reponse).map(r =>
    `<g transform="rotate(${angle(r.reponse)} 150 150)"><path d="M150 40v-16" stroke="${r.couleur}" stroke-width="6" stroke-linecap="round"/></g>`).join('') : '';
  const grad = Array.from({length: 13}, (_, i) => `<path d="M150 34v${i % 2 ? 8 : 16}" transform="rotate(${-90 + 15 * i} 150 150)" stroke="#e8e2d0" stroke-width="${i % 2 ? 2 : 3}"/>`).join('');
  const aiguille = `<g class="aiguille" style="transform:rotate(${vrai ? angle(vrai) : -90}deg)"><path d="M150 150L150 46" stroke="#ff5a2c" stroke-width="5" stroke-linecap="round"/></g>`;
  const hh = vrai ? String(Math.floor(vrai / 60)) : '?', mm = vrai ? String(vrai % 60).padStart(2, '0') : '??';
  const compteur = `<b data-k="ch">${hh}</b><span>h</span>` + mm.split('').map((c, i) => `<b data-k="c${i}">${c}</b>`).join('');
  return `<div class="pompe-jeu" data-k="pompe"><div class="pj-film"><img src="${src(e.img)}" alt=""><b>${esc(e.titre || '')}</b><small>${esc(e.sous || '')}</small></div>` +
    `<div class="pj-cadran"><svg viewBox="0 0 300 175" aria-hidden="true"><path d="M30 150a120 120 0 0 1 240 0" fill="none" stroke="#2a2530" stroke-width="26"/>` +
    `<path d="M30 150a120 120 0 0 1 60-104" fill="none" stroke="#b71c2b" stroke-width="26"/>${grad}` +
    `<text x="22" y="172" fill="#e8e2d0" font-size="18" font-family="Georgia">E</text><text x="268" y="172" fill="#e8e2d0" font-size="18" font-family="Georgia">F</text>` +
    `<text x="150" y="128" text-anchor="middle" fill="#8b8397" font-size="11" font-family="Arial" letter-spacing="2">DURÉE</text>` +
    `${marques}${aiguille}<circle cx="150" cy="150" r="12" fill="#e8e2d0"/></svg>` +
    `<div class="pj-compteur">${compteur}<span>min</span></div></div></div>`;
}

/* James' Just You : la jaquette de cassette écrite à la main, la liste des morceaux de la bande originale */
function tracklistHTML(e, src) {
  const pistes = e.pistes || [], total = Math.max(e.total || 0, pistes.length);
  let h = '';
  for (let i = 0; i < total; i++) {
    h += i < pistes.length
      ? `<li class="apparait" data-k="p${i}"><span>${String(i + 1).padStart(2, '0')}</span>${esc(pistes[i]).replace(/▒+/g, m => `<i class="cache">${m}</i>`)}</li>`
      : `<li class="vide" data-k="v${i}"><span>${String(i + 1).padStart(2, '0')}</span></li>`;
  }
  const poch = e.pochette !== undefined && e.pochette !== null && src
    ? `<div class="jc-pochette apparait" data-k="poch"><img src="${src(e.pochette)}" alt=""><small>la pochette</small></div>` : '';
  return `<div class="jcard" data-k="jcard"><div class="jc-dos"><b>JUST YOU</b><small>pour Donna &amp; Maddy</small></div>` +
    `<div class="jc-face"><div class="jc-tete">Face A <small>${e.compo ? `musique de <b>${esc(e.compo)}</b>` : 'bande originale'}</small></div>` +
    `<ol>${h}</ol></div>${poch}</div>`;
}

/* Ben's Ghostwood Deal : le registre de Ben Horne. À gauche le budget, à droite le box-office, le film sur la reliure.
   opt.cellule(page, i) -> {cls, badge} (téléphone) ; opt.sansVotes : pas les pastilles des joueurs. */
function benHTML(v, src, opt = {}) {
  const e = v.etat || {}, mo = v.moteur || {}, rev = v.phase === 'reponse' && mo.bonnes;
  const page = (cle, titre) => ({cle, titre, items: (e[cle] || []).map((it, i) => {
    const c = opt.cellule ? opt.cellule(cle, i) || {} : {};
    if (rev) {
      const ok = i === mo.bonnes[cle], votes = ((mo.votes || {})[cle] || {})[i] || [];
      return {txt: it.txt, cls: ok ? 'bonne' : 'terne', badge: ok ? cooper(true, 'mini') : c.badge || '',
              sous: ok ? '' : esc(((mo.infos || {})[cle] || [])[i] || ''),
              votes: votes.length && !opt.sansVotes ? votes.map(j => puce(j, '', j.ok ? 'juste' : 'faux')).join('') : ''};
    }
    return {txt: it.txt, cls: (it.barre ? 'barre ' : '') + (c.cls || ''), badge: c.badge || ''};
  })});
  const f = e.film || {};
  const milieu = `<figure><img src="${src(f.img)}" alt=""><figcaption>${esc(f.txt || '')}<small>${esc(f.sous || '')}</small></figcaption></figure>`;
  const entete = `<div class="ben-tete"><div class="plaque"><b>BENJAMIN HORNE</b><small>GREAT NORTHERN · GHOSTWOOD</small></div></div>`;
  return registreHTML('ben', entete, [page('budget', 'Budget · ce qu\'il a coûté'), page('recettes', 'Box-office · ce qu\'il a rapporté')], milieu) +
    (rev ? '' : indicesHTML(e));
}

/* Josie's Double Ledger : le registre de la scierie Packard ; une des affirmations est le mensonge de Josie. */
function josieHTML(v, src, opt = {}) {
  const e = v.etat || {}, items = e.items || [], rev = v.phase === 'reponse' && v.choix, coupe = Math.ceil(items.length / 2);
  const ligne = (it, i) => {
    const c = opt.cellule ? opt.cellule(i) || {} : {};
    if (rev) {
      const faux = i === v.choix.bonne, votes = (v.choix.votes || {})[i] || [];
      return {txt: it.txt, cls: faux ? 'bonne mensonge' : 'terne', badge: faux ? cooper(true, 'mini') : '✓',
              sous: faux ? esc((v.choix.infos || [])[i] || '') : '',
              votes: votes.length && !opt.sansVotes ? votes.map(j => puce(j, '', j.ok ? 'juste' : 'faux')).join('') : ''};
    }
    return {txt: it.txt, cls: (it.barre ? 'barre ' : '') + (c.cls === 'verrou' ? 'sel' : c.cls || ''), badge: ''};
  };
  const f = e.film || {};
  const entete = `<div class="film-josie" data-k="film"><img src="${src(f.img)}" alt=""><div>` +
    `<div class="couv-josie"><b>REGISTRE</b><small>Packard Sawmill · comptes de l'année</small></div>` +
    `<b>${esc(f.txt || '')}</b><p class="csous">${rev ? esc(v.solution || '') : esc(e.question || '')}</p></div></div>`;
  const pages = [{cle: 'a', titre: 'Folio I', items: items.slice(0, coupe).map((it, i) => ligne(it, i))},
                 {cle: 'b', titre: 'Folio II', items: items.slice(coupe).map((it, i) => ligne(it, i + coupe))}];
  // l'indice de chaque ligne doit rester l'indice global de l'affirmation (data-g)
  let h = registreHTML('josie', entete, pages, ' ');
  let k = 0;
  h = h.replace(/data-page="([ab])" data-i="(\d+)"/g, () => `data-page="j" data-i="${k++}"`);
  return h + (rev ? '' : indicesHTML(e));
}

/* Catherine's Disguise : les titres étrangers, comme les cartes de visite de « Mr. Tojamura » */
function titresHTML(e) {
  const cartes = e.cartes || [], total = Math.max(e.total || 0, cartes.length);
  const via = l => (/^(a|e|i|o|u|é|hé)/i.test(l || '') ? "via l'" : 'via le ') + (l || '');
  /* le déguisement de « Mr. Tojamura », posé sur les cartes comme des post-it */
  const objets = [col('o-lunettes', OBJ.pince_nez), col('o-moustache', OBJ.moustache), col('o-scie', OBJ.lame)];
  let h = '';
  for (let i = 0; i < total; i++) {
    const c = cartes[i];
    h += c ? `<li class="meishi apparait" data-k="t${i}" style="--i:${i}"><small>${esc(via(c.langue))}<span>${c.etapes} langues</span></small>` +
             `<b>${esc(c.titre)}</b>${c.pays ? `<span class="tampon">${esc(c.pays)}</span>` : ''}${objets[i % 3]}</li>`
           : `<li class="meishi vide" data-k="t${i}"></li>`;
  }
  return `<div class="titres-deguises" data-k="titres"><ol>${h}</ol></div>`;
}

/* le nom à deviner, une case par lettre (les lettres données apparaissent dans leur case) */
function nomCases(nom) {
  return String(nom).split(' ').map(m => `<span>${m.split('').map(c => `<i>${c === '_' ? '' : esc(c)}</i>`).join('')}</span>`).join('');
}
/* Denise's Undercover : le porte-carte de la DEA, la carte d'identité se remplit */
function identiteHTML(e) {
  const f = e.fiche || [];
  const lignes = Array.from({length: Math.max(e.total || 0, f.length)}, (_, i) => f[i]
    ? `<div class="id-ligne apparait" data-k="l${i}"><small>${esc(f[i].k)}</small><b>${esc(f[i].v).replace(/▒+/g, m => `<i class="cache">${m}</i>`)}</b></div>`
    : `<div class="id-ligne vide" data-k="l${i}"><small>&nbsp;</small><b>&nbsp;</b></div>`).join('');
  return `<div class="porte-carte" data-k="porte"><div class="pc-gauche">${OBJ.insigne_dea}</div>` +
    `<div class="pc-carte"><div class="pc-tete">DRUG ENFORCEMENT ADMINISTRATION</div>` +
    `<div class="pc-corps"><div class="pc-photo">?</div><div class="pc-champs"><div class="id-ligne nom"><small>Nom</small>` +
    `<b class="id-nom">${nomCases(e.nom || '______ ______')}</b></div>${lignes}</div></div></div></div>`;
}

/* Carl's Fat Trout Trailers : la caravane ; sur l'écran hôte, la bande-annonce passe dans la fenêtre */
function caravaneHTML(e, src) {
  const ouv = new Set(e.lames || []), n = e.total || 12;
  const lames = Array.from({length: n}, (_, i) => `<i class="${ouv.has(i) ? 'ouverte' : ''}" style="--i:${i};--n:${n}"></i>`).join('');
  return `<div class="caravane" data-k="caravane"><svg class="cv-corps" viewBox="0 0 900 520" aria-hidden="true">` +
    '<defs><linearGradient id="cv-a" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#f3f5f7"/><stop offset=".55" stop-color="#b9c1c8"/>' +
    '<stop offset="1" stop-color="#7a838a"/></linearGradient></defs>' +
    '<ellipse cx="450" cy="506" rx="420" ry="12" fill="#000" opacity=".45"/>' +
    '<path d="M60 430V170C60 80 150 30 260 30h420c90 0 160 60 160 150v250z" fill="url(#cv-a)"/>' +
    '<path d="M60 384h780" stroke="#c8102e" stroke-width="10"/><path d="M60 402h780" stroke="#2a5bd7" stroke-width="6"/>' +
    '<rect x="96" y="110" width="124" height="300" rx="12" fill="#3a3f45"/><rect x="112" y="128" width="92" height="90" rx="8" fill="#1d2126"/>' +
    '<circle cx="200" cy="270" r="6" fill="#c9d1d6"/>' +
    '<rect x="262" y="52" width="536" height="316" rx="18" fill="#5c636a"/>' +
    '<circle cx="680" cy="450" r="50" fill="#141414"/><circle cx="680" cy="450" r="22" fill="#8a939a"/>' +
    '<path d="M840 430h40v14h-40z" fill="#5c636a"/><path d="M30 430h40v14H30z" fill="#5c636a"/></svg>' +
    `<div class="cv-fenetre"><img data-k="img" src="${src(e.img || 0)}" alt=""><div class="cv-store">${lames}</div></div>` +
    `<div class="cv-enseigne">${OBJ.enseigne_fat_trout}<span class="cv-plaque">“${esc(citation('carl')[0])}”<br>— ${esc(citation('carl')[1])}</span></div></div>`;
}

/* Phillip's Associates : la personne mystère au centre, ceux avec qui elle a le plus tourné autour, reliés par l'électricité */
const PLACES_PH = [[13, 21], [87, 21], [6, 56], [94, 56], [30, 79], [70, 79], [50, 14]];
function complicesHTML(e, src) {
  const cs = e.complices || [], total = Math.max(e.total || 0, cs.length);
  let fils = '', cartes = '';
  for (let i = 0; i < total; i++) {
    const [x, y] = PLACES_PH[i % PLACES_PH.length], c = cs[i];
    if (c) fils += `<path data-k="f${i}" pathLength="1" d="M50 50L${(50 + x) / 2 + (i % 2 ? 2 : -2)} ${(50 + y) / 2}L${x} ${y}"/>`;
    cartes += c
      ? `<figure class="ph-carte apparait${x > 55 ? ' ph-g' : ''}" data-k="c${i}" style="left:${x}%;top:${y}%">` +
        (c.img !== null && c.img !== undefined ? `<img src="${src(c.img)}" alt="">` : `<span class="ph-init">${initiale(c.nom)}</span>`) +
        `<figcaption><b>${esc(c.nom)}</b><small>${c.n} films ensemble · ${esc(c.metier)}</small>` +
        `${c.film && c.img_f === undefined ? `<em>dont « ${esc(c.film)} »</em>` : ''}</figcaption>` +
        `${c.img_f !== undefined ? `<img class="ph-affiche" src="${src(c.img_f)}" alt="" title="${esc(c.film || '')}">` : ''}</figure>`
      : `<figure class="ph-carte vide" data-k="c${i}" style="left:${x}%;top:${y}%"><span class="ph-init">·</span></figure>`;
  }
  return `<div class="complices" data-k="complices"><svg class="ph-fils" viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden="true">` +
    `${fils}</svg><div class="ph-centre"><span>?</span><small>${esc(e.metier || '')}</small></div>${cartes}</div>`;
}

/* Jerry's Trip : le titre en rébus phonétique. Chaque image se prononce comme un morceau du titre ; les mots sous les
   images arrivent en indice (etat.mots). Un morceau qui ne se dessine pas est écrit, comme un son. */
function rebusHTML(e) {
  return `<div class="rebus${e.mots ? ' avec-mots' : ''}" data-k="rebus">` + (e.rebus || []).map((x, i) => {
    const rot = [-3, 2, -1.5, 3, -2.5, 1.5, -1, 2.5][i % 8];
    if (x.t === 'emoji' || x.t === undefined && x.v) {
      return `<figure class="rb-carte${x.cadre ? ' cadre' : ''}" data-k="r${i}" style="--i:${i};--rot:${rot}deg">` +
        `<span class="rb-emoji${x.cadre ? ' rb-cadre' : ''}">${x.v}</span>` +
        `<figcaption>${e.mots && x.mot ? esc(x.mot) : '&nbsp;'}</figcaption></figure>`;
    }
    if (x.t === 'case') {                                                  // (ancien format)
      return `<span class="rb-son" data-k="r${i}">${'_'.repeat(Math.min(x.v, 12))}</span>`;
    }
    return `<figure class="rb-carte son" data-k="r${i}" style="--i:${i};--rot:${rot}deg"><span class="rb-son">${esc(x.v)}</span>` +
      '<figcaption>&nbsp;</figcaption></figure>';
  }).join('') + '</div>';
}

/* Audrey's Dance : le Roadhouse, sous l'enseigne au néon du Bang Bang Bar (« The », le revolver, BANG / BANG qui
   s'allument tour à tour, BAR). La cerise et la clé de la chambre 315 sont au milieu, entre les deux rangées de photos,
   avec une réplique d'Audrey (VO) ; les néons rouges grésillent de temps en temps. */
const NEON_BANG = '<svg class="bb-neon" viewBox="0 0 520 330" aria-hidden="true"><defs><filter id="bb-g" x="-30%" y="-30%" width="160%" height="160%">' +
  '<feGaussianBlur stdDeviation="3.2" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter></defs>' +
  '<g filter="url(#bb-g)" fill="none" stroke="#ffd9e0" stroke-width="5" stroke-linecap="round" stroke-linejoin="round">' +
  '<g class="bb-the"><text x="40" y="92" font-family="Brush Script MT,Segoe Script,cursive" font-size="86" fill="none" stroke-width="3">The</text></g>' +
  '<path class="bb-pistolet" d="M60 300l40-92c4-10 10-16 22-18l18-2c6-12 10-28 26-30l210-4c14 0 16 22 2 22l-10 0-2 16-122 6c-16 2-26 12-30 24' +
  'l-8 20c-4 10-14 14-24 12l-16-2-30 54z"/><path class="bb-pistolet" d="M150 216c10 0 18 8 18 18s-8 18-18 18"/>' +
  '<g class="bb-rayons"><path d="M368 160L500 108M372 196L504 186M370 232L500 262"/></g>' +
  '<g class="bb-bang b1"><text x="384" y="170" font-family="Arial Black,Arial,sans-serif" font-size="40" fill="#ffe3ea" stroke="none" transform="rotate(-12 430 160)">BANG</text></g>' +
  '<g class="bb-bang b2"><text x="384" y="226" font-family="Arial Black,Arial,sans-serif" font-size="40" fill="#ffe3ea" stroke="none" transform="rotate(-3 430 214)">BANG</text></g>' +
  '<g class="bb-bar"><text x="250" y="316" font-family="Arial Black,Arial,sans-serif" font-style="italic" font-size="74" fill="none" stroke-width="3">BAR</text></g>' +
  '</g></svg>';
function audreyHTML(cellules, cols) {
  const moitie = Math.ceil(cellules.length / 2), c = citation('casting');
  return `<div class="roadhouse" data-k="roadhouse">${NEON_BANG}<span class="bb-tube g"></span><span class="bb-tube d"></span>` +
    `<div class="grille rh-casting" style="--cols:${cols}">${cellules.slice(0, moitie).join('')}</div>` +
    `<div class="rh-milieu"><span class="rh-objet cerise">${OBJ.cerise_noeud}</span>` +
    `<p class="rh-voix">“${esc(c[0])}” <small>— ${esc(c[1])}</small></p><span class="rh-objet cle">${OBJ.cle_gn}</span></div>` +
    `<div class="grille rh-casting" style="--cols:${cols}">${cellules.slice(moitie).join('')}</div></div>`;
}

/* Dougie's Jackpots : la machine à sous du Silver Mustang. Trois rouleaux ; sur chacun défilent les affiches des cinq
   films (dans un ordre différent), très vite puis un peu moins (sans jamais devenir lent). opt.arret : la machine s'arrête. */
const VITESSES = [0.7, 0.95, 1.3, 1.7, 2.2, 2.8, 3.4], FLOUS = [5, 4, 3, 2.2, 1.6, 1.1, .7];
function jackpotHTML(e, src, opt = {}) {
  const bs = e.bandes || [], arret = !!opt.arret, v = arret ? VITESSES.length - 1 : Math.min(VITESSES.length - 1, e.vitesse || 0);
  const rouleau = (b, k) => {
    const imgs = b.map(i => `<img src="${src(i)}" alt="">`).join('');
    return `<div class="jp-rouleau" data-k="r${k}"><div class="jp-bande${k % 2 ? ' inverse' : ''}" ` +
      `style="--t:${(VITESSES[v] * (1 + k * 0.13)).toFixed(2)}s;--f:${FLOUS[v]}px;--d:${-k * 0.37}s">${imgs}${imgs}</div></div>`;
  };
  return `<div class="jackpot trois${arret ? ' arrete' : ''}" data-k="jackpot"><div class="jp-fronton"><span class="jp-titre">SILVER MUSTANG</span>` +
    `<span class="jp-ampoules">${'<i></i>'.repeat(12)}</span></div>` +
    `<div class="jp-vitre">${bs.map(rouleau).join('')}</div>` +
    `<div class="jp-bas"><span class="jp-fente"></span></div><span class="jp-levier"><i></i></span>` +
    `<p class="jp-voix">“Hellooo!” <small>— Dougie Jones</small></p></div>`;
}


/* Annie's Miss Twin Peaks : sept écharpes de candidates, chacune avec deux mots qui évoquent un film ;
   le film qui n'a pas d'écharpe est l'absent. */
function echarpesHTML(e) {
  const c = ['#c8102e', '#2a5bd7', '#1f6b3f', '#8a6ae6', '#d9822b', '#b3121f', '#1d8a8a'];
  return `<div class="miss" data-k="miss"><div class="miss-tete"><span class="miss-couronne">${OBJ.couronne_miss}</span>` +
    `<b>Miss Twin Peaks</b></div><div class="echarpes">` + (e.echarpes || []).map((t, i) =>
      `<span class="echarpe" style="--c:${c[i % c.length]};--r:${[-1.2, 1, -.6, 1.2, -.9, .7, -.4][i % 7]}deg;--i:${i}"><i>${i + 1}</i>${esc(t)}</span>`).join('') +
    '</div></div>';
}

/* ===================================================================== v9 : Mike, Windom Earle, Harold Smith, Jacques Renault */

/* Windom Earle's Chessboard : 64 lettres sur l'échiquier ; le titre se lit en sauts de cavalier, case après case. */
function cavalierHTML(e) {
  const g = e.grille || [], ch = e.chemin || [], n = e.n || 0;
  const rang = Object.fromEntries(ch.map((c, k) => [c, k]));
  const cases = g.map((l, c) => {
    const k = rang[c], lu = k !== undefined, der = lu && k === ch.length - 1;
    return `<span class="cv-case ${((c >> 3) + c) % 2 ? 'n' : 'b'}${lu ? ' lu' : ''}${der ? ' der' : ''}" data-k="c${c}">` +
      `${esc(l)}${lu ? `<small>${k + 1}</small>` : ''}${der ? `<i class="cv-cheval">${e.piece || '♞'}</i>` : ''}</span>`;
  }).join('');
  const pts = ch.map(c => `${(c % 8) * 12.5 + 6.25},${(c >> 3) * 12.5 + 6.25}`).join(' ');
  const lu = ch.map(c => g[c]).join('');
  const bande = Array.from({length: n}, (_, i) => i < lu.length ? `<b>${esc(lu[i])}</b>` : '<i></i>').join('');
  return `<div class="cavalier" data-k="cavalier"><div class="cv-plateau" data-k="plateau"><div class="cv-cases">${cases}</div>` +
    `<svg class="cv-trace" viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden="true"><polyline points="${pts}"/></svg></div>` +
    `<div class="cv-droite"><p class="cv-citation">“The king must die.” <small>— Windom Earle</small></p>` +
    `<div class="cv-bande" data-k="bande">${bande}</div><p class="frise-aide">La pièce posée joue la lettre suivante</p></div></div>`;
}

/* Harold's Orchids : cinq pétales autour du cœur de l'orchidée, chacun un détail de l'affiche vu à la loupe. */
function orchideeHTML(e, src) {
  const ps = e.petales || [];
  const petales = Array.from({length: 5}, (_, k) => {
    const id = ps[k];
    return `<div class="or-petale${id === undefined ? ' ferme' : ''}" style="--a:${k * 72 - 90}deg;--i:${k}" data-k="pt${k}">` +
      (id !== undefined ? `<img src="${src(id)}" alt="" style="--z:${e.zoom || 0}">` : '') +
      (id !== undefined && (e.sources || [])[k] ? `<small class="or-etiq">${esc(e.sources[k])}</small>` : '') + '</div>';
  }).join('');
  return `<div class="orchidee" data-k="orchidee"><svg class="or-tige" viewBox="0 0 200 300" aria-hidden="true">` +
    `<path d="M100 150C96 200 108 250 92 300" fill="none" stroke="#5f8a3a" stroke-width="7" stroke-linecap="round"/>` +
    `<path d="M98 232c-40-6-70 8-88 34 34 4 64-6 88-34zM102 262c34-14 64-8 86 12-30 10-60 6-86-12z" fill="#3f6b2a"/></svg>` +
    `${petales}<div class="or-coeur">${OBJ.coeur_orchidee || ''}</div>` +
    `<p class="or-note">Living Novel <small>— H.S.</small></p></div>`;
}

/* Jacques Renault's Card Table : cinq cartes distribuées (les affiches) ; les cartes pas encore données sont de dos.
   opt.cellule(i) -> {cls, badge} (sélection du joueur, résultat). */
function brelanHTML(v, src, opt = {}) {
  const e = v.etat || {}, items = e.items || [], mo = v.moteur || {};
  const rev = v.phase === 'reponse' && mo.bons, n = rev ? items.length : e.donnes ?? items.length;
  const coins = ['A♠', 'K♥', 'Q♣', 'J♦', '10♠'];
  const cartes = items.map((it, i) => {
    const c = opt.cellule ? opt.cellule(i) || {} : {};
    const bon = rev && mo.bons.includes(i);
    if (i >= n) return `<figure class="bj-carte dos" data-k="c${i}" style="--i:${i};--y:${Math.abs(i - 2) * 8}px"><div class="bj-face"></div></figure>`;
    return `<figure class="bj-carte ${c.cls || ''}${rev ? (bon ? ' bon' : ' terne') : ''}" data-i="${i}" data-k="c${i}" style="--i:${i};--y:${Math.abs(i - 2) * 8}px">` +
      `<div class="bj-face"><span class="bj-cadre"><img src="${src(it.img)}" alt=""></span><span class="bj-coin">${coins[i].replace(/(.)$/, '<i>$1</i>')}</span>` +
      `<span class="bj-coin bas">${coins[i].replace(/(.)$/, '<i>$1</i>')}</span>${c.badge ? `<b class="badge-ordre">${c.badge}</b>` : ''}</div>` +
      `<figcaption>${esc(it.txt)}</figcaption></figure>`;
  }).join('');
  const bandeau = rev ? `<p class="bj-commun"><small>${esc(mo.metier || '')}</small><b>${esc(mo.commun || '')}</b></p>`
    : '<p class="frise-aide">Trois cartes ont quelqu\'un en commun : lesquelles ?</p>';
  return `<div class="brelan" data-k="brelan"><div class="bj-table">${cartes}</div>` +
    `<div class="bj-bas"><span class="bj-jetons" aria-hidden="true">${OBJ.jetons || ''}</span>${bandeau}` +
    `<span class="bj-jetons d" aria-hidden="true">${OBJ.jetons || ''}</span></div></div>` + (rev ? '' : indicesHTML(e));
}

/* Mike's Shoe Samples : la valise d'échantillons ; quatre boîtes à chaussures (les personnages), quatre affiches.
   opt.affect[k] : l'affiche donnée à la boîte k (ou undefined) ; opt.sel : la boîte choisie ; opt.actif : touchable ;
   opt.justes[k] : résultat du joueur. À la réponse, chaque boîte s'ouvre sur la bonne affiche. */
const COULEURS_PAIRES = ['#e0a526', '#3a86ff', '#e0457b', '#2bb673'];
function pairesHTML(v, src, opt = {}) {
  const e = v.etat || {}, bx = e.boites || [], items = e.items || [], mo = v.moteur || {};
  const rev = v.phase === 'reponse' && mo.ordre, affect = opt.affect || [];
  const boites = bx.map((b, k) => {
    const f = rev ? mo.ordre[k] : affect[k];
    const j = opt.justes ? opt.justes[k] : null;
    return `<figure class="mk-boite${opt.sel === k ? ' sel' : ''}${opt.actif ? ' actif' : ''}${rev ? ' ouverte' : ''}${j === true ? ' juste' : j === false ? ' faux' : ''}" ` +
      `data-b="${k}" data-k="b${k}" style="--c:${COULEURS_PAIRES[k]}"><span class="mk-couvercle"></span>` +
      `<span class="mk-num">${k + 1}</span>` +
      (rev && f !== undefined ? `<img class="mk-dedans" src="${src(items[f].img)}" alt="">` : '') +
      `<figcaption><b>${esc(b.nom)}</b><small>${b.acteur ? 'joué par ' + esc(b.acteur) : '&nbsp;'}</small></figcaption></figure>`;
  }).join('');
  const affiches = items.map((it, i) => {
    const k = rev ? mo.ordre.indexOf(i) : affect.indexOf(i);
    return `<figure class="mk-affiche-p${opt.actif && opt.sel !== undefined && opt.sel >= 0 ? ' actif' : ''}${k >= 0 ? ' prise' : ''}" ` +
      `data-f="${i}" data-k="f${i}" style="--c:${k >= 0 ? COULEURS_PAIRES[k] : 'transparent'}"><img src="${src(it.img)}" alt="">` +
      `${k >= 0 ? `<b class="mk-badge">${k + 1}</b>` : ''}<figcaption>${esc(it.txt)}</figcaption></figure>`;
  }).join('');
  return `<div class="paires-mike" data-k="paires"><div class="mk-valise"><span class="mk-poignee"></span>${boites}</div>` +
    `<p class="frise-aide">${rev ? 'Les bonnes paires' : 'Les chaussures vont par paires : à chaque personnage, son film'}</p>` +
    `<div class="mk-affiches">${affiches}</div></div>` + (rev ? '' : indicesHTML(e));
}

/* Hank's Dominoes (façon Focus) : la grille de dominos-affiches, les joueurs et leurs indices (dominos retirés).
   opt.joueur : téléphone ; opt.cible : joueur visé pour une devinette ; cellules touchables selon le mode. */
function focusHTML(v, src, opt = {}) {
  const mo = v.moteur || {}, rev = v.phase === 'reponse', cases = mo.cases || [], js = mo.joueurs || [];
  const proprio = {};
  js.forEach(j => { if (j.film !== null && j.film !== undefined) proprio[j.film] = j; });
  const mes = mo.mes_devines || {};
  const devine = {};
  Object.entries(mes).forEach(([c, x]) => { (devine[x.i] = devine[x.i] || []).push({c, ok: x.ok}); });
  const nomDe = id => (js.find(j => j.id === id) || {}).nom || '?';
  const modeRetirer = opt.joueur && mo.mon_tour && mo.actif, modeDevine = opt.joueur && opt.cible && mo.actif;
  const chips = js.map(j => {
    const peut = opt.joueur && mo.actif && j.id !== opt.moi && !j.devoile && !mes[j.id];
    return `<button class="fo-joueur${j.actif && !rev ? ' tour' : ''}${opt.cible === j.id ? ' sel' : ''}${peut ? ' cible-ok' : ''}${j.devoile ? ' devoile' : ''}" ` +
      `data-cible="${esc(j.id)}" style="--c:${j.couleur}" ${peut ? '' : 'tabindex="-1"'}>${esc(j.nom)}<small>${j.indices} indice${j.indices > 1 ? 's' : ''}</small>` +
      (mes[j.id] ? `<b class="${mes[j.id].ok ? 'ok' : 'ko'}">${mes[j.id].ok ? '✓' : '✗'}</b>` : '') +
      (j.actif && !rev ? `<i class="fo-temps" style="--p:${Math.max(0, Math.min(1, (mo.reste_tour || 0) / (mo.dur_tour || 1)))}"></i>` : '') + '</button>';
  }).join('');
  const grille = cases.map(c => {
    const mien = opt.joueur && c.img === mo.mon_film, pr = proprio[c.img];
    const touche = !c.retire && ((modeRetirer && !mien) || modeDevine);
    const marques = (devine[c.img] || []).map(x => `<b class="fo-marque ${x.ok ? 'ok' : 'ko'}">${esc(nomDe(x.c))}</b>`).join('');
    return `<figure class="fo-domino${c.retire ? ' retire' : ''}${mien ? ' mien' : ''}${touche ? ' actif' : ''}${pr ? ' secret' : ''}" data-f="${c.img}" ` +
      `data-k="f${c.img}" style="--c:${c.par ? c.par.couleur : 'transparent'}"><img src="${src(c.img)}" alt="">` +
      `<figcaption>${esc(c.txt)}</figcaption>${c.retire && c.par ? `<span class="fo-par">${esc(c.par.nom)}</span>` : ''}` +
      `${mien ? '<span class="fo-mien">Mon film</span>' : ''}${pr ? `<span class="fo-proprio" style="--c:${pr.couleur}">${esc(pr.nom)}</span>` : ''}${marques}</figure>`;
  }).join('');
  const n = cases.length, cols = opt.joueur ? (n <= 10 ? 4 : 5) : Math.min(8, Math.ceil(n / (n > 16 ? 3 : 2)));
  const pd = mo.perdant && mo.perdant.qui ? `<p class="fo-perdant">${esc(mo.perdant.qui.nom)} a retiré le film de ` +
    `${esc((mo.perdant.victime || {}).nom || '?')} : perdu, la manche s'arrête !</p>` : '';
  return `<div class="focus" data-k="focus">${pd}<div class="fo-joueurs">${chips}</div>` +
    `<div class="fo-grille" style="--cols:${cols}">${grille}</div></div>`;
}

/* Sarah Palmer's Visions : la vision passe dans le vieux téléviseur du salon des Palmer ; avant et après, le cheval
   blanc. Chaque écran joue la vision lui-même (horloge locale calée sur le chrono de la manche), si bien qu'aucune
   affiche n'est sautée, même à 0,1 s. */
const VISION = {seq: null, base: 0};
function caleVision(v) {                       // appelée à chaque état reçu (hôte et téléphones)
  if (!v || v.jeu !== 'sarah' || v.phase !== 'manche') return;
  const base = performance.now() - (v.ecoule || 0) * 1000;
  if (VISION.seq !== v.seq) { VISION.seq = v.seq; VISION.base = base; } else VISION.base = Math.min(VISION.base, base);
}
function visionHTML(e, src) {
  const seq = e.sequence || [];
  const imgs = [...new Set(seq)].map(i => `<img class="vi-flash" data-i="${i}" src="${src(i)}" alt="" hidden>`).join('');
  return `<div class="vision" data-k="vision"><div class="vi-tele"><div class="vi-ecran" data-sequence="${seq.join(',')}" ` +
    `data-t0="${e.t0 || 0}" data-pas="${e.pas || 0.8}" data-mods="${(e.mods || []).join(',')}">${imgs}<span class="vi-cheval">${OBJ.cheval_blanc}</span>` +
    `<span class="vi-neige"></span></div><span class="vi-boutons"><i></i><i></i></span></div>` +
    `<p class="frise-aide">${seq.length ? 'Regardez bien…' : 'La vision s\'efface…'}</p></div>`;
}
(function animerVision() {
  for (const ecran of document.querySelectorAll('.vi-ecran')) {
    const seq = (ecran.dataset.sequence || '').split(',').filter(x => x !== ''), pas = Number(ecran.dataset.pas) || 0.8;
    const t = (performance.now() - VISION.base) / 1000 - Number(ecran.dataset.t0 || 0);
    const k = seq.length && t >= 0 ? Math.floor(t / pas) : -1;
    const cur = k >= 0 && k < seq.length ? seq[k] : null;
    if (ecran.dataset.cur === String(cur)) continue;
    ecran.dataset.cur = String(cur);
    const mod = cur !== null ? ((ecran.dataset.mods || '').split(',')[k] || '') : '';
    ecran.querySelectorAll('.vi-flash').forEach(im => { im.hidden = im.dataset.i !== cur; if (!im.hidden) im.dataset.m = mod; });
    ecran.querySelector('.vi-cheval').hidden = cur !== null;
  }
  requestAnimationFrame(animerVision);
})();

/* Jean Renault's Ransom : la lettre de rançon en lettres découpées, puis les photos de l'otage (images du film). */
function lettresDecoupees(t) {
  const fonds = ['#f4efe2', '#ffd24a', '#111', '#c8102e', '#e8e0ff', '#fff'], encres = ['#111', '#111', '#f4efe2', '#fff', '#2a1f45', '#c8102e'];
  const polices = ['Georgia,serif', 'Impact,sans-serif', '"Courier New",monospace', 'var(--sans)', '"Times New Roman",serif'];
  return [...t].map((c, i) => c === ' ' ? '<i class="rc-espace"></i>' : (() => {
    const k = (i * 7 + c.charCodeAt(0)) % fonds.length;
    return `<b style="background:${fonds[k]};color:${encres[k]};font-family:${polices[(i * 3 + c.charCodeAt(0)) % polices.length]};` +
      `--r:${((i * 37) % 11) - 5}deg">${esc(c)}</b>`;
  })()).join('');
}
function ranconHTML(v, src) {
  const e = v.etat || {}, mo = v.moteur || {}, et = e.etape || mo.etape;
  const infos = (e.infos || []).map(i => `<span class="rc-info"><small>${esc(i.nom)}</small><b>${esc(i.texte)}</b></span>`).join('');
  const joueurs = (mo.joueurs || []).map(j => `<span class="rc-mise${j.libere ? ' libere' : ''}" style="--c:${j.couleur}">${esc(j.nom)} ` +
    `<b>${j.mise !== null && j.mise !== undefined ? j.mise : j.a_mise ? '✓' : '…'}</b>` +
    (et !== 'mise' ? `<small>${j.achats} preuve${j.achats > 1 ? 's' : ''}</small>` : '') + '</span>').join('');
  return `<div class="rancon${et === 'mise' ? '' : ' marche-ouvert'}" data-k="rancon"><div class="rc-lettre" data-k="lettre">` +
    `<p class="rc-titre">${lettresDecoupees(et === 'mise' ? 'RANÇON' : 'MARCHÉ NOIR')}</p>` +
    `<p class="rc-otage">J'ai un film en otage.</p><div class="rc-infos">${infos}</div>` +
    `<p class="rc-consigne">${et === 'mise' ? 'Combien misez-vous sur sa libération ?' : 'Les preuves s\'achètent en secret, sur vos téléphones.'}</p></div>` +
    `<div class="rc-mises">${joueurs}</div></div>`;
}

/* The Woodsman's Light (Got a light?) : l'écran dans le noir ; seules les lumières des joueurs éclairent les affiches
   et les indices cachés. Les indices trouvés restent allumés. */
function lumiereHTML(v, src) {
  const e = v.etat || {}, mo = v.moteur || {}, rev = v.phase === 'reponse';
  const r = (mo.rayon || 0.06) * 100, w = (e.w || 0.064) * 100, h = (e.h || 0.17) * 100;
  const affiches = (e.affiches || []).map(a => {
    const bon = rev && a.img === mo.bonne, faux = rev && Object.values(mo.elimines || {}).includes(a.img);
    return `<img class="lu-aff${bon ? ' bon' : ''}${faux ? ' faux' : ''}" src="${src(a.img)}" alt="" ` +
      `style="left:${a.x * 100 - w / 2}%;top:${a.y * 100 - h / 2}%;width:${w}%;height:${h}%;--r:${a.r}deg">`;
  }).join('');
  const notes = (mo.toutes_notes || mo.notes || []).map(n => `<span class="lu-note${n.vu || rev ? ' vue' : ''}" ` +
    `style="left:${n.x * 100}%;top:${n.y * 100}%;--r:${n.r}deg">${esc(n.texte)}</span>`).join('');
  const lumieres = mo.lumieres || [];
  const masque = rev ? 'none' : lumieres.length ? lumieres.map(l => `radial-gradient(circle ${r}cqw at ${l.x * 100}% ${l.y * 100}%, #000 0 ${r * .62}cqw, transparent ${r}cqw)`).join(',')
    : 'linear-gradient(transparent,transparent)';
  const vues = (mo.toutes_notes || []).filter(n => n.vu).map(n => `<span class="lu-note vue fixe" ` +
    `style="left:${n.x * 100}%;top:${n.y * 100}%;--r:${n.r}deg">${esc(n.texte)}</span>`).join('');
  const halos = rev ? '' : lumieres.map(l => `<i class="lu-halo" style="left:${l.x * 100}%;top:${l.y * 100}%;--c:${l.couleur};--d:${2 * r}cqw"><b>${esc(l.nom)}</b></i>`).join('');
  return `<div class="lumiere" data-k="lumiere"><div class="lu-plateau"><div class="lu-scene" style="-webkit-mask-image:${masque};mask-image:${masque}">` +
    `${affiches}${notes}</div>${vues}${halos}</div><p class="frise-aide">“Got a light?” — trouvez le film des indices</p></div>`;
}

/* Le pavé du téléphone : le doigt promène la lumière (position envoyée au serveur, quelques fois par seconde). */
function padLumiereHTML(mo) {
  const p = mo.ma_pos || [0.5, 0.5];
  return `<div class="lu-pad" id="lu-pad"><i class="lu-moi" style="left:${p[0] * 100}%;top:${p[1] * 100}%"></i>` +
    '<span>Glissez le doigt pour éclairer l\'écran</span></div>';
}

/* The Mitchum Brothers' Contract : les joueurs autour de la table du Silver Mustang ; les contrats (enveloppes) passent
   de main en main, toujours dans le même sens ; au centre, la mèche de la minuterie. */
function contratHTML(v, opt = {}) {
  const mo = v.moteur || {}, rev = v.phase === 'reponse', js = mo.joueurs || [], n = js.length || 1;
  const places = js.map((j, k) => {
    const a = -Math.PI / 2 + 2 * Math.PI * k / n, x = 50 + 41 * Math.cos(a), y = 50 + 38 * Math.sin(a);
    const env = `<span class="ct-enveloppe">${OBJ.enveloppe_contrat}</span>`.repeat(Math.min(3, j.contrats || 0));
    return `<div class="ct-joueur${j.contrats && !rev ? ' porteur' : ''}${rev && j.perte ? ' victime' : ''}" style="left:${x}%;top:${y}%;--c:${j.couleur}" data-k="j${esc(j.id)}">` +
      `${env ? `<span class="ct-envs">${env}</span>` : ''}<b>${esc(j.nom)}</b>` +
      `${rev && j.perte ? `<small>−${j.perte}</small>` : j.passes ? `<small>${j.passes} refilé${j.passes > 1 ? 's' : ''}</small>` : ''}</div>`;
  }).join('');
  const p = Math.max(0, Math.min(1, (mo.ecoule || 0) / (mo.duree || 1)));
  const centre = rev ? `<p class="ct-boum">BOUM !</p>`
    : `<small>Répondez juste pour refiler votre contrat</small><div class="ct-meche" style="--p:${p.toFixed(3)}"><i></i><b>💥</b></div>` +
      `<p class="ct-reste">${Math.max(0, Math.ceil((mo.duree || 0) - (mo.ecoule || 0)))} s</p>`;
  const journal = (mo.journal || []).slice().reverse().map(x => `<li><b>${esc(x.de)}</b> → ${esc(x.a)}</li>`).join('');
  return `<div class="contrat${opt.joueur ? ' tel' : ''}" data-k="contrat"><div class="ct-table"><span class="ct-sens">↻</span>` +
    `<div class="ct-centre">${centre}</div>${places}</div>${journal && !opt.joueur ? `<ul class="ct-journal">${journal}</ul>` : ''}</div>`;
}

/* Mr. C's Doppelganger : l'affiche et son double trafiqué, côte à côte. opt.mes : les différences trouvées par ce
   joueur ; à la réponse, toutes les différences sont entourées. */
function jumeauxHTML(v, src, opt = {}) {
  const mo = v.moteur || {}, rev = v.phase === 'reponse' && mo.diffs;
  const cercles = (rev ? mo.diffs : opt.mes || []).map(d => `<i class="jm-cercle" style="left:${d.x * 100}%;top:${d.y * 100}%;width:${d.r * 200}%"></i>`).join('');
  const face = (i, nom) => `<figure class="jm-face" data-face="${i}"><div class="jm-cadre"><img src="${src(i)}" alt="" draggable="false">${cercles}</div>` +
    `<figcaption>${nom}</figcaption></figure>`;
  const compte = opt.joueur ? '' : `<div class="rc-mises">${(mo.compte || []).map(j => `<span class="rc-mise" style="--c:${j.couleur}">${esc(j.nom)} <b>${j.n}/${mo.n || 3}</b></span>`).join('')}</div>`;
  return `<div class="jumeaux${opt.joueur ? ' tel' : ''}" data-k="jumeaux"><div class="jm-paire">${face(0, 'Cooper')}${face(1, 'Mr. C')}</div>` +
    (rev ? '' : `<p class="frise-aide">${mo.n || 3} différences discrètes : touchez-les${opt.joueur ? '' : ' sur vos téléphones'}</p>`) + compte + '</div>';
}

/* Desmond's Code : la grille de 16 affiches. Le donneur voit le code couleur (or : à faire deviner ; rouge ; noir ;
   neutre) ; les devineurs voient la couleur des films qu'ils ont touchés ; à la réponse, tout le code. */
function codeHTML(v, src, opt = {}) {
  const mo = v.moteur || {}, rev = v.phase === 'reponse', roles = mo.roles, mes = mo.mes || [];
  const d = mo.donneur, avant = (mo.indices || []).slice(0, -1);
  const tete = mo.indice ? `<p class="cd-indice"><b>${esc(mo.indice)}</b><span>${mo.nb}</span></p>` +
      (avant.length ? `<p class="cd-avant">${avant.map(x => `${esc(x.mot)} <b>${x.n}</b>`).join(' · ')}</p>` : '')
    : `<p class="cd-attente">${opt.joueur && mo.donneur_moi ? 'À vous : un indice (1 à 4 mots) et un nombre' :
      `${d ? esc(d.nom) : '?'} cherche un indice…`}</p>`;
  const cases = (mo.cases || []).map(c => {
    const k = mes.indexOf(c.img), role = roles ? roles[c.img] : k >= 0 ? mo.mes_roles[k] : '';
    const touche = opt.joueur && mo.actif && !mo.donneur_moi && k < 0;
    const qui = rev ? ((mo.touches || {})[c.img] || []).filter(Boolean).map(j => puce(j, '', 'mini')).join('') : '';
    return `<figure class="cd-case${role ? ' ' + role : ''}${k >= 0 ? ' touche' : ''}${touche ? ' actif' : ''}" data-cd="${c.img}" data-k="c${c.img}">` +
      `<img src="${src(c.img)}" alt=""><figcaption>${esc(c.txt)}</figcaption>${qui ? `<span class="cd-qui">${qui}</span>` : ''}</figure>`;
  }).join('');
  const av = opt.joueur ? '' : `<div class="rc-mises">${(mo.avance || []).map(j => `<span class="rc-mise${j.elimine ? ' ko' : ''}" style="--c:${j.couleur}">` +
    `${esc(j.nom)} <b>${j.elimine ? '☠' : `${j.n}/${mo.x}`}</b>${!j.elimine && j.fini && mo.indice ? ' ✓' : ''}</span>`).join('')}</div>`;
  return `<div class="code-desmond${opt.joueur ? ' tel' : ''}" data-k="code">` +
    `${opt.joueur && mo.donneur_moi ? '' : `<p class="cd-donneur">${d ? `Donneur : <b style="color:${d.couleur}">${esc(d.nom)}</b>` : ''}</p>`}${tete}` +
    `<div class="cd-grille">${cases}</div>${av}</div>`;
}

/* Jean Renault's Blackjack : la table de blackjack du One Eyed Jack's. Les cartes sont des affiches ; leur valeur
   (la note TMDB) ne s'affiche qu'à la fin. Jean, le croupier, en haut ; les joueurs autour. */
function carteBJ(c, src, cls = '') {
  if (!c || c.img === null || c.img === undefined) return `<figure class="bj-c dos ${cls}"><span>J</span></figure>`;
  return `<figure class="bj-c ${cls}"><img src="${src(c.img)}" alt=""><figcaption>${esc(c.txt)}</figcaption>` +
    (c.v !== null && c.v !== undefined ? `<b class="bj-v">${String(c.v).replace('.', ',')}</b>` : '') + '</figure>';
}
function totalBJ(t) { return t === null || t === undefined ? '' : String(t).replace('.', ','); }
function blackjackHTML(v, src, opt = {}) {
  const mo = v.moteur || {}, rev = v.phase === 'reponse';
  const RES = {gagne: 'Gagné', perd: 'Perdu', egal: 'Égalité', saute: 'Sauté'};
  const jean = `<div class="bj-jean"><p class="bj-nom">Jean Renault <small>croupier</small>` +
    (rev ? `<b class="bj-total${mo.jean_total > 21 ? ' saute' : ''}">${totalBJ(mo.jean_total)}</b>` : '') + `</p>` +
    `<div class="bj-main">${(mo.jean || []).map(c => carteBJ(c, src)).join('')}</div></div>`;
  if (opt.joueur) return jean;
  const joueurs = (mo.joueurs || []).map(j => `<div class="bj-joueur${j.reste && !rev ? ' reste' : ''} ${j.res || ''}" style="--c:${j.couleur}" data-k="j${esc(j.id)}">` +
    `<p class="bj-nom">${esc(j.nom)}${j.mise ? `<span class="bj-jeton">${j.mise}</span>` : mo.etape === 'mise' && !rev ? (j.a_mise ? ' <small>✓ a misé</small>' : ' <small>mise…</small>') : ''}` +
    `${rev ? `<b class="bj-total">${totalBJ(j.total)}</b><small class="bj-res">${RES[j.res] || ''}</small>` : j.reste ? ' <small>reste</small>' : ''}</p>` +
    `<div class="bj-main">${(j.cartes || []).map(c => carteBJ(c, src, 'petite')).join('')}</div></div>`).join('');
  return `<div class="blackjack" data-k="blackjack"><div class="bj-tapis">${jean}` +
    `<p class="bj-regle">${mo.etape === 'mise' && !rev ? 'Faites vos jeux : misez sur vos téléphones' : 'Approchez-vous de 21 sans dépasser · Jean tire jusqu\'à 17'}</p>` +
    `<div class="bj-joueurs">${joueurs}</div></div></div>`;
}

/* Windom Earle's Chess Clock : la chaîne des films (le lien entre chaque) et les pendules d'échecs des joueurs. */
const LIEN_ICONE = {acteur: '🎭', 'réalisateur': '🎬', compositeur: '🎼', 'scénariste': '✒️', 'directeur photo': '🎥', 'année': '📅'};
function penduleHTML(v, src, opt = {}) {
  const mo = v.moteur || {}, rev = v.phase === 'reponse', ch = mo.chaine || [];
  const films = ch.map((c, k) => (c.lien ? `<span class="pd-lien"><i>${LIEN_ICONE[c.lien.type] || '↔'}</i>${esc(c.lien.nom)}</span>` : '') +
    `<figure class="pd-film${k === ch.length - 1 ? ' dernier' : ''}">${c.img !== null && c.img !== undefined ? `<img src="${src(c.img)}" alt="">` : ''}` +
    `<figcaption><b>${esc(c.titre)}</b>${c.annee ? `<small>${c.annee}</small>` : ''}${c.qui ? `<small style="color:${c.qui.couleur}">${esc(c.qui.nom)}</small>` : ''}</figcaption></figure>`).join('');
  const pend = (mo.pendules || []).map(j => {
    const p = Math.max(0, Math.min(1, j.reste / Math.max(mo.temps || 40, j.reste)));
    return `<div class="pd-pendule${j.actif ? ' actif' : ''}${j.mat ? ' mat' : ''}" style="--c:${j.couleur};--p:${p.toFixed(3)}" data-k="p${esc(j.id)}">` +
      `<span class="pd-cadran"><i></i></span><b>${j.mat ? 'mat' : Math.ceil(j.reste) + ' s'}</b><small>${esc(j.nom)}</small></div>`;
  }).join('');
  const liste = (mo.pendules || []).map(j => `<span class="pd-txt${j.actif ? ' actif' : ''}${j.mat ? ' mat' : ''}" style="--c:${j.couleur}">` +
    `${esc(j.nom)} <b>${j.mat ? 'mat' : Math.ceil(j.reste) + ' s'}</b></span>`).join('');
  const interdit = mo.interdit && !rev ? `<p class="pd-interdit">Lien interdit au prochain coup : <b>${esc(mo.interdit)}</b></p>` : '';
  return `<div class="pendule${opt.joueur ? ' tel' : ''}" data-k="pendule"><div class="pd-chaine">${films}</div>${interdit}` +
    (opt.joueur ? `<div class="pd-liste">${liste}</div>` : `<div class="pd-pendules">${pend}</div>`) +
    `<p class="pd-regle">Chacun ${Math.round(mo.temps || 40)} s de pendule · répondre en moins de 10 s rend 5 s</p></div>`;
}

/* La cérémonie (Dick Tremayne) et le Hibou d'or (Dwayne Milford) : l'enveloppe, les nommés, le lauréat. */
function ceremonieHTML(v, src, opt = {}) {
  const mo = v.moteur || {}, env = mo.env, rev = v.phase === 'reponse';
  if (!env) return `<div class="ceremonie" data-k="ceremonie"><p class="ce-hote">${esc(mo.hote_nom || '')} monte sur scène…</p></div>`;
  const devoile = env.bonne !== null && env.bonne !== undefined;
  const items = (env.items || []).map((it, i) => `<figure class="ce-nomme${devoile && i === env.bonne ? ' laureat' : ''}${devoile && i !== env.bonne ? ' perdant' : ''}" data-k="n${it.img}">` +
    `<img src="${src(it.img)}" alt=""><figcaption>${esc(it.txt)}${devoile && env.infos ? `<small>${esc(env.infos[i] || '')}</small>` : ''}</figcaption>` +
    `${devoile && i === env.bonne ? '<span class="ce-trophee">🏆</span>' : ''}</figure>`).join('');
  const tambour = !devoile ? `<p class="ce-tambour">${Math.ceil(mo.reste || 0)}<small>s</small> <span>🥁</span></p>` : '';
  const qui = devoile ? `<p class="ce-justes">${(env.justes || []).map(j => puce(j, '', 'juste')).join('') || '<span class="doux">Personne n\'a trouvé</span>'}</p>`
    : `<p class="ce-justes">${(env.repondu || []).map(j => puce(j, '', 'attend')).join('')}</p>`;
  return `<div class="ceremonie" data-k="ceremonie"><p class="ce-hote">${esc(mo.hote_nom || '')} · enveloppe ${mo.k + 1}/${mo.n}</p>` +
    `<div class="ce-enveloppe"><b>${esc(env.titre)}</b>${env.sous ? `<small>${esc(env.sous)}</small>` : ''}</div>` +
    (items ? `<div class="ce-nommes">${items}</div>` : '<p class="ce-cache">Les nommés sont sur vos téléphones…</p>') + tambour + qui + '</div>';
}

/* Bushnell Mullins : la pluie d'affiches. Chaque écran anime la chute avec sa propre horloge, calée sur le chrono
   de la manche (comme la vision de Sarah). */
const PLUIE = {seq: null, base: 0, touches: new Set()};
function calePluie(v) {
  if (!v || v.jeu !== 'bushnell' || v.phase !== 'manche') return;
  const base = performance.now() - (v.ecoule || 0) * 1000;
  if (PLUIE.seq !== v.seq) { PLUIE.seq = v.seq; PLUIE.base = base; PLUIE.touches = new Set(); }
  else PLUIE.base = Math.min(PLUIE.base + 40, Math.max(PLUIE.base - 40, base));
}
function pluieHTML(v, src, opt = {}) {
  calePluie(v);
  const mo = v.moteur || {}, mes = mo.mes || {};
  const g = (mo.gouttes || []).map(x => {
    const t = mes[x.id] !== undefined ? (mes[x.id] ? ' bon' : ' faux') : x.ok === true ? ' rate' : '';
    return `<img class="pl-goutte${t}" data-g="${x.id}" data-t0="${x.t0}" data-dur="${x.dur}" style="left:${x.x * 100}%" src="${src(x.img)}" alt="" draggable="false">`;
  }).join('');
  const scores = opt.joueur ? '' : `<div class="pl-scores">${(mo.scores || []).map(j => `<span style="--c:${j.couleur}">${esc(j.nom)} <b>${j.live > 0 ? '+' : ''}${j.live}</b></span>`).join('')}</div>`;
  return `<div class="pluie${opt.joueur ? ' tel' : ''}" data-k="pluie"><p class="pl-cond">${mo.condition ? `Touchez : <b>${esc(mo.condition)}</b>` : 'Prêts ?'}</p>` +
    `<div class="pl-zone">${g}<span class="pl-sol"></span></div>${scores}</div>`;
}
(function animerPluie() {
  const t = (performance.now() - PLUIE.base) / 1000;
  for (const el of document.querySelectorAll('.pl-goutte')) {
    const t0 = Number(el.dataset.t0), dur = Number(el.dataset.dur), p = (t - t0) / dur;
    if (p < 0 || p > 1.02) { el.style.visibility = 'hidden'; continue; }
    el.style.visibility = 'visible';
    el.style.top = `calc(${(p * 100).toFixed(2)}% - ${(p * 30).toFixed(1)}%)`;
    if (PLUIE.touches.has(el.dataset.g)) el.classList.add('touche');
  }
  requestAnimationFrame(animerPluie);
})();

/* Lana Budding : les mensonges (façon Fibbage). La question à trou, puis les réponses mélangées, puis qui a menti. */
function mensongesHTML(v, opt = {}) {
  const mo = v.moteur || {}, et = mo.etape;
  const q = `<div class="ms-q"><small>Question ${mo.k + 1}/${mo.n}</small><b>${esc(mo.q || '').replace('___', '<i>_____</i>')}</b></div>`;
  if (et === 'ecrire') return `<div class="mensonges" data-k="ms">${q}<p class="ms-consigne">Inventez une fausse réponse crédible` +
    `${opt.joueur ? '' : ' sur vos téléphones'} · ${Math.ceil(mo.reste || 0)} s</p></div>`;
  const opts = (mo.options || []).map((o, i) => {
    const cls = o.vraie ? ' vraie' : o.leurre ? ' leurre' : '';
    const det = et === 'rev' ? `<small>${o.vraie ? 'LA VÉRITÉ' : o.leurre ? 'mensonge de Lana' : (o.auteurs || []).map(a => esc(a.nom)).join(', ') + ' a menti'}` +
      `${(o.votants || []).length ? ' · ' + o.votants.map(j => puce(j, '', 'mini')).join('') : ''}</small>` : '';
    return `<div class="ms-opt${et === 'rev' ? cls : ''}"><b>${LETTRES_MS[i]}</b><span>${esc(o.txt)}</span>${det}</div>`;
  }).join('');
  return `<div class="mensonges" data-k="ms">${q}${et === 'voter' ? `<p class="ms-consigne">Laquelle est vraie ? ${Math.ceil(mo.reste || 0)} s</p>` : ''}` +
    `<div class="ms-opts">${opts}</div></div>`;
}
const LETTRES_MS = 'ABCDEFGHIJKL';

/* Mrs. Tremond : le tableau (façon Dixit). Le cadre doré du tableau porte l'indice ; les affiches posées dessous. */
function tableauHTML(v, src, opt = {}) {
  const mo = v.moteur || {}, et = mo.etape, c = mo.conteur;
  const tete = `<div class="tb-cadre"><small>${c ? `Conteur : <b style="color:${c.couleur}">${esc(c.nom)}</b>` : ''}${mo.deux ? ' · règle à deux' : ''}</small>` +
    `<b>${mo.indice ? '« ' + esc(mo.indice) + ' »' : '…'}</b></div>`;
  if (et === 'conteur') return `<div class="tableau" data-k="tb">${tete}<p class="tb-consigne">${c ? esc(c.nom) : '?'} choisit une affiche de sa main et tape un indice… ${Math.ceil(mo.reste || 0)} s</p></div>`;
  if (et === 'poser') return `<div class="tableau" data-k="tb">${tete}<p class="tb-consigne">Choisissez dans votre main l'affiche qui colle le mieux à l'indice · ${Math.ceil(mo.reste || 0)} s</p></div>`;
  const cartes = (mo.table || []).map(t => `<figure class="tb-carte${t.cible ? ' cible' : ''}" data-k="t${t.img}"><b>${LETTRES_MS[t.i]}</b><img src="${src(t.img)}" alt="">` +
    (et === 'rev' ? `<figcaption>${esc(t.txt || '')}<small>${t.cible ? 'l\'affiche du conteur' : t.de ? 'posée par ' + esc(t.de.nom) : 'le tableau'}</small>` +
      `<span>${(t.votants || []).map(j => puce(j, '', 'mini')).join('')}</span></figcaption>` : '') + '</figure>').join('');
  return `<div class="tableau" data-k="tb">${tete}${et === 'voter' ? `<p class="tb-consigne">Laquelle est l'affiche du conteur ? ${Math.ceil(mo.reste || 0)} s</p>` : ''}` +
    `<div class="tb-table">${cartes}</div></div>`;
}

/* Le Dr Hayward : le dossier médical, trois secrets (anecdotes) qui s'écrivent l'un après l'autre ; leur place est
   réservée dès le début. */
function secretsHTML(e) {
  const s = e.secrets || [];
  const lignes = [0, 1, 2].map(k => `<li class="${s[k] ? '' : 'vide'}" data-k="s${k}">${s[k] ? esc(s[k]) : '&nbsp;'}</li>`).join('');
  return `<div class="dossier" data-k="dossier"><p class="ds-tete"><b>Dr W. Hayward</b><span>Dossier confidentiel</span></p><ol>${lignes}</ol></div>`;
}

/* Bernard Renault : le poker. Les cartes sont des affiches ; un badge (valeur + couleur) apparaît quand la valeur
   est connue. Les règles de la table se dévoilent tour après tour (leur place est réservée). */
function cartePK(c, src, cls = '') {
  if (!c) return `<figure class="pk-c dos ${cls}"><span>B</span></figure>`;
  return `<figure class="pk-c ${cls}"><img src="${src(c.img)}" alt=""><figcaption>${esc(c.txt)}</figcaption>` +
    (c.r ? `<b class="pk-badge${c.rouge ? ' rouge' : ''}">${c.r}${c.c}</b>` : '<b class="pk-badge inconnu">?</b>') + '</figure>';
}
function reglesPK(mo) {
  const l = mo.regles || [];
  return `<ul class="pk-regles">${Array.from({length: mo.n_regles || 6}, (_, k) => `<li class="${l[k] ? '' : 'vide'}">${l[k] ? esc(l[k]) : 'Règle cachée…'}</li>`).join('')}</ul>`;
}
function pokerHTML(v, src, opt = {}) {
  const mo = v.moteur || {}, rev = v.phase === 'reponse';
  const milieu = `<div class="pk-milieu">${(mo.milieu || []).map(c => cartePK(c, src)).join('')}</div>`;
  if (opt.joueur) return milieu + reglesPK(mo);
  const b = mo.bernard || {};
  const bern = `<div class="pk-bernard${b.gagne ? ' gagne' : ''}"><p class="bj-nom">Bernard Renault <small>suit toujours</small>${b.main ? ` <b class="pk-main">${esc(b.main)}</b>` : ''}</p>` +
    `<div class="bj-main">${(b.cartes && b.cartes.length ? b.cartes : [null, null]).map(c => cartePK(c, src, 'petite')).join('')}</div></div>`;
  const tours = ['Avant le flop', 'Le flop', 'Le turn', 'La river', 'Abattage'];
  const js = (mo.joueurs || []).map(j => `<div class="pk-joueur${j.couche ? ' couche' : ''}" style="--c:${j.couleur}" data-k="j${esc(j.id)}">` +
    `<p class="bj-nom">${esc(j.nom)} <span class="bj-jeton">${j.mise}</span>${j.couche ? ' <small>couché</small>' : j.a_joue ? ` <small>${esc(j.a_joue)}</small>` : ''}` +
    `${j.defausses ? ` <small>défausses ${j.defausses}</small>` : ''}${j.main ? ` <b class="pk-main">${esc(j.main)}</b>` : ''}</p>` +
    (j.cartes && j.cartes.length ? `<div class="bj-main">${j.cartes.map(c => cartePK(c, src, 'petite')).join('')}</div>` : '') + '</div>').join('');
  return `<div class="poker" data-k="poker"><div class="pk-tapis">${bern}` +
    `<p class="bj-regle">${tours[rev ? 4 : Math.min(mo.tour || 0, 3)]} · pot ${mo.pot || 0}${rev ? '' : ` · ${Math.ceil(mo.reste || 0)} s`}</p>${milieu}` +
    `<div class="pk-joueurs">${js}</div></div>${reglesPK(mo)}</div>`;
}
