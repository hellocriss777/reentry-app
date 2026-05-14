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
    # ── Shared: What Changed & Resources ─────────────────────────────────────
    conn.executemany(
        'INSERT INTO what_changed (category,title,body,date) VALUES (?,?,?,?)',
        [
            ('Process', 'Standup moved to 9am daily',
             'The team now does a 15-min standup every morning at 9am via Teams. Optional Fridays.',
             '2026-04-10'),
            ('Tools', 'New design system launched in Q1',
             'Figma component library was rebuilt in March. See #design-system Slack channel for docs.',
             '2026-03-20'),
            ('Team', 'Two new team members joined',
             'Alex Kim (Engineer) and Priya Sharma (PM) joined in February. Say hi!',
             '2026-02-15'),
            ('Policy', 'Flexible work policy updated',
             'New hybrid policy allows up to 3 days WFH per week. Talk to your manager about your arrangement.',
             '2026-03-01'),
        ]
    )

    conn.executemany(
        'INSERT INTO resources (category,title,url) VALUES (?,?,?)',
        [
            ('Skills',    'LinkedIn Learning — Back to Work', 'https://linkedin.com/learning'),
            ('Wellbeing', 'EAP Mental Health Support',        '#'),
            ('Network',   'Women in Tech Slack community',    '#'),
            ('Policy',    'Flexible Work Policy (updated)',   '#'),
        ]
    )

    # ── Employee 1: Sarah Chen — Day 7 · low confidence · needs attention ─────
    # Return date: 2026-04-17  →  at demo date 2026-04-24 she is on Day 7
    e1 = conn.execute(
        'INSERT INTO employees (name,role,start_date,manager_name,buddy_name,buddy_email,manager_email) VALUES (?,?,?,?,?,?,?)',
        ('Sarah Chen', 'Senior Designer', '2026-04-17', 'Tom Walters', 'Lisa Morgan',
         'lisa.morgan@company.com', 'tom.walters@company.com')
    ).lastrowid

    conn.executemany(
        'INSERT INTO checklist_items (employee_id,week,text,done,added_by) VALUES (?,?,?,?,?)',
        [
            (e1, 1, 'Meet your buddy',           1, 'hr'),
            (e1, 1, 'IT setup complete',          1, 'hr'),
            (e1, 1, 'Team intro meeting',         1, 'hr'),
            (e1, 2, 'Complete weekly check-in',   0, 'hr'),
            (e1, 2, 'Skills refresh session',     0, 'hr'),
            (e1, 2, 'Review what changed digest', 0, 'hr'),
            (e1, 3, '30-day milestone review',    0, 'hr'),
        ]
    )
    # One check-in — low scores (avg 2.4) → triggers attention alert
    conn.execute(
        'INSERT INTO checkins (employee_id,date,belonging,confidence,inclusion,support,visibility,note) VALUES (?,?,?,?,?,?,?,?)',
        (e1, '18 Apr 2026', 2, 3, 2, 3, 2,
         'Feeling a bit overwhelmed but trying to stay positive.')
    )
    conn.execute(
        'INSERT INTO bias_nudges (employee_id,text,seen) VALUES (?,?,0)',
        (e1, "Sarah hasn't been invited to the last 2 planning meetings. Consider a direct invite.")
    )

    # ── Employee 2: Maya Patel — Day 31 · improving · on track ───────────────
    # Return date: 2026-03-24  →  at demo date 2026-04-24 she is on Day 31
    e2 = conn.execute(
        'INSERT INTO employees (name,role,start_date,manager_name,buddy_name,buddy_email,manager_email) VALUES (?,?,?,?,?,?,?)',
        ('Maya Patel', 'Product Manager', '2026-03-24', 'Rachel Brooks', 'Chloe Davis',
         'chloe.davis@company.com', 'rachel.brooks@company.com')
    ).lastrowid

    conn.executemany(
        'INSERT INTO checklist_items (employee_id,week,text,done,added_by) VALUES (?,?,?,?,?)',
        [
            (e2, 1, 'Meet your buddy',              1, 'hr'),
            (e2, 1, 'IT setup complete',             1, 'hr'),
            (e2, 1, 'Team intro meeting',            1, 'hr'),
            (e2, 2, 'Complete weekly check-in',      1, 'hr'),
            (e2, 2, 'Skills refresh session',        1, 'hr'),
            (e2, 2, 'Review what changed digest',    1, 'hr'),
            (e2, 3, '30-day milestone review',       1, 'hr'),
            (e2, 4, 'Lead a team meeting',           0, 'manager'),
            (e2, 5, 'Present to stakeholders',       0, 'manager'),
        ]
    )
    # Four check-ins — gradual improvement (2.8 → 3.0 → 3.4 → 3.8 avg)
    conn.executemany(
        'INSERT INTO checkins (employee_id,date,belonging,confidence,inclusion,support,visibility,note) VALUES (?,?,?,?,?,?,?,?)',
        [
            (e2, '25 Mar 2026', 3, 3, 3, 2, 3, 'First week was hard but the buddy system really helped.'),
            (e2, '1 Apr 2026',  3, 3, 3, 3, 3, 'Getting back into the rhythm.'),
            (e2, '8 Apr 2026',  4, 3, 4, 3, 3, 'Starting to feel more like myself again.'),
            (e2, '15 Apr 2026', 4, 4, 4, 4, 3, 'Had a great 1:1 with Rachel this week — feeling supported.'),
        ]
    )
    conn.execute(
        'INSERT INTO bias_nudges (employee_id,text,seen) VALUES (?,?,1)',
        (e2, "Maya has not been offered a visible project yet. Consider assigning one at the 30-day review.")
    )
    conn.execute(
        'INSERT INTO manager_feedback (employee_id,date,text) VALUES (?,?,?)',
        (e2, '10 Apr 2026', "You're doing a fantastic job getting back up to speed, Maya. Really proud of how you've handled the first few weeks.")
    )

    # ── Employee 3: Jess Thompson — Day 60 · thriving · high confidence ──────
    # Return date: 2026-02-23  →  at demo date 2026-04-24 she is on Day 60
    e3 = conn.execute(
        'INSERT INTO employees (name,role,start_date,manager_name,buddy_name,buddy_email,manager_email) VALUES (?,?,?,?,?,?,?)',
        ('Jess Thompson', 'UX Researcher', '2026-02-23', 'Tom Walters', 'Priya Sharma',
         'priya.sharma@company.com', 'tom.walters@company.com')
    ).lastrowid

    conn.executemany(
        'INSERT INTO checklist_items (employee_id,week,text,done,added_by) VALUES (?,?,?,?,?)',
        [
            (e3, 1, 'Meet your buddy',              1, 'hr'),
            (e3, 1, 'IT setup complete',             1, 'hr'),
            (e3, 1, 'Team intro meeting',            1, 'hr'),
            (e3, 2, 'Complete weekly check-in',      1, 'hr'),
            (e3, 2, 'Skills refresh session',        1, 'hr'),
            (e3, 2, 'Review what changed digest',    1, 'hr'),
            (e3, 3, '30-day milestone review',       1, 'hr'),
            (e3, 4, 'Lead user research session',    1, 'manager'),
            (e3, 5, '60-day formal review',          1, 'hr'),
            (e3, 6, 'Present research findings',     0, 'manager'),
        ]
    )
    # Six check-ins — strong recovery arc (2.6 → 3.0 → 3.4 → 3.8 → 4.0 → 4.4 avg)
    conn.executemany(
        'INSERT INTO checkins (employee_id,date,belonging,confidence,inclusion,support,visibility,note) VALUES (?,?,?,?,?,?,?,?)',
        [
            (e3, '24 Feb 2026', 3, 2, 3, 3, 2, 'Nervous but glad to be back.'),
            (e3, '3 Mar 2026',  3, 3, 3, 3, 3, 'Things are starting to click.'),
            (e3, '10 Mar 2026', 4, 3, 3, 4, 3, 'Buddy has been amazing this week.'),
            (e3, '17 Mar 2026', 4, 4, 4, 4, 3, 'Led my first session back — felt great.'),
            (e3, '24 Mar 2026', 4, 4, 4, 4, 4, '30-day review went really well.'),
            (e3, '14 Apr 2026', 5, 4, 5, 4, 4, 'Feeling fully integrated. 60-day review confirmed I\'m on track.'),
        ]
    )
    conn.execute(
        'INSERT INTO bias_nudges (employee_id,text,seen) VALUES (?,?,1)',
        (e3, "Jess is performing well — make sure she is being considered for the Q2 research lead role.")
    )
    conn.execute(
        'INSERT INTO manager_feedback (employee_id,date,text) VALUES (?,?,?)',
        (e3, '24 Mar 2026', "Jess — your 30-day review was outstanding. You've set the bar for how a return-to-work journey should look.")
    )
