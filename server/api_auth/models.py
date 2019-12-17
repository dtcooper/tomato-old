import secrets

from django.contrib.auth.models import AnonymousUser, User
from django.db import models


class ApiToken(models.Model):
    TOKEN_LENGTH = 36
    token = models.CharField(max_length=TOKEN_LENGTH, db_index=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    @classmethod
    def generate(cls, user):
        token = secrets.token_hex(cls.TOKEN_LENGTH // 2)
        cls.objects.update_or_create(user=user, defaults={'token': token})
        return token

    @classmethod
    def clear(cls, user):
        cls.objects.filter(user=user).delete()

    @classmethod
    def user_from_token(cls, token):
        try:
            return cls.objects.get(token=token).user
        except cls.DoesNotExist:
            return AnonymousUser()

    def __repr__(self):
        return f'<{self.__class__.__name__} {self.user.username}:{self.token!r}>'

    class Meta:
        db_table = 'api_tokens'
        unique_together = (('token', 'user'),)
