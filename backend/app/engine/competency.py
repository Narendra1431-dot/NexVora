"""The canonical competency engine.

This module is the single source of truth for a student's skill state and for
every derived score in the product (mastery, gaps, roadmap state, readiness).

Design rules enforced here:

* **Claims are never verified skills.** A resume claim or manual claim can only
  produce ``Unverified Claim`` / ``Estimated`` — never ``Verified``.
* **The LLM never writes these numbers.** Only deterministic functions below
  change mastery, confidence or readiness.
* Skill state is *derived*, never stored as an independent field, so the graph,
  career gaps and roadmap can never disagree with each other.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Optional

# --------------------------------------------------------------------------
# Vocabulary
# --------------------------------------------------------------------------
NODE_STATES = (
    "Verified",
    "Estimated",
    "In Progress",
    "Skill Gap",
    "Prerequisite Gap",
    "Unverified Claim",
)

EVIDENCE_TYPES = (
    "Resume Claim",
    "Course Record",
    "Certificate",
    "GitHub Artifact",
    "Assessment",
    "Coding Challenge",
    "Project",
    "Manual Claim",
    "Mentor Review",
)

# Evidence weight = how much a proof type is trusted, and how far it can push
# mastery on its own. A resume claim can never verify a skill.
EVIDENCE_PROFILE: dict[str, dict[str, Any]] = {
    "Course Record": {"weight": 0.90, "mastery": 78, "confidence": 90, "verifies": False},
    "Certificate": {"weight": 0.70, "mastery": 72, "confidence": 80, "verifies": False},
    "GitHub Artifact": {"weight": 0.85, "mastery": 82, "confidence": 88, "verifies": True},
    "Assessment": {"weight": 0.95, "mastery": 84, "confidence": 92, "verifies": True},
    "Coding Challenge": {"weight": 0.80, "mastery": 80, "confidence": 86, "verifies": True},
    "Project": {"weight": 1.00, "mastery": 88, "confidence": 95, "verifies": True},
    "Manual Claim": {"weight": 0.15, "mastery": 45, "confidence": 35, "verifies": False},
    "Resume Claim": {"weight": 0.18, "mastery": 48, "confidence": 38, "verifies": False},
    "Mentor Review": {"weight": 0.35, "mastery": 55, "confidence": 50, "verifies": False},
}

VERIFICATION_STATES = ("Verified", "Estimated", "Needs Review", "Unverified")

MASTERY_VERIFIED_THRESHOLD = 80
MASTERY_IN_PROGRESS_THRESHOLD = 60
PREREQUISITE_SATISFIED = 75


# --------------------------------------------------------------------------
# Node model
# --------------------------------------------------------------------------
@dataclass
class CompetencyNode:
    id: str
    name: str
    domain: str
    type: str = "Skill"
    mastery: int = 0
    confidence: int = 0
    targetLevel: int = 85
    careerImportance: str = "Medium"
    evidenceCount: int = 0
    lastAssessed: Optional[str] = None
    lastAssessedAt: Optional[str] = None
    prerequisites: list[str] = field(default_factory=list)
    dependents: list[str] = field(default_factory=list)
    relatedConcepts: list[str] = field(default_factory=list)
    remainingGap: str = ""
    recommendedAction: str = ""
    history: list[dict[str, Any]] = field(default_factory=list)
    x: int = 0
    y: int = 0
    careerRequired: bool = False

    # --- persistence -----------------------------------------------------
    @classmethod
    def from_doc(cls, doc: dict[str, Any]) -> "CompetencyNode":
        known = {f for f in cls.__dataclass_fields__}  # type: ignore[attr-defined]
        payload = {k: v for k, v in doc.items() if k in known and k != "state"}
        node = cls(**payload)
        node.mastery = int(max(0, min(100, node.mastery)))
        node.confidence = int(max(0, min(100, node.confidence)))
        return node

    def to_doc(self) -> dict[str, Any]:
        data = self.__dict__.copy()
        return data


@dataclass
class EngineResult:
    """Everything the API needs to answer a state-changing request."""

    nodes: list[CompetencyNode]
    competencies: list[dict[str, Any]]
    readiness: int
    previous_readiness: int
    mission: dict[str, Any] = field(default_factory=dict)
    events: list[dict[str, Any]] = field(default_factory=list)
    notifications: list[dict[str, Any]] = field(default_factory=list)
    evidence: list[dict[str, Any]] = field(default_factory=list)
    attempts: list[dict[str, Any]] = field(default_factory=list)
    resume: dict[str, Any] = field(default_factory=dict)
    projects: list[dict[str, Any]] = field(default_factory=list)
    milestones: list[dict[str, Any]] = field(default_factory=list)
    unlock_code: str = "ok"
    allowed: bool = True
    message: str = ""


# --------------------------------------------------------------------------
# Prerequisite propagation
# --------------------------------------------------------------------------
def _prereq_map(nodes: Iterable[CompetencyNode]) -> dict[str, CompetencyNode]:
    return {node.id: node for node in nodes}


def unmet_prerequisites(node: CompetencyNode, index: dict[str, CompetencyNode]) -> list[str]:
    """Prerequisite ids that are below the mastery bar (recursively unresolved)."""
    unmet: list[str] = []
    for prereq_id in node.prerequisites:
        prereq = index.get(prereq_id)
        if prereq is None:
            continue
        if prereq.mastery < PREREQUISITE_SATISFIED:
            unmet.append(prereq_id)
    return unmet


def prerequisite_chain(node: CompetencyNode, index: dict[str, CompetencyNode]) -> list[str]:
    """Full transitive chain of unmet prerequisites (for explanation text)."""
    seen: set[str] = set()
    ordered: list[str] = []
    stack = list(unmet_prerequisites(node, index))
    while stack:
        current = stack.pop(0)
        if current in seen:
            continue
        seen.add(current)
        ordered.append(current)
        parent = index.get(current)
        if parent is not None:
            stack.extend(unmet_prerequisites(parent, index))
    return ordered


# --------------------------------------------------------------------------
# Evidence aggregation
# --------------------------------------------------------------------------
def evidence_signal(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate a skill's evidence into (mastery, confidence, count, state)."""
    records = [r for r in records if not r.get("superseded")]
    if not records:
        return {"mastery": 0, "confidence": 0, "count": 0, "verified": False, "top_quality": "None", "claim_only": False}

    weighted_mastery = 0.0
    weighted_confidence = 0.0
    total_weight = 0.0
    has_verifier = False
    verified_count = 0

    for record in records:
        profile = EVIDENCE_PROFILE.get(record.get("type", "Manual Claim"), EVIDENCE_PROFILE["Manual Claim"])
        quality_factor = {"High": 1.0, "Medium": 0.8, "Low": 0.55}.get(record.get("quality", "Medium"), 0.8)
        score = float(record.get("confidenceScore", profile["confidence"]))

        weight = profile["weight"] * quality_factor
        verified = profile["verifies"] and record.get("verificationState") == "Verified"
        mastery = score if record.get("type") in {"Assessment", "Coding Challenge", "Project"} else min(score, profile["mastery"])
        if not verified and profile["verifies"]:
            mastery = min(mastery, 60)
        weighted_mastery += mastery * weight
        weighted_confidence += score * weight
        total_weight += weight

        if verified:
            has_verifier = True
        if verified:
            verified_count += 1

    mastery = weighted_mastery / total_weight if total_weight else 0.0
    confidence = weighted_confidence / total_weight if total_weight else 0.0
    if has_verifier:
        confidence += 4  # corroborated proof
    if verified_count >= 2:
        confidence += 4

    return {
        "mastery": int(round(max(0.0, min(100.0, mastery)))),
        "confidence": int(round(max(0.0, min(100.0, confidence)))),
        "count": len(records),
        "verified": has_verifier,
        "verified_count": verified_count,
        "claim_only": all(r.get("type") in {"Resume Claim", "Manual Claim"} for r in records),
    }


