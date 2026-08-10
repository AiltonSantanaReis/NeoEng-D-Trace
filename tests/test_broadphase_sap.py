# tests/test_broadphase_sap.py
from src.collision.broadphase import AABB, BroadPhaseSAP


def test_sap_insert_update_remove():
    sap = BroadPhaseSAP()
    aabb = AABB(0, 0, 10, 10)
    sap.insert(1, aabb)
    assert 1 in sap._intervals
    aabb2 = AABB(5, 5, 15, 15)
    sap.update(1, aabb2)
    assert sap._intervals[1] == (5, 15)
    sap.remove(1)
    assert 1 not in sap._intervals


def test_sap_potential_pairs_non_overlapping():
    sap = BroadPhaseSAP()
    sap.insert(1, AABB(0, 0, 5, 5))
    sap.insert(2, AABB(10, 10, 15, 15))
    pairs = sap.potential_pairs()
    assert len(pairs) == 0


def test_sap_potential_pairs_overlapping():
    sap = BroadPhaseSAP()
    sap.insert(1, AABB(0, 0, 10, 10))
    sap.insert(2, AABB(5, 5, 15, 15))
    pairs = sap.potential_pairs()
    assert (1, 2) in pairs or (2, 1) in pairs
