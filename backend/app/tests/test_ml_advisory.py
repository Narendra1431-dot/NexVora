import copy
import pytest
from app.ml.inference.advisory import predict, summarize

@pytest.mark.parametrize('name',['learning-risk','evidence-strength'])
def test_advisory_rejects_invalid_features(name):
    for values in [[.5]*4,[float('nan')]*5,[-1]*5,[2]*5]:
        with pytest.raises(ValueError): predict(name,values)

def test_advisory_predictions_are_sensitive_and_never_verify():
    assert predict('evidence-strength',[0,0,0,0,0])['label']=='weak'
    assert predict('evidence-strength',[1,1,1,1,1])['label']=='strong'
    assert predict('learning-risk',[0,1,0,0,0])['score'] > predict('learning-risk',[1,0,1,1,1])['score']
    competencies=[{'id':'python','careerRequired':True,'mastery':0,'targetLevel':80}]
    evidence=[{'id':'claim','skillId':'python','score':30,'quality':'Low','verificationState':'Unverified','provenance':{'source':'manual'}}]
    original=copy.deepcopy((competencies,evidence))
    result=summarize(competencies,evidence,{'weeklyAvailabilityHours':5},[])
    assert result['advisoryOnly'] and result['trainingData']=='synthetic_demo'
    assert (competencies,evidence)==original
