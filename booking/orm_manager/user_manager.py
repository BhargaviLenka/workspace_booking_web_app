from django.core.exceptions import ObjectDoesNotExist

from booking.models import User


class UserManager:

    @staticmethod
    def create_user(validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user

    @staticmethod
    def deactivate_user(user_id):
        try:
            user = User.objects.get(id=user_id)
            if not user.is_active:
                return {"error": "User is already inactive."}

            user.is_active = False
            user.save()
            return {"success": "User deactivated successfully."}

        except ObjectDoesNotExist:
            return {"error": "User not found."}
        except Exception as e:
            return {"error": str(e)}

    @staticmethod
    def activate_user(user_id):
        try:
            user = User.objects.get(id=user_id)
            if user.is_active:
                return {"error": "User is already active."}

            user.is_active = True
            user.save()
            return {"success": "User activated successfully."}

        except ObjectDoesNotExist:
            return {"error": "User not found."}
        except Exception as e:
            return {"error": str(e)}
