import sqlite3, os

DB_PATH = os.environ.get('DATABASE_PATH', 'reentry.db')

def open_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys = ON')
    return conn

def get_db():
    from flask import g
    if not hasattr(g, 'db'):
        g.db = open_db()
    return g.db

def init_db():
    conn = open_db()
    conn.executescript('''
        CREATE TABLE IF NOT EXISTS employees (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            name          TEXT NOT NULL,
            role          TEXT,
            start_date    TEXT,
            manager_name  TEXT,
            buddy_name    TEXT,
            buddy_email   TEXT,
            manager_email TEXT
        );
        CREATE TABLE IF NOT EXISTS checkins (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER,
            date        TEXT,
            belonging   INTEGER,
            confidence  INTEGER,
            inclusion   INTEGER,
            support     INTEGER,
            visibility  INTEGER,
            note        TEXT DEFAULT '',
            FOREIGN KEY (employee_id) REFERENCES employees(id)
        );
        CREATE TABLE IF NOT EXISTS checklist_items (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER,
            week        INTEGER,
            text        TEXT,
            done        INTEGER DEFAULT 0,
            added_by    TEXT DEFAULT 'hr',
            FOREIGN KEY (employee_id) REFERENCES employees(id)
        );
        CREATE TABLE IF NOT EXISTS what_changed (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT,
            title    TEXT,
            body     TEXT,
            date     TEXT
        );
        CREATE TABLE IF NOT EXISTS manager_feedback (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER,
            date        TEXT,
            text        TEXT,
            FOREIGN KEY (employee_id) REFERENCES employees(id)
        );
        CREATE TABLE IF NOT EXISTS manager_notes (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER,
            date        TEXT,
            text        TEXT,
            FOREIGN KEY (employee_id) REFERENCES employees(id)
        );
        CREATE TABLE IF NOT EXISTS manager_actions (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER,
            date        TEXT,
            text        TEXT,
            done        INTEGER DEFAULT 0,
            FOREIGN KEY (employee_id) REFERENCES employees(id)
        );
        CREATE TABLE IF NOT EXISTS bias_nudges (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER,
            text        TEXT,
            seen        INTEGER DEFAULT 0,
            FOREIGN KEY (employee_id) REFERENCES employees(id)
        );
        CREATE TABLE IF NOT EXISTS resources (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT,
            title    TEXT,
            url      TEXT
        );
        CREATE TABLE IF NOT EXISTS diary_entries (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER,
            date        TEXT,
            text        TEXT,
            mood        TEXT DEFAULT '',
            FOREIGN KEY (employee_id) REFERENCES employees(id)
        );
        CREATE TABLE IF NOT EXISTS settings (
            key   TEXT PRIMARY KEY,
            value TEXT
        );
    ''')

    if conn.execute('SELECT COUNT(*) FROM employees').fetchone()[0] == 0:
        _seed(conn)

    conn.commit()
    conn.close()

def _seed(conn):
    cur = conn.execute(
        'INSERT INTO employees (name,role,start_date,manager_name,buddy_name,buddy_email,manager_email) VALUES (?,?,?,?,?,?,?)',
        ('Sarah Chen','Senior Designer','2026-04-17','Tom Walters','Lisa Morgan',
         'lisa.morgan@company.com','tom.walters@company.com')
    )
    eid = cur.lastrowid

    conn.executemany(
        'INSERT INTO checklist_items (employee_id,week,text,done,added_by) VALUES (?,?,?,?,?)',
        [
            (eid,1,'Meet your buddy',1,'hr'),
            (eid,1,'IT setup complete',1,'hr'),
            (eid,1,'Team intro meeting',1,'hr'),
            (eid,2,'Complete weekly check-in',0,'hr'),
            (eid,2,'Skills refresh session',0,'hr'),
            (eid,2,'Review what changed digest',0,'hr'),
            (eid,3,'30-day milestone review',0,'hr'),
        ]
    )

    conn.executemany(
        'INSERT INTO what_changed (category,title,body,date) VALUES (?,?,?,?)',
        [
            ('Process','Standup moved to 9am daily',
             'The team now does a 15-min standup every morning at 9am via Teams. Optional Fridays.',
             '2026-04-10'),
            ('Tools','New design system launched in Q1',
             'Figma component library was rebuilt in March. See #design-system Slack channel for docs.',
             '2026-03-20'),
            ('Team','Two new team members joined',
             'Alex Kim (Engineer) and Priya Sharma (PM) joined in February. Say hi!',
             '2026-02-15'),
        ]
    )

    conn.executemany(
        'INSERT INTO resources (category,title,url) VALUES (?,?,?)',
        [
            ('Skills','LinkedIn Learning — Back to Work','https://linkedin.com/learning'),
            ('Wellbeing','EAP Mental Health Support','#'),
            ('Network','Women in Tech Slack community','#'),
        ]
    )

    conn.execute(
        'INSERT INTO bias_nudges (employee_id,text,seen) VALUES (?,?,0)',
        (eid, "Sarah hasn't been invited to the last 2 planning meetings. Consider a direct invite.")
    )
