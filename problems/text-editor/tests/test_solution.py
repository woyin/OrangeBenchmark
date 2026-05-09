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
