const STATS = ["stamina", "power", "shooting", "finishing", "passing", "dribbling"];
const state = {
  view: "squad",
  persona: "coach",
  squad: null,
  sessions: [],
  selectedSession: null,
  selectedPlayer: null,
  averages: null,
};

const $ = (sel) => document.querySelector(sel);

function persona() {
  return $("#persona").value;
}

async function api(path) {
  const res = await fetch(path);
  if (!res.ok) throw new Error(`${path} failed`);
  return res.json();
}

function setPill(el, flag) {
  el.className = `pill ${flag || "yellow"}`;
  el.textContent = ({ green: "Good form", yellow: "Mixed", red: "Needs work" })[flag] || "—";
}

function drawRadar(canvas, averages) {
  const ctx = canvas.getContext("2d");
  const w = canvas.width;
  const h = canvas.height;
  ctx.clearRect(0, 0, w, h);
  const cx = w / 2;
  const cy = h / 2 + 8;
  const r = Math.min(w, h) * 0.36;
  const n = STATS.length;

  ctx.strokeStyle = "#2a3d31";
  ctx.fillStyle = "rgba(125,255,179,0.12)";
  for (let ring = 1; ring <= 4; ring++) {
    ctx.beginPath();
    for (let i = 0; i <= n; i++) {
      const a = (-Math.PI / 2) + (i % n) * (Math.PI * 2 / n);
      const rr = (r * ring) / 4;
      const x = cx + Math.cos(a) * rr;
      const y = cy + Math.sin(a) * rr;
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    }
    ctx.closePath();
    ctx.stroke();
  }

  ctx.beginPath();
  STATS.forEach((key, i) => {
    const val = Number(averages[key] || 0) / 100;
    const a = (-Math.PI / 2) + i * (Math.PI * 2 / n);
    const x = cx + Math.cos(a) * r * val;
    const y = cy + Math.sin(a) * r * val;
    if (i === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  });
  ctx.closePath();
  ctx.fill();
  ctx.strokeStyle = "#7dffb3";
  ctx.lineWidth = 2;
  ctx.stroke();
  ctx.lineWidth = 1;

  ctx.fillStyle = "#9bb0a2";
  ctx.font = "12px DM Sans, sans-serif";
  ctx.textAlign = "center";
  STATS.forEach((key, i) => {
    const a = (-Math.PI / 2) + i * (Math.PI * 2 / n);
    const x = cx + Math.cos(a) * (r + 22);
    const y = cy + Math.sin(a) * (r + 22);
    ctx.fillText(key.slice(0, 3).toUpperCase(), x, y);
  });
}

function drawBars(canvas, players) {
  const ctx = canvas.getContext("2d");
  const w = canvas.width;
  const h = canvas.height;
  ctx.clearRect(0, 0, w, h);
  const counts = { green: 0, yellow: 0, red: 0 };
  players.forEach((p) => { counts[p.form_flag] = (counts[p.form_flag] || 0) + 1; });
  const keys = ["green", "yellow", "red"];
  const colors = { green: "#3dd68c", yellow: "#e6c35c", red: "#ff6b6b" };
  const labels = { green: "Good", yellow: "Mixed", red: "Weak" };
  const max = Math.max(...keys.map((k) => counts[k]), 1);
  const barW = 70;
  const gap = 40;
  const baseY = h - 40;
  const startX = (w - (keys.length * barW + (keys.length - 1) * gap)) / 2;

  keys.forEach((k, i) => {
    const bh = (counts[k] / max) * (h - 90);
    const x = startX + i * (barW + gap);
    const y = baseY - bh;
    ctx.fillStyle = colors[k];
    ctx.beginPath();
    ctx.roundRect(x, y, barW, bh, 8);
    ctx.fill();
    ctx.fillStyle = "#eef5ef";
    ctx.font = "bold 16px Space Grotesk, sans-serif";
    ctx.textAlign = "center";
    ctx.fillText(String(counts[k]), x + barW / 2, y - 10);
    ctx.fillStyle = "#9bb0a2";
    ctx.font = "13px DM Sans, sans-serif";
    ctx.fillText(labels[k], x + barW / 2, baseY + 22);
  });
}

function drawTrend(canvas, trend) {
  const ctx = canvas.getContext("2d");
  const w = canvas.width;
  const h = canvas.height;
  ctx.clearRect(0, 0, w, h);
  if (!trend || !trend.length) return;
  const pad = 28;
  const xs = trend.map((_, i) => pad + (i * (w - pad * 2)) / Math.max(trend.length - 1, 1));
  const ys = trend.map((t) => {
    const v = Number(t.overall);
    return h - pad - ((v - 30) / 70) * (h - pad * 2);
  });
  ctx.strokeStyle = "#2a3d31";
  ctx.beginPath();
  ctx.moveTo(pad, h - pad);
  ctx.lineTo(w - pad, h - pad);
  ctx.stroke();

  ctx.strokeStyle = "#7dffb3";
  ctx.lineWidth = 2.5;
  ctx.beginPath();
  xs.forEach((x, i) => {
    if (i === 0) ctx.moveTo(x, ys[i]);
    else ctx.lineTo(x, ys[i]);
  });
  ctx.stroke();
  trend.forEach((t, i) => {
    const color = t.verdict === "good" ? "#3dd68c" : t.verdict === "poor" ? "#ff6b6b" : "#e6c35c";
    ctx.fillStyle = color;
    ctx.beginPath();
    ctx.arc(xs[i], ys[i], 5, 0, Math.PI * 2);
    ctx.fill();
  });
}

function drawPitch(positions) {
  const svg = $("#pitch");
  svg.innerHTML = `
    <rect width="105" height="68" fill="#1a5c38"/>
    <rect x="0.5" y="0.5" width="104" height="67" fill="none" stroke="#d7ffe8" stroke-width="0.6" opacity="0.7"/>
    <line x1="52.5" y1="0" x2="52.5" y2="68" stroke="#d7ffe8" stroke-width="0.4" opacity="0.6"/>
    <circle cx="52.5" cy="34" r="9.15" fill="none" stroke="#d7ffe8" stroke-width="0.4" opacity="0.6"/>
  `;
  (positions || []).forEach((p) => {
    const color = p.verdict === "good" ? "#3dd68c" : p.verdict === "poor" ? "#ff6b6b" : "#e6c35c";
    const g = document.createElementNS("http://www.w3.org/2000/svg", "g");
    g.innerHTML = `
      <circle cx="${p.x}" cy="${p.y}" r="2.2" fill="${color}" stroke="#062314" stroke-width="0.35"/>
      <title>${p.name} · ${p.overall}</title>
    `;
    svg.appendChild(g);
  });
}

function miniStatRows(player) {
  return STATS.map((k) => {
    const v = Number(player[k] || 0);
    return `<div><span>${k.slice(0, 3)}</span><i><b style="width:${v}%"></b></i><em>${Math.round(v)}</em></div>`;
  }).join("");
}

function renderPlayerGrid(players) {
  const q = ($("#player-filter").value || "").toLowerCase();
  const grid = $("#player-grid");
  grid.innerHTML = players
    .filter((p) => !q || p.name.toLowerCase().includes(q))
    .map(
      (p) => `
      <button class="player-card" data-player="${p.player_id}">
        <div class="meta"><span>#${p.jersey} · ${p.position}</span><span class="pill ${p.form_flag}">${p.form_flag}</span></div>
        <strong>${p.name}</strong>
        <div class="meta"><span>Overall</span><span>${p.avg_overall}</span></div>
        <div class="mini-bars">${miniStatRows(p)}</div>
      </button>`
    )
    .join("");
  grid.querySelectorAll("[data-player]").forEach((btn) => {
    btn.addEventListener("click", () => {
      state.selectedPlayer = btn.dataset.player;
      switchView("player");
      loadPlayer(state.selectedPlayer);
    });
  });
}

function renderSessionList(sessions) {
  const ul = $("#session-list");
  ul.innerHTML = sessions
    .map(
      (s) => `
      <li>
        <button data-session="${s.session_id}" class="${state.selectedSession === s.session_id ? "active" : ""}">
          <strong>${s.title}</strong>
          <small>${s.date} · intensity ${s.intensity}/5 · avg ${s.avg_overall ?? "—"}</small>
        </button>
      </li>`
    )
    .join("");
  ul.querySelectorAll("[data-session]").forEach((btn) => {
    btn.addEventListener("click", () => loadSession(btn.dataset.session));
  });
}

function renderPlayerPicker(players) {
  const box = $("#player-picker");
  box.innerHTML = players
    .map(
      (p) => `
      <button data-pick="${p.player_id}" class="${state.selectedPlayer === p.player_id ? "active" : ""}">
        <strong>#${p.jersey} ${p.name}</strong>
        <small>${p.position}</small>
      </button>`
    )
    .join("");
  box.querySelectorAll("[data-pick]").forEach((btn) => {
    btn.addEventListener("click", () => {
      state.selectedPlayer = btn.dataset.pick;
      loadPlayer(state.selectedPlayer);
      renderPlayerPicker(players);
    });
  });
}

async function loadSquad() {
  const data = await api(`/api/metrics?query_id=squad&persona=${persona()}`);
  state.squad = data;
  state.averages = await api("/api/stats/averages");
  $("#insight").textContent = data.explanation.text;
  setPill($("#form-pill"), data.explanation.form_flag || data.facts.form_flag);
  drawRadar($("#radar"), state.averages);
  drawBars($("#bars"), data.facts.players);
  renderPlayerGrid(data.facts.players);
  renderPlayerPicker(data.facts.players);
}

async function loadSessions() {
  state.sessions = await api("/api/sessions");
  renderSessionList(state.sessions);
  if (!state.selectedSession && state.sessions.length) {
    await loadSession(state.sessions[0].session_id);
  }
}

async function loadSession(sessionId) {
  state.selectedSession = sessionId;
  renderSessionList(state.sessions);
  const data = await api(`/api/session/${sessionId}?persona=${persona()}`);
  const f = data.facts;
  $("#session-detail-title").textContent = `${f.title} · ${f.date}`;
  $("#session-detail-insight").textContent = data.explanation.text;
  drawPitch(f.positions);
  $("#session-logs").innerHTML = (f.logs || [])
    .map(
      (l) => `
      <tr>
        <td>${l.name}</td>
        <td>${l.overall}</td>
        <td>${l.stamina}</td>
        <td>${l.power}</td>
        <td>${l.shooting}</td>
        <td>${l.finishing}</td>
        <td>${l.passing}</td>
        <td>${l.dribbling}</td>
        <td class="verdict-${l.verdict}">${l.verdict}</td>
      </tr>`
    )
    .join("");
}

async function loadPlayer(playerId) {
  const data = await api(`/api/player/${playerId}?persona=${persona()}`);
  const f = data.facts;
  if (f.error) return;
  $("#player-name").textContent = `${f.name} · #${f.jersey} ${f.position}`;
  $("#player-insight").textContent = data.explanation.text;
  setPill($("#player-pill"), f.form_flag);
  drawTrend($("#trend"), f.trend);
  $("#player-stats").innerHTML = STATS.concat(["avg_overall"])
    .map((k) => {
      const label = k === "avg_overall" ? "Overall" : k;
      return `<div class="stat-chip"><span>${label}</span><strong>${f[k]}</strong></div>`;
    })
    .join("");
  $("#player-history").innerHTML = (f.history || [])
    .map(
      (h) => `
      <tr>
        <td>${h.date}</td>
        <td>${h.title}</td>
        <td>${h.overall}</td>
        <td class="verdict-${h.verdict}">${h.verdict}</td>
        <td>${Math.round(h.distance_m)} m</td>
      </tr>`
    )
    .join("");
}

function switchView(view) {
  state.view = view;
  document.querySelectorAll(".nav-btn").forEach((b) => {
    b.classList.toggle("active", b.dataset.view === view);
  });
  document.querySelectorAll(".view").forEach((v) => v.classList.remove("active"));
  $(`#view-${view}`).classList.add("active");
  $("#page-title").textContent =
    ({ squad: "Squad board", sessions: "Session logs", player: "Player focus" })[view];
}

async function boot() {
  document.querySelectorAll(".nav-btn").forEach((btn) => {
    btn.addEventListener("click", async () => {
      switchView(btn.dataset.view);
      if (btn.dataset.view === "sessions") await loadSessions();
      if (btn.dataset.view === "player" && state.selectedPlayer) await loadPlayer(state.selectedPlayer);
      if (btn.dataset.view === "squad") {
        $("#insight").textContent = state.squad?.explanation?.text || "";
        setPill($("#form-pill"), state.squad?.facts?.form_flag);
      }
    });
  });
  $("#refresh-btn").addEventListener("click", () => bootData());
  $("#persona").addEventListener("change", () => bootData());
  $("#player-filter").addEventListener("input", () => {
    if (state.squad?.facts?.players) renderPlayerGrid(state.squad.facts.players);
  });
  $("#note-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    if (!state.selectedPlayer) return;
    const text = $("#note-text").value.trim();
    if (!text) return;
    await fetch("/api/notes", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ player_id: state.selectedPlayer, text }),
    });
    $("#note-text").value = "";
    await loadPlayer(state.selectedPlayer);
  });
  await bootData();
}

async function bootData() {
  await loadSquad();
  await loadSessions();
  if (state.selectedPlayer) await loadPlayer(state.selectedPlayer);
}

boot().catch((err) => {
  $("#insight").textContent = `Failed to load: ${err.message}`;
});
