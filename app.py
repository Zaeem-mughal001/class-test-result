import json
import os
import secrets
import sqlite3
from datetime import datetime, date
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

HOST = "0.0.0.0"
PORT = int(os.environ.get("PORT", 8000))

# CHANGE THESE TWO VALUES to your own codes. Keep the quotation marks.
TEACHER_ACCESS_CODE = "admin1234"
STUDENT_PIN = "user1234"

DB_FILE = "class_test_result.db"
sessions = {}

SUBJECTS = [
    "English",
    "Urdu",
    "Mathematics",
    "Computer Science",
    "Physics",
    "Chemistry",
]

HTML = r'''<!doctype html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>📚 Class Test Result</title>
<style>
*{box-sizing:border-box}body{margin:0;font-family:Arial,sans-serif;background:#f4f7fb;color:#18212f}
header{background:#173b67;color:white;padding:18px 16px;text-align:center}
main{max-width:1100px;margin:auto;padding:18px}
.card{background:white;border-radius:14px;padding:18px;margin:14px 0;box-shadow:0 3px 14px #00000012}
button{border:0;border-radius:9px;padding:10px 14px;background:#173b67;color:white;cursor:pointer;margin:3px}
button.secondary{background:#e7edf5;color:#173b67}.danger{background:#b42318}.success{background:#087443}
input,select{width:100%;padding:10px;border:1px solid #cbd5e1;border-radius:8px;margin:5px 0 10px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:10px}
table{width:100%;border-collapse:collapse;background:white}th,td{padding:9px;border-bottom:1px solid #e5e7eb;text-align:left}
.small{font-size:13px;color:#64748b}.hidden{display:none}.pill{display:inline-block;padding:5px 9px;border-radius:20px;background:#e8f0fb;margin:3px}
.subject-row{border:1px solid #dbe3ee;border-radius:10px;padding:10px;margin:8px 0}
.result{border-left:4px solid #173b67;padding:12px;margin:10px 0;background:#f8fafc;border-radius:8px}
.att-card{border-left:4px solid #087443;padding:14px;margin:10px 0;background:#f8fafc;border-radius:8px}
.status-present{color:#087443;font-weight:bold}.status-absent{color:#b42318;font-weight:bold}.status-leave{color:#9a6700;font-weight:bold}
nav{display:flex;flex-wrap:wrap;gap:4px}nav button{background:#fff;color:#173b67}
.kpi{font-size:24px;font-weight:bold}.muted{color:#64748b}
@media(max-width:600px){main{padding:10px}table{font-size:13px}.wide{overflow-x:auto}}
</style>
</head>
<body>
<header><h1>📚 Class Test Result</h1><div id="status" class="small" style="color:#dbeafe"></div></header>
<main>
<section id="home" class="card">
<h2>Welcome 👋</h2><p>Choose your login.</p>
<button onclick="show('studentLogin')">🎓 Student Login</button>
<button onclick="show('teacherLogin')">👨‍🏫 Teacher Login</button>
</section>

<section id="studentLogin" class="card hidden">
<h2>🎓 Student Login</h2><p class="small">Enter your name or roll number (or both) and the common Student PIN.</p>
<label>Name</label><input id="sName" placeholder="Student name">
<label>Roll Number</label><input id="sRoll" placeholder="Roll number">
<label>Student PIN</label><input id="sPin" type="password" placeholder="Student PIN">
<button onclick="studentLogin()">Login</button><button class="secondary" onclick="show('home')">Back</button>
<p id="studentMsg"></p>
</section>

<section id="teacherLogin" class="card hidden">
<h2>👨‍🏫 Teacher Login</h2><label>Teacher Access Code</label><input id="tCode" type="password" placeholder="Teacher access code">
<button onclick="teacherLogin()">Login</button><button class="secondary" onclick="show('home')">Back</button>
<p id="teacherMsg"></p>
</section>

<section id="studentPage" class="hidden">
<div class="card">
<button onclick="logout()">Logout</button><h2 id="studentTitle"></h2>
<div class="grid">
<div><label>Week</label><select id="studentWeek" onchange="renderStudentResults()"><option value="">All Weeks</option></select></div>
<div><label>Subject</label><select id="studentSubject" onchange="renderStudentResults()"><option value="">All Subjects</option></select></div>
</div></div>
<div class="card" id="studentAttendanceSummary"></div>
<div id="studentResults"></div>
</section>

<section id="teacherPage" class="hidden">
<div class="card"><button onclick="logout()">Logout</button><h2>👨‍🏫 Teacher Dashboard</h2>
<nav>
<button onclick="teacherTab('students')">👥 Students</button>
<button onclick="teacherTab('addTest')">➕ Add Test</button>
<button onclick="teacherTab('history')">📜 History</button>
<button onclick="teacherTab('attendance')">📅 Attendance</button>
</nav></div>

<div id="studentsTab" class="card">
<h3>Students</h3><div class="grid"><div><label>Name</label><input id="newName"></div><div><label>Roll Number</label><input id="newRoll"></div></div>
<button onclick="addStudent()">Add Student</button>
<div class="wide"><table><thead><tr><th>Name</th><th>Roll</th><th>Action</th></tr></thead><tbody id="studentsTable"></tbody></table></div>
</div>

<div id="addTestTab" class="card hidden">
<h3>➕ Add Test Result</h3>
<div class="grid"><div><label>Student</label><select id="testStudent"></select></div><div><label>Date</label><input id="testDate" type="date"></div><div><label>Test Title</label><input id="testTitle" placeholder="Daily Test"></div></div>
<h4>Subjects tested</h4><p class="small">For each subject choose Present, Absent, or Leave. Marks are only required for Present.</p>
<div id="subjectRows"></div><button class="secondary" onclick="addSubjectRow()">+ Add Subject</button><br>
<button onclick="saveTest()">Save Test</button><p id="testMsg"></p>
</div>

<div id="historyTab" class="card hidden">
<h3>📜 Result History</h3><div class="grid">
<div><label>Student</label><select id="filterStudent" onchange="loadTeacherTests()"><option value="">All Students</option></select></div>
<div><label>Subject</label><select id="filterSubject" onchange="loadTeacherTests()"><option value="">All Subjects</option></select></div>
<div><label>From</label><input id="fromDate" type="date" onchange="loadTeacherTests()"></div>
<div><label>To</label><input id="toDate" type="date" onchange="loadTeacherTests()"></div>
</div><div class="wide"><table><thead><tr><th>Date</th><th>Student</th><th>Test</th><th>Subjects / Status</th><th>Total</th><th>%</th><th>Action</th></tr></thead><tbody id="testsTable"></tbody></table></div>
</div>

<div id="attendanceTab" class="card hidden">
<h3>📅 Daily Attendance</h3>
<p class="small">Record one school-day status for a student. Leave is counted as a school day but not as a present day.</p>
<div class="grid">
<div><label>Student</label><select id="attStudent"></select></div>
<div><label>Date</label><input id="attDate" type="date"></div>
<div><label>Status</label><select id="attStatus"><option value="present">Present</option><option value="absent">Absent</option><option value="leave">Leave</option></select></div>
</div>
<button onclick="saveAttendance()">Save Attendance</button><p id="attMsg"></p>
<hr>
<h4>Attendance Records</h4>
<div class="grid">
<div><label>Student</label><select id="attFilterStudent" onchange="loadAttendance()"><option value="">All Students</option></select></div>
<div><label>From</label><input id="attFrom" type="date" onchange="loadAttendance()"></div>
<div><label>To</label><input id="attTo" type="date" onchange="loadAttendance()"></div>
</div>
<div class="wide"><table><thead><tr><th>Date</th><th>Student</th><th>Status</th><th>Action</th></tr></thead><tbody id="attendanceTable"></tbody></table></div>
<div id="attendanceStats"></div>
</div>
</section>
</main>

<script>
const SUBJECTS=["English","Urdu","Mathematics","Computer Science","Physics","Chemistry"];
const $=id=>document.getElementById(id);
let currentStudent=null,teacherStudents=[],teacherTests=[],studentTests=[],attendanceRows=[];
function show(id){["home","studentLogin","teacherLogin","studentPage","teacherPage"].forEach(x=>$(x).classList.add("hidden"));$(id).classList.remove("hidden")}
function msg(id,text,ok=false){$(id).textContent=text;$(id).style.color=ok?"#087443":"#b42318"}
async function api(url,opt={}){const r=await fetch(url,{headers:{"Content-Type":"application/json"},...opt});const data=await r.json().catch(()=>({}));if(!r.ok)throw new Error(data.error||"Request failed");return data}
async function studentLogin(){try{const data=await api("/api/login/student",{method:"POST",body:JSON.stringify({name:$('sName').value.trim(),roll:$('sRoll').value.trim(),pin:$('sPin').value})});currentStudent=data.student;$('studentTitle').textContent="🎓 "+data.student.name+" — Roll "+data.student.roll_number;show('studentPage');await loadStudentResults();await loadStudentAttendance()}catch(e){msg('studentMsg',e.message)}}
async function teacherLogin(){try{await api('/api/login/teacher',{method:'POST',body:JSON.stringify({code:$('tCode').value})});show('teacherPage');await openTeacher()}catch(e){msg('teacherMsg',e.message)}}
async function logout(){await api('/api/logout',{method:'POST'});location.reload()}
function teacherTab(tab){['studentsTab','addTestTab','historyTab','attendanceTab'].forEach(x=>$(x).classList.add('hidden'));$(tab+'Tab').classList.remove('hidden');if(tab==='students')loadStudents();if(tab==='addTest')prepareAddTest();if(tab==='history')loadTeacherTests();if(tab==='attendance'){prepareAttendance();loadAttendance()}}
async function openTeacher(){await loadStudents();prepareAddTest();await loadTeacherTests();prepareAttendance();await loadAttendance()}
async function loadStudents(){teacherStudents=await api('/api/students');$('studentsTable').innerHTML=teacherStudents.map(s=>`<tr><td>${esc(s.name)}</td><td>${esc(s.roll_number)}</td><td><button onclick="editStudent(${s.id},'${js(s.name)}','${js(s.roll_number)}')">Edit</button><button class="danger" onclick="deleteStudent(${s.id})">Delete</button></td></tr>`).join('');const opts=teacherStudents.map(s=>`<option value="${s.id}">${esc(s.name)} — ${esc(s.roll_number)}</option>`).join('');$('testStudent').innerHTML=opts;$('filterStudent').innerHTML='<option value="">All Students</option>'+opts;$('attStudent').innerHTML=opts;$('attFilterStudent').innerHTML='<option value="">All Students</option>'+opts}
async function addStudent(){try{await api('/api/students',{method:'POST',body:JSON.stringify({name:$('newName').value.trim(),roll_number:$('newRoll').value.trim()})});$('newName').value='';$('newRoll').value='';await loadStudents();msg('testMsg','Student added',true)}catch(e){alert(e.message)}}
async function editStudent(id,name,roll){const n=prompt('Student name:',name);if(n===null)return;const r=prompt('Roll number:',roll);if(r===null)return;try{await api('/api/students/'+id,{method:'PUT',body:JSON.stringify({name:n,roll_number:r})});await loadStudents();await loadTeacherTests();await loadAttendance()}catch(e){alert(e.message)}}
async function deleteStudent(id){if(!confirm('Delete this student and all their results and attendance?'))return;try{await api('/api/students/'+id,{method:'DELETE'});await loadStudents();await loadTeacherTests();await loadAttendance()}catch(e){alert(e.message)}}
function prepareAddTest(){if(!$('testDate').value)$('testDate').value=new Date().toISOString().slice(0,10);if(!$('subjectRows').children.length)addSubjectRow()}
function addSubjectRow(data={subject:SUBJECTS[0],status:'present',obtained:'',maximum:''}){const div=document.createElement('div');div.className='subject-row';div.innerHTML=`<div class="grid"><div><label>Subject</label><select class="sub">${SUBJECTS.map(s=>`<option ${s===data.subject?'selected':''}>${s}</option>`).join('')}</select></div><div><label>Status</label><select class="status"><option value="present" ${data.status==='present'?'selected':''}>Present</option><option value="absent" ${data.status==='absent'?'selected':''}>Absent</option><option value="leave" ${data.status==='leave'?'selected':''}>Leave</option></select></div><div><label>Obtained Marks</label><input class="obt" type="number" min="0" step="0.01" value="${data.obtained}"></div><div><label>Maximum Marks</label><input class="max" type="number" min="0.01" step="0.01" value="${data.maximum}"></div><div><button class="danger" onclick="this.closest('.subject-row').remove()">Remove</button></div></div>`;$('subjectRows').appendChild(div);const st=div.querySelector('.status');const sync=()=>{const disabled=st.value!=='present';div.querySelector('.obt').disabled=disabled;div.querySelector('.max').disabled=disabled;if(disabled){div.querySelector('.obt').value='';div.querySelector('.max').value=''}};st.addEventListener('change',sync);sync()}
async function saveTest(){const rows=[...document.querySelectorAll('.subject-row')].map(r=>({subject:r.querySelector('.sub').value,status:r.querySelector('.status').value,obtained:r.querySelector('.obt').value===''?null:Number(r.querySelector('.obt').value),maximum:r.querySelector('.max').value===''?null:Number(r.querySelector('.max').value)}));try{await api('/api/tests',{method:'POST',body:JSON.stringify({student_id:Number($('testStudent').value),test_date:$('testDate').value,test_title:$('testTitle').value,subjects:rows})});msg('testMsg','Test saved successfully',true);$('testTitle').value='';$('subjectRows').innerHTML='';addSubjectRow();await loadTeacherTests()}catch(e){msg('testMsg',e.message)}}
async function loadTeacherTests(){try{const q=new URLSearchParams();if($('filterStudent').value)q.set('student_id',$('filterStudent').value);if($('filterSubject').value)q.set('subject',$('filterSubject').value);if($('fromDate').value)q.set('from',$('fromDate').value);if($('toDate').value)q.set('to',$('toDate').value);teacherTests=await api('/api/tests?'+q.toString());$('testsTable').innerHTML=teacherTests.map(t=>`<tr><td>${esc(t.test_date)}</td><td>${esc(t.student_name)}<br><span class="small">${esc(t.roll_number)}</span></td><td>${esc(t.test_title)}</td><td>${t.subjects.map(x=>`<div>${esc(x.subject)}: ${statusText(x)}${x.status==='present'?` (${x.obtained}/${x.maximum})`:''}</div>`).join('')}</td><td>${t.total_max?`${t.total_obtained}/${t.total_max}`:'—'}</td><td>${t.percentage===null?'—':t.percentage+'%'}</td><td><button onclick="editTest(${t.id})">Edit</button><button class="danger" onclick="deleteTest(${t.id})">Delete</button></td></tr>`).join('')||'<tr><td colspan="7">No results found.</td></tr>';setupSubjectFilter()}catch(e){console.error(e)}}
function setupSubjectFilter(){const old=$('filterSubject').value;const set=new Set();teacherTests.forEach(t=>t.subjects.forEach(x=>set.add(x.subject)));$('filterSubject').innerHTML='<option value="">All Subjects</option>'+[...set].sort().map(s=>`<option ${s===old?'selected':''}>${esc(s)}</option>`).join('')}
function statusText(x){if(x.status==='absent')return '<span class="status-absent">Absent</span>';if(x.status==='leave')return '<span class="status-leave">Leave</span>';return '<span class="status-present">Present</span>'}
async function editTest(id){const t=teacherTests.find(x=>x.id===id);if(!t)return;const title=prompt('Test title:',t.test_title);if(title===null)return;const d=prompt('Date (YYYY-MM-DD):',t.test_date);if(d===null)return;const subjects=t.subjects.map(x=>{const val=prompt(`${x.subject} status and marks. Use present,absent,leave OR present,18/20`,x.status==='present'?`present,${x.obtained}/${x.maximum}`:x.status);if(val===null)return null;const p=val.split(',').map(z=>z.trim());const st=p[0].toLowerCase();if(st!=='present')return {subject:x.subject,status:st,obtained:null,maximum:null};const m=(p[1]||'').split('/');return {subject:x.subject,status:'present',obtained:Number(m[0]),maximum:Number(m[1])}}).filter(Boolean);try{await api('/api/tests/'+id,{method:'PUT',body:JSON.stringify({test_date:d,test_title:title,subjects})});await loadTeacherTests()}catch(e){alert(e.message)}}
async function deleteTest(id){if(!confirm('Delete this test?'))return;try{await api('/api/tests/'+id,{method:'DELETE'});await loadTeacherTests()}catch(e){alert(e.message)}}
async function loadStudentResults(){studentTests=await api('/api/my-results');const weeks=[...new Set(studentTests.map(t=>t.week))].sort((a,b)=>a-b);$('studentWeek').innerHTML='<option value="">All Weeks</option>'+weeks.map(w=>`<option value="${w}">Week ${w}</option>`).join('');const subs=new Set();studentTests.forEach(t=>t.subjects.forEach(x=>subs.add(x.subject)));$('studentSubject').innerHTML='<option value="">All Subjects</option>'+[...subs].sort().map(s=>`<option>${esc(s)}</option>`).join('');renderStudentResults()}
function renderStudentResults(){const w=$('studentWeek').value,s=$('studentSubject').value;const arr=studentTests.filter(t=>(!w||String(t.week)===w)&&(!s||t.subjects.some(x=>x.subject===s)));$('studentResults').innerHTML=arr.length?arr.map(t=>`<div class="card result"><b>📅 ${esc(t.test_date)} — ${esc(t.test_title)}</b><br><span class="small">Week ${t.week}</span><hr>${t.subjects.filter(x=>!s||x.subject===s).map(x=>`<span class="pill">${esc(x.subject)}: ${x.status==='present'?x.obtained+'/'+x.maximum:statusText(x)}</span>`).join('')}<p><b>Total:</b> ${t.total_max?t.total_obtained+'/'+t.total_max:'—'} &nbsp; <b>Percentage:</b> ${t.percentage===null?'—':t.percentage+'%'}</p></div>`).join(''):'<div class="card">No results found for this filter.</div>'}
async function prepareAttendance(){if(!$('attDate').value)$('attDate').value=new Date().toISOString().slice(0,10)}
async function saveAttendance(){try{await api('/api/attendance',{method:'POST',body:JSON.stringify({student_id:Number($('attStudent').value),att_date:$('attDate').value,status:$('attStatus').value})});msg('attMsg','Attendance saved successfully',true);await loadAttendance()}catch(e){msg('attMsg',e.message)}}
async function loadAttendance(){try{const q=new URLSearchParams();if($('attFilterStudent').value)q.set('student_id',$('attFilterStudent').value);if($('attFrom').value)q.set('from',$('attFrom').value);if($('attTo').value)q.set('to',$('attTo').value);const data=await api('/api/attendance?'+q.toString());attendanceRows=data.rows;$('attendanceTable').innerHTML=attendanceRows.map(x=>`<tr><td>${esc(x.att_date)}</td><td>${esc(x.student_name)}<br><span class="small">${esc(x.roll_number)}</span></td><td>${statusText({status:x.status})}</td><td><button onclick="editAttendance(${x.id})">Edit</button><button class="danger" onclick="deleteAttendance(${x.id})">Delete</button></td></tr>`).join('')||'<tr><td colspan="4">No attendance records.</td></tr>';const s=data.summary;$('attendanceStats').innerHTML=`<div class="card"><b>Attendance Summary</b><div class="grid"><div><span class="small">Present</span><div class="kpi">${s.present}</div></div><div><span class="small">Absent</span><div class="kpi">${s.absent}</div></div><div><span class="small">Leave</span><div class="kpi">${s.leave}</div></div><div><span class="small">Attendance</span><div class="kpi">${s.percentage===null?'—':s.percentage+'%'}</div></div></div></div>`}catch(e){console.error(e)}}
async function editAttendance(id){const x=attendanceRows.find(r=>r.id===id);if(!x)return;const d=prompt('Date (YYYY-MM-DD):',x.att_date);if(d===null)return;const st=prompt('Status: present, absent, or leave',x.status);if(st===null)return;try{await api('/api/attendance/'+id,{method:'PUT',body:JSON.stringify({att_date:d,status:st.toLowerCase()})});await loadAttendance()}catch(e){alert(e.message)}}
async function deleteAttendance(id){if(!confirm('Delete this attendance record?'))return;try{await api('/api/attendance/'+id,{method:'DELETE'});await loadAttendance()}catch(e){alert(e.message)}}
async function loadStudentAttendance(){const d=await api('/api/my-attendance');const s=d.summary;$('studentAttendanceSummary').innerHTML=`<h3>📅 Attendance</h3><div class="grid"><div><span class="small">Present Days</span><div class="kpi">${s.present}</div></div><div><span class="small">Absent Days</span><div class="kpi">${s.absent}</div></div><div><span class="small">Leave Days</span><div class="kpi">${s.leave}</div></div><div><span class="small">Attendance</span><div class="kpi">${s.percentage===null?'—':s.percentage+'%'}</div></div></div>`}
function esc(v){return String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}
function js(v){return String(v??'').replace(/\\/g,'\\\\').replace(/'/g,"\\'")}
</script>
</body></html>'''

