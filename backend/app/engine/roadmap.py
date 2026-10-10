"""Adaptive roadmap generation.

Milestones are generated from the *current* competency graph and target role, so
the roadmap re-sequences itself whenever evidence changes. States are derived:

* ``Completed``       — the skill reached its band and has verifier evidence,
* ``Active``          — prerequisites satisfied, skill still short of target,
* ``Needs Assessment``— evidence exists but no verifier artefact has scored it,
* ``Locked``          — one or more prerequisites remain unmet,
* ``Blocked``         — prerequisites unmet *and* the deficit is large enough
                        that jumping ahead would create knowledge debt.

Every milestone carries reason, prerequisites, target mastery, resources,
assessment and an explicit completion rule.
"""

from __future__ import annotations

from typing import Any, Optional

from .competency import CompetencyNode

ASSESSMENTS_BY_SKILL: dict[str, str] = {
    "prog-python-advanced": "assess-python-baseline",
    "data-sql-querying": "assess-sql-baseline",
    "dl-pytorch": "assess-pytorch-adaptive",
    "dl-transformers": "assess-transformers-mastery",
    "dl-rag-systems": "assess-rag-systems",
    "data-vector-databases": "assess-vector-databases",
}

# Minimal prerequisite-walk depth used to order the sequence.
_DOMAIN_ORDER = {
    "Math & Foundations": 0,
    "Core Programming": 1,
    "Data Systems": 2,
    "Machine Learning": 3,
    "Deep Learning & NLP": 4,
    "MLOps & Deployment": 5,
}

DEFAULT_COMPLETION_RULE = "Reach the target mastery with at least one verifier artefact (assessment or rubric-verified project)."


def _depth(node: CompetencyNode, index: dict[str, CompetencyNode], seen: Optional[set[str]] = None) -> int:
    seen = seen or set()
    if node.id in seen or not node.prerequisites:
        return 0
    seen.add(node.id)
    return 1 + max(
        (_depth(index[p], index, seen) for p in node.prerequisites if p in index),
        default=0,
    )


def _resources_for(skill_id: str, resources: list[dict[str, Any]]) -> list[str]:
    return [item["id"] for item in resources if item.get("skillId") == skill_id]


def _practice_tasks(node: CompetencyNode, competencies: list[dict[str, Any]]) -> list[str]:
    entry = next((c for c in competencies if c["id"] == node.id), None)
    tasks = [f"Work through: {concept}" for concept in node.relatedConcepts[:3]]
    if entry and entry.get("state") == "Unverified Claim":
        tasks.append("Attach a verifier artefact to your existing claim (repository or rubric submission)")
    if entry and entry.get("state") == "Prerequisite Gap":
        tasks.append("Close the blocking prerequisite milestone before attempting this assessment")
    return tasks or [f"Study and practise {node.name} fundamentals"]


def _duration(target: int, mastery: int, depth: int) -> str:
    deficit = max(0, target - mastery)
    hours = max(3, int(round(deficit / 9)) + depth * 2)
    return f"{hours} hours"


