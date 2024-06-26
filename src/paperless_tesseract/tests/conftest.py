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
        if "parser" in locals():
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


@pytest.fixture(scope="session")
def multi_page_digital_pdf(sample_dir: Path) -> Path:
    return sample_dir / "multi-page-digital.pdf"


@pytest.fixture(scope="session")
def multi_page_images_pdf(sample_dir: Path) -> Path:
    return sample_dir / "multi-page-images.pdf"


@pytest.fixture(scope="session")
def multi_page_mixed_pdf(sample_dir: Path) -> Path:
    return sample_dir / "multi-page-mixed.pdf"


@pytest.fixture(scope="session")
def pdf_with_form(sample_dir: Path) -> Path:
    return sample_dir / "with-form.pdf"


@pytest.fixture(scope="session")
def signed_pdf(sample_dir: Path) -> Path:
    return sample_dir / "signed.pdf"


@pytest.fixture(scope="session")
def simple_no_dpi_png(sample_dir: Path) -> Path:
    return sample_dir / "simple-no-dpi.png"


@pytest.fixture(scope="session")
def simple_png(sample_dir: Path) -> Path:
    return sample_dir / "simple.png"


@pytest.fixture(scope="session")
def png_with_alpha(sample_dir: Path) -> Path:
    return sample_dir / "simple-alpha.png"
