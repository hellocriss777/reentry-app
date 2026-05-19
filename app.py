from flask import Flask, request, jsonify, render_template, g
from database import init_db, get_db
import os

app = Flask(__name__, static_folder='static', template_folder='templates')

init_db()

@app.teardown_appcontext
def close_db(err):
    db = g.pop('db', None)
    if db:
        db.close()

# ── Pages ──────────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/employee')
def employee():
    return render_template('employee.html')

@app.route('/hr')
def hr():
    return render_template('hr.html')

@app.route('/manager')
def manager():
    return render_template('manager.html')

@app.route('/onboarding/employee')
def onboarding_employee():
    return render_template('onboarding_employee.html')

@app.route('/onboarding/hr')
def onboarding_hr():
    return render_template('onboarding_hr.html')

@app.route('/onboarding/manager')
def onboarding_manager():
    return render_template('onboarding_manager.html')

# ── Employees ──────────────────────────────────────────────────────────────────

@app.route('/api/employees', methods=['GET'])
def list_employees():
    rows = get_db().execute('SELECT * FROM employees ORDER BY id').fetchall()
    return jsonify([dict(r) for r in rows])

@app.route('/api/employees', methods=['POST'])
def create_employee():
    d = request.json
    db = get_db()
    cur = db.execute(
        'INSERT INTO employees (name,role,start_date,manager_name,buddy_name,buddy_email,manager_email) VALUES (?,?,?,?,?,?,?)',
        (d['name'], d['role'], d['startDate'],
         d.get('manager',''), d.get('buddy',''),
         d.get('buddyEmail',''), d.get('managerEmail',''))
    )
    db.commit()
    # Seed default checklist for new employee
    eid = cur.lastrowid
    db.executemany(
        'INSERT INTO checklist_items (employee_id,week,text,done,added_by) VALUES (?,?,?,0,?)',
        [
            (eid,1,'Meet your buddy','hr'),
            (eid,1,'IT setup complete','hr'),
            (eid,1,'Team intro meeting','hr'),
            (eid,2,'Complete weekly check-in','hr'),
            (eid,2,'Skills refresh session','hr'),
            (eid,2,'Review what changed digest','hr'),
            (eid,3,'30-day milestone review','hr'),
        ]
    )
    db.execute(
        'INSERT INTO bias_nudges (employee_id,text,seen) VALUES (?,?,0)',
        (eid, f"{d['name']} is new to this platform. Check in with them this week.")
    )
    db.commit()
    row = db.execute('SELECT * FROM employees WHERE id=?', (eid,)).fetchone()
    return jsonify(dict(row)), 201

@app.route('/api/employees/<int:eid>', methods=['GET'])
def get_employee(eid):
    row = get_db().execute('SELECT * FROM employees WHERE id=?', (eid,)).fetchone()
    if not row:
        return jsonify({'error': 'Not found'}), 404
    return jsonify(dict(row))

@app.route('/api/employees/<int:eid>', methods=['PUT'])
def update_employee(eid):
    d = request.json
    db = get_db()
    db.execute(
        'UPDATE employees SET name=?,role=?,start_date=?,manager_name=?,buddy_name=?,buddy_email=?,manager_email=? WHERE id=?',
        (d['name'], d['role'], d['startDate'],
         d.get('manager',''), d.get('buddy',''),
         d.get('buddyEmail',''), d.get('managerEmail',''), eid)
    )
    db.commit()
    return jsonify(dict(db.execute('SELECT * FROM employees WHERE id=?', (eid,)).fetchone()))

# ── Check-ins ──────────────────────────────────────────────────────────────────

@app.route('/api/employees/<int:eid>/checkins', methods=['GET'])
def get_checkins(eid):
    rows = get_db().execute('SELECT * FROM checkins WHERE employee_id=? ORDER BY id', (eid,)).fetchall()
    return jsonify([dict(r) for r in rows])

@app.route('/api/employees/<int:eid>/checkins', methods=['POST'])
def add_checkin(eid):
    d = request.json
    db = get_db()
    cur = db.execute(
        'INSERT INTO checkins (employee_id,date,belonging,confidence,inclusion,support,visibility,note) VALUES (?,?,?,?,?,?,?,?)',
        (eid, d['date'], d['belonging'], d['confidence'], d['inclusion'], d['support'], d['visibility'], d.get('note',''))
    )
    db.commit()
    return jsonify(dict(db.execute('SELECT * FROM checkins WHERE id=?', (cur.lastrowid,)).fetchone())), 201

