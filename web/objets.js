/* Les objets dessinés (SVG) des décors : des choses posées sur la table, jamais un fond.
   Dessins sobres : dégradés doux, peu de contours, pas de traits « dessin animé ». */
const SVG = (vb, corps, cls = '') => `<svg class="objet ${cls}" viewBox="${vb}" aria-hidden="true">${corps}</svg>`;

const OBJ = {
  /* Cooper : la tasse du Double R, le donut au sucre, la part de cherry pie, le dictaphone pour Diane */
  tasse: SVG('0 0 200 170', `<defs>
      <linearGradient id="t-cer" x1="0" x2="1"><stop offset="0" stop-color="#d8d3c8"/><stop offset=".3" stop-color="#fbfaf6"/>
        <stop offset=".62" stop-color="#ece8df"/><stop offset="1" stop-color="#b9b2a4"/></linearGradient>
      <radialGradient id="t-cafe" cx=".45" cy=".4" r=".7"><stop offset="0" stop-color="#3a2416"/><stop offset=".7" stop-color="#170d07"/><stop offset="1" stop-color="#0b0604"/></radialGradient>
      <linearGradient id="t-sou" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#f3f0e9"/><stop offset="1" stop-color="#bdb6a8"/></linearGradient></defs>
    <ellipse cx="98" cy="150" rx="92" ry="15" fill="#0007"/>
    <ellipse cx="98" cy="142" rx="88" ry="17" fill="url(#t-sou)"/><ellipse cx="98" cy="140" rx="56" ry="9" fill="#d6d0c4"/>
    <path d="M146 72c26-2 32 34 4 40" fill="none" stroke="#ddd8cd" stroke-width="11" stroke-linecap="round"/>
    <path d="M146 72c26-2 32 34 4 40" fill="none" stroke="#fff" stroke-opacity=".5" stroke-width="3" stroke-linecap="round"/>
    <path d="M44 58h108l-8 66c-1 10-9 16-19 16H71c-10 0-18-6-19-16z" fill="url(#t-cer)"/>
    <path d="M47 76h102" stroke="#9c3a2c" stroke-width="3" opacity=".8"/><path d="M48 82h100" stroke="#9c3a2c" stroke-width="1.2" opacity=".6"/>
    <ellipse cx="98" cy="58" rx="54" ry="11" fill="#f6f3ed"/><ellipse cx="98" cy="59" rx="47" ry="7.5" fill="url(#t-cafe)"/>
    <ellipse cx="84" cy="57" rx="14" ry="2" fill="#fff" opacity=".12"/>
    <g class="vapeur" fill="none" stroke="#fff" stroke-opacity=".28" stroke-width="5" stroke-linecap="round">
      <path d="M80 44c-9-10 9-14 0-26"/><path d="M100 42c-9-10 9-14 0-26"/><path d="M120 44c-9-10 9-14 0-26"/></g>`, 'fume'),
  donut: SVG('0 0 170 120', `<defs>
      <radialGradient id="d-pate" cx=".5" cy=".45" r=".6"><stop offset=".55" stop-color="#e2a35a"/><stop offset=".85" stop-color="#b8743a"/><stop offset="1" stop-color="#8d5426"/></radialGradient>
      <radialGradient id="d-glace" cx=".42" cy=".35" r=".7"><stop offset="0" stop-color="#fff7e6" stop-opacity=".95"/><stop offset=".6" stop-color="#f3dcb2" stop-opacity=".75"/><stop offset="1" stop-color="#e9c48a" stop-opacity=".55"/></radialGradient></defs>
    <ellipse cx="85" cy="102" rx="70" ry="12" fill="#0007"/>
    <path fill-rule="evenodd" fill="url(#d-pate)" d="M15 64c0-26 31-44 70-44s70 18 70 44-31 40-70 40-70-14-70-40zm52-3c0 6 8 10 18 10s18-4 18-10-8-10-18-10-18 4-18 10z"/>
    <path fill-rule="evenodd" fill="url(#d-glace)" d="M22 60c0-21 28-35 63-35s63 14 63 35c0 7-6 6-9 11-4 5-10 1-15 6-6 5-13 0-20 4-7 3-12-1-19 0-8 1-13 4-20-1-7-4-12 1-18-5-5-5-9-1-14-6-4-4-11-3-11-9zm45 1c0 6 8 10 18 10s18-4 18-10-8-10-18-10-18 4-18 10z"/>
    <path d="M40 46c10-9 26-13 40-13" stroke="#fff" stroke-opacity=".7" stroke-width="5" stroke-linecap="round" fill="none"/>
    <g fill="#fff" opacity=".85"><circle cx="58" cy="40" r="1.2"/><circle cx="96" cy="34" r="1.1"/><circle cx="122" cy="48" r="1.3"/>
      <circle cx="44" cy="64" r="1"/><circle cx="130" cy="64" r="1.1"/><circle cx="74" cy="78" r="1"/><circle cx="108" cy="80" r="1.2"/></g>`),
  tarte: SVG('0 0 200 130', `<defs><linearGradient id="p-pate" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#f0c27a"/><stop offset="1" stop-color="#b9772f"/></linearGradient>
      <linearGradient id="p-assiette" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#f7f4ee"/><stop offset="1" stop-color="#c9c2b4"/></linearGradient></defs>
    <ellipse cx="100" cy="112" rx="94" ry="16" fill="#0007"/><ellipse cx="100" cy="104" rx="92" ry="20" fill="url(#p-assiette)"/>
    <ellipse cx="100" cy="102" rx="70" ry="13" fill="#e4dfd4"/>
    <path d="M36 92L150 58l12 30-120 22z" fill="#7d0a16"/><path d="M36 92l120-22 6 18-120 22z" fill="#5c0710"/>
    <path d="M36 92L150 58" stroke="url(#p-pate)" stroke-width="10" stroke-linecap="round"/>
    <path d="M150 58l12 30" stroke="#d99a4c" stroke-width="12" stroke-linecap="round"/>
    <g stroke="#e7b06a" stroke-width="6" stroke-linecap="round"><path d="M64 84l14 14"/><path d="M92 76l16 16"/><path d="M120 68l16 16"/></g>
    <g fill="#a10f1f"><circle cx="58" cy="95" r="4.5"/><circle cx="88" cy="90" r="4"/><circle cx="118" cy="84" r="4.5"/><circle cx="140" cy="80" r="3.5"/></g>
    <g fill="#fff" opacity=".35"><circle cx="57" cy="93" r="1.4"/><circle cx="117" cy="82" r="1.4"/></g>`),
  tarte_entiere: SVG('0 0 220 150', `<defs><radialGradient id="pe-c" cx=".5" cy=".45" r=".6"><stop offset="0" stop-color="#b3121f"/><stop offset="1" stop-color="#6d0711"/></radialGradient>
      <linearGradient id="pe-a" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#f7f4ee"/><stop offset="1" stop-color="#c9c2b4"/></linearGradient></defs>
    <ellipse cx="110" cy="128" rx="104" ry="18" fill="#0007"/><ellipse cx="110" cy="118" rx="104" ry="26" fill="url(#pe-a)"/>
    <ellipse cx="110" cy="110" rx="86" ry="26" fill="#c8843b"/><ellipse cx="110" cy="104" rx="80" ry="22" fill="url(#pe-c)"/>
    <g stroke="#ecb46a" stroke-width="7" stroke-linecap="round" opacity=".95">
      <path d="M56 92l38 30"/><path d="M84 84l52 40"/><path d="M118 82l42 32"/><path d="M150 88l18 14"/>
      <path d="M164 92l-38 30"/><path d="M136 84l-52 40"/><path d="M102 82l-42 32"/><path d="M70 88l-18 14"/></g>
    <ellipse cx="110" cy="104" rx="84" ry="24" fill="none" stroke="#e0a457" stroke-width="7"/>`),
  dictaphone: SVG('0 0 130 200', `<defs><linearGradient id="dc-b" x1="0" x2="1"><stop offset="0" stop-color="#2b2d31"/><stop offset=".5" stop-color="#45484e"/><stop offset="1" stop-color="#1f2124"/></linearGradient></defs>
    <ellipse cx="66" cy="192" rx="54" ry="7" fill="#0007"/>
    <rect x="18" y="20" width="96" height="168" rx="12" fill="url(#dc-b)"/>
    <rect x="18" y="20" width="96" height="168" rx="12" fill="none" stroke="#5c6067" stroke-width="1.5"/>
    <rect x="30" y="36" width="72" height="44" rx="4" fill="#111"/>
    <rect x="34" y="40" width="64" height="36" rx="3" fill="#2a2016"/>
    <g fill="#d8cfb8"><circle cx="50" cy="58" r="9"/><circle cx="82" cy="58" r="9"/></g>
    <g fill="#2a2016"><circle cx="50" cy="58" r="3"/><circle cx="82" cy="58" r="3"/></g>
    <path d="M59 58h14" stroke="#5a4630" stroke-width="5"/>
    <g fill="#3a3d43"><circle cx="40" cy="100" r="2"/><circle cx="52" cy="100" r="2"/><circle cx="64" cy="100" r="2"/><circle cx="76" cy="100" r="2"/><circle cx="88" cy="100" r="2"/>
      <circle cx="46" cy="110" r="2"/><circle cx="58" cy="110" r="2"/><circle cx="70" cy="110" r="2"/><circle cx="82" cy="110" r="2"/>
      <circle cx="40" cy="120" r="2"/><circle cx="52" cy="120" r="2"/><circle cx="64" cy="120" r="2"/><circle cx="76" cy="120" r="2"/><circle cx="88" cy="120" r="2"/></g>
    <rect x="30" y="140" width="72" height="8" rx="2" fill="#191b1e"/>
    <g fill="#8d939c"><rect x="24" y="10" width="16" height="12" rx="2"/><rect x="46" y="10" width="16" height="12" rx="2"/><rect x="68" y="10" width="16" height="12" rx="2"/></g>
    <rect x="90" y="10" width="16" height="12" rx="2" fill="#c0262b"/>
    <circle cx="98" cy="160" r="4" fill="#ff3b30" class="clignote"/><text x="38" y="164" font-family="Arial" font-size="8" fill="#8d939c" letter-spacing="1">DIANE…</text>`),

  /* Truman : le chapeau et l'étoile du shérif */
  chapeau: SVG('0 0 220 120', `<defs><linearGradient id="ch-f" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#8a6a45"/><stop offset="1" stop-color="#4f3a22"/></linearGradient></defs>
    <ellipse cx="110" cy="104" rx="104" ry="13" fill="#0007"/>
    <path d="M6 88c10 14 56 20 104 20s94-6 104-20c-12-10-46-12-104-12S18 78 6 88z" fill="#5c4428"/>
    <path d="M58 82c-2-30 4-62 22-66 10-2 18 8 30 8s20-10 30-8c18 4 24 36 22 66-16 6-34 8-52 8s-36-2-52-8z" fill="url(#ch-f)"/>
    <path d="M60 70c16 6 34 8 50 8s34-2 50-8l2 12c-16 6-34 8-52 8s-36-2-52-8z" fill="#2c2015"/>
    <path d="M110 24c-4 14-4 34 0 46" stroke="#3b2b19" stroke-width="3" fill="none" opacity=".6"/>`),
  etoile_sherif: SVG('0 0 120 120', `<defs><radialGradient id="es" cx=".4" cy=".35" r=".7"><stop offset="0" stop-color="#fff3c4"/><stop offset=".5" stop-color="#d9b04a"/><stop offset="1" stop-color="#8a6516"/></radialGradient></defs>
    <ellipse cx="62" cy="112" rx="40" ry="6" fill="#0006"/>
    <path d="M60 6l12 26 28-4-18 22 18 22-28-4-12 26-12-26-28 4 18-22-18-22 28 4z" fill="url(#es)" stroke="#7a5a12" stroke-width="1.5"/>
    <g fill="url(#es)" stroke="#7a5a12"><circle cx="60" cy="6" r="5"/><circle cx="100" cy="28" r="5"/><circle cx="100" cy="72" r="5"/>
      <circle cx="60" cy="94" r="5"/><circle cx="20" cy="72" r="5"/><circle cx="20" cy="28" r="5"/></g>
    <circle cx="60" cy="50" r="19" fill="none" stroke="#7a5a12" stroke-width="1.5"/>
    <text x="60" y="47" text-anchor="middle" font-family="Georgia" font-size="7" font-weight="700" fill="#5c430c">SHERIFF</text>
    <text x="60" y="58" text-anchor="middle" font-family="Georgia" font-size="5.5" fill="#5c430c">TWIN PEAKS</text>`),

  /* Audrey : la queue de cerise nouée avec la langue, les chaussures bicolores, la clé du Great Northern */
  cerise_noeud: SVG('0 0 140 130', `<ellipse cx="64" cy="120" rx="46" ry="7" fill="#0006"/>
    <defs><radialGradient id="cr" cx=".35" cy=".3" r=".75"><stop offset="0" stop-color="#e2384a"/><stop offset=".6" stop-color="#9c0d1d"/><stop offset="1" stop-color="#5a0610"/></radialGradient></defs>
    <circle cx="44" cy="96" r="22" fill="url(#cr)"/><ellipse cx="36" cy="88" rx="6" ry="4" fill="#fff" opacity=".45"/>
    <path d="M48 76c4-14 12-24 24-30" fill="none" stroke="#5f7a2a" stroke-width="3" stroke-linecap="round"/>
    <path d="M72 46c10-6 20 2 14 10s-18 2-12-8c6-10 22-8 30 4" fill="none" stroke="#5f7a2a" stroke-width="3" stroke-linecap="round"/>
    <path d="M104 52c8 10 10 20 10 28" fill="none" stroke="#5f7a2a" stroke-width="3" stroke-linecap="round"/>`),
  souliers: SVG('0 0 220 110', `<ellipse cx="110" cy="100" rx="104" ry="9" fill="#0007"/>
    <g><path d="M10 84c0-14 8-22 22-22 18 0 30-10 44-10 14 0 22 12 22 26v10H14c-3 0-4-2-4-4z" fill="#f2efe8"/>
      <path d="M40 60c14 0 26-8 36-8 14 0 22 12 22 26v4H60c-8-6-14-14-20-22z" fill="#1d1b1a"/>
      <path d="M10 88h88v6H12z" fill="#3a2a20"/><path d="M60 62l14 6M64 58l14 6" stroke="#ccc" stroke-width="1.5"/></g>
    <g transform="translate(112 0)"><path d="M10 84c0-14 8-22 22-22 18 0 30-10 44-10 14 0 22 12 22 26v10H14c-3 0-4-2-4-4z" fill="#f2efe8"/>
      <path d="M40 60c14 0 26-8 36-8 14 0 22 12 22 26v4H60c-8-6-14-14-20-22z" fill="#1d1b1a"/>
      <path d="M10 88h88v6H12z" fill="#3a2a20"/><path d="M60 62l14 6M64 58l14 6" stroke="#ccc" stroke-width="1.5"/></g>`),
  cle_gn: SVG('0 0 120 190', `<ellipse cx="60" cy="182" rx="40" ry="6" fill="#0006"/>
    <path d="M30 8h60l10 12v86c0 8-6 14-14 14H34c-8 0-14-6-14-14V20z" fill="#7a2b1d"/>
    <path d="M30 8h60l10 12v86c0 8-6 14-14 14H34c-8 0-14-6-14-14V20z" fill="none" stroke="#c9a24a" stroke-width="2"/>
    <circle cx="60" cy="22" r="6" fill="#2a120c" stroke="#c9a24a" stroke-width="2"/>
    <text x="60" y="52" text-anchor="middle" font-family="Georgia" font-size="9" letter-spacing="1" fill="#e6c36a">GREAT</text>
    <text x="60" y="64" text-anchor="middle" font-family="Georgia" font-size="9" letter-spacing="1" fill="#e6c36a">NORTHERN</text>
    <text x="60" y="96" text-anchor="middle" font-family="Georgia" font-size="22" font-weight="700" fill="#e6c36a">315</text>
    <path d="M60 28v4" stroke="#c9a24a" stroke-width="3"/>
    <g fill="#c9a24a"><circle cx="60" cy="132" r="12"/><rect x="56" y="140" width="8" height="40"/><rect x="64" y="160" width="10" height="5"/><rect x="64" y="170" width="7" height="5"/></g>
    <circle cx="60" cy="132" r="5" fill="#2a120c"/>`),

  /* BOB */
  bougie: SVG('0 0 60 140', `<defs><radialGradient id="o-fl" cx=".5" cy=".7" r=".6"><stop offset="0" stop-color="#fff6c2"/><stop offset=".45" stop-color="#ffb02e"/><stop offset="1" stop-color="#ff4d00" stop-opacity="0"/></radialGradient></defs>
    <ellipse cx="30" cy="34" rx="24" ry="32" fill="url(#o-fl)" class="flamme"/>
    <path d="M30 6c10 16 12 30 0 40-12-10-10-24 0-40z" fill="#ffcf5a" class="flamme"/>
    <path d="M30 56v8" stroke="#222" stroke-width="2"/><rect x="18" y="62" width="24" height="74" rx="3" fill="#efe6d2"/>
    <path d="M18 70c6 4 12-2 24 2" fill="none" stroke="#d8cdb4" stroke-width="3"/>`),

  /* Jacoby (Dr. Amp) : la pelle dorée */
  pelle: SVG('0 0 120 330', `<defs><linearGradient id="pl-or" x1="0" x2="1"><stop offset="0" stop-color="#8a6416"/><stop offset=".35" stop-color="#ffe9a0"/>
      <stop offset=".6" stop-color="#d9a92c"/><stop offset="1" stop-color="#7a5510"/></linearGradient></defs>
    <ellipse cx="62" cy="322" rx="46" ry="7" fill="#0007"/>
    <path d="M44 10h32l-4 14H48z" fill="url(#pl-or)"/><rect x="40" y="2" width="40" height="12" rx="6" fill="none" stroke="url(#pl-or)" stroke-width="6"/>
    <rect x="54" y="20" width="12" height="190" rx="5" fill="url(#pl-or)"/>
    <path d="M50 206h20l4 14H46z" fill="url(#pl-or)"/>
    <path d="M22 226c0-6 8-10 38-10s38 4 38 10v54c0 20-18 40-38 44-20-4-38-24-38-44z" fill="url(#pl-or)"/>
    <path d="M36 236v44c0 12 10 26 24 30" stroke="#fff6cf" stroke-width="4" fill="none" opacity=".55"/>`),

  /* Laura */
  demicoeur: SVG('0 0 140 140', `<defs><linearGradient id="dm" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#fff0b8"/><stop offset=".45" stop-color="#e2b84e"/><stop offset="1" stop-color="#8f6716"/></linearGradient></defs>
    <path d="M14 10c30 30 60 40 66 52" fill="none" stroke="#d9b24a" stroke-width="2" stroke-dasharray="1.5 3.5"/>
    <path d="M126 10c-20 28-38 40-46 52" fill="none" stroke="#d9b24a" stroke-width="2" stroke-dasharray="1.5 3.5"/>
    <circle cx="80" cy="64" r="4" fill="none" stroke="#d9b24a" stroke-width="2"/>
    <path d="M80 70C70 58 42 58 42 82c0 20 22 32 38 48l5-11-6-8 8-9-7-8 7-9-6-8z" fill="url(#dm)" stroke="#7a5510" stroke-width="1.5"/>
    <path d="M52 78c2-7 9-10 15-9" stroke="#fff" stroke-opacity=".7" stroke-width="3" fill="none" stroke-linecap="round"/>`),

  /* Janey-E */
  etoile: SVG('0 0 20 20', `<path d="M10 0l2 8 8 2-8 2-2 8-2-8-8-2 8-2z" fill="#f2e3a6"/>`, 'scintille'),

  /* Norma : l'enseigne du Double R */
  enseigne_rr: SVG('0 0 260 150', `<defs><filter id="rr-glow" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="3" result="b"/>
      <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter></defs>
    <path d="M40 140v-26M220 140v-26" stroke="#3a3a3a" stroke-width="6"/>
    <rect x="8" y="10" width="244" height="108" rx="18" fill="#1a0c0e" stroke="#4a2a2c" stroke-width="3"/>
    <rect x="18" y="20" width="224" height="88" rx="12" fill="none" stroke="#ff5a6e" stroke-width="3" filter="url(#rr-glow)" class="neon"/>
    <text x="130" y="72" text-anchor="middle" font-family="Brush Script MT,Segoe Script,cursive" font-size="44" fill="#ffe7ea" stroke="#ff3b58" stroke-width="1.5" filter="url(#rr-glow)" class="neon">Double R</text>
    <text x="130" y="98" text-anchor="middle" font-family="Arial" font-size="13" letter-spacing="9" fill="#ffd36a" filter="url(#rr-glow)">DINER</text>`),

  /* Shelly : la cherry pie (tarte_entiere) */

  /* Lucy */

  /* Donna : l'enseigne du One-Eyed Jack's, au trait */
  one_eyed_jack: SVG('0 0 220 200', `<defs><filter id="oj-n" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="2.5" result="b"/>
      <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter></defs>
    <g fill="none" stroke-linecap="round" stroke-linejoin="round" stroke-width="4">
      <rect x="10" y="10" width="200" height="180" rx="14" stroke="#3d8bff" filter="url(#oj-n)" class="neon"/>
      <path d="M58 72l-8-42 26 20 16-28 14 28 22-24 4 46" stroke="#f2c230"/>
      <path d="M56 74c26-6 50-6 76-2" stroke="#f2c230"/>
      <path d="M60 76c-14 20-20 48-14 76l30 6" stroke="#ff5a5a"/>
      <path d="M96 76c10 12 16 22 18 32l-8 6 10 8-6 10c2 10-4 18-16 18l-14-4" stroke="#ffb3a1"/>
      <path d="M102 102l14-6-4 12z" stroke="#3d8bff" filter="url(#oj-n)"/>
      <path d="M70 160h70M78 160v18M94 160v18M110 160v18M126 160v18" stroke="#f2c230"/>
      <path d="M150 48c10-6 18 0 14 10-4 8-12 6-12 16 0 8 10 10 14 4" stroke="#c9c9c9"/></g>`),

  /* Bobby */
  cigarettes: SVG('0 0 140 120', `<ellipse cx="70" cy="112" rx="56" ry="7" fill="#0006"/>
    <rect x="30" y="30" width="80" height="80" rx="4" fill="#f4f1ea"/><rect x="30" y="58" width="80" height="52" fill="#b3121f"/>
    <path d="M30 58l40 18 40-18" fill="#f4f1ea"/>
    <g fill="#f8f5ee"><rect x="42" y="12" width="10" height="26" rx="2"/><rect x="56" y="6" width="10" height="32" rx="2"/><rect x="70" y="14" width="10" height="24" rx="2"/></g>
    <g fill="#d9a35a"><rect x="42" y="12" width="10" height="7" rx="2"/><rect x="56" y="6" width="10" height="7" rx="2"/><rect x="70" y="14" width="10" height="7" rx="2"/></g>`),

  /* Pete */
  percolateur: SVG('0 0 140 190', `<defs><linearGradient id="o-alu" x1="0" x2="1"><stop offset="0" stop-color="#8d969c"/><stop offset=".35" stop-color="#eef2f4"/><stop offset=".6" stop-color="#b7c0c5"/><stop offset="1" stop-color="#6d767c"/></linearGradient>
    <clipPath id="o-dome"><circle cx="62" cy="30" r="17"/></clipPath></defs>
    <ellipse cx="66" cy="182" rx="56" ry="7" fill="#00000055"/>
    <path d="M30 56h64l10 116a8 8 0 0 1-8 8H28a8 8 0 0 1-8-8z" fill="url(#o-alu)"/>
    <path d="M28 56h68l-6-10H34z" fill="#c9d1d6"/><path d="M94 70l26-18-4 12-20 18" fill="url(#o-alu)"/>
    <path d="M24 76c-22 6-22 64 0 70" fill="none" stroke="#2b1a10" stroke-width="10" stroke-linecap="round"/>
    <circle cx="62" cy="30" r="17" fill="#e8eef2aa" stroke="#cfd8dc" stroke-width="2"/>
    <g clip-path="url(#o-dome)"><rect x="40" y="30" width="44" height="20" fill="#5b3418"/>
      <g class="poisson"><path d="M52 31c5-6 14-6 18 0-4 6-13 6-18 0z" fill="#f08a2c"/><path d="M70 31l6-5v10z" fill="#f08a2c"/><circle cx="56" cy="30" r="1.2" fill="#111"/></g></g>
    <path d="M58 13h8v-6h-8z" fill="#9aa3a8"/>`),

  /* Albert */
  rose: SVG('0 0 64 64', `<path d="M32 40v20" stroke="#3f7a3a" stroke-width="3"/><path d="M32 50c-8-2-12-8-12-8 8-2 12 4 12 8z" fill="#4f8f45"/>
    <path d="M32 54c8-2 12-8 12-8-8-2-12 4-12 8z" fill="#4f8f45"/>
    <path d="M14 22c0 12 8 20 18 20s18-8 18-20c-4 4-10 4-12 0-2 4-10 4-12 0-2 4-8 4-12 0z" fill="#2c55c9"/>
    <path d="M20 18c2 10 6 16 12 16s10-6 12-16c-6 4-18 4-24 0z" fill="#3f72f0"/>
    <path d="M24 16c2 6 4 10 8 10s6-4 8-10c-2-6-14-6-16 0z" fill="#6f9cff"/><path d="M28 14c2 3 6 3 8 0" stroke="#1b3a98" stroke-width="2" fill="none"/>`),

  /* Hawk : la plume et l'insigne */
  plume: SVG('0 0 120 420', `<defs><linearGradient id="pm" x1="0" x2="1"><stop offset="0" stop-color="#f7f2e8"/><stop offset=".55" stop-color="#e7dccb"/><stop offset="1" stop-color="#cbbca4"/></linearGradient></defs>
    <path d="M60 414c0-60 2-150 8-246" stroke="#cfc3ae" stroke-width="3" fill="none"/>
    <path d="M68 168C64 110 70 46 86 6c18 44 16 112-6 176-8 22-14 36-14 36s-14-20-20-44c-6-22-2-38 22-6z" fill="url(#pm)"/>
    <path d="M86 6C70 60 66 120 66 216" stroke="#b5a68c" stroke-width="2" fill="none"/>
    <g stroke="#3b302a" stroke-width="13" fill="none" opacity=".55"><path d="M74 46c6 4 14 4 20 0"/><path d="M70 92c8 4 18 4 24-2"/><path d="M68 140c8 4 18 2 22-4"/></g>
    <g stroke="#c2b399" stroke-width="1" opacity=".8"><path d="M84 20l10-8M82 34l12-8M80 52l14-8M78 70l14-8M76 88l14-8M74 106l14-8M72 124l12-8M70 142l12-8M68 160l10-8"/>
      <path d="M84 24l-12-6M82 42l-14-6M80 60l-14-6M78 78l-14-6M76 96l-14-6M74 114l-12-6M72 132l-12-6M70 150l-10-6M68 168l-10-6"/></g>
    <g stroke="#e9e0cf" stroke-width="1.2"><path d="M62 230l-14 10M62 240l-10 14M64 236l12 12"/></g>`),
  insigne_hawk: SVG('0 0 120 140', `<defs><radialGradient id="ih" cx=".4" cy=".3" r=".8"><stop offset="0" stop-color="#fff6d0"/><stop offset=".5" stop-color="#cfa43e"/><stop offset="1" stop-color="#7a5a12"/></radialGradient></defs>
    <ellipse cx="60" cy="132" rx="40" ry="6" fill="#0006"/>
    <path d="M60 6l40 14v40c0 34-20 56-40 68-20-12-40-34-40-68V20z" fill="url(#ih)" stroke="#6b4c0e" stroke-width="2"/>
    <path d="M60 18l30 10v32c0 26-15 44-30 54-15-10-30-28-30-54V28z" fill="none" stroke="#6b4c0e" stroke-width="1.2"/>
    <text x="60" y="52" text-anchor="middle" font-family="Georgia" font-size="9" font-weight="700" fill="#4a3407">DEPUTY</text>
    <text x="60" y="68" text-anchor="middle" font-family="Georgia" font-size="7" fill="#4a3407">SHERIFF</text>
    <text x="60" y="88" text-anchor="middle" font-family="Georgia" font-size="7" fill="#4a3407">TWIN PEAKS</text>`),

  /* Ben, Josie */
  cigare: SVG('0 0 220 80', `<g class="fumee" fill="none" stroke="#ffffff40" stroke-width="3" stroke-linecap="round"><path d="M200 28c-10-8 8-12-2-22"/><path d="M188 30c-8-10 8-12 0-24"/></g>
    <path d="M14 52l170-26c8-1 12 3 12 9s-4 10-12 11L18 64c-8 1-12-2-12-6s3-6 8-6z" fill="#7a4a24"/>
    <path d="M14 52l170-26c4 0 6 2 6 4L18 56c-4 0-6-2-4-4z" fill="#9a6232"/>
    <path d="M40 48l26-4 2 12-26 4z" fill="#c8202e"/><path d="M44 50l18-3" stroke="#d9b45a" stroke-width="2"/>
    <path d="M184 26c8-1 12 3 12 9s-4 10-12 11z" fill="#9b9b9b"/><path d="M190 32l6-1" stroke="#ff6a1a" stroke-width="3"/>`),
  bouton: SVG('0 0 120 120', `<ellipse cx="60" cy="108" rx="40" ry="7" fill="#00000055"/>
    <circle cx="60" cy="58" r="44" fill="#7a4a24"/><circle cx="60" cy="58" r="44" fill="none" stroke="#4e2c12" stroke-width="3"/>
    <g fill="none" stroke="#5b3518" stroke-width="2"><ellipse cx="56" cy="62" rx="30" ry="24"/><ellipse cx="54" cy="64" rx="18" ry="13"/><ellipse cx="53" cy="65" rx="7" ry="5"/></g>
    <ellipse cx="44" cy="40" rx="14" ry="8" fill="#ffffff22"/>`),

  /* Maddy */
  grosses_lunettes: SVG('0 0 170 80', `<g fill="#f2b8a040" stroke="#b5432f" stroke-width="7"><ellipse cx="44" cy="40" rx="36" ry="32"/><ellipse cx="126" cy="40" rx="36" ry="32"/></g>
    <path d="M80 34c4-6 6-6 10 0" fill="none" stroke="#b5432f" stroke-width="6"/><ellipse cx="34" cy="28" rx="12" ry="6" fill="#ffffff55"/><ellipse cx="116" cy="28" rx="12" ry="6" fill="#ffffff55"/>`),

  /* James : sa moto */
  moto: SVG('0 0 300 180', `<defs><linearGradient id="mt-c" x1="0" x2="1"><stop offset="0" stop-color="#8d969c"/><stop offset=".4" stop-color="#f2f5f7"/><stop offset="1" stop-color="#7a838a"/></linearGradient></defs>
    <ellipse cx="150" cy="170" rx="140" ry="8" fill="#0007"/>
    <g fill="none" stroke="#111" stroke-width="12"><circle cx="62" cy="128" r="38"/><circle cx="238" cy="128" r="38"/></g>
    <g fill="none" stroke="url(#mt-c)" stroke-width="3"><circle cx="62" cy="128" r="28"/><circle cx="238" cy="128" r="28"/></g>
    <g class="rayons" stroke="#bbb" stroke-width="1.4"><circle cx="62" cy="128" r="28" fill="none" stroke="none"/><path d="M62 100v56M34 128h56M42 108l40 40M42 148l40-40"/></g>
    <g class="rayons" stroke="#bbb" stroke-width="1.4"><circle cx="238" cy="128" r="28" fill="none" stroke="none"/><path d="M238 100v56M210 128h56M218 108l40 40M218 148l40-40"/></g>
    <path d="M62 128l40-50h70l26 50" fill="none" stroke="#1d1d1f" stroke-width="7" stroke-linejoin="round"/>
    <path d="M100 84c10-22 50-26 74-10l-6 20H106z" fill="#141416"/><path d="M112 76c14-10 36-10 50-2" stroke="#ffffff40" stroke-width="3" fill="none"/>
    <path d="M178 88c16-6 34-4 44 4l-10 10h-36z" fill="#2a1a12"/>
    <rect x="120" y="100" width="44" height="30" rx="6" fill="url(#mt-c)"/><g stroke="#666" stroke-width="2"><path d="M126 104v22M134 104v22M142 104v22M150 104v22M158 104v22"/></g>
    <path d="M150 132l70 6" stroke="url(#mt-c)" stroke-width="7" stroke-linecap="round"/>
    <path d="M238 128l-40-78" stroke="url(#mt-c)" stroke-width="7" stroke-linecap="round"/>
    <path d="M194 46l-18-6M196 48l30-14" stroke="#1d1d1f" stroke-width="5" stroke-linecap="round"/>
    <circle cx="214" cy="62" r="11" fill="url(#mt-c)"/><circle cx="216" cy="62" r="6" fill="#fff8d0"/>`),

  /* Big Ed : la pompe à essence (sans texte) */
  pompe: SVG('0 0 160 300', `<defs><linearGradient id="pp-r" x1="0" x2="1"><stop offset="0" stop-color="#7c0f19"/><stop offset=".35" stop-color="#d0283a"/><stop offset=".7" stop-color="#b51d2c"/><stop offset="1" stop-color="#6a0c15"/></linearGradient>
      <radialGradient id="pp-g" cx=".4" cy=".35" r=".7"><stop offset="0" stop-color="#fffdf4"/><stop offset=".7" stop-color="#f3ead6"/><stop offset="1" stop-color="#cfc3a6"/></radialGradient>
      <linearGradient id="pp-ch" x1="0" x2="1"><stop offset="0" stop-color="#8d969c"/><stop offset=".45" stop-color="#f2f5f7"/><stop offset="1" stop-color="#7a838a"/></linearGradient></defs>
    <ellipse cx="74" cy="292" rx="66" ry="8" fill="#0007"/>
    <circle cx="72" cy="40" r="32" fill="url(#pp-g)"/><circle cx="72" cy="40" r="32" fill="none" stroke="url(#pp-ch)" stroke-width="5"/>
    <circle cx="72" cy="40" r="18" fill="none" stroke="#c4202f" stroke-width="5"/>
    <rect x="62" y="72" width="20" height="10" fill="url(#pp-ch)"/>
    <path d="M30 86c0-6 4-8 10-8h64c6 0 10 2 10 8v190c0 6-4 10-10 10H40c-6 0-10-4-10-10z" fill="url(#pp-r)"/>
    <rect x="42" y="100" width="60" height="56" rx="8" fill="#f6f1e2"/><rect x="42" y="100" width="60" height="56" rx="8" fill="none" stroke="url(#pp-ch)" stroke-width="3"/>
    <g fill="#222"><rect x="50" y="110" width="44" height="12" rx="2"/><rect x="50" y="130" width="44" height="12" rx="2"/></g>
    <g fill="#ffb347" opacity=".9"><rect x="54" y="113" width="6" height="6"/><rect x="62" y="113" width="6" height="6"/><rect x="70" y="113" width="6" height="6"/><rect x="80" y="133" width="6" height="6"/></g>
    <rect x="42" y="170" width="60" height="90" rx="6" fill="#00000022"/><path d="M48 178h48M48 190h48M48 202h48" stroke="#ffffff22" stroke-width="2"/>
    <path d="M114 150h12v56" fill="none" stroke="url(#pp-ch)" stroke-width="6"/>
    <path d="M126 206c0 30 -6 50 -26 58" fill="none" stroke="#1d1d1f" stroke-width="7" stroke-linecap="round"/>
    <path d="M118 120l18-4 6 16-14 10z" fill="#2a2a2a"/><path d="M136 118l12 30" stroke="url(#pp-ch)" stroke-width="5" stroke-linecap="round"/>`),

  /* Log Lady : la bûche */
  buche: SVG('0 0 240 140', `<defs><linearGradient id="bc-e" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#8a6a4a"/><stop offset=".5" stop-color="#6b4f35"/><stop offset="1" stop-color="#3f2c1c"/></linearGradient>
      <radialGradient id="bc-c" cx=".5" cy=".5" r=".55"><stop offset="0" stop-color="#e4c48f"/><stop offset=".85" stop-color="#c79c62"/><stop offset="1" stop-color="#8d6a3c"/></radialGradient></defs>
    <ellipse cx="124" cy="128" rx="110" ry="10" fill="#0007"/>
    <path d="M40 30h160c22 0 36 20 36 44s-14 44-36 44H40z" fill="url(#bc-e)"/>
    <g stroke="#3a2818" stroke-width="2" fill="none" opacity=".55"><path d="M60 40c30 6 70 4 110-2M60 64c40 4 90 6 140 0M56 92c50 6 100 6 150 0M64 108c40 2 80 2 120-2"/></g>
    <path d="M150 34c6 6 4 14-4 16" stroke="#2a1a10" stroke-width="3" fill="none"/>
    <ellipse cx="40" cy="74" rx="34" ry="44" fill="url(#bc-c)"/>
    <g fill="none" stroke="#8d6a3c" stroke-width="1.5"><ellipse cx="40" cy="74" rx="27" ry="35"/><ellipse cx="40" cy="74" rx="20" ry="26"/><ellipse cx="40" cy="74" rx="13" ry="17"/><ellipse cx="40" cy="74" rx="6" ry="8"/></g>`),

  /* Leo : les dés et les chaussures neuves */
  des: SVG('0 0 180 120', `<ellipse cx="90" cy="112" rx="80" ry="8" fill="#0007"/>
    <g transform="rotate(-12 50 66)"><rect x="14" y="30" width="72" height="72" rx="12" fill="#f4f1ea"/><rect x="14" y="30" width="72" height="72" rx="12" fill="none" stroke="#c9c2b4" stroke-width="2"/>
      <g fill="#b3121f"><circle cx="32" cy="48" r="6"/><circle cx="50" cy="66" r="6"/><circle cx="68" cy="84" r="6"/></g></g>
    <g transform="rotate(14 132 70)"><rect x="98" y="36" width="66" height="66" rx="11" fill="#f4f1ea"/><rect x="98" y="36" width="66" height="66" rx="11" fill="none" stroke="#c9c2b4" stroke-width="2"/>
      <g fill="#111"><circle cx="114" cy="52" r="5.5"/><circle cx="148" cy="52" r="5.5"/><circle cx="114" cy="86" r="5.5"/><circle cx="148" cy="86" r="5.5"/><circle cx="131" cy="69" r="5.5"/></g></g>`),
  bottes: SVG('0 0 200 140', `<ellipse cx="100" cy="132" rx="94" ry="8" fill="#0007"/>
    <g><path d="M20 10h36v76c14 6 40 10 40 30v10H16V10z" fill="#3a2414"/><path d="M20 10h36v8H20z" fill="#2a190d"/>
      <path d="M16 116h80v10H16z" fill="#1a0f08"/><path d="M28 30v60" stroke="#5a3a20" stroke-width="2"/></g>
    <g transform="translate(96 0)"><path d="M20 10h36v76c14 6 40 10 40 30v10H16V10z" fill="#4a2e1a"/><path d="M20 10h36v8H20z" fill="#2a190d"/>
      <path d="M16 116h80v10H16z" fill="#1a0f08"/><path d="M28 30v60" stroke="#6a4626" stroke-width="2"/></g>`),

  /* Le Géant : la bague de la grotte du hibou, le nœud papillon à chevrons */
  bague: SVG('0 0 120 110', `<defs><linearGradient id="bg-o" x1="0" x2="1"><stop offset="0" stop-color="#7a5510"/><stop offset=".4" stop-color="#ffe9a0"/><stop offset="1" stop-color="#8a6416"/></linearGradient>
      <radialGradient id="bg-v" cx=".4" cy=".35" r=".7"><stop offset="0" stop-color="#9df0b8"/><stop offset=".6" stop-color="#1f8a4a"/><stop offset="1" stop-color="#0b3d20"/></radialGradient></defs>
    <ellipse cx="60" cy="102" rx="44" ry="6" fill="#0007"/>
    <ellipse cx="60" cy="68" rx="40" ry="28" fill="none" stroke="url(#bg-o)" stroke-width="9"/>
    <path d="M38 40h44l-6 14H44z" fill="url(#bg-o)"/><ellipse cx="60" cy="30" rx="22" ry="16" fill="url(#bg-v)" stroke="url(#bg-o)" stroke-width="4"/>
    <path d="M52 30c4-6 12-6 16 0-4 4-12 4-16 0z" fill="#0b3d20" opacity=".6"/>`),
  noeud_pap: SVG('0 0 160 80', `<defs><pattern id="np-z" width="16" height="16" patternUnits="userSpaceOnUse"><rect width="16" height="16" fill="#f4f1ea"/>
      <path d="M0 4l4 4 4-4 4 4 4-4v6l-4-4-4 4-4-4-4 4z" fill="#111"/><path d="M0 12l4 4 4-4 4 4 4-4" fill="none" stroke="#111" stroke-width="3"/></pattern></defs>
    <ellipse cx="80" cy="74" rx="60" ry="5" fill="#0006"/>
    <path d="M80 40L14 8c-8 20-8 44 0 64z" fill="url(#np-z)"/><path d="M80 40l66-32c8 20 8 44 0 64z" fill="url(#np-z)"/>
    <rect x="68" y="28" width="24" height="24" rx="6" fill="url(#np-z)" stroke="#111" stroke-width="2"/>`),

  /* L'Homme d'ailleurs : la Vénus et le lampadaire de la Red Room */
  venus: SVG('0 0 120 330', `<defs><linearGradient id="vn" x1="0" x2="1"><stop offset="0" stop-color="#8f8a80"/><stop offset=".35" stop-color="#f3efe6"/>
      <stop offset=".7" stop-color="#d8d2c6"/><stop offset="1" stop-color="#8a857b"/></linearGradient></defs>
    <ellipse cx="60" cy="324" rx="46" ry="6" fill="#0008"/>
    <rect x="26" y="284" width="68" height="36" fill="url(#vn)"/><rect x="22" y="278" width="76" height="8" fill="#e2ddd2"/>
    <ellipse cx="62" cy="22" rx="10" ry="12" fill="url(#vn)"/><ellipse cx="58" cy="12" rx="9" ry="6" fill="#d8d2c6"/>
    <path d="M58 33h8l1 9c10 2 20 8 22 18l-3 8c-2-3-5-4-7-3 0 6 2 12 1 18 4 8 4 16 0 24-3 6-6 10-6 14l4 12c6 4 10 10 12 18l4 20
      c3 16 6 34 6 52 0 22-4 38-6 52H34c-2-18-4-38-2-56 2-18 6-34 12-46 2-8 0-12 0-16-6-6-8-14-6-24 2-8 6-12 8-16-1-6 0-12 2-18-4 0-6 2-8 4
      l-4-8c4-10 12-16 22-18z" fill="url(#vn)"/>
    <path d="M47 82c4 6 10 6 14 0M63 82c4 6 10 6 14 0" stroke="#b5afa3" stroke-width="2" fill="none"/>
    <path d="M44 150c10 10 30 14 46 4M40 182c14 16 34 22 54 10M38 220c16 14 36 18 56 6M40 252c14 10 32 12 50 4" stroke="#b5afa3" stroke-width="2.5" fill="none"/>`),
  lampadaire: SVG('0 0 120 320', `<defs><linearGradient id="lp" x1="0" x2="1"><stop offset="0" stop-color="#3a2a1a"/><stop offset=".5" stop-color="#7a5a3a"/><stop offset="1" stop-color="#2a1a10"/></linearGradient>
      <radialGradient id="lp-l" cx=".5" cy=".9" r=".9"><stop offset="0" stop-color="#fff2c8" stop-opacity=".8"/><stop offset="1" stop-color="#fff2c8" stop-opacity="0"/></radialGradient></defs>
    <ellipse cx="60" cy="314" rx="40" ry="6" fill="#0008"/>
    <path d="M24 30h72l14 60H10z" fill="#e9dcc0"/><path d="M24 30h72l14 60H10z" fill="none" stroke="#b9a988" stroke-width="2"/>
    <path d="M14 82h92" stroke="#c9b48c" stroke-width="3"/>
    <rect x="56" y="90" width="8" height="210" fill="url(#lp)"/><path d="M30 304h60l-8-12H38z" fill="url(#lp)"/>`),

  /* Cole : son appareil auditif */
  appareil: SVG('0 0 200 220', `<defs><linearGradient id="ap" x1="0" x2="1"><stop offset="0" stop-color="#b48d6a"/><stop offset=".45" stop-color="#e9c9a6"/><stop offset="1" stop-color="#a07a58"/></linearGradient></defs>
    <ellipse cx="100" cy="212" rx="80" ry="7" fill="#0007"/>
    <path d="M118 30c34 0 52 24 52 60 0 40-22 72-46 76-14 2-20-10-14-24 10-22 20-38 20-58 0-20-10-30-24-34-14-4-12-20 12-20z" fill="url(#ap)"/>
    <path d="M150 60c6 10 6 26 2 40" stroke="#fff" stroke-opacity=".35" stroke-width="5" fill="none" stroke-linecap="round"/>
    <circle cx="150" cy="140" r="6" fill="#6d543d"/><rect x="140" y="44" width="16" height="6" rx="3" fill="#6d543d"/>
    <path d="M112 162c-20 18-50 20-66 10" fill="none" stroke="#d9c3a8" stroke-width="5" stroke-linecap="round"/>
    <path d="M30 152c-10 0-18 10-14 22 4 14 20 18 30 8 8-8 6-26-16-30z" fill="url(#ap)"/>
    <circle cx="26" cy="168" r="4" fill="#6d543d"/>`),
};