def db():
    con=sqlite3.connect(DB_FILE, timeout=10)
    con.row_factory=sqlite3.Row
    con.execute("PRAGMA foreign_keys=ON")
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA busy_timeout=10000")
    return con

def init_db():
    con=db()
    con.executescript('''
    CREATE TABLE IF NOT EXISTS students(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      name TEXT NOT NULL,
      roll_number TEXT NOT NULL UNIQUE
    );
    CREATE TABLE IF NOT EXISTS tests(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      student_id INTEGER NOT NULL,
      test_date TEXT NOT NULL,
      test_title TEXT NOT NULL,
      created_at TEXT NOT NULL,
      FOREIGN KEY(student_id) REFERENCES students(id) ON DELETE CASCADE
    );
    CREATE TABLE IF NOT EXISTS test_subjects(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      test_id INTEGER NOT NULL,
      subject TEXT NOT NULL,
      obtained REAL NOT NULL DEFAULT 0,
      maximum REAL NOT NULL DEFAULT 0,
      status TEXT NOT NULL DEFAULT 'present',
      FOREIGN KEY(test_id) REFERENCES tests(id) ON DELETE CASCADE
    );
    CREATE TABLE IF NOT EXISTS attendance(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      student_id INTEGER NOT NULL,
      att_date TEXT NOT NULL,
      status TEXT NOT NULL CHECK(status IN ('present','absent','leave')),
      UNIQUE(student_id,att_date),
      FOREIGN KEY(student_id) REFERENCES students(id) ON DELETE CASCADE
    );
    ''')
    cols=[r[1] for r in con.execute('PRAGMA table_info(test_subjects)').fetchall()]
    if 'status' not in cols:
        con.execute("ALTER TABLE test_subjects ADD COLUMN status TEXT NOT NULL DEFAULT 'present'")
    con.commit();con.close()