# ── Checklist ──────────────────────────────────────────────────────────────────

@app.route('/api/employees/<int:eid>/checklist', methods=['GET'])
def get_checklist(eid):
    rows = get_db().execute('SELECT * FROM checklist_items WHERE employee_id=? ORDER BY week,id', (eid,)).fetchall()
    return jsonify([dict(r) for r in rows])

@app.route('/api/employees/<int:eid>/checklist', methods=['POST'])
def add_checklist_item(eid):
    d = request.json
    db = get_db()
    cur = db.execute(
        'INSERT INTO checklist_items (employee_id,week,text,done,added_by) VALUES (?,?,?,0,?)',
        (eid, d['week'], d['text'], d.get('addedBy','manager'))
    )
    db.commit()
    return jsonify(dict(db.execute('SELECT * FROM checklist_items WHERE id=?', (cur.lastrowid,)).fetchone())), 201

@app.route('/api/checklist/<int:item_id>', methods=['PUT'])
def toggle_checklist(item_id):
    d = request.json
    db = get_db()
    db.execute('UPDATE checklist_items SET done=? WHERE id=?', (1 if d['done'] else 0, item_id))
    db.commit()
    return jsonify(dict(db.execute('SELECT * FROM checklist_items WHERE id=?', (item_id,)).fetchone()))

# ── What Changed ───────────────────────────────────────────────────────────────

@app.route('/api/changes', methods=['GET'])
def get_changes():
    rows = get_db().execute('SELECT * FROM what_changed ORDER BY id DESC').fetchall()
    return jsonify([dict(r) for r in rows])

@app.route('/api/changes', methods=['POST'])
def add_change():
    d = request.json
    db = get_db()
    cur = db.execute(
        'INSERT INTO what_changed (category,title,body,date) VALUES (?,?,?,?)',
        (d['category'], d['title'], d['body'], d['date'])
    )
    db.commit()
    return jsonify(dict(db.execute('SELECT * FROM what_changed WHERE id=?', (cur.lastrowid,)).fetchone())), 201

@app.route('/api/changes/<int:cid>', methods=['DELETE'])
def delete_change(cid):
    db = get_db()
    db.execute('DELETE FROM what_changed WHERE id=?', (cid,))
    db.commit()
    return jsonify({'ok': True})

# ── Manager messages to employee ───────────────────────────────────────────────

@app.route('/api/employees/<int:eid>/messages', methods=['GET'])
def get_messages(eid):
    rows = get_db().execute('SELECT * FROM manager_feedback WHERE employee_id=? ORDER BY id DESC', (eid,)).fetchall()
    return jsonify([dict(r) for r in rows])

@app.route('/api/employees/<int:eid>/messages', methods=['POST'])
def add_message(eid):
    d = request.json
    db = get_db()
    cur = db.execute(
        'INSERT INTO manager_feedback (employee_id,date,text) VALUES (?,?,?)',
        (eid, d['date'], d['text'])
    )
    db.commit()
    return jsonify(dict(db.execute('SELECT * FROM manager_feedback WHERE id=?', (cur.lastrowid,)).fetchone())), 201

# ── Manager private notes ──────────────────────────────────────────────────────

@app.route('/api/employees/<int:eid>/notes', methods=['GET'])
def get_notes(eid):
    rows = get_db().execute('SELECT * FROM manager_notes WHERE employee_id=? ORDER BY id DESC', (eid,)).fetchall()
    return jsonify([dict(r) for r in rows])

@app.route('/api/employees/<int:eid>/notes', methods=['POST'])
def add_note(eid):
    d = request.json
    db = get_db()
    cur = db.execute(
        'INSERT INTO manager_notes (employee_id,date,text) VALUES (?,?,?)',
        (eid, d['date'], d['text'])
    )
    db.commit()
    return jsonify(dict(db.execute('SELECT * FROM manager_notes WHERE id=?', (cur.lastrowid,)).fetchone())), 201

# ── Manager actions (sent by HR) ───────────────────────────────────────────────

@app.route('/api/employees/<int:eid>/actions', methods=['GET'])
def get_actions(eid):
    rows = get_db().execute('SELECT * FROM manager_actions WHERE employee_id=? ORDER BY id DESC', (eid,)).fetchall()
    return jsonify([dict(r) for r in rows])

