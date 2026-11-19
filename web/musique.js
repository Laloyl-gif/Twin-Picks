/* Musique d'ambiance de l'écran hôte : au menu et sur le podium, la musique du menu ; pendant la partie, celle de la
   partie (BO des films des listes, avec le nom du film en bas de l'écran). Coupée pendant le blind test.
   Trois sources (Réglages › Général) :
     - dossier musique/ du jeu : morceaux complets, enchaînés en fondu (lecteur audio du navigateur) ;
     - playlist YouTube : morceaux complets, lus au hasard par le lecteur YouTube intégré (caché) ;
     - Deezer : extraits de 30 s enchaînés en fondu.
   Le morceau en cours s'affiche discrètement en bas de l'écran (clic sur l'égaliseur : couper / remettre). */
/* Téléphone administrateur : le menu est dans un cadre (iframe) de la page du joueur. Le navigateur n'autorise le son
   qu'après un geste de l'utilisateur sur la page : les lecteurs sont donc créés dans la page du joueur (le parent),
   qui reçoit les gestes, et non dans le cadre. */
const HOTE_WIN = (() => { try { return window.parent !== window && window.parent.document ? window.parent : window; } catch (e) { return window; } })();
const AMB = {lecteurs: [new HOTE_WIN.Audio(), new HOTE_WIN.Audio()], actif: 0, genre: null, piste: null, recents: [],
             bloque: false, jeton: 0, essai: 0, source: null};
const FONDU = 2500;
AMB.lecteurs.forEach(a => {
  a.preload = 'auto';
  a.volume = 0;
  a.addEventListener('timeupdate', () => {
    // fin du morceau : on enchaîne sur le suivant en fondu
    if (a === AMB.lecteurs[AMB.actif] && AMB.genre && AMB.source !== 'youtube' && !a._suite && a.duration &&
        a.duration - a.currentTime < FONDU / 1000 + 0.4) {
      a._suite = true;
      lancerPiste(AMB.genre);
    }
  });
  a.addEventListener('ended', () => {
    if (a === AMB.lecteurs[AMB.actif] && AMB.genre && AMB.source !== 'youtube' && !a._suite) lancerPiste(AMB.genre);
  });
  a.addEventListener('error', () => {
    if (a === AMB.lecteurs[AMB.actif] && AMB.genre && AMB.source !== 'youtube') { AMB.essai = Date.now() + 3000; AMB.piste = null; }
  });
});

function genreMusique(e) {
  if (!CFG || !R().musique || !(R().musique_volume > 0)) return null;
  if (e.audio) return null;                                   // blind test en cours
  if (typeof TEL !== 'undefined' && TEL && e.ecran_actif) return null;   // un écran de partie joue déjà la musique
  return e.phase === 'lobby' || e.phase === 'fin' ? 'menu' : 'jeu';
}
const volumeMusique = g => Math.min(1, (R().musique_volume / 100) * (g === 'menu' ? 0.8 : 0.45));

function fondu(a, vers, ms, fin) {
  clearInterval(a._fondu);
  const depart = a.volume, t0 = performance.now();
  a._fondu = setInterval(() => {
    const k = Math.min(1, (performance.now() - t0) / ms);
    a.volume = Math.max(0, Math.min(1, depart + (vers - depart) * k));
    if (k >= 1) { clearInterval(a._fondu); a._fondu = null; if (fin) fin(); }
  }, 50);
}

/* ---------------- lecteur YouTube (caché) ---------------- */
const YT_AMB = {player: null, pret: null, playlist: '', melange: false, suite: false, vol: 0, fondu: null,
                recents: [], depuis: 0, demarre: false};
