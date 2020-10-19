from django.conf import settings
from mozilla_django_oidc.auth import OIDCAuthenticationBackend
from mozilla_django_oidc.utils import absolutify

from ..models import BceidUser


class EDivorceKeycloakBackend(OIDCAuthenticationBackend):

    def verify_claims(self, claims):
        verified = super(EDivorceKeycloakBackend, self).verify_claims(claims)
        print(claims)

        return verified

    def create_user(self, claims):
        user = super(EDivorceKeycloakBackend, self).create_user(claims)

        user.first_name = claims.get('given_name', '')
        user.last_name = claims.get('family_name', '')
        user.display_name = "{} {}".format(user.first_name, user.last_name).strip()
        user.sm_user = claims.get('preferred_username', '')
        user.user_guid = claims.get('universal-id', '')
        user.save()

        return user

    def update_user(self, user, claims):
        user.first_name = claims.get('given_name', '')
        user.last_name = claims.get('family_name', '')
        user.display_name = "{} {}".format(user.first_name, user.last_name).strip()
        user.sm_user = claims.get('preferred_username', '')
        user.user_guid = claims.get('universal-id', '')
        user.save()

        return user

    def filter_users_by_claims(self, claims):
        user_guid = claims.get('universal-id')
        if not user_guid:
            return self.UserModel.objects.none()
        return self.UserModel.objects.filter(user_guid=user_guid)


def keycloak_logout(request):
    redirect_uri = absolutify(request, '/')

    return f'{settings.KEYCLOAK_LOGOUT}?redirect_uri={redirect_uri}'