# --------------------------------------------------------------------------
# Derived state
# --------------------------------------------------------------------------
def derive_state(node: CompetencyNode, index: dict[str, CompetencyNode], signal: dict[str, Any]) -> str:
    """The single rule table that produces a node's canonical state."""
    unmet = unmet_prerequisites(node, index)

    if signal["count"] == 0:
        # No evidence at all: a target we still have to reach.
        return "Prerequisite Gap" if unmet else "Skill Gap"

    if signal["claim_only"]:
        # Claims never become verified skills, no matter how confident they sound.
        return "Unverified Claim"

    if unmet and node.mastery < node.targetLevel:
        return "Prerequisite Gap"

    if signal.get("verified") and node.mastery >= MASTERY_VERIFIED_THRESHOLD:
        return "Verified"

    if node.mastery >= MASTERY_VERIFIED_THRESHOLD and not signal.get("verified"):
        # Strong claim or partial proof without a verifier: estimated, not proven.
        return "Estimated"

    if node.mastery >= MASTERY_IN_PROGRESS_THRESHOLD:
        return "In Progress"

    if node.mastery > 0:
        return "In Progress"

    return "Prerequisite Gap" if unmet else "Skill Gap"


def priority_weight(node: CompetencyNode, required: Optional[int]) -> float:
    """How much a skill matters for the target role."""
    importance = {"Required": 1.0, "Preferred": 0.65, "Bonus": 0.35}.get(node.careerImportance, 0.5)
    if node.careerImportance == "Critical":
        importance = 1.0
    target = required if required is not None else node.targetLevel
    deficiency = max(0, target - node.mastery)
    return importance * (deficiency / 100.0)


