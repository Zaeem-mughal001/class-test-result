import json
import os
import secrets
import sqlite3
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

HOST = "0.0.0.0"
PORT = 8000

# CHANGE THESE TWO VALUES to your own codes. Keep the quotation marks.
TEACHER_ACCESS_CODE = "482917"
STUDENT_PIN = "735204"

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

HTML = r"""<!doctype html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>📚 Class Test Result</title>
<style>
*{box-sizing:border-box}body{margin:0;font-family:Arial,sans-serif;background:#f4f7fb;color:#18212f}
header{background:#173b67;color:white;padding:18px 16px;text-align:center}
main{max-width:1050px;margin:auto;padding:18px}
.card{background:white;border-radius:14px;padding:18px;margin:14px 0;box-shadow:0 3px 14px #00000012}
button{border:0;border-radius:9px;padding:10px 14px;background:#173b67;color:white;cursor:pointer;margin:3px}
button.secondary{background:#e7edf5;color:#173b67}.danger{background:#b42318}
input,select{width:100%;padding:10px;border:1px solid #cbd5e1;border-radius:8px;margin:5px 0 10px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:10px}
table{width:100%;border-collapse:collapse;background:white}th,td{padding:9px;border-bottom:1px solid #e5e7eb;text-align:left}
.small{font-size:13px;color:#64748b}.hidden{display:none}.pill{display:inline-block;padding:5px 9px;border-radius:20px;background:#e8f0fb;margin:3px}
.subject-row{border:1px solid #dbe3ee;border-radius:10px;padding:10px;margin:8px 0}
.result{border-left:4px solid #173b67;padding:12px;margin:10px 0;background:#f8fafc;border-radius:8px}
nav button{background:#fff;color:#173b67}
@media(max-width:600px){main{padding:10px}table{font-size:13px}.wide{overflow-x:auto}}
</style>
</head>
<body>
<header><h1>📚 Class Test Result</h1><div id="status" class="small" style="color:#dbeafe"></div></header>
<main>
<section id="home" class="card">
<h2>Welcome 👋</h2>
<p>Choose your login.</p>
<button onclick="show('studentLogin')">🎓 Student Login</button>
<button onclick="show('teacherLogin')">👨‍🏫 Teacher Login</button>
</section>

<section id="studentLogin" class="card hidden">
<h2>🎓 Student Login</h2>
<p class="small">Enter your name or roll number (or both) and the common Student PIN.</p>
<label>Name</label><input id="sName" placeholder="Student name">
<label>Roll Number</label><input id="sRoll" placeholder="Roll number">
<label>Student PIN</label><input id="sPin" type="password" placeholder="Student PIN">
<button onclick="studentLogin()">Login</button>
<button class="secondary" onclick="show('home')">Back</button>
<p id="studentMsg"></p>
</section>

<section id="teacherLogin" class="card hidden">
<h2>👨‍🏫 Teacher Login</h2>
<label>Teacher Access Code</label><input id="tCode" type="password" placeholder="Teacher access code">
<button onclick="teacherLogin()">Login</button>
<button class="secondary" onclick="show('home')">Back</button>
<p id="teacherMsg"></p>
</section>

<section id="studentPage" class="hidden">
<div class="card">
<button onclick="logout()">Logout</button>
<h2 id="studentTitle"></h2>
<div class="grid">
<div><label>Week</label><select id="studentWeek" onchange="renderStudentResults()"><option value="">All Weeks</option></select></div>
<div><label>Subject</label><select id="studentSubject" onchange="renderStudentResults()"><option value="">All Subjects</option></select></div>
</div>
</div>
<div id="studentResults"></div>
</section>

<section id="teacherPage" class="hidden">
<div class="card">
<button onclick="logout()">Logout</button>
<h2>👨‍🏫 Teacher Dashboard</h2>
<nav>
<button onclick="teacherTab('students')">👥 Students</button>
<button onclick="teacherTab('addTest')">➕ Add Test</button>
<button onclick="teacherTab('history')">📜 History</button>
</nav>
</div>

<div id="studentsTab" class="card">
<h3>Students</h3>
<div class="grid">
<div><label>Name</label><input id="newName"></div>
<div><label>Roll Number</label><input id="newRoll"></div>
</div>
<button onclick="addStudent()">Add Student</button>
<div class="wide"><table><thead><tr><th>Name</th><th>Roll</th><th>Action</th></tr></thead><tbody id="studentsTable"></tbody></table></div>
</div>

<div id="addTestTab" class="card hidden">
<h3>➕ Add Test Result</h3>
<div class="grid">
<div><label>Student</label><select id="testStudent"></select></div>
<div><label>Date</label><input id="testDate" type="date"></div>
<div><label>Test Title</label><input id="testTitle" placeholder="Daily Test"></div>
</div>
<h4>Subjects tested</h4>
<div id="subjectRows"></div>
<button class="secondary" onclick="addSubjectRow()">+ Add Subject</button><br>
<button onclick="saveTest()">Save Test</button>
<p id="testMsg"></p>
</div>

<div id="historyTab" class="card hidden">
<h3>📜 Result History</h3>
<div class="grid">
<div><label>Student</label><select id="filterStudent" onchange="loadTeacherTests()"><option value="">All Students</option></select></div>
<div><label>Subject</label><select id="filterSubject" onchange="loadTeacherTests()"><option value="">All Subjects</option></select></div>
<div><label>From</label><input id="fromDate" type="date" onchange="loadTeacherTests()"></div>
<div><label>To</label><input id="toDate" type="date" onchange="loadTeacherTests()"></div>
</div>
<div class="wide"><table><thead><tr><th>Date</th><th>Student</th><th>Test</th><th>Subjects / Marks</th><th>Total</th><th>%</th><th>Action</th></tr></thead><tbody id="testsTable"></tbody></table></div>
</div>
</section>
</main>

<script>
const SUBJECTS = ["English","Urdu","Mathematics","Computer Science","Physics","Chemistry"];
const $=id=>document.getElementById(id);
let currentStudent=null, teacherStudents=[], teacherTests=[], studentTests=[];

function show(id){
  ["home","studentLogin","teacherLogin","studentPage","teacherPage"].forEach(x=>$(x).classList.add("hidden"));
  $(id).classList.remove("hidden");
}
function msg(id,text,ok=false){$(id).textContent=text;$(id).style.color=ok?"#087443":"#b42318"}

async function api(url,opt={}){
  const r=await fetch(url,{headers:{"Content-Type":"application/json"},...opt});
  const data=await r.json().catch(()=>({}));
  if(!r.ok) throw new Error(data.error||"Request failed");
  return data;
}
async function studentLogin(){
  try{
    const data=await api("/api/login/student",{method:"POST",body:JSON.stringify({name:$("sName").value.trim(),roll:$("sRoll").value.trim(),pin:$("sPin").value})});
    currentStudent=data.student;
    $("studentTitle").textContent="🎓 "+data.student.name+" — Roll "+data.student.roll_number;
    show("studentPage"); await loadStudentResults();
  }catch(e){msg("studentMsg",e.message)}
}
async function teacherLogin(){
  try{await api("/api/login/teacher",{method:"POST",body:JSON.stringify({code:$("tCode").value}));show("teacherPage");await openTeacher()}
  catch(e){msg("teacherMsg",e.message)}
}
async function logout(){await api("/api/logout",{method:"POST"});location.reload()}

function teacherTab(tab){
  ["studentsTab","addTestTab","historyTab"].forEach(x=>$(x).classList.add("hidden"));
  $(tab+"Tab").classList.remove("hidden");
  if(tab==="students")loadStudents();
  if(tab==="addTest")prepareAddTest();
  if(tab==="history")loadTeacherTests();
}
async function openTeacher(){await loadStudents();prepareAddTest();await loadTeacherTests()}

async function loadStudents(){
  teacherStudents=await api("/api/students");
  $("studentsTable").innerHTML=teacherStudents.map(s=>`<tr><td>${esc(s.name)}</td><td>${esc(s.roll_number)}</td><td><button onclick="editStudent(${s.id},'${js(s.name)}','${js(s.roll_number)}')">Edit</button><button class="danger" onclick="deleteStudent(${s.id})">Delete</button></td></tr>`).join("");
  const opts=teacherStudents.map(s=>`<option value="${s.id}">${esc(s.name)} — ${esc(s.roll_number)}</option>`).join("");
  $("testStudent").innerHTML=opts;
  $("filterStudent").innerHTML='<option value="">All Students</option>'+opts;
}
async function addStudent(){
  try{await api("/api/students",{method:"POST",body:JSON.stringify({name:$("newName").value.trim(),roll_number:$("newRoll").value.trim()})});$("newName").value="";$("newRoll").value="";await loadStudents();msg("testMsg","Student added",true)}
  catch(e){alert(e.message)}
}
async function editStudent(id,name,roll){
  const n=prompt("Student name:",name);if(n===null)return;
  const r=prompt("Roll number:",roll);if(r===null)return;
  try{await api("/api/students/"+id,{method:"PUT",body:JSON.stringify({name:n,roll_number:r})});await loadStudents();await loadTeacherTests()}
  catch(e){alert(e.message)}
}
async function deleteStudent(id){
  if(!confirm("Delete this student and their results?"))return;
  try{await api("/api/students/"+id,{method:"DELETE"});await loadStudents();await loadTeacherTests()}catch(e){alert(e.message)}
}

function prepareAddTest(){
  $("testDate").value=new Date().toISOString().slice(0,10);
  if(!$("subjectRows").children.length)addSubjectRow();
}
function addSubjectRow(){
  const div=document.createElement("div");div.className="subject-row";
  div.innerHTML=`<div class="grid"><div><label>Subject</label><select class="sub">${SUBJECTS.map(s=>`<option>${s}</option>`).join("")}</select></div><div><label>Obtained Marks</label><input class="obt" type="number" min="0" step="0.01"></div><div><label>Maximum Marks</label><input class="max" type="number" min="0.01" step="0.01"></div><div><button class="danger" onclick="this.parentElement.parentElement.parentElement.remove()">Remove</button></div></div>`;
  $("subjectRows").appendChild(div);
}
async function saveTest(){
  const rows=[...document.querySelectorAll(".subject-row")].map(r=>({subject:r.querySelector(".sub").value,obtained:Number(r.querySelector(".obt").value),maximum:Number(r.querySelector(".max").value)}));
  try{
    await api("/api/tests",{method:"POST",body:JSON.stringify({student_id:Number($("testStudent").value),test_date:$("testDate").value,test_title:$("testTitle").value.trim()||"Test",subjects:rows})});
    msg("testMsg","Test saved successfully ✅",true);$("testTitle").value="";$("subjectRows").innerHTML="";addSubjectRow();await loadTeacherTests();
  }catch(e){msg("testMsg",e.message)}
}

async function loadTeacherTests(){
  const p=new URLSearchParams();if($("filterStudent").value)p.set("student_id",$("filterStudent").value);if($("filterSubject").value)p.set("subject",$("filterSubject").value);if($("fromDate").value)p.set("from",$("fromDate").value);if($("toDate").value)p.set("to",$("toDate").value);
  teacherTests=await api("/api/tests?"+p.toString());setupSubjectFilter();
  $("testsTable").innerHTML=teacherTests.map(t=>`<tr><td>${esc(t.test_date)}</td><td>${esc(t.student_name)}<br>${esc(t.roll_number)}</td><td>${esc(t.test_title)}</td><td>${t.subjects.map(x=>`${esc(x.subject)}: ${x.obtained}/${x.maximum}`).join("<br>")}</td><td>${t.total_obtained}/${t.total_max}</td><td>${t.percentage}%</td><td><button onclick="editTest(${t.id})">Edit</button><button class="danger" onclick="deleteTest(${t.id})">Delete</button></td></tr>`).join("");
}
function setupSubjectFilter(){
  const old=$("filterSubject").value;
  const set=new Set();teacherTests.forEach(t=>t.subjects.forEach(x=>set.add(x.subject)));
  $("filterSubject").innerHTML='<option value="">All Subjects</option>'+[...set].sort().map(s=>`<option>${esc(s)}</option>`).join("");
  $("filterSubject").value=old;
}
async function editTest(id){
  const t=teacherTests.find(x=>x.id===id);if(!t)return;
  const title=prompt("Test title:",t.test_title);if(title===null)return;
  const date=prompt("Date (YYYY-MM-DD):",t.test_date);if(date===null)return;
  const subjects=t.subjects.map(x=>{const o=prompt(`${x.subject} obtained / maximum`,`${x.obtained}/${x.maximum}`);if(o===null)return null;const parts=o.split("/");return {subject:x.subject,obtained:Number(parts[0]),maximum:Number(parts[1])}}).filter(Boolean);
  try{await api("/api/tests/"+id,{method:"PUT",body:JSON.stringify({test_date:date,test_title:title,subjects})});await loadTeacherTests()}catch(e){alert(e.message)}
}
async function deleteTest(id){if(!confirm("Delete this test?"))return;try{await api("/api/tests/"+id,{method:"DELETE"});await loadTeacherTests()}catch(e){alert(e.message)}}

async function loadStudentResults(){
  studentTests=await api("/api/my-results");const weeks=[...new Set(studentTests.map(t=>t.week))].sort((a,b)=>a-b);
  $("studentWeek").innerHTML='<option value="">All Weeks</option>'+weeks.map(w=>`<option value="${w}">Week ${w}</option>`).join("");
  const subs=new Set();studentTests.forEach(t=>t.subjects.forEach(x=>subs.add(x.subject)));
  $("studentSubject").innerHTML='<option value="">All Subjects</option>'+[...subs].sort().map(s=>`<option>${esc(s)}</option>`).join("");
  renderStudentResults();
}
function renderStudentResults(){
  const w=$("studentWeek").value,s=$("studentSubject").value;
  let arr=studentTests.filter(t=>(!w||String(t.week)===w)&&(!s||t.subjects.some(x=>x.subject===s)));
  $("studentResults").innerHTML=arr.length?arr.map(t=>`<div class="card result"><b>📅 ${esc(t.test_date)} — ${esc(t.test_title)}</b><br><span class="small">Week ${t.week}</span><hr>${t.subjects.filter(x=>!s||x.subject===s).map(x=>`<span class="pill">${esc(x.subject)}: ${x.obtained}/${x.maximum}</span>`).join("")}<p><b>Total:</b> ${t.total_obtained}/${t.total_max} &nbsp; <b>Percentage:</b> ${t.percentage}%</p></div>`).join(""):'<div class="card">No results found for this filter.</div>';
}
function esc(v){return String(v??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]))}
function js(v){return String(v??"").replace(/\\/g,"\\\\").replace(/'/g,"\\'")}

</script>
</body>
</html>"""

