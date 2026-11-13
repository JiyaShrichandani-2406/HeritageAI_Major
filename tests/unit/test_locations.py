from backend.app.ai.itinerary_generator import (
    _resolve_place_area,
    _supports_destination,
    _validate_place,
)
from backend.app.repositories.location_repository import (
    LocationRepository,
    _build_catalog,
)


def test_unified_catalog_has_unique_ids_and_valid_city_relationships():
    repository = LocationRepository()
    cities = repository.cities()
    places = repository.places()

    location_ids = [location["id"] for location in [*cities, *places]]
    city_ids = {city["id"] for city in cities}

    assert len(places) == 25
    assert len(location_ids) == len(set(location_ids))
    assert all(place["city_id"] in city_ids for place in places)
    assert {city["name"] for city in cities} == {
        "Agra",
        "Fatehpur Sikri",
        "Bharatpur",
        "Delhi",
        "Bhopal",
    }


def test_location_aliases_merge_duplicate_and_inconsistent_names():
    repository = LocationRepository()

    assert repository.find_place("Chini Ka Rauza")["id"] == (
        repository.find_place("Chini ka Rauza")["id"]
    )
    assert repository.find_place("Guru Ka Taal Gurudwara")["name"] == (
        "Guru ka Taal"
    )
    assert repository.find_place("Tomb of Mariam-uz-Zamani")["id"] == (
        "place-tomb-mariam-uz-zamani"
    )
    assert repository.find_place("Soami Bagh (Radhasoami Samadhi)")["name"] == (
        "Soami Bagh Samadhi"
    )


def test_nearby_coordinates_are_canonical_when_both_sources_have_a_place():
    repository = LocationRepository()
    chini = repository.find_place("Chini Ka Rauza")
    jama_masjid = repository.find_place("Jama Masjid Agra")

    assert (chini["latitude"], chini["longitude"]) == (27.2, 78.0233)
    assert chini["coordinate_source"] == "nearby_places.json"
    assert (jama_masjid["latitude"], jama_masjid["longitude"]) == (
        27.183,
        78.0147,
    )


def test_agra_fatehpur_sikri_and_bharatpur_remain_distinct():
    repository = LocationRepository()
    taj = repository.find_place("Taj Mahal")
    fatehpur = repository.find_place("Fatehpur Sikri")
    keoladeo = repository.find_place("Keoladeo National Park")

    assert taj["city_id"] == "city-agra"
    assert fatehpur["city_id"] == "city-fatehpur-sikri"
    assert keoladeo["city_id"] == "city-bharatpur"
    assert _resolve_place_area("Fatehpur Sikri") == "Fatehpur Sikri"
    assert _resolve_place_area("Keoladeo National Park") == "Bharatpur"
    assert _supports_destination("Bharatpur") is True


def test_itinerary_place_validation_uses_canonical_city_relationships():
    assert _validate_place("Ram Bagh", "Agra") == "Ram Bagh (Aram Bagh)"
    assert _validate_place("Taj Mahal", "Bharatpur") is None
    assert _validate_place("Tomb of Mariam-uz-Zamani", "Sikandra, Agra") == (
        "Tomb of Mariam-uz-Zamani"
    )


def test_same_place_name_in_different_cities_does_not_merge():
    heritage_records = [
        {
            "id": "agra-same-site",
            "name": "Same Site",
            "city": "Agra",
            "state": "Uttar Pradesh",
            "country": "India",
            "latitude": 27.1,
            "longitude": 78.1,
            "sources": [],
        },
        {
            "id": "jaipur-same-site",
            "name": "Same Site",
            "city": "Jaipur",
            "state": "Rajasthan",
            "country": "India",
            "latitude": 26.9,
            "longitude": 75.8,
            "sources": [],
        },
    ]
    nearby_records = [
        {
            "id": "same-site-jaipur",
            "name": "Same Site",
            "category": "monument",
            "latitude": 26.9,
            "longitude": 75.8,
            "address": "Jaipur, Rajasthan, India",
            "source_url": "https://example.com/same-site",
        }
    ]

    catalog = _build_catalog(heritage_records, nearby_records)

    assert len(catalog["places"]) == 2
    jaipur_place = next(
        place for place in catalog["places"] if place["city"] == "Jaipur"
    )
    assert jaipur_place["source_ids"] == [
        "heritage:jaipur-same-site",
        "nearby:same-site-jaipur",
    ]
