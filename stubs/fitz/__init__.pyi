"""Type stubs for PyMuPDF (fitz).

This module provides type information for the fitz package (PyMuPDF),
focusing on the core functionality used in our document processing pipeline.
"""

from typing import Iterator, List, Optional, Union

class Point:
    """Represents a point in a PDF document."""

    x: float
    y: float

class Rect:
    """Represents a rectangle in a PDF document."""

    x0: float
    y0: float
    x1: float
    y1: float

class Page:
    """Page class for PDF document pages.

    Provides methods for text extraction and page manipulation.
    """

    rotation: int
    rect: Rect

    def get_text(
        self,
        option: str = "text",
        *,
        clip: Optional[Union[Rect, List[float]]] = None,
        flags: int = 0,
    ) -> str:
        """Extract text from the page.

        Args:
            option: Text extraction mode ('text', 'blocks', 'words', etc.)
            clip: Optional rectangle to restrict text extraction
            flags: Optional flags to control text extraction

        Returns:
            Extracted text in the specified format
        """
        ...

class Document:
    """Document class for PDF files.

    Provides methods for document manipulation and page access.
    """

    page_count: int
    metadata: dict

    def __len__(self) -> int: ...
    def __iter__(self) -> Iterator[Page]: ...
    def __getitem__(self, index: int) -> Page: ...
    def get_page_numbers(self, number_list: Optional[List[int]] = None) -> List[int]:
        """Get valid page numbers.

        Args:
            number_list: Optional list of page numbers to validate

        Returns:
            List of valid page numbers
        """
        ...

def open(
    filename: str,
    *,
    filetype: Optional[str] = None,
    password: Optional[str] = None,
) -> Document:
    """Open a PDF document.

    Args:
        filename: Path to the PDF file
        filetype: Optional file type hint
        password: Optional password for encrypted documents

    Returns:
        Document object for the opened PDF
    """
    ...
