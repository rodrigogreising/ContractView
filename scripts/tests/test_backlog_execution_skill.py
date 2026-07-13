"""Executable contract for the reusable Linear backlog skill."""

from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SKILL = ROOT / ".agents/skills/cv-execute-linear-backlog/SKILL.md"
METADATA = ROOT / ".agents/skills/cv-execute-linear-backlog/agents/openai.yaml"


@dataclass(frozen=True)
class Story:
    identifier: str
    scope: str
    blocker_severity: int
    priority: int
    dependency_depth: int
    created_order: int
    prerequisites_verified: bool


def select_story(stories: list[Story], scope: str) -> Story | None:
    eligible = [
        story
        for story in stories
        if story.scope == scope and story.prerequisites_verified
    ]
    if not eligible:
        return None
    return sorted(
        eligible,
        key=lambda story: (
            -story.blocker_severity,
            story.priority,
            -story.dependency_depth,
            story.created_order,
        ),
    )[0]


def test_skill_has_generic_trigger_and_no_recovery_terminal() -> None:
    content = SKILL.read_text(encoding="utf-8")
    metadata = METADATA.read_text(encoding="utf-8")

    assert "explicitly scoped unfinished ContractView Linear stories" in content
    assert "explicitly scoped unfinished ContractView Linear stories" in metadata
    for legacy_literal in ("SUB-55", "SUB-56", "REC-12", "recovery-first"):
        assert legacy_literal not in content
        assert legacy_literal not in metadata


def test_mvp_epic_scope_selects_first_ready_leaf_and_excludes_other_backlog() -> None:
    stories = [
        Story("SUB-70", "other", 1, 2, 0, 1, True),
        Story("SUB-74", "SUB-73", 0, 2, 4, 2, True),
        Story("SUB-75", "SUB-73", 0, 2, 3, 3, False),
    ]

    selected = select_story(stories, "SUB-73")

    assert selected is not None
    assert selected.identifier == "SUB-74"
    assert selected.identifier != "SUB-70"


def test_single_story_waits_for_merged_and_post_merge_verified_prerequisite() -> None:
    stories = [Story("SUB-75", "SUB-75", 0, 2, 3, 1, False)]

    assert select_story(stories, "SUB-75") is None
    assert "post-merge evidence is recorded" in SKILL.read_text(encoding="utf-8")


def test_dirty_worktree_stops_before_mutation() -> None:
    content = SKILL.read_text(encoding="utf-8")

    assert "Stop before mutation for unrelated user changes" in content


def test_review_requires_immutable_diff_manifest_and_clean_worktree() -> None:
    content = SKILL.read_text(encoding="utf-8")

    assert "immutable remote base/head diff with a clean worktree" in content
    assert "docs/sdlc/evidence-manifest.schema.json" in content
    assert "Do not edit during a review pass" in content


def test_goal_creation_and_completion_are_explicit_and_scope_bound() -> None:
    content = SKILL.read_text(encoding="utf-8")

    assert "Create a persistent goal only when the user explicitly asks" in content
    assert "Never absorb newly created or unrelated backlog silently" in content
    assert "every in-scope non-canceled leaf is merged and post-merge verified" in content
