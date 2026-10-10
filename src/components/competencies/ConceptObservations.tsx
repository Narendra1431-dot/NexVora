export interface ConceptObservation {
  id: string;
  skillId: string;
  name: string;
  score: number;
  attemptId: string;
  assessedAt?: string;
  sampleSize: number;
  errorTags: string[];
}

export function ConceptObservations({ observations, skillId }: { observations: ConceptObservation[]; skillId: string }) {
  const related = observations.filter(item => item.skillId === skillId);
  return <section aria-label="Concept assessment observations" className="space-y-2">
    <h4 className="font-bold text-slate-900">Latest concept observations</h4>
    <p className="text-slate-500">These are question results, not independent verification of an entire concept.</p>
    {related.length === 0 ? <p>No scored concept observations yet. Unassessed topics have no score.</p> : related.map(item => <div key={item.id} className="p-3 border border-slate-200 rounded-lg space-y-1">
      <div className="flex justify-between gap-3"><strong>{item.name}</strong><span>{item.score}%</span></div>
      <p>{item.sampleSize} scored {item.sampleSize === 1 ? 'question' : 'questions'} in the latest attempt.</p>
      {item.errorTags.length > 0 && <p className="text-amber-800">Review needed: {item.errorTags.map(tag=>tag.replaceAll('_',' ')).join(', ')}.</p>}
      <p className="text-slate-500">Assessed: {item.assessedAt || 'Date unavailable'}</p>
    </div>)}
  </section>;
}
