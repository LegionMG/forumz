import os
import sys
import datetime
import sqlite3
from hashlib import md5
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

@app.route('/', methods=['GET','POST'])
def glagne():
    cur = g.db.execute('select sid, sname, sdesc from sections')
    c = cur.fetchall()
    print(list(c[0]))
    sections = [dict(name=row[1], id=row[0], desc=row[2]) for row in c]
    return render_template('main.html', sections=sections, error = None)


@app.route('/bloge')
def show_entries():
    cur = g.db.execute('select title, text, user from entries order by id desc')
    entries = [dict(title=row[0], text=row[1], user=row[2]) for row in cur.fetchall()]
    return render_template('show_entries.html', entries=entries)     



@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        print(request.form)
        cur = g.db.execute('select nickname, password, role from users order by id desc')
        users = [dict(nickname=row[0], password=row[1], role=row[2]) for row in cur.fetchall()]
        for i in users:
            if i['nickname']==request.form['username'] and i['password']==md5(request.form['password'].encode('utf-8')).hexdigest():
                session['logged_in'] = True
                session['user'] = request.form['username']
                if i['role'] == 0:
                    session['admin'] = True
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
                 [request.form['nickname'], md5(request.form['password'].encode('utf-8')).hexdigest(), 1])
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
    session.pop('admin', None)
    flash('You were logged out')
    return redirect(url_for('show_entries'))



@app.route('/section=<sect>', methods=['GET', 'POST'])
def get_sections(sect):
    topics = g.db.execute('select * from topics where sid=(?)', [sect])
    get_topics = topics.fetchall()
    topics = [dict(tid=row[0], tname=row[2], tdesc=row[3]) for row in get_topics]
    return render_template('section.html', topics=topics)


@app.route('/add_section', methods=['GET', 'POST'])
def add_section():
    if not session.get('logged_in'):
        abort(401)
    if request.method == 'POST':
        try:
            print(request.form['sname'], request.form['sdesc'])
            g.db.execute('insert into sections (sname, sdesc) values (?, ?)',
                 [request.form['sname'], request.form['sdesc']])
            g.db.commit()
            return redirect(url_for('glagne'))
        except Exception as err:
            flash('Something is wrong')
            print("lol", err)
            return  render_template('new_section.html', error = None)
    return render_template('new_section.html', error = None) 

@app.route('/new_topic=<sect>', methods=['GET', 'POST'])
def new_topic(sect):
    if not session.get('logged_in'):
        abort(401)
    if request.method == 'POST':
        #try:
            g.db.execute('insert into topics (sid, tname, tdesc) values (?, ?, ?)',
                 [sect, request.form['tname'], request.form['tdesc']])
            g.db.commit()
            tid = g.db.execute('select max(tid) from topics')
            tid = tid.fetchall()[0][0]
            cur = g.db.execute('select id from users where nickname=(?)',[session.get('user')])
            user = cur.fetchall()[0][0]
            date = datetime.datetime.now()
            g.db.execute('insert into messages (uid, tid, time, msg) values (?, ?, ?, ?)',
                [user, tid, date, request.form['msg']])
            return redirect(url_for('get_topic', to=tid))
            '''except:
            flash('Something is wrong')
            return render_template('new_topic.html', error = None)'''
    return render_template('new_topic.html', sect=sect, error = None) 



@app.route('/topic=<to>', methods=['GET', 'POST'])
def get_topic(to):
    c = g.db.execute('select * from topics where tid=(?)',[to])
    print(to)
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
    messages = [dict(msg=row[1], time=row[0], user=row[2]) for row in c]
    return render_template('topic.html', topic=to, messages=messages, error = None)
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


@app.route('/adminnn')
def add_admin():
    g.db.execute('insert into users (nickname, password, role) values (?,?,?)',
        ['Admin', md5('default'.encode('utf-8')).hexdigest(), 0])
    g.db.commit()
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
