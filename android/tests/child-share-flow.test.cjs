// Behavior-level regression checks for the opt-in child sharing wizard.
// Execute the actual production scripts against a DOM, not grep-based tests.
'use strict';
const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const {JSDOM}=require('jsdom');
const ROOT=path.resolve(__dirname,'..','body');
const source=name=>fs.readFileSync(path.join(ROOT,name),'utf8');
function createApp(){
  const html='<!doctype html><html><head></head><body><main>'+
    '<div id="profiles"></div><div id="shared"><div id="shared-content"></div></div>'+
    '<details id="outgoing-share-wrapper"><details id="outgoing-advanced">'+
    '<div id="share-actions"><h3>Partager mon profil</h3>'+
    '<p class="notice">Le destinataire ne peut rien modifier.</p>'+
    '<p id="share-state">Aucun fichier de partage relié</p>'+
    '<button id="create-share">Créer le fichier partagé sur Drive</button>'+
    '<button id="share-relink">Relier un partage existant</button>'+
    '</div></details></details></main></body></html>';
  const dom=new JSDOM(html,{runScripts:'outside-only',url:'https://localhost/'});
  const {window}=dom,document=window.document;
  const state={
    enabled:false,linked:false,password:false,editableFileName:'mon-evolution-partage-enfant.json',
    active:{id:'child1',name:'Enfant',birthDate:'2018-04-03'},
    nativeOpen:[],createClicks:0,relinkClicks:0,genericDriveOpens:0
  };
  window.profile=()=>state.active;
  window.render=()=>null;
  window.message=()=>null;
  window.confirm=()=>true;
  window.requestAnimationFrame=fn=>{fn();return 1};
  window.backupPayload=()=>'{ }';
  const api={
    childEditEnabled:id=>state.enabled&&id===state.active.id,
    setChildEditEnabled:(id,v)=>{if(id===state.active.id)state.enabled=v},
    childSetupVerified:()=>false,
    sharedStatus:id=>state.linked&&id===state.active.id?'1':'0',
    hasSharePassword:id=>state.password&&id===state.active.id,
    childShareDocumentInfo:id=>JSON.stringify({
      linked:state.linked&&id===state.active.id,
      name:state.editableFileName,provider:'Google Drive'
    }),
    openChildShareDocument:id=>state.nativeOpen.push(id),
    openDrive:()=>state.genericDriveOpens++,
    autoSave:()=>null,
    verifyOwnedChildShare:()=>null
  };
  window.AndroidBackup=api;
  document.getElementById('create-share').addEventListener('click',()=>state.createClicks++);
  document.getElementById('share-relink').addEventListener('click',()=>state.relinkClicks++);
  for(const name of ['child-collaboration.js','child-share-verification.js','child-share-file-guide.js']){
    window.eval(source(name));
  }
  const get=id=>document.getElementById(id);
  const ready=()=>new Promise(resolve=>setTimeout(resolve,0));
  const render=async()=>{window.render();await ready()};
  const activate=async()=>{
    const checkbox=get('child-collab-enable');
    checkbox.checked=true;
    checkbox.dispatchEvent(new window.Event('change',{bubbles:true}));
    await render();
  };
  return {dom,window,document,state,api,get,ready,render,activate};
}
test('Option OFF: no mandatory Drive checks',async()=>{
  const a=createApp();await a.render();
  assert.equal(a.get('child-owner-required-steps').hidden,true);
  assert.equal(a.get('child-share-file-guide').hidden,true);
  assert.equal(a.state.enabled,false);
  a.dom.window.close();
});
test('Option ON, missing file: create/relink offered and Editor blocked',async()=>{
  const a=createApp();await a.activate();
  assert.equal(a.get('child-owner-required-steps').hidden,false);
  assert.equal(a.get('child-share-file-guide').hidden,false);
  assert.equal(a.get('child-share-file-create').disabled,false);
  assert.equal(a.get('child-share-file-relink').hidden,false);
  assert.equal(a.get('child-share-file-open').disabled,true);
  assert.equal(a.get('child-verify-invitation').disabled,true);
  assert.equal(a.get('child-verify-invitation').checked,false);
  assert.equal(([...a.get('child-owner-required-steps').querySelectorAll('button.primary')].find(b=>b.textContent.includes('Vérifier et activer'))).disabled,true);
  assert.match(a.get('child-share-selected-file').textContent,/Aucun fichier relié/);
  a.dom.window.close();
});
test('Create uses existing share creation handler, no fake Drive permissions',async()=>{
  const a=createApp();await a.activate();
  a.get('child-share-file-create').click();
  assert.equal(a.state.createClicks,1);
  assert.equal(a.get('outgoing-advanced').open,true);
  assert.equal(a.get('outgoing-share-wrapper').open,true);
  assert.equal(a.state.genericDriveOpens,0);
  a.dom.window.close();
});
test('Existing file without password keeps editing disabled',async()=>{
  const a=createApp();await a.activate();
  a.state.linked=true;a.state.password=false;
  a.get('share-state').textContent='Partage relié';
  await a.ready();await a.render();
  assert.equal(a.get('child-share-file-create').disabled,true);
  assert.equal(a.get('child-share-file-open').disabled,false);
  assert.equal(a.get('child-verify-invitation').disabled,true);
  assert.equal(([...a.get('child-owner-required-steps').querySelectorAll('button.primary')].find(b=>b.textContent.includes('Vérifier et activer'))).disabled,true);
  a.dom.window.close();
});
test('Linked encrypted file opens exact document, needs Editor confirmation',async()=>{
  const a=createApp();await a.activate();
  a.state.linked=true;a.state.password=true;
  a.get('share-state').textContent='Partage relié';
  await a.ready();await a.render();
  assert.equal(a.get('child-share-file-create').disabled,true);
  assert.equal(a.get('child-share-file-open').disabled,false);
  assert.equal(a.get('child-verify-invitation').disabled,false);
  assert.equal(([...a.get('child-owner-required-steps').querySelectorAll('button.primary')].find(b=>b.textContent.includes('Vérifier et activer'))).disabled,true);
  assert.match(a.get('child-share-selected-file').textContent,/mon-evolution-partage-enfant\.json/);
  a.get('child-share-file-open').click();
  assert.deepEqual(a.state.nativeOpen,['child1']);
  assert.equal(a.state.genericDriveOpens,0);
  a.get('child-verify-invitation').checked=true;
  a.get('child-verify-invitation').dispatchEvent(new a.window.Event('change',{bubbles:true}));
  await a.ready();
  assert.equal(([...a.get('child-owner-required-steps').querySelectorAll('button.primary')].find(b=>b.textContent.includes('Vérifier et activer'))).disabled,false);
  a.dom.window.close();
});
test('Disconnect resets checked Editor and green checklist',async()=>{
  const a=createApp();await a.activate();
  a.state.linked=true;a.state.password=true;
  a.get('share-state').textContent='Partage relié';await a.ready();await a.render();
  const checkbox=a.get('child-verify-invitation');
  checkbox.checked=true;checkbox.dispatchEvent(new a.window.Event('change',{bubbles:true}));
  await a.ready();
  assert.equal(checkbox.checked,true);
  a.state.linked=false;
  a.get('share-state').textContent='Aucun partage configuré';
  await a.ready();await a.render();
  assert.equal(checkbox.checked,false);
  assert.equal(checkbox.disabled,true);
  const wizard=a.get('child-owner-required-steps');
  assert.equal(wizard.querySelector('button.primary').disabled,true);
  const rows=[...wizard.querySelectorAll('div > div')];
  const last=rows.find(row=>row.textContent.includes('Invitation Éditeur privée confirmée'));
  assert.ok(last,'Checklist must include invitation');
  assert.ok(last.textContent.includes('✕'),'Stale green checklist: '+last.textContent);
  a.dom.window.close();
});
test('Switching profile clears prior Editor confirmation',async()=>{
  const a=createApp();await a.activate();
  a.state.linked=true;a.state.password=true;
  a.get('share-state').textContent='Partage relié';await a.ready();await a.render();
  const checkbox=a.get('child-verify-invitation');
  checkbox.checked=true;checkbox.dispatchEvent(new a.window.Event('change',{bubbles:true}));
  await a.ready();assert.equal(checkbox.checked,true);
  a.state.active={id:'child2',name:'Autre enfant',birthDate:'2020-01-11'};
  a.state.linked=false;a.state.password=false;a.state.enabled=true;
  await a.render();
  assert.equal(checkbox.checked,false);
  assert.equal(checkbox.disabled,true);
  assert.match(a.get('child-share-selected-file').textContent,/Autre enfant/);
  a.dom.window.close();
});
