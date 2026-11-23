import {test} from 'node:test';import assert from 'node:assert/strict';import fs from 'node:fs';
import PLAYERS from '../data/players.json' with {type:'json'};
import PHOTOS from '../data/player-photos.json' with {type:'json'};
import DRAFTS from '../data/worlds-drafts.json' with {type:'json'};
test('43 fotos locais reais têm proveniência e o build preserva arquivos aninhados',()=>{for(const p of PLAYERS){const photo=PHOTOS[p.id];assert.ok(photo.source.startsWith('https://'));assert.ok(photo.credit);assert.equal(p.photo,photo.path);const file=fs.readFileSync('public'+photo.path);assert.equal(file.toString('ascii',0,4),'RIFF');assert.equal(file.toString('ascii',8,12),'WEBP');assert.ok(file.length>1000);}});
test('50 drafts citam o Worlds 2026 e quatro packs garantem alternativas disjuntas',()=>{assert.equal(DRAFTS.length,50);let packs=0;for(const [series,rows] of Object.entries(Object.groupBy(DRAFTS,d=>d.series))){for(const row of rows){assert.equal(row.event,'Worlds 2026');assert.ok(row.source.startsWith('https://'));assert.ok(row.team&&row.opponent&&row.game);}if(rows.length>=8&&new Set(rows.flatMap(d=>Object.values(d.champions))).size===rows.length*5)packs++;}assert.equal(packs,4);});

// Guard against the production boot regression: app.js imports champion stats as JSON.
test('production bundle serves champion stats imported by the entry module',async()=>{
  const {execFileSync}=await import('node:child_process');
  execFileSync(process.execPath,['scripts/build.mjs'],{cwd:process.cwd(),stdio:'pipe'});
  const worker=(await import('../dist/server/index.js?assetcheck='+Date.now())).default;
  const r=await worker.fetch(new Request('https://rift.example/champion-stats.json'),{},{});
  assert.equal(r.status,200);
  assert.match(r.headers.get('content-type')||'',/application\/json/);
  const body=await r.json();
  assert.ok(body&&typeof body==='object');
  assert.ok(Object.keys(body).length>0);
});
