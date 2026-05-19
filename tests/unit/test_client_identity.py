from iceflo_signal.privacy import ClientIdentityTransformer


def test_client_display_name_uses_first_two_letters_of_first_and_last_name() -> None:
    transformer = ClientIdentityTransformer("mindful_oregon:simple_practice")

    identity = transformer.transform_name("John Jones")

    assert identity.client_display_name == "Jo Jo"
    assert len(identity.client_key) == 64


def test_display_name_collision_keeps_unique_keys() -> None:
    transformer = ClientIdentityTransformer("mindful_oregon:simple_practice")

    john = transformer.transform_name("John Jones")
    joseph = transformer.transform_name("Joseph Johnson")

    assert john.client_display_name == "Jo Jo"
    assert joseph.client_display_name == "Jo Jo"
    assert john.client_key != joseph.client_key
