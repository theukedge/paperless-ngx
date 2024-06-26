import os
import shutil
import tempfile
from pathlib import Path
from unittest import mock

import pytest
from django.test import TestCase
from django.test import override_settings
from ocrmypdf import SubprocessOutputError
from pytest_django.fixtures import SettingsWrapper
from pytest_mock import MockerFixture

from documents.parsers import ParseError
from documents.parsers import run_convert
from documents.tests.utils import DirectoriesMixin
from documents.tests.utils import FileSystemAssertsMixin
from paperless_tesseract.parsers import RasterisedDocumentParser
from paperless_tesseract.parsers import post_process_text


class TestContentPostProcess:
    @pytest.mark.parametrize(
        ("source", "expected"),
        [
            ("simple     string", "simple string"),
            ("simple    newline\n   testing string", "simple newline\ntesting string"),
            (
                "utf-8   строка с пробелами в конце  ",
                "utf-8 строка с пробелами в конце",
            ),
        ],
    )
    def test_post_process_text(self, source: str, expected: str):
        assert expected == post_process_text(source)


class TestParser:
    def assertContainsStrings(self, content, strings):
        # Asserts that all strings appear in content, in the given order.
        indices = []
        for s in strings:
            if s in content:
                indices.append(content.index(s))
            else:
                pytest.fail(f"'{s}' is not in '{content}'")
        assert indices == sorted(indices)

    def test_get_text_from_pdf(
        self,
        tesseract_parser_no_db: RasterisedDocumentParser,
        simple_digital_pdf: Path,
    ):
        text = tesseract_parser_no_db.extract_text(None, simple_digital_pdf)

        assert text is not None

        self.assertContainsStrings(text.strip(), ["This is a test document."])

    def test_thumbnail(
        self,
        tesseract_parser_no_db: RasterisedDocumentParser,
        simple_digital_pdf: Path,
    ):
        thumb = tesseract_parser_no_db.get_thumbnail(
            simple_digital_pdf,
            "application/pdf",
        )

        assert thumb.exists()
        assert thumb.is_file()

    def test_thumbnail_fallback(
        self,
        mocker: MockerFixture,
        tesseract_parser_no_db: RasterisedDocumentParser,
        simple_digital_pdf: Path,
    ):
        def call_convert(input_file, output_file, **kwargs):
            if ".pdf" in str(input_file):
                raise ParseError("Does not compute.")
            else:
                run_convert(input_file=input_file, output_file=output_file, **kwargs)

        mocker.patch("documents.parsers.run_convert").side_effect = call_convert

        thumb = tesseract_parser_no_db.get_thumbnail(
            simple_digital_pdf,
            "application/pdf",
        )

        assert thumb.exists()
        assert thumb.is_file()

    def test_thumbnail_encrypted(
        self,
        tesseract_parser_no_db: RasterisedDocumentParser,
        encrypted_digital_pdf: Path,
    ):
        thumb = tesseract_parser_no_db.get_thumbnail(
            encrypted_digital_pdf,
            "application/pdf",
        )

        assert thumb.exists()
        assert thumb.is_file()

    def test_get_dpi(
        self,
        tesseract_parser_no_db: RasterisedDocumentParser,
        simple_no_dpi_png: Path,
        simple_png: Path,
    ):
        assert tesseract_parser_no_db.get_dpi(simple_no_dpi_png) is None

        assert tesseract_parser_no_db.get_dpi(simple_png) == 72

    def test_simple_digital(
        self,
        tesseract_parser_no_db: RasterisedDocumentParser,
        simple_digital_pdf: Path,
    ):
        tesseract_parser_no_db.parse(
            simple_digital_pdf,
            "application/pdf",
        )

        assert tesseract_parser_no_db.archive_path is not None
        assert tesseract_parser_no_db.archive_path.exists()
        assert tesseract_parser_no_db.archive_path.is_file()

        self.assertContainsStrings(
            tesseract_parser_no_db.get_text(),
            ["This is a test document."],
        )

    def test_with_form(
        self,
        tesseract_parser_no_db: RasterisedDocumentParser,
        pdf_with_form: Path,
    ):
        tesseract_parser_no_db.parse(pdf_with_form, "application/pdf")

        assert tesseract_parser_no_db.archive_path is not None
        assert tesseract_parser_no_db.archive_path.exists()
        assert tesseract_parser_no_db.archive_path.is_file()

        self.assertContainsStrings(
            tesseract_parser_no_db.get_text(),
            ["Please enter your name in here:", "This is a PDF document with a form."],
        )

    def test_with_form_error(
        self,
        settings: SettingsWrapper,
        tesseract_parser_no_db: RasterisedDocumentParser,
        pdf_with_form: Path,
    ):
        settings.OCR_MODE = "redo"

        tesseract_parser_no_db.parse(
            pdf_with_form,
            "application/pdf",
        )

        assert tesseract_parser_no_db.archive_path is not None
        self.assertContainsStrings(
            tesseract_parser_no_db.get_text(),
            ["Please enter your name in here:", "This is a PDF document with a form."],
        )

    def test_signed(
        self,
        settings: SettingsWrapper,
        tesseract_parser_no_db: RasterisedDocumentParser,
        signed_pdf: Path,
    ):
        settings.OCR_MODE = "skip"

        tesseract_parser_no_db.parse(signed_pdf, "application/pdf")

        assert tesseract_parser_no_db.archive_path is None
        self.assertContainsStrings(
            tesseract_parser_no_db.get_text(),
            [
                "This is a digitally signed PDF, created with Acrobat Pro for the Paperless project to enable",
                "automated testing of signed/encrypted PDFs",
            ],
        )

    def test_encrypted(
        self,
        settings: SettingsWrapper,
        tesseract_parser_no_db: RasterisedDocumentParser,
        encrypted_digital_pdf: Path,
    ):
        settings.OCR_MODE = "skip"

        tesseract_parser_no_db.parse(encrypted_digital_pdf, "application/pdf")

        assert tesseract_parser_no_db.archive_path is None
        assert tesseract_parser_no_db.get_text() == ""

    def test_with_form_error_no_text(
        self,
        settings: SettingsWrapper,
        tesseract_parser_no_db: RasterisedDocumentParser,
        pdf_with_form: Path,
    ):
        settings.OCR_MODE = "redo"

        tesseract_parser_no_db.parse(pdf_with_form, "application/pdf")

        self.assertContainsStrings(
            tesseract_parser_no_db.get_text(),
            ["Please enter your name in here:", "This is a PDF document with a form."],
        )

    def test_with_form_force(
        self,
        settings: SettingsWrapper,
        tesseract_parser_no_db: RasterisedDocumentParser,
        pdf_with_form: Path,
    ):
        settings.OCR_MODE = "force"
        tesseract_parser_no_db.parse(
            pdf_with_form,
            "application/pdf",
        )

        self.assertContainsStrings(
            tesseract_parser_no_db.get_text(),
            ["Please enter your name in here:", "This is a PDF document with a form."],
        )

    def test_image_simple(
        self,
        tesseract_parser_no_db: RasterisedDocumentParser,
        simple_png: Path,
    ):
        tesseract_parser_no_db.parse(simple_png, "image/png")

        assert tesseract_parser_no_db.archive_path is not None
        assert tesseract_parser_no_db.archive_path.exists()
        assert tesseract_parser_no_db.archive_path.is_file()

        self.assertContainsStrings(
            tesseract_parser_no_db.get_text(),
            ["This is a test document."],
        )

    def test_image_simple_alpha(
        self,
        tmp_path: Path,
        tesseract_parser_no_db: RasterisedDocumentParser,
        png_with_alpha: Path,
    ):
        # Copy sample file to temp directory, as the parsing changes the file
        # and this makes it modified to Git
        dest_file = shutil.copy(png_with_alpha, tmp_path)

        tesseract_parser_no_db.parse(dest_file, "image/png")

        assert tesseract_parser_no_db.archive_path is not None
        assert tesseract_parser_no_db.archive_path.exists()
        assert tesseract_parser_no_db.archive_path.is_file()

        self.assertContainsStrings(
            tesseract_parser_no_db.get_text(),
            ["This is a test document."],
        )

    def test_image_calc_a4_dpi(
        self,
        tesseract_parser_no_db: RasterisedDocumentParser,
        simple_no_dpi_png: Path,
    ):
        assert tesseract_parser_no_db.calculate_a4_dpi(simple_no_dpi_png) == 62

    def test_image_dpi_fail(
        self,
        tesseract_parser_no_db: RasterisedDocumentParser,
        simple_no_dpi_png: Path,
        mocker: MockerFixture,
    ):
        mocker.patch(
            "paperless_tesseract.parsers.RasterisedDocumentParser.calculate_a4_dpi",
        ).return_value = None

        with pytest.raises(ParseError):
            tesseract_parser_no_db.parse(
                simple_no_dpi_png,
                "image/png",
            )

    @override_settings(OCR_IMAGE_DPI=72, MAX_IMAGE_PIXELS=0)
    def test_image_no_dpi_default(
        self,
        settings: SettingsWrapper,
        tesseract_parser_no_db: RasterisedDocumentParser,
        simple_no_dpi_png: Path,
    ):
        settings.OCR_IMAGE_DPI = 72
        settings.MAX_IMAGE_PIXELS = 0

        tesseract_parser_no_db.parse(
            simple_no_dpi_png,
            "image/png",
        )

        assert tesseract_parser_no_db.archive_path is not None
        assert tesseract_parser_no_db.archive_path.exists()
        assert tesseract_parser_no_db.archive_path.is_file()

        self.assertContainsStrings(
            tesseract_parser_no_db.get_text().lower(),
            ["this is a test document."],
        )

    def test_multi_page(
        self,
        tesseract_parser_no_db: RasterisedDocumentParser,
        multi_page_digital_pdf: Path,
    ):
        tesseract_parser_no_db.parse(
            multi_page_digital_pdf,
            "application/pdf",
        )

        assert tesseract_parser_no_db.archive_path is not None
        assert tesseract_parser_no_db.archive_path.exists()
        assert tesseract_parser_no_db.archive_path.is_file()

        self.assertContainsStrings(
            tesseract_parser_no_db.get_text().lower(),
            ["page 1", "page 2", "page 3"],
        )

    def test_multi_page_pages_skip(
        self,
        settings: SettingsWrapper,
        tesseract_parser_no_db: RasterisedDocumentParser,
        multi_page_digital_pdf: Path,
    ):
        settings.OCR_PAGES = 2
        settings.OCR_MODE = "skip"

        tesseract_parser_no_db.parse(
            multi_page_digital_pdf,
            "application/pdf",
        )

        assert tesseract_parser_no_db.archive_path is not None
        assert tesseract_parser_no_db.archive_path.exists()
        assert tesseract_parser_no_db.archive_path.is_file()

        self.assertContainsStrings(
            tesseract_parser_no_db.get_text().lower(),
            ["page 1", "page 2", "page 3"],
        )

    def test_multi_page_pages_redo(
        self,
        settings: SettingsWrapper,
        tesseract_parser_no_db: RasterisedDocumentParser,
        multi_page_digital_pdf: Path,
    ):
        settings.OCR_PAGES = 2
        settings.OCR_MODE = "redo"

        tesseract_parser_no_db.parse(
            multi_page_digital_pdf,
            "application/pdf",
        )
        assert tesseract_parser_no_db.archive_path is not None
        assert tesseract_parser_no_db.archive_path.exists()
        assert tesseract_parser_no_db.archive_path.is_file()

        self.assertContainsStrings(
            tesseract_parser_no_db.get_text().lower(),
            ["page 1", "page 2", "page 3"],
        )

    def test_multi_page_pages_force(
        self,
        settings: SettingsWrapper,
        tesseract_parser_no_db: RasterisedDocumentParser,
        multi_page_digital_pdf: Path,
    ):
        settings.OCR_PAGES = 2
        settings.OCR_MODE = "force"

        tesseract_parser_no_db.parse(multi_page_digital_pdf, "application/pdf")

        assert tesseract_parser_no_db.archive_path is not None
        assert tesseract_parser_no_db.archive_path.exists()
        assert tesseract_parser_no_db.archive_path.is_file()
        self.assertContainsStrings(
            tesseract_parser_no_db.get_text().lower(),
            ["page 1", "page 2", "page 3"],
        )

    def test_multi_page_analog_pages_skip(
        self,
        settings: SettingsWrapper,
        tesseract_parser_no_db: RasterisedDocumentParser,
        multi_page_images_pdf: Path,
    ):
        settings.OCR_MODE = "skip"

        tesseract_parser_no_db.parse(multi_page_images_pdf, "application/pdf")

        assert tesseract_parser_no_db.archive_path is not None
        assert tesseract_parser_no_db.archive_path.exists()
        assert tesseract_parser_no_db.archive_path.is_file()
        self.assertContainsStrings(
            tesseract_parser_no_db.get_text().lower(),
            ["page 1", "page 2", "page 3"],
        )

    def test_multi_page_analog_pages_redo(
        self,
        settings: SettingsWrapper,
        tesseract_parser_no_db: RasterisedDocumentParser,
        multi_page_images_pdf: Path,
    ):
        """
        GIVEN:
            - File with text contained in images but no text layer
            - OCR of only pages 1 and 2 requested
            - OCR mode set to redo
        WHEN:
            - Document is parsed
        THEN:
            - Text of page 1 and 2 extracted
            - An archive file is created
        """

        settings.OCR_PAGES = 2
        settings.OCR_MODE = "redo"

        tesseract_parser_no_db.parse(multi_page_images_pdf, "application/pdf")

        assert tesseract_parser_no_db.archive_path is not None
        assert tesseract_parser_no_db.archive_path.exists()
        assert tesseract_parser_no_db.archive_path.is_file()
        self.assertContainsStrings(
            tesseract_parser_no_db.get_text().lower(),
            ["page 1", "page 2"],
        )
        assert "page 3" not in tesseract_parser_no_db.get_text().lower()

    @override_settings(OCR_PAGES=1, OCR_MODE="force")
    def test_multi_page_analog_pages_force(
        self,
        settings: SettingsWrapper,
        tesseract_parser_no_db: RasterisedDocumentParser,
        multi_page_images_pdf: Path,
    ):
        """
        GIVEN:
            - File with text contained in images but no text layer
            - OCR of only page 1 requested
            - OCR mode set to force
        WHEN:
            - Document is parsed
        THEN:
            - Only text of page 1 is extracted
            - An archive file is created
        """

        settings.OCR_PAGES = 1
        settings.OCR_MODE = "force"

        tesseract_parser_no_db.parse(multi_page_images_pdf, "application/pdf")

        assert tesseract_parser_no_db.archive_path is not None
        assert tesseract_parser_no_db.archive_path.exists()
        assert tesseract_parser_no_db.archive_path.is_file()
        self.assertContainsStrings(
            tesseract_parser_no_db.get_text().lower(),
            ["page 1"],
        )
        assert "page 2" not in tesseract_parser_no_db.get_text().lower()
        assert "page 3" not in tesseract_parser_no_db.get_text().lower()

    def test_skip_noarchive_with_text(
        self,
        settings: SettingsWrapper,
        tesseract_parser_no_db: RasterisedDocumentParser,
        multi_page_digital_pdf: Path,
    ):
        """
        GIVEN:
            - File with existing text layer
            - OCR mode set to skip_noarchive
        WHEN:
            - Document is parsed
        THEN:
            - Text from images is extracted
            - No archive file is created
        """

        settings.OCR_MODE = "skip_noarchive"

        tesseract_parser_no_db.parse(multi_page_digital_pdf, "application/pdf")
        assert tesseract_parser_no_db.archive_path is None
        self.assertContainsStrings(
            tesseract_parser_no_db.get_text().lower(),
            ["page 1", "page 2", "page 3"],
        )

    @override_settings(OCR_MODE="skip_noarchive")
    def test_skip_noarchive_notext(
        self,
        tesseract_parser_no_db: RasterisedDocumentParser,
        multi_page_images_pdf: Path,
    ):
        """
        GIVEN:
            - File with text contained in images but no text layer
            - OCR mode set to skip_noarchive
        WHEN:
            - Document is parsed
        THEN:
            - Text from images is extracted
            - An archive file is created with the OCRd text
        """

        tesseract_parser_no_db.parse(
            multi_page_images_pdf,
            "application/pdf",
        )

        self.assertContainsStrings(
            tesseract_parser_no_db.get_text().lower(),
            ["page 1", "page 2", "page 3"],
        )

        assert tesseract_parser_no_db.archive_path is not None

    @override_settings(OCR_SKIP_ARCHIVE_FILE="never")
    def test_skip_archive_never_withtext(
        self,
        tesseract_parser_no_db: RasterisedDocumentParser,
        multi_page_digital_pdf: Path,
    ):
        """
        GIVEN:
            - File with existing text layer
            - OCR_SKIP_ARCHIVE_FILE set to never
        WHEN:
            - Document is parsed
        THEN:
            - Text from text layer is extracted
            - Archive file is created
        """

        tesseract_parser_no_db.parse(
            multi_page_digital_pdf,
            "application/pdf",
        )
        assert tesseract_parser_no_db.archive_path is not None
        self.assertContainsStrings(
            tesseract_parser_no_db.get_text().lower(),
            ["page 1", "page 2", "page 3"],
        )

    @override_settings(OCR_SKIP_ARCHIVE_FILE="never")
    def test_skip_archive_never_withimages(
        self,
        tesseract_parser_no_db: RasterisedDocumentParser,
        multi_page_images_pdf: Path,
    ):
        """
        GIVEN:
            - File with text contained in images but no text layer
            - OCR_SKIP_ARCHIVE_FILE set to never
        WHEN:
            - Document is parsed
        THEN:
            - Text from images is extracted
            - Archive file is created
        """

        tesseract_parser_no_db.parse(
            multi_page_images_pdf,
            "application/pdf",
        )
        assert tesseract_parser_no_db.archive_path is not None
        self.assertContainsStrings(
            tesseract_parser_no_db.get_text().lower(),
            ["page 1", "page 2", "page 3"],
        )

    @override_settings(OCR_SKIP_ARCHIVE_FILE="with_text")
    def test_skip_archive_withtext_withtext(
        self,
        tesseract_parser_no_db: RasterisedDocumentParser,
        multi_page_digital_pdf: Path,
    ):
        """
        GIVEN:
            - File with existing text layer
            - OCR_SKIP_ARCHIVE_FILE set to with_text
        WHEN:
            - Document is parsed
        THEN:
            - Text from text layer is extracted
            - No archive file is created
        """

        tesseract_parser_no_db.parse(
            multi_page_digital_pdf,
            "application/pdf",
        )
        assert tesseract_parser_no_db.archive_path is None
        self.assertContainsStrings(
            tesseract_parser_no_db.get_text().lower(),
            ["page 1", "page 2", "page 3"],
        )

    @override_settings(OCR_SKIP_ARCHIVE_FILE="with_text")
    def test_skip_archive_withtext_withimages(
        self,
        tesseract_parser_no_db: RasterisedDocumentParser,
        multi_page_images_pdf: Path,
    ):
        """
        GIVEN:
            - File with text contained in images but no text layer
            - OCR_SKIP_ARCHIVE_FILE set to with_text
        WHEN:
            - Document is parsed
        THEN:
            - Text from images is extracted
            - Archive file is created
        """

        tesseract_parser_no_db.parse(
            multi_page_images_pdf,
            "application/pdf",
        )
        assert tesseract_parser_no_db.archive_path is not None
        self.assertContainsStrings(
            tesseract_parser_no_db.get_text().lower(),
            ["page 1", "page 2", "page 3"],
        )

    @override_settings(OCR_SKIP_ARCHIVE_FILE="always")
    def test_skip_archive_always_withtext(
        self,
        tesseract_parser_no_db: RasterisedDocumentParser,
        multi_page_digital_pdf: Path,
    ):
        """
        GIVEN:
            - File with existing text layer
            - OCR_SKIP_ARCHIVE_FILE set to always
        WHEN:
            - Document is parsed
        THEN:
            - Text from text layer is extracted
            - No archive file is created
        """

        tesseract_parser_no_db.parse(
            multi_page_digital_pdf,
            "application/pdf",
        )
        assert tesseract_parser_no_db.archive_path is None
        self.assertContainsStrings(
            tesseract_parser_no_db.get_text().lower(),
            ["page 1", "page 2", "page 3"],
        )

    @override_settings(OCR_SKIP_ARCHIVE_FILE="always")
    def test_skip_archive_always_withimages(
        self,
        tesseract_parser_no_db: RasterisedDocumentParser,
        multi_page_images_pdf: Path,
    ):
        """
        GIVEN:
            - File with text contained in images but no text layer
            - OCR_SKIP_ARCHIVE_FILE set to always
        WHEN:
            - Document is parsed
        THEN:
            - Text from images is extracted
            - No archive file is created
        """

        tesseract_parser_no_db.parse(
            multi_page_images_pdf,
            "application/pdf",
        )
        assert tesseract_parser_no_db.archive_path is None
        self.assertContainsStrings(
            tesseract_parser_no_db.get_text().lower(),
            ["page 1", "page 2", "page 3"],
        )

    @override_settings(OCR_MODE="skip")
    def test_multi_page_mixed(
        self,
        tesseract_parser_no_db: RasterisedDocumentParser,
        multi_page_mixed_pdf: Path,
    ):
        """
        GIVEN:
            - File with some text contained in images and some in text layer
            - OCR mode set to skip
        WHEN:
            - Document is parsed
        THEN:
            - Text from images is extracted
            - An archive file is created with the OCRd text and the original text
        """

        tesseract_parser_no_db.parse(multi_page_mixed_pdf, "application/pdf")
        assert tesseract_parser_no_db.archive_path is not None
        assert tesseract_parser_no_db.archive_path is not None
        assert tesseract_parser_no_db.archive_path.exists()
        assert tesseract_parser_no_db.archive_path.is_file()
        self.assertContainsStrings(
            tesseract_parser_no_db.get_text().lower(),
            ["page 1", "page 2", "page 3", "page 4", "page 5", "page 6"],
        )

        with open(os.path.join(tesseract_parser_no_db.tempdir, "sidecar.txt")) as f:
            sidecar = f.read()

        assert "[OCR skipped on page(s) 4-6]" in sidecar

    @override_settings(OCR_MODE="redo")
    def test_single_page_mixed(
        self,
        tesseract_parser_no_db: RasterisedDocumentParser,
        multi_page_mixed_pdf: Path,
    ):
        """
        GIVEN:
            - File with some text contained in images and some in text layer
            - Text and images are mixed on the same page
            - OCR mode set to redo
        WHEN:
            - Document is parsed
        THEN:
            - Text from images is extracted
            - Full content of the file is parsed (not just the image text)
            - An archive file is created with the OCRd text and the original text
        """

        tesseract_parser_no_db.parse(multi_page_mixed_pdf, "application/pdf")
        assert tesseract_parser_no_db.archive_path is not None
        assert tesseract_parser_no_db.archive_path is not None
        assert tesseract_parser_no_db.archive_path.exists()
        assert tesseract_parser_no_db.archive_path.is_file()
        self.assertContainsStrings(
            tesseract_parser_no_db.get_text().lower(),
            [
                "this is some normal text, present on page 1 of the document.",
                "this is some text, but in an image, also on page 1.",
                "this is further text on page 1.",
            ],
        )

        with open(os.path.join(tesseract_parser_no_db.tempdir, "sidecar.txt")) as f:
            sidecar = f.read().lower()

        assert "this is some text, but in an image, also on page 1." in sidecar
        assert (
            "this is some normal text, present on page 1 of the document."
            not in sidecar
        )

    @override_settings(OCR_MODE="skip_noarchive")
    def test_multi_page_mixed_no_archive(
        self,
        tesseract_parser_no_db: RasterisedDocumentParser,
        multi_page_mixed_pdf: Path,
    ):
        """
        GIVEN:
            - File with some text contained in images and some in text layer
            - OCR mode set to skip_noarchive
        WHEN:
            - Document is parsed
        THEN:
            - Text from images is extracted
            - No archive file is created as original file contains text
        """

        tesseract_parser_no_db.parse(
            multi_page_mixed_pdf,
            "application/pdf",
        )
        assert tesseract_parser_no_db.archive_path is None
        self.assertContainsStrings(
            tesseract_parser_no_db.get_text().lower(),
            ["page 4", "page 5", "page 6"],
        )

    @override_settings(OCR_MODE="skip", OCR_ROTATE_PAGES=True)
    def test_rotate(self):
        tesseract_parser_no_db.parse(
            os.path.join(self.SAMPLE_FILES, "rotated.pdf"),
            "application/pdf",
        )
        self.assertContainsStrings(
            tesseract_parser_no_db.get_text(),
            [
                "This is the text that appears on the first page. It’s a lot of text.",
                "Even if the pages are rotated, OCRmyPDF still gets the job done.",
                "This is a really weird file with lots of nonsense text.",
                "If you read this, it’s your own fault. Also check your screen orientation.",
            ],
        )

    def test_multi_page_tiff(self):
        """
        GIVEN:
            - Multi-page TIFF image
        WHEN:
            - Image is parsed
        THEN:
            - Text from all pages extracted
        """

        tesseract_parser_no_db.parse(
            os.path.join(self.SAMPLE_FILES, "multi-page-images.tiff"),
            "image/tiff",
        )
        assert tesseract_parser_no_db.archive_path is not None
        assert tesseract_parser_no_db.archive_path.exists()
        assert tesseract_parser_no_db.archive_path.is_file()
        self.assertContainsStrings(
            tesseract_parser_no_db.get_text().lower(),
            ["page 1", "page 2", "page 3"],
        )

    def test_multi_page_tiff_alpha(self):
        """
        GIVEN:
            - Multi-page TIFF image
            - Image include an alpha channel
        WHEN:
            - Image is parsed
        THEN:
            - Text from all pages extracted
        """

        sample_file = os.path.join(self.SAMPLE_FILES, "multi-page-images-alpha.tiff")
        with tempfile.NamedTemporaryFile() as tmp_file:
            shutil.copy(sample_file, tmp_file.name)
            tesseract_parser_no_db.parse(
                tmp_file.name,
                "image/tiff",
            )
            assert tesseract_parser_no_db.archive_path is not None
            assert tesseract_parser_no_db.archive_path.exists()
            assert tesseract_parser_no_db.archive_path.is_file()
            self.assertContainsStrings(
                tesseract_parser_no_db.get_text().lower(),
                ["page 1", "page 2", "page 3"],
            )

    def test_multi_page_tiff_alpha_srgb(self):
        """
        GIVEN:
            - Multi-page TIFF image
            - Image include an alpha channel
            - Image is srgb colorspace
        WHEN:
            - Image is parsed
        THEN:
            - Text from all pages extracted
        """

        sample_file = os.path.join(
            self.SAMPLE_FILES,
            "multi-page-images-alpha-rgb.tiff",
        )
        with tempfile.NamedTemporaryFile() as tmp_file:
            shutil.copy(sample_file, tmp_file.name)
            tesseract_parser_no_db.parse(
                tmp_file.name,
                "image/tiff",
            )
            assert tesseract_parser_no_db.archive_path is not None
            assert tesseract_parser_no_db.archive_path.exists()
            assert tesseract_parser_no_db.archive_path.is_file()
            self.assertContainsStrings(
                tesseract_parser_no_db.get_text().lower(),
                ["page 1", "page 2", "page 3"],
            )

    def test_ocrmypdf_parameters(self):
        params = tesseract_parser_no_db.construct_ocrmypdf_parameters(
            input_file="input.pdf",
            output_file="output.pdf",
            sidecar_file="sidecar.txt",
            mime_type="application/pdf",
            safe_fallback=False,
        )

        assert params["input_file"] == "input.pdf"
        assert params["output_file"] == "output.pdf"
        assert params["sidecar"] == "sidecar.txt"

        with override_settings(OCR_CLEAN="none"):
            params = tesseract_parser_no_db.construct_ocrmypdf_parameters(
                "",
                "",
                "",
                "",
            )
            assert "clean" not in params
            assert "clean_final" not in params

        with override_settings(OCR_CLEAN="clean"):
            params = tesseract_parser_no_db.construct_ocrmypdf_parameters(
                "",
                "",
                "",
                "",
            )
            assert params["clean"]
            assert "clean_final" not in params

        with override_settings(OCR_CLEAN="clean-final", OCR_MODE="skip"):
            params = tesseract_parser_no_db.construct_ocrmypdf_parameters(
                "",
                "",
                "",
                "",
            )
            assert params["clean_final"]
            assert "clean" not in params

        with override_settings(OCR_CLEAN="clean-final", OCR_MODE="redo"):
            params = tesseract_parser_no_db.construct_ocrmypdf_parameters(
                "",
                "",
                "",
                "",
            )
            assert params["clean"]
            assert "clean_final" not in params

        with override_settings(OCR_DESKEW=True, OCR_MODE="skip"):
            params = tesseract_parser_no_db.construct_ocrmypdf_parameters(
                "",
                "",
                "",
                "",
            )
            assert params["deskew"]

        with override_settings(OCR_DESKEW=True, OCR_MODE="redo"):
            params = tesseract_parser_no_db.construct_ocrmypdf_parameters(
                "",
                "",
                "",
                "",
            )
            assert "deskew" not in params

        with override_settings(OCR_DESKEW=False, OCR_MODE="skip"):
            params = tesseract_parser_no_db.construct_ocrmypdf_parameters(
                "",
                "",
                "",
                "",
            )
            assert "deskew" not in params

        with override_settings(OCR_MAX_IMAGE_PIXELS=1_000_001.0):
            params = tesseract_parser_no_db.construct_ocrmypdf_parameters(
                "",
                "",
                "",
                "",
            )
            assert "max_image_mpixels" in params
            self.assertAlmostEqual(params["max_image_mpixels"], 1, places=4)

        with override_settings(OCR_MAX_IMAGE_PIXELS=-1_000_001.0):
            params = tesseract_parser_no_db.construct_ocrmypdf_parameters(
                "",
                "",
                "",
                "",
            )
            assert "max_image_mpixels" not in params

    def test_rtl_language_detection(self):
        """
        GIVEN:
            - File with text in an RTL language
        WHEN:
            - Document is parsed
        THEN:
            - Text from the document is extracted
        """

        tesseract_parser_no_db.parse(
            os.path.join(self.SAMPLE_FILES, "rtl-test.pdf"),
            "application/pdf",
        )

        # Copied from the PDF to here.  Don't even look at it
        assert "ةﯾﻠﺧﺎدﻻ ةرازو" in tesseract_parser_no_db.get_text()

    @mock.patch("ocrmypdf.ocr")
    def test_gs_rendering_error(self, m):
        m.side_effect = SubprocessOutputError("Ghostscript PDF/A rendering failed")

        self.assertRaises(
            ParseError,
            tesseract_parser_no_db.parse,
            simple_digital_pdf,
            "application/pdf",
        )


