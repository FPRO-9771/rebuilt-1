"""
Tests for vision system.
"""

from handlers.mock_vision import MockVisionProvider
from handlers.vision import VisionTarget


def test_mock_vision_target_left():
    """Verify simulated left target has negative tx."""
    vision = MockVisionProvider()
    vision.simulate_target_left(tag_id=4, offset_degrees=10, distance=2.0)

    target = vision.get_target(4)
    assert target is not None
    assert target.tx == -10
    assert target.distance == 2.0
    assert target.tag_id == 4


def test_mock_vision_target_right():
    """Verify simulated right target has positive tx."""
    vision = MockVisionProvider()
    vision.simulate_target_right(tag_id=7, offset_degrees=5, distance=3.0)

    target = vision.get_target(7)
    assert target is not None
    assert target.tx == 5
    assert target.distance == 3.0


def test_mock_vision_target_centered():
    """Verify simulated centered target has tx=0."""
    vision = MockVisionProvider()
    vision.simulate_target_centered(tag_id=4, distance=1.5)

    target = vision.get_target(4)
    assert target is not None
    assert target.tx == 0
    assert target.distance == 1.5


def test_mock_vision_no_target():
    """Verify no target returns None."""
    vision = MockVisionProvider()
    vision.simulate_no_target()

    assert vision.get_target(4) is None
    assert vision.has_target(4) is False


def test_mock_vision_query_history():
    """Verify query history tracks tag_id lookups."""
    vision = MockVisionProvider()
    vision.simulate_target_centered(tag_id=4)

    vision.get_target(4)
    vision.get_target(7)
    vision.get_target(None)

    assert vision._query_history == [4, 7, None]


def test_mock_vision_multiple_tags():
    """Verify multiple tags can be set and queried independently."""
    vision = MockVisionProvider()
    vision.simulate_target_left(tag_id=4, offset_degrees=10, distance=2.0)
    vision.simulate_target_right(tag_id=7, offset_degrees=5, distance=3.0)

    target_4 = vision.get_target(4)
    target_7 = vision.get_target(7)

    assert target_4.tx == -10
    assert target_4.distance == 2.0
    assert target_7.tx == 5
    assert target_7.distance == 3.0
