export interface Certificate {
 certificateId:string;studentName:string;displaySubtitle?:string;courseId:string;courseName:string;type:'free'|'premium';skills:string[];assessmentScore:number|null;completedAt?:string;issuedAt:string;verificationStatus:string;templateVersion:string;paymentStatus:string;issuer:string;achievementDescription:string;publicUrl:string;pdfUrl:string;qrUrl:string;
}
export interface Eligibility {courseId:string;courseName:string;eligible:boolean;reasons:string[];requiredModuleIds:string[];completedModules:number;assessments:{id:string;title:string;passed:boolean;passingScore:number}[];skills:string[];assessmentScore:number|null;completionNote:string;}
export interface Order {orderId:string;courseId:string;mode:string;amount:number;currency:string;status:string;notice:string;}
export interface CertificateList {certificates:Certificate[];courses:Eligibility[];payment:{mode:string;amount:number;currency:string;notice:string};}
export async function certificateApi<T>(path:string,body?:unknown,authenticated=true):Promise<T>{
 const response=await fetch('/api/v1/certificates'+path,{method:body===undefined?'GET':'POST',headers:{...(body!==undefined?{'Content-Type':'application/json'}:{}),...(authenticated?{Authorization:`Bearer ${sessionStorage.getItem('plcip_token')||''}`}:{})},body:body===undefined?undefined:JSON.stringify(body)});
 const data=await response.json().catch(()=>({detail:'Certificate service returned an invalid response.'}));
 if(!response.ok)throw new Error(typeof data.detail==='string'?data.detail:'Certificate request failed.');return data;
}
