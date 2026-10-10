"""Reproducible demo ranking model. Synthetic labels are not real outcomes."""
import json
from pathlib import Path
import numpy as np
from sklearn.linear_model import Ridge
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, ndcg_score
ROOT = Path(__file__).resolve().parents[1]
FEATURES = ['gap', 'careerImportance', 'difficultyFit', 'quality', 'timeFit']
def train():
    rng = np.random.default_rng(42)
    x = rng.uniform(0, 1, (1500, 5))
    y = np.clip(x @ np.array([.35,.25,.2,.12,.08]) + rng.normal(0,.03,1500),0,1)
    xt, xe, yt, ye = train_test_split(x,y,test_size=.2,random_state=42)
    xt, xv, yt, yv = train_test_split(xt,yt,test_size=.25,random_state=42)
    candidates = [Ridge(alpha=a).fit(xt,yt) for a in [.01,.1,1,10]]
    model = min(candidates, key=lambda m: mean_absolute_error(yv,m.predict(xv)))
    metrics = {'modelVersion':'demo-ranker-1','seed':42,'data':'SYNTHETIC DEMO DATA; no real-world accuracy claim','train':len(yt),'validation':len(yv),'test':len(ye),'validationMAE':mean_absolute_error(yv,model.predict(xv)),'testMAE':mean_absolute_error(ye,model.predict(xe)),'testRMSE':float(np.sqrt(mean_squared_error(ye,model.predict(xe)))),'testNDCGAt5':float(np.mean([ndcg_score([ye[i:i+10]], [model.predict(xe[i:i+10])], k=5) for i in range(0,len(ye),10)])),'constantBaselineMAE':mean_absolute_error(ye,np.full(len(ye),yt.mean()))}
    artifact = {'features':FEATURES,'coefficients':model.coef_.tolist(),'intercept':float(model.intercept_),**metrics}
    (ROOT/'models/ranker.json').write_text(json.dumps(artifact,indent=2))
    (ROOT/'evaluation/metrics.json').write_text(json.dumps(metrics,indent=2))
    np.savetxt(ROOT/'data/synthetic.csv',np.column_stack([x,y]),delimiter=',',header=','.join(FEATURES+['synthetic_relevance']),comments='')
    print(json.dumps(metrics))
if __name__ == '__main__': train()
