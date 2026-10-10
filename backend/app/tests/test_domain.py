import pytest
from app.engine.competency import evidence_signal, score_attempt, CompetencyNode, compute_competencies
from app.security import hash_password, verify_password
from app.ml.inference.ranker import predict

def test_passwords():
    hashed=hash_password('correct-password')
    assert 'correct-password' not in hashed
    assert verify_password('correct-password',hashed)
    assert not verify_password('wrong-password',hashed)
    assert not verify_password('password','hashed:password:fakehash8')

def test_zero_score_cannot_verify():
    result=evidence_signal([{'type':'Assessment','quality':'High','confidenceScore':0,'verificationState':'Needs Review'}])
    assert result['mastery']==0 and not result['verified']

def test_claim_cannot_verify():
    result=evidence_signal([{'type':'Resume Claim','quality':'High','confidenceScore':100,'verificationState':'Verified'}])
    assert result['mastery']<80 and not result['verified']

def test_project_requires_verification():
    result=evidence_signal([{'type':'Project','quality':'High','confidenceScore':95,'verificationState':'Needs Review'}])
    assert result['mastery']<=60 and not result['verified']

def test_multiselect_and_malformed():
    q=[{'id':'q','correctAnswers':[0,2]}]
    assert score_attempt(q,{'q':0})['accuracy']==0
    assert score_attempt(q,{'q':[0,2]})['accuracy']==100
    assert score_attempt(q,{'q':['garbage']})['accuracy']==0

def test_prerequisite_order_independence():
    evidence={'a':[{'type':'Assessment','confidenceScore':100,'verificationState':'Verified','quality':'High'}]}
    a=CompetencyNode('a','A','Math & Foundations')
    b=CompetencyNode('b','B','Math & Foundations',prerequisites=['a'])
    forward=compute_competencies([a,b],evidence)
    reverse=compute_competencies([b,a],evidence)
    assert {n['id']:n['state'] for n in forward}=={n['id']:n['state'] for n in reverse}

def test_ml_inference():
    assert 0<=predict([.5]*5)<=1
    assert predict([.8,1,.9,1,1])>predict([.1,.1,.1,.1,.1])
    with pytest.raises(ValueError): predict([float('nan')]*5)
