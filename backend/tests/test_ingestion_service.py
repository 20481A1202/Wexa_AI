from app.services.ingestion_service import parse_csv_events


def test_parse_csv_events_maps_extra_columns_to_properties():
    events = parse_csv_events("name,source,plan,amount\nsignup,csv,pro,99\n")

    assert len(events) == 1
    assert events[0].name == "signup"
    assert events[0].source == "csv"
    assert events[0].properties == {"plan": "pro", "amount": "99"}
