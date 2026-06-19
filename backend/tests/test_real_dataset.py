from pathlib import Path

from app.services.real_dataset import load_result_rows, make_fifa_codes


def test_real_dataset_file_has_expected_columns():
    rows = load_result_rows(Path("app/data/international_results.csv"))
    assert len(rows) > 1000
    assert rows[0].home_team == "Scotland"
    assert rows[0].away_team == "England"


def test_generated_fifa_codes_are_unique_and_three_chars():
    codes = make_fifa_codes(["Brazil", "Barbados", "Belgium"], reserved_codes={"BRA"})
    assert len(set(codes.values())) == 3
    assert all(len(code) == 3 for code in codes.values())
    assert "BRA" not in codes.values()
