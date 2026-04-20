/**
 * app.js — Frontend logic for Smart Citizen Complaint Analyzer
 *
 * Handles:
 *  - Complaint form submission (text & voice)
 *  - Voice recording via MediaRecorder API
 *  - Fetching and rendering complaints table
 *  - Filter controls
 *  - Chart.js statistics charts
 *  - Auto-refresh after submission
 */

// ─── Configuration ──────────────────────────────────────────────────────────
const API_BASE = window.location.origin;

// ─── DOM Elements ───────────────────────────────────────────────────────────
const complaintForm   = document.getElementById("complaintForm");
const complaintText   = document.getElementById("complaintText");
const voiceBtn        = document.getElementById("voiceBtn");
const submitBtn       = document.getElementById("submitBtn");
const voiceStatus     = document.getElementById("voiceStatus");
const submitResult    = document.getElementById("submitResult");
const complaintsBody  = document.getElementById("complaintsBody");
const filterCategory  = document.getElementById("filterCategory");
const filterPriority  = document.getElementById("filterPriority");
const refreshBtn      = document.getElementById("refreshBtn");

// Header stat badges
const totalBadge  = document.getElementById("totalBadge");
const highBadge   = document.getElementById("highBadge");
const mediumBadge = document.getElementById("mediumBadge");
const lowBadge    = document.getElementById("lowBadge");

// Charts
let categoryChart = null;
let priorityChart = null;

// Voice recording state
let mediaRecorder = null;
let audioChunks   = [];
let isRecording   = false;

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
    "rgba(34, 211, 238, 0.8)",   // Cyan — Water
    "rgba(250, 204, 21, 0.8)",   // Yellow — Electricity
    "rgba(168, 85, 247, 0.8)",   // Purple — Road
    "rgba(251, 146, 60, 0.8)",   // Orange — Sanitation
    "rgba(99, 102, 241, 0.8)",   // Indigo — Traffic
];

const PRIORITY_COLORS = {
    "High":   "rgba(239, 68, 68, 0.8)",
    "Medium": "rgba(245, 158, 11, 0.8)",
    "Low":    "rgba(16, 185, 129, 0.8)",
};

// ═══════════════════════════════════════════════════════════════════════════
//  INITIALIZATION
// ═══════════════════════════════════════════════════════════════════════════

document.addEventListener("DOMContentLoaded", () => {
    loadComplaints();
    loadStats();
    setupEventListeners();
});

function setupEventListeners() {
    // Form submission
    complaintForm.addEventListener("submit", handleSubmit);

    // Voice recording
    voiceBtn.addEventListener("click", toggleVoiceRecording);

    // Filters
    filterCategory.addEventListener("change", loadComplaints);
    filterPriority.addEventListener("change", loadComplaints);

    // Refresh button
    refreshBtn.addEventListener("click", () => {
        loadComplaints();
        loadStats();
    });
}

// ═══════════════════════════════════════════════════════════════════════════
//  COMPLAINT SUBMISSION
// ═══════════════════════════════════════════════════════════════════════════

async function handleSubmit(e) {
    e.preventDefault();

    const text = complaintText.value.trim();
    if (!text) {
        showResult("Please enter a complaint description.", "error");
        return;
    }

    // Disable submit button
    submitBtn.disabled = true;
    submitBtn.querySelector(".btn-text").textContent = "Analyzing...";

    try {
        const formData = new FormData();
        formData.append("text", text);

        const response = await fetch(`${API_BASE}/submit_complaint`, {
            method: "POST",
            body: formData,
        });

        const data = await response.json();

        if (response.ok && data.status === "success") {
            const c = data.data;
            showResult(
                `✅ Complaint submitted! Category: <strong>${c.category}</strong> | ` +
                `Priority: <strong>${c.priority}</strong> (Score: ${c.priority_score})`,
                "success"
            );
            complaintText.value = "";
            // Refresh dashboard
            loadComplaints();
            loadStats();
        } else {
            showResult(`❌ Error: ${data.detail || "Unknown error"}`, "error");
        }
    } catch (err) {
        showResult(`❌ Connection error: ${err.message}`, "error");
    } finally {
        submitBtn.disabled = false;
        submitBtn.querySelector(".btn-text").textContent = "Submit Complaint";
    }
}

function showResult(message, type) {
    submitResult.innerHTML = message;
    submitResult.className = `submit-result ${type}`;
    submitResult.classList.remove("hidden");

    // Auto-hide after 8 seconds
    setTimeout(() => {
        submitResult.classList.add("hidden");
    }, 8000);
}

