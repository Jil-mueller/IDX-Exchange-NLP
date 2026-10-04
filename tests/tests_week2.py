from scripts.text_cleaning import TextCleaner

import pandas as pd

from scripts.text_cleaning import TextCleaner


# Given setup

def test_clean_text_basic():
    cleaner = TextCleaner()
    result = cleaner.clean_text("Beautiful home")
    assert result == "Beautiful home"


def test_clean_text_strips_whitespace():
    cleaner = TextCleaner()
    result = cleaner.clean_text("   Beautiful home   ")
    assert result == "Beautiful home"


def test_clean_text_empty_string():
    cleaner = TextCleaner()
    assert cleaner.clean_text("") == ""


def test_clean_text_none():
    cleaner = TextCleaner()
    assert cleaner.clean_text(None) == ""


# unicode tests

def test_unicode_normalization():
    cleaner = TextCleaner()
    result = cleaner.normalize_unicode("café")
    assert result == "café"


def test_unicode_fullwidth_characters():
    cleaner = TextCleaner()
    result = cleaner.normalize_unicode("ＡＢＣ")
    assert result == "ABC"


def test_unicode_numbers():
    cleaner = TextCleaner()
    result = cleaner.normalize_unicode("１２３")
    assert result == "123"

# price tests

def test_price_450k():
    cleaner = TextCleaner()
    assert "450000" in cleaner.normalize_prices("priced at 450k")


def test_price_1200k():
    cleaner = TextCleaner()
    assert "1200000" in cleaner.normalize_prices("priced at 1200k")


def test_price_1_2m():
    cleaner = TextCleaner()
    assert "1200000" in cleaner.normalize_prices("$1.2m home")


def test_price_2m():
    cleaner = TextCleaner()
    assert "2000000" in cleaner.normalize_prices("2m home")


def test_price_decimal_k():
    cleaner = TextCleaner()
    assert "125000" in cleaner.normalize_prices("125k price")


def test_price_uppercase_k():
    cleaner = TextCleaner()
    assert "450000" in cleaner.normalize_prices("450K")


def test_price_uppercase_m():
    cleaner = TextCleaner()
    assert "1200000" in cleaner.normalize_prices("1.2M")


def test_price_with_space():
    cleaner = TextCleaner()
    assert "450000" in cleaner.normalize_prices("450 k")

# measurement tests

def test_sqft():
    cleaner = TextCleaner()
    result = cleaner.normalize_measurements("2,000 sqft")
    assert result == "2000 square feet"


def test_sq_ft():
    cleaner = TextCleaner()
    result = cleaner.normalize_measurements("2,000 sq ft")
    assert result == "2000 square feet"


def test_sqft_without_comma():
    cleaner = TextCleaner()
    result = cleaner.normalize_measurements("2000 sqft")
    assert result == "2000 square feet"


def test_large_sqft():
    cleaner = TextCleaner()
    result = cleaner.normalize_measurements("12,500 sqft")
    assert result == "12500 square feet"


def test_sqft_uppercase():
    cleaner = TextCleaner()
    result = cleaner.normalize_measurements("2000 SQFT")
    assert result == "2000 square feet"


def test_sq_ft_uppercase():
    cleaner = TextCleaner()
    result = cleaner.normalize_measurements("2000 SQ FT")
    assert result == "2000 square feet"


# HTML tests

def test_remove_bold_html():
    cleaner = TextCleaner()
    assert cleaner.remove_html("<b>Beautiful</b>") == "Beautiful"


def test_remove_paragraph_html():
    cleaner = TextCleaner()
    assert cleaner.remove_html("<p>Beautiful home</p>") == "Beautiful home"


def test_remove_multiple_html_tags():
    cleaner = TextCleaner()
    result = cleaner.remove_html("<b>Beautiful</b> <i>home</i>")
    assert result == "Beautiful home"


def test_remove_html_with_attributes():
    cleaner = TextCleaner()
    result = cleaner.remove_html('<div class="listing">Beautiful home</div>')
    assert result == "Beautiful home"

# Abbreviations tests

def test_br_abbreviation():
    cleaner = TextCleaner()
    result = cleaner.expand_abbreviations("3br home")
    assert result == "3 bedroom home"


def test_ba_abbreviation():
    cleaner = TextCleaner()
    result = cleaner.expand_abbreviations("2ba home")
    assert result == "2 bathroom home"


def test_bdrm_abbreviation():
    cleaner = TextCleaner()
    result = cleaner.expand_abbreviations("3bdrm home")
    assert result == "3 bedroom home"


def test_bd_abbreviation():
    cleaner = TextCleaner()
    result = cleaner.expand_abbreviations("4bd home")
    assert result == "4 bedroom home"


def test_sqft_abbreviation():
    cleaner = TextCleaner()
    result = cleaner.expand_abbreviations("large sqft")
    assert result == "large square feet"


