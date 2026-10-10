import {useEffect,useState} from 'react';
import {ShieldCheck,History} from 'lucide-react';
import {intelligenceApi} from './api';
import {useAppState} from '../../lib/state/app-state';

type Approval={id:string;toolName:string;status:string;reason:string;preview:Record<string,unknown>;createdAt:string;errorCode?:string};
type Audit={auditId:string;tool:string;resultStatus:string;approvalStatus:string;timestamp:string};
export function AgentGovernance(){
  const {refreshWorkspace}=useAppState();
  const [approvals,setApprovals]=useState<Approval[]>([]),[audit,setAudit]=useState<Audit[]>([]);
  const [error,setError]=useState(''),[busy,setBusy]=useState('');
  useEffect(()=>{let alive=true;const load=async()=>{try{
    const [a,b]=await Promise.all([intelligenceApi('/agent/approvals'),intelligenceApi('/agent/audit')]);
    if(alive){setApprovals(a);setAudit(b);}
  }catch{if(alive)setError('Agent activity could not be loaded.');}};
    void load();const timer=setInterval(load,4000);return()=>{alive=false;clearInterval(timer);};},[]);
  const decide=async(id:string,decision:'approve'|'reject')=>{
    setBusy(id);setError('');try{
      const result=await intelligenceApi('/agent/approvals/'+id,{decision});
      setApprovals(rows=>rows.map(a=>a.id===id?result:a));
      if(result.status==='completed')await refreshWorkspace();
      if(result.status==='failed')setError('The action failed. Inspect its status before submitting another request.');
    }catch(e){setError(e instanceof Error?e.message:'Decision could not be saved.');}finally{setBusy('');}
  };
  return <section aria-label="Agent approvals and audit" className="rounded-xl border border-slate-200 bg-white p-4 space-y-3">
    <h3 className="flex items-center gap-2 font-semibold text-slate-800"><ShieldCheck size={17}/>Agent approvals</h3>
    <p className="text-xs text-slate-500">Agent changes require your approval. Read-only checks do not change your scores.</p>
    {error&&<p role="alert" className="text-sm text-red-700">{error}</p>}
    {approvals.filter(a=>a.status==='pending_approval').length===0&&<p className="text-sm text-slate-500">No actions awaiting approval.</p>}
    {approvals.filter(a=>a.status==='pending_approval').map(a=><article key={a.id} className="rounded-lg border border-teal-200 bg-teal-50/40 p-3 space-y-2">
      <h4 className="font-semibold text-sm">{a.toolName.replace(/([a-z])([A-Z])/g,'$1 $2').replace('workspace.','Workspace: ')}</h4>
      <p className="text-xs text-slate-600">{a.reason}</p>
      <pre className="text-xs whitespace-pre-wrap break-words max-h-40 overflow-auto">{JSON.stringify(a.preview,null,2)}</pre>
      <div className="flex gap-2"><button disabled={!!busy} onClick={()=>void decide(a.id,'approve')} className="px-3 py-1.5 rounded bg-teal-700 text-white text-sm disabled:opacity-50">{busy===a.id?'Processing…':'Approve'}</button>
      <button disabled={!!busy} onClick={()=>void decide(a.id,'reject')} className="px-3 py-1.5 rounded border border-slate-300 text-sm disabled:opacity-50">Reject</button></div>
    </article>)}
    <details><summary className="cursor-pointer text-sm font-semibold flex items-center gap-2"><History size={16}/>Agent activity / audit history</summary>
      <ul className="mt-3 space-y-2 max-h-64 overflow-auto">{audit.map(a=><li key={a.auditId} className="text-xs border-b border-slate-100 pb-2"><strong>{a.tool}</strong> · {a.resultStatus} · {a.approvalStatus}<br/><time>{new Date(a.timestamp).toLocaleString()}</time></li>)}</ul>
    </details>
  </section>;
}
