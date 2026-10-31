"""Contract tests for audit_case(): evidence integrity guarantees.

These cover the two failure modes that produced false COMPLETE rows in the
first pass over the 518-request dataset:

1. A subject with no resolvable evidence was reported COMPLETE with zero steps.
2. The per-run index was mutated while auditing, making results order-dependent.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from audit.pipeline import audit_case


CASE = {
    "case_id": "t_empty",
    "request_text": "please delete my account and everything attached to it",
    "email": "subject@example.com",
    "audit_at": "2026-10-01T00:00:00Z",
    "requested_at": "2026-09-01T00:00:00Z",
    "reported_at": "2026-09-05T00:00:00Z",
}


def _indices(activity=None):
    """Minimal index tuple: uid_to_info, ident_to_uid, user_resources,
    res_observations, all_res_to_obs, ev_manifest, activity."""
    return ({}, {"subject@example.com": "user_99"}, {}, {}, {}, {}, activity or [])


def test_no_evidence_is_never_complete():
    status, steps = audit_case(dict(CASE), _indices())
    assert status != "COMPLETE", "absence of evidence must not be reported as COMPLETE"
    assert steps == []


def test_shared_index_is_not_mutated():
    activity = [{
        "activity_id": "activity_test",
        "source_system": "deletion_worker",
        "target_system": "account_service",
        "resource_id": "account_001",
        "event_time": "2026-09-05T00:00:00Z",
        "details": "deletion_worker submitted account_001",
    }]
    indices = _indices(activity)
    before = json.dumps(indices[4], sort_keys=True)

    first = audit_case(dict(CASE), indices)
    second = audit_case(dict(CASE), indices)

    assert before == json.dumps(indices[4], sort_keys=True), "shared index was mutated"
    assert first == second, "results depend on case processing order"
