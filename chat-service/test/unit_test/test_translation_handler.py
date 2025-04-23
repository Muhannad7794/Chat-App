# test/unit_test/test_translation_handler.py

import pytest
from django.core.cache import cache
from chat.translation_handler import (
    get_language_preference,
    set_language_preference,
    DEFAULT_LANGUAGE,
)


@pytest.mark.django_db
def test_default_language_preference():
    user_id = 999
    room_id = 555
    key = f"user_{user_id}_room_{room_id}_lang"
    cache.delete(key)  # Ensure key is gone

    lang = get_language_preference(user_id, room_id)
    assert lang == DEFAULT_LANGUAGE


@pytest.mark.django_db
def test_set_and_get_language_preference():
    user_id = 123
    room_id = 321
    test_lang = "es"

    set_language_preference(user_id, room_id, test_lang)
    retrieved_lang = get_language_preference(user_id, room_id)

    assert retrieved_lang == test_lang
