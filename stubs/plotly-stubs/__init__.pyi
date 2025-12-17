"""Type stubs for plotly package."""

from typing import Any, Dict, List, Optional, Union

class Figure:
    """Plotly Figure class."""

    def __init__(
        self,
        data: Optional[List[Any]] = None,
        layout: Optional[Dict[str, Any]] = None,
        frames: Optional[List[Any]] = None,
    ) -> None: ...
    def add_trace(
        self, trace: Any, row: Optional[int] = None, col: Optional[int] = None
    ) -> Figure: ...
    def update_layout(self, **kwargs: Any) -> Figure: ...
    def update_xaxes(self, **kwargs: Any) -> Figure: ...
    def update_yaxes(self, **kwargs: Any) -> Figure: ...
    def to_html(
        self,
        config: Optional[Dict[str, Any]] = None,
        auto_play: bool = True,
        include_plotlyjs: Union[bool, str] = True,
        include_mathjax: Union[bool, str] = False,
        post_script: Optional[Union[str, List[str]]] = None,
        full_html: bool = True,
        animation_opts: Optional[Dict[str, Any]] = None,
        default_width: str = "100%",
        default_height: str = "100%",
        validate: bool = True,
        div_id: Optional[str] = None,
    ) -> str: ...
    def write_html(
        self,
        file: Union[str, Any],
        config: Optional[Dict[str, Any]] = None,
        auto_play: bool = True,
        include_plotlyjs: Union[bool, str] = True,
        include_mathjax: Union[bool, str] = False,
        post_script: Optional[Union[str, List[str]]] = None,
        full_html: bool = True,
        animation_opts: Optional[Dict[str, Any]] = None,
        default_width: str = "100%",
        default_height: str = "100%",
        validate: bool = True,
        auto_open: bool = False,
        div_id: Optional[str] = None,
    ) -> None: ...
    def show(self, **kwargs: Any) -> None: ...

class graph_objects:
    """Plotly graph_objects module."""

    class Scatter:
        def __init__(
            self,
            x: Optional[List[Any]] = None,
            y: Optional[List[Any]] = None,
            mode: str = "lines",
            name: Optional[str] = None,
            **kwargs: Any,
        ) -> None: ...

    class Bar:
        def __init__(
            self,
            x: Optional[List[Any]] = None,
            y: Optional[List[Any]] = None,
            name: Optional[str] = None,
            **kwargs: Any,
        ) -> None: ...

    class Pie:
        def __init__(
            self,
            labels: Optional[List[str]] = None,
            values: Optional[List[Any]] = None,
            name: Optional[str] = None,
            **kwargs: Any,
        ) -> None: ...

    class Heatmap:
        def __init__(
            self,
            z: Optional[List[List[Any]]] = None,
            x: Optional[List[Any]] = None,
            y: Optional[List[Any]] = None,
            colorscale: Optional[str] = None,
            **kwargs: Any,
        ) -> None: ...

    Figure = Figure

def make_subplots(
    rows: int = 1,
    cols: int = 1,
    subplot_titles: Optional[List[str]] = None,
    specs: Optional[List[List[Optional[Dict[str, Any]]]]] = None,
    **kwargs: Any,
) -> Figure: ...
