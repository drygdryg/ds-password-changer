#!/usr/bin/env python3
from os import path
import logging
from configparser import ConfigParser

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
        return error("Ошибка — заполните требуемые поля формы")

    if new_password != new_password_confirmation:
        return error("Ошибка: подтверждение пароля не совпадает с паролем")

    if username in PROTECTED_USERS:
        logging.warning(f"[{requester_ip}] Попытка изменить пароль защищённого пользователя {username}")
        return error("Ошибка: указанный пользователь защищён от изменений")

    try:
        username_with_realm = f"{username}@{KERBEROS_REALM}"
        result = kerberos.changePassword(username_with_realm, old_password, new_password)
    except kerberos.PwdChangeError as e:
        logging.warning(f"[{requester_ip}] Неудачная попытка изменить пароль для пользователя {username}: {e}")

        if isinstance(e.args[0], tuple):
            err_msg, err_code = e.args[0]
        else:
            err_msg, err_code = e.args

        if err_code == -1765328378:
            return error("Ошибка: пользователь с указанным именем не найден")
        elif err_code == -1765328366:
            return error("Ошибка: учётные данные пользователя были отозваны — "
                         "убедитесь, что пользователь не заблокирован в домене")
        elif err_code == -1765328360:
            return error("Ошибка аутентификации: убедитесь, что старый пароль введён верно")
        elif err_code == 4:
            return error("Изменение пароля отклонено. Это могло произойти по причине слишком частой его смены "
                         "либо его несоответствия политикам безопасности домена")
        else:
            return error(f"Неизвестная ошибка: {err_msg} ({err_code})")

    if result:
        logging.info(f"[{requester_ip}] Пароль успешно изменён для пользователя {username}")
        return index_template(alerts=[('success', "Пароль успешно изменён")])
    else:
        logging.warning(f"[{requester_ip}] Пароль не был изменён по неизвестной причине для пользователя {username}")
        return error(f"Ошибка: пароль не был изменён по неизвестной причине — обратитесь к администратору")


SimpleTemplate.defaults.update(dict(config['webpage']))

if __name__ == '__main__':
    bottle.run(**config['webserver'])
else:
    application = bottle.default_app()