function chargerYouTube() {
  if (YT_AMB.pret) return YT_AMB.pret;
  YT_AMB.pret = new Promise((ok, ko) => {
    const D = HOTE_WIN.document;
    const boite = D.createElement('div');
    boite.id = 'yt-ambiance';
    boite.style.cssText = 'position:fixed;left:-10000px;top:0;width:320px;height:180px;pointer-events:none;opacity:0';
    boite.innerHTML = '<div id="yt-lecteur"></div>';
    D.body.appendChild(boite);
    const pret = () => {
      window.YT = HOTE_WIN.YT;
      YT_AMB.player = new HOTE_WIN.YT.Player(D.getElementById('yt-lecteur'), {
        width: 320, height: 180,
        playerVars: {autoplay: 0, controls: 0, disablekb: 1, fs: 0, rel: 0, iv_load_policy: 3, playsinline: 1,
                     origin: location.origin},
        events: {onReady: () => ok(YT_AMB.player), onStateChange: ytEtat, onError: ytErreur},
      });
    };
    if (HOTE_WIN.YT && HOTE_WIN.YT.Player) return pret();
    HOTE_WIN.onYouTubeIframeAPIReady = pret;
    const s = D.createElement('script');
    s.src = 'https://www.youtube.com/iframe_api';
    s.onerror = () => { YT_AMB.pret = null; ko(new Error('YouTube injoignable')); };
    D.head.appendChild(s);
  });
  return YT_AMB.pret;
}
function ytVolume(vers, ms, fin) {
  const p = YT_AMB.player;
  clearInterval(YT_AMB.fondu);
  if (!p) return;
  const depart = YT_AMB.vol, t0 = performance.now();
  YT_AMB.fondu = setInterval(() => {
    const k = Math.min(1, (performance.now() - t0) / Math.max(1, ms));
    YT_AMB.vol = depart + (vers - depart) * k;
    try { p.setVolume(Math.round(100 * YT_AMB.vol)); } catch (e) { /* lecteur pas prêt */ }
    if (k >= 1) { clearInterval(YT_AMB.fondu); YT_AMB.fondu = null; if (fin) fin(); }
  }, 50);
}
function ytSuivant() {
  const p = YT_AMB.player;
  const liste = (p && p.getPlaylist && p.getPlaylist()) || [];
  if (!liste.length) return;
  const libres = liste.map((_, i) => i).filter(i => !YT_AMB.recents.includes(i));
  const i = (libres.length ? libres : liste.map((_, k) => k))[Math.floor(Math.random() * (libres.length || liste.length))];
  YT_AMB.recents = [...YT_AMB.recents, i].slice(-Math.min(15, Math.floor(liste.length / 2)));
  YT_AMB.suite = false;
  YT_AMB.depuis = Date.now();
  p.playVideoAt(i);
}
function ytEtat(ev) {
  if (AMB.source !== 'youtube') return;
  if (ev.data === YT.PlayerState.PLAYING) {
    YT_AMB.demarre = true;
    AMB.bloque = false;
    if (!YT_AMB.melange) { YT_AMB.melange = true; ytSuivant(); return; }   // première lecture : au hasard
    const d = YT_AMB.player.getVideoData() || {};
    AMB.piste = {source: 'youtube', titre: nettoyerTitre(d.title || ''), artiste: (d.author || '').replace(/ - Topic$/, '')};
    ytVolume(volumeMusique(AMB.genre || 'menu'), FONDU);
    afficherMusique();
  } else if (ev.data === YT.PlayerState.ENDED) {
    ytSuivant();
  }
}
function ytErreur() { if (AMB.source === 'youtube') setTimeout(ytSuivant, 500); }   // vidéo non intégrable : la suivante
const nettoyerTitre = t => t.replace(/\s*[\(\[](official|audio|lyrics?|hd|hq|remaster(ed)?|vid[eé]o)[^\)\]]*[\)\]]/gi, '').trim();

async function jouerYouTube(playlist) {
  let p;
  try { p = await chargerYouTube(); } catch (err) { AMB.essai = Date.now() + 30000; return; }
  if (AMB.source !== 'youtube') return;
  if (YT_AMB.playlist !== playlist) {
    YT_AMB.playlist = playlist;
    YT_AMB.melange = false;
    YT_AMB.recents = [];
    YT_AMB.vol = 0;
    p.setVolume(0);
    p.loadPlaylist({list: playlist, listType: 'playlist', index: 0});
  } else {
    p.playVideo();
  }
  YT_AMB.depuis = Date.now();
  YT_AMB.demarre = false;
}
function arreterYouTube(ms = 1200) {
  if (!YT_AMB.player) return;
  ytVolume(0, ms, () => { try { YT_AMB.player.pauseVideo(); } catch (e) { /* rien */ } });
}
/* Toutes les 0,4 s : fin du morceau (fondu puis suivant), lecture bloquée par le navigateur. */
function surveillerYouTube() {
  const p = YT_AMB.player;
  if (AMB.source !== 'youtube' || !p || !p.getPlayerState) return;
  const etat = p.getPlayerState();
  if (etat === YT.PlayerState.PLAYING) {
    const d = p.getDuration(), t = p.getCurrentTime();
    if (d > 0 && d - t < FONDU / 1000 + 0.5 && !YT_AMB.suite) {
      YT_AMB.suite = true;
      ytVolume(0, FONDU, ytSuivant);
    }
  } else if (!YT_AMB.demarre && Date.now() - YT_AMB.depuis > 3000 && [-1, 5, 2].includes(etat)) {
    AMB.bloque = true;                                         // le navigateur attend un clic
  }
}