def send_json(h,data,status=200):
    raw=json.dumps(data,ensure_ascii=False).encode()
    h.send_response(status);h.send_header('Content-Type','application/json; charset=utf-8');h.send_header('Content-Length',str(len(raw)));h.send_header('Cache-Control','no-store');h.end_headers();h.wfile.write(raw)

def body(h):
    n=int(h.headers.get('Content-Length','0'));return json.loads(h.rfile.read(n) or b'{}')

def session(h):
    cookie=h.headers.get('Cookie','')
    for part in cookie.split(';'):
        if part.strip().startswith('sid='): return sessions.get(part.strip()[4:])
    return None

def require_teacher(h):
    if session(h)!='teacher':raise PermissionError()

def session_student_id(h):
    s=session(h)
    if not s or not s.startswith('student:'):raise PermissionError()
    return int(s.split(':',1)[1])

def test_obj(con,test_id):
    t=con.execute('''SELECT t.*,s.name student_name,s.roll_number FROM tests t JOIN students s ON s.id=t.student_id WHERE t.id=?''',(test_id,)).fetchone()
    if not t:return None
    subs=con.execute('SELECT subject,obtained,maximum,status FROM test_subjects WHERE test_id=? ORDER BY id',(test_id,)).fetchall()
    present=[x for x in subs if x['status']=='present']
    total=sum(float(x['obtained']) for x in present);mx=sum(float(x['maximum']) for x in present)
    return {'id':t['id'],'student_id':t['student_id'],'student_name':t['student_name'],'roll_number':t['roll_number'],'test_date':t['test_date'],'test_title':t['test_title'],'subjects':[dict(x) for x in subs],'total_obtained':round(total,2),'total_max':round(mx,2),'percentage':round(total/mx*100,2) if mx else None}

