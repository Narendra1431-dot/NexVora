import copy,json
from app.services.mentor_context import bounded_context,bounded_history

def test_projection_is_bounded_and_keeps_relevant_scores_without_mutation():
    context={'skills':[{'id':str(i),'name':'Python' if i==39 else 'Other '+str(i),'mastery':0,'description':'x'*20000} for i in range(40)],'evidence':[],'readiness':19}
    original=copy.deepcopy(context)
    blocks=bounded_context(context,[{'documentId':'kb-test','text':'x'*10000}],'Explain Python')
    assert len(json.dumps(blocks[0],ensure_ascii=False))<=7000
    assert blocks[0]['skills'][0]['name']=='Python'
    assert blocks[0]['skills'][0]['mastery']==0
    assert context==original
    assert len(blocks[1])<850

def test_history_retains_recent_order_with_a_text_budget():
    result=bounded_history([{'role':'user','content':str(i)+'x'*2000} for i in range(20)])
    assert sum(len(m['content']) for m in result)<=4000
    assert result[-1]['content'].startswith('19')
