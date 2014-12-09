import os
import sys
import datetime
import sqlite3
from contextlib import closing
from flask import Flask, request, session, g, redirect, url_for, abort, \
     render_template, flash


app = Flask(__name__)
app.config.from_object(__name__)

# Load default config and override config from an environment variable
app.config.update(dict(
    DATABASE=os.path.join(app.root_path, 'forum.db'),
    DEBUG=True,
    SECRET_KEY='development key',
    USERNAME='admin',
    PASSWORD='default'
))
app.config.from_envvar('FLASKR_SETTINGS', silent=True)

def connect_db():
    """Connects to the specific database."""
    rv = sqlite3.connect(app.config['DATABASE'])
    rv.row_factory = sqlite3.Row
    return rv

def init_db():
    with closing(connect_db()) as db:
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()   


@app.before_request
def before_request():
    g.db = connect_db()

@app.teardown_request
def teardown_request(exception):
    db = getattr(g, 'db', None)
    if db is not None:
        db.close()

@app.route('/')
def show_entries():
    cur = g.db.execute('select title, text, user from entries order by id desc')
    entries = [dict(title=row[0], text=row[1], user=row[2]) for row in cur.fetchall()]
    return render_template('show_entries.html', entries=entries)     



@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        print(request.form)
        cur = g.db.execute('select nickname, password from users order by id desc')
        users = [dict(nickname=row[0], password=row[1]) for row in cur.fetchall()]
        for i in users:
            print(i)
            if i['nickname']==request.form['username'] and i['password']==request.form['password']:
                session['logged_in'] = True
                session['user'] = request.form['username']
                flash('You were logged in')
                return redirect(url_for('show_entries'))
        else:
        	flash('No such users')
        	return render_template('login.html', error=error)
    return render_template('login.html', error=error)


@app.route('/register', methods=['GET', 'POST'])
def register():
	if request.method == 'POST':
		try:
			g.db.execute('insert into users (nickname, password, role) values (?, ?, ?)',
                 [request.form['nickname'], request.form['password'], 1])
			g.db.commit()
			session['logged_in'] = True
			session['user'] = request.form['nickname']
			session['role'] = 1
			return redirect(url_for('show_entries'))
		except:
			flash('Already registered')
			return render_template('register.html', error = None) 
	return render_template('register.html', error = None) 



@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('You were logged out')
    return redirect(url_for('show_entries'))

@app.route('/section=<sect>', methods=['GET', 'POST'])
def get_sections():
    topics = g.db.execute('select * from topics where sid=(?)', [sect])
    get_topics = topics.fetchall()
    topics = [dict(tid=row[0], tname=row[2], tdesc=row[3]) for row in get_topics]
    if request.method == 'POST':
        return redirect('/new_topic{0}'.format(sect))
    return render_template('section.html', topics=topics)


@app.route('/new_topic<sect>', methods=['GET', 'POST'])
def new_topic():
    if not session.get['logged_in']:
        abort(401)
    if request.method == 'POST':
        try:
            g.db.execute('insert into topics (sid, tname, tdesc) values (?, ?, ?)',
                 sect, [request.form['tname'], request.form['tdesc']])
            g.db.commit()
            tid = g.db.execute('select max(tid) from topics')
            tid = tid.fetchall()[0][0]
            cur = g.db.execute('select id from users where nickname=(?)',[user])
            user = cur.fetchall()[0][0]
            date = datetime.datetime.now()
            g.db.execute('insert into messages (uid, tid, time, msg) values (?, ?, ?, ?)',
                user, tid, date, request.form['msg'])
            return redirect(url_for('/topic={0}'.format(tid)))
        except:
            flash('Already registered')
            return render_template('new_topic.html', error = None)
    return render_template('new_topic.html', error = None) 



@app.route('/topic=<to>', methods=['GET', 'POST'])
def get_topic(to=None):
    c = g.db.execute('select * from topics where tid=(?)',[to])
    if list(c.fetchall()) == []:
        abort(401)
    if request.method == 'POST':
        user = session.get('user')
        date = datetime.datetime.now()
        cur = g.db.execute('select id from users where nickname=(?)',[user])
        user = cur.fetchall()
        g.db.execute('insert into messages (uid, tid, time, msg) values (?, ?, ?, ?)',
                 [user[0][0], to, date, request.form['msg']])
        g.db.commit()
        return redirect('/topic={0}'.format(to))
    cur = g.db.execute('select m.time, m.msg, u.nickname from (select * from messages where tid=(?)) as m join (select nickname, id from users) as u on u.id=m.uid',[to])
    c = cur.fetchall()
    print(len(c))
    messages = [dict(msg=row[1], time=row[0], user=row[2]) for row in c]
    print(len(messages))

    if not session.get['logged_in']:
        render_template('g_topic.html', messages=messages, error = None)
    return render_template('topic.html', messages=messages, error = None)
#150267

@app.route('/debug')
def debug():
    cur = g.db.execute('select * from users')
    users = cur.fetchall()
    cur = g.db.execute('select max(id) from users')
    c = cur.fetchall()
    print(c[0][0])
    for i in users:
        print(list(i))
    return redirect(url_for('show_entries'))


@app.route('/add', methods=['POST'])
def add_entry():
    if not session.get('logged_in'):
        abort(401)
    g.db.execute('insert into entries (title, text,  user) values (?, ?, ?)',
                 [request.form['title'], request.form['text'], session['user']])
    g.db.commit()
    flash('New entry was successfully posted')
    return redirect(url_for('show_entries'))       


if __name__ == '__main__':
    app.run(host='0.0.0.0')
