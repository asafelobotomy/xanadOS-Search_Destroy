"""Type stubs for weasyprint package."""

from pathlib import Path
from typing import Any, List, Optional, Union

class HTML:
    """WeasyPrint HTML class."""

    def __init__(
        self,
        guess: Optional[str] = None,
        filename: Optional[Union[str, Path]] = None,
        url: Optional[str] = None,
        file_obj: Optional[Any] = None,
        string: Optional[Union[str, bytes]] = None,
        encoding: Optional[str] = None,
        base_url: Optional[str] = None,
        url_fetcher: Optional[Any] = None,
        media_type: str = "print",
    ) -> None: ...
    def write_pdf(
        self,
        target: Optional[Union[str, Path, Any]] = None,
        stylesheets: Optional[List[Any]] = None,
        zoom: float = 1,
        finisher: Optional[Any] = None,
        font_config: Optional[Any] = None,
        counter_style: Optional[Any] = None,
        **kwargs: Any,
    ) -> bytes: ...
    def render(
        self,
        stylesheets: Optional[List[Any]] = None,
        optimize_size: Union[bool, tuple] = False,
        font_config: Optional[Any] = None,
        counter_style: Optional[Any] = None,
    ) -> "Document": ...

class CSS:
    """WeasyPrint CSS class."""

    def __init__(
        self,
        guess: Optional[str] = None,
        filename: Optional[Union[str, Path]] = None,
        url: Optional[str] = None,
        file_obj: Optional[Any] = None,
        string: Optional[Union[str, bytes]] = None,
        encoding: Optional[str] = None,
        base_url: Optional[str] = None,
        url_fetcher: Optional[Any] = None,
        _check_mime_type: bool = False,
        media_type: str = "print",
        font_config: Optional[Any] = None,
        counter_style: Optional[Any] = None,
        matcher: Optional[Any] = None,
        page_rules: Optional[List[Any]] = None,
    ) -> None: ...

class Document:
    """WeasyPrint Document class."""

    def write_pdf(
        self,
        target: Optional[Union[str, Path, Any]] = None,
        zoom: float = 1,
        finisher: Optional[Any] = None,
        **kwargs: Any,
    ) -> bytes: ...
