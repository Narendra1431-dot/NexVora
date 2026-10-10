"""Reproducible advisory models trained solely on synthetic demonstration labels."""
import json
import numpy as np
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.metrics import precision_score, recall_score, f1_score, mean_absolute_error, mean_squared_error
from sklearn.model_selection import train_test_split
from .train import ROOT

EVIDENCE_FEATURES = ['score', 'quality', 'provenancePresent', 'careerRelevant', 'recency']
RISK_FEATURES = ['mastery', 'gap', 'engagement', 'evidenceStrength', 'weeklyTimeFit']

def fit(name, features, x, y, classification=False):
    stratify = y if classification else None
    xt, xe, yt, ye = train_test_split(x,y,test_size=.2,random_state=42,stratify=stratify)
    xt, xv, yt, yv = train_test_split(xt,yt,test_size=.25,random_state=42,stratify=yt if classification else None)
    candidates = [LogisticRegression(C=c,random_state=42,max_iter=1000).fit(xt,yt) for c in [.1,1,10]] if classification else [Ridge(alpha=a).fit(xt,yt) for a in [.1,1,10]]
    model = max(candidates,key=lambda m:f1_score(yv,m.predict(xv),average='macro')) if classification else min(candidates,key=lambda m:mean_absolute_error(yv,m.predict(xv)))
    pred = model.predict(xe)
    metadata = {'modelVersion':name+'-synthetic-1','data':'SYNTHETIC DEMO DATA; advisory only; not validated on learner outcomes','seed':42,'train':len(yt),'validation':len(yv),'test':len(ye),'features':features,'task':'classification' if classification else 'regression'}
    if classification:
        metrics={'precisionMacro':precision_score(ye,pred,average='macro',zero_division=0),'recallMacro':recall_score(ye,pred,average='macro',zero_division=0),'f1Macro':f1_score(ye,pred,average='macro'),'validationF1Macro':f1_score(yv,model.predict(xv),average='macro')}
        weights={'classes':model.classes_.tolist(),'coefficients':model.coef_.tolist(),'intercept':model.intercept_.tolist()}
    else:
        metrics={'testMAE':mean_absolute_error(ye,pred),'testRMSE':float(np.sqrt(mean_squared_error(ye,pred))),'validationMAE':mean_absolute_error(yv,model.predict(xv)),'constantBaselineMAE':mean_absolute_error(ye,np.full(len(ye),yt.mean()))}
        weights={'coefficients':model.coef_.tolist(),'intercept':float(model.intercept_)}
    for folder in ['models','evaluation','data']: (ROOT/folder).mkdir(exist_ok=True)
    (ROOT/f'models/{name}.json').write_text(json.dumps({**metadata,**weights},indent=2))
    (ROOT/f'evaluation/{name}.json').write_text(json.dumps({**metadata,**metrics},indent=2))
    np.savetxt(ROOT/f'data/{name}.csv',np.column_stack([x,y]),delimiter=',',header=','.join(features+['synthetic_label']),comments='')
    return {**metadata,**metrics}

def train():
    rng=np.random.default_rng(42)
    evidence=rng.uniform(0,1,(2400,5))
    evidence[:,2:4]=rng.integers(0,2,(2400,2))
    relevance=evidence@np.array([.3,.2,.25,.15,.1])+rng.normal(0,.025,2400)
    labels=np.digitize(relevance,[.4,.65])
    risk=rng.uniform(0,1,(2400,5))
    risk_labels=np.clip(.65+risk@np.array([-.2,.35,-.25,-.2,-.15])+rng.normal(0,.03,2400),0,1)
    reports=[fit('evidence-strength',EVIDENCE_FEATURES,evidence,labels,True),fit('learning-risk',RISK_FEATURES,risk,risk_labels)]
    print(json.dumps(reports))
if __name__=='__main__': train()
