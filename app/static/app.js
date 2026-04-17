"use strict";

// ── Helpers ──────────────────────────────────────────────────────────────────

const $ = (id) => document.getElementById(id);

const fmt = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" });
const fmtDate = (iso) => {
  const [y, m, d] = iso.split("-");
  return `${d}/${m}/${y}`;
};

function today() {
  return new Date().toISOString().slice(0, 10);
}

async function apiFetch(path, opts = {}) {
  const res = await fetch(path, opts);
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || "Erro desconhecido");
  }
  return res.status === 204 ? null : res.json();
}

// ── Chart instances ───────────────────────────────────────────────────────────

let pieChart = null;
let lineChart = null;

const PIE_COLORS = [
  "#4f46e5","#7c3aed","#db2777","#ea580c","#ca8a04",
  "#16a34a","#0891b2","#2563eb","#9333ea","#e11d48",
];

function renderPie(data) {
  const ctx = $("chart-pie").getContext("2d");
  if (pieChart) pieChart.destroy();
  pieChart = new Chart(ctx, {
    type: "pie",
    data: {
      labels: data.map((d) => `${d.category} (${d.pct}%)`),
      datasets: [{
        data: data.map((d) => d.total),
        backgroundColor: PIE_COLORS.slice(0, data.length),
        borderWidth: 1,
        borderColor: "#fff",
      }],
    },
    options: {
      plugins: {
        legend: { position: "bottom", labels: { font: { size: 11 }, boxWidth: 12 } },
        tooltip: {
          callbacks: {
            label: (ctx) => ` ${fmt.format(ctx.raw)}`,
          },
        },
      },
      maintainAspectRatio: false,
    },
  });
}

function renderLine(data) {
  const ctx = $("chart-line").getContext("2d");
  if (lineChart) lineChart.destroy();
  lineChart = new Chart(ctx, {
    type: "line",
    data: {
      labels: data.map((d) => d.month),
      datasets: [
        {
          label: "Saldo",
          data: data.map((d) => d.balance),
          borderColor: "#4f46e5",
          backgroundColor: "rgba(79,70,229,.08)",
          fill: true,
          tension: 0.35,
          pointRadius: 4,
        },
        {
          label: "Receitas",
          data: data.map((d) => d.income),
          borderColor: "#16a34a",
          backgroundColor: "transparent",
          tension: 0.35,
          pointRadius: 3,
          borderDash: [4, 3],
        },
        {
          label: "Despesas",
          data: data.map((d) => d.expense),
          borderColor: "#dc2626",
          backgroundColor: "transparent",
          tension: 0.35,
          pointRadius: 3,
          borderDash: [4, 3],
        },
      ],
    },
    options: {
      scales: {
        y: {
          ticks: {
            callback: (v) => fmt.format(v),
          },
        },
      },
      plugins: {
        tooltip: {
          callbacks: {
            label: (ctx) => ` ${ctx.dataset.label}: ${fmt.format(ctx.raw)}`,
          },
        },
      },
      maintainAspectRatio: false,
    },
  });
}

// ── Dashboard load ────────────────────────────────────────────────────────────

async function loadDashboard() {
  const now = new Date();
  const year = now.getFullYear();
  const month = now.getMonth() + 1;

  const [summary, byCategory, evolution] = await Promise.all([
    apiFetch(`/api/reports/summary?year=${year}&month=${month}`),
    apiFetch(`/api/reports/expenses-by-category?year=${year}&month=${month}`),
    apiFetch(`/api/reports/balance-evolution?months=12`),
  ]);

  $("kpi-balance").textContent  = fmt.format(summary.balance);
  $("kpi-income").textContent   = fmt.format(summary.month_income);
  $("kpi-expense").textContent  = fmt.format(summary.month_expense);

  const balanceCard = $("card-balance");
  balanceCard.querySelector(".kpi-value").style.color =
    summary.balance >= 0 ? "var(--income)" : "var(--expense)";

  const monthName = now.toLocaleString("pt-BR", { month: "long" });
  $("chart-month-label").textContent = `— ${monthName}`;

  if (byCategory.length) renderPie(byCategory);
  if (evolution.length)  renderLine(evolution);
}

