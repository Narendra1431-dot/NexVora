export async function codingApi<T=any>(path:string,body?:unknown,method?:string,signal?:AbortSignal):Promise<T>{
 const r=await fetch('/api/v1/coding'+path,{method:method||(body===undefined?'GET':'POST'),headers:{Authorization:'Bearer '+sessionStorage.getItem('plcip_token'),'Content-Type':'application/json'},body:body===undefined?undefined:JSON.stringify(body),signal});
 const d=await r.json().catch(()=>({detail:'Coding service returned an invalid response.'}));
 if(!r.ok)throw new Error(typeof d.detail==='string'?d.detail:'Check your input and try again.');return d;
}
