import {useEffect,useRef,useState} from 'react';
type Recognition={lang:string;continuous:boolean;interimResults:boolean;onresult:((event:{results:ArrayLike<ArrayLike<{transcript:string}>>})=>void)|null;onerror:((event:{error:string})=>void)|null;onend:(()=>void)|null;start:()=>void;abort:()=>void};
type SpeechWindow=Window & {SpeechRecognition?:new()=>Recognition;webkitSpeechRecognition?:new()=>Recognition};

export function useVoice(onTranscript:(text:string)=>void){
 const [listening,setListening]=useState(false),[speaking,setSpeaking]=useState(false),[error,setError]=useState('');
 const active=useRef<Recognition|null>(null),callback=useRef(onTranscript);callback.current=onTranscript;
 const Constructor=(window as SpeechWindow).SpeechRecognition||(window as SpeechWindow).webkitSpeechRecognition;
 const canSpeak='speechSynthesis' in window;
 const stop=()=>{active.current?.abort();active.current=null;setListening(false);if(canSpeak)window.speechSynthesis.cancel();setSpeaking(false);};
 useEffect(()=>()=>{active.current?.abort();if(canSpeak)window.speechSynthesis.cancel();},[canSpeak]);
 const listen=()=>{
  if(!Constructor){setError('Speech input is unavailable in this browser. You can still type.');return;}
  stop();setError('');const recognition=new Constructor();active.current=recognition;
  recognition.lang='en-US';recognition.continuous=false;recognition.interimResults=false;
  recognition.onresult=event=>callback.current(Array.from(event.results).map(r=>r[0].transcript).join(' ').slice(0,3000));
  recognition.onerror=event=>{setListening(false);setError(event.error==='not-allowed'?'Microphone permission was denied. Type your question or enable it in browser settings.':'Speech recognition failed. Please type or try again.');};
  recognition.onend=()=>{setListening(false);active.current=null;};
  try{recognition.start();setListening(true);}catch{setError('Microphone could not start. You can still type.');}
 };
 const speak=(text:string)=>{if(!canSpeak)return;stop();setError('');const utterance=new SpeechSynthesisUtterance(text);utterance.lang='en-US';utterance.onend=()=>setSpeaking(false);utterance.onerror=()=>{setSpeaking(false);setError('Read aloud unavailable. The answer remains visible.');};setSpeaking(true);window.speechSynthesis.speak(utterance);};
 return {listening,speaking,error,listen,speak,stop,canListen:!!Constructor,canSpeak};
}
