from django.core.checks import ERROR
from pytest_django.fixtures import SettingsWrapper
from pytest_mock import MockerFixture

from paperless_tesseract import check_default_language_available


class TestChecks:
    def test_default_language(self):
        check_default_language_available(None)

    def test_no_language(self, settings: SettingsWrapper):
        settings.OCR_LANGUAGE = ""
        msgs = check_default_language_available(None)
        assert len(msgs) == 1
        assert msgs[0].msg.startswith(
            "No OCR language has been specified with PAPERLESS_OCR_LANGUAGE",
        )

    def test_invalid_language(self, settings: SettingsWrapper, mocker: MockerFixture):
        settings.OCR_LANGUAGE = "ita"
        mocker.patch(
            "paperless_tesseract.checks.get_tesseract_langs",
            return_value=["deu", "eng"],
        )

        msgs = check_default_language_available(None)

        assert len(msgs) == 1
        assert msgs[0].level == ERROR

    def test_multi_part_language(
        self,
        settings: SettingsWrapper,
        mocker: MockerFixture,
    ):
        """
        GIVEN:
            - An OCR language which is multi part (ie chi-sim)
            - The language is correctly formatted
        WHEN:
            - Installed packages are checked
        THEN:
            - No errors are reported
        """
        settings.OCR_LANGUAGE = "chi_sim"
        mocker.patch(
            "paperless_tesseract.checks.get_tesseract_langs",
            return_value=["chi_sim", "eng"],
        )

        msgs = check_default_language_available(None)

        assert len(msgs) == 0

    def test_multi_part_language_bad_format(
        self,
        settings: SettingsWrapper,
        mocker: MockerFixture,
    ):
        """
        GIVEN:
            - An OCR language which is multi part (ie chi-sim)
            - The language is correctly NOT formatted
        WHEN:
            - Installed packages are checked
        THEN:
            - No errors are reported
        """
        settings.OCR_LANGUAGE = "chi-sim"
        mocker.patch(
            "paperless_tesseract.checks.get_tesseract_langs",
            return_value=["chi_sim", "eng"],
        )

        msgs = check_default_language_available(None)

        assert len(msgs) == 1
        assert msgs[0].level == ERROR