@app.route('/api/employees/<int:eid>/actions', methods=['POST'])
def add_action(eid):
    d = request.json
    db = get_db()
    cur = db.execute(
        'INSERT INTO manager_actions (employee_id,date,text,done) VALUES (?,?,?,0)',
        (eid, d['date'], d['text'])
    )
    db.commit()
    return jsonify(dict(db.execute('SELECT * FROM manager_actions WHERE id=?', (cur.lastrowid,)).fetchone())), 201

@app.route('/api/actions/<int:aid>', methods=['PUT'])
def toggle_action(aid):
    d = request.json
    db = get_db()
    db.execute('UPDATE manager_actions SET done=? WHERE id=?', (1 if d['done'] else 0, aid))
    db.commit()
    return jsonify(dict(db.execute('SELECT * FROM manager_actions WHERE id=?', (aid,)).fetchone()))

# ── Resources ──────────────────────────────────────────────────────────────────

@app.route('/api/resources', methods=['GET'])
def get_resources():
    rows = get_db().execute('SELECT * FROM resources ORDER BY id').fetchall()
    return jsonify([dict(r) for r in rows])

@app.route('/api/resources', methods=['POST'])
def add_resource():
    d = request.json
    db = get_db()
    cur = db.execute(
        'INSERT INTO resources (category,title,url) VALUES (?,?,?)',
        (d['category'], d['title'], d['url'])
    )
    db.commit()
    return jsonify(dict(db.execute('SELECT * FROM resources WHERE id=?', (cur.lastrowid,)).fetchone())), 201

@app.route('/api/resources/<int:rid>', methods=['DELETE'])
def delete_resource(rid):
    db = get_db()
    db.execute('DELETE FROM resources WHERE id=?', (rid,))
    db.commit()
    return jsonify({'ok': True})

# ── Bias nudges ────────────────────────────────────────────────────────────────

@app.route('/api/employees/<int:eid>/nudges', methods=['GET'])
def get_nudges(eid):
    rows = get_db().execute('SELECT * FROM bias_nudges WHERE employee_id=? AND seen=0', (eid,)).fetchall()
    return jsonify([dict(r) for r in rows])

@app.route('/api/nudges/<int:nid>/dismiss', methods=['PUT'])
def dismiss_nudge(nid):
    db = get_db()
    db.execute('UPDATE bias_nudges SET seen=1 WHERE id=?', (nid,))
    db.commit()
    return jsonify({'ok': True})

# ── Diary ──────────────────────────────────────────────────────────────────────

@app.route('/api/employees/<int:eid>/diary', methods=['GET'])
def get_diary(eid):
    rows = get_db().execute('SELECT * FROM diary_entries WHERE employee_id=? ORDER BY id DESC', (eid,)).fetchall()
    return jsonify([dict(r) for r in rows])

@app.route('/api/employees/<int:eid>/diary', methods=['POST'])
def add_diary(eid):
    d = request.json
    db = get_db()
    cur = db.execute(
        'INSERT INTO diary_entries (employee_id,date,text,mood) VALUES (?,?,?,?)',
        (eid, d['date'], d['text'], d.get('mood',''))
    )
    db.commit()
    return jsonify(dict(db.execute('SELECT * FROM diary_entries WHERE id=?', (cur.lastrowid,)).fetchone())), 201

# ── Stats (HR) ─────────────────────────────────────────────────────────────

@app.route('/api/stats', methods=['GET'])
def get_stats():
    db = get_db()
    employees = db.execute('SELECT * FROM employees').fetchall()
    total = len(employees)
    checkins_count = db.execute('SELECT COUNT(*) FROM checkins').fetchone()[0]
    items = db.execute('SELECT done FROM checklist_items').fetchall()
    total_items = len(items)
    done_items = sum(1 for i in items if i['done'])
    completion_pct = round((done_items / total_items * 100) if total_items else 0)
    return jsonify({
        'total_employees': total,
        'checkins_count': checkins_count,
        'milestone_completion_pct': completion_pct,
        'total_milestones': total_items,
        'done_milestones': done_items,
    })

# ── Demo helpers ───────────────────────────────────────────────────────────────

@app.route('/api/reset', methods=['POST'])
def reset_demo():
    """Re-seed database (demo use only)."""
    from database import open_db, _seed
    conn = open_db()
    for t in ['diary_entries','bias_nudges','resources','manager_actions',
              'manager_notes','manager_feedback','what_changed',
              'checklist_items','checkins','employees','settings']:
        conn.execute(f'DELETE FROM {t}')
    conn.execute("DELETE FROM sqlite_sequence")
    _seed(conn)
    conn.commit()
    conn.close()
    return jsonify({'ok': True})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