/* ---------------- lecture ---------------- */
async function lancerPiste(genre) {
  const jeton = ++AMB.jeton;
  let r = {};
  try { r = await get(`/api/hote/musique${Q}&genre=${genre}&sauf=${AMB.recents.join(',')}`); } catch (err) { /* hors ligne */ }
  if (jeton !== AMB.jeton) return;
  const p = r && r.piste;
  if (!p) {                                                    // rien de disponible : nouvel essai dans 30 s
    AMB.piste = null;
    afficherMusique();
    AMB.essai = Date.now() + 30000;
    return;
  }
  if (p.source === 'youtube') {
    const ancien = AMB.lecteurs[AMB.actif];
    if (!ancien.paused) fondu(ancien, 0, FONDU, () => ancien.pause());
    AMB.source = 'youtube';
    if (YT_AMB.playlist !== p.playlist) AMB.piste = null;
    afficherMusique();
    return jouerYouTube(p.playlist);
  }
  if (AMB.source === 'youtube') arreterYouTube(FONDU);
  AMB.source = p.source || 'deezer';
  AMB.recents = [...AMB.recents, p.id].slice(-10);
  const ancien = AMB.lecteurs[AMB.actif], neuf = AMB.lecteurs[1 - AMB.actif];
  clearInterval(neuf._fondu);
  neuf._suite = false;
  neuf.volume = 0;
  neuf.src = `/musique/${p.id}${Q}`;
  try {
    await neuf.play();
  } catch (err) {
    if (jeton !== AMB.jeton) return;
    if (err && err.name === 'NotAllowedError') AMB.bloque = true;   // le navigateur attend un clic
    else AMB.essai = Date.now() + 5000;
    afficherMusique();
    return;
  }
  if (jeton !== AMB.jeton) { neuf.pause(); return; }
  AMB.bloque = false;
  AMB.actif = 1 - AMB.actif;
  AMB.piste = p;
  afficherMusique();
  fondu(ancien, 0, FONDU, () => ancien.pause());
  fondu(neuf, volumeMusique(genre), FONDU);
}

function arreterMusique() {
  AMB.jeton++;
  AMB.piste = null;
  AMB.lecteurs.forEach(a => { if (!a.paused) fondu(a, 0, 1200, () => a.pause()); });
  arreterYouTube();
  afficherMusique();
}

/* Appelée à chaque rafraîchissement de l'état (toutes les 0,4 s). */
function majMusique(e) {
  const g = genreMusique(e);
  const reglage = CFG ? [R().musique_menu_source, R().musique_menu_youtube, R().musique_jeu_source,
                         R().musique_jeu_youtube].join('|') : '';
  if (g !== AMB.genre || reglage !== AMB.reglage) {             // changement d'écran ou de source : on relance
    AMB.genre = g;
    AMB.reglage = reglage;
    AMB.essai = 0;
    if (g) lancerPiste(g); else arreterMusique();
  } else if (g && !AMB.piste && !AMB.bloque && AMB.essai && Date.now() > AMB.essai) {
    AMB.essai = 0;
    lancerPiste(g);
  }
  if (AMB.source === 'youtube') {
    surveillerYouTube();
    if (g && AMB.piste && !YT_AMB.fondu && YT_AMB.player) {
      const v = volumeMusique(g);
      if (Math.abs(YT_AMB.vol - v) > 0.01) { YT_AMB.vol = v; YT_AMB.player.setVolume(Math.round(100 * v)); }
    }
  } else {
    const a = AMB.lecteurs[AMB.actif];
    if (g && AMB.piste && !a._fondu && !a.paused) a.volume = volumeMusique(g);   // volume modifié dans les réglages
  }
  afficherMusique();
}

function afficherMusique() {
  const el = $('#musique');
  if (!el || !CFG) return;
  const coupe = !R().musique, p = AMB.genre && AMB.piste;
  el.classList.toggle('coupe', coupe || !p);
  let html = '';
  if (AMB.bloque && AMB.genre) html = '<span class="m-invite">Toucher pour lancer la musique</span>';
  else if (p) html = `<span class="m-titre">${esc(p.titre)}</span>` + (p.artiste ? `<span class="m-sep"></span><span class="m-artiste">${esc(p.artiste)}</span>` : '') +
    (p.film ? `<span class="m-sep"></span><span class="m-film">${esc(p.film)}</span>` : '');
  maj($('#m-texte'), html, html);
  $('#m-bascule').title = coupe ? 'Remettre la musique' : 'Couper la musique';
}

function debloquerMusique(ev) {
  if (!AMB.bloque || (ev && ev.target && ev.target.closest && ev.target.closest('#m-bascule'))) return;
  AMB.bloque = false;
  if (AMB.source === 'youtube' && YT_AMB.player) {
    YT_AMB.depuis = Date.now();
    YT_AMB.player.playVideo();
  } else if (AMB.genre) {
    lancerPiste(AMB.genre);
  }
}
document.addEventListener('pointerdown', debloquerMusique);
document.addEventListener('keydown', debloquerMusique);
if (HOTE_WIN !== window) {                      // téléphone administrateur : les gestes sur la page du joueur comptent
  HOTE_WIN.document.addEventListener('pointerdown', debloquerMusique);
  HOTE_WIN.document.addEventListener('keydown', debloquerMusique);
}
$('#m-bascule').onclick = ev => { ev.stopPropagation(); regler({musique: !R().musique}); };
$('#m-texte').onclick = debloquerMusique;
