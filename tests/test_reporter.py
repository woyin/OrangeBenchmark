from runner.reporter import _grade_label


def test_grade_label_a_plus():
    assert "A+" in _grade_label(0.95)
    assert "green" in _grade_label(0.95)


def test_grade_label_a():
    assert "A" in _grade_label(0.90)
    assert "blue" in _grade_label(0.90)


def test_grade_label_b():
    assert "B" in _grade_label(0.75)
    assert "yellow" in _grade_label(0.75)


def test_grade_label_c():
    assert "C" in _grade_label(0.60)


def test_grade_label_d():
    assert "D" in _grade_label(0.30)
    assert "red" in _grade_label(0.30)
