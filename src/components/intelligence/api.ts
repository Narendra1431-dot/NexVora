export async function intelligenceApi(path:string,body?:unknown,method?:string) {
  const form=body instanceof FormData;
  const response=await fetch('/api/v1'+path,{method:method||(body?'POST':'GET'),
    headers:{Authorization:'Bearer '+sessionStorage.getItem('plcip_token'),...(!form?{'Content-Type':'application/json'}:{})},
    body:body===undefined?undefined:form?body:JSON.stringify(body)});
  const data=await response.json();
  if(!response.ok)throw new Error(typeof data.detail==='string'?data.detail:'The request could not be completed.');
  return data;
}
