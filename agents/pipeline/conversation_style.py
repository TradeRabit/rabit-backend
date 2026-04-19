"""Conversation style helpers for agent responses."""
from typing import Final


CONVERSATION_STYLE_NORMAL: Final[str] = "normal"
CONVERSATION_STYLE_LEARNING: Final[str] = "learning"
CONVERSATION_STYLE_CONCISE: Final[str] = "concise"
CONVERSATION_STYLE_EXPLANATORY: Final[str] = "explanatory"
CONVERSATION_STYLE_FORMAL: Final[str] = "formal"

VALID_CONVERSATION_STYLES: Final[set[str]] = {
    CONVERSATION_STYLE_NORMAL,
    CONVERSATION_STYLE_LEARNING,
    CONVERSATION_STYLE_CONCISE,
    CONVERSATION_STYLE_EXPLANATORY,
    CONVERSATION_STYLE_FORMAL,
}


def normalize_conversation_style(value: str | None) -> str:
    """Normalize a frontend style value to a supported style."""
    normalized = str(value or CONVERSATION_STYLE_NORMAL).strip().lower()
    if normalized in VALID_CONVERSATION_STYLES:
        return normalized
    return CONVERSATION_STYLE_NORMAL


def get_conversation_style_guidance(style: str) -> str:
    """Return system-prompt guidance for the selected style."""
    normalized = normalize_conversation_style(style)
    mapping = {
        CONVERSATION_STYLE_NORMAL: (
            "Use a balanced conversational style: clear, direct, and helpful without "
            "being overly short or overly verbose."
        ),
        CONVERSATION_STYLE_LEARNING: (
            "Use a teaching-oriented style. Explain the reasoning, define important "
            "terms simply, and help the user learn while solving the task."
        ),
        CONVERSATION_STYLE_CONCISE: (
            "Use a concise style. Keep the answer compact, high-signal, and minimally "
            "wordy unless a detail is essential."
        ),
        CONVERSATION_STYLE_EXPLANATORY: (
            "Use an explanatory style. Expand the reasoning, provide context, and walk "
            "through the logic more explicitly than usual."
        ),
        CONVERSATION_STYLE_FORMAL: (
            "Use a formal professional style. Be polished, structured, and restrained, "
            "while still staying readable and practical."
        ),
    }
    return mapping[normalized]
