import os
import sqlite3

from datetime import datetime
from flask import Flask, jsonify, request, abort, render_template, send_from_directory
from flask_compress import Compress

app = Flask(__name__, static_url_path='')
Compress(app)
app.config.from_pyfile('app.cfg')
app.secret_key = app.config['SECRET_KEY']

db_filename = "updater.db"

page_header = "<link rel='stylesheet' href='/static/css/updater.css'>"

if "SOURCE_URL" in app.config:
  source_url = app.config['SOURCE_URL']
else:
  source_url = "https://github.com/invisiblek/simple_lineage_updater"
html_footer="<h3>Simple LineageOS Updater Server.<br/>Source <a href='" + source_url + "'>here</a>"

@app.route('/static/<path:path>')
def send_static(path):
  return send_from_directory('static', path)

@app.route('/api/v1/<string:device>/<string:romtype>/<string:incrementalversion>')
def index(device, romtype, incrementalversion):
  conn = sqlite3.connect(db_filename)
  c = conn.cursor()
  c.execute("SELECT * from rom where device = '{0}' and romtype = '{1}';".format(device, romtype))
  roms = c.fetchall()
  conn.commit()
  conn.close()
  zips = {}
  zips['response'] = []
  for r in roms:
    z = {}
    z['id'] = str(r[0])
    z['filename'] = r[1]
    z['datetime'] = r[2]
    z['device'] = r[3]
    z['version'] = r[4]
    z['romtype'] = r[5]
    z['md5sum'] = r[6]
    z['size'] = r[7]
    z['url'] = r[8]
    zips['response'].append(z)
  return jsonify(zips)

@app.route('/')
def root():
  conn = sqlite3.connect(db_filename)
  c = conn.cursor()
  c.execute("SELECT DISTINCT r.device, d.oem, d.name from rom r inner join device d on r.device = d.model order by r.device;")
  devices = c.fetchall()
  c.execute("SELECT * from rom r order by r.datetime desc limit 10;")
  recent_roms = c.fetchall()
  conn.commit()
  conn.close()

  h = "<html>"
  h = h + page_header
  if "PAGE_BANNER" in app.config:
    h = h + "<h1>welcome to invisiblek's lineage updater server</h1>"
  else:
    h = h + "<h1>welcome to the updater server</h1>"
  h = h + "<table class='main'>"
  h = h + "<tr><th>roms by device</th><th> most recent roms</th></tr>"
  h = h + "<tr><td>"
  h = h + "<table class='roms'>"
  for d in devices:
    h = h + "<tr><td><a href='/" + d[0] + "'>" + d[0] + "</a></td><td>" + d[1] + " " + d[2] + "</td></tr>"
  h = h + "</table>"
  h = h + "</td><td>"
  h = h + "<table class='recent'>"
  for r in recent_roms:
    size = str(round(r[7]/(1024*1024),2)) + "MB"
    h = h + "<tr><td><a href='" + r[8] + "'>" + r[1] + "</a></td><td>" + size + "</td><td>" + datetime.fromtimestamp(r[2]).strftime("%m/%d/%Y, %H:%M:%S") + "</td></tr>"
  h = h + "</table>"
  h = h + "</td></tr><table>"
  h = h + html_footer
  h = h + "</html>"
  return h

@app.route('/<string:device>')
def device(device):
  conn = sqlite3.connect(db_filename)
  c = conn.cursor()
  c.execute("SELECT r.filename, r.url, d.name, d.oem, d.model, r.romsize, r.datetime from rom r inner join device d on r.device = d.model where r.device = '" + device + "' order by r.filename desc;")
  roms = c.fetchall()
  conn.commit()
  conn.close()

  h = "<html>"
  h = h + page_header
  if len(roms) > 0:
    h = h + "<h1>" + roms[0][3] + " " + roms[0][2] + " (" + roms[0][4] + ")</h1>"
  h = h + "<table class='roms'>"
  for r in roms:
    size = str(round(r[5]/(1024*1024),2)) + "MB"
    h = h + "<tr><td><a href='" + r[1] + "'>" + r[0] + "</a></td><td>" + size + "</td><td>" + datetime.fromtimestamp(r[6]).strftime("%m/%d/%Y, %H:%M:%S") + "</td></tr>"
  h = h + "</table>"
  h = h + html_footer
  h = h + "</html>"
  return h
