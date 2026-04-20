/**
 * admin.js — Frontend logic for the Admin Dashboard
 *
 * Handles:
 *  - Auth check (must be admin)
 *  - Fetching and rendering all complaints
 *  - Filter controls
 *  - Chart.js statistics charts
 *  - Auto-refresh
 */

// ─── Configuration ──────────────────────────────────────────────────────────
const API_BASE = window.location.origin;

// ─── Auth Check ─────────────────────────────────────────────────────────────
const token = localStorage.getItem("token");
const role = localStorage.getItem("role");
const username = localStorage.getItem("username");

if (!token) {
    window.location.href = "/";
}
if (role !== "admin") {
    window.location.href = "/user";
}

// ─── DOM Elements ───────────────────────────────────────────────────────────
const complaintsBody  = document.getElementById("complaintsBody");
const filterCategory  = document.getElementById("filterCategory");
const filterPriority  = document.getElementById("filterPriority");
const refreshBtn      = document.getElementById("refreshBtn");
const logoutBtn       = document.getElementById("logoutBtn");
const adminAvatar     = document.getElementById("adminAvatar");
const adminNameEl     = document.getElementById("adminName");

// Header stat badges
const totalBadge  = document.getElementById("totalBadge");
const highBadge   = document.getElementById("highBadge");
const mediumBadge = document.getElementById("mediumBadge");
const lowBadge    = document.getElementById("lowBadge");

// Charts
let categoryChart = null;
let priorityChart = null;

// ─── Category Icons ─────────────────────────────────────────────────────────
const CATEGORY_ICONS = {
    "Water Issue":       "💧",
    "Electricity Issue": "⚡",
    "Road Issue":        "🛣️",
    "Sanitation Issue":  "🗑️",
    "Traffic Issue":     "🚦",
};

// ─── Chart Colors ───────────────────────────────────────────────────────────
const CATEGORY_COLORS = [
    "rgba(14, 165, 233, 0.8)",   // Sky — Water
    "rgba(245, 158, 11, 0.8)",   // Amber — Electricity
    "rgba(124, 92, 191, 0.8)",   // Purple — Road
    "rgba(249, 115, 22, 0.8)",   // Orange — Sanitation
    "rgba(79, 110, 247, 0.8)",   // Blue — Traffic
];

const PRIORITY_COLORS = {
    "High":   "rgba(220, 38, 38, 0.8)",
    "Medium": "rgba(217, 119, 6, 0.8)",
    "Low":    "rgba(5, 150, 105, 0.8)",
};

// ═══════════════════════════════════════════════════════════════════════════
//  INITIALIZATION
// ═══════════════════════════════════════════════════════════════════════════

document.addEventListener("DOMContentLoaded", () => {
    // Set admin info
    if (username) {
        adminNameEl.textContent = username;
        adminAvatar.textContent = username.charAt(0).toUpperCase();
    }

    loadComplaints();
    loadStats();
    setupEventListeners();
});

function setupEventListeners() {
    filterCategory.addEventListener("change", loadComplaints);
    filterPriority.addEventListener("change", loadComplaints);
    refreshBtn.addEventListener("click", () => {
        loadComplaints();
        loadStats();
    });
    logoutBtn.addEventListener("click", logout);
}

function authHeaders() {
    return { "Authorization": `Bearer ${token}` };
}

function logout() {
    localStorage.removeItem("token");
    localStorage.removeItem("username");
    localStorage.removeItem("role");
    window.location.href = "/";
}

// ═══════════════════════════════════════════════════════════════════════════
//  LOAD & RENDER COMPLAINTS
// ═══════════════════════════════════════════════════════════════════════════

async function loadComplaints() {
    const category = filterCategory.value;
    const priority = filterPriority.value;

    let url = `${API_BASE}/get_complaints?`;
    if (category) url += `category=${encodeURIComponent(category)}&`;
    if (priority) url += `priority=${encodeURIComponent(priority)}&`;

    try {
        const response = await fetch(url, {
            headers: authHeaders(),
        });

        if (response.status === 401 || response.status === 403) {
            logout();
            return;
        }

        const data = await response.json();

        if (data.status === "success") {
            renderComplaints(data.data);
        }
    } catch (err) {
        console.error("Failed to load complaints:", err);
    }
}

