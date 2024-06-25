from collections.abc import Generator
from pathlib import Path

import pytest

from paperless_tesseract.parsers import RasterisedDocumentParser


@pytest.fixture()
def tesseract_parser() -> Generator[RasterisedDocumentParser, None, None]:
    try:
        parser = RasterisedDocumentParser(logging_group=None)
        yield parser
    finally:
        parser.cleanup()


@pytest.fixture(scope="session")
def sample_dir() -> Path:
    return (Path(__file__).parent / Path("samples")).resolve()


@pytest.fixture(scope="session")
def simple_digital_pdf(sample_dir: Path) -> Path:
    return sample_dir / "simple-digital.pdf"


@pytest.fixture(scope="session")
def encrypted_digital_pdf(sample_dir: Path) -> Path:
    return sample_dir / "encrypted.pdf"