def knowledge_debt(node: CompetencyNode, signal: dict[str, Any]) -> float:
    """Decay risk: strong mastery we have not re-verified recently."""
    if node.mastery < MASTERY_IN_PROGRESS_THRESHOLD:
        return 0.0
    recency_penalty = 0.35 if node.lastAssessedAt is None else 0.0
    if node.lastAssessedAt:
        from ..security import relative_label  # local import avoids a cycle at module load

        label = relative_label(node.lastAssessedAt)
        if "month" in label or label == "Never":
            recency_penalty = 0.35
        elif "days ago" in label:
            try:
                days = int(label.split()[0])
                recency_penalty = 0.25 if days >= 30 else (0.12 if days >= 14 else 0.0)
            except ValueError:
                recency_penalty = 0.0
    return round(min(1.0, recency_penalty + (0.1 if signal["claim_only"] else 0.0)), 3)


def compute_competencies(
    nodes: list[CompetencyNode],
    evidence_by_skill: dict[str, list[dict[str, Any]]],
    requirement_by_skill: Optional[dict[str, int]] = None,
    *,
    requirement_importance: Optional[dict[str, str]] = None,
) -> list[dict[str, Any]]:
    """Project canonical nodes into the API/UI competency shape."""
    requirement_by_skill = requirement_by_skill or {}
    requirement_importance = requirement_importance or {}
    index = _prereq_map(nodes)
    output: list[dict[str, Any]] = []

    # Resolve all evidence signals before traversing prerequisites (order independent).
    for node in nodes:
        signal = evidence_signal(evidence_by_skill.get(node.id, []))
        node.mastery, node.confidence = signal["mastery"], signal["confidence"]
    for node in nodes:
        records = evidence_by_skill.get(node.id, [])
        signal = evidence_signal(records)
        node.evidenceCount = signal["count"]

        required = requirement_by_skill.get(node.id)
        node.careerRequired = required is not None
        if required is not None:
            node.targetLevel = required
        if requirement_importance.get(node.id):
            node.careerImportance = requirement_importance[node.id]

        # Mastery is evidence-derived: manual edits never bypass this line.
        node.mastery = signal["mastery"]
        node.confidence = signal["confidence"]

        state = derive_state(node, index, signal)
        unmet = unmet_prerequisites(node, index)
        chain = prerequisite_chain(node, index)

        if state == "Verified":
            gap_text = (
                "No blocking gap detected; periodically re-verify to prevent knowledge decay."
                if node.mastery >= node.targetLevel
                else f"Verified at {node.mastery}% but role target is {node.targetLevel}%."
            )
            action = "Maintain with periodic re-verification and stretch practice."
        elif state == "Prerequisite Gap":
            names = [index[i].name for i in chain[:2] if i in index]
            gap_text = f"Blocked by prerequisite{'s' if len(names) != 1 else ''}: {', '.join(names)}."
            action = f"Close {names[0] if names else 'prerequisite'} first to unlock this skill."
        elif state == "Unverified Claim":
            gap_text = (
                f"Claimed on {records[0].get('type', 'evidence')} but no verifier artifact exists yet."
            )
            action = "Produce an assessment score or a rubric-verified project to verify this claim."
        elif state == "Skill Gap":
            gap_text = f"Required mastery is {node.targetLevel}%; current evidence places you at {node.mastery}%."
            action = "Work the linked milestone, then assess to convert learning into proof."
        elif state == "Estimated":
            gap_text = f"Estimated at {node.mastery}% without a verifier artifact."
            action = "Convert the estimate into verified mastery with an assessment."
        else:
            gap_text = f"In progress at {node.mastery}% against a {node.targetLevel}% target."
            action = "Continue practice tasks, then run the linked assessment."

        output.append(
            {
                "id": node.id,
                "name": node.name,
                "domain": node.domain,
                "type": node.type,
                "state": state,
                "mastery": node.mastery,
                "confidence": node.confidence,
                "targetLevel": node.targetLevel,
                "careerImportance": node.careerImportance,
                "careerRequired": node.careerRequired,
                "evidenceCount": node.evidenceCount,
                "lastAssessed": node.lastAssessed or "Never",
                "lastAssessedAt": node.lastAssessedAt,
                "prerequisites": list(node.prerequisites),
                "unmetPrerequisites": unmet,
                "prerequisiteChain": chain,
                "dependents": list(node.dependents),
                "relatedConcepts": list(node.relatedConcepts),
                "remainingGap": gap_text,
                "recommendedAction": action,
                "history": list(node.history)[-12:],
                "knowledgeDebt": knowledge_debt(node, signal),
                "priority": round(priority_weight(node, required), 4),
                "x": node.x,
                "y": node.y,
                "updatedAt": node.lastAssessedAt,
            }
        )

    output.sort(key=lambda item: (-item["priority"], item["name"]))
    return output


