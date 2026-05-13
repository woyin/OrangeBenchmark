import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "markdown_solution",
    Path(__file__).resolve().parents[1] / "solution.py",
)
solution = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(solution)
markdown_to_html = solution.markdown_to_html


def test_header_h1():
    assert "<h1>Title</h1>" in markdown_to_html("# Title")


def test_header_h2():
    assert "<h2>Subtitle</h2>" in markdown_to_html("## Subtitle")


def test_header_h3():
    assert "<h3>Section</h3>" in markdown_to_html("### Section")


def test_bold():
    assert "<strong>bold</strong>" in markdown_to_html("This is **bold** text")


def test_italic():
    assert "<em>italic</em>" in markdown_to_html("This is *italic* text")


def test_link():
    result = markdown_to_html("[Click here](https://example.com)")
    assert '<a href="https://example.com">Click here</a>' in result


def test_unordered_list():
    result = markdown_to_html("- item1\n- item2\n- item3")
    assert "<ul>" in result
    assert "<li>item1</li>" in result
    assert "<li>item2</li>" in result
    assert "<li>item3</li>" in result
    assert "</ul>" in result


def test_ordered_list():
    result = markdown_to_html("1. first\n2. second\n3. third")
    assert "<ol>" in result
    assert "<li>first</li>" in result
    assert "<li>second</li>" in result
    assert "</ol>" in result


def test_code_block():
    result = markdown_to_html("```\nprint('hello')\n```")
    assert "<pre>" in result
    assert "<code>" in result
    assert "print('hello')" in result


def test_inline_code():
    assert "<code>var</code>" in markdown_to_html("Use `var` here")


def test_paragraph():
    result = markdown_to_html("Hello world")
    assert "<p>Hello world</p>" in result


def test_empty_input():
    assert markdown_to_html("") == "" or markdown_to_html("") is not None


def test_mixed_formatting():
    md = "# Title\n\nThis is **bold** and *italic*.\n\n- item with **bold**"
    result = markdown_to_html(md)
    assert "<h1>Title</h1>" in result
    assert "<strong>bold</strong>" in result
    assert "<em>italic</em>" in result
    assert "<ul>" in result
