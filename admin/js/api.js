// ─────────────────────────────────────────────
//  API Client — Bearer token auth
//  Works from any origin (CORS enabled on backend)
// ─────────────────────────────────────────────

const API = {
  token: () => localStorage.getItem(CONFIG.TOKEN_KEY),

  headers() {
    const h = { "Content-Type": "application/json" };
    const t = this.token();
    if (t) h["Authorization"] = `Bearer ${t}`;
    return h;
  },

  async request(method, path, body = null) {
    const opts = { method, headers: this.headers() };
    if (body) opts.body = JSON.stringify(body);
    const res = await fetch(CONFIG.API_BASE_URL + path, opts);
    if (res.status === 401) {
      localStorage.removeItem(CONFIG.TOKEN_KEY);
      localStorage.removeItem(CONFIG.USER_KEY);
      window.location.href = "login.html";
      return;
    }
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || "Request failed");
    }
    return res.json();
  },

  async login(email, password) {
    const form = new URLSearchParams();
    form.append("username", email);
    form.append("password", password);
    const res = await fetch(CONFIG.API_BASE_URL + "/api/v1/auth/token", {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: form,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: "فشل تسجيل الدخول" }));
      throw new Error(err.detail || "فشل تسجيل الدخول");
    }
    return res.json();
  },

  get: (path) => API.request("GET", path),
  patch: (path, body) => API.request("PATCH", path, body),
};

function requireAuth() {
  if (!API.token()) {
    window.location.href = "login.html";
  }
}

function logout() {
  localStorage.removeItem(CONFIG.TOKEN_KEY);
  localStorage.removeItem(CONFIG.USER_KEY);
  window.location.href = "login.html";
}

function formatDate(iso) {
  if (!iso) return "—";
  const d = new Date(iso);
  return d.toLocaleDateString("ar-SA", { year: "numeric", month: "short", day: "numeric" });
}

function formatDateTime(iso) {
  if (!iso) return "—";
  const d = new Date(iso);
  return d.toLocaleString("ar-SA", { year: "numeric", month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" });
}

function roleBadge(role) {
  const map = {
    super_admin: ["مدير النظام", "bg-purple-100 text-purple-800"],
    admin: ["أدمين", "bg-blue-100 text-blue-800"],
    manager: ["مدير", "bg-green-100 text-green-800"],
    reviewer: ["مراجع", "bg-yellow-100 text-yellow-800"],
    viewer: ["مشاهد", "bg-gray-100 text-gray-700"],
  };
  const [label, cls] = map[role] || [role, "bg-gray-100 text-gray-700"];
  return `<span class="px-2 py-0.5 rounded-full text-xs font-medium ${cls}">${label}</span>`;
}
