import os
import random

from sqlalchemy import *
from sqlalchemy.pool import NullPool
from flask import Flask, request, render_template, g, redirect, Response

#for templates
tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)

#postgres uri
DATABASEURI = "postgresql://xw2337:f7b5g@104.196.175.120/postgres"

engine = create_engine(DATABASEURI)

#before each request we need to connect to database
@app.before_request
def before_request():
  try:
    g.conn = engine.connect()
  except:
    print "uh oh, problem connecting to database"
    import traceback; traceback.print_exc()
    g.conn = None

#after each request we need to close connection
@app.teardown_request
def teardown_request(exception):
  try:
    g.conn.close()
  except Exception as e:
    pass


#root path will go to index.html
@app.route('/')
def index():
  return render_template("index.html")

#for nearby function
@app.route('/nearby')
def nearby():
  foods = []
  trans = []
  cmd = 'SELECT * FROM food where distance<3';#find the foods whose distance is less than 3
  cursor = g.conn.execute(text(cmd))
  
  for result in cursor:
    foods.append([result[0],result[1],result[2],result[3],result[4],result[5]])
  cursor.close()
  random.shuffle(foods)
  if len(foods)>2:
    foods = foods[:1]

  cmd = 'SELECT * FROM transportation'
  cursor = g.conn.execute(text(cmd))
 
  for result in cursor:
    trans.append([result[0],result[1],result[2]])
  cursor.close()
  random.shuffle(trans)
  if len(trans)>2:
    trans = trans[:1]
  context = dict(foods = foods,trans=trans)
  return render_template("nearby.html",**context)

#insert user info
@app.route('/doSign',methods=['POST'])
def doSign():
  uid = request.form['uid']
  name = request.form['name']
  hobby = request.form['hobby']
  dateofbirth = request.form['dateofbirth']
  cmd = 'INSERT INTO users VALUES (:uid, :name,:hobby,:dateofbirth)'
  g.conn.execute(text(cmd), uid=uid,name=name,hobby=hobby,dateofbirth=dateofbirth)
  return redirect('/refer?hobby='+hobby)

#get refered activities by hobby or time
@app.route('/refer',methods=['GET'])
def refer():
  hobby = request.args['hobby']
  cmd = 'SELECT * FROM activities where type = :type or time=:time'
  cursor = g.conn.execute(text(cmd),type=hobby,time=hobby)
  acts = []
  for result in cursor:
    acts.append([result[0],result[1],result[2],result[3],result[4],result[5]])
  cursor.close()
  context = dict(data = acts)
  return render_template("activity.html",**context)

#add activity
@app.route('/add',methods=['GET'])
def add():
  return render_template("add.html")

@app.route('/addAct',methods=['POST'])
def addAct():
  name = request.form['name']
  location = request.form['location']
  time = request.form['time']
  contact = request.form['contact']
  type = request.form['type']
  ticket_price = request.form['ticket_price']
  cmd = 'INSERT INTO activities VALUES (:name, :location,:time,:contact,:type,:ticket_price)'
  #avoid sql injection
  g.conn.execute(text(cmd), name=name,location=location,time=time,contact=contact,type=type,ticket_price=ticket_price)
  return render_template('add.html')

@app.route('/login')
def login():
    return render_template("index.html")


if __name__ == "__main__":
  import click

  @click.command()
  @click.option('--debug', is_flag=True)
  @click.option('--threaded', is_flag=True)
  @click.argument('HOST', default='0.0.0.0')
  @click.argument('PORT', default=8111, type=int)
  def run(debug, threaded, host, port):
    HOST, PORT = host, port
    print "running on %s:%d" % (HOST, PORT)
    try:
      app.run(host=HOST, port=PORT, debug=debug, threaded=threaded)
    except:
      pass

  run()

