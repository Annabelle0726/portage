"""The Scale-2 EduCloud profile's policy assertions, made machine-checkable.

Hermetic: reads the checked-in profile YAML, no network, no model calls.

These tests exist because "student lanes are sovereign by absence" is the
platform's strongest privacy claim and, until something asserts it, it is a
sentence in a roadmap rather than a property of the system. CC-P2 Step 5 asks
for exactly this check ("assert that every configuration file marked sensitive
contains only local deployments, and that no non-local endpoint can be added to
one without the check failing"). It arrives here early, scoped to the profile
that needs it first, because the EduCloud student lane is the first
configuration in the platform that will carry real student coursework.

The strong test is `test_student_lane_has_no_off_institution_deployment`: it
fails if ANY row in the student registry routes off the institution, and it
reads the registry rather than the rendered output so that a row cannot be
introduced and then rendered away.
"""

from pathlib import Path

import pytest

yaml = pytest.importorskip("yaml")

PROFILES = Path(__file__).resolve().parent.parent / "config" / "profiles"
STUDENT = PROFILES / "scale2.educloud.student.registry.yaml"
STAFF = PROFILES / "scale2.educloud.staff.registry.yaml"

# The sovereign route. vLLM on institutional HPC speaks the OpenAI wire format,
# so `openai` is the provider_route for an institution-hosted deployment. Every
# other route in the schema's enum leaves the institution by definition:
# openrouter, anthropic and perplexity are commercial endpoints, and
# ollama_chat is a personal-machine route that has no meaning at Scale 2.
SOVEREIGN_ROUTE = "openai"
OFF_INSTITUTION_ROUTES = {"openrouter", "anthropic", "perplexity"}

SEVEN_ALIASES = {
    "classifier",
    "code_small",
    "code_large",
    "research_synthesis",
    "embedding",
    "proprietary_code",
    "proprietary_research",
}

# Fields that must match between the two lanes' sovereign rows. These describe
# the same physical vLLM deployments addressed from two configurations; a drift
# here means the lanes have silently forked and the student lane may be talking
# to something the staff lane isn't.
SHARED_DEPLOYMENT_FIELDS = ("model_id", "endpoint", "max_context")


def _models(path: Path) -> list[dict]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))["models"]


@pytest.fixture
def student():
    return _models(STUDENT)


@pytest.fixture
def staff():
    return _models(STAFF)


class TestStudentLaneIsolation:
    def test_student_lane_has_no_off_institution_deployment(self, student):
        offenders = [
            f"{m['alias']} -> {m['provider_route']}/{m['model_id']}"
            for m in student
            if m["provider_route"] in OFF_INSTITUTION_ROUTES
        ]
        assert not offenders, (
            "the student registry contains an off-institution deployment: "
            f"{offenders}. Student lanes are sovereign by ABSENCE — the "
            "guarantee is that no such row exists in the configuration this "
            "lane runs against, so a misroute is impossible rather than "
            "merely disallowed. Setting `enabled: false` on the row is NOT a "
            "fix: it still renders into model_list. Remove the row."
        )

    def test_student_lane_is_entirely_sovereign(self, student):
        routes = {m["provider_route"] for m in student}
        assert routes == {SOVEREIGN_ROUTE}, (
            f"expected every student deployment on the {SOVEREIGN_ROUTE!r} "
            f"(institutional vLLM) route, got {routes}"
        )

    def test_student_lane_declares_no_proprietary_alias(self, student):
        proprietary = [
            m["alias"] for m in student if m["alias"].startswith("proprietary_")
        ]
        assert not proprietary, (
            f"student registry declares {proprietary}. These aliases have no "
            "sovereign deployment and must be absent from this lane entirely, "
            "so a student-lane request for one fails loudly at the proxy."
        )

    def test_student_endpoints_are_env_refs_never_literals(self, student):
        for m in student:
            endpoint = m.get("endpoint") or ""
            assert endpoint.startswith("os.environ/"), (
                f"{m['alias']} ({m['model_id']}) endpoint {endpoint!r} is not an "
                "os.environ/ reference — a literal hostname or URL here would "
                "both break portability and put institutional infrastructure "
                "into a public repository"
            )

    def test_student_lane_carries_no_regulated_deployment(self, student):
        """Institutional HPC is sovereign but SHARED — CC-P2's data-destinations
        policy states administrators can view interactions there, and that
        identifiable student records never reach a shared endpoint. Student
        coursework reaches this tier de-identified, carrying only opaque
        attribution labels, so `personal_sensitive` is the honest ceiling.
        A `regulated` row appearing here means someone has pointed
        identifiable-record processing at shared infrastructure."""
        regulated = [
            m["alias"] for m in student if m["data_classification"] == "regulated"
        ]
        assert not regulated, (
            f"student registry marks {regulated} as `regulated`, but every "
            "deployment in it is institutional HPC, which CC-P2's policy "
            "defines as sovereign-but-shared. Identifiable-record processing "
            "has no deployment at E0 by design — see scale2.educloud.md §3."
        )


class TestStaffLane:
    def test_staff_lane_declares_all_seven_aliases(self, staff):
        assert {m["alias"] for m in staff} == SEVEN_ALIASES

    def test_proprietary_rows_are_registered_but_disabled(self, staff):
        proprietary = [m for m in staff if m["alias"].startswith("proprietary_")]
        assert proprietary, "the rescue rows must exist so enabling them is a flag flip"
        for m in proprietary:
            assert m["enabled"] is False, (
                f"{m['alias']} is enabled in the staff profile. Proprietary "
                "rescue stays off until a deliberate, audited decision turns "
                "it on."
            )

    def test_sovereign_is_first_wherever_a_lane_has_a_fallback(self, staff):
        by_alias: dict[str, list[dict]] = {}
        for m in staff:
            if m["enabled"]:
                by_alias.setdefault(m["alias"], []).append(m)
        for alias, entries in by_alias.items():
            if len(entries) < 2:
                continue
            first = min(entries, key=lambda e: e["order"])
            assert first["provider_route"] == SOVEREIGN_ROUTE, (
                f"alias {alias!r} prefers {first['provider_route']!r} over the "
                "sovereign deployment. Sovereign is the DEFAULT at Scale 2, "
                "not merely one option — the hosted tail is a fallback for "
                "queue delay, never the first choice."
            )

    def test_off_institution_rows_are_public_only(self, staff):
        for m in staff:
            if m["provider_route"] in OFF_INSTITUTION_ROUTES:
                assert m["data_classification"] == "public", (
                    f"{m['alias']} ({m['provider_route']}/{m['model_id']}) leaves "
                    f"the institution but is classified "
                    f"{m['data_classification']!r}. A commercial endpoint may "
                    "only ever be cleared for `public`."
                )


class TestLanesDescribeTheSameDeployments:
    def test_sovereign_rows_match_across_lanes(self, student, staff):
        """The two lanes address the SAME vLLM deployments from two configs.
        If the student lane's contract drifts from the staff lane's, the JS2
        launch can only satisfy one of them."""
        staff_sovereign = {
            m["alias"]: m for m in staff if m["provider_route"] == SOVEREIGN_ROUTE
        }
        for m in student:
            counterpart = staff_sovereign.get(m["alias"])
            assert counterpart is not None, (
                f"student lane declares {m['alias']!r} with no sovereign "
                "counterpart in the staff lane"
            )
            for field in SHARED_DEPLOYMENT_FIELDS:
                assert m[field] == counterpart[field], (
                    f"{m['alias']}.{field} differs between lanes: "
                    f"student={m[field]!r} staff={counterpart[field]!r}"
                )
