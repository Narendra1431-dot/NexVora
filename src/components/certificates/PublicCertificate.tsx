import {useEffect,useState} from 'react';

import {certificateApi,type Certificate} from './api';

import {CertificateActions} from './CertificateShared';

export function PublicCertificate({id}:{id:string}){

 const [certificate,setCertificate]=useState<Certificate|null>(null);const [error,setError]=useState('');

 useEffect(()=>{let active=true;setCertificate(null);setError('');certificateApi<Certificate>('/verify/'+encodeURIComponent(id),undefined,false).then(c=>{if(active)setCertificate(c);}).catch(e=>{if(active)setError(e.message);});return()=>{active=false;};},[id]);

 return <main className="min-h-screen bg-slate-50 p-4 sm:p-8 text-slate-900"><div className="mx-auto max-w-5xl space-y-5"><a href="/" className="font-semibold text-teal-800">NexVora</a>{error?<div role="alert" className="rounded-xl border bg-white p-6"><h1 className="text-xl font-semibold">{error.includes('not found')?'Certificate not found or invalid.':'Certificate verification unavailable.'}</h1><p className="mt-2 text-sm">{error.includes('not found')?'Check the certificate ID and try the original verification link.':error}</p></div>:!certificate?<p role="status">Loading certificate registry record...</p>:<><section className="rounded-xl border border-slate-200 bg-white p-5"><p className="text-sm font-semibold text-teal-800">Registry verification: {certificate.verificationStatus}</p><h1 className="mt-2 text-2xl font-semibold break-words">{certificate.courseName}</h1><dl className="mt-4 grid sm:grid-cols-2 gap-3 text-sm">{[['Student',certificate.studentName],['Display subtitle',certificate.displaySubtitle||'—'],['Type',certificate.type],['Completed',(certificate.completedAt||certificate.issuedAt).slice(0,10)],['Issue date',certificate.issuedAt.slice(0,10)],['Certificate ID',certificate.certificateId],['Issuer',certificate.issuer],['Verified skills',certificate.skills.join(', ')||'Full competency verification pending']].map(([key,value])=><div key={key}><dt className="text-slate-500">{key}</dt><dd className="font-medium break-all">{value}</dd></div>)}{certificate.type==='premium'&&<div><dt>Assessment score</dt><dd>{certificate.assessmentScore}%</dd></div>}</dl>{certificate.paymentStatus==='demo_confirmed'&&<p className="mt-4 text-sm text-amber-800">DEMO premium purchase. No money was charged.</p>}<div className="mt-5 flex flex-wrap gap-4 items-center"><img src={certificate.qrUrl} alt="QR code for this certificate verification link" width="96" height="96"/><CertificateActions certificate={certificate}/></div><p className="mt-3 text-xs text-slate-500">This record certifies course completion and passed assessment requirements. It grants no additional independent mastery credit.</p></section><img title="Issued certificate PDF preview" alt="Issued certificate, rendered from the original PDF" src={`/api/v1/certificates/${certificate.certificateId}/preview.png`} className="w-full h-auto border rounded-xl bg-white"/><p className="text-xs text-slate-500">This preview is rendered from the same stored PDF available to download.</p></>}</div></main>;

}

