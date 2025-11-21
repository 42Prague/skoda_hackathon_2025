"""Micro-question generator."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

from .models import UserProfile


@dataclass
class MicroQuestion:
    skill: str
    question: str
    answer: str
    remediation: str


QUESTION_LIBRARY = {
    "powerpoint_basics": MicroQuestion(
        skill="powerpoint_basics",
        question="How do you add a custom slide master and apply it across a deck?",
        answer="View > Slide Master, insert/edit master, close master view, apply layout.",
        remediation="Watch 3 min clip on master slides inside S³.",
    ),
    "copilot_assistance": MicroQuestion(
        skill="copilot_assistance",
        question="What prompt should you use to draft a Škoda-branded client recap email?",
        answer="Provide audience, tone, and attach briefing doc; use Škoda template 'Client Recap v2'.",
        remediation="Open Copilot template pack inside Outlook add-in.",
    ),
}


def generate_questions(profile: UserProfile) -> List[MicroQuestion]:
    questions: List[MicroQuestion] = []
    for hole in profile.holes():
        q = QUESTION_LIBRARY.get(
            hole,
            MicroQuestion(
                skill=hole,
                question=f"What is a key workflow step for {hole}?",
                answer="Refer to best-practice guide.",
                remediation="Review personalized chunk playlist.",
            ),
        )
        questions.append(q)
    return questions

