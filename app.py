from flask import Flask, request, jsonify, render_template, redirect, flash
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from werkzeug.utils import secure_filename
from config import Config
import re
import os

# init app
app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
app.config.from_object(Config)
# Set path DB
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'pluginMarket.sqlite')
# Bind SQLAlchemy and Marshmellow to app
db = SQLAlchemy(app)
ma = Marshmallow(app)


# Model for in DB
class Plugin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    description = db.Column(db.String(500))
    version_code = db.Column(db.String(10))
    unique_name = db.Column(db.String(100), unique=True)
    plugin_logo = db.Column(db.String(100))
    internal_services = db.Column(db.String(500))
    apk_location = db.Column(db.String(100))
    creator = db.Column(db.String(100))

    def __init__(self, name, description, version_code, unique_name, plugin_logo, internal_services, apk_location,
                 creator):
        self.name = name
        self.description = description
        self.version_code = version_code
        self.unique_name = unique_name
        self.plugin_logo = plugin_logo
        self.internal_services = internal_services
        self.apk_location = apk_location
        self.creator = creator


# What to expose on requests
class PluginSchema(ma.Schema):
    class Meta:
        fields = (
            'id', 'name', 'description', 'version_code', 'unique_name', 'plugin_logo', 'internal_services',
            'apk_location', 'creator')


plugin_schema = PluginSchema()
plugin_market_schema = PluginSchema(many=True)


@app.route("/plugin", methods=["POST"])
def add_plugin():
    # the plugin in json to plugin object
    pj = request.json
    token = valid_token(pj["token"])
    if token[0]:
        new_plugin = Plugin(pj["name"], pj["description"], pj["version_code"], pj["unique_name"], pj["plugin_logo"],
                            pj["internal_services"], pj["apk_location"], token[1])
        db.session.add(new_plugin)
        db.session.commit()
        return plugin_schema.jsonify(new_plugin)


@app.route("/plugin", methods=["GET"])
def get_plugins():
    all_plugins = Plugin.query.all()
    result = plugin_market_schema.dump(all_plugins)
    return plugin_market_schema.jsonify(result.data)


@app.route("/plugin/<id>", methods=["GET"])
def get_plugin(id):
    plugin = Plugin.query.get(id)
    return plugin_schema.jsonify(plugin)


@app.route("/plugin/<id>", methods=["DELETE"])
def delete_plugin(id):
    plugin = Plugin.query.get(id)
    db.session.delete(plugin)
    db.session.commit()
    return plugin_schema.jsonify(plugin)


@app.route("/")
def hello():
    return "Hello World!"


def valid_token(token):
    for line in open(basedir + '\\tokens.txt'):
        line = line.strip()
        [user, user_token] = re.split(' *\|\| *', line)
        if token == user_token:
            return [True, user]
    return [False, None]


@app.route("/plugin_create", methods=["GET", "POST"])
def plugin_creator():
    if request.method == "GET":
        return render_template("create_plugin.html")
    validated_token = valid_token(request.form['token'])
    if request.method == "POST" and validated_token[0]:
        name = request.form['name']
        description = request.form['description']
        version_code = request.form['version_code']
        unique_name = request.form['unique_name']
        internal_services = request.form['internal_services']
        if request.form['plugin_logo'] != "":
            plugin_logo = request.form['plugin_logo']
        else:
            logo = request.files['plugin_logo_file']
            if logo.filename == '':
                flash('No selected logo')
                return redirect(request.url)
            if logo and allowed_file(logo.filename, Config.ALLOWED_LOGO):
                filename = secure_filename(logo.filename)
                logo.save(os.path.join(basedir, "logos", filename))
                plugin_logo = "aurora-files.ml/logos/" + filename
            else:
                flash('No selected file')
                return redirect(request.url)
        if request.form['apk_location'] != "":
            apk_location = request.form['plugin_logo']
        else:
            apk = request.files['plugin_apk_file']
            if apk.filename == '':
                flash('No selected app')
                return redirect(request.url)
            if apk and allowed_file(apk.filename, Config.ALLOWED_APK):
                filename = secure_filename(apk.filename)
                apk.save(os.path.join(basedir, "apk", filename))
                apk_location = "aurora-files.ml/apk/" + filename
            else:
                flash('No selected file')
                return redirect(request.url)
        new_plugin = Plugin(name, description, version_code, unique_name, plugin_logo, internal_services,
                            apk_location, validated_token[1])
        db.session.add(new_plugin)
        db.session.commit()
        return plugin_schema.jsonify(new_plugin)


def allowed_file(filename, extensions):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in extensions


@app.errorhandler(404)
def page_not_found(e):
    return jsonify(error=404, text=str(e)), 404


if __name__ == '__main__':
    app.run(debug=True)
