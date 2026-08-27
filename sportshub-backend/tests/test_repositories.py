from app.db.models import Team, User, UserAlert, UserTeamPreference
from app.repositories.notifications import NotificationRepository
from app.repositories.team_preferences import TeamPreferenceRepository
from app.repositories.teams import TeamRepository
from app.repositories.users import UserRepository


def test_domain_repositories_persist_and_resolve_records(client):
    with client.app.state.session_factory() as session:
        users = UserRepository(session)
        teams = TeamRepository(session)
        preferences = TeamPreferenceRepository(session)
        notifications = NotificationRepository(session)

        user = User(
            email="repository@example.com",
            username="repository-fan",
            password_hash="test-only-hash",
        )
        team = Team(
            api_team_id=42,
            third_party_id="42",
            name="Arsenal",
            country="England",
            provider="sample",
        )
        users.add(user)
        teams.add(team)
        users.flush()
        preferences.add(UserTeamPreference(user_id=user.id, team_id=team.id))
        notifications.add(
            UserAlert(
                user_id=user.id,
                kind="repository_test",
                title="Repository test alert",
                summary="Persistence operations are isolated behind repositories.",
            )
        )
        users.commit()

        assert users.get(user.id) == user
        assert users.find_by_email(user.email) == user
        assert users.find_duplicate(user.email, "different-name") == user
        assert teams.find_by_provider_id(42) == team
        assert teams.find_by_supplied_id(team.id) == team
        assert teams.search_by_name("Ars") == [team]
        assert preferences.list_for_user(user.id) == [team]
        assert preferences.existing_team_ids(user.id, {team.id}) == {team.id}
        assert notifications.unread_count(user.id) == 1
        assert notifications.total_count(user.id) == 1

        assert notifications.mark_all_read(user.id) == 1
        notifications.commit()
        assert notifications.unread_count(user.id) == 0
