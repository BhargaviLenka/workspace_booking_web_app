from django.core.exceptions import ObjectDoesNotExist

from booking.models import Team, User, TeamMember


class TeamManager:

    @staticmethod
    def create_team(validated_data):
        team = Team.objects.create(**validated_data)
        return team

    @staticmethod
    def add_user_to_team(team_id, user_id):
        try:
            team = Team.objects.get(id=team_id)
            user = User.objects.get(id=user_id)

            if TeamMember.objects.filter(team=team, user=user).exists():
                return {"error": "User already in team."}

            TeamMember.objects.create(team=team, user=user)
            return {"success": "User added to team."}

        except ObjectDoesNotExist:
            return {"error": "Team or User not found."}
        except Exception as e:
            return {"error": str(e)}

    @staticmethod
    def remove_user_from_team(team_id, user_id):
        try:
            team_member = TeamMember.objects.get(team_id=team_id, user_id=user_id)
            team_member.delete()
            return {"success": "User removed from team."}

        except TeamMember.DoesNotExist:
            return {"error": "User is not part of this team."}
        except Exception as e:
            return {"error": str(e)}
