from flask import Flask, request, jsonify, render_template, redirect, flash
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from werkzeug.utils import secure_filename
from pluginmarket.config import Config
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
home = "https://pluginmarket.aurora-files.ml"


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

# For receiving one plugin
plugin_schema = PluginSchema()
# For receiving all the plugins
plugin_market_schema = PluginSchema(many=True)

# Create a new plugin by posting here
@app.route("/plugin", methods=["POST"])
def add_plugin():
    # The plugin in json to plugin object
    pj = request.json
    token = valid_token(pj["token"])
    # Allow if the token is valid
    if token[0]:
        new_plugin = Plugin(pj["name"], pj["description"], pj["version_code"], pj["unique_name"], pj["plugin_logo"],
                            pj["internal_services"], pj["apk_location"], token[1])
        db.session.add(new_plugin)
        db.session.commit()
        return plugin_schema.jsonify(new_plugin)

# Get all plugins
@app.route("/plugin", methods=["GET"])
def get_plugins():
    all_plugins = Plugin.query.all()
    result = plugin_market_schema.dump(all_plugins)
    return plugin_market_schema.jsonify(result.data)

# Get the plugin with id id in json
@app.route("/plugin/<id>", methods=["GET"])
def get_plugin(id):
    plugin = Plugin.query.get(id)
    return plugin_schema.jsonify(plugin)

# Delete the plugin with id id
def delete_plugin(id):
    plugin = Plugin.query.get(id)
    db.session.delete(plugin)
    db.session.commit()
    return plugin_schema.jsonify(plugin)

# Direct the user to the needed links
@app.route("/")
def home():
    return jsonify(plugins=home + "/plugin", create_plugin=home + "/create_plugin",
                   edit_plugin=home + "/edit_plugin/<id>"), 200

# Check if the token is valid, returns if valid and the user of the token
def valid_token(token, user_put=None):
    for line in open(basedir + '/tokens.txt'):
        line = line.strip()
        [user, user_token] = re.split(' *\|\| *', line)

        if token == user_token:
            if user_put is None or user == user_put:
                return [True, user]
    return [False, None]

# Delete the plugin with id ID
@app.route("/delete_plugin/<id>", methods=["POST"])
def plugin_delete(id):
    plugin = Plugin.query.get(id)
    validated_token = valid_token(request.form['token'], plugin.creator)
    # check if token is valid
    if request.method == "POST" and validated_token[0]:
        return delete_plugin(id)
    return jsonify(error=401, text="Faulty token"), 401

# Edit a plugin (As well UI as processing
@app.route("/edit_plugin/<id>", methods=["GET", "POST"])
def plugin_edit(id):
    plugin = Plugin.query.get(id)
    # Get the template for editing the plugin
    if request.method == "GET":
        return render_template("create_plugin.html", plugin=plugin)
    # If submit is clicked
    if request.method == "POST":
        validated_token = valid_token(request.form['token'], plugin.creator)
        if request.method == "POST" and validated_token[0]:
            plugin.name = request.form['name']
            plugin.description = request.form['description']
            plugin.version_code = request.form['version_code']
            plugin.unique_name = request.form['unique_name']
            plugin.internal_services = request.form['internal_services']
            # Check if the string of the logo is nog empty
            if request.form['plugin_logo'] != "":
                # Use the logi string
                plugin.plugin_logo = request.form['plugin_logo']
            else:
                # Check if image atached
                logo = request.files['plugin_logo_file']
                if logo.filename == '':
                    flash('No selected logo')
                    return redirect(request.url)
                # Check if the logo is an image and exists
                if logo and allowed_file(logo.filename, Config.ALLOWED_LOGO):
                    filename = secure_filename(logo.filename)
                    logo.save("/var/www/logos/" + filename)
                    plugin.plugin_logo = "https://aurora-files.ml/logos/" + filename
                else:
                    flash('No selected file')
                    return redirect(request.url)
            if request.form['apk_location'] != "":
                plugin.apk_location = request.form['apk_location']
            else:
                apk = request.files['plugin_apk_file']
                if apk.filename == '':
                    flash('No selected app')
                    return redirect(request.url)
                # Check if the apk is an apk and exists
                if apk and allowed_file(apk.filename, Config.ALLOWED_APK):
                    filename = secure_filename(apk.filename)
                    apk.save("/var/www/apk/" + filename)
                    plugin.apk_location = "https://aurora-files.ml/apk/" + filename
                else:
                    flash('No selected file')
                    return redirect(request.url)

            db.session.commit()
            return plugin_schema.jsonify(plugin)

# Create a new plugin (same as edit plugin)
@app.route("/create_plugin", methods=["GET", "POST"])
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
                logo.save("/var/www/logos/" + filename)
                plugin_logo = "https://aurora-files.ml/logos/" + filename
            else:
                flash('No selected file')
                return redirect(request.url)
        if request.form['apk_location'] != "":
            apk_location = request.form['apk_location']
        else:
            apk = request.files['plugin_apk_file']
            if apk.filename == '':
                flash('No selected app')
                return redirect(request.url)
            if apk and allowed_file(apk.filename, Config.ALLOWED_APK):
                filename = secure_filename(apk.filename)
                apk.save("/var/www/apk/" + filename)
                apk_location = "https://aurora-files.ml/apk/" + filename
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