function renderComplaints(complaints) {
    if (!complaints || complaints.length === 0) {
        complaintsBody.innerHTML = `
            <tr class="empty-row">
                <td colspan="8">No complaints found.</td>
            </tr>`;
        return;
    }

    complaintsBody.innerHTML = complaints.map(c => {
        const icon = CATEGORY_ICONS[c.category] || "📌";
        const priorityClass = c.priority.toLowerCase();
        const sentimentClass = c.sentiment < -0.1 ? "negative" : c.sentiment > 0.1 ? "positive" : "neutral";
        const sentimentLabel = c.sentiment < -0.1 ? "Negative" : c.sentiment > 0.1 ? "Positive" : "Neutral";
        const timeStr = formatTime(c.timestamp);
        const displayUser = c.username || "—";

        return `
        <tr>
            <td>#${c.id}</td>
            <td>${escapeHtml(c.text)}</td>
            <td>${escapeHtml(displayUser)}</td>
            <td><span class="category-badge">${icon} ${c.category}</span></td>
            <td><span class="priority-badge ${priorityClass}">${c.priority}</span></td>
            <td>${c.priority_score}</td>
            <td><span class="sentiment ${sentimentClass}">${sentimentLabel} (${c.sentiment})</span></td>
            <td>${timeStr}</td>
        </tr>`;
    }).join("");
}

// ═══════════════════════════════════════════════════════════════════════════
//  STATISTICS & CHARTS
// ═══════════════════════════════════════════════════════════════════════════

async function loadStats() {
    try {
        const response = await fetch(`${API_BASE}/analyze`, {
            headers: authHeaders(),
        });

        if (response.status === 401 || response.status === 403) {
            logout();
            return;
        }

        const data = await response.json();

        if (data.status === "success") {
            const stats = data.data;

            // Update header badges
            totalBadge.textContent  = stats.total_complaints;
            highBadge.textContent   = stats.priority_distribution["High"]   || 0;
            mediumBadge.textContent = stats.priority_distribution["Medium"] || 0;
            lowBadge.textContent    = stats.priority_distribution["Low"]    || 0;

            // Render charts
            renderCategoryChart(stats.category_distribution);
            renderPriorityChart(stats.priority_distribution);
        }
    } catch (err) {
        console.error("Failed to load stats:", err);
    }
}

function renderCategoryChart(distribution) {
    const ctx = document.getElementById("categoryChart").getContext("2d");

    const allCategories = ["Water Issue", "Electricity Issue", "Road Issue", "Sanitation Issue", "Traffic Issue"];
    const labels = allCategories.map(c => CATEGORY_ICONS[c] + " " + c.replace(" Issue", ""));
    const values = allCategories.map(c => distribution[c] || 0);

    if (categoryChart) categoryChart.destroy();

    categoryChart = new Chart(ctx, {
        type: "bar",
        data: {
            labels: labels,
            datasets: [{
                label: "Complaints",
                data: values,
                backgroundColor: CATEGORY_COLORS,
                borderColor: CATEGORY_COLORS.map(c => c.replace("0.8", "1")),
                borderWidth: 1,
                borderRadius: 6,
                barPercentage: 0.7,
            }],
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: "#ffffff",
                    titleColor: "#1a1d26",
                    bodyColor: "#5a6178",
                    borderColor: "rgba(0,0,0,0.1)",
                    borderWidth: 1,
                    cornerRadius: 8,
                    padding: 12,
                },
            },
            scales: {
                x: {
                    ticks: { color: "#5a6178", font: { size: 11, family: "Inter" } },
                    grid: { display: false },
                },
                y: {
                    beginAtZero: true,
                    ticks: {
                        color: "#8c94a6",
                        font: { size: 11, family: "Inter" },
                        stepSize: 1,
                    },
                    grid: { color: "rgba(0,0,0,0.04)" },
                },
            },
        },
    });
}

function renderPriorityChart(distribution) {
    const ctx = document.getElementById("priorityChart").getContext("2d");

    const labels = ["High", "Medium", "Low"];
    const values = labels.map(p => distribution[p] || 0);
    const colors = labels.map(p => PRIORITY_COLORS[p]);

    if (priorityChart) priorityChart.destroy();

    priorityChart = new Chart(ctx, {
        type: "doughnut",
        data: {
            labels: labels,
            datasets: [{
                data: values,
                backgroundColor: colors,
                borderColor: "#ffffff",
                borderWidth: 3,
                hoverOffset: 8,
            }],
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            cutout: "60%",
            plugins: {
                legend: {
                    position: "bottom",
                    labels: {
                        color: "#5a6178",
                        font: { size: 12, family: "Inter" },
                        padding: 16,
                        usePointStyle: true,
                        pointStyleWidth: 12,
                    },
                },
                tooltip: {
                    backgroundColor: "#ffffff",
                    titleColor: "#1a1d26",
                    bodyColor: "#5a6178",
                    borderColor: "rgba(0,0,0,0.1)",
                    borderWidth: 1,
                    cornerRadius: 8,
                    padding: 12,
                },
            },
        },
    });
}

// ═══════════════════════════════════════════════════════════════════════════
//  UTILITY FUNCTIONS
// ═══════════════════════════════════════════════════════════════════════════

function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
}

function formatTime(isoString) {
    if (!isoString) return "—";
    const date = new Date(isoString);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return "Just now";
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;

    return date.toLocaleDateString("en-IN", {
        day: "numeric",
        month: "short",
        year: "numeric",
    });
}