def db():
    con = sqlite3.connect(DB_FILE)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys=ON")
    return con

def init_db():
    con=db()
    con.executescript("""
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
      obtained REAL NOT NULL,
      maximum REAL NOT NULL,
      FOREIGN KEY(test_id) REFERENCES tests(id) ON DELETE CASCADE
    );
    """)
    con.commit();con.close()

def send_json(h,data,status=200):
    raw=json.dumps(data,ensure_ascii=False).encode()
    h.send_response(status);h.send_header("Content-Type","application/json; charset=utf-8")
    h.send_header("Content-Length",str(len(raw)));h.send_header("Cache-Control","no-store");h.end_headers();h.wfile.write(raw)

def body(h):
    n=int(h.headers.get("Content-Length","0"));return json.loads(h.rfile.read(n) or b"{}")

def session(h):
    cookie=h.headers.get("Cookie","")
    for part in cookie.split(";"):
        if part.strip().startswith("sid="):
            return sessions.get(part.strip()[4:])
    return None

def require_teacher(h):
    if session(h)!="teacher": raise PermissionError()

def test_obj(con,test_id):
    t=con.execute("""SELECT t.*,s.name student_name,s.roll_number FROM tests t
                     JOIN students s ON s.id=t.student_id WHERE t.id=?""",(test_id,)).fetchone()
    if not t:return None
    subs=con.execute("SELECT subject,obtained,maximum FROM test_subjects WHERE test_id=? ORDER BY id",(test_id,)).fetchall()
    total=sum(float(x["obtained"]) for x in subs);mx=sum(float(x["maximum"]) for x in subs)
    return {"id":t["id"],"student_id":t["student_id"],"student_name":t["student_name"],"roll_number":t["roll_number"],
            "test_date":t["test_date"],"test_title":t["test_title"],"subjects":[dict(x) for x in subs],
            "total_obtained":round(total,2),"total_max":round(mx,2),"percentage":round(total/mx*100,2) if mx else 0}