def build_roadmap(
    nodes: list[CompetencyNode],
    competencies: list[dict[str, Any]],
    requirements: list[dict[str, Any]],
    resources: list[dict[str, Any]],
    projects: list[dict[str, Any]],
    skills_by_id: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    """Generate the ordered, prerequisite-aware milestone list."""
    index = {node.id: node for node in nodes}
    entry_by_id = {item["id"]: item for item in competencies}
    requirement_by_skill = {req["skillId"]: req for req in requirements}

    # Only skills that matter for the target role, plus any unmet prerequisite
    # of those skills, enter the roadmap.
    considered: dict[str, CompetencyNode] = {}
    for skill_id in requirement_by_skill:
        node = index.get(skill_id)
        if node is None:
            continue
        considered[node.id] = node
        entry = entry_by_id.get(node.id)
        for prereq_id in (entry or {}).get("prerequisiteChain", []):
            if prereq_id in index:
                considered[prereq_id] = index[prereq_id]

    def sort_key(node: CompetencyNode) -> tuple[int, int, int]:
        depth = _depth(node, index)
        required = requirement_by_skill.get(node.id)
        importance_rank = {"Required": 0, "Preferred": 1, "Bonus": 2}.get(
            (required or {}).get("importance", "Bonus"), 3
        )
        return (depth, importance_rank, _DOMAIN_ORDER.get(node.domain, 9))

    ordered = sorted(considered.values(), key=sort_key)

    milestones: list[dict[str, Any]] = []
    for position, node in enumerate(ordered, start=1):
        entry = entry_by_id.get(node.id, {})
        required = requirement_by_skill.get(node.id, {})
        target = int(required.get("requiredMastery", node.targetLevel or 85))
        mastery = int(entry.get("mastery", node.mastery))
        unmet = [pid for pid in entry.get("unmetPrerequisites", []) if pid in index]
        chain = [pid for pid in entry.get("prerequisiteChain", []) if pid in index]
        state_name = entry.get("state", "Skill Gap")

        blocking_names = [index[pid].name for pid in (unmet or chain)]

        if mastery >= target and entry.get("state") == "Verified":
            milestone_state = "Completed"
            reason = f"Verified at {mastery}% against the {target}% requirement for this target role."
        elif unmet:
            # A deep deficit behind an unmet prerequisite is a Blocked milestone;
            # anything else is merely Locked until the prerequisite clears.
            milestone_state = "Blocked" if (target - mastery) >= 30 else "Locked"
            reason = (
                f"Locked behind {', '.join(blocking_names[:2])}. "
                f"Target is {target}% and the current evidenced level is {mastery}%."
            )
        elif state_name in {"Estimated", "Unverified Claim"}:
            milestone_state = "Needs Assessment"
            reason = (
                f"{state_name} evidence only — the {target}% target cannot be claimed until a "
                "verifier artefact scores this skill."
            )
        elif state_name == "In Progress":
            milestone_state = "Active"
            reason = f"In progress at {mastery}% toward the {target}% requirement."
        else:
            milestone_state = "Active"
            reason = f"Direct gap: {mastery}% evidenced against a {target}% requirement."

        milestone_projects = [
            project["id"]
            for project in projects
            if node.id in project.get("skillsValidated", [])
        ]
        assessment_id = ASSESSMENTS_BY_SKILL.get(node.id)

        completion = DEFAULT_COMPLETION_RULE
        if assessment_id:
            completion = "Pass the linked assessment at 80% or higher, or submit a rubric-verified project."
        elif milestone_projects:
            completion = "Submit the linked project and pass the deterministic rubric threshold."

        milestones.append(
            {
                "id": f"ms-{position:02d}-{node.id}",
                "order": position,
                "title": _title_for(node, milestone_state),
                "skillId": node.id,
                "skillName": node.name,
                "domain": node.domain,
                "state": milestone_state,
                "reason": reason,
                "prerequisites": [index[pid].name for pid in (unmet or chain)] or ["Foundational"],
                "prerequisiteIds": unmet or chain,
                "blockedBy": [index[pid].id for pid in (unmet or chain)],
                "estimatedDuration": _duration(target, mastery, _depth(node, index)),
                "masteryTarget": target,
                "currentMastery": mastery,
                "completionCondition": completion,
                "evidenceGenerated": f"Verified {node.name} artefact in the evidence vault",
                "practiceTasks": _practice_tasks(node, competencies),
                "resourceIds": _resources_for(node.id, resources),
                "assessmentId": assessment_id,
                "projectId": milestone_projects[0] if milestone_projects else None,
                "importance": required.get("importance", "Preferred"),
                "category": required.get("category", node.domain),
            }
        )

    return milestones


def _title_for(node: CompetencyNode, state_name: str) -> str:
    verb = {
        "Completed": "Maintain verified",
        "Needs Assessment": "Verify",
        "Locked": "Prepare for",
        "Blocked": "Remediate before",
    }.get(state_name, "Master")
    return f"{verb} {node.name}"


def summarise(milestones: list[dict[str, Any]]) -> dict[str, int]:
    counts = {"Completed": 0, "Active": 0, "Locked": 0, "Blocked": 0, "Needs Assessment": 0}
    for milestone in milestones:
        counts[milestone["state"]] = counts.get(milestone["state"], 0) + 1
    total = len(milestones) or 1
    counts["percentComplete"] = int(round((counts["Completed"] / total) * 100))
    counts["total"] = len(milestones)
    return counts
