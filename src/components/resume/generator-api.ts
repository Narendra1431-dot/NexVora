export type ResumeBlock={id:string;text:string;state?:'VERIFIED'|'SUPPORTED'|'UNVERIFIED';sourceIds?:string[];keepSelfReported:boolean};
export type ResumeSection={id:string;blocks:ResumeBlock[]};
export type ResumeDraft={draftId:string;version:number;name:string;headline:string;headlineSelfReported?:boolean;contact:string;targetRole:string;careerId:string;template:string;sections:ResumeSection[];generatedContent:ResumeSection[];manualEdits:boolean;updatedAt:string;provider?:string};
export type ResumeMetrics={atsScore:number;targetRoleMatch:number;keywordCoverage:number;evidenceCoverage:number;sectionCompleteness:number;unsupportedClaims:{id:string;text:string;acknowledged:boolean}[];missingKeywords:string[];exportReady:boolean;note:string;sections:ResumeSection[]};
export type ResumeFact={id:string;section:string;text:string;state:'VERIFIED'|'SUPPORTED'|'UNVERIFIED';evidenceIds:string[]};
export type ResumeContext={targetRole:string;careerId:string;name:string;facts:ResumeFact[];missingInformation:string[];provider:string;findings:string[]};
export async function resumeRequest<T>(path:string,body?:unknown,signal?:AbortSignal):Promise<T>{
 const r=await fetch('/api/v1/resume'+path,{method:body===undefined?'GET':'POST',headers:{Authorization:'Bearer '+(sessionStorage.getItem('plcip_token')||''),...(body!==undefined?{'Content-Type':'application/json'}:{})},body:body===undefined?undefined:JSON.stringify(body),signal});
 if(!r.ok){const d=await r.json().catch(()=>({detail:'Resume service unavailable.'}));throw new Error(typeof d.detail==='string'?d.detail:'Check the resume fields and retry.');}
 return await r.json();
}
export async function resumeFile(format:string,doc:ResumeDraft){
 const r=await fetch('/api/v1/resume/export/'+format,{method:'POST',headers:{Authorization:'Bearer '+(sessionStorage.getItem('plcip_token')||''),'Content-Type':'application/json'},body:JSON.stringify(doc)});
 if(!r.ok){const d=await r.json().catch(()=>({detail:'Export failed.'}));throw new Error(d.detail||'Export failed.');}
 return r.blob();
}
