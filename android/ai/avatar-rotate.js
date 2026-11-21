/* Mon Evolution IMC — non-destructive portrait rotation/mirror, v1.6.100.
   Changes only the active local profile's JPEG; shares/backup use the saved pixels. */
(() => {
  'use strict';
  const photo = document.getElementById('avatar-display');
  if (!photo || !document.getElementById('avatar-choose')) return;

  const toolbar = document.createElement('div');
  toolbar.id = 'avatar-rotate-tools';
  toolbar.style.cssText = 'display:flex;align-items:center;justify-content:center;flex-wrap:wrap;gap:9px;margin:0 auto 12px';
  const controls = [];
  let busy = false;

  function updateControls() {
    const active = profile();
    const available = !busy && typeof active?.avatar === 'string' &&
      /^data:image\/jpeg;base64,/.test(active.avatar) && active.avatar.length < 250000;
    for (const btn of controls) btn.disabled = !available;
    toolbar.style.display = active?.avatar ? 'flex' : 'none';
  }
  function button(symbol, name, operation) {
    const b = document.createElement('button');
    b.type = 'button';
    b.className = 'secondary';
    b.title = name;
    b.setAttribute('aria-label',name+' la photo du profil');
    b.style.cssText = 'display:inline-flex;align-items:center;justify-content:center;gap:6px;padding:8px 12px;min-height:39px;font-size:.84rem;line-height:1.2';
    const icon = document.createElement('span');
    icon.textContent = symbol;
    icon.setAttribute('aria-hidden','true');
    icon.style.cssText = 'font-size:1.25rem;line-height:1';
    b.append(icon,document.createTextNode(name));
    b.addEventListener('click',()=>transform(operation));
    controls.push(b);
    toolbar.append(b);
  }
  button('⟲','Gauche','left');
  button('⟳','Droite','right');
  button('⇋','Miroir','mirror');
  photo.insertAdjacentElement('afterend',toolbar);

  function transform(operation) {
    const selected = profile();
    const id = selected?.id;
    const original = selected?.avatar || '';
    if (busy || !id || !/^data:image\/jpeg;base64,/.test(original)) return;
    busy = true; updateControls();
    const image = new Image();
    image.onload = () => {
      try {
        const naturalWidth = image.naturalWidth;
        const naturalHeight = image.naturalHeight;
        if (!naturalWidth || !naturalHeight) throw Error('Dimensions de la photo indisponibles');
        let result = '';
        for (const limit of [640,480,360,280]) {
          const ratio = Math.min(1,limit/Math.max(naturalWidth,naturalHeight));
          const width = Math.max(1,Math.round(naturalWidth*ratio));
          const height = Math.max(1,Math.round(naturalHeight*ratio));
          const turn = operation !== 'mirror';
          const canvas = document.createElement('canvas');
          canvas.width = turn ? height : width;
          canvas.height = turn ? width : height;
          const ctx = canvas.getContext('2d');
          if (!ctx) throw Error('Rotation non disponible');
          if (operation === 'right') {
            ctx.translate(canvas.width,0);
            ctx.rotate(Math.PI/2);
          } else if (operation === 'left') {
            ctx.translate(0,canvas.height);
            ctx.rotate(-Math.PI/2);
          } else if (operation === 'mirror') {
            ctx.translate(canvas.width,0);
            ctx.scale(-1,1);
          }
          ctx.drawImage(image,0,0,width,height);
          for (const quality of [.90,.82,.72,.62,.50]) {
            const jpeg = canvas.toDataURL('image/jpeg',quality);
            if (jpeg.length < 250000) {result = jpeg;break;}
          }
          if (result) break;
        }
        if (!result) throw Error('Photo trop volumineuse pour la sauvegarde');
        const target = data.profiles.find(p=>p.id===id);
        // Ignore a stale rotation if another photo was chosen in the meantime.
        if (!target || target.avatar !== original) return;
        target.avatar = result;
        save();
        renderAvatars();
        message('Orientation de la photo enregistrée ✓');
      } catch(e) {
        message('Rotation impossible : '+(e?.message||'image invalide'));
      } finally {
        busy = false;updateControls();
      }
    };
    image.onerror = () => {busy=false;updateControls();message('Photo impossible à ouvrir');};
    image.src = original;
  }
  const originalRender = renderAvatars;
  renderAvatars = function() {
    const result = originalRender.apply(this,arguments);
    updateControls();
    return result;
  };
  updateControls();
})();