import os


class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'our_badass_pluginmarket'
    UPLOAD_FOLDER = "/var/www"
    ALLOWED_LOGO = set(['png', 'jpg', 'jpeg', 'ico'])
    ALLOWED_APK = set(['apk'])
