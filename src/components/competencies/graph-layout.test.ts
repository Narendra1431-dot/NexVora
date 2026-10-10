import {describe,it,expect} from 'vitest';
import {layoutSkills,prerequisitePath} from './graph-layout';
import type {CompetencyNode} from '../../types';
export function fixture(count:number):CompetencyNode[]{return Array.from({length:count},(_,i)=>({id:'skill-'+i,name:'Competency '+i+' with a descriptive readable label',domain:'Core Programming',state:'Skill Gap',mastery:i%100,confidence:60,careerImportance:'High',evidenceCount:i%3,prerequisites:i>=5?[`skill-${i-5}`,...(i%5<4?[`skill-${i-4}`]:[]),...(i>=10&&i%3===0?[`skill-${i-10}`]:[])]:[],dependents:[],relatedConcepts:[],remainingGap:'Needs evidence',recommendedAction:'Study next',type:'Skill',x:0,y:0}));}
describe('ELK layout',()=>{
 for(const count of [30,50])it(`routes ${count} skills without overlapping cards or edge/card collisions`,async()=>{
  const nodes=fixture(count);const original=JSON.stringify(nodes);const map=await layoutSkills(nodes,new Set([nodes.at(-1)!.id]),'Career goal');
  expect(JSON.stringify(nodes)).toBe(original);expect(map.cards).toHaveLength(count+1);
  for(let i=0;i<map.cards.length;i++)for(let j=i+1;j<map.cards.length;j++){
   const a=map.cards[i],b=map.cards[j];expect(a.x+a.width<=b.x||b.x+b.width<=a.x||a.y+a.height<=b.y||b.y+b.height<=a.y).toBe(true);
  }
  for(const edge of map.edges){
   const source=map.cards.find(c=>c.id===edge.source)!,target=map.cards.find(c=>c.id===edge.target)!;
   expect(source.x+source.width).toBeLessThanOrEqual(target.x);
   for(let i=1;i<edge.points.length;i++){
    const a=edge.points[i-1],b=edge.points[i];expect(a.x===b.x||a.y===b.y).toBe(true);
    for(const card of map.cards.filter(c=>c.id!==edge.source&&c.id!==edge.target)){
     const intersects=a.x===b.x?a.x>card.x&&a.x<card.x+card.width&&Math.max(a.y,b.y)>card.y&&Math.min(a.y,b.y)<card.y+card.height:a.y>card.y&&a.y<card.y+card.height&&Math.max(a.x,b.x)>card.x&&Math.min(a.x,b.x)<card.x+card.width;
     expect(intersects).toBe(false);
    }
   }
  }
 },15000);
 it('handles cycles safely when finding prerequisite chains',()=>{
  const nodes=fixture(3);nodes[0].prerequisites=['skill-2'];nodes[1].prerequisites=['skill-0'];nodes[2].prerequisites=['skill-1'];expect([...prerequisitePath(nodes,['skill-2'])].sort()).toEqual(['skill-0','skill-1','skill-2']);
 });
});
