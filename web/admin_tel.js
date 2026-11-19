/* Téléphone administrateur (application Android, quand aucun ordinateur n'héberge la partie) : ce téléphone a ouvert
   la partie, il en a la clé. En plus de jouer, il choisit les jeux, règle, lance, met en pause… dans un panneau qui
   reprend l'écran hôte en version téléphone (une colonne de cartes qui défile). Les autres joueurs n'ont pas ce bouton :
   seul l'administrateur (l'ordinateur, ou ce téléphone) modifie les jeux et les réglages. */
(function () {
  const url = new URL(location.href);
  const venue = url.searchParams.get('admin');
  if (venue) {
    localStorage.setItem('cleAdmin', venue);
    url.searchParams.delete('admin');
    history.replaceState(null, '', url.pathname + url.search);
  }
  const CLE = localStorage.getItem('cleAdmin');
  if (!CLE) return;
  let valide = false, ouvert = false, derniere = '', ouvertAuto = false;

  const bouton = document.createElement('button');
  bouton.id = 'b-admin';
  bouton.className = 'admin-tel';
  bouton.innerHTML = '<span class="ad-pic">▲▲</span>Partie';
  bouton.hidden = true;
  const panneau = document.createElement('div');
  panneau.id = 'admin-panneau';
  panneau.className = 'admin-panneau';
  panneau.hidden = true;
  panneau.innerHTML = '<div class="ap-tete"><b>Administrateur</b><button class="discret petit" id="ap-fermer">Fermer</button></div>' +
    `<iframe id="ap-cadre" title="Menu de la partie" src="/hote?k=${encodeURIComponent(CLE)}&tel=1"></iframe>`;
  document.body.append(bouton, panneau);

  const montrer = v => { ouvert = v; panneau.hidden = !v; document.body.classList.toggle('admin-ouvert', v); };
  bouton.onclick = () => montrer(true);
  panneau.querySelector('#ap-fermer').onclick = () => montrer(false);

  async function verifier() {
    try {
      const r = await fetch('/api/hote/etat?k=' + encodeURIComponent(CLE) + '&tel=1');
      if (r.status === 403) { localStorage.removeItem('cleAdmin'); bouton.remove(); panneau.remove(); return; }
      const e = await r.json();
      valide = true;
      document.body.classList.add('a-admin');
      bouton.hidden = !document.getElementById('v-jeu') || document.getElementById('v-jeu').hidden;
      // le menu s'ouvre de lui-même au retour au menu (une fois le joueur entré dans la partie)
      if (e.phase !== derniere) {
        if (e.phase === 'lobby' && !bouton.hidden) { montrer(true); ouvertAuto = true; }
        else if (derniere === 'lobby' && ouvertAuto) { montrer(false); ouvertAuto = false; }
        derniere = bouton.hidden ? '' : e.phase;
      }
    } catch (err) { /* réseau : on réessaie */ }
    setTimeout(verifier, valide ? 1500 : 3000);
  }
  verifier();
})();
