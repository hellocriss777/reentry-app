// reentry — API-backed data layer
// DB.get() reads from in-memory cache (sync, same as before)
// DB.init(empId) loads all data from API before first render
// Write methods are async and reload cache after writing

const DB = {
  _store: {},
  _empId: 1,

  // ── Read (sync, from cache) ───────────────────────────────────────────────
  get(key) {
    return this._store[key];
  },

  // ── Init: load all data for one employee ─────────────────────────────────
  async init(empId) {
    this._empId = empId || 1;
    await this._reload();
  },

  async _reload() {
    const id = this._empId;
    const [emp, checkins, checklist, changes, resources, messages, actions, nudges, diary, notes] =
      await Promise.all([
        this._get(`/api/employees/${id}`),
        this._get(`/api/employees/${id}/checkins`),
        this._get(`/api/employees/${id}/checklist`),
        this._get('/api/changes'),
        this._get('/api/resources'),
        this._get(`/api/employees/${id}/messages`),
        this._get(`/api/employees/${id}/actions`),
        this._get(`/api/employees/${id}/nudges`),
        this._get(`/api/employees/${id}/diary`),
        this._get(`/api/employees/${id}/notes`),
      ]);

    if (emp && !emp.error) {
      this._store.employee = {
        name:         emp.name,
        role:         emp.role,
        startDate:    emp.start_date,
        manager:      emp.manager_name,
        buddy:        emp.buddy_name,
        buddyEmail:   emp.buddy_email,
        managerEmail: emp.manager_email,
      };
    }

    this._store.checkins = (checkins || []).map(c => ({
      date: c.date, belonging: c.belonging, confidence: c.confidence,
      inclusion: c.inclusion, support: c.support, visibility: c.visibility, note: c.note || ''
    }));

    this._store.checklist = (checklist || []).map(c => ({
      id: c.id, week: c.week, text: c.text, done: !!c.done, addedBy: c.added_by
    }));

    this._store.whatChanged = (changes || []).map(c => ({
      id: c.id, category: c.category, title: c.title, body: c.body, date: c.date
    }));

    this._store.resources = (resources || []).map(r => ({
      id: r.id, category: r.category, title: r.title, url: r.url
    }));

    this._store.managerFeedback = (messages || []).map(m => ({
      id: m.id, date: m.date, text: m.text
    }));

    this._store.managerActions = (actions || []).map(a => ({
      id: a.id, date: a.date, text: a.text, done: !!a.done
    }));

    this._store.biasNudges = (nudges || []).map(n => ({
      id: n.id, text: n.text, seen: !!n.seen
    }));

    this._store.diary = (diary || []).map(d => ({
      id: d.id, date: d.date, text: d.text, mood: d.mood || ''
    }));

    this._store.managerNotes = (notes || []).map(n => ({
      date: n.date, text: n.text
    }));
  },

  // Init for HR view: loads all employees
  async initHR() {
    const [employees, changes, resources] = await Promise.all([
      this._get('/api/employees'),
      this._get('/api/changes'),
      this._get('/api/resources'),
    ]);
    this._store.employees = employees || [];
    this._store.whatChanged = (changes || []).map(c => ({
      id: c.id, category: c.category, title: c.title, body: c.body, date: c.date
    }));
    this._store.resources = (resources || []).map(r => ({
      id: r.id, category: r.category, title: r.title, url: r.url
    }));

    // Load checkins for all employees to compute stats
    const allCheckins = await Promise.all(
      (employees || []).map(e => this._get(`/api/employees/${e.id}/checkins`))
    );
    this._store._allCheckins = allCheckins;

    const allActions = await Promise.all(
      (employees || []).map(e => this._get(`/api/employees/${e.id}/actions`))
    );
    this._store._allActions = allActions;
  },

  // ── Write methods (async, reload cache after) ─────────────────────────────

  async submitCheckin(data) {
    await this._post(`/api/employees/${this._empId}/checkins`, data);
    await this._reload();
  },

  async toggleChecklist(itemId, done) {
    await this._put(`/api/checklist/${itemId}`, { done });
    await this._reload();
  },

  async addChecklistItem(text, week) {
    await this._post(`/api/employees/${this._empId}/checklist`, { text, week, addedBy: 'manager' });
    await this._reload();
  },

  async sendMessage(text, date) {
    await this._post(`/api/employees/${this._empId}/messages`, { text, date });
    await this._reload();
  },

  async addManagerNote(text, date) {
    await this._post(`/api/employees/${this._empId}/notes`, { text, date });
    await this._reload();
  },

  async toggleManagerAction(id, done) {
    await this._put(`/api/actions/${id}`, { done });
    await this._reload();
  },

  async dismissNudge(id) {
    await this._put(`/api/nudges/${id}/dismiss`, {});
    await this._reload();
  },

  async addChange(category, title, body, date) {
    await this._post('/api/changes', { category, title, body, date });
    await this._reload();
  },

  async deleteChange(id) {
    await fetch(`/api/changes/${id}`, { method: 'DELETE' });
    await this._reload();
  },

  async createEmployee(data) {
    const res = await this._post('/api/employees', data);
    await this.initHR();
    return res;
  },

  async addManagerAction(eid, text, date) {
    await this._post(`/api/employees/${eid}/actions`, { text, date });
    await this.initHR();
  },

  async addDiaryEntry(text, date, mood) {
    await this._post(`/api/employees/${this._empId}/diary`, { text, date, mood });
    await this._reload();
  },

  async addResource(category, title, url) {
    await this._post('/api/resources', { category, title, url });
    await this._reload();
  },

  // ── Demo date (stays in localStorage — demo-only, no need to sync) ────────
  getDemoDate() {
    const d = localStorage.getItem('reentry_demoDate');
    if (d) { const [y,m,day] = d.split('-').map(Number); return new Date(y,m-1,day,12,0,0); }
    return new Date();
  },
  setDemoDate(s) { localStorage.setItem('reentry_demoDate', s); },
  clearDemoDate() { localStorage.removeItem('reentry_demoDate'); },

  daysSinceReturn() {
    const emp = this._store.employee || {};
    if (!emp.startDate) return 0;
    const [y,m,d] = emp.startDate.split('-').map(Number);
    const start = new Date(y,m-1,d,12,0,0);
    return Math.max(0, Math.floor((this.getDemoDate() - start) / 86400000));
  },

  avgCheckin() {
    const checkins = this._store.checkins || [];
    if (!checkins.length) return null;
    const last = checkins[checkins.length - 1];
    const dims = [last.belonging, last.confidence, last.inclusion, last.support, last.visibility];
    return (dims.reduce((a,b) => a+b, 0) / dims.length).toFixed(1);
  },

  // ── HTTP helpers ──────────────────────────────────────────────────────────
  async _get(url) {
    try {
      const r = await fetch(url);
      return r.ok ? r.json() : null;
    } catch { return null; }
  },

  async _post(url, body) {
    const r = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    return r.json();
  },

  async _put(url, body) {
    const r = await fetch(url, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    return r.ok ? r.json() : null;
  },
};
