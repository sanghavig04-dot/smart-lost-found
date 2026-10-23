import numpy as np

from app.matching import image_score, rank_matches, score, text_score


def vec(*xs):
    v = np.array(xs, dtype="float32")
    return (v / np.linalg.norm(v)).tolist()


def test_text_score_rewards_shared_keywords_and_category():
    lost = {"title": "Blue water bottle", "description": "steel, dent on side", "category": "other", "location": "Library"}
    found = {"title": "Steel water bottle", "description": "found in library", "category": "other", "location": "Library"}
    other = {"title": "Calculus textbook", "description": "", "category": "stationery", "location": "Canteen"}
    assert text_score(lost, found) > text_score(lost, other)


def test_image_score_identical_vs_different():
    a, b = vec(1, 0, 0), vec(0, 1, 0)
    assert image_score(a, a) == 1.0
    assert image_score(a, b) == 0.0
    assert image_score(a, None) is None


def test_score_falls_back_to_text_without_images():
    a = {"title": "Black wallet", "category": "other", "location": "Gate"}
    b = {"title": "Leather wallet", "category": "other", "location": "Gate"}
    assert score(a, b) == text_score(a, b)


def test_rank_matches_orders_and_filters():
    lost = {"title": "Red backpack", "category": "bags", "location": "Hostel", "embedding": vec(1, 0, 0)}
    good = {"title": "Red backpack", "category": "bags", "location": "Hostel", "embedding": vec(1, 0.05, 0)}
    bad = {"title": "Spectacles case", "category": "other", "location": "Canteen", "embedding": vec(0, 1, 0)}
    ranked = rank_matches(lost, [bad, good], threshold=0.35)
    assert [c for _, c in ranked] == [good]
    assert ranked[0][0] > 0.9
