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

function shirtNumber(row) {
  const n = row?.jersey ?? row?.number ?? row?.shirt;
  if (n === null || n === undefined || n === "") return null;
  const num = Number(n);
  return Number.isFinite(num) ? String(Math.trunc(num)) : String(n);
}

/** Fallback formation if API positions lack coordinates (offline / old server). */
const FORMATION_SLOTS = {
  GK: [[10, 28], [10, 40]],
  DF: [[32, 10], [32, 24], [32, 38], [32, 52]],
  MF: [[55, 10], [55, 24], [55, 38], [55, 52]],
  FW: [[80, 14], [80, 28], [80, 42], [80, 56]],
};

function pitchMarkersFromSession(facts) {
  const positions = facts?.positions || [];
  if (positions.length && positions.every((p) => p.jersey != null && p.x != null)) {
    return positions;
  }
  const logs = facts?.logs || [];
  const grouped = { GK: [], DF: [], MF: [], FW: [] };
  logs.forEach((l) => {
    const pos = String(l.position || "MF").toUpperCase();
    (grouped[pos] || grouped.MF).push(l);
  });
  const out = [];
  ["GK", "DF", "MF", "FW"].forEach((line) => {
    const band = FORMATION_SLOTS[line];
    grouped[line]
      .slice()
      .sort((a, b) => Number(a.jersey) - Number(b.jersey))
      .forEach((l, i) => {
        const [x, y] = band[Math.min(i, band.length - 1)];
        out.push({
          player_id: l.player_id,
          name: l.name,
          position: l.position,
          jersey: l.jersey,
          x: i < band.length ? x : x + 4,
          y,
          overall: l.overall,
          verdict: l.verdict,
          stamina: l.stamina,
          power: l.power,
          shooting: l.shooting,
          finishing: l.finishing,
          passing: l.passing,
          dribbling: l.dribbling,
          line,
        });
      });
  });
  return out;
}

function hidePitchPopover() {
  const pop = $("#pitch-popover");
  if (pop) pop.hidden = true;
}

function showPitchPopover(marker, clientX, clientY) {
  const pop = $("#pitch-popover");
  const wrap = $("#pitch-wrap");
  if (!pop || !wrap) return;
  const num = shirtNumber(marker) || "—";
  const stats = ["overall", "stamina", "power", "shooting", "finishing", "passing", "dribbling"]
    .filter((k) => marker[k] != null)
    .map((k) => `<div><span>${k}</span> <b>${marker[k]}</b></div>`)
    .join("");
  pop.innerHTML = `
    <strong>#${num} ${marker.name || ""}</strong>
    <div class="pop-meta">${marker.position || marker.line || "—"} · ${marker.verdict || "—"}</div>
    <div class="pop-stats">${stats}</div>
  `;
  pop.hidden = false;
  const rect = wrap.getBoundingClientRect();
  let left = clientX - rect.left + 12;
  let top = clientY - rect.top + 12;
  pop.style.left = "0px";
  pop.style.top = "0px";
  const pw = pop.offsetWidth;
  const ph = pop.offsetHeight;
  if (left + pw > rect.width - 8) left = Math.max(8, rect.width - pw - 8);
  if (top + ph > rect.height - 8) top = Math.max(8, clientY - rect.top - ph - 12);
  pop.style.left = `${left}px`;
  pop.style.top = `${top}px`;
}