// ── Category datalist & filter select ────────────────────────────────────────

async function loadCategories() {
  const cats = await apiFetch("/api/transactions/categories");
  const datalist = $("category-list");
  const sel = $("filter-category");

  datalist.innerHTML = cats.map((c) => `<option value="${c}"></option>`).join("");

  const existing = new Set([...sel.options].map((o) => o.value));
  cats.forEach((c) => {
    if (!existing.has(c)) {
      const opt = document.createElement("option");
      opt.value = c;
      opt.textContent = c;
      sel.appendChild(opt);
    }
  });
}

// ── Transaction list ──────────────────────────────────────────────────────────

async function loadTransactions(params = {}) {
  const qs = new URLSearchParams();
  if (params.date_from) qs.set("date_from", params.date_from);
  if (params.date_to)   qs.set("date_to",   params.date_to);
  if (params.category)  qs.set("category",  params.category);

  const data = await apiFetch(`/api/transactions/?${qs}`);
  const tbody = $("tbody");
  const emptyMsg = $("empty-msg");

  tbody.innerHTML = "";

  if (!data.length) {
    emptyMsg.classList.remove("hidden");
    return;
  }
  emptyMsg.classList.add("hidden");

  data.forEach((t) => {
    const tr = document.createElement("tr");
    const sign = t.type === "income" ? "+" : "−";
    tr.innerHTML = `
      <td>${fmtDate(t.date)}</td>
      <td>${t.description}</td>
      <td>${t.category}</td>
      <td><span class="badge ${t.type}">${t.type === "income" ? "Receita" : "Despesa"}</span></td>
      <td class="right"><span class="amount ${t.type}">${sign} ${fmt.format(t.amount)}</span></td>
      <td><button class="btn-delete" data-id="${t.id}" title="Excluir">✕</button></td>
    `;
    tbody.appendChild(tr);
  });

  tbody.querySelectorAll(".btn-delete").forEach((btn) => {
    btn.addEventListener("click", async () => {
      if (!confirm("Excluir esta transação?")) return;
      await apiFetch(`/api/transactions/${btn.dataset.id}`, { method: "DELETE" });
      await Promise.all([loadTransactions(currentFilters()), loadDashboard(), loadCategories()]);
    });
  });
}

function currentFilters() {
  return {
    date_from: $("filter-from").value  || undefined,
    date_to:   $("filter-to").value    || undefined,
    category:  $("filter-category").value || undefined,
  };
}

// ── Form ──────────────────────────────────────────────────────────────────────

$("f-date").value = today();

$("form-transaction").addEventListener("submit", async (e) => {
  e.preventDefault();
  const msg = $("form-msg");
  msg.textContent = "";
  msg.className = "form-msg";

  const body = {
    description: $("f-desc").value.trim(),
    amount:      parseFloat($("f-amount").value),
    category:    $("f-category").value.trim(),
    date:        $("f-date").value,
    type:        $("f-type").value,
  };

  try {
    await apiFetch("/api/transactions/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    msg.textContent = "Transação adicionada!";
    msg.classList.add("ok");
    e.target.reset();
    $("f-date").value = today();
    await Promise.all([loadTransactions(currentFilters()), loadDashboard(), loadCategories()]);
  } catch (err) {
    msg.textContent = err.message;
    msg.classList.add("err");
  }
});

// ── Filter controls ───────────────────────────────────────────────────────────

$("btn-filter").addEventListener("click", () => loadTransactions(currentFilters()));

$("btn-clear").addEventListener("click", () => {
  $("filter-from").value = "";
  $("filter-to").value   = "";
  $("filter-category").value = "";
  loadTransactions();
});

// ── Init ──────────────────────────────────────────────────────────────────────

(async () => {
  await Promise.all([loadDashboard(), loadCategories(), loadTransactions()]);
})();
