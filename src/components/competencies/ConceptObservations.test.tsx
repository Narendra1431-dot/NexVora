import { describe, it, expect } from 'vitest';
import { renderToStaticMarkup } from 'react-dom/server';
import { ConceptObservations } from './ConceptObservations';

describe('Concept observations',()=>{
  it('distinguishes unassessed concepts from zero scores',()=>{
    expect(renderToStaticMarkup(<ConceptObservations observations={[]} skillId="s"/>)).toContain('Unassessed topics have no score');
    const html=renderToStaticMarkup(<ConceptObservations skillId="s" observations={[{id:'s:joins',skillId:'s',name:'Joins',score:0,attemptId:'a',sampleSize:2,errorTags:['incorrect_or_missing_answer']}]} />);
    expect(html).toContain('0%');
    expect(html).toContain('2 scored questions');
    expect(html).toContain('incorrect or missing answer');
    expect(html).not.toContain('No scored concept observations yet');
  });
  it('shows only observations for the inspected skill',()=>{
    const html=renderToStaticMarkup(<ConceptObservations skillId="python" observations={[{id:'sql:joins',skillId:'sql',name:'SQL joins',score:100,attemptId:'a',sampleSize:1,errorTags:[]}]} />);
    expect(html).not.toContain('SQL joins');
  });
});
