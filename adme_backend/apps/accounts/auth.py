"""
RD CORE-1: "Login accepts email/phone + password".

Django's ModelBackend authenticates on USERNAME_FIELD only. This backend lets
the submitted identifier be a username, an email, or a phone number, then
falls back to the default behaviour. Wire it in via AUTHENTICATION_BACKENDS
in config/settings/base.py.
"""
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.db.models import Q

UserModel = get_user_model()


class EmailOrPhoneBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None:
            username = kwargs.get(UserModel.USERNAME_FIELD)
        if username is None or password is None:
            return None

        try:
            user = UserModel.objects.get(
                Q(username__iexact=username)
                | Q(email__iexact=username)
                | Q(phone=username)
            )
        except UserModel.DoesNotExist:
            # Run the default hasher once to reduce timing differences.
            UserModel().set_password(password)
            return None
        except UserModel.MultipleObjectsReturned:
            return None

        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