/* ===== version 5 : dessins refaits ou ajoutés (remplacent ceux du dessus) ===== */
const SYMBOLE_HIBOU = '<path d="M4 20l15 17 15-17 13-13 13 13 15-17 15 17" fill="none" stroke-linejoin="miter" stroke-linecap="square"/>' +
  '<path d="M34 20l13 14 13-14M60 20l9 10v14" fill="none" stroke-linejoin="miter" stroke-linecap="square"/>';
Object.assign(OBJ, {
  /* Cooper */
  tasse: SVG('0 0 220 180', `<defs>
      <linearGradient id="t5-c" x1="0" x2="1"><stop offset="0" stop-color="#bdb6a9"/><stop offset=".18" stop-color="#ebe7df"/>
        <stop offset=".42" stop-color="#ffffff"/><stop offset=".7" stop-color="#e6e1d7"/><stop offset="1" stop-color="#a9a194"/></linearGradient>
      <linearGradient id="t5-a" x1="0" x2="1"><stop offset="0" stop-color="#d9d3c8"/><stop offset=".5" stop-color="#fbfaf6"/><stop offset="1" stop-color="#b8b0a2"/></linearGradient>
      <radialGradient id="t5-k" cx=".38" cy=".35" r=".8"><stop offset="0" stop-color="#4a2d18"/><stop offset=".55" stop-color="#1c1009"/><stop offset="1" stop-color="#0a0503"/></radialGradient>
      <radialGradient id="t5-s" cx=".5" cy=".4" r=".6"><stop offset="0" stop-color="#ffffff"/><stop offset=".8" stop-color="#e2ddd2"/><stop offset="1" stop-color="#b5ad9f"/></radialGradient>
      <linearGradient id="t5-o" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#000" stop-opacity="0"/><stop offset="1" stop-color="#000" stop-opacity=".25"/></linearGradient></defs>
    <ellipse cx="104" cy="160" rx="100" ry="17" fill="#000" opacity=".45"/>
    <ellipse cx="104" cy="150" rx="96" ry="22" fill="url(#t5-s)"/><ellipse cx="104" cy="147" rx="64" ry="12" fill="#d8d2c6"/>
    <ellipse cx="104" cy="146" rx="52" ry="8" fill="#000" opacity=".18"/>
    <path d="M154 70c34-6 46 40 6 52" fill="none" stroke="url(#t5-a)" stroke-width="15" stroke-linecap="round"/>
    <path d="M156 78c22-2 28 28 2 36" fill="none" stroke="#000" stroke-opacity=".15" stroke-width="4" stroke-linecap="round"/>
    <path d="M48 56h112l-7 78c-1 12-10 18-22 18H77c-12 0-21-6-22-18z" fill="url(#t5-c)"/>
    <path d="M48 56h112l-7 78c-1 12-10 18-22 18H77c-12 0-21-6-22-18z" fill="url(#t5-o)"/>
    <ellipse cx="104" cy="56" rx="56" ry="12" fill="#faf8f3"/><ellipse cx="104" cy="57.5" rx="50" ry="9" fill="#cfc8bb"/>
    <ellipse cx="104" cy="59" rx="47" ry="7.6" fill="url(#t5-k)"/>
    <path d="M78 57c10-3 26-4 40-2" stroke="#fff" stroke-opacity=".22" stroke-width="2.5" fill="none" stroke-linecap="round"/>
    <g class="vapeur" fill="none" stroke="#fff" stroke-opacity=".22" stroke-width="6" stroke-linecap="round">
      <path d="M86 42c-10-12 10-16 0-30"/><path d="M106 40c-10-12 10-16 0-30"/><path d="M126 42c-10-12 10-16 0-30"/></g>`, 'fume'),
  donut: SVG('0 0 200 130', `<defs>
      <radialGradient id="d5-p" cx=".5" cy=".42" r=".62"><stop offset=".5" stop-color="#e8b06a"/><stop offset=".8" stop-color="#c47f3e"/><stop offset="1" stop-color="#8a5226"/></radialGradient>
      <linearGradient id="d5-g" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fffaf0" stop-opacity=".95"/><stop offset=".6" stop-color="#f7e6c6" stop-opacity=".8"/><stop offset="1" stop-color="#eccf9c" stop-opacity=".5"/></linearGradient>
      <linearGradient id="d5-t" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#6b3c18"/><stop offset="1" stop-color="#c88a4c"/></linearGradient></defs>
    <ellipse cx="100" cy="112" rx="88" ry="15" fill="#000" opacity=".45"/>
    <ellipse cx="100" cy="80" rx="88" ry="38" fill="url(#d5-p)"/>
    <ellipse cx="100" cy="70" rx="86" ry="34" fill="url(#d5-g)"/>
    <path d="M18 72c4 10 12 12 18 18 6 6 14 2 22 8 10 6 18 0 28 4 10 4 18-2 28 0 10 2 18-4 26-6 10-2 14-8 22-10 8-2 14-8 20-16"
      fill="none" stroke="#f9ecd2" stroke-opacity=".8" stroke-width="4" stroke-linecap="round"/>
    <ellipse cx="100" cy="66" rx="26" ry="10" fill="url(#d5-t)"/>
    <ellipse cx="100" cy="70" rx="22" ry="7" fill="#2a1609" opacity=".85"/>
    <path d="M38 52c16-12 40-18 62-18" stroke="#fff" stroke-opacity=".85" stroke-width="6" stroke-linecap="round" fill="none"/>
    <path d="M140 46c10 4 18 10 22 16" stroke="#fff" stroke-opacity=".5" stroke-width="4" stroke-linecap="round" fill="none"/>
    <g fill="#fff" opacity=".9"><circle cx="60" cy="58" r="1.3"/><circle cx="84" cy="48" r="1.1"/><circle cx="124" cy="50" r="1.3"/><circle cx="150" cy="64" r="1.1"/>
      <circle cx="52" cy="80" r="1"/><circle cx="146" cy="82" r="1.2"/><circle cx="96" cy="92" r="1.1"/><circle cx="120" cy="90" r="1"/><circle cx="72" cy="88" r="1.2"/></g>`),
  tarte: SVG('0 0 220 140', `<defs>
      <linearGradient id="p5-a" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#f8f6f1"/><stop offset="1" stop-color="#c3bbad"/></linearGradient>
      <linearGradient id="p5-c" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#f3c27a"/><stop offset="1" stop-color="#b06a28"/></linearGradient>
      <linearGradient id="p5-f" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#5a0610"/><stop offset=".5" stop-color="#9c0f1e"/><stop offset="1" stop-color="#6e0914"/></linearGradient></defs>
    <ellipse cx="110" cy="124" rx="104" ry="15" fill="#000" opacity=".45"/>
    <ellipse cx="110" cy="114" rx="102" ry="22" fill="url(#p5-a)"/><ellipse cx="110" cy="111" rx="78" ry="14" fill="#e3ddd1"/>
    <path d="M40 98l122-44 18 34-128 30z" fill="url(#p5-f)"/>
    <path d="M52 118l128-30v10l-128 30z" fill="#c9893f"/>
    <path d="M40 98l12 20v10L40 108z" fill="#d79a52"/>
    <path d="M40 98l122-44" stroke="url(#p5-c)" stroke-width="12" stroke-linecap="round"/>
    <path d="M162 54l18 34" stroke="#e2a95e" stroke-width="15" stroke-linecap="round"/>
    <g stroke="#f0c07a" stroke-width="7" stroke-linecap="round"><path d="M70 92l16 18"/><path d="M100 80l20 22"/><path d="M130 70l20 22"/>
      <path d="M62 104l40-16M92 110l58-24"/></g>
    <g fill="#b0121f"><circle cx="82" cy="99" r="4.5"/><circle cx="114" cy="92" r="4.5"/><circle cx="142" cy="84" r="4"/></g>
    <g fill="#fff" opacity=".5"><circle cx="81" cy="97.5" r="1.3"/><circle cx="113" cy="90.5" r="1.3"/></g>`),
  dictaphone: SVG('0 0 140 230', `<defs><linearGradient id="m5-b" x1="0" x2="1"><stop offset="0" stop-color="#1b1c1f"/><stop offset=".45" stop-color="#3b3e44"/><stop offset="1" stop-color="#16171a"/></linearGradient>
      <linearGradient id="m5-s" x1="0" x2="1"><stop offset="0" stop-color="#8e959c"/><stop offset=".5" stop-color="#e6eaee"/><stop offset="1" stop-color="#7d848b"/></linearGradient></defs>
    <ellipse cx="72" cy="222" rx="58" ry="7" fill="#000" opacity=".5"/>
    <rect x="22" y="22" width="100" height="196" rx="10" fill="url(#m5-b)"/>
    <rect x="28" y="30" width="88" height="70" rx="4" fill="url(#m5-s)"/>
    <rect x="36" y="38" width="72" height="44" rx="3" fill="#0d0e10"/>
    <rect x="40" y="42" width="64" height="36" rx="2" fill="#2b2d31"/><rect x="44" y="46" width="56" height="12" rx="1" fill="#e8e2d2"/>
    <g fill="#141414"><circle cx="58" cy="68" r="5"/><circle cx="86" cy="68" r="5"/></g><path d="M58 73h28" stroke="#5a3a1c" stroke-width="3"/>
    <text x="72" y="55" text-anchor="middle" font-family="Arial" font-size="6" fill="#333" letter-spacing=".5">MC-60 · DIANE</text>
    <text x="72" y="94" text-anchor="middle" font-family="Arial" font-size="6.5" fill="#444" letter-spacing="1.5">MICROCASSETTE</text>
    <g stroke="#0b0c0e" stroke-width="2.5" stroke-linecap="round"><path d="M38 118h68M38 126h68M38 134h68M38 142h68M38 150h68M38 158h68"/></g>
    <rect x="114" y="120" width="8" height="40" rx="3" fill="url(#m5-s)"/>
    <g fill="url(#m5-s)"><rect x="30" y="10" width="18" height="14" rx="2"/><rect x="52" y="10" width="18" height="14" rx="2"/><rect x="74" y="10" width="18" height="14" rx="2"/></g>
    <rect x="96" y="10" width="18" height="14" rx="2" fill="#b3202a"/>
    <circle cx="108" cy="186" r="4" fill="#ff3b30" class="clignote"/><text x="38" y="190" font-family="Arial" font-size="8" fill="#8d939c" letter-spacing="1">REC</text>
    <circle cx="72" cy="204" r="6" fill="#0b0c0e"/>`),

  /* Cole : des écouteurs filaires */
  ecouteurs: SVG('0 0 220 220', `<defs><linearGradient id="e5" x1="0" x2="1"><stop offset="0" stop-color="#d9dde2"/><stop offset=".5" stop-color="#ffffff"/><stop offset="1" stop-color="#aeb4bb"/></linearGradient></defs>
    <ellipse cx="110" cy="210" rx="96" ry="8" fill="#000" opacity=".45"/>
    <path d="M58 70c-6 40 30 50 40 80 6 18-8 30 0 44M150 62c10 40-24 56-36 84-6 14 2 26-6 48" fill="none" stroke="#e9ecef" stroke-width="4" stroke-linecap="round"/>
    <path d="M100 194h20" stroke="#e9ecef" stroke-width="6" stroke-linecap="round"/><rect x="104" y="196" width="12" height="20" rx="3" fill="url(#e5)"/>
    <g transform="rotate(-25 58 52)"><rect x="50" y="40" width="16" height="40" rx="7" fill="url(#e5)"/><ellipse cx="58" cy="38" rx="20" ry="17" fill="url(#e5)"/>
      <ellipse cx="58" cy="34" rx="11" ry="8" fill="#4a4f57"/><ellipse cx="55" cy="32" rx="4" ry="2" fill="#fff" opacity=".4"/></g>
    <g transform="rotate(22 150 46)"><rect x="142" y="34" width="16" height="40" rx="7" fill="url(#e5)"/><ellipse cx="150" cy="32" rx="20" ry="17" fill="url(#e5)"/>
      <ellipse cx="150" cy="28" rx="11" ry="8" fill="#4a4f57"/><ellipse cx="147" cy="26" rx="4" ry="2" fill="#fff" opacity=".4"/></g>`),

  /* Audrey : escarpins rouges, rouge à lèvres, le boîtier de juke-box du Double R */
  escarpins: SVG('0 0 230 120', `<defs><linearGradient id="es5" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#e2283a"/><stop offset="1" stop-color="#7a0a16"/></linearGradient></defs>
    <ellipse cx="115" cy="110" rx="108" ry="8" fill="#000" opacity=".45"/>
    <g><path d="M12 92c18-2 34-14 46-30 8-10 20-12 30-6 10 6 16 18 18 30l2 14H96c-10-8-30-12-50-10-14 2-24 6-34 6z" fill="url(#es5)"/>
      <path d="M100 74l6 34h-8l-4-26z" fill="#5a0610"/><path d="M30 86c20-4 38-16 48-24" stroke="#fff" stroke-opacity=".35" stroke-width="3" fill="none"/></g>
    <g transform="translate(108 0)"><path d="M12 92c18-2 34-14 46-30 8-10 20-12 30-6 10 6 16 18 18 30l2 14H96c-10-8-30-12-50-10-14 2-24 6-34 6z" fill="url(#es5)"/>
      <path d="M100 74l6 34h-8l-4-26z" fill="#5a0610"/><path d="M30 86c20-4 38-16 48-24" stroke="#fff" stroke-opacity=".35" stroke-width="3" fill="none"/></g>`),
  rouge_levres: SVG('0 0 80 170', `<defs><linearGradient id="rl5" x1="0" x2="1"><stop offset="0" stop-color="#8a6a20"/><stop offset=".45" stop-color="#ffe08a"/><stop offset="1" stop-color="#8a6a20"/></linearGradient></defs>
    <ellipse cx="40" cy="164" rx="30" ry="5" fill="#000" opacity=".45"/>
    <rect x="18" y="90" width="44" height="72" rx="4" fill="#141414"/><rect x="20" y="68" width="40" height="26" rx="2" fill="url(#rl5)"/>
    <path d="M24 68V34c0-10 8-22 22-26 0 0 10 10 10 26v34z" fill="#c4102a"/><path d="M30 64V36c0-8 4-16 10-20" stroke="#fff" stroke-opacity=".35" stroke-width="3" fill="none"/>`),
  jukebox: SVG('0 0 170 200', `<defs><linearGradient id="jb5" x1="0" x2="1"><stop offset="0" stop-color="#8e959c"/><stop offset=".5" stop-color="#f2f5f7"/><stop offset="1" stop-color="#7a838a"/></linearGradient></defs>
    <ellipse cx="85" cy="194" rx="70" ry="6" fill="#000" opacity=".45"/>
    <path d="M20 40c0-22 30-34 65-34s65 12 65 34v130c0 10-6 16-16 16H36c-10 0-16-6-16-16z" fill="url(#jb5)"/>
    <path d="M32 44c0-14 24-24 53-24s53 10 53 24v62H32z" fill="#f4eedf"/>
    <g stroke="#b3202a" stroke-width="1.2"><path d="M40 50h90M40 58h90M40 66h90M40 74h90M40 82h90M40 90h90M40 98h90"/></g>
    <path d="M85 30v76" stroke="#555" stroke-width="1"/>
    <g fill="#e2c35a"><rect x="34" y="118" width="12" height="10" rx="2"/><rect x="50" y="118" width="12" height="10" rx="2"/><rect x="66" y="118" width="12" height="10" rx="2"/>
      <rect x="82" y="118" width="12" height="10" rx="2"/><rect x="98" y="118" width="12" height="10" rx="2"/><rect x="114" y="118" width="12" height="10" rx="2"/>
      <rect x="34" y="134" width="12" height="10" rx="2"/><rect x="50" y="134" width="12" height="10" rx="2"/><rect x="66" y="134" width="12" height="10" rx="2"/>
      <rect x="82" y="134" width="12" height="10" rx="2"/><rect x="98" y="134" width="12" height="10" rx="2"/><rect x="114" y="134" width="12" height="10" rx="2"/></g>
    <rect x="58" y="154" width="54" height="16" rx="3" fill="#2a2a2a"/><circle cx="135" cy="160" r="6" fill="#d32f2f"/>`),

  /* Leland : le club de golf et la photo de Laura reine du bal */
  golf: SVG('0 0 120 300', `<defs><linearGradient id="g5" x1="0" x2="1"><stop offset="0" stop-color="#8e959c"/><stop offset=".5" stop-color="#f2f5f7"/><stop offset="1" stop-color="#7a838a"/></linearGradient></defs>
    <ellipse cx="60" cy="292" rx="52" ry="7" fill="#000" opacity=".45"/>
    <rect x="46" y="10" width="12" height="70" rx="5" fill="#1b1b1b"/><path d="M52 80l10 196" stroke="url(#g5)" stroke-width="5" stroke-linecap="round"/>
    <path d="M60 272l36 4c6 1 8 6 6 10l-2 4H56z" fill="url(#g5)"/>
    <circle cx="26" cy="280" r="11" fill="#f7f7f2"/><g fill="#d9d9d0"><circle cx="22" cy="276" r="1.5"/><circle cx="28" cy="278" r="1.5"/><circle cx="24" cy="283" r="1.5"/><circle cx="30" cy="284" r="1.5"/></g>`),
  cadre_bal: SVG('0 0 160 200', `<defs><linearGradient id="cb5" x1="0" x2="1" y1="0" y2="1"><stop offset="0" stop-color="#7a5510"/><stop offset=".3" stop-color="#f6dc8c"/><stop offset=".6" stop-color="#a87a1c"/><stop offset="1" stop-color="#fbe7a8"/></linearGradient>
      <linearGradient id="cb5f" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#3b5a8a"/><stop offset="1" stop-color="#1c2b45"/></linearGradient></defs>
    <ellipse cx="80" cy="194" rx="66" ry="6" fill="#000" opacity=".45"/>
    <path d="M30 186l20-40M130 186l-20-40" stroke="#5a3e12" stroke-width="5"/>
    <rect x="10" y="6" width="140" height="176" rx="4" fill="url(#cb5)"/><rect x="22" y="18" width="116" height="152" fill="url(#cb5f)"/>
    <path d="M48 170c2-34 14-52 32-52s30 18 32 52z" fill="#e8d7c7"/>
    <ellipse cx="80" cy="96" rx="20" ry="24" fill="#f3dcc6"/>
    <path d="M56 100c-6-30 6-50 24-50s32 18 24 50c-4-14-8-22-24-26-16 4-20 12-24 26z" fill="#e8c46a"/>
    <path d="M64 58l6-12 6 8 4-12 4 12 6-8 6 12z" fill="#f4f1ea" stroke="#c9b37a" stroke-width="1"/>`),

  /* Insignes : l'écusson du Sheriff Department, l'insigne doré de Deputy */
  ecusson_sherif: SVG('0 0 220 170', `<ellipse cx="110" cy="162" rx="96" ry="7" fill="#000" opacity=".45"/>
    <path d="M12 60C40 16 180 16 208 60l-22 92c-24-16-52-22-76-22s-52 6-76 22z" fill="#7a5a3a"/>
    <path d="M20 62C46 24 174 24 200 62l-19 82c-22-12-46-18-71-18s-49 6-71 18z" fill="#f3efe4"/>
    <path id="ec-arc" d="M40 70C60 38 160 38 180 70" fill="none"/>
    <text font-family="Arial Black,Arial" font-weight="900" font-size="15" fill="#6b1d14" letter-spacing="1"><textPath href="#ec-arc" startOffset="50%" text-anchor="middle">SHERIFF DEPARTMENT</textPath></text>
    <path d="M62 112c0-26 22-44 48-44s48 18 48 44z" fill="#a9c9e6"/>
    <path d="M62 112l22-30 10 10 14-26 18 30 10-8 22 24z" fill="#7a2e1e"/><path d="M98 76l10-10 10 18-6-4-6 6-4-4z" fill="#fff"/>
    <g fill="#1f6b3f"><path d="M66 112l8-22 8 22z"/><path d="M78 112l7-18 7 18z"/><path d="M124 112l8-24 8 24z"/><path d="M136 112l7-20 7 20z"/><path d="M146 112l6-16 6 16z"/></g>
    <path d="M62 112c0-26 22-44 48-44s48 18 48 44" fill="none" stroke="#e2b23a" stroke-width="3"/>
    <text x="110" y="134" text-anchor="middle" font-family="Arial Black,Arial" font-weight="900" font-size="15" fill="#6b1d14" letter-spacing="1">TWIN  PEAKS</text>`),
  insigne_deputy: SVG('0 0 140 180', `<defs><radialGradient id="dp5" cx=".4" cy=".3" r=".85"><stop offset="0" stop-color="#fff4c4"/><stop offset=".45" stop-color="#e2b84e"/><stop offset="1" stop-color="#8a6516"/></radialGradient></defs>
    <ellipse cx="70" cy="174" rx="48" ry="6" fill="#000" opacity=".45"/>
    <path d="M70 30c-20 0-34-8-42-14-6 10-10 14-18 16 4 30-2 60 8 90 10 26 30 40 52 48 22-8 42-22 52-48 10-30 4-60 8-90-8-2-12-6-18-16-8 6-22 14-42 14z" fill="url(#dp5)" stroke="#7a5510" stroke-width="2"/>
    <path d="M54 22c4-12 28-12 32 0l-6 8H60z" fill="url(#dp5)" stroke="#7a5510"/><path d="M40 18c10-8 20-6 30 2 10-8 20-10 30-2-8 2-14 6-30 8-16-2-22-6-30-8z" fill="url(#dp5)" stroke="#7a5510"/>
    <path d="M24 46h92l-4 20H28z" fill="#1f3fa8"/><text x="70" y="61" text-anchor="middle" font-family="Georgia" font-weight="700" font-size="12" fill="#f4f1ea">TWIN PEAKS</text>
    <circle cx="70" cy="92" r="20" fill="#f4f1ea" stroke="#1f3fa8" stroke-width="5"/>
    <path d="M70 76l5 11 12 1-9 8 3 12-11-6-11 6 3-12-9-8 12-1z" fill="#1f3fa8"/>
    <path d="M28 116h84l-4 18H32z" fill="#1f3fa8"/><text x="70" y="130" text-anchor="middle" font-family="Georgia" font-weight="700" font-size="12" fill="#f4f1ea">DEPUTY</text>
    <rect x="54" y="138" width="32" height="16" rx="2" fill="#f1e2a8" stroke="#7a5510"/><text x="70" y="151" text-anchor="middle" font-family="Georgia" font-weight="700" font-size="12" fill="#5c430c">13</text>`),

  /* Bobby (saison 3) : la capsule du major Briggs */
  capsule: SVG('0 0 240 110', `<defs><linearGradient id="cp5" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#5c636a"/><stop offset=".35" stop-color="#d9dee3"/><stop offset=".6" stop-color="#9aa2aa"/><stop offset="1" stop-color="#3e444a"/></linearGradient></defs>
    <ellipse cx="120" cy="100" rx="110" ry="8" fill="#000" opacity=".45"/>
    <rect x="20" y="28" width="170" height="56" rx="24" fill="url(#cp5)"/><rect x="186" y="34" width="34" height="44" rx="10" fill="url(#cp5)"/>
    <g stroke="#2d3237" stroke-width="2" opacity=".6"><path d="M70 30v52M140 30v52"/></g>
    <path d="M196 36v40M206 36v40" stroke="#2d3237" stroke-width="1.5" opacity=".5"/>
    <path d="M24 46c40-6 120-6 160 0" stroke="#fff" stroke-opacity=".45" stroke-width="3" fill="none"/>
    <rect x="160" y="4" width="70" height="30" rx="2" fill="#f2ecd6" transform="rotate(8 195 19)"/>
    <text x="196" y="24" text-anchor="middle" font-family="Courier New" font-size="7" fill="#333" transform="rotate(8 195 19)">COOPER · COOPER</text>`),

  /* Le Géant : la bague de la grotte du hibou, avec son symbole */
  bague: SVG('0 0 120 120', `<defs><linearGradient id="bg5" x1="0" x2="1"><stop offset="0" stop-color="#7a5510"/><stop offset=".4" stop-color="#ffe9a0"/><stop offset="1" stop-color="#8a6416"/></linearGradient>
      <radialGradient id="bg5v" cx=".4" cy=".35" r=".75"><stop offset="0" stop-color="#7fd9a6"/><stop offset=".55" stop-color="#1f8a5a"/><stop offset="1" stop-color="#0b3d28"/></radialGradient></defs>
    <ellipse cx="60" cy="112" rx="44" ry="6" fill="#000" opacity=".45"/>
    <ellipse cx="60" cy="80" rx="40" ry="26" fill="none" stroke="url(#bg5)" stroke-width="9"/>
    <path d="M30 50h60l-6 16H36z" fill="url(#bg5)"/>
    <ellipse cx="60" cy="38" rx="30" ry="24" fill="url(#bg5)"/><ellipse cx="60" cy="38" rx="25" ry="19" fill="url(#bg5v)"/>
    <g transform="translate(37 26) scale(.46)" stroke="#0a2a1c" stroke-width="7">${SYMBOLE_HIBOU}</g>
    <ellipse cx="51" cy="29" rx="8" ry="4" fill="#fff" opacity=".35"/>`),

  /* Donna : l'enseigne du One-Eyed Jack's, au trait, d'après la vraie */
  one_eyed_jack: SVG('0 0 240 230', `<defs><filter id="oj5" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="2.4" result="b"/>
      <feMerge><feMergeNode in="b"/><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter></defs>
    <rect x="8" y="8" width="224" height="214" rx="10" fill="#1c2240" stroke="#5a4630" stroke-width="5"/>
    <g fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="22" y="22" width="196" height="186" rx="16" stroke="#4aa3ff" stroke-width="5" filter="url(#oj5)" class="neon"/>
      <path d="M70 76l-6-40 26 18 20-30 18 30 24-22 2 44" stroke="#f2c230" stroke-width="5"/>
      <path d="M70 76c28-6 58-6 86 0" stroke="#f2c230" stroke-width="5"/>
      <path d="M74 52l14 10M102 40l8 16M130 44l2 14" stroke="#c0283a" stroke-width="5"/>
      <path d="M72 80c-18 22-24 52-18 84l40 12" stroke="#ff5a6e" stroke-width="5"/>
      <path d="M118 80c6 10 12 16 16 22l10 6-8 6 6 6-4 4 6 8-10 8c-4 8-12 12-24 12" stroke="#ffc7b5" stroke-width="4.5"/>
      <path d="M120 128c4 2 8 2 12 0" stroke="#ff5a6e" stroke-width="3.5"/>
      <path d="M102 96c10-6 22-6 30 0" stroke="#4aa3ff" stroke-width="5" filter="url(#oj5)" class="neon"/>
      <path d="M118 102l14-4-3 12z" stroke="#4aa3ff" stroke-width="4" filter="url(#oj5)"/>
      <path d="M60 176h108M70 176v24M86 176v24M102 176v24M118 176v24M134 176v24M150 176v24" stroke="#f2c230" stroke-width="4.5"/>
      <path d="M58 164c30 6 70 8 112 4" stroke="#f2c230" stroke-width="4.5"/>
      <path d="M176 46c10-8 22-2 20 10-2 10-12 12-12 22 0 10 12 12 16 6" stroke="#9aa3ad" stroke-width="5"/></g>`),
});
Object.assign(OBJ, {
  escarpins: SVG('0 0 240 120', `<defs><linearGradient id="es6" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#ea3346"/><stop offset="1" stop-color="#8a0c18"/></linearGradient></defs>
    <ellipse cx="120" cy="112" rx="112" ry="7" fill="#000" opacity=".45"/>
    ${[0, 118].map(dx => `<g transform="translate(${dx} 6)">
      <path d="M6 98Q4 92 14 90C34 86 50 76 62 66C70 60 80 60 86 64L100 56C106 54 108 60 106 66L104 72C96 76 90 84 84 98Z" fill="url(#es6)"/>
      <path d="M62 66C72 62 84 62 100 58C96 64 88 67 80 69C72 71 66 70 62 66Z" fill="#3a050b"/>
      <path d="M99 70h7l-3 34h-3z" fill="#5a0610"/><path d="M6 98h78" stroke="#3a050b" stroke-width="2"/>
      <path d="M22 88C36 84 48 78 58 70" stroke="#fff" stroke-opacity=".4" stroke-width="3" fill="none" stroke-linecap="round"/></g>`).join('')}`),
  ecusson_sherif: SVG('0 0 220 170', `<ellipse cx="110" cy="162" rx="96" ry="7" fill="#000" opacity=".45"/>
    <path d="M10 62C38 14 182 14 210 62l-22 92c-24-16-52-22-78-22s-54 6-78 22z" fill="#7a5a3a"/>
    <path d="M18 64C44 24 176 24 202 64l-19 82c-22-12-47-18-73-18s-51 6-73 18z" fill="#f3efe4"/>
    <path id="ec6-arc" d="M30 66C56 30 164 30 190 66" fill="none"/>
    <text font-family="Arial Black,Arial" font-weight="900" font-size="12" fill="#6b1d14" letter-spacing=".5"><textPath href="#ec6-arc" startOffset="50%" text-anchor="middle">SHERIFF DEPARTMENT</textPath></text>
    <path d="M64 110c0-24 20-40 46-40s46 16 46 40z" fill="#a9c9e6"/>
    <path d="M64 110l20-28 10 9 14-25 18 28 10-8 20 24z" fill="#7a2e1e"/><path d="M98 76l10-10 10 18-6-4-6 6-4-4z" fill="#fff"/>
    <g fill="#1f6b3f"><path d="M68 110l7-20 7 20z"/><path d="M79 110l6-16 6 16z"/><path d="M124 110l7-22 7 22z"/><path d="M135 110l6-18 6 18z"/><path d="M145 110l5-14 5 14z"/></g>
    <path d="M64 110c0-24 20-40 46-40s46 16 46 40" fill="none" stroke="#e2b23a" stroke-width="3"/>
    <text x="110" y="130" text-anchor="middle" font-family="Arial Black,Arial" font-weight="900" font-size="12" fill="#6b1d14" letter-spacing="1">TWIN  PEAKS</text>`),
  one_eyed_jack: SVG('0 0 240 230', `<defs><filter id="oj6" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="2.4" result="b"/>
      <feMerge><feMergeNode in="b"/><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter></defs>
    <rect x="8" y="8" width="224" height="214" rx="8" fill="#1d2747" stroke="#5a4630" stroke-width="6"/>
    <g fill="none" stroke-linecap="round" stroke-linejoin="round" stroke-width="4.5">
      <rect x="22" y="22" width="196" height="186" rx="18" stroke="#4aa3ff" stroke-width="5" filter="url(#oj6)" class="neon"/>
      <path d="M66 78L60 36l24 20 20-30 20 30 26-24 6 46z" stroke="#f2c230"/>
      <path d="M72 66l12-8 12 10 12-14 12 14 14-12 10 8" stroke="#c0283a"/>
      <path d="M68 80c-14 18-18 46-12 70 4 14 16 22 32 24" stroke="#ff5a6e"/>
      <path d="M82 86c-6 18-6 40 0 60" stroke="#ff5a6e"/>
      <path d="M120 80c2 8 4 14 8 20l2 6c8 10 16 18 22 22l-12 4 2 8-4 4 2 6c-2 6-8 8-14 8l-8 6-14 0" stroke="#ffc7b5"/>
      <path d="M96 100c14-4 30-4 42 0" stroke="#4aa3ff" filter="url(#oj6)" class="neon"/>
      <path d="M122 98l16-2-6 14z" stroke="#4aa3ff" filter="url(#oj6)" class="neon"/>
      <path d="M58 172c34 6 74 6 112 0M58 172v28h112v-28M76 176v24M94 176v24M112 178v22M130 176v24M148 176v24" stroke="#f2c230"/>
      <path d="M170 172c8-8 18-16 30-20" stroke="#c0283a"/>
      <path d="M182 44c12-8 24-2 22 10-2 10-12 12-12 22 0 10 12 12 16 6" stroke="#8d96a0" stroke-width="5"/></g>`),
});