function drawPitch(markers) {
  const svg = $("#pitch");
  while (svg.firstChild) svg.removeChild(svg.firstChild);
  hidePitchPopover();

  const ns = "http://www.w3.org/2000/svg";
  const add = (tag, attrs = {}) => {
    const el = document.createElementNS(ns, tag);
    Object.entries(attrs).forEach(([k, v]) => el.setAttribute(k, String(v)));
    svg.appendChild(el);
    return el;
  };

  add("rect", { width: 105, height: 68, fill: "#1a5c38" });
  add("rect", {
    x: 0.5, y: 0.5, width: 104, height: 67,
    fill: "none", stroke: "#d7ffe8", "stroke-width": 0.6, opacity: 0.7,
  });
  add("line", {
    x1: 52.5, y1: 0, x2: 52.5, y2: 68,
    stroke: "#d7ffe8", "stroke-width": 0.4, opacity: 0.6,
  });
  add("circle", {
    cx: 52.5, cy: 34, r: 9.15,
    fill: "none", stroke: "#d7ffe8", "stroke-width": 0.4, opacity: 0.6,
  });
  // Goal mouths (left = GK side)
  add("rect", {
    x: 0.5, y: 24, width: 5.5, height: 20,
    fill: "none", stroke: "#d7ffe8", "stroke-width": 0.35, opacity: 0.55,
  });
  add("rect", {
    x: 99, y: 24, width: 5.5, height: 20,
    fill: "none", stroke: "#d7ffe8", "stroke-width": 0.35, opacity: 0.55,
  });

  (markers || []).forEach((p) => {
    const color = p.verdict === "good" ? "#3dd68c" : p.verdict === "poor" ? "#ff6b6b" : "#e6c35c";
    const num = shirtNumber(p) || "·";
    const g = document.createElementNS(ns, "g");
    g.classList.add("pitch-token");
    g.setAttribute("tabindex", "0");
    g.setAttribute("role", "button");
    g.setAttribute("aria-label", `#${num} ${p.name || ""} stats`);
    g.dataset.playerId = p.player_id || "";
    svg.appendChild(g);

    const circle = document.createElementNS(ns, "circle");
    circle.setAttribute("cx", p.x);
    circle.setAttribute("cy", p.y);
    circle.setAttribute("r", "3.4");
    circle.setAttribute("fill", color);
    circle.setAttribute("stroke", "#062314");
    circle.setAttribute("stroke-width", "0.45");
    g.appendChild(circle);

    const text = document.createElementNS(ns, "text");
    text.setAttribute("x", p.x);
    text.setAttribute("y", p.y);
    text.setAttribute("text-anchor", "middle");
    text.setAttribute("dominant-baseline", "central");
    text.setAttribute("font-size", "2.7");
    text.setAttribute("font-weight", "700");
    text.setAttribute("fill", "#062314");
    text.style.pointerEvents = "none";
    text.textContent = num;
    g.appendChild(text);

    const open = (evt) => {
      evt.preventDefault();
      const pt = evt.clientX != null ? evt : (evt.touches && evt.touches[0]);
      if (pt) showPitchPopover(p, pt.clientX, pt.clientY);
    };
    g.addEventListener("mouseenter", open);
    g.addEventListener("mousemove", open);
    g.addEventListener("mouseleave", hidePitchPopover);
    g.addEventListener("click", (evt) => {
      open(evt);
      if (p.player_id) {
        state.selectedPlayer = p.player_id;
        // Keep popover; also jump to player focus on double-intent via focus view
      }
    });
    g.addEventListener("keydown", (evt) => {
      if (evt.key === "Enter" || evt.key === " ") {
        const rect = g.getBoundingClientRect();
        showPitchPopover(p, rect.left + rect.width / 2, rect.top);
      }
    });
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
  const select = $("#session-select");
  const chips = $("#session-chips");
  if (!select || !chips) return;

  select.innerHTML = sessions
    .map(
      (s) =>
        `<option value="${s.session_id}" ${
          state.selectedSession === s.session_id ? "selected" : ""
        }>${s.date} — ${s.title}</option>`
    )
    .join("");

  // Show a short chip row (newest first already from API); keep page scannable.
  const shown = sessions.slice(0, 8);
  chips.innerHTML = shown
    .map(
      (s) => `
      <button type="button" class="session-chip ${
        state.selectedSession === s.session_id ? "active" : ""
      }" data-session="${s.session_id}" role="option" aria-selected="${
        state.selectedSession === s.session_id
      }">
        <strong>${s.title}</strong>
        <small>${s.date} · int ${s.intensity}/5</small>
      </button>`
    )
    .join("");

  chips.querySelectorAll("[data-session]").forEach((btn) => {
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
  const id = state.selectedSession || state.sessions[0]?.session_id;
  if (id) await loadSession(id);
}

async function loadSession(sessionId) {
  state.selectedSession = sessionId;
  renderSessionList(state.sessions);
  const data = await api(`/api/session/${sessionId}?persona=${persona()}`);
  const f = data.facts;
  if (f.error) {
    $("#session-detail-insight").textContent = "Could not load that session.";
    return;
  }

  $("#session-detail-title").textContent = f.title;
  $("#session-detail-insight").textContent = data.explanation.text;

  const meta = $("#session-meta");
  meta.hidden = false;
  $("#session-date-chip").textContent = f.date;
  $("#session-intensity-chip").textContent = `Intensity ${f.intensity}/5 · ${f.duration_min} min`;
  $("#session-avg-chip").textContent = `Squad avg ${f.avg_overall}`;
  setPill($("#session-form-pill"), f.form_flag);

  // Always refresh the page header when session data arrives (not only if already on Sessions).
  if (state.view === "sessions") {
    $("#insight").textContent = data.explanation.text;
    setPill($("#form-pill"), f.form_flag);
  }

  // Use logs for pitch markers — they always include jersey + coordinates.
  drawPitch(pitchMarkersFromSession(f));
  $("#session-logs").innerHTML = (f.logs || [])
    .map((l) => {
      const num = shirtNumber(l) || "—";
      return `
      <tr>
        <td class="shirt-num">${num}</td>
        <td class="player-cell">${l.name}</td>
        <td class="pos-cell">${l.position || "—"}</td>
        <td>${l.overall}</td>
        <td>${l.stamina}</td>
        <td>${l.power}</td>
        <td>${l.shooting}</td>
        <td>${l.finishing}</td>
        <td>${l.passing}</td>
        <td>${l.dribbling}</td>
        <td class="verdict-${l.verdict}">${l.verdict}</td>
      </tr>`;
    })
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
  $("#session-select")?.addEventListener("change", (e) => {
    if (e.target.value) loadSession(e.target.value);
  });
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
  try {
    await loadSquad();
  } catch (err) {
    $("#insight").textContent = `Squad data failed: ${err.message}`;
    console.error(err);
  }
  try {
    await loadSessions();
  } catch (err) {
    const msg = `Session logs failed: ${err.message}`;
    if (state.view === "sessions") $("#insight").textContent = msg;
    $("#session-detail-insight").textContent = msg;
    console.error(err);
  }
  if (state.selectedPlayer) {
    try {
      await loadPlayer(state.selectedPlayer);
    } catch (err) {
      console.error(err);
    }
  }
}

boot().catch((err) => {
  $("#insight").textContent = `Failed to load: ${err.message}`;
  console.error(err);
});
