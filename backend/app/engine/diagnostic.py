"""Deterministic bank selection based on evidenced mastery and available difficulty."""
def select_bank(bank, nodes):
    levels={'Beginner':20,'Intermediate':55,'Advanced':80}
    candidates=[a for a in bank if a.get('skillId') in nodes]
    if not candidates: return None
    return min(candidates,key=lambda a:(abs(levels.get(a.get('difficulty'),50)-nodes[a['skillId']].mastery),nodes[a['skillId']].mastery,a['id']))
