import {test} from 'node:test';
import assert from 'node:assert/strict';
import {getRank,rankLabel,applyRankResult} from '../public/rank.mjs';

function makeRoom(code,created,winner,teams=4){
 const members=Array.from({length:teams},(_,i)=>({id:`t${i+1}`,name:`Equipe ${i+1}`,roster:{TOP:'a'}}));
 const matches=teams===2
  ? [{a:'t1',b:'t2',winner,stage:'playoffs',round:1,score:winner==='t1'?[2,1]:[1,2]}]
  : [{a:'t1',b:'t2',winner:'t1',stage:'playoffs',round:1,score:[2,0]},
    {a:'t3',b:'t4',winner:'t3',stage:'playoffs',round:1,score:[2,0]},
    {a:'t1',b:'t3',winner,stage:'playoffs',round:2,score:winner==='t1'?[2,0]:[0,2]}];
 return {code,created,phase:'finished',members,matches,champion:winner};
}

test('ranking começa no Bronze IV e premia o campeão uma única vez por sala',()=>{
 const data=new Map();globalThis.localStorage={getItem:key=>data.get(key)??null,setItem:(key,value)=>data.set(key,value)};
 const r=makeRoom('T1',100,'t1',4);
 assert.equal(rankLabel(getRank('Equipe 1')),'Bronze IV');
 const reward=applyRankResult(r,'t1');assert.equal(reward.delta,22);
 assert.equal(reward.place,1);assert.equal(reward.rank,'Bronze IV');
 assert.equal(getRank('Equipe 1').lp,22);assert.equal(getRank('Equipe 1').titles,1);
 assert.equal(getRank('Equipe 1').wins,1);assert.equal(getRank('Equipe 1').losses,0);
 assert.equal(applyRankResult(r,'t1'),null);assert.equal(getRank('Equipe 1').titles,1);
});
test('vice perde menos PDL que último; várias conquistas geram subida lenta',()=>{
 const data=new Map();globalThis.localStorage={getItem:key=>data.get(key)??null,setItem:(key,value)=>data.set(key,value)};
 const r=makeRoom('T2',200,'t1',4);
 const vice=applyRankResult(r,'t3'),eliminado=applyRankResult(r,'t4');
 assert.equal(vice.place,2);assert.equal(vice.delta,-5);
 assert.ok(eliminado.delta<vice.delta);
 assert.equal(getRank('Equipe 3').losses,1);
 for(let n=0;n<5;n++)applyRankResult(makeRoom('V'+n,300+n,'t1',4),'t1');
 assert.equal(rankLabel(getRank('Equipe 1')),'Bronze III');
 assert.equal(getRank('Equipe 1').lp,10);
});
