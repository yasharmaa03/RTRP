/**
 * user.js — Frontend logic for the Citizen Portal
 *
 * Handles:
 *  - Auth check & redirect
 *  - Complaint form submission (text & voice)
 *  - Voice recording via MediaRecorder API
 *  - Loading user's own complaints
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
if (role === "admin") {
    window.location.href = "/admin";
}

// ─── DOM Elements ───────────────────────────────────────────────────────────
const complaintForm   = document.getElementById("complaintForm");
const complaintText   = document.getElementById("complaintText");
const voiceBtn        = document.getElementById("voiceBtn");
const submitBtn       = document.getElementById("submitBtn");
const voiceStatus     = document.getElementById("voiceStatus");
const submitResult    = document.getElementById("submitResult");
const recentList      = document.getElementById("recentList");
const logoutBtn       = document.getElementById("logoutBtn");
const userAvatar      = document.getElementById("userAvatar");
const userNameEl      = document.getElementById("userName");

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

// ═══════════════════════════════════════════════════════════════════════════
//  INITIALIZATION
// ═══════════════════════════════════════════════════════════════════════════

document.addEventListener("DOMContentLoaded", () => {
    // Set user info in header
    if (username) {
        userNameEl.textContent = username;
        userAvatar.textContent = username.charAt(0).toUpperCase();
    }

    loadMyComplaints();
    setupEventListeners();
});

function setupEventListeners() {
    complaintForm.addEventListener("submit", handleSubmit);
    voiceBtn.addEventListener("click", toggleVoiceRecording);
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
//  COMPLAINT SUBMISSION
// ═══════════════════════════════════════════════════════════════════════════

async function handleSubmit(e) {
    e.preventDefault();

    const text = complaintText.value.trim();
    if (!text) {
        showResult("Please enter a complaint description.", "error");
        return;
    }

    submitBtn.disabled = true;
    submitBtn.querySelector(".btn-text").textContent = "Analyzing...";

    try {
        const language = document.getElementById("voiceLanguage").value;
        const formData = new FormData();
        formData.append("text", text);
        formData.append("language", language);

        const response = await fetch(`${API_BASE}/submit_complaint`, {
            method: "POST",
            headers: authHeaders(),
            body: formData,
        });

        if (response.status === 401) {
            logout();
            return;
        }

        const data = await response.json();

        if (response.ok && data.status === "success") {
            const c = data.data;
            showResult(
                `✅ Complaint submitted! Category: <strong>${c.category}</strong> | ` +
                `Priority: <strong>${c.priority}</strong> (Score: ${c.priority_score})`,
                "success"
            );
            complaintText.value = "";
            loadMyComplaints();
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
            stream.getTracks().forEach(track => track.stop());
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
        const language = document.getElementById("voiceLanguage").value;
        const formData = new FormData();
        formData.append("audio", audioBlob, "recording.webm");
        formData.append("language", language);

        const response = await fetch(`${API_BASE}/speech_to_text`, {
            method: "POST",
            headers: authHeaders(),
            body: formData,
        });

        if (response.status === 401) {
            logout();
            return;
        }

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
//  LOAD MY COMPLAINTS
// ═══════════════════════════════════════════════════════════════════════════

async function loadMyComplaints() {
    try {
        const response = await fetch(`${API_BASE}/my_complaints`, {
            headers: authHeaders(),
        });

        if (response.status === 401) {
            logout();
            return;
        }

        const data = await response.json();

        if (data.status === "success") {
            renderRecentComplaints(data.data);
        }
    } catch (err) {
        console.error("Failed to load complaints:", err);
    }
}

function renderRecentComplaints(complaints) {
    if (!complaints || complaints.length === 0) {
        recentList.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">📭</div>
                <div class="empty-state-text">No complaints yet. Submit one above!</div>
            </div>`;
        return;
    }

    recentList.innerHTML = complaints.map(c => {
        const icon = CATEGORY_ICONS[c.category] || "📌";
        const priorityClass = c.priority.toLowerCase();
        const timeStr = formatTime(c.timestamp);

        return `
        <div class="recent-item">
            <div class="recent-item-body">
                <div class="recent-item-text">${escapeHtml(c.text)}</div>
                <div class="recent-item-meta">
                    <span class="category-badge">${icon} ${c.category}</span>
                    <span class="priority-badge ${priorityClass}">${c.priority}</span>
                    <span class="recent-item-time">${timeStr}</span>
                </div>
            </div>
        </div>`;
    }).join("");
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
