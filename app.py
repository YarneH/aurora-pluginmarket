from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
import os
# init app
app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
#Set path DB
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'pluginMarket.sqlite')
#Bind SQLAlchemy and Marshmellow to app
db = SQLAlchemy(app)
ma = Marshmallow(app)

# Model for in DB
class Plugin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    description = db.Column(db.String(500))
    version = db.Column(db.String(10))
    unique_name = db.Column(db.String(100), unique=True)

    def __init__(self,name,description,version,unique_name):
        self.name = name
        self.description = description
        self.version = version
        self.unique_name = unique_name

# What to expose on requests
class PluginSchema(ma.Schema):
    class Meta:
        fields = ('name','description','version','unique_name')

plugin_schema = PluginSchema()
plugin_market_schema = PluginSchema(many=True)

@app.route("/plugin", methods=["POST"])
def add_plugin():
    # the plugin in json to plugin object
    pj = request.json
    new_plugin = Plugin(pj["name"], pj["description"], pj["version"], pj["unique_name"])
    db.session.add(new_plugin)
    db.session.commit()
    return plugin_schema.jsonify(new_plugin)

@app.route("/plugin", methods=["GET"])
def get_plugins():
    all_plugins = Plugin.query.all()
    result = plugin_market_schema.dump(all_plugins)
    return plugin_market_schema.jsonify(result.data)

@app.route("/plugin/<id>", methods=["DELETE"])
def delete_plugin(id):
    plugin = Plugin.query.get(id)
    db.session.delete(plugin)
    db.session.commit()
    return plugin_schema.jsonify(plugin)
@app.route("/")
def hello():
    return "Hello World!"


if __name__ == '__main__':
    app.run(debug=True)
