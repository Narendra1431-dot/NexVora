import {TargetLearningHub} from './TargetLearningHub';
import {LearningMaterial} from '../intelligence/LearningMaterial';
import { useState, useEffect, useRef } from 'react';
import { useAppState } from '../../lib/state/app-state';
import {
  BookOpen,
  Search,
  CheckCircle2,
  Bookmark,
  Sparkles,
  ExternalLink,
  Clock,
  Star,
  Layers,
  ArrowRight,
  Filter
} from 'lucide-react';
import { LearningResource, ResourceType } from '../../types';

export function ResourceCenter() {
  const {
    resources,
    catalogSelection,
    completeResource,
    toggleBookmarkResource,
    targetCareer,
    setActiveTab,
    setSelectedSkillId
  } = useAppState();

  const [topicResourceIds,setTopicResourceIds]=useState<string[]|null>(null);
  const [searchQuery, setSearchQuery] = useState(catalogSelection?.tab === 'resources' ? resources.find(r=>r.id===catalogSelection.id)?.title || '' : '');
  const [selectedType, setSelectedType] = useState<string>('All');
  const [selectedDifficulty, setSelectedDifficulty] = useState<string>('All');

  const previousCareer=useRef(targetCareer.id);
  useEffect(()=>{if(previousCareer.current!==targetCareer.id){setSearchQuery('');setSelectedType('All');setSelectedDifficulty('All');previousCareer.current=targetCareer.id;}},[targetCareer.id]);

  const filteredResources = resources.filter((res) => {
    if(!topicResourceIds || !topicResourceIds.includes(res.id))return false;
    const matchesSearch =
      res.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      res.skillName.toLowerCase().includes(searchQuery.toLowerCase()) ||
      res.provider.toLowerCase().includes(searchQuery.toLowerCase());

    const matchesType = selectedType === 'All' || res.type === selectedType;
    const matchesDiff = selectedDifficulty === 'All' || res.difficulty === selectedDifficulty;

    return matchesSearch && matchesType && matchesDiff;
  });

  const handleInspectSkill = (skillId: string) => {
    setSelectedSkillId(skillId);
    setActiveTab('competencies');
  };

  return (
    <div className="space-y-6 pb-12">
      <TargetLearningHub onCoverage={setTopicResourceIds}/>
      <LearningMaterial />
      <h3 className="text-base font-bold text-slate-900">Mapped Courses, Documentation & Practice</h3>
      {/* Search & Filter Toolbar */}
      <div className="bg-white p-4 rounded-2xl border border-slate-200/80 shadow-2xs flex flex-col sm:flex-row items-stretch sm:items-center gap-3">
        <div className="relative flex-1">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search papers, docs, labs, courses, or specific skills..."
            className="w-full pl-9 pr-4 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs outline-hidden focus:border-teal-500 text-slate-900"
          />
        </div>

        <div className="flex items-center gap-2">
          <select
            value={selectedType}
            onChange={(e) => setSelectedType(e.target.value)}
            className="px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs font-medium text-slate-700 outline-hidden"
          >
            <option value="All">All Formats</option>
            <option value="Video">Videos</option>
            <option value="Article">Research Papers & Articles</option>
            <option value="Documentation">Official Docs</option>
            <option value="Course">Full Courses</option>
            <option value="Practice">Interactive Practice</option>
            <option value="Lab">Hands-on Labs</option>
          </select>

          <select
            value={selectedDifficulty}
            onChange={(e) => setSelectedDifficulty(e.target.value)}
            className="px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs font-medium text-slate-700 outline-hidden"
          >
            <option value="All">All Levels</option>
            <option value="Beginner">Beginner</option>
            <option value="Intermediate">Intermediate</option>
            <option value="Advanced">Advanced</option>
          </select>
        </div>
      </div>

      {topicResourceIds && !filteredResources.length && <div className="flex items-center gap-3 rounded-xl border border-slate-200 bg-white p-5"><p className="text-sm text-slate-600">No resources match these filters. Try another format, level or search term.</p></div>}
      {/* Resource Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filteredResources.map((item) => {
          const isCompleted = item.completed;
          const isBookmarked = item.bookmarked;

          return (
            <div
              key={item.id}
              className={`rounded-2xl border p-5 interactive-card flex flex-col justify-between shadow-2xs ${
                isCompleted
                  ? 'bg-emerald-50/20 border-emerald-200'
                  : 'bg-white border-slate-200/80 hover:shadow-md'
              }`}
            >
              <div>
                
                {/* Meta header */}
                <div className="flex items-center justify-between gap-2 mb-2">
                  <div className="flex items-center gap-1.5">
                    <span className="text-[10px] font-bold bg-slate-100 text-slate-700 px-2 py-0.5 rounded">
                      {item.type}
                    </span>
                    <span className="text-[10px] font-semibold text-slate-500">
                      {item.difficulty}
                    </span>
                  </div>

                  <div className="flex items-center gap-1">
                    <button
                      aria-label={(isBookmarked ? "Remove bookmark: " : "Bookmark: ")+item.title}
                      onClick={() => toggleBookmarkResource(item.id)}
                      className={`p-1 rounded-lg transition cursor-pointer ${
                        isBookmarked
                          ? 'text-teal-600 bg-teal-50'
                          : 'text-slate-400 hover:text-slate-600'
                      }`}
                    >
                      <Bookmark className="w-3.5 h-3.5" fill={isBookmarked ? 'currentColor' : 'none'} />
                    </button>
                    <div className="flex items-center gap-0.5 text-[11px] font-bold text-amber-600 bg-amber-50 px-1.5 py-0.5 rounded">
                      <Star className="w-3 h-3 fill-current" />
                      <span>{item.qualityRating}</span>
                    </div>
                  </div>
                </div>

                {/* Title and Provider */}
                <h4 className="text-xs font-bold text-slate-900 leading-snug">
                  {item.title}
                </h4>
                <div className="text-[11px] text-slate-500 mt-1 flex items-center justify-between">
                  <span>{item.provider}</span>
                  <span className="flex items-center gap-1">
                    <Clock className="w-3 h-3 text-slate-400" />
                    <span>{item.duration}</span>
                  </span>
                </div>

                {/* Why recommended rationale */}
                <div className="mt-3 p-2.5 bg-teal-50/50 border border-teal-100 rounded-xl space-y-1 text-[11px]">
                  <div className="flex items-center gap-1 text-teal-800 font-bold text-[10px] uppercase tracking-wide">
                    <Sparkles className="w-3 h-3 text-teal-600" />
                    <span>Target Gap Rationale</span>
                  </div>
                  <p className="text-slate-700 leading-relaxed">
                    {item.reasonRecommended}
                  </p>
                </div>
              </div>

              {item.type==='Course' && <button onClick={()=>setActiveTab('certificates')} className="mt-3 text-left text-xs font-semibold text-teal-700 hover:underline">Check certificate eligibility</button>}
              {/* Action footer */}
              <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between gap-2">
                <button
                  type="button"
                  onClick={() => handleInspectSkill(item.skillId)}
                  className="text-[11px] font-semibold text-teal-700 hover:underline cursor-pointer"
                >
                  Skill: {item.skillName}
                </button>

                <div className="flex items-center gap-2">
                  <button
                    onClick={() => completeResource(item.id)}
                    className={`px-2.5 py-1 rounded-lg text-xs font-semibold transition cursor-pointer flex items-center gap-1 ${
                      isCompleted
                        ? 'bg-emerald-100 text-emerald-800'
                        : 'bg-slate-100 hover:bg-slate-200 text-slate-700'
                    }`}
                  >
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    <span>{isCompleted ? 'Finished' : 'Mark Done'}</span>
                  </button>

                  <a
                    aria-label={"Open resource: "+item.title}
                    href={item.url}
                    target="_blank"
                    rel="noreferrer"
                    className="p-1 text-slate-400 hover:text-slate-700 transition"
                  >
                    <ExternalLink className="w-3.5 h-3.5" />
                  </a>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