# --------------------------------------------------------------------------
# Career gap analysis
# --------------------------------------------------------------------------
def analyse_career(
    nodes: list[CompetencyNode],
    requirements: list[dict[str, Any]],
    evidence_by_skill: dict[str, list[dict[str, Any]]],
) -> dict[str, Any]:
    """Direct / prerequisite / evidence gaps, knowledge debt and readiness.

    Readiness is a weighted coverage score: it is fully deterministic and cannot
    be nudged by the LLM or by a "+7%" literal anywhere in the stack.
    """
    index = _prereq_map(nodes)
    importance_weight = {"Required": 1.0, "Preferred": 0.6, "Bonus": 0.3}

    direct: list[dict[str, Any]] = []
    prerequisite: list[dict[str, Any]] = []
    evidence_gaps: list[dict[str, Any]] = []
    debt: list[dict[str, Any]] = []

    total_weight = 0.0
    earned = 0.0

    for requirement in requirements:
        node = index.get(requirement["skillId"])
        if node is None:
            continue
        weight = importance_weight.get(requirement.get("importance", "Preferred"), 0.5)
        total_weight += weight

        records = evidence_by_skill.get(node.id, [])
        signal = evidence_signal(records)
        required_mastery = int(requirement.get("requiredMastery", 85))
        node.targetLevel = required_mastery
        node.careerImportance = requirement.get("importance", node.careerImportance)

        # Coverage contributes partially, and full credit needs verification.
        coverage = min(1.0, node.mastery / max(1, required_mastery))
        if not signal.get("verified"):
            # Unverified evidence can never earn full readiness credit.
            coverage = min(0.85, coverage) * 0.9
        earned += weight * coverage

        unmet = unmet_prerequisites(node, index)
        chain = prerequisite_chain(node, index)

        if node.mastery < required_mastery:
            entry = {
                "skillId": node.id,
                "skillName": node.name,
                "domain": node.domain,
                "gapType": "Prerequisite Gap" if unmet else "Direct Gap",
                "currentMastery": node.mastery,
                "requiredMastery": required_mastery,
                "deficit": required_mastery - node.mastery,
                "importance": requirement.get("importance", "Preferred"),
                "category": requirement.get("category", node.domain),
                "whyExplanation": (
                    f"Blocked by {', '.join(index[i].name for i in chain[:2] if i in index)} before this can be verified."
                    if unmet
                    else f"Current verified mastery {node.mastery}% is below the {required_mastery}% requirement."
                ),
                "recommendedAction": (
                    f"Close {index[chain[0]].name} first." if chain and chain[0] in index else f"Work the {node.name} milestone."
                ),
                "priority": "High" if weight >= 1.0 and required_mastery - node.mastery >= 20 else "Medium",
            }
            (prerequisite if unmet else direct).append(entry)

        if not signal.get("verified") and signal["count"] > 0:
            evidence_gaps.append(
                {
                    "skillId": node.id,
                    "skillName": node.name,
                    "gapType": "Evidence Gap",
                    "currentMastery": node.mastery,
                    "requiredMastery": required_mastery,
                    "whyExplanation": (
                        f"Claimed on {records[0].get('type', 'evidence')} with no verifier artifact."
                        if signal.get("claim_only")
                        else f"{signal['count']} artifact(s) exist but none is machine-verifiable."
                    ),
                    "recommendedAction": "Submit an assessment or rubric-verified project for this skill.",
                    "priority": "High" if weight >= 1.0 else "Medium",
                }
            )
        elif signal["count"] == 0:
            evidence_gaps.append(
                {
                    "skillId": node.id,
                    "skillName": node.name,
                    "gapType": "Evidence Gap",
                    "currentMastery": 0,
                    "requiredMastery": required_mastery,
                    "whyExplanation": "No evidence artifact of any kind is linked to this requirement.",
                    "recommendedAction": "Start the milestone and produce the first proof artifact.",
                    "priority": "High",
                }
            )

        debt_score = knowledge_debt(node, signal)
        if debt_score >= 0.2:
            debt.append(
                {
                    "skillId": node.id,
                    "skillName": node.name,
                    "gapType": "Knowledge Debt",
                    "currentMastery": node.mastery,
                    "requiredMastery": required_mastery,
                    "whyExplanation": f"Last assessed {node.lastAssessed or 'never'}; decay risk {int(debt_score * 100)}%.",
                    "recommendedAction": "Schedule a short re-verification assessment.",
                    "priority": "Low" if debt_score < 0.3 else "Medium",
                }
            )

    readiness = int(round((earned / total_weight) * 100)) if total_weight else 0
    compliance = int(round(100 * sum(1 for req in requirements if req["skillId"] in index and index[req["skillId"]].mastery >= req.get("requiredMastery",85)) / max(1,len(requirements))))

    return {
        "readiness": max(0, min(100, readiness)),
        "requirementCoverage": compliance,
        "directGaps": sorted(direct, key=lambda g: -g["deficit"]),
        "prerequisiteGaps": sorted(prerequisite, key=lambda g: -g["deficit"]),
        "evidenceGaps": evidence_gaps,
        "knowledgeDebt": debt,
        "gapCount": len(direct) + len(prerequisite),
        "evidenceGapCount": len(evidence_gaps),
    }


