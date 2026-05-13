import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "text_editor_solution",
    Path(__file__).resolve().parents[1] / "solution.py",
)
solution = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(solution)
TextEditor = solution.TextEditor


def test_insert_single_and_multi_line_text():
    editor = TextEditor()
    editor.insert(0, 0, "hello")
    editor.insert(0, 5, "\nworld")
    assert editor.get_text() == "hello\nworld"


def test_delete_across_lines_and_replace():
    editor = TextEditor()
    editor.insert(0, 0, "hello\nworld")
    editor.delete(0, 3, 4)
    assert editor.get_text() == "helorld"
    editor.replace(0, 3, 2, "XX")
    assert editor.get_text() == "helXXld"


def test_undo_redo_insert_delete_replace():
    editor = TextEditor()
    editor.insert(0, 0, "abc")
    editor.delete(0, 1, 1)
    editor.replace(0, 1, 1, "Z")
    assert editor.get_text() == "aZ"
    editor.undo()
    assert editor.get_text() == "ac"
    editor.undo()
    assert editor.get_text() == "abc"
    editor.redo()
    assert editor.get_text() == "ac"


def test_repeated_undo_to_initial_and_empty_undo_noop():
    editor = TextEditor()
    editor.undo()
    editor.insert(0, 0, "abc")
    editor.undo()
    editor.undo()
    assert editor.get_text() == ""


def test_new_edit_clears_redo_stack():
    editor = TextEditor()
    editor.insert(0, 0, "abc")
    editor.undo()
    editor.insert(0, 0, "x")
    editor.redo()
    assert editor.get_text() == "x"


def test_invalid_positions_raise_index_error():
    editor = TextEditor()
    editor.insert(0, 0, "abc")
    for operation in (
        lambda: editor.insert(9, 0, "x"),
        lambda: editor.delete(0, 9, 1),
        lambda: editor.replace(0, 9, 1, "x"),
    ):
        try:
            operation()
        except IndexError:
            pass
        else:
            raise AssertionError("expected IndexError")


def test_large_document_operations():
    editor = TextEditor()
    editor.insert(0, 0, "\n".join(str(i) for i in range(10_000)))
    editor.insert(9_999, len("9999"), "!")
    assert editor.get_text().endswith("9999!")
    editor.undo()
    assert editor.get_text().endswith("9999")


def test_deep_undo_redo_chain():
    editor = TextEditor()
    for i in range(50):
        editor.insert(0, 0, f"line{i}\n")
    for _ in range(50):
        editor.undo()
    assert editor.get_text() == ""
    for _ in range(50):
        editor.redo()
    assert editor.get_text().startswith("line49")


def test_empty_string_operations():
    editor = TextEditor()
    editor.insert(0, 0, "")
    assert editor.get_text() == ""
    editor.undo()
    assert editor.get_text() == ""


def test_replace_with_longer_text():
    editor = TextEditor()
    editor.insert(0, 0, "hello world")
    editor.replace(0, 6, 5, "universe and beyond")
    assert editor.get_text() == "hello universe and beyond"


def test_delete_at_end_of_line():
    editor = TextEditor()
    editor.insert(0, 0, "line1\nline2\nline3")
    editor.delete(1, 0, 5)
    assert editor.get_text() == "line1\n\nline3"


def test_unicode_multibyte():
    editor = TextEditor()
    editor.insert(0, 0, "你好世界")
    editor.insert(0, 2, "🎉")
    assert "🎉" in editor.get_text()
    editor.undo()
    assert editor.get_text() == "你好世界"
