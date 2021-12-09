import hmac
import re
import werkzeug.security


SESSIONID = 'SESSIONID'

PASSWORD_MIN_LENGTH = 8
PASSWORD_MAX_LENGTH = 255

USERNAME_MAX_LENGTH = 255
EMAIL_MAX_LENGTH = 255

PBKDF2_ITERATIONS = 310_000
PBKDF2_HASH = 'sha256'

SALT_LENGTH = 32
SESSIONID_RAND_BYTES = 32
SESSION_LIFETIME = 24

MAX_LOGIN_ATTEMPTS = 10

OTP_LENGTH = 32

EMAIL_VERIFICATION_TOKEN_LIFETIME = 2   #hours
ACCOUNT_LOCK_DURATION = 2               #hours
PASSWORD_RESET_TOKEN_LIFETIME = 1       #hours


class OTP:
    EMAIL = 'email_token'
    ACCOUNT_LOCK = 'account_lock_token'
    PASSWORD_RESET = 'password_reset'

OTP_TYPES = (
    OTP.EMAIL,
    OTP.ACCOUNT_LOCK,
    OTP.PASSWORD_RESET
    )


def matching_tokens(src, cmp):
    return hmac.compare_digest(src, cmp)


def check_password_hash(password_hash, provided_password):
    return werkzeug.security.check_password_hash(password_hash, provided_password)


def generate_password_hash(password: str) -> str:
    method = f'pbkdf2:{PBKDF2_HASH}:{PBKDF2_ITERATIONS}'
    hash_ = werkzeug.security.generate_password_hash(password, method, SALT_LENGTH)
    return hash_


def valid_username(username: str) -> bool:
    if len(username) > USERNAME_MAX_LENGTH:
        return False
    username_re = re.compile(r'[a-z0-9_]+')
    return re.fullmatch(username_re, username) is not None


def valid_email(email: str) -> bool:
    if len(email) > EMAIL_MAX_LENGTH:
        return False
    email_re = re.compile(r'[a-zA-Z0-9]([a-zA-Z0-9.][a-zA-Z0-9]+)+@[a-zA-Z]+\.[a-zA-Z]+')
    return re.fullmatch(email_re, email) is not None


def valid_password(password: str) -> bool:
    if len(password) < PASSWORD_MIN_LENGTH:
        return False
    if len(password) > PASSWORD_MAX_LENGTH:
        return False
    password_exp = re.compile(r'[^\s]+')
    return re.fullmatch(password_exp, password)
