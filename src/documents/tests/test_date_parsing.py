import datetime

from dateutil import tz
from django.conf import settings
from django.test import TestCase
from django.test import override_settings

from documents.parsers import parse_date
from documents.parsers import parse_date_generator


class TestDate(TestCase):
    def test_date_format_1(self):
        text = "lorem ipsum 130218 lorem ipsum"
        self.assertEqual(parse_date("", text), None)

    def test_date_format_2(self):
        text = "lorem ipsum 2018 lorem ipsum"
        self.assertEqual(parse_date("", text), None)

    def test_date_format_3(self):
        text = "lorem ipsum 20180213 lorem ipsum"
        self.assertEqual(parse_date("", text), None)

    def test_date_format_4(self):
        text = "lorem ipsum 13.02.2018 lorem ipsum"
        date = parse_date("", text)
        self.assertEqual(
            date,
            datetime.datetime(2018, 2, 13, 0, 0, tzinfo=tz.gettz(settings.TIME_ZONE)),
        )

    def test_date_format_5(self):
        text = "lorem ipsum 130218, 2018, 20180213 and lorem 13.02.2018 lorem ipsum"
        date = parse_date("", text)
        self.assertEqual(
            date,
            datetime.datetime(2018, 2, 13, 0, 0, tzinfo=tz.gettz(settings.TIME_ZONE)),
        )

    def test_date_format_6(self):
        text = (
            "lorem ipsum\n"
            "Wohnort\n"
            "3100\n"
            "IBAN\n"
            "AT87 4534\n"
            "1234\n"
            "1234 5678\n"
            "BIC\n"
            "lorem ipsum"
        )
        self.assertEqual(parse_date("", text), None)

    def test_date_format_7(self):
        text = "lorem ipsum\nMärz 2019\nlorem ipsum"
        date = parse_date("", text)
        self.assertEqual(
            date,
            datetime.datetime(2019, 3, 1, 0, 0, tzinfo=tz.gettz(settings.TIME_ZONE)),
        )

    def test_date_format_8(self):
        text = (
            "lorem ipsum\n"
            "Wohnort\n"
            "3100\n"
            "IBAN\n"
            "AT87 4534\n"
            "1234\n"
            "1234 5678\n"
            "BIC\n"
            "lorem ipsum\n"
            "März 2020"
        )
        self.assertEqual(
            parse_date("", text),
            datetime.datetime(2020, 3, 1, 0, 0, tzinfo=tz.gettz(settings.TIME_ZONE)),
        )

    def test_date_format_9(self):
        text = "lorem ipsum\n27. Nullmonth 2020\nMärz 2020\nlorem ipsum"
        self.assertEqual(
            parse_date("", text),
            datetime.datetime(2020, 3, 1, 0, 0, tzinfo=tz.gettz(settings.TIME_ZONE)),
        )

    def test_date_format_10(self):
        text = "Customer Number Currency 22-MAR-2022 Credit Card 1934829304"
        self.assertEqual(
            parse_date("", text),
            datetime.datetime(2022, 3, 22, 0, 0, tzinfo=tz.gettz(settings.TIME_ZONE)),
        )

    def test_date_format_11(self):
        text = "Customer Number Currency 22 MAR 2022 Credit Card 1934829304"
        self.assertEqual(
            parse_date("", text),
            datetime.datetime(2022, 3, 22, 0, 0, tzinfo=tz.gettz(settings.TIME_ZONE)),
        )

    def test_date_format_12(self):
        text = "Customer Number Currency 22/MAR/2022 Credit Card 1934829304"
        self.assertEqual(
            parse_date("", text),
            datetime.datetime(2022, 3, 22, 0, 0, tzinfo=tz.gettz(settings.TIME_ZONE)),
        )

    def test_date_format_13(self):
        text = "Customer Number Currency 22.MAR.2022 Credit Card 1934829304"
        self.assertEqual(
            parse_date("", text),
            datetime.datetime(2022, 3, 22, 0, 0, tzinfo=tz.gettz(settings.TIME_ZONE)),
        )

    def test_date_format_14(self):
        text = "Customer Number Currency 22.MAR 2022 Credit Card 1934829304"
        self.assertEqual(
            parse_date("", text),
            datetime.datetime(2022, 3, 22, 0, 0, tzinfo=tz.gettz(settings.TIME_ZONE)),
        )

    def test_date_format_15(self):
        text = "Customer Number Currency 22.MAR.22 Credit Card 1934829304"
        self.assertIsNone(parse_date("", text), None)

    def test_date_format_16(self):
        text = "Customer Number Currency 22.MAR,22 Credit Card 1934829304"
        self.assertIsNone(parse_date("", text), None)

    def test_date_format_17(self):
        text = "Customer Number Currency 22,MAR,2022 Credit Card 1934829304"
        self.assertIsNone(parse_date("", text), None)

    def test_date_format_18(self):
        text = "Customer Number Currency 22 MAR,2022 Credit Card 1934829304"
        self.assertIsNone(parse_date("", text), None)

    def test_date_format_19(self):
        text = "Customer Number Currency 21st MAR 2022 Credit Card 1934829304"
        self.assertEqual(
            parse_date("", text),
            datetime.datetime(2022, 3, 21, 0, 0, tzinfo=tz.gettz(settings.TIME_ZONE)),
        )

    def test_date_format_20(self):
        text = "Customer Number Currency 22nd March 2022 Credit Card 1934829304"
        self.assertEqual(
            parse_date("", text),
            datetime.datetime(2022, 3, 22, 0, 0, tzinfo=tz.gettz(settings.TIME_ZONE)),
        )

    def test_date_format_21(self):
        text = "Customer Number Currency 2nd MAR 2022 Credit Card 1934829304"
        self.assertEqual(
            parse_date("", text),
            datetime.datetime(2022, 3, 2, 0, 0, tzinfo=tz.gettz(settings.TIME_ZONE)),
        )

    def test_date_format_22(self):
        text = "Customer Number Currency 23rd MAR 2022 Credit Card 1934829304"
        self.assertEqual(
            parse_date("", text),
            datetime.datetime(2022, 3, 23, 0, 0, tzinfo=tz.gettz(settings.TIME_ZONE)),
        )

    def test_date_format_23(self):
        text = "Customer Number Currency 24th MAR 2022 Credit Card 1934829304"
        self.assertEqual(
            parse_date("", text),
            datetime.datetime(2022, 3, 24, 0, 0, tzinfo=tz.gettz(settings.TIME_ZONE)),
        )

    def test_date_format_24(self):
        text = "Customer Number Currency 21-MAR-2022 Credit Card 1934829304"
        self.assertEqual(
            parse_date("", text),
            datetime.datetime(2022, 3, 21, 0, 0, tzinfo=tz.gettz(settings.TIME_ZONE)),
        )

    def test_date_format_25(self):
        text = "Customer Number Currency 25TH MAR 2022 Credit Card 1934829304"
        self.assertEqual(
            parse_date("", text),
            datetime.datetime(2022, 3, 25, 0, 0, tzinfo=tz.gettz(settings.TIME_ZONE)),
        )

    def test_date_format_26(self):
        text = "CHASE 0 September 25, 2019 JPMorgan Chase Bank, NA. P0 Box 182051"
        self.assertEqual(
            parse_date("", text),
            datetime.datetime(2019, 9, 25, 0, 0, tzinfo=tz.gettz(settings.TIME_ZONE)),
        )

    def test_crazy_date_past(self):
        self.assertIsNone(parse_date("", "01-07-0590 00:00:00"))

    def test_crazy_date_future(self):
        self.assertIsNone(parse_date("", "01-07-2350 00:00:00"))

    def test_crazy_date_with_spaces(self):
        self.assertIsNone(parse_date("", "20 408000l 2475"))

    def test_utf_month_names(self):
        self.assertEqual(
            parse_date("", "13 décembre 2023"),
            datetime.datetime(2023, 12, 13, 0, 0, tzinfo=tz.gettz(settings.TIME_ZONE)),
        )
        self.assertEqual(
            parse_date("", "13 août 2022"),
            datetime.datetime(2022, 8, 13, 0, 0, tzinfo=tz.gettz(settings.TIME_ZONE)),
        )
        self.assertEqual(
            parse_date("", "11 März 2020"),
            datetime.datetime(2020, 3, 11, 0, 0, tzinfo=tz.gettz(settings.TIME_ZONE)),
        )
        self.assertEqual(
            parse_date("", "17. ožujka 2018."),
            datetime.datetime(2018, 3, 17, 0, 0, tzinfo=tz.gettz(settings.TIME_ZONE)),
        )
        self.assertEqual(
            parse_date("", "1. veljače 2016."),
            datetime.datetime(2016, 2, 1, 0, 0, tzinfo=tz.gettz(settings.TIME_ZONE)),
        )
        self.assertEqual(
            parse_date("", "15. února 1985"),
            datetime.datetime(1985, 2, 15, 0, 0, tzinfo=tz.gettz(settings.TIME_ZONE)),
        )
        self.assertEqual(
            parse_date("", "30. září 2011"),
            datetime.datetime(2011, 9, 30, 0, 0, tzinfo=tz.gettz(settings.TIME_ZONE)),
        )
        self.assertEqual(
            parse_date("", "28. května 1990"),
            datetime.datetime(1990, 5, 28, 0, 0, tzinfo=tz.gettz(settings.TIME_ZONE)),
        )
        self.assertEqual(
            parse_date("", "1. grudzień 1997"),
            datetime.datetime(1997, 12, 1, 0, 0, tzinfo=tz.gettz(settings.TIME_ZONE)),
        )
        self.assertEqual(
            parse_date("", "17 Şubat 2024"),
            datetime.datetime(2024, 2, 17, 0, 0, tzinfo=tz.gettz(settings.TIME_ZONE)),
        )
        self.assertEqual(
            parse_date("", "30 Ağustos 2012"),
            datetime.datetime(2012, 8, 30, 0, 0, tzinfo=tz.gettz(settings.TIME_ZONE)),
        )
        self.assertEqual(
            parse_date("", "17 Eylül 2000"),
            datetime.datetime(2000, 9, 17, 0, 0, tzinfo=tz.gettz(settings.TIME_ZONE)),
        )
        self.assertEqual(
            parse_date("", "5. október 1992"),
            datetime.datetime(1992, 10, 5, 0, 0, tzinfo=tz.gettz(settings.TIME_ZONE)),
        )

    def test_multiple_dates(self):
        text = """This text has multiple dates.
                  For example 02.02.2018, 22 July 2022 and December 2021.
                  But not 24-12-9999 because it's in the future..."""
        dates = list(parse_date_generator("", text))
        self.assertEqual(len(dates), 3)
        self.assertEqual(
            dates[0],
            datetime.datetime(2018, 2, 2, 0, 0, tzinfo=tz.gettz(settings.TIME_ZONE)),
        )
        self.assertEqual(
            dates[1],
            datetime.datetime(2022, 7, 22, 0, 0, tzinfo=tz.gettz(settings.TIME_ZONE)),
        )
        self.assertEqual(
            dates[2],
            datetime.datetime(2021, 12, 1, 0, 0, tzinfo=tz.gettz(settings.TIME_ZONE)),
        )

    @override_settings(FILENAME_DATE_ORDER="YMD")
    def test_filename_date_parse_valid_ymd(self, *args):
        """
        GIVEN:
            - Date parsing from the filename is enabled
            - Filename date format is with Year Month Day (YMD)
            - Filename contains date matching the format

        THEN:
            - Should parse the date from the filename
        """
        self.assertEqual(
            parse_date("/tmp/Scan-2022-04-01.pdf", "No date in here"),
            datetime.datetime(2022, 4, 1, 0, 0, tzinfo=tz.gettz(settings.TIME_ZONE)),
        )

    @override_settings(FILENAME_DATE_ORDER="DMY")
    def test_filename_date_parse_valid_dmy(self, *args):
        """
        GIVEN:
            - Date parsing from the filename is enabled
            - Filename date format is with Day Month Year (DMY)
            - Filename contains date matching the format

        THEN:
            - Should parse the date from the filename
        """
        self.assertEqual(
            parse_date("/tmp/Scan-10.01.2021.pdf", "No date in here"),
            datetime.datetime(2021, 1, 10, 0, 0, tzinfo=tz.gettz(settings.TIME_ZONE)),
        )

    @override_settings(FILENAME_DATE_ORDER="YMD")
    def test_filename_date_parse_invalid(self, *args):
        """
        GIVEN:
            - Date parsing from the filename is enabled
            - Filename includes no date
            - File content includes no date

        THEN:
            - No date is parsed
        """
        self.assertIsNone(
            parse_date("/tmp/20 408000l 2475 - test.pdf", "No date in here"),
        )

    @override_settings(
        FILENAME_DATE_ORDER="YMD",
        IGNORE_DATES=(datetime.date(2022, 4, 1),),
    )
    def test_filename_date_ignored_use_content(self, *args):
        """
        GIVEN:
            - Date parsing from the filename is enabled
            - Filename date format is with Day Month Year (YMD)
            - Date order is Day Month Year (DMY, the default)
            - Filename contains date matching the format
            - Filename date is an ignored date
            - File content includes a date

        THEN:
            - Should parse the date from the content not filename
        """
        self.assertEqual(
            parse_date("/tmp/Scan-2022-04-01.pdf", "The matching date is 24.03.2022"),
            datetime.datetime(2022, 3, 24, 0, 0, tzinfo=tz.gettz(settings.TIME_ZONE)),
        )

    @override_settings(
        IGNORE_DATES=(datetime.date(2019, 11, 3), datetime.date(2020, 1, 17)),
    )
    def test_ignored_dates_default_order(self, *args):
        """
        GIVEN:
            - Ignore dates have been set
            - File content includes ignored dates
            - File content includes 1 non-ignored date

        THEN:
            - Should parse the date non-ignored date from content
        """
        text = "lorem ipsum 110319, 20200117 and lorem 13.02.2018 lorem ipsum"
        self.assertEqual(
            parse_date("", text),
            datetime.datetime(2018, 2, 13, 0, 0, tzinfo=tz.gettz(settings.TIME_ZONE)),
        )

    @override_settings(
        IGNORE_DATES=(datetime.date(2019, 11, 3), datetime.date(2020, 1, 17)),
        DATE_ORDER="YMD",
    )
    def test_ignored_dates_order_ymd(self, *args):
        """
        GIVEN:
            - Ignore dates have been set
            - Date order is Year Month Date (YMD)
            - File content includes ignored dates
            - File content includes 1 non-ignored date

        THEN:
            - Should parse the date non-ignored date from content
        """
        text = "lorem ipsum 190311, 20200117 and lorem 13.02.2018 lorem ipsum"

        self.assertEqual(
            parse_date("", text),
            datetime.datetime(2018, 2, 13, 0, 0, tzinfo=tz.gettz(settings.TIME_ZONE)),
        )
