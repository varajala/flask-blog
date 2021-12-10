import microtest
import flask_blog.security.utils as utils


@microtest.test
def test_username_validation():
    valid_usernames = [
        'user',
        'u_s_e_r',
        'user100',
        'abcdefghijklmnopqrstuwxyz_0123456789'
    ]
    for username in valid_usernames:
        assert utils.valid_username(username), ('Valid username did not pass validation: ', username)

    invalid_usernames = [
        'User',
        'user-1',
        'user!',
        'user?',
        'user@user',
        'user&user',
        'user|user',
        'ŋʒəəßðəßð',
        ''.join([ str('a') for _ in range(257) ]),
        '',
        ' user',
        'user ',
        'user user',
    ]
    for username in invalid_usernames:
        assert not utils.valid_username(username), ('Invalid username passed validation: ', username)


@microtest.test
def test_password_validation():
    valid_passwords = [
        '12345678',
        'aAaAaAAAaaa',
        'əßðəhəf?!"%&¤#/((=/&/&/&&)))|<>;,.:ßəðəßðŊfhðf',
    ]
    for password in valid_passwords:
        assert utils.valid_password(password), ('Valid password did not pass validation: ', password)

    invalid_passwords = [
        '124567',
        ''.join([ str('1') for _ in range(257) ]),
        '  asdasdasd',
        'asdasdasd   ',
        'a   sdas  dasd',
        '\tasdadasd',
        '\nasdadasd',
        '\tasdadasd',
        '\rasdadasd',
        'asdadasd\t',
        'asdadasd\n',
        'asdadasd\r',
        'asda\tdasd',
        'asda\ndasd',
        'asda\rdasd',
    ]
    for password in invalid_passwords:
        assert not utils.valid_password(password), ('Invalid password passed validation: ', password)


@microtest.test
def test_email_validation():
    valid_emails = [
        'test@gmail.com',
        'test.testing@gmail.com',
        'test.testing.test@gmail.com',
        'Tester.Tester@t.t',
        'abcdefghijklmonpqrstuvwxyz0123456789@domain.end',
        'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789@domain.end',
    ]
    for email in valid_emails:
        assert utils.valid_email(email), ('Valid password did not pass validation: ', email)

    invalid_emails = [
        '.test@gmail.com',
        'test.@gmail.com',
        'te..st@gmail.com',
        'äää@gmail.com',
        '"asd"#*@gmail.com',
        '"asd&%!?*@gmail.com',
        'test.com',
        'test@com',
        'test+test@com',
        'test@+com',
        'test@com.',
        'test@a11.com',
        'test@gmail.c1',
        ''.join([ str('a') for _ in range(250) ]) + '@gmail.com',
    ]
    for email in invalid_emails:
        assert not utils.valid_email(email), ('Invalid password passed validation: ', email)
