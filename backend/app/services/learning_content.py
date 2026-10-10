"""Reject structurally incomplete content before exposing it as a study chapter."""
import json


def valid_chapter(notes, concepts):
    if not isinstance(notes, dict):
        return False
    for key in ('introduction', 'foundations', 'summary', 'source', 'version'):
        if not isinstance(notes.get(key), str) or not notes[key].strip():
            return False
    required = {
        'concepts': (1, ('title', 'explanation', 'example')),
        'examples': (2, ('title', 'code', 'explanation')),
        'interview': (4, ('question', 'answer')),
        'practice': (6, ('question', 'answer')),
    }
    for key, (minimum, fields) in required.items():
        items = notes.get(key)
        if not isinstance(items, list) or len(items) < minimum:
            return False
        if any(not isinstance(item, dict) or any(not isinstance(item.get(field), str) or not item[field].strip() for field in fields) for item in items):
            return False
    titles = [item['title'] for item in notes['concepts']]
    steps = notes.get('flow')
    return (len(titles) == len(set(titles)) and set(concepts) <= set(titles)
            and isinstance(steps, list) and len(steps) >= 3
            and all(isinstance(step, str) and step.strip() for step in steps)
            and len(json.dumps(notes).split()) >= 1300)
