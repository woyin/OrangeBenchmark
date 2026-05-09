class TextEditor:
    def __init__(self):
        self._text = ""
        self._undo: list[str] = []
        self._redo: list[str] = []

    def insert(self, line: int, col: int, text: str) -> None:
        offset = self._offset(line, col)
        self._record()
        self._text = self._text[:offset] + text + self._text[offset:]

    def delete(self, line: int, col: int, length: int) -> None:
        offset = self._offset(line, col)
        self._record()
        self._text = self._text[:offset] + self._text[offset + max(0, length) :]

    def replace(self, line: int, col: int, length: int, new_text: str) -> None:
        offset = self._offset(line, col)
        self._record()
        self._text = self._text[:offset] + new_text + self._text[offset + max(0, length) :]

    def get_text(self) -> str:
        return self._text

    def undo(self) -> None:
        if not self._undo:
            return
        self._redo.append(self._text)
        self._text = self._undo.pop()

    def redo(self) -> None:
        if not self._redo:
            return
        self._undo.append(self._text)
        self._text = self._redo.pop()

    def _record(self) -> None:
        self._undo.append(self._text)
        self._redo.clear()

    def _offset(self, line: int, col: int) -> int:
        if line < 0 or col < 0:
            raise IndexError("invalid position")
        if self._text == "":
            if line == 0 and col == 0:
                return 0
            raise IndexError("invalid position")

        parts = self._text.split("\n")
        if line >= len(parts) or col > len(parts[line]):
            raise IndexError("invalid position")
        return sum(len(parts[idx]) + 1 for idx in range(line)) + col
