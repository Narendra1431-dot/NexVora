import type {ElkNode} from 'elkjs/lib/elk-api';
import type {CompetencyNode} from '../../types';
export const domains = [
 {id:'Math & Foundations',label:'Foundations'}, {id:'Core Programming',label:'Programming'},
 {id:'Data Systems',label:'Data'}, {id:'Machine Learning',label:'ML'},
 {id:'Deep Learning & NLP',label:'Deep Learning / NLP'}, {id:'MLOps & Deployment',label:'MLOps'}
];
export function prerequisitePath(nodes:CompetencyNode[], seeds:string[]) {
 const map=new Map(nodes.map(n=>[n.id,n])); const result=new Set<string>();
 const visit=(id:string)=>{if(result.has(id)||!map.has(id))return;result.add(id);map.get(id)!.prerequisites.forEach(visit);};
 seeds.forEach(visit);return result;
}
export function stateColor(state:string) {
 return state==='Verified'?'#15803d':state==='In Progress'?'#2563eb':state==='Prerequisite Gap'?'#dc2626':state==='Skill Gap'?'#c2410c':'#64748b';
}
export interface LayoutCard {id:string;x:number;y:number;width:number;height:number}
export interface LayoutEdge {id:string;source:string;target:string;points:{x:number;y:number}[]}
export interface MapLayout {cards:LayoutCard[];edges:LayoutEdge[];width:number;height:number}
export async function layoutSkills(nodes:CompetencyNode[],required:Set<string>,goalTitle:string):Promise<MapLayout> {
 const {default:ELK}=await import('elkjs/lib/elk.bundled.js');
 const ids=new Set(nodes.map(n=>n.id));
 const children=nodes.map(n=>({id:n.id,width:248,height:Math.max(144,Math.ceil(n.name.length/24)*20+82)}));
 if(goalTitle)children.push({id:'__goal__',width:248,height:144});
 const edges=nodes.flatMap(n=>n.prerequisites.filter(p=>ids.has(p)&&p!==n.id).map(p=>({id:p+'->'+n.id,sources:[p],targets:[n.id]})));
 if(goalTitle)nodes.filter(n=>required.has(n.id)).forEach(n=>edges.push({id:n.id+'->__goal__',sources:[n.id],targets:['__goal__']}));
 const result=await new ELK().layout<ElkNode>({id:'root',layoutOptions:{'elk.algorithm':'layered','elk.direction':'RIGHT','elk.edgeRouting':'ORTHOGONAL','elk.spacing.nodeNode':'54','elk.spacing.edgeNode':'24','elk.spacing.edgeEdge':'16','elk.layered.spacing.nodeNodeBetweenLayers':'100','elk.layered.spacing.edgeNodeBetweenLayers':'24','elk.layered.spacing.edgeEdgeBetweenLayers':'18','elk.layered.mergeEdges':'false','elk.padding':'[top=32,left=32,bottom=32,right=32]'},children,edges});
 return {width:result.width||1,height:result.height||1,cards:(result.children||[]).map(n=>({id:n.id,x:n.x||0,y:n.y||0,width:n.width!,height:n.height!})),edges:(result.edges||[]).flatMap(e=>(e.sections||[]).map((s,i)=>({id:e.id+'-'+i,source:e.sources[0],target:e.targets[0],points:[s.startPoint,...(s.bendPoints||[]),s.endPoint]})))};
}
