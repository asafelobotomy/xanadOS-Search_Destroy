"""Type stubs for openpyxl package."""

from pathlib import Path
from typing import Any, Iterator, Optional, Union

class Workbook:
    """Openpyxl Workbook class."""

    active: "Worksheet"
    sheetnames: list[str]

    def __init__(self, write_only: bool = False, iso_dates: bool = False) -> None: ...
    def create_sheet(
        self, title: Optional[str] = None, index: Optional[int] = None
    ) -> "Worksheet": ...
    def save(self, filename: Union[str, Path]) -> None: ...
    def close(self) -> None: ...
    def __getitem__(self, key: str) -> "Worksheet": ...
    def __iter__(self) -> Iterator["Worksheet"]: ...

class Worksheet:
    """Openpyxl Worksheet class."""

    title: str
    max_row: int
    max_column: int

    def __init__(self, parent: Workbook, title: Optional[str] = None) -> None: ...
    def append(self, iterable: list[Any]) -> None: ...
    def cell(self, row: int, column: int, value: Optional[Any] = None) -> "Cell": ...
    def __getitem__(self, key: str) -> Union["Cell", tuple["Cell", ...]]: ...
    def iter_rows(
        self,
        min_row: Optional[int] = None,
        max_row: Optional[int] = None,
        min_col: Optional[int] = None,
        max_col: Optional[int] = None,
        values_only: bool = False,
    ) -> Iterator[tuple["Cell", ...]]: ...

class Cell:
    """Openpyxl Cell class."""

    value: Any
    row: int
    column: int
    coordinate: str

    def __init__(
        self,
        worksheet: Worksheet,
        row: Optional[int] = None,
        column: Optional[int] = None,
        value: Optional[Any] = None,
    ) -> None: ...

def load_workbook(
    filename: Union[str, Path],
    read_only: bool = False,
    keep_vba: bool = False,
    data_only: bool = False,
    keep_links: bool = True,
    rich_text: bool = False,
) -> Workbook: ...