# --------------------------------------------------------------------------
# Mutation: the only ways a competency may change
# --------------------------------------------------------------------------
def apply_evidence(
    node: CompetencyNode,
    record: dict[str, Any],
    *,
    event_label: str,
) -> dict[str, Any]:
    """Record history for a node after new evidence lands (idempotent reporting)."""
    node.history.append(
        {
            "date": record.get("date"),
            "mastery": node.mastery,
            "event": event_label,
        }
    )
    node.history = node.history[-40:]
    return {"skillId": node.id, "mastery": node.mastery, "event": event_label}


def score_attempt(questions: list[dict[str, Any]], answers: dict[str, Any]) -> dict[str, Any]:
    """Grade an attempt server-side. Correct answers never leave the API before submit."""
    correct = 0
    total = len(questions)
    per_question: list[dict[str, Any]] = []

    for question in questions:
        key = str(question.get("id"))
        given = answers.get(key, answers.get(question.get("id"), None))  # type: ignore[arg-type]
        expected = question.get("correctAnswers")
        is_correct = False

        if isinstance(expected, list):
            if isinstance(given, list):
                is_correct = {str(v) for v in given} == {str(v) for v in expected}
            elif given is not None:
                try:
                    is_correct = len(expected) == 1 and int(given) == int(expected[0])
                except (TypeError, ValueError):
                    is_correct = False
        elif isinstance(expected, str):
            is_correct = str(given or "").strip().lower() == expected.strip().lower()

        correct += 1 if is_correct else 0
        per_question.append(
            {
                "questionId": question.get("id"),
                "concept": question.get("topic", ""),
                "errorTags": [] if is_correct else ["incorrect_or_missing_answer"],
                "correct": is_correct,
                "expected": expected,
                "explanation": question.get("explanation", ""),
            }
        )

    accuracy = int(round((correct / total) * 100)) if total else 0
    return {"correct": correct, "total": total, "accuracy": accuracy, "breakdown": per_question}


def practice_credit(previous_mastery: int, target_mastery: int) -> int:
    """Learning a resource nudges mastery but can never verify a skill by itself."""
    ceiling = max(target_mastery - 12, previous_mastery)
    step = 4 if previous_mastery < 50 else 3
    return int(max(previous_mastery, min(ceiling, previous_mastery + step, 76)))
