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
    # ── What Changed digest ───────────────────────────────────────────────────
    conn.executemany(
        'INSERT INTO what_changed (category,title,body,date) VALUES (?,?,?,?)',
        [
            ('Process', 'Standup moved to 9am daily',
             'The team now does a 15-min standup every morning at 9am via Teams. Optional Fridays.',
             '2026-04-10'),
            ('Tools', 'New design system launched in Q1',
             'Figma component library was rebuilt in March. See #design-system Slack channel for docs and templates.',
             '2026-03-20'),
            ('Team', 'Two new team members joined',
             'Alex Kim (Engineer) and Priya Sharma (PM) joined in February. Great people to know.',
             '2026-02-15'),
            ('Policy', 'Flexible work policy updated',
             'New hybrid policy allows up to 3 days WFH per week. Talk to your manager about your arrangement.',
             '2026-03-01'),
            ('Tools', 'Slack workspace reorganised',
             'Several channels were merged or archived. Key channels to join: #general, #product, #design-system, #watercooler.',
             '2026-04-01'),
        ]
    )

    # ── Resources (PDR-aligned categories) ───────────────────────────────────
    conn.executemany(
        'INSERT INTO resources (category,title,url) VALUES (?,?,?)',
        [
            # Employee-facing
            ('Confidence & visibility',   'How to re-establish your presence in meetings',               '#'),
            ('Confidence & visibility',   'Speaking up after time away: a practical guide',             '#'),
            ('Team relationships',        'Rebuilding trust and rapport after a career break',           '#'),
            ('Team relationships',        'How to reconnect one-on-one without it feeling awkward',      '#'),
            ('Tools & technology',        'Getting up to speed: what changed while you were away',      '#'),
            ('Tools & technology',        'Figma 2025 — what\'s new and what you need to know',         '#'),
            ('Career progression',        'Navigating performance conversations after a break',          '#'),
            ('Career progression',        'How to articulate the value of your time away',              '#'),
            ('Identity & belonging',      'Returning to work: it\'s normal to feel like an outsider',  '#'),
            ('Workload & wellbeing',      'Managing re-entry fatigue in the first 30 days',             '#'),
            ('Workload & wellbeing',      'EAP Mental Health Support — available 24/7',                 '#'),
            # Manager-facing
            ('Manager — welcome back',   'How to have the welcome back conversation',                  '#'),
            ('Manager — welcome back',   'What not to say when someone returns from a career break',   '#'),
            ('Manager — support',        'How to give feedback to someone who is rebuilding confidence','#'),
            ('Manager — support',        'Avoiding common biases during the re-entry period',          '#'),
            # Policy / HR
            ('Policy',                   'Flexible Work Policy 2026 (updated March)',                  '#'),
            ('Policy',                   'Return to Work Framework — TechForward Ltd',                 '#'),
        ]
    )

    # ─────────────────────────────────────────────────────────────────────────
    # Employee 1: Sarah Chen — Senior Designer
    # Return date: 2026-04-17 → on demo day (2026-05-18) she is on Day 32
    # Story arc: early-phase, low confidence, needs more visibility
    # ─────────────────────────────────────────────────────────────────────────
    e1 = conn.execute(
        'INSERT INTO employees (name,role,start_date,manager_name,buddy_name,buddy_email,manager_email) VALUES (?,?,?,?,?,?,?)',
        ('Sarah Chen', 'Senior Designer', '2026-04-17',
         'Tom Walters', 'Lisa Morgan', 'lisa.morgan@company.com', 'tom.walters@company.com')
    ).lastrowid

    conn.executemany(
        'INSERT INTO checklist_items (employee_id,week,text,done,added_by) VALUES (?,?,?,?,?)',
        [
            (e1, 1, 'Meet your buddy',                           1, 'hr'),
            (e1, 1, 'IT setup and tools access confirmed',       1, 'hr'),
            (e1, 1, 'Attend first team standup',                 1, 'hr'),
            (e1, 2, 'Complete Week 1 check-in',                  1, 'hr'),
            (e1, 2, 'Review the What Changed digest',            1, 'hr'),
            (e1, 2, 'Reconnect with two colleagues one-on-one',  1, 'hr'),
            (e1, 3, 'Complete Month 1 check-in',                 0, 'hr'),
            (e1, 3, 'Identify one project to get involved in',   0, 'manager'),
            (e1, 3, 'Share a milestone with your manager',       0, 'hr'),
            (e1, 4, '30-day milestone review with manager',      0, 'hr'),
            (e1, 4, 'Lead or contribute to one team discussion',  0, 'manager'),
        ]
    )

    conn.executemany(
        'INSERT INTO checkins (employee_id,date,belonging,confidence,inclusion,support,visibility,note) VALUES (?,?,?,?,?,?,?,?)',
        [
            (e1, '2026-04-22', 2, 2, 2, 3, 2,
             'Feeling a bit overwhelmed. Everyone is kind but I feel invisible in meetings.'),
            (e1, '2026-04-29', 3, 2, 3, 3, 2,
             'Had a good chat with Lisa (buddy). Still finding it hard to speak up.'),
            (e1, '2026-05-06', 3, 3, 3, 3, 3,
             'Tom checked in with me one-on-one — that helped a lot. Starting to feel more settled.'),
            (e1, '2026-05-13', 3, 3, 3, 4, 3,
             'Contributed in the design review today. Small thing but it felt good.'),
        ]
    )

    conn.executemany(
        'INSERT INTO diary_entries (employee_id,date,text,mood) VALUES (?,?,?,?)',
        [
            (e1, '2026-04-22', 'Made it through the first week. More tired than I expected but glad I\'m back.', 'reflective'),
            (e1, '2026-04-28', 'Lisa and I had coffee — she remembered all the little things about the old team. Felt grounding.', 'warm'),
            (e1, '2026-05-05', 'Tom specifically asked for my take on the brief today. I wasn\'t expecting it but I had something to say.', 'proud'),
            (e1, '2026-05-12', 'Contributed to the design review for the first time. Rusty but real.', 'proud'),
            (e1, '2026-05-16', 'Finished the Figma onboarding. The new component library is actually better than I feared.', 'relieved'),
        ]
    )

    conn.executemany(
        'INSERT INTO manager_feedback (employee_id,date,text) VALUES (?,?,?)',
        [
            (e1, '2026-05-05', 'Sarah — I noticed your contribution in the design review this week. Good to have your perspective back.'),
            (e1, '2026-05-13', 'Really glad to see you settling in. Your instincts on the brief were spot on.'),
        ]
    )

    conn.executemany(
        'INSERT INTO manager_notes (employee_id,date,text) VALUES (?,?,?)',
        [
            (e1, '2026-04-18', 'First day went well. She seemed nervous but engaged. Make sure she\'s included in the Sprint planning next week.'),
            (e1, '2026-04-29', 'Buddy pairing confirmed with Lisa. Check in again at Week 3.'),
            (e1, '2026-05-06', 'One-on-one today — she mentioned feeling invisible in large meetings. Action: explicitly invite her contribution in next design review.'),
        ]
    )

    conn.executemany(
        'INSERT INTO manager_actions (employee_id,date,text,done) VALUES (?,?,?,?)',
        [
            (e1, '2026-04-18', 'Have a welcome back conversation within the first two days', 1),
            (e1, '2026-04-24', 'Include Sarah in at least one team decision this week', 1),
            (e1, '2026-05-01', 'Check in informally — ask how it is going, not how the work is going', 1),
            (e1, '2026-05-15', 'Acknowledge one specific contribution Sarah made this month', 0),
            (e1, '2026-05-15', 'Have a brief conversation about workload — is the pace manageable?', 0),
        ]
    )

    conn.executemany(
        'INSERT INTO bias_nudges (employee_id,text,seen) VALUES (?,?,?)',
        [
            (e1, "Sarah hasn't been invited to the last 2 planning meetings. Consider a direct invite — visibility in decisions matters early in re-entry.", 0),
            (e1, "It's been 2 weeks since Tom sent a nudge. A short check-in message can make a big difference at this stage.", 0),
        ]
    )

    # ─────────────────────────────────────────────────────────────────────────
    # Employee 2: Maya Patel — Product Manager
    # Return date: 2026-03-24 → on demo day she is on Day 56
    # Story arc: mid-phase, improving steadily, positive trajectory
    # ─────────────────────────────────────────────────────────────────────────
    e2 = conn.execute(
        'INSERT INTO employees (name,role,start_date,manager_name,buddy_name,buddy_email,manager_email) VALUES (?,?,?,?,?,?,?)',
        ('Maya Patel', 'Product Manager', '2026-03-24',
         'Rachel Brooks', 'Chloe Davis', 'chloe.davis@company.com', 'rachel.brooks@company.com')
    ).lastrowid

    conn.executemany(
        'INSERT INTO checklist_items (employee_id,week,text,done,added_by) VALUES (?,?,?,?,?)',
        [
            (e2, 1, 'Meet your buddy',                           1, 'hr'),
            (e2, 1, 'IT setup and tools access confirmed',       1, 'hr'),
            (e2, 1, 'Attend first team standup',                 1, 'hr'),
            (e2, 2, 'Complete Week 1 check-in',                  1, 'hr'),
            (e2, 2, 'Review the What Changed digest',            1, 'hr'),
            (e2, 2, 'Reconnect with two colleagues one-on-one',  1, 'hr'),
            (e2, 3, 'Complete Month 1 check-in',                 1, 'hr'),
            (e2, 3, 'Identify one project to get involved in',   1, 'manager'),
            (e2, 3, 'Share a milestone with your manager',       1, 'hr'),
            (e2, 4, '30-day milestone review with manager',      1, 'hr'),
            (e2, 4, 'Lead or contribute to one team discussion',  1, 'manager'),
            (e2, 5, 'Lead a full team meeting',                  1, 'manager'),
            (e2, 5, 'Complete Month 2 check-in',                 0, 'hr'),
            (e2, 6, 'Present product update to stakeholders',    0, 'manager'),
        ]
    )

    conn.executemany(
        'INSERT INTO checkins (employee_id,date,belonging,confidence,inclusion,support,visibility,note) VALUES (?,?,?,?,?,?,?,?)',
        [
            (e2, '2026-03-28', 3, 2, 3, 3, 2, 'First week done. Buddy system really helped — Chloe is brilliant.'),
            (e2, '2026-04-04', 3, 3, 3, 3, 3, 'Getting back into the rhythm. Sprint planning felt natural again.'),
            (e2, '2026-04-11', 4, 3, 4, 3, 3, 'Starting to feel more like myself. Ran part of the retro today.'),
            (e2, '2026-04-18', 4, 4, 4, 4, 3, 'Great 1:1 with Rachel — feeling genuinely supported.'),
            (e2, '2026-04-25', 4, 4, 4, 4, 4, '30-day review was positive. Rachel said my re-entry has been one of the smoothest she\'s seen.'),
            (e2, '2026-05-09', 5, 4, 5, 4, 4, 'Led the full product review meeting today. Felt completely in flow.'),
        ]
    )

    conn.executemany(
        'INSERT INTO diary_entries (employee_id,date,text,mood) VALUES (?,?,?,?)',
        [
            (e2, '2026-03-28', 'Made it through week one. More capable than I gave myself credit for.', 'relieved'),
            (e2, '2026-04-07', 'Ran part of the retro. The team laughed at my joke. Small thing. Big deal.', 'warm'),
            (e2, '2026-04-25', 'Rachel said my 30-day review was one of the best she\'s seen. Cried a little. Good tears.', 'proud'),
            (e2, '2026-05-09', 'Led the product review. Didn\'t hesitate once. This is what getting back feels like.', 'proud'),
        ]
    )

    conn.executemany(
        'INSERT INTO manager_feedback (employee_id,date,text) VALUES (?,?,?)',
        [
            (e2, '2026-04-10', "You're doing a fantastic job getting back up to speed, Maya. Really proud of how you've handled these first few weeks."),
            (e2, '2026-04-25', "Your 30-day review was one of the smoothest I've facilitated. Your instincts are sharp as ever."),
            (e2, '2026-05-09', "I want you to know — the way you led that product review today was exactly what the team needed. Outstanding."),
        ]
    )

    conn.executemany(
        'INSERT INTO manager_notes (employee_id,date,text) VALUES (?,?,?)',
        [
            (e2, '2026-03-25', 'Great first day energy. Chloe (buddy) already messaged me to say Maya seems great.'),
            (e2, '2026-04-11', 'Maya ran part of the retro — completely unprompted. Strong signal she\'s ready for more.'),
            (e2, '2026-04-25', '30-day review: scored 4.2 avg across all dimensions. On track for full independence by Day 60.'),
        ]
    )

    conn.executemany(
        'INSERT INTO manager_actions (employee_id,date,text,done) VALUES (?,?,?,?)',
        [
            (e2, '2026-03-25', 'Have a welcome back conversation within the first two days', 1),
            (e2, '2026-03-28', 'Include Maya in at least one team decision this week', 1),
            (e2, '2026-04-04', 'Check in informally — how is the pace feeling?', 1),
            (e2, '2026-04-11', 'Acknowledge one specific contribution Maya made this month', 1),
            (e2, '2026-04-25', '30-day milestone review', 1),
            (e2, '2026-05-15', 'Have a forward-looking conversation about Maya\'s goals and career trajectory', 0),
            (e2, '2026-05-15', 'Consider Maya for the Q3 roadmap lead role', 0),
        ]
    )

    conn.executemany(
        'INSERT INTO bias_nudges (employee_id,text,seen) VALUES (?,?,?)',
        [
            (e2, "Maya has not been offered a visible project lead yet. She is ready — consider assigning one before Day 60.", 1),
            (e2, "Maya's confidence scores have increased every week. She may be ready for a forward-looking career conversation.", 0),
        ]
    )

    # ─────────────────────────────────────────────────────────────────────────
    # Employee 3: Jess Thompson — UX Researcher
    # Return date: 2026-02-23 → on demo day she is on Day 85
    # Story arc: late-phase, thriving, near window close
    # ─────────────────────────────────────────────────────────────────────────
    e3 = conn.execute(
        'INSERT INTO employees (name,role,start_date,manager_name,buddy_name,buddy_email,manager_email) VALUES (?,?,?,?,?,?,?)',
        ('Jess Thompson', 'UX Researcher', '2026-02-23',
         'Tom Walters', 'Priya Sharma', 'priya.sharma@company.com', 'tom.walters@company.com')
    ).lastrowid

    conn.executemany(
        'INSERT INTO checklist_items (employee_id,week,text,done,added_by) VALUES (?,?,?,?,?)',
        [
            (e3, 1, 'Meet your buddy',                           1, 'hr'),
            (e3, 1, 'IT setup and tools access confirmed',       1, 'hr'),
            (e3, 1, 'Attend first team standup',                 1, 'hr'),
            (e3, 2, 'Complete Week 1 check-in',                  1, 'hr'),
            (e3, 2, 'Review the What Changed digest',            1, 'hr'),
            (e3, 2, 'Reconnect with two colleagues one-on-one',  1, 'hr'),
            (e3, 3, 'Complete Month 1 check-in',                 1, 'hr'),
            (e3, 3, 'Identify one project to get involved in',   1, 'manager'),
            (e3, 3, 'Share a milestone with your manager',       1, 'hr'),
            (e3, 4, '30-day milestone review with manager',      1, 'hr'),
            (e3, 4, 'Lead a user research session',              1, 'manager'),
            (e3, 5, 'Lead a full team meeting',                  1, 'manager'),
            (e3, 5, '60-day formal review',                      1, 'hr'),
            (e3, 6, 'Present research findings to stakeholders', 1, 'manager'),
            (e3, 7, '85-day closing nudge review',               0, 'hr'),
        ]
    )

    conn.executemany(
        'INSERT INTO checkins (employee_id,date,belonging,confidence,inclusion,support,visibility,note) VALUES (?,?,?,?,?,?,?,?)',
        [
            (e3, '2026-02-27', 3, 2, 3, 3, 2, 'Nervous but genuinely glad to be back. The team made me feel welcome.'),
            (e3, '2026-03-06', 3, 3, 3, 3, 3, 'Things are starting to click. Priya (buddy) has been incredible.'),
            (e3, '2026-03-13', 4, 3, 3, 4, 3, 'Led my first research session back — it came back like muscle memory.'),
            (e3, '2026-03-20', 4, 4, 4, 4, 3, '30-day review with Tom was encouraging. I\'m ahead of where I expected to be.'),
            (e3, '2026-03-27', 4, 4, 4, 4, 4, 'Presented research findings to the whole team. Got a standing ovation (almost).'),
            (e3, '2026-04-17', 5, 4, 5, 4, 4, '60-day review: Tom said I\'ve set a new standard for how re-entry can look.'),
            (e3, '2026-05-08', 5, 5, 5, 5, 5, 'Fully integrated. Leading the Q2 research stream. Couldn\'t be happier to be back.'),
        ]
    )

    conn.executemany(
        'INSERT INTO diary_entries (employee_id,date,text,mood) VALUES (?,?,?,?)',
        [
            (e3, '2026-02-27', 'Week one done. I was terrified and it was fine. Better than fine.', 'relieved'),
            (e3, '2026-03-13', 'Led the research session today. My hands were shaking at the start and steady by the end.', 'proud'),
            (e3, '2026-03-27', 'Presented to the full team. I thought I had forgotten how to do this. I hadn\'t.', 'proud'),
            (e3, '2026-04-17', '60-day review. Tom said I\'ve set the bar. I cried on the way home. Good crying.', 'warm'),
            (e3, '2026-05-08', 'Leading the Q2 research stream. Five months ago I wasn\'t sure I still had it. I did.', 'proud'),
        ]
    )

    conn.executemany(
        'INSERT INTO manager_feedback (employee_id,date,text) VALUES (?,?,?)',
        [
            (e3, '2026-03-20', "Jess — your 30-day review was outstanding. You've set the bar for how a return-to-work journey should look."),
            (e3, '2026-03-27', "The presentation today was exceptional. The whole team noticed. Really proud of what you've done."),
            (e3, '2026-04-17', "60-day review: you are fully integrated and exceeding expectations. I'm recommending you for the Q2 research lead."),
            (e3, '2026-05-08', "Leading the Q2 stream is exactly the right next step. You've earned it."),
        ]
    )

    conn.executemany(
        'INSERT INTO manager_notes (employee_id,date,text) VALUES (?,?,?)',
        [
            (e3, '2026-02-24', 'Strong first day. Priya messaged immediately — great buddy pairing.'),
            (e3, '2026-03-20', '30-day review: 4.0 avg check-in score. On track to exceed all milestones.'),
            (e3, '2026-04-17', '60-day review: 4.8 avg. Formally nominating for Q2 research lead — should be an easy yes.'),
        ]
    )

    conn.executemany(
        'INSERT INTO manager_actions (employee_id,date,text,done) VALUES (?,?,?,?)',
        [
            (e3, '2026-02-24', 'Have a welcome back conversation within the first two days', 1),
            (e3, '2026-03-01', 'Include Jess in at least one team decision this week', 1),
            (e3, '2026-03-13', 'Acknowledge one specific contribution Jess made this month', 1),
            (e3, '2026-03-20', '30-day milestone review', 1),
            (e3, '2026-04-17', '60-day formal review and career conversation', 1),
            (e3, '2026-05-17', 'Send a closing nudge — 85-day window check-in', 0),
            (e3, '2026-05-24', 'Formal close of 90-day re-entry window — celebrate the journey', 0),
        ]
    )

    conn.executemany(
        'INSERT INTO bias_nudges (employee_id,text,seen) VALUES (?,?,?)',
        [
            (e3, "Jess is performing well — make sure she is being formally considered for the Q2 research lead role.", 1),
            (e3, "Jess's support window closes in 5 days. Send a closing nudge and schedule a final check-in.", 0),
        ]
    )
