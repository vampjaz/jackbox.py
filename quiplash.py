
from flask import Flask, redirect, request, make_response, render_template
import sqlite3, os, time, urllib, hashlib, random, threading
from flask_socketio import SocketIO, emit
from flask_qrcode import QRcode
from config import *

current_id = 0

def newid(): # make it easy to get a new unique numeric id for stuff in the database
	global current_id
	current_id += 1
	return current_id

db = sqlite3.connect(":memory:")
c = db.cursor()
c.execute("CREATE TABLE users (uid int, cookie text, nickname text, score int)")
c.execute("CREATE TABLE questions (qid int, question text)")
c.execute("CREATE TABLE assignedq (uid int, qid int)")
c.execute("CREATE TABLE answers (aid int, uid int, qid int, answer text)")
c.execute("CREATE TABLE votes (vid int, uid int, qid int, aid int)")

questions = open("questions.txt",'r').readlines()
for q in questions:
	c.execute("INSERT INTO questions VALUES (?,?)",(newid(),q))

app = Flask(__name__)
app.config['SECRET_KEY'] = 'sfsfkljtrsbltbrtyugfcv8898w7672482478472847092834750923k74059823470928734098273045702dfjefgjdfgjdfgyfgjdfsgheryju rty hj cvj ertyhesrthg asdf93847509274509230495029347584567456767456981092810293801978278'
socketio = SocketIO(app, async_mode=None)
qrcode = QRcode(app)


gamemode = 0
gametimer = 0
gamedatalock = threading.Lock()

def timerjob():
	while 1:
		time.sleep(1)
		global gamemode,gametimer
		print gamemode,gametimer
		with gamedatalock:
			if gamemode == 0: # waiting for users to join
				pass
			elif gamemode == 1: # start timer
				gamemode = 2
				gametimer = QUESTIONTIMER
			elif gamemode == 2:
				gametimer -= 1
				socketio.emit("timerupdate",{"time":gametimer},namespace='/')

bgthread = threading.Thread(target=timerjob)
bgthread.start()

@app.route('/')
def homepage():
	cookie = request.cookies.get('session_id','')
	if not cookie:
		cookie = hashlib.sha256(os.urandom(24)).hexdigest()
	resp = make_response(render_template('main.html'))
	resp.set_cookie('session_id',cookie)
	return resp

@app.route('/spectate') # this page is meant to be loaded by computers to give spectators an idea of what's going on
def spectate():
	return 'NYI'

@socketio.on('connected')
def handleconnect(msg):
	with gamedatalock:
		c = db.cursor()
		cookie = msg['cookie']
		c.execute("SELECT nickname FROM users WHERE cookie=?",(cookie,))
		nickname = c.fetchone()
		if nickname:
			nickname = nickname[0]
			emit('joined',{'nickname':nickname})
			c.execute("SELECT nickname FROM users")
			users = c.fetchall()
			emit('userlist',{'users':users,"canstart":len(users) >= QUESTIONSPERUSER}, broadcast=True)

@socketio.on('join')
def handlejoin(msg):
	with gamedatalock:
		c = db.cursor()
		nickname = msg['nickname']
		cookie = msg['cookie']
		emit('joined',{'nickname':nickname})
		c.execute("INSERT INTO users VALUES (?,?,?,0)",(newid(),cookie,nickname))
		c.execute("SELECT nickname FROM users")
		users = c.fetchall()
		emit('userlist',{'users':users,"canstart":len(users) >= QUESTIONSPERUSER}, broadcast=True)

@socketio.on('start')
def handlestart():
	emit("loading",broadcast=True)
	print "starting!"
	c = db.cursor()
	c.execute("SELECT uid FROM users")
	uids = [i[0] for i in c.fetchall()]
	c.execute("SELECT qid FROM questions")
	qids = [i[0] for i in c.fetchall()]
	random.shuffle(qids)
	questions = qids[:len(uids)] # random questions
	for i in range(QUESTIONSPERUSER): # basically we just shift the arrays to easily assign quesions to multiple users
		assigned = zip(uids,qids[-i:]+qids[:-i])
		c.executemany("INSERT INTO assignedq VALUES (?,?)",assigned)
	global gamemode
	gamemode = 1 # start timer
	emit("ready",broadcast=True)

@socketio.on('ready')
def handleready(msg):
	with gamedatalock:
		c = db.cursor()
		# send the user their first question
		cookie = msg['cookie']
		c.execute("SELECT uid FROM users WHERE cookie=?",(cookie,))
		user = c.fetchone()
		if not user:
			return
		uid = user[0]
		c.execute("SELECT qid FROM assignedq WHERE uid=?",(uid,))
		quest = c.fetchone()
		if not quest:
			emit("holdon")
			return
		qid = quest[0]
		c = db.cursor() # reset this so any questions in the fetch operation will be cleared
		c.execute("SELECT question FROM questions WHERE qid = ?",(qid,))
		question = c.fetchone()[0] # we assume this has to be in the database and don;t check if nothing is returned
		emit("question",{"question":question,"qid":qid})
		c.execute("DELETE FROM assignedq WHERE uid=? AND qid=?",(uid,qid)) # remove from db


@socketio.on('answer')
def handleanswer(msg):
	with gamedatalock:
		c = db.cursor()
		# record answer
		cookie = msg['cookie']
		c.execute("SELECT uid FROM users WHERE cookie=?",(cookie,))
		user = c.fetchone()
		if not user:
			return
		uid = user[0]
		qid = msg['qid']
		answer = msg['answer']
		c.execute("INSERT INTO answers VALUES (?,?,?,?)",(newid(),uid,qid,answer))
		# send user their next question if one exists
		c.execute("SELECT qid FROM assignedq WHERE uid=?",(uid,))
		quest = c.fetchone()
		if not quest:
			emit("holdon")
			return
		qid = quest[0]
		_ = c.fetchall() # reset this so any questions in the fetch operation will be cleared
		c.execute("SELECT question FROM questions WHERE qid = ?",(qid,))
		question = c.fetchone()[0] # we assume this has to be in the database and don;t check if nothing is returned
		print question
		emit("question",{"question":question,"qid":qid})
		c.execute("DELETE FROM assignedq WHERE uid=? AND qid=?",(uid,qid)) # remove from db



@socketio.on('vote')
def handlevote(msg):
	with gamedatalock:
		c = db.cursor()


@socketio.on('ping')
def handleping(msg):
	pass   # maybe make something here, not that we need to


if __name__ == '__main__':
	socketio.run(app)
