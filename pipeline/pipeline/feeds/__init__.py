"""Feed parser registry — one module per source, joined only by NormalizedEvent (ADR 0006)."""

from collections.abc import Callable
from typing import Any

from pipeline.feeds.gdacs import parse_gdacs
from pipeline.feeds.usgs import parse_usgs
from pipeline.models import NormalizedEvent

Parser = Callable[[dict[str, Any]], list[NormalizedEvent]]

PARSERS: dict[str, Parser] = {"usgs": parse_usgs, "gdacs": parse_gdacs}
