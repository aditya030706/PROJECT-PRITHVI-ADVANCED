from app.document_ai import extract_numeric_readings


def test_standard_inspection_wording():
    text = """
    Methane concentration: 1.25%.
    Air quantity: 450 m3/min.
    Temperature: 32 C.
    """

    result = extract_numeric_readings(text)

    assert result["methane_pct"] == 1.25
    assert result["airflow_m3_min"] == 450.0
    assert result["temperature_c"] == 32.0


def test_natural_inspection_wording():
    text = """
    Methane concentration was recorded at 1.25%.
    Measured air quantity was 450 m3/min.
    Temperature recorded during inspection was 32 C.
    """

    result = extract_numeric_readings(text)

    assert result["methane_pct"] == 1.25
    assert result["airflow_m3_min"] == 450.0
    assert result["temperature_c"] == 32.0


def test_ch4_and_temperature_variations():
    text = """
    CH4 level was 1.25 percent.
    Airflow reading was 450 m3/min.
    Temperature was 32 degrees Celsius.
    """

    result = extract_numeric_readings(text)

    assert result["methane_pct"] == 1.25
    assert result["airflow_m3_min"] == 450.0
    assert result["temperature_c"] == 32.0