/* ===== version 6 ===== */
Object.assign(OBJ, {
  /* Cooper : la pince à épiler et la petite lettre « R » trouvée sous l'ongle de Laura */
  pince_r: SVG('0 0 200 120', `<defs><linearGradient id="pr6" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#f2f5f7"/><stop offset=".5" stop-color="#9aa2aa"/><stop offset="1" stop-color="#5c636a"/></linearGradient></defs>
    <ellipse cx="100" cy="110" rx="90" ry="6" fill="#000" opacity=".45"/>
    <path d="M10 52l120 8 4 6-124-6z" fill="url(#pr6)"/><path d="M10 52l120 22 2 6L8 58z" fill="url(#pr6)"/>
    <rect x="130" y="54" width="44" height="34" rx="2" fill="#fbf8ee" transform="rotate(8 152 71)"/>
    <text x="152" y="80" text-anchor="middle" font-family="Times New Roman,serif" font-size="28" font-weight="700" fill="#1a1a1a" transform="rotate(8 152 71)">R</text>`),
  /* Audrey : chaussures de lycée bicolores, la queue de cerise nouée, le juke-box */
  souliers: SVG('0 0 240 110', `<ellipse cx="120" cy="100" rx="114" ry="8" fill="#000" opacity=".45"/>
    ${[0, 120].map(dx => `<g transform="translate(${dx} 0)">
      <path d="M8 86c0-16 10-26 26-28 14-2 24-10 36-16 14-6 30-4 38 8 6 8 8 18 8 30v6H12c-3 0-4-0-4-0z" fill="#f4f1ea"/>
      <path d="M34 58c14-2 24-10 36-16 14-6 30-4 38 8 4 6 6 12 7 18-16-2-34 0-50 6-12-2-22-8-31-16z" fill="#1d1b1a"/>
      <path d="M8 86h108v8H10z" fill="#c9a77a"/><path d="M8 94h108v6H10z" fill="#2a1d14"/>
      <path d="M62 50l14 8M68 46l14 8M74 43l14 7" stroke="#e8e2d5" stroke-width="2"/>
      <path d="M14 82c20-4 40-4 60-2" stroke="#fff" stroke-opacity=".4" stroke-width="2" fill="none"/></g>`).join('')}`),
  cerise_noeud: SVG('0 0 180 150', `<defs><radialGradient id="cr6" cx=".35" cy=".3" r=".75"><stop offset="0" stop-color="#ef4458"/><stop offset=".55" stop-color="#a50f22"/><stop offset="1" stop-color="#55040e"/></radialGradient></defs>
    <ellipse cx="90" cy="140" rx="74" ry="7" fill="#000" opacity=".45"/>
    <circle cx="46" cy="110" r="26" fill="url(#cr6)"/><ellipse cx="37" cy="100" rx="8" ry="5" fill="#fff" opacity=".45"/>
    <path d="M48 84c2-18 10-30 22-38" fill="none" stroke="#6a8a32" stroke-width="4" stroke-linecap="round"/>
    <path d="M102 120c22-6 36-24 30-44-6-18-28-22-38-8-10 14 2 30 18 26 18-4 22-28 8-40-10-8-26-6-34 4" fill="none" stroke="#6a8a32" stroke-width="4" stroke-linecap="round"/>
    <path d="M70 46c8-4 14-4 18 2" fill="none" stroke="#6a8a32" stroke-width="4" stroke-linecap="round"/>`),
  jukebox: SVG('0 0 170 230', `<defs><linearGradient id="jb6" x1="0" x2="1"><stop offset="0" stop-color="#7a2b14"/><stop offset=".5" stop-color="#b9572c"/><stop offset="1" stop-color="#6a2410"/></linearGradient>
      <linearGradient id="jb6c" x1="0" x2="1"><stop offset="0" stop-color="#8e959c"/><stop offset=".5" stop-color="#f2f5f7"/><stop offset="1" stop-color="#7a838a"/></linearGradient>
      <linearGradient id="jb6l" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#ffe27a"/><stop offset=".5" stop-color="#ff8a3a"/><stop offset="1" stop-color="#e5484d"/></linearGradient></defs>
    <ellipse cx="85" cy="222" rx="76" ry="7" fill="#000" opacity=".45"/>
    <path d="M14 214V96C14 46 46 12 85 12s71 34 71 84v118z" fill="url(#jb6)"/>
    <path d="M24 100C24 56 50 26 85 26s61 30 61 74" fill="none" stroke="url(#jb6l)" stroke-width="10" class="neon"/>
    <path d="M38 102c0-30 20-52 47-52s47 22 47 52v30H38z" fill="#1c1410"/>
    <path d="M44 132v-28c0-26 18-44 41-44s41 18 41 44v28" fill="none" stroke="url(#jb6c)" stroke-width="3"/>
    <ellipse cx="85" cy="118" rx="28" ry="8" fill="#111"/><ellipse cx="85" cy="117" rx="10" ry="3" fill="#c8102e"/>
    <rect x="30" y="140" width="110" height="26" rx="4" fill="#f4eedf"/>
    <g stroke="#b3202a" stroke-width="1"><path d="M36 147h98M36 153h98M36 159h98"/></g>
    <rect x="22" y="172" width="126" height="40" rx="6" fill="url(#jb6c)"/>
    <g fill="#5c636a"><path d="M32 180h106M32 188h106M32 196h106M32 204h106" stroke="#5c636a" stroke-width="2"/></g>`),
  /* Leland : sa carte de visite d'avocat */
  carte_leland: SVG('0 0 220 120', `<ellipse cx="110" cy="112" rx="96" ry="6" fill="#000" opacity=".45"/>
    <rect x="16" y="16" width="190" height="92" rx="3" fill="#f6f2e8" transform="rotate(-4 110 62)"/>
    <g transform="rotate(-4 110 62)" font-family="Georgia,serif" fill="#2a2420" text-anchor="middle">
      <text x="110" y="50" font-size="15" letter-spacing="1">LELAND PALMER</text>
      <text x="110" y="68" font-size="9" font-style="italic">Avocat · Attorney at Law</text>
      <path d="M50 76h120" stroke="#9a8a6a" stroke-width="1"/>
      <text x="110" y="92" font-size="8">Twin Peaks, Washington</text></g>`),
  /* Leo : les bottes (« New shoes ») */
  bottes: SVG('0 0 220 150', `<defs><linearGradient id="bt6" x1="0" x2="1"><stop offset="0" stop-color="#2e1c0f"/><stop offset=".5" stop-color="#5a3a20"/><stop offset="1" stop-color="#2a190c"/></linearGradient></defs>
    <ellipse cx="110" cy="142" rx="104" ry="7" fill="#000" opacity=".45"/>
    ${[0, 104].map(dx => `<g transform="translate(${dx} 0)">
      <path d="M22 8h42v84c18 6 38 12 38 28v16H18V8z" fill="url(#bt6)"/>
      <path d="M22 8h42v10H22z" fill="#1d1208"/><path d="M18 128h84v8H18z" fill="#140c06"/>
      <path d="M30 24v70M56 24v66" stroke="#7a5230" stroke-width="2" stroke-dasharray="3 4"/>
      <path d="M64 98c14 4 26 8 30 16" stroke="#7a5230" stroke-width="2" fill="none"/></g>`).join('')}`),
  /* Catherine : le déguisement de Mr. Tojamura ; la lame de la scierie Packard */
  moustache: SVG('0 0 200 120', `<ellipse cx="100" cy="112" rx="88" ry="6" fill="#000" opacity=".45"/>
    <g fill="none" stroke="#c9a24a" stroke-width="6"><circle cx="62" cy="40" r="24"/><circle cx="138" cy="40" r="24"/><path d="M86 38c8-6 20-6 28 0M38 34l-24-6M162 34l24-6"/></g>
    <g fill="#ffffff22"><circle cx="62" cy="40" r="21"/><circle cx="138" cy="40" r="21"/></g>
    <path d="M100 86c-14-12-40-14-60-2 10 2 20 8 28 10 14 4 26 0 32-8 6 8 18 12 32 8 8-2 18-8 28-10-20-12-46-10-60 2z" fill="#6b4a30"/>
    <path d="M52 84c14-6 30-6 44 0M104 84c14-6 30-6 44 0" stroke="#9a7452" stroke-width="2" fill="none"/>`),
  lame: SVG('0 0 160 160', `<defs><radialGradient id="lm6" cx=".4" cy=".35" r=".7"><stop offset="0" stop-color="#f2f5f7"/><stop offset=".6" stop-color="#a7afb6"/><stop offset="1" stop-color="#6d757c"/></radialGradient></defs>
    <ellipse cx="80" cy="152" rx="62" ry="6" fill="#000" opacity=".45"/>
    <path d="${Array.from({length: 24}, (_, i) => { const a = i * Math.PI / 12, b = a + Math.PI / 24;
      return `${i ? 'L' : 'M'}${(80 + 70 * Math.cos(a)).toFixed(1)} ${(76 + 70 * Math.sin(a)).toFixed(1)}L${(80 + 60 * Math.cos(b)).toFixed(1)} ${(76 + 60 * Math.sin(b)).toFixed(1)}`; }).join('')}Z" fill="url(#lm6)"/>
    <circle cx="80" cy="76" r="16" fill="#3a3f45"/><circle cx="80" cy="76" r="7" fill="#15171a"/>
    <text x="80" y="118" text-anchor="middle" font-family="Georgia" font-size="9" fill="#4a4f55" letter-spacing="1">PACKARD</text>`),
  /* Denise : l'insigne de la DEA */
  insigne_dea: SVG('0 0 140 170', `<defs><radialGradient id="de6" cx=".4" cy=".3" r=".85"><stop offset="0" stop-color="#fff4c4"/><stop offset=".45" stop-color="#e2b84e"/><stop offset="1" stop-color="#8a6516"/></radialGradient></defs>
    <ellipse cx="70" cy="164" rx="48" ry="6" fill="#000" opacity=".45"/>
    <path d="M70 6l14 18 24-4 4 24 22 10-10 22 10 22-22 10-4 24-24-4-14 18-14-18-24 4-4-24-22-10 10-22-10-22 22-10 4-24 24 4z" fill="url(#de6)" stroke="#7a5510" stroke-width="2"/>
    <circle cx="70" cy="78" r="38" fill="#1f3a6b" stroke="#7a5510" stroke-width="2"/>
    <path d="M44 74c10-14 20-16 26-8 6-8 16-6 26 8-8-4-14-2-18 4l-8 16-8-16c-4-6-10-8-18-4z" fill="#e2b84e"/>
    <text x="70" y="104" text-anchor="middle" font-family="Georgia" font-weight="700" font-size="11" fill="#f4f1ea">D·E·A</text>
    <text x="70" y="136" text-anchor="middle" font-family="Georgia" font-weight="700" font-size="8" fill="#5c430c">SPECIAL AGENT</text>`),
  /* Carl : l'enseigne du camping Fat Trout */
  enseigne_fat_trout: SVG('0 0 260 190', `<ellipse cx="130" cy="182" rx="110" ry="7" fill="#000" opacity=".45"/>
    <path d="M50 180V90M210 180V90" stroke="#5a3e24" stroke-width="10"/>
    <rect x="14" y="20" width="232" height="96" rx="10" fill="#e9dcc0" stroke="#5a3e24" stroke-width="6"/>
    <text x="130" y="52" text-anchor="middle" font-family="Georgia,serif" font-weight="700" font-size="22" fill="#7a2e1e" letter-spacing="1">FAT TROUT</text>
    <text x="130" y="72" text-anchor="middle" font-family="Arial" font-size="11" fill="#3a2a1a" letter-spacing="4">TRAILER PARK</text>
    <g transform="translate(130 96)"><path d="M-42 0c18-14 52-14 70 0-18 14-52 14-70 0z" fill="#8a9a5a"/><path d="M28 0l14-10v20z" fill="#8a9a5a"/>
      <circle cx="-30" cy="-2" r="2.5" fill="#1a1a1a"/><g fill="#c0505a"><circle cx="-6" cy="-3" r="2"/><circle cx="6" cy="2" r="2"/><circle cx="14" cy="-4" r="1.6"/></g></g>`),
});

