const $ = id => document.getElementById(id);
let personas = {}, current = localStorage.getItem("persona") || "tutor", history = [];
const key = () => "chat_" + current;

const esc = s => s.replace(/[&<>]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;"}[c]));
function render(text){
  return esc(text)
    .replace(/```(?:\w+)?\n?([\s\S]*?)```/g, "<pre><code>$1</code></pre>")
    .replace(/`([^`]+)`/g, "<code>$1</code>")
    .replace(/\*\*([^*]+)\*\*/g, "<b>$1</b>");
}
function add(role, text, cls=""){
  const d = document.createElement("div");
  d.className = "msg " + (role === "user" ? "user" : "bot") + " " + cls;
  d.innerHTML = role === "user" ? esc(text) : render(text);
  $("log").appendChild(d); $("log").scrollTop = 1e9; return d;
}
function load(){
  const p = personas[current];
  $("title").textContent = p.icon + " " + p.name; $("tag").textContent = p.tagline;
  history = JSON.parse(localStorage.getItem(key()) || "[]");
  $("log").innerHTML = "";
  if (!history.length) add("assistant", `Hi! I'm ${p.name}. ${p.tagline}. How can I help?`);
  history.forEach(m => add(m.role, m.content));
  document.querySelectorAll(".persona").forEach(b => b.classList.toggle("on", b.dataset.k === current));
}
async function send(){
  const t = $("input").value.trim(); if (!t) return;
  $("input").value = ""; $("send").disabled = true;
  history.push({role:"user", content:t}); add("user", t);
  const wait = add("assistant", "", ""); wait.innerHTML = '<span class="dots"><span></span><span></span><span></span></span>';
  try {
    const r = await fetch("/api/chat", {method:"POST", headers:{"Content-Type":"application/json"},
      body: JSON.stringify({persona: current, messages: history})});
    const j = await r.json();
    if (!r.ok) throw new Error(j.error || "Error");
    history.push({role:"assistant", content:j.reply}); wait.innerHTML = render(j.reply);
    localStorage.setItem(key(), JSON.stringify(history.slice(-40)));
  } catch(e){ wait.classList.add("err"); wait.textContent = e.message; history.pop(); }
  $("send").disabled = false; $("log").scrollTop = 1e9; $("input").focus();
}
(async () => {
  personas = await (await fetch("/api/personas")).json();
  if (!personas[current]) current = "tutor";
  for (const [k,p] of Object.entries(personas)){
    const b = document.createElement("button"); b.className = "persona"; b.dataset.k = k;
    b.innerHTML = `<span class="ic">${p.icon}</span><span><b>${p.name}</b><small>${p.tagline}</small></span>`;
    b.onclick = () => { current = k; localStorage.setItem("persona", k); load(); $("side").classList.remove("open"); };
    $("personas").appendChild(b);
  }
  load();
})();
$("send").onclick = send;
$("input").addEventListener("keydown", e => { if (e.key === "Enter" && !e.shiftKey){ e.preventDefault(); send(); }});
$("clear").onclick = () => { localStorage.removeItem(key()); load(); };
$("menu").onclick = () => $("side").classList.toggle("open");