def test_with_abbreviation():
    cleaner = TextCleaner()
    result = cleaner.expand_abbreviations("home w/ garage")
    assert result == "home with garage"


def test_without_abbreviation():
    cleaner = TextCleaner()
    result = cleaner.expand_abbreviations("home w/o garage")
    assert result == "home without garage"


def test_mbr_abbreviation():
    cleaner = TextCleaner()
    result = cleaner.expand_abbreviations("large mbr")
    assert result == "large master bedroom"


def test_hoa_abbreviation():
    cleaner = TextCleaner()
    result = cleaner.expand_abbreviations("hoa fees")
    assert result == "homeowners association fees"


def test_condo_abbreviation():
    cleaner = TextCleaner()
    result = cleaner.expand_abbreviations("beautiful condo")
    assert result == "beautiful condominium"


def test_ave_abbreviation():
    cleaner = TextCleaner()
    result = cleaner.expand_abbreviations("Main Ave")
    assert result == "Main avenue"


def test_blvd_abbreviation():
    cleaner = TextCleaner()
    result = cleaner.expand_abbreviations("Main Blvd")
    assert result == "Main boulevard"


def test_rd_abbreviation():
    cleaner = TextCleaner()
    result = cleaner.expand_abbreviations("Main Rd")
    assert result == "Main road"


def test_st_abbreviation():
    cleaner = TextCleaner()
    result = cleaner.expand_abbreviations("Main St")
    assert result == "Main street"

# Whitespace tests

def test_multiple_spaces():
    cleaner = TextCleaner()
    assert cleaner.normalize_whitespace("hello    world") == "hello world"


def test_tabs():
    cleaner = TextCleaner()
    assert cleaner.normalize_whitespace("hello\tworld") == "hello world"


def test_newlines():
    cleaner = TextCleaner()
    assert cleaner.normalize_whitespace("hello\nworld") == "hello world"


def test_mixed_whitespace():
    cleaner = TextCleaner()
    assert cleaner.normalize_whitespace("hello \n\t world") == "hello world"

# Combined cleaning tests

def test_combined_price_and_abbreviation():
    cleaner = TextCleaner()
    result = cleaner.clean_text("Beautiful 3br home priced at 450k")
    assert "3 bedroom" in result
    assert "450000" in result


def test_combined_measurement_and_abbreviation():
    cleaner = TextCleaner()
    result = cleaner.clean_text("3br home with 2,000 sqft")
    assert "3 bedroom" in result
    assert "2000 square feet" in result


def test_combined_html_and_whitespace():
    cleaner = TextCleaner()
    result = cleaner.clean_text("<b>Beautiful</b>    home")
    assert result == "Beautiful home"


def test_combined_multiple_cleaning_rules():
    cleaner = TextCleaner()
    result = cleaner.clean_text(
        "<b>Beautiful 3br home</b> w/ 2,000 sqft priced at 450k"
    )

    assert "Beautiful 3 bedroom home with 2000 square feet priced at 450000" == result


# profiling tests

def test_profiling():
    cleaner = TextCleaner()

    df = pd.DataFrame({
        "remarks": [
            "Beautiful 3br home",
            "2,000 sqft property",
            "Priced at 450k",
            None
        ]
    })

    profile = cleaner.profile_column(df, "remarks")

    assert "null_rate" in profile
    assert "avg_length" in profile
    assert "common_terms" in profile
    assert "price_mentions" in profile
    assert "has_html" in profile
    assert "common_abbreviations" in profile


def test_profiling_null_rate():
    cleaner = TextCleaner()

    df = pd.DataFrame({
        "remarks": [
            "Beautiful home",
            None,
            "Another home",
            None
        ]
    })

    profile = cleaner.profile_column(df, "remarks")

    assert profile["null_rate"] == 0.5


def test_profiling_price_mentions():
    cleaner = TextCleaner()

    df = pd.DataFrame({
        "remarks": [
            "Home priced at 450k",
            "Beautiful home",
            "1.2m property"
        ]
    })

    profile = cleaner.profile_column(df, "remarks")

    assert profile["price_mentions"] == 2


def test_profiling_html():
    cleaner = TextCleaner()

    df = pd.DataFrame({
        "remarks": [
            "<b>Beautiful home</b>",
            "Normal home",
            "<p>Another home</p>"
        ]
    })

    profile = cleaner.profile_column(df, "remarks")

    assert profile["has_html"] == 2


def test_profiling_abbreviations():
    cleaner = TextCleaner()

    df = pd.DataFrame({
        "remarks": [
            "3br home",
            "2br home",
            "Beautiful home"
        ]
    })

    profile = cleaner.profile_column(df, "remarks")

    assert profile["common_abbreviations"]["br"] == 2