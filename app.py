#!/usr/bin/env python3
from os import path
import logging
from configparser import ConfigParser
import gettext

import kerberos
import bottle
from bottle import get, post, static_file, request, route, template
from bottle import SimpleTemplate


BASE_DIR = path.dirname(__file__)
STATIC_DIR = path.join(BASE_DIR, 'static')

config = ConfigParser()
config.read('settings.ini')

KERBEROS_REALM = config.get('app', 'kerberos_realm')
PROTECTED_USERS = data.split(',') if (data := config['app'].get('protected_users')) else []
LOG_LEVELS = {
    'debug': logging.DEBUG,
    'info': logging.INFO,
    'warning': logging.WARNING,
    'error': logging.ERROR,
    'critical': logging.CRITICAL
}
LOG_FORMAT = '%(asctime)s %(levelname)s: %(message)s'
LOG_LEVEL = LOG_LEVELS[config['logging'].get('level', 'warning')]
if log_filename := config['logging'].get('filename'):
    logging.basicConfig(format=LOG_FORMAT, level=LOG_LEVEL, filename=log_filename)
else:
    logging.basicConfig(format=LOG_FORMAT, level=LOG_LEVEL)

# Setting the web interface language
LANG_CODE = config['webpage'].get('language', 'en')
lang = gettext.translation('base', localedir='locales', languages=[LANG_CODE])
_ = lang.gettext


@route('/<filepath:path>')
def server_static(filepath):
    return static_file(filepath, root=STATIC_DIR)


def index_template(**kwargs):
    return template('index', **kwargs)


@get('/')
def get_index():
    # Adjust username value from query string: "/?username=alex"
    if username := request.query.username:
        return index_template(username=username)
    return index_template()


@post('/')
def post_index():

    def error(msg):
        return index_template(username=username, alerts=[('danger', msg)])

    requester_ip = request.remote_addr
    form = request.forms.getunicode
    username, old_password = form('username'), form('old-password')
    new_password, new_password_confirmation = form('new-password'), form('confirm-password')

    if not all((username, old_password, new_password, new_password_confirmation)):
        return error(_("Error — please fill in the required form fields"))

    if new_password != new_password_confirmation:
        return error(_("Error: password confirmation does not match the password"))

    if username in PROTECTED_USERS:
        logging.warning(
            f"[{requester_ip}] " +
            _("Attempting to change password of the protected user {username}").format(username=username)
        )
        return error(_("Error: the specified user is protected from changes"))

    try:
        username_with_realm = f"{username}@{KERBEROS_REALM}"
        result = kerberos.changePassword(username_with_realm, old_password, new_password)
    except kerberos.PwdChangeError as e:
        logging.warning(
            f"[{requester_ip}] " +
            _("Unsuccessful attempt to change password for user {username}: {e}").format(username=username, e=e)
        )

        if isinstance(e.args[0], tuple):
            err_msg, err_code = e.args[0]
        else:
            err_msg, err_code = e.args

        if err_code == -1765328378:
            return error(_("Error: the user with the specified name was not found"))
        elif err_code == -1765328366:
            return error(
                _("Error: the user's credentials were revoked — make sure that the user is not blocked in the domain"))
        elif err_code == -1765328360:
            return error(_("Authentication failed: make sure old password is correct"))
        elif err_code == 4:
            return error(_("Password change rejected. This could have happened due to its too frequent change or "
                           "its inconsistency with domain security policies"))
        else:
            return error(_("Unknown error: {err_msg} ({err_code})").format(err_msg=err_msg, err_code=err_code))

    if result:
        logging.info(
            f"[{requester_ip}] " +
            _("Password changed successfully for user {username}").format(username=username)
        )
        return index_template(alerts=[('success', _("The password was successfully changed"))])
    else:
        logging.warning(
            f"[{requester_ip}] " +
            _("The password was not changed for an unknown reason for the user {username}").format(username=username)
        )
        return error(_("Error: the password was not changed for an unknown reason — contact your administrator"))


SimpleTemplate.defaults.update(dict(config['webpage']))
SimpleTemplate.defaults.update(
    {
        'text_username': _("Username"),
        'text_old_password': _("Old password"),
        'text_new_password': _("New password"),
        'text_new_password_confirmation': _("Confirm new password"),
        'text_update_password': _("Update password")
    }
)

if __name__ == '__main__':
    bottle.run(**config['webserver'])
else:
    application = bottle.default_app()
