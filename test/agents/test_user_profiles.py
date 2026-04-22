import pytest

from agents.user_profiles import UsernameValidationError, get_user_profile_service


def test_user_profile_service_persists_and_reloads_username(tmp_path):
    db_path = tmp_path / "user_profiles.json"
    service = get_user_profile_service(db_path=str(db_path))

    profile = service.set_username(
        user_id="wallet:test-user",
        wallet_address="TestWalletAddress",
        username="TraderOne",
    )

    assert profile["user_id"] == "wallet:test-user"
    assert profile["username"] == "TraderOne"

    reloaded_service = get_user_profile_service(db_path=str(db_path))
    reloaded = reloaded_service.get_profile(
        user_id="wallet:test-user",
        wallet_address="TestWalletAddress",
    )

    assert reloaded["username"] == "TraderOne"
    assert reloaded["wallet_address"] == "TestWalletAddress"


@pytest.mark.parametrize("username", ["", "ab", "bad name", "*invalid*"])
def test_user_profile_service_rejects_invalid_usernames(tmp_path, username):
    service = get_user_profile_service(db_path=str(tmp_path / "user_profiles.json"))

    with pytest.raises(UsernameValidationError):
        service.set_username(
            user_id="wallet:test-user",
            wallet_address="TestWalletAddress",
            username=username,
        )