// ═══════════════════════════════════════════════════════════════════════════
//  VOICE RECORDING
// ═══════════════════════════════════════════════════════════════════════════

async function toggleVoiceRecording() {
    if (isRecording) {
        stopRecording();
    } else {
        await startRecording();
    }
}

async function startRecording() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaRecorder = new MediaRecorder(stream, { mimeType: "audio/webm" });
        audioChunks = [];

        mediaRecorder.ondataavailable = (event) => {
            if (event.data.size > 0) {
                audioChunks.push(event.data);
            }
        };

        mediaRecorder.onstop = async () => {
            const audioBlob = new Blob(audioChunks, { type: "audio/webm" });
            // Stop all tracks
            stream.getTracks().forEach(track => track.stop());
            // Send to speech-to-text API
            await transcribeAudio(audioBlob);
        };

        mediaRecorder.start();
        isRecording = true;
        voiceBtn.classList.add("recording");
        voiceBtn.querySelector(".btn-text").textContent = "Stop Recording";
        voiceStatus.classList.remove("hidden");

    } catch (err) {
        showResult("❌ Microphone access denied. Please allow microphone access and try again.", "error");
    }
}

function stopRecording() {
    if (mediaRecorder && mediaRecorder.state !== "inactive") {
        mediaRecorder.stop();
    }
    isRecording = false;
    voiceBtn.classList.remove("recording");
    voiceBtn.querySelector(".btn-text").textContent = "Voice Input";
    voiceStatus.classList.add("hidden");
}

async function transcribeAudio(audioBlob) {
    voiceBtn.disabled = true;
    voiceBtn.querySelector(".btn-text").textContent = "Transcribing...";

    try {
        const formData = new FormData();
        formData.append("audio", audioBlob, "recording.webm");

        const response = await fetch(`${API_BASE}/speech_to_text`, {
            method: "POST",
            body: formData,
        });

        const data = await response.json();

        if (response.ok && data.status === "success") {
            complaintText.value = data.text;
            showResult("🎤 Voice transcribed successfully! Review and submit.", "success");
        } else {
            showResult(`❌ Transcription failed: ${data.detail || "Unknown error"}`, "error");
        }
    } catch (err) {
        showResult(`❌ Transcription error: ${err.message}`, "error");
    } finally {
        voiceBtn.disabled = false;
        voiceBtn.querySelector(".btn-text").textContent = "Voice Input";
    }
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
        const response = await fetch(url);
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
                <td colspan="7">No complaints found. Submit one above!</td>
            </tr>`;
        return;
    }

    complaintsBody.innerHTML = complaints.map(c => {
        const icon = CATEGORY_ICONS[c.category] || "📌";
        const priorityClass = c.priority.toLowerCase();
        const sentimentClass = c.sentiment < -0.1 ? "negative" : c.sentiment > 0.1 ? "positive" : "neutral";
        const sentimentLabel = c.sentiment < -0.1 ? "Negative" : c.sentiment > 0.1 ? "Positive" : "Neutral";
        const timeStr = formatTime(c.timestamp);

        return `
        <tr>
            <td>#${c.id}</td>
            <td>${escapeHtml(c.text)}</td>
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
        const response = await fetch(`${API_BASE}/analyze`);
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

    // All 5 categories (show 0 if no data)
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
                    backgroundColor: "rgba(15, 15, 30, 0.9)",
                    titleColor: "#e8e8f0",
                    bodyColor: "#9a9ab0",
                    borderColor: "rgba(255,255,255,0.1)",
                    borderWidth: 1,
                    cornerRadius: 8,
                    padding: 12,
                },
            },
            scales: {
                x: {
                    ticks: { color: "#9a9ab0", font: { size: 11, family: "Inter" } },
                    grid: { display: false },
                },
                y: {
                    beginAtZero: true,
                    ticks: {
                        color: "#6b6b80",
                        font: { size: 11, family: "Inter" },
                        stepSize: 1,
                    },
                    grid: { color: "rgba(255,255,255,0.04)" },
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
                borderColor: "rgba(15, 15, 30, 0.8)",
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
                        color: "#9a9ab0",
                        font: { size: 12, family: "Inter" },
                        padding: 16,
                        usePointStyle: true,
                        pointStyleWidth: 12,
                    },
                },
                tooltip: {
                    backgroundColor: "rgba(15, 15, 30, 0.9)",
                    titleColor: "#e8e8f0",
                    bodyColor: "#9a9ab0",
                    borderColor: "rgba(255,255,255,0.1)",
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
