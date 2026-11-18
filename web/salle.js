/* Le code de la partie : affiché en clair, et un bouton pour rejoindre une autre partie avec son code, même sans être
   sur le même Wi-Fi (le serveur retrouve ses adresses : Wi-Fi d'abord, sinon Internet). */
(function () {
  let code = '';
  async function afficher() {
    try {
      const s = await get('/api/salle');
      code = s.code || '';
      const el = document.getElementById('salle-tel');
      if (el) el.innerHTML = code ? `<small>Partie</small><b>${esc(code)}</b>` : '';
      document.body.dataset.salle = code;
    } catch (e) { /* hors ligne */ }
  }
  afficher();
  const dlg = document.getElementById('d-code'), champ = document.getElementById('code-saisie'), msg = document.getElementById('code-msg');
  document.addEventListener('click', ev => {
    if (!ev.target.closest('button[data-code]')) return;
    const p = document.getElementById('d-profil');
    if (p && p.open) p.close();
    champ.value = ''; msg.textContent = '';
    dlg.showModal();
    setTimeout(() => champ.focus(), 50);
  });
  document.getElementById('code-non').onclick = () => dlg.close();
  champ.onkeydown = ev => { if (ev.key === 'Enter') document.getElementById('code-ok').click(); };
  champ.oninput = () => { champ.value = champ.value.toUpperCase().replace(/[^A-Z0-9]/g, ''); };
  const joignable = url => new Promise(ok => {
    const ctrl = new AbortController(), t = setTimeout(() => { ctrl.abort(); ok(false); }, 2200);
    fetch(url.replace(/\/$/, '') + '/web/icone.png?' + Date.now(), {mode: 'no-cors', signal: ctrl.signal})
      .then(() => { clearTimeout(t); ok(true); }).catch(() => { clearTimeout(t); ok(false); });
  });
  document.getElementById('code-ok').onclick = async () => {
    const c = champ.value.trim();
    if (c.length < 4) { msg.textContent = 'Le code a 5 caractères.'; return; }
    msg.textContent = 'Recherche de la partie…';
    const r = await post('/api/salle/rejoindre', {code: c});
    if (r.erreur) { msg.textContent = r.erreur; return; }
    if (r.ici) { msg.textContent = 'Vous êtes déjà dans cette partie.'; return; }
    msg.textContent = 'Connexion…';
    if (r.lan && await joignable(r.lan)) { location.href = r.lan.replace(/\/$/, '') + '/'; return; }
    if (r.net && await joignable(r.net)) { location.href = r.net.replace(/\/$/, '') + '/'; return; }
    msg.textContent = r.net ? 'La partie ne répond pas. Réessayez dans un instant.'
      : 'Partie injoignable : elle n\'est pas sur ce Wi-Fi et n\'est pas ouverte sur Internet.';
  };
})();
