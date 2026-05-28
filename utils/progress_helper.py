"""Utility for creating uniform Rich progress bars across the project."""

from rich.console import Console
from rich.progress import (
    BarColumn,
    Progress,
    TaskProgressColumn,
    TextColumn,
    TimeRemainingColumn,
)


def make_progress(
    description: str,
    total: int | None = None,
    text_style: str = "green",
    bar_style: str = "green",
    console: Console | None = None,
) -> Progress:
    """Создаёт Progress с единым стилем для всего проекта.

    Args:
        description: Текст описания задачи (используется как заголовок).
        total: Общее количество шагов (None = бесконечный).
        text_style: Цвет текста описания.
        bar_style: Цвет полосы прогресса.
        console: Опциональный Console для рендеринга.

    Returns:
        Экземпляр Progress.
    """
    cols = [
        TextColumn(f"[bold {text_style}]{{task.description}}"),
        BarColumn(bar_width=None, complete_style=bar_style, finished_style=f"bold {bar_style}"),
        TaskProgressColumn(),
        TextColumn("{task.completed}/{task.total}"),
        TimeRemainingColumn(),
    ]
    return Progress(*cols, console=console) if console else Progress(*cols)