/* ===== version 7 ===== */
/* le symbole de la bague de la grotte du hibou (Owl Cave ring) : un losange entre deux V, et une queue sous le losange */
const SYMBOLE_HIBOU2 = '<path d="M2 22L16 36 30 22 46 6 62 22 46 38 30 22M62 22L76 36 92 22M46 38L36 48" fill="none" stroke-linejoin="miter" stroke-linecap="square"/>';
Object.assign(OBJ, {
  bague: SVG('0 0 120 120', `<defs><linearGradient id="bg7" x1="0" x2="1"><stop offset="0" stop-color="#7a5510"/><stop offset=".4" stop-color="#ffe9a0"/><stop offset="1" stop-color="#8a6416"/></linearGradient>
      <radialGradient id="bg7v" cx=".4" cy=".35" r=".75"><stop offset="0" stop-color="#7fd9a6"/><stop offset=".55" stop-color="#1f8a5a"/><stop offset="1" stop-color="#0b3d28"/></radialGradient></defs>
    <ellipse cx="60" cy="112" rx="44" ry="6" fill="#000" opacity=".45"/>
    <ellipse cx="60" cy="80" rx="40" ry="26" fill="none" stroke="url(#bg7)" stroke-width="9"/>
    <path d="M30 50h60l-6 16H36z" fill="url(#bg7)"/>
    <ellipse cx="60" cy="38" rx="32" ry="25" fill="url(#bg7)"/><ellipse cx="60" cy="38" rx="27" ry="20" fill="url(#bg7v)"/>
    <g transform="translate(37 26) scale(.5)" stroke="#e8d9a0" stroke-width="7">${SYMBOLE_HIBOU2}</g>
    <ellipse cx="50" cy="28" rx="8" ry="4" fill="#fff" opacity=".3"/>`),
  /* Catherine : lunettes sans branches (un pince-nez) */
  pince_nez: SVG('0 0 160 70', `<g fill="#ffffff14" stroke="#caa04a" stroke-width="5"><circle cx="42" cy="36" r="26"/><circle cx="118" cy="36" r="26"/></g>
    <path d="M68 32c6-8 18-8 24 0" fill="none" stroke="#caa04a" stroke-width="5"/>
    <ellipse cx="32" cy="26" rx="9" ry="5" fill="#fff" opacity=".35"/><ellipse cx="108" cy="26" rx="9" ry="5" fill="#fff" opacity=".35"/>`),
  moustache: SVG('0 0 200 70', `<path d="M100 26c-14-12-40-14-60-2 10 2 20 8 28 10 14 4 26 0 32-8 6 8 18 12 32 8 8-2 18-8 28-10-20-12-46-10-60 2z" fill="#5a3a20"/>
    <path d="M52 24c14-6 30-6 44 0M104 24c14-6 30-6 44 0" stroke="#8a6440" stroke-width="2" fill="none"/>`),
  /* Cole : le petit boîtier où sont branchés les écouteurs */
  boitier: SVG('0 0 120 160', `<defs><linearGradient id="bo7" x1="0" x2="1"><stop offset="0" stop-color="#2b2e33"/><stop offset=".5" stop-color="#4a4f57"/><stop offset="1" stop-color="#1d1f23"/></linearGradient></defs>
    <rect x="16" y="20" width="88" height="130" rx="10" fill="url(#bo7)"/><rect x="26" y="34" width="68" height="30" rx="3" fill="#a9c08c"/>
    <text x="60" y="54" text-anchor="middle" font-family="ui-monospace,Consolas,monospace" font-size="13" fill="#1d2a14">VOL 11</text>
    <circle cx="60" cy="104" r="22" fill="#1a1c20" stroke="#5c636a" stroke-width="3"/><path d="M60 86v12" stroke="#c9d1d6" stroke-width="4" stroke-linecap="round"/>
    <rect x="52" y="8" width="16" height="14" rx="2" fill="#8d939c"/><circle cx="96" cy="142" r="3" fill="#3fb27f" class="clignote"/>`),
  /* Leo : la paire de chaussures neuves, posée entre les deux films */
  chaussures: SVG('0 0 160 90', `<defs><linearGradient id="ch7" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#6b4022"/><stop offset="1" stop-color="#2e1a0c"/></linearGradient></defs>
    <ellipse cx="80" cy="82" rx="74" ry="6" fill="#000" opacity=".45"/>
    ${[0, 76].map(dx => `<g transform="translate(${dx} 0)"><path d="M6 70c0-14 8-20 20-22 12-2 22-12 30-16 10-4 18 2 20 14 1 8 2 16 2 24v6H8z" fill="url(#ch7)"/>
      <path d="M8 72h70v6H8z" fill="#140c06"/><path d="M32 44l10 6M38 40l10 6" stroke="#e8d5b5" stroke-width="2"/>
      <path d="M16 62c14-2 26-4 36-10" stroke="#fff" stroke-opacity=".25" stroke-width="2" fill="none"/></g>`).join('')}`),
  /* Phillip Jeffries */
  telephone_noir: SVG('0 0 140 110', `<ellipse cx="70" cy="102" rx="60" ry="6" fill="#000" opacity=".45"/>
    <defs><linearGradient id="tn7" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#5a5a62"/><stop offset=".35" stop-color="#2a2a30"/><stop offset="1" stop-color="#121216"/></linearGradient></defs>
    <path d="M18 70c0-20 20-30 52-30s52 10 52 30v20H18z" fill="url(#tn7)"/><circle cx="70" cy="68" r="16" fill="#e9e2d0" stroke="#8a8a90" stroke-width="3"/>
    <g fill="#2a2a30">${[0, 45, 90, 135, 180, 225, 270, 315].map(a => `<circle cx="${70 + 10 * Math.cos(a * Math.PI / 180)}" cy="${68 + 10 * Math.sin(a * Math.PI / 180)}" r="2.4"/>`).join('')}</g>
    <path d="M8 34c0-14 14-22 30-22h64c16 0 30 8 30 22v6c0 4-4 8-8 8h-14c-6 0-8-4-8-8v-4H38v4c0 4-2 8-8 8H16c-4 0-8-4-8-8z" fill="url(#tn7)"/>
    <path d="M30 18h80" stroke="#ffffff40" stroke-width="3" stroke-linecap="round"/>`),
  /* Jerry : la baguette au brie */
  baguette: SVG('0 0 240 90', `<defs><linearGradient id="bq7" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#e8b06a"/><stop offset="1" stop-color="#a86a2a"/></linearGradient></defs>
    <ellipse cx="120" cy="80" rx="110" ry="7" fill="#000" opacity=".45"/>
    <path d="M14 58c20-30 180-42 212-24 8 6 0 18-10 22-50 18-170 26-196 16-10-4-10-8-6-14z" fill="url(#bq7)"/>
    <g stroke="#f4d7a0" stroke-width="4" stroke-linecap="round"><path d="M50 50l14-8M90 44l14-8M130 40l14-8M170 38l14-8"/></g>
    <path d="M100 58c20-2 50-6 70-12l2 8c-20 6-50 10-72 12z" fill="#f6efd8"/>`),
  /* Hank : un domino */
  domino: SVG('0 0 80 150', `<ellipse cx="40" cy="144" rx="32" ry="5" fill="#000" opacity=".45"/>
    <rect x="6" y="4" width="68" height="136" rx="10" fill="#f4f1ea" stroke="#c9c2b4" stroke-width="2"/><path d="M14 72h52" stroke="#1a1a1a" stroke-width="3"/>
    <g fill="#1a1a1a"><circle cx="22" cy="22" r="6"/><circle cx="58" cy="22" r="6"/><circle cx="22" cy="54" r="6"/><circle cx="58" cy="54" r="6"/>
      <circle cx="40" cy="106" r="6"/><circle cx="22" cy="90" r="6"/><circle cx="58" cy="122" r="6"/></g>`),
  /* Cooper : des taches de café renversé */
  tache_cafe: SVG('0 0 160 120', `<path d="M40 30c20-22 60-14 72 6 16 2 34 16 26 34-6 14-26 14-34 26-12 16-44 12-52-2-16 2-34-8-30-26 2-12 10-16 18-38z" fill="#6b3d1a" opacity=".55"/>
    <path d="M60 40c14-8 34-4 40 8" stroke="#3a2010" stroke-width="3" fill="none" opacity=".35"/>
    <circle cx="130" cy="28" r="7" fill="#6b3d1a" opacity=".5"/><circle cx="20" cy="96" r="5" fill="#6b3d1a" opacity=".5"/>`),
});
/* Donna : l'enseigne du One Eyed Jack's (planches bleues, néon, valet de profil : le visage bien sous la couronne) */
Object.assign(OBJ, {
  one_eyed_jack: SVG('0 0 240 230', `<defs><filter id="oj7" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="2.4" result="b"/>
      <feMerge><feMergeNode in="b"/><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter></defs>
    <rect x="8" y="8" width="224" height="214" rx="6" fill="#2a3a7a" stroke="#4a3a28" stroke-width="7"/>
    <g stroke="#1d2a5c" stroke-width="2">${[44, 80, 116, 152, 188].map(x => `<path d="M${x} 12v206"/>`).join('')}</g>
    <g stroke="#2a1a14" stroke-width="2" stroke-linejoin="round">
      <path d="M150 162c18-12 44-10 60-2v36h-60z" fill="#8a1d2e"/>
      <path d="M74 80c-14 22-16 58-6 82h40c-8-24-10-56-4-82z" fill="#e8475a"/>
      <path d="M104 80h56l2 16 14 16-14 6 4 8-6 4 4 6-6 12c-10 6-24 6-36 4l-2 10h-20c-8-24-10-56-4-82z" fill="#f4b48c"/>
      <path d="M68 80L62 40l24 18 18-26 16 24 18-24 16 24 22-18-6 42z" fill="#f2c230"/>
      <path d="M78 72l-2-16 14 12 14-20 14 20 16-20 14 20 14-12-2 16z" fill="#c0283a"/>
      <path d="M58 162h124v30H58z" fill="#f2c230"/>
      <path d="M74 162v30M90 162v30M106 162v30M122 162v30M138 162v30M154 162v30M170 162v30" stroke="#a87a18"/></g>
    <path d="M144 132l14-2" stroke="#2a1a14" stroke-width="2.5" stroke-linecap="round"/>
    <path d="M134 96c8-4 18-4 24 0" stroke="#2a1a14" stroke-width="3" fill="none" stroke-linecap="round"/>
    <g fill="none" stroke="#7fd0ff" stroke-width="3.5" stroke-linejoin="round" filter="url(#oj7)" class="neon">
      <path d="M136 104l18-4-6 12z"/><rect x="22" y="22" width="196" height="186" rx="18" stroke="#4aa3ff" stroke-width="5"/></g>
    <path d="M190 46h22M202 46v32c0 10-12 12-16 4" fill="none" stroke="#1a1a1a" stroke-width="7" stroke-linecap="round"/>
    <path d="M190 46h22M202 46v32c0 10-12 12-16 4" fill="none" stroke="#8d96a0" stroke-width="3" stroke-linecap="round"/>`),
});
/* Bobby : la capsule du major Briggs (saison 3), ouverte, son message roulé qui dépasse */
Object.assign(OBJ, {
  capsule: SVG('0 0 320 150', `<defs><linearGradient id="cp8" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#4a5056"/><stop offset=".3" stop-color="#e6eaee"/>
      <stop offset=".55" stop-color="#9aa2aa"/><stop offset="1" stop-color="#33383d"/></linearGradient>
      <linearGradient id="cp8p" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#f6efdc"/><stop offset="1" stop-color="#d8cba6"/></linearGradient></defs>
    <ellipse cx="160" cy="138" rx="140" ry="8" fill="#000" opacity=".45"/>
    <rect x="30" y="52" width="170" height="64" rx="10" fill="url(#cp8)"/>
    <g stroke="#5c636a" stroke-width="2" opacity=".7"><path d="M60 52v64M170 52v64"/></g>
    <ellipse cx="200" cy="84" rx="12" ry="32" fill="#2a2e33"/>
    <path d="M198 66c40-6 80-6 100 2v34c-20 8-60 8-100 2z" fill="url(#cp8p)"/>
    <path d="M206 78h70M206 88h80M206 98h56" stroke="#7a6a4a" stroke-width="2.4" stroke-linecap="round"/>
    <g transform="translate(264 70) scale(.22)" stroke="#2a2a2a" stroke-width="7" fill="none">${SYMBOLE_HIBOU2}</g>
    <ellipse cx="300" cy="85" rx="6" ry="17" fill="#c9bb94"/>
    <rect x="236" y="110" width="58" height="28" rx="8" fill="url(#cp8)" transform="rotate(14 265 124)"/>
    <ellipse cx="40" cy="84" rx="10" ry="32" fill="#7a838a"/>`),
});
/* Annie : la couronne de Miss Twin Peaks */
Object.assign(OBJ, {
  couronne_miss: SVG('0 0 160 90', `<defs><linearGradient id="cm9" x1="0" x2="1"><stop offset="0" stop-color="#9aa2aa"/><stop offset=".5" stop-color="#ffffff"/><stop offset="1" stop-color="#8a939a"/></linearGradient></defs>
    <path d="M14 78l8-46 26 26 32-48 32 48 26-26 8 46z" fill="url(#cm9)" stroke="#6d757d" stroke-width="2"/>
    <g fill="#7fd0ff"><circle cx="80" cy="40" r="7"/><circle cx="46" cy="60" r="5"/><circle cx="114" cy="60" r="5"/></g>
    <path d="M14 78h132" stroke="#c9d1d6" stroke-width="6" stroke-linecap="round"/>`),
});
/* v9 : Mike (le bras absent, la manche épinglée), Harold (le cœur de l'orchidée), Jacques (les jetons du One Eyed Jack's) */
Object.assign(OBJ, {
  bras_mike: SVG('0 0 60 60', `<circle cx="30" cy="30" r="27" fill="#2a1b12" stroke="#c9a46a" stroke-width="2"/>
    <path d="M18 42c4-12 8-20 12-22s8 6 12 22" fill="none" stroke="#c9a46a" stroke-width="3" stroke-linecap="round"/>
    <circle cx="30" cy="17" r="5" fill="#c9a46a"/><path d="M24 30h12" stroke="#b3121f" stroke-width="3"/>`),
  coeur_orchidee: SVG('0 0 120 120', `<defs><radialGradient id="co9"><stop offset="0" stop-color="#fff6c8"/><stop offset=".6" stop-color="#f2c84b"/><stop offset="1" stop-color="#b8782a"/></radialGradient></defs>
    <path d="M60 18c18 10 26 30 22 50-4 18-14 30-22 34-8-4-18-16-22-34-4-20 4-40 22-50z" fill="#f5e7f0" stroke="#c98fb5" stroke-width="2"/>
    <path d="M60 46c10 4 14 14 12 24s-6 16-12 18c-6-2-10-8-12-18s2-20 12-24z" fill="url(#co9)"/>
    <g fill="#8a2a5a"><circle cx="54" cy="62" r="2.4"/><circle cx="66" cy="60" r="2.2"/><circle cx="58" cy="74" r="2"/><circle cx="64" cy="72" r="1.8"/></g>`),
  jetons: SVG('0 0 120 90', `<g stroke="#00000055" stroke-width="1.5">
    <ellipse cx="40" cy="70" rx="30" ry="10" fill="#b3121f"/><rect x="10" y="44" width="60" height="26" fill="#b3121f"/><ellipse cx="40" cy="44" rx="30" ry="10" fill="#d8323c"/>
    <ellipse cx="88" cy="74" rx="26" ry="9" fill="#1d1d24"/><rect x="62" y="58" width="52" height="16" fill="#1d1d24"/><ellipse cx="88" cy="58" rx="26" ry="9" fill="#3a3a46"/></g>
    <g fill="none" stroke="#fff" stroke-width="3" stroke-dasharray="6 7"><ellipse cx="40" cy="44" rx="22" ry="7"/><ellipse cx="88" cy="58" rx="19" ry="6"/></g>`),
});
/* Sarah Palmer : le cheval blanc de ses visions */
Object.assign(OBJ, {
  cheval_blanc: SVG('0 0 200 160', `<defs><radialGradient id="chb" cx=".5" cy=".4"><stop offset="0" stop-color="#fff"/><stop offset="1" stop-color="#d8d4cc"/></radialGradient></defs>
    <path d="M44 62c10-18 34-26 58-22 12-14 28-22 40-20l6-12 6 14c10 6 16 16 16 26l14 18c4 6-2 12-8 10l-16-6c-6 10-14 16-14 30l2 34h-10l-6-32-10 4-4 30h-10l-2-30c-16 2-30-2-40-10l-8 40h-10l2-44c-8-6-12-10-16-14l-10 30H18l12-40c-2-12 2-24 14-34z" fill="url(#chb)" stroke="#bfb8ab" stroke-width="2"/>
    <path d="M140 34c-6 10-8 22-4 34M150 30c-4 12-2 24 4 32" fill="none" stroke="#e8e4dc" stroke-width="5" stroke-linecap="round"/>
    <circle cx="160" cy="44" r="2.4" fill="#222"/>`),
});
/* Les frères Mitchum : l'enveloppe du contrat (cachet rouge) */
Object.assign(OBJ, {
  enveloppe_contrat: SVG('0 0 120 80', `<rect x="4" y="6" width="112" height="70" rx="5" fill="#efe6cf" stroke="#b8a780" stroke-width="2"/>
    <path d="M4 10l56 38 56-38" fill="none" stroke="#b8a780" stroke-width="3"/>
    <circle cx="60" cy="46" r="13" fill="#b3121f"/><path d="M53 46h14M60 39v14" stroke="#7a0d16" stroke-width="3"/>
    <text x="60" y="72" text-anchor="middle" font-family="Georgia,serif" font-size="9" fill="#5a4a3a">CONTRACT</text>`),
});
