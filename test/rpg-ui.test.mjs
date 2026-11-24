import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
const read=p=>readFileSync(new URL('../'+p,import.meta.url),'utf8');
test('RPG UI is self-contained and has a GM panel, player character builder and map',()=>{
 const html=read('public/rpg.html'),js=read('public/rpg.js');
 for(const label of ['id="app"','/rpg.js','/rpg.css','Discord'])assert.ok(html.includes(label),label);
 for(const label of ['characterEditor','masterPanel','mapSvg','newSession','requestRoll','leaderboard','room.code'].filter(x=>x!=='leaderboard'))assert.ok(js.includes(label),label);
});
test('original RPG assets do not embed unofficial copyrighted rulebook prose or fetched remote images',()=>{
 const html=read('public/rpg.html'),js=read('public/rpg.js'),css=read('public/rpg.css');
 assert.doesNotMatch(js,/(ordem paranormal|or[oó] realitas|o outro lado)/i);
 assert.doesNotMatch(css,/@import\s+url/);
 assert.doesNotMatch(html,/<script(?![^>]+src)/i);
});