def all_tests(con,student_id=None,subject=None,fd=None,td=None):
    q="SELECT id FROM tests WHERE 1=1";args=[]
    if student_id:q+=" AND student_id=?";args.append(student_id)
    if fd:q+=" AND test_date>=?";args.append(fd)
    if td:q+=" AND test_date<=?";args.append(td)
    q+=" ORDER BY test_date DESC,id DESC"
    ids=[r["id"] for r in con.execute(q,args)]
    out=[]
    for i in ids:
        x=test_obj(con,i)
        if x and (not subject or any(s["subject"]==subject for s in x["subjects"])):out.append(x)
    return out

def week_number(con,test_date):
    row=con.execute("SELECT MIN(test_date) m FROM tests").fetchone()
    if not row["m"]:return 1
    a=datetime.strptime(row["m"],"%Y-%m-%d").date();b=datetime.strptime(test_date,"%Y-%m-%d").date()
    return max(1,(b-a).days//7+1)

class Handler(BaseHTTPRequestHandler):
    def log_message(self,*a):pass
    def send_html(self):
        raw=HTML.encode();self.send_response(200);self.send_header("Content-Type","text/html; charset=utf-8");self.send_header("Content-Length",str(len(raw)));self.end_headers();self.wfile.write(raw)
    def do_GET(self):
        p=urlparse(self.path)
        if p.path=="/":return self.send_html()
        try:
            if p.path=="/api/students":
                require_teacher(self);con=db();data=[dict(x) for x in con.execute("SELECT * FROM students ORDER BY CAST(roll_number AS INTEGER),roll_number")];con.close();return send_json(self,data)
            if p.path=="/api/tests":
                require_teacher(self);qs=dict(x.split("=",1) for x in p.query.split("&") if "=" in x)
                con=db();data=all_tests(con,int(qs["student_id"]) if qs.get("student_id") else None,qs.get("subject"),qs.get("from"),qs.get("to"));con.close();return send_json(self,data)
            if p.path=="/api/my-results":
                if session(self)!="student":raise PermissionError()
                con=db();data=all_tests(con,session_student_id(self));con.close()
                for x in data:x["week"]=week_number(db(),x["test_date"])
                return send_json(self,data)
            if p.path=="/api/me":
                return send_json(self,{"role":session(self)})
            return send_json(self,{"error":"Not found"},404)
        except PermissionError:return send_json(self,{"error":"Not authorized"},401)
        except Exception as e:return send_json(self,{"error":str(e)},400)
    def do_POST(self):
        try:
            d=body(self)
            if self.path=="/api/login/teacher":
                if str(d.get("code",""))!=TEACHER_ACCESS_CODE:raise ValueError("Wrong teacher access code")
                sid=secrets.token_urlsafe(24);sessions[sid]="teacher";self.send_response(200);self.send_header("Set-Cookie",f"sid={sid}; HttpOnly; SameSite=Lax; Path=/");self.end_headers();return
            if self.path=="/api/login/student":
                if str(d.get("pin",""))!=STUDENT_PIN:raise ValueError("Wrong Student PIN")
                name=str(d.get("name","")).strip();roll=str(d.get("roll","")).strip()
                if not name and not roll:raise ValueError("Enter name or roll number")
                con=db();rows=con.execute("SELECT * FROM students").fetchall()
                matches=[r for r in rows if (not name or r["name"].lower()==name.lower()) and (not roll or r["roll_number"]==roll)]
                if not matches and name and not roll:matches=[r for r in rows if r["name"].lower()==name.lower()]
                if len(matches)!=1:raise ValueError("Student not found, or roll number is needed for a duplicate name")
                sid=secrets.token_urlsafe(24);sessions[sid]=f"student:{matches[0]['id']}";self.send_response(200);self.send_header("Content-Type","application/json");self.send_header("Set-Cookie",f"sid={sid}; HttpOnly; SameSite=Lax; Path=/");raw=json.dumps({"student":dict(matches[0])}).encode();self.send_header("Content-Length",str(len(raw)));self.end_headers();self.wfile.write(raw);con.close();return
            if self.path=="/api/logout":
                c=self.headers.get("Cookie","");sid=c.split("sid=",1)[1].split(";",1)[0] if "sid=" in c else None
                if sid:sessions.pop(sid,None)
                return send_json(self,{"ok":True})
            require_teacher(self)
            if self.path=="/api/students":
                n=str(d.get("name","")).strip();r=str(d.get("roll_number","")).strip()
                if not n or not r:raise ValueError("Name and roll number are required")
                con=db();con.execute("INSERT INTO students(name,roll_number) VALUES(?,?)",(n,r));con.commit();con.close();return send_json(self,{"ok":True})
            if self.path=="/api/tests":
                sid=int(d["student_id"]);date=str(d["test_date"]);title=str(d.get("test_title","Test")).strip() or "Test";subs=d.get("subjects",[])
                if not subs:raise ValueError("Add at least one subject")
                con=db();cur=con.execute("INSERT INTO tests(student_id,test_date,test_title,created_at) VALUES(?,?,?,?)",(sid,date,title,datetime.now().isoformat()))
                tid=cur.lastrowid
                for x in subs:
                    if x["subject"] not in SUBJECTS:raise ValueError("Invalid subject")
                    o=float(x["obtained"]);m=float(x["maximum"])
                    if m<=0 or o<0 or o>m:raise ValueError("Marks must be valid and obtained cannot exceed maximum")
                    con.execute("INSERT INTO test_subjects(test_id,subject,obtained,maximum) VALUES(?,?,?,?)",(tid,x["subject"],o,m))
                con.commit();con.close();return send_json(self,{"ok":True,"id":tid})
            return send_json(self,{"error":"Not found"},404)
        except sqlite3.IntegrityError:return send_json(self,{"error":"Roll number already exists"},400)
        except PermissionError:return send_json(self,{"error":"Not authorized"},401)
        except Exception as e:return send_json(self,{"error":str(e)},400)
    def do_PUT(self):
        try:
            require_teacher(self);d=body(self)
            if self.path.startswith("/api/students/"):
                sid=int(self.path.rsplit("/",1)[1]);n=str(d.get("name","")).strip();r=str(d.get("roll_number","")).strip()
                con=db();con.execute("UPDATE students SET name=?,roll_number=? WHERE id=?",(n,r,sid));con.commit();con.close();return send_json(self,{"ok":True})
            if self.path.startswith("/api/tests/"):
                tid=int(self.path.rsplit("/",1)[1]);con=db()
                con.execute("UPDATE tests SET test_date=?,test_title=? WHERE id=?",(d["test_date"],d["test_title"],tid))
                con.execute("DELETE FROM test_subjects WHERE test_id=?",(tid,))
                for x in d["subjects"]:
                    o=float(x["obtained"]);m=float(x["maximum"])
                    if m<=0 or o<0 or o>m:raise ValueError("Invalid marks")
                    con.execute("INSERT INTO test_subjects(test_id,subject,obtained,maximum) VALUES(?,?,?,?)",(tid,x["subject"],o,m))
                con.commit();con.close();return send_json(self,{"ok":True})
            return send_json(self,{"error":"Not found"},404)
        except PermissionError:return send_json(self,{"error":"Not authorized"},401)
        except Exception as e:return send_json(self,{"error":str(e)},400)
    def do_DELETE(self):
        try:
            require_teacher(self);con=db()
            if self.path.startswith("/api/students/"):
                sid=int(self.path.rsplit("/",1)[1]);con.execute("DELETE FROM students WHERE id=?",(sid,))
            elif self.path.startswith("/api/tests/"):
                tid=int(self.path.rsplit("/",1)[1]);con.execute("DELETE FROM tests WHERE id=?",(tid,))
            else:return send_json(self,{"error":"Not found"},404)
            con.commit();con.close();return send_json(self,{"ok":True})
        except PermissionError:return send_json(self,{"error":"Not authorized"},401)
        except Exception as e:return send_json(self,{"error":str(e)},400)

def session_student_id(h):
    s=session(h)
    if not s or not s.startswith("student:"):raise PermissionError()
    return int(s.split(":",1)[1])

if __name__=="__main__":
    init_db()
    print("📚 Class Test Result")
    print("Database:",os.path.abspath(DB_FILE))
    print("Running on port:",PORT)
    print("Open the forwarded port in your browser.")
    ThreadingHTTPServer((HOST,PORT),Handler).serve_forever()
