"""Confined workspace, adapted from Open Dots (see OPEN_DOTS_LICENSE.txt)."""
import hashlib
import os
import re
from pathlib import Path
from fastapi import HTTPException

def resolve(student_id, name):
    # Flat, generated artifacts only. Reject Windows ADS/devices and secret files.
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,79}\.(txt|md|pdf|json)',name):
        raise HTTPException(422,'Use a simple report filename ending in .txt, .md, .json or .pdf.')
    stem=name.split('.')[0].lower()
    if stem in {'con','prn','aux','nul',*[f'com{i}' for i in range(10)],*[f'lpt{i}' for i in range(10)]} or any(w in stem for w in ('secret','credential','token','password','env','key','auth','config')):
        raise HTTPException(403,'Restricted workspace filename.')
    base=Path(os.getenv('NEXVORA_WORKSPACE',str(Path(__file__).resolve().parents[2]/'data'/'agent-workspaces'))).absolute()
    root=base/hashlib.sha256(student_id.encode()).hexdigest()
    root.mkdir(parents=True,exist_ok=True)
    path=root/name
    for part in [base,root,path]:
        if part.is_symlink() or (hasattr(part,'is_junction') and part.is_junction()):raise HTTPException(403,'Linked workspace paths are prohibited.')
    if path.resolve().parent!=root.resolve():raise HTTPException(403,'Workspace confinement failed.')
    return path

def write(student_id,name,content):
    path=resolve(student_id,name)
    if len(content)>2_000_000:raise HTTPException(413,'Report exceeds workspace size limit.')
    # Never overwrite an existing artifact, including one from an interrupted job.
    try:
        with path.open('xb') as f:f.write(content)
    except FileExistsError:raise HTTPException(409,'This artifact already exists. Choose a new name.')
    return {'fileName':name,'bytes':len(content),'written':True}

def read(student_id,name):
    path=resolve(student_id,name)
    if not path.is_file():raise HTTPException(404,'Workspace artifact not found.')
    if path.stat().st_size>2_000_000:raise HTTPException(413,'Artifact exceeds size limit.')
    return path.read_bytes()
