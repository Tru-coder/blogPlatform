from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError, InvalidHashError

from src.configs.settings import app_settings
from src.domain.app_user import AppUser
from src.exceptions.user_exceptions import UserPasswordIsMissingException
from src.logger.app_logger import AppLogger


class SecurityUtils:
    salt = app_settings.SALT

    ph = PasswordHasher(
        hash_len=app_settings.PASSWORD_HASH_LENGTH,
        salt_len=app_settings.PASSWORD_SALT_LENGTH
    )

    @classmethod
    def check_password(cls, user: AppUser, password_from_db: str, password_from_request: str) -> bool:
        # Verify password, raises exception if wrong.

        """
          :raises argon2.exceptions.VerifyMismatchError: If verification fails
              because *hash* is not valid for *password*.
          :raises argon2.exceptions.VerificationError: If verification fails for
              other reasons.
          :raises argon2.exceptions.InvalidHashError: If *hash* is so clearly
              invalid, that it couldn't be passed to Argon2.
        """

        try:
            return cls.ph.verify(
                hash=password_from_db,
                password=cls.complicate_user_password(user_password=password_from_request)
            )
        except VerifyMismatchError as e:
            # hash is not valid
            AppLogger.custom_logger.exception(
                msg=f"Несовпадение паролей для <User(login={user.login})>", exc_info=e)
            raise e

        except VerificationError as e:
            AppLogger.custom_logger.exception(
                msg=f"Введённый пароль не смог пройти проверку для <User(login={user.login})>",
                exc_info=e
            )
            raise e
        except InvalidHashError as e:
            AppLogger.custom_logger.exception(
                msg=f"Невалидный хеш для argon2id <User(login={user.login})>",
                exc_info=e
            )
            raise e

    @classmethod
    def rehash_user_password(cls, user: AppUser, user_password: str) -> str:
        # https://argon2-cffi.readthedocs.io/en/stable/howto.html

        rehashed_password = cls.ph.hash(
            cls.complicate_user_password(user_password=user_password)
        )
        AppLogger.custom_logger.info(
            msg=f"Пароль для <User(id={user.id}> был перехеширован"
        )
        return rehashed_password

    @classmethod
    def complicate_user_password(
            cls,
            user_password: str,
    ) -> bytes:
        """
        This function needed to protect user_password and prevent from databases with hashes
        Even if database will be fully leaked, user_password will be protected
        """

        return (
                user_password.encode("utf-8") +
                cls.salt.encode("utf-8")
        )

    @classmethod
    def hash_password(cls, user: AppUser) -> str:
        # https://argon2-cffi.readthedocs.io/en/stable/argon2.html
        # https://datatracker.ietf.org/doc/html/rfc9106.html

        if user.password is None:
            raise UserPasswordIsMissingException(f'У пользователя={user!r} отсутствует пароль')

        return cls.ph.hash(
            cls.complicate_user_password(
                user_password=user.password,
            ),
        )