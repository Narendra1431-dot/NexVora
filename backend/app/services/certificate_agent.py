"""Presentation-only certificate agent. No grading, payments or eligibility tools."""
def prepare(context: dict, tier: str) -> dict:
    # Allow-listed, deterministic output: never accepts student-authored achievement text.
    return {
        'templateVersion': 'nexvora-premium-locked-v1' if tier == 'premium' else 'nexvora-free-v1',
        'achievementDescription': 'Completed the recorded course requirements and passed the required platform assessment.',
        'issuer': 'NexVora Learning Platform',
        'skills': context['skills'],
        'agentVersion': 'certificate-presenter-v1',
    }
