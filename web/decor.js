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
  hank: () => ob('d-bg petit', OBJ.domino),
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
  mike: [['Is it future, or is it past?', 'Mike, the one-armed man'], ['Fire walk with me.', 'Mike, the one-armed man']],
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
  mike: () => replique('mike', 'sous', 'griffe'),
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
      ? `<figure class="ph-carte apparait" data-k="c${i}" style="left:${x}%;top:${y}%">` +
        (c.img !== null && c.img !== undefined ? `<img src="${src(c.img)}" alt="">` : `<span class="ph-init">${initiale(c.nom)}</span>`) +
        `<figcaption><b>${esc(c.nom)}</b><small>${c.n} films ensemble · ${esc(c.metier)}</small>` +
        `${c.film ? `<em>dont « ${esc(c.film)} »</em>` : ''}</figcaption></figure>`
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
      return `<figure class="rb-carte" data-k="r${i}" style="--i:${i};--rot:${rot}deg"><span class="rb-emoji">${x.v}</span>` +
        `<figcaption>${e.mots && x.mot ? esc(x.mot) : '&nbsp;'}</figcaption></figure>`;
    }
    if (x.t === 'case') {                                                  // (ancien format)
      return `<span class="rb-son" data-k="r${i}">${'_'.repeat(Math.min(x.v, 12))}</span>`;
    }
    return `<figure class="rb-carte son" data-k="r${i}" style="--i:${i};--rot:${rot}deg"><span class="rb-son">${esc(x.v)}</span>` +
      '<figcaption>&nbsp;</figcaption></figure>';
  }).join('') + '</div>';
}

/* Hank's Dominoes : la chaîne de dominos. À gauche [film A | acteur], à droite [acteur | film C], au centre le domino
   manquant (le film mystère). Les acteurs charnières se dévoilent sur les dominos. */
function dominosHTML(e, src) {
  const ch = e.chaine || [];
  const acteur = d => d.img_a !== null && d.img_a !== undefined
    ? `<figure class="dm-acteur apparait"><img src="${src(d.img_a)}" alt=""><figcaption>${esc(d.acteur)}</figcaption></figure>`
    : '<figure class="dm-acteur cache"><span>?</span><figcaption>&nbsp;</figcaption></figure>';
  const film = d => `<figure class="dm-film"><img src="${src(d.img_f)}" alt=""><figcaption>${esc(d.film)}</figcaption></figure>`;
  const g = ch[0], dr = ch[1];
  return `<div class="dominos chaine" data-k="dominos">` +
    (g ? `<div class="domino" data-k="dg">${film(g)}<i></i>${acteur(g)}</div>` : '') +
    '<span class="dm-joint"></span><div class="dm-centre"><span>?</span><i></i><span>?</span></div><span class="dm-joint"></span>' +
    (dr ? `<div class="domino" data-k="dd">${acteur(dr)}<i></i>${film(dr)}</div>` : '') + '</div>';
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

/* Dougie's Jackpots : la machine à sous. Chaque rouleau tourne sur des morceaux d'affiches (flous), puis s'arrête sur
   un tiers de l'affiche du film. Quand les trois sont arrêtés : jackpot ! */
function jackpotHTML(e, src) {
  const r = e.rouleaux || [], leurres = e.leurres || [], tous = r.length && r.every(Boolean);
  const bande = k => [...leurres, ...leurres].map((l, i) => `<img src="${src(leurres[(i + k * 2) % Math.max(1, leurres.length)])}" alt="">`).join('');
  const rouleau = k => r[k]
    ? `<div class="jp-rouleau arrete" data-k="r${k}a"><img class="jp-tiers" src="${src(k)}" alt=""></div>`
    : `<div class="jp-rouleau" data-k="r${k}t"><div class="jp-bande" style="--k:${k}">${bande(k)}</div></div>`;
  return `<div class="jackpot${tous ? ' gagne' : ''}" data-k="jackpot"><div class="jp-fronton">` +
    `<span class="jp-titre">${tous ? 'JACKPOT' : 'SILVER MUSTANG'}</span><span class="jp-ampoules">${'<i></i>'.repeat(14)}</span></div>` +
    `<div class="jp-vitre">${[0, 1, 2].map(rouleau).join('')}</div>` +
    `<div class="jp-bas"><span class="jp-fente"></span><span class="jp-plateau"></span></div>` +
    `<span class="jp-levier"><i></i></span><p class="jp-voix">${tous ? '“Hellooo!”' : `“${esc(citation('dougie')[0])}”`} — Dougie Jones</p></div>`;
}

/* Mr. C's Coordinates : les nombres du film, tapés un à un sur la fiche de Mr. C */
function coordonneesHTML(e) {
  const ns = e.nombres || [], total = Math.max(e.total || 0, ns.length);
  let h = '';
  for (let i = 0; i < total; i++) {
    const n = ns[i];
    h += n ? `<li class="apparait" data-k="n${i}"><b>${esc(n[0])}</b><small>${esc(n[1])}</small></li>`
           : `<li class="vide" data-k="n${i}"><b>&nbsp;</b><small>&nbsp;</small></li>`;
  }
  return `<div class="coordonnees" data-k="coord"><div class="co-fiche"><div class="co-tete">COORDONNÉES</div><ol>${h}</ol></div></div>`;
}

/* Lil's Coded Dress : la robe de Lil, neuf objets épinglés dessus (chacun évoque un film) */
function robeHTML(e) {
  const pos = [[30, 26], [50, 22], [70, 26], [26, 50], [50, 47], [74, 50], [30, 74], [50, 78], [70, 74]];
  const objets = (e.robe || []).map((o, i) => `<span class="rb-objet" style="left:${pos[i % 9][0]}%;top:${pos[i % 9][1]}%;--r:${o.r || 0}deg;--i:${i}">${o.v}</span>`).join('');
  return `<div class="robe-lil" data-k="robe"><svg class="rl-robe" viewBox="0 0 300 400" aria-hidden="true"><defs>` +
    '<linearGradient id="rl-t" x1="0" x2="1"><stop offset="0" stop-color="#7a0e1c"/><stop offset=".5" stop-color="#c8102e"/><stop offset="1" stop-color="#6a0c18"/></linearGradient></defs>' +
    '<path d="M110 20c10 14 70 14 80 0l22 10-10 64c30 40 70 150 84 290H14C28 244 68 134 98 94L88 30z" fill="url(#rl-t)"/>' +
    '<path d="M110 20c10 14 70 14 80 0" fill="none" stroke="#3a0610" stroke-width="4"/>' +
    '<path d="M98 94c30 10 74 10 104 0" fill="none" stroke="#ffffff22" stroke-width="3"/></svg>' +
    `<span class="rl-rose">${OBJ.rose}</span>${objets}</div>`;
}