class TestParserFileTypes(DirectoriesMixin, FileSystemAssertsMixin, TestCase):
    SAMPLE_FILES = os.path.join(os.path.dirname(__file__), "samples")

    def test_bmp(self):
        tesseract_parser_no_db.parse(
            os.path.join(self.SAMPLE_FILES, "simple.bmp"),
            "image/bmp",
        )
        assert tesseract_parser_no_db.archive_path is not None
        assert tesseract_parser_no_db.archive_path.exists()
        assert tesseract_parser_no_db.archive_path.is_file()
        assert "this is a test document" in tesseract_parser_no_db.get_text().lower()

    def test_jpg(self):
        tesseract_parser_no_db.parse(
            os.path.join(self.SAMPLE_FILES, "simple.jpg"),
            "image/jpeg",
        )
        assert tesseract_parser_no_db.archive_path is not None
        assert tesseract_parser_no_db.archive_path.exists()
        assert tesseract_parser_no_db.archive_path.is_file()
        assert "this is a test document" in tesseract_parser_no_db.get_text().lower()

    @override_settings(OCR_IMAGE_DPI=200)
    def test_gif(self):
        tesseract_parser_no_db.parse(
            os.path.join(self.SAMPLE_FILES, "simple.gif"),
            "image/gif",
        )
        assert tesseract_parser_no_db.archive_path is not None
        assert tesseract_parser_no_db.archive_path.exists()
        assert tesseract_parser_no_db.archive_path.is_file()
        assert "this is a test document" in tesseract_parser_no_db.get_text().lower()

    def test_tiff(self):
        tesseract_parser_no_db.parse(
            os.path.join(self.SAMPLE_FILES, "simple.tif"),
            "image/tiff",
        )
        assert tesseract_parser_no_db.archive_path is not None
        assert tesseract_parser_no_db.archive_path.exists()
        assert tesseract_parser_no_db.archive_path.is_file()
        assert "this is a test document" in tesseract_parser_no_db.get_text().lower()

    @override_settings(OCR_IMAGE_DPI=72)
    def test_webp(self):
        tesseract_parser_no_db.parse(
            os.path.join(self.SAMPLE_FILES, "document.webp"),
            "image/webp",
        )
        assert tesseract_parser_no_db.archive_path is not None
        assert tesseract_parser_no_db.archive_path.exists()
        assert tesseract_parser_no_db.archive_path.is_file()
        # Older tesseracts consistently mangle the space between "a webp",
        # tesseract 5.3.0 seems to do a better job, so we're accepting both
        assert re.search(
            "this is a ?webp document, created 11/14/2022.",
            tesseract_parser_no_db.get_text().lower(),
        )