def all_tests(con,student_id=None,subject=None,fd=None,td=None):
    q='SELECT id FROM tests WHERE 1=1';args=[]
    if student_id:q+=' AND student_id=?';args.append(student_id)
    if fd:q+=' AND test_date>=?';args.append(fd)
    if td:q+=' AND test_date<=?';args.append(td)
    q+=' ORDER BY test_date DESC,id DESC'
    out=[]
    for r in con.execute(q,args):
        x=test_obj(con,r['id'])
        if x and (not subject or any(s['subject']==subject for s in x['subjects'])):out.append(x)
    return out

def week_number(con,test_date):
    row=con.execute('SELECT MIN(test_date) m FROM tests').fetchone()
    if not row['m']:return 1
    a=datetime.strptime(row['m'],'%Y-%m-%d').date();b=datetime.strptime(test_date,'%Y-%m-%d').date()
    return max(1,(b-a).days//7+1)

def attendance_summary(con,student_id=None,fd=None,td=None):
    q='SELECT status,COUNT(*) c FROM attendance WHERE 1=1';args=[]
    if student_id:q+=' AND student_id=?';args.append(student_id)
    if fd:q+=' AND att_date>=?';args.append(fd)
    if td:q+=' AND att_date<=?';args.append(td)
    q+=' GROUP BY status'
    counts={'present':0,'absent':0,'leave':0}
    for r in con.execute(q,args):counts[r['status']]=r['c']
    total=counts['present']+counts['absent']+counts['leave']
    return {'present':counts['present'],'absent':counts['absent'],'leave':counts['leave'],'total':total,'percentage':round(counts['present']/total*100,2) if total else None}

class Handler(BaseHTTPRequestHandler):
    def log_message(self,*a):pass
    def send_html(self):
        raw=HTML.encode();self.send_response(200);self.send_header('Content-Type','text/html; charset=utf-8');self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw)
    def do_GET(self):
        p=urlparse(self.path);qs={k:v[0] for k,v in parse_qs(p.query).items()}
        if p.path=='/':return self.send_html()
        try:
            if p.path=='/api/students':
                require_teacher(self);con=db();data=[dict(x) for x in con.execute("SELECT * FROM students ORDER BY roll_number")];con.close();return send_json(self,data)
            if p.path=='/api/tests':
                require_teacher(self);con=db();data=all_tests(con,int(qs['student_id']) if qs.get('student_id') else None,qs.get('subject'),qs.get('from'),qs.get('to'));con.close();return send_json(self,data)
            if p.path=='/api/my-results':
                sid=session_student_id(self);con=db();data=all_tests(con,sid);[x.update(week=week_number(con,x['test_date'])) for x in data];con.close();return send_json(self,data)
            if p.path=='/api/attendance':
                require_teacher(self);con=db();q='''SELECT a.*,s.name student_name,s.roll_number FROM attendance a JOIN students s ON s.id=a.student_id WHERE 1=1''';args=[]
                if qs.get('student_id'):q+=' AND a.student_id=?';args.append(int(qs['student_id']))
                if qs.get('from'):q+=' AND a.att_date>=?';args.append(qs['from'])
                if qs.get('to'):q+=' AND a.att_date<=?';args.append(qs['to'])
                q+=' ORDER BY a.att_date DESC,s.roll_number';rows=[dict(x) for x in con.execute(q,args)];summary=attendance_summary(con,int(qs['student_id']) if qs.get('student_id') else None,qs.get('from'),qs.get('to'));con.close();return send_json(self,{'rows':rows,'summary':summary})
            if p.path=='/api/my-attendance':
                sid=session_student_id(self);con=db();rows=[dict(x) for x in con.execute('SELECT att_date,status FROM attendance WHERE student_id=? ORDER BY att_date DESC',(sid,))];summary=attendance_summary(con,sid);con.close();return send_json(self,{'rows':rows,'summary':summary})
            if p.path=='/api/me':return send_json(self,{'role':session(self)})
            return send_json(self,{'error':'Not found'},404)
        except PermissionError:return send_json(self,{'error':'Not authorized'},401)
        except Exception as e:return send_json(self,{'error':str(e)},400)
    def do_POST(self):
        try:
            d=body(self)
            if self.path=='/api/login/teacher':
                if str(d.get('code',''))!=TEACHER_ACCESS_CODE:raise ValueError('Wrong teacher access code')
                sid=secrets.token_urlsafe(24);sessions[sid]='teacher';self.send_response(200);self.send_header('Set-Cookie',f'sid={sid}; HttpOnly; SameSite=Lax; Path=/');self.end_headers();return
            if self.path=='/api/login/student':
                if str(d.get('pin',''))!=STUDENT_PIN:raise ValueError('Wrong Student PIN')
                name=str(d.get('name','')).strip();roll=str(d.get('roll','')).strip()
                if not name and not roll:raise ValueError('Enter name or roll number')
                con=db();rows=con.execute('SELECT * FROM students').fetchall();matches=[r for r in rows if (not name or r['name'].lower()==name.lower()) and (not roll or r['roll_number']==roll)]
                if not matches and name and not roll:matches=[r for r in rows if r['name'].lower()==name.lower()]
                if len(matches)!=1:raise ValueError('Student not found, or roll number is needed for a duplicate name')
                sid=secrets.token_urlsafe(24);sessions[sid]=f"student:{matches[0]['id']}";raw=json.dumps({'student':dict(matches[0])}).encode();self.send_response(200);self.send_header('Content-Type','application/json');self.send_header('Set-Cookie',f'sid={sid}; HttpOnly; SameSite=Lax; Path=/');self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw);con.close();return
            if self.path=='/api/logout':
                c=self.headers.get('Cookie','');sid=c.split('sid=',1)[1].split(';',1)[0] if 'sid=' in c else None
                if sid:sessions.pop(sid,None)
                return send_json(self,{'ok':True})
            require_teacher(self)
            if self.path=='/api/students':
                n=str(d.get('name','')).strip();r=str(d.get('roll_number','')).strip()
                if not n or not r:raise ValueError('Name and roll number are required')
                con=db();con.execute('INSERT INTO students(name,roll_number) VALUES(?,?)',(n,r));con.commit();con.close();return send_json(self,{'ok':True})
            if self.path=='/api/tests':
                sid=int(d['student_id']);td=str(d['test_date']);title=str(d.get('test_title','Test')).strip() or 'Test';subs=d.get('subjects',[])
                if not subs:raise ValueError('Add at least one subject')
                con=db();cur=con.execute('INSERT INTO tests(student_id,test_date,test_title,created_at) VALUES(?,?,?,?)',(sid,td,title,datetime.now().isoformat()));tid=cur.lastrowid
                for x in subs:
                    if x.get('subject') not in SUBJECTS:raise ValueError('Invalid subject')
                    st=str(x.get('status','present')).lower()
                    if st not in ('present','absent','leave'):raise ValueError('Invalid status')
                    if st=='present':
                        if x.get('obtained') is None or x.get('maximum') is None:raise ValueError('Present subjects need obtained and maximum marks')
                        o=float(x['obtained']);m=float(x['maximum'])
                        if m<=0 or o<0 or o>m:raise ValueError('Marks must be valid and obtained cannot exceed maximum')
                    else:o=0;m=0
                    con.execute('INSERT INTO test_subjects(test_id,subject,obtained,maximum,status) VALUES(?,?,?,?,?)',(tid,x['subject'],o,m,st))
                con.commit();con.close();return send_json(self,{'ok':True,'id':tid})
            if self.path=='/api/attendance':
                sid=int(d['student_id']);ad=str(d['att_date']);st=str(d['status']).lower()
                if st not in ('present','absent','leave'):raise ValueError('Status must be present, absent, or leave')
                con=db();con.execute('INSERT INTO attendance(student_id,att_date,status) VALUES(?,?,?) ON CONFLICT(student_id,att_date) DO UPDATE SET status=excluded.status',(sid,ad,st));con.commit();con.close();return send_json(self,{'ok':True})
            return send_json(self,{'error':'Not found'},404)
        except sqlite3.IntegrityError:return send_json(self,{'error':'Roll number already exists or invalid duplicate attendance'},400)
        except PermissionError:return send_json(self,{'error':'Not authorized'},401)
        except Exception as e:return send_json(self,{'error':str(e)},400)
    def do_PUT(self):
        try:
            require_teacher(self);d=body(self)
            if self.path.startswith('/api/students/'):
                sid=int(self.path.rsplit('/',1)[1]);n=str(d.get('name','')).strip();r=str(d.get('roll_number','')).strip()
                if not n or not r:raise ValueError('Name and roll number are required')
                con=db();con.execute('UPDATE students SET name=?,roll_number=? WHERE id=?',(n,r,sid));con.commit();con.close();return send_json(self,{'ok':True})
            if self.path.startswith('/api/tests/'):
                tid=int(self.path.rsplit('/',1)[1]);con=db();con.execute('UPDATE tests SET test_date=?,test_title=? WHERE id=?',(d['test_date'],d['test_title'],tid));con.execute('DELETE FROM test_subjects WHERE test_id=?',(tid,))
                for x in d['subjects']:
                    st=str(x.get('status','present')).lower()
                    if st not in ('present','absent','leave'):raise ValueError('Invalid status')
                    if st=='present':o=float(x['obtained']);m=float(x['maximum']);
                    else:o=0;m=0
                    if st=='present' and (m<=0 or o<0 or o>m):raise ValueError('Invalid marks')
                    con.execute('INSERT INTO test_subjects(test_id,subject,obtained,maximum,status) VALUES(?,?,?,?,?)',(tid,x['subject'],o,m,st))
                con.commit();con.close();return send_json(self,{'ok':True})
            if self.path.startswith('/api/attendance/'):
                aid=int(self.path.rsplit('/',1)[1]);ad=str(d['att_date']);st=str(d['status']).lower()
                if st not in ('present','absent','leave'):raise ValueError('Invalid attendance status')
                con=db();con.execute('UPDATE attendance SET att_date=?,status=? WHERE id=?',(ad,st,aid));con.commit();con.close();return send_json(self,{'ok':True})
            return send_json(self,{'error':'Not found'},404)
        except PermissionError:return send_json(self,{'error':'Not authorized'},401)
        except sqlite3.IntegrityError:return send_json(self,{'error':'That student already has an attendance record for that date'},400)
        except Exception as e:return send_json(self,{'error':str(e)},400)
    def do_DELETE(self):
        try:
            require_teacher(self);con=db()
            if self.path.startswith('/api/students/'):sid=int(self.path.rsplit('/',1)[1]);con.execute('DELETE FROM students WHERE id=?',(sid,))
            elif self.path.startswith('/api/tests/'):tid=int(self.path.rsplit('/',1)[1]);con.execute('DELETE FROM tests WHERE id=?',(tid,))
            elif self.path.startswith('/api/attendance/'):aid=int(self.path.rsplit('/',1)[1]);con.execute('DELETE FROM attendance WHERE id=?',(aid,))
            else:return send_json(self,{'error':'Not found'},404)
            con.commit();con.close();return send_json(self,{'ok':True})
        except PermissionError:return send_json(self,{'error':'Not authorized'},401)
        except Exception as e:return send_json(self,{'error':str(e)},400)

if __name__=='__main__':
    init_db()
    print('📚 Class Test Result')
    print('Database:',os.path.abspath(DB_FILE))
    print('Running on port:',PORT)
    print('Open the forwarded port in your browser.')
    ThreadingHTTPServer((HOST,PORT),Handler).serve_forever()
