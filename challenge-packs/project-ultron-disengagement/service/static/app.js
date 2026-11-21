// PROJECT ULTRON Disengagement Console Client
let currentSessionId = localStorage.getItem("ultron_session_id") || null;
let commandHistory = [];
let historyIndex = -1;

const authPanel = document.getElementById("auth-panel");
const consolePanel = document.getElementById("console-panel");
const loginForm = document.getElementById("login-form");
const authError = document.getElementById("auth-error");
const btnLogout = document.getElementById("btn-logout");

const termScreen = document.getElementById("terminal-screen");
const termOutput = document.getElementById("term-output");
const termInput = document.getElementById("term-input");
const termPrompt = document.getElementById("term-prompt");

const opIdentity = document.getElementById("op-identity");
const effectiveRole = document.getElementById("effective-role");
const adminPerimeter = document.getElementById("admin-perimeter");
const feedbackDisplay = document.getElementById("feedback-display");

const flagForm = document.getElementById("flag-form");
const flagInput = document.getElementById("flag-input");
const flagResult = document.getElementById("flag-result");

// Live UTC Clock
function updateClock() {
  const now = new Date();
  document.getElementById("clock-display").textContent = now.toUTCString().slice(17, 25) + " UTC";
}
setInterval(updateClock, 1000);
updateClock();

// Check Existing Session
async function checkSession() {
  if (!currentSessionId) {
    showAuth();
    return;
  }
  try {
    const res = await fetch("/api/session", {
      headers: { "X-Session-ID": currentSessionId }
    });
    if (res.ok) {
      const data = await res.json();
      showConsole(data);
    } else {
      currentSessionId = null;
      localStorage.removeItem("ultron_session_id");
      showAuth();
    }
  } catch (err) {
    showAuth();
  }
}

function showAuth() {
  authPanel.classList.remove("hidden");
  consolePanel.classList.add("hidden");
}

function showConsole(sessionData) {
  authPanel.classList.add("hidden");
  consolePanel.classList.remove("hidden");
  opIdentity.textContent = sessionData.username ? `Elias Ward (${sessionData.username})` : "Operator";
  updateRoleDisplay(sessionData.effective_role);
  refreshFeedback();
  termInput.focus();
}

function updateRoleDisplay(role) {
  effectiveRole.textContent = role;
  if (role === "ADMIN") {
    effectiveRole.className = "t-val role-admin";
    adminPerimeter.textContent = "UNRESTRICTED";
    adminPerimeter.className = "t-val status-unrestricted";
    termPrompt.textContent = "eward@ultron-recovery [ADMIN]:#";
  } else {
    effectiveRole.className = "t-val role-operator";
    adminPerimeter.textContent = "RESTRICTED";
    adminPerimeter.className = "t-val status-restricted";
    termPrompt.textContent = "eward@ultron-recovery:~$";
  }
}

// Authentication
loginForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  authError.classList.add("hidden");

  const username = document.getElementById("username").value.trim();
  const password = document.getElementById("password").value.trim();
  const totp = document.getElementById("totp").value.trim();

  try {
    const res = await fetch("/api/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: jsonStr = JSON.stringify({ username, password, totp })
    });
    const data = await res.json();
    if (res.ok && data.status === "success") {
      currentSessionId = data.session_id;
      localStorage.setItem("ultron_session_id", currentSessionId);
      showConsole(data);
    } else {
      authError.textContent = data.error || "Authentication failed.";
      authError.classList.remove("hidden");
    }
  } catch (err) {
    authError.textContent = "Network error communicating with authentication service.";
    authError.classList.remove("hidden");
  }
});

// Logout
btnLogout.addEventListener("click", () => {
  currentSessionId = null;
  localStorage.removeItem("ultron_session_id");
  showAuth();
});

// Refresh Feedback File
async function refreshFeedback() {
  if (!currentSessionId) return;
  try {
    const res = await fetch("/api/feedback", {
      headers: { "X-Session-ID": currentSessionId }
    });
    if (res.ok) {
      const data = await res.json();
      feedbackDisplay.textContent = data.feedback || "(No feedback generated yet)";
    }
  } catch (e) {}
}

// Terminal Execution
termInput.addEventListener("keydown", async (e) => {
  if (e.key === "Enter") {
    const cmd = termInput.value.trim();
    if (!cmd) return;

    commandHistory.push(cmd);
    historyIndex = commandHistory.length;
    termInput.value = "";

    // Echo input
    appendTerminalLine(`${termPrompt.textContent} ${cmd}`, "cmd-prompt");

    if (cmd === "clear") {
      termOutput.innerHTML = "";
      return;
    }

    try {
      const res = await fetch("/api/terminal", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Session-ID": currentSessionId
        },
        body: JSON.stringify({ command: cmd, session_id: currentSessionId })
      });
      const data = await res.json();
      if (res.ok) {
        if (data.session_id) {
          currentSessionId = data.session_id;
          localStorage.setItem("ultron_session_id", currentSessionId);
        }
        if (data.output) {
          appendTerminalLine(data.output);
        }
        if (data.effective_role) {
          updateRoleDisplay(data.effective_role);
        }
        if (data.feedback) {
          feedbackDisplay.textContent = data.feedback;
        }
      } else {
        appendTerminalLine(`Error: ${data.error || "Command execution failed"}`);
      }
    } catch (err) {
      appendTerminalLine(`Communication failure: ${err.message}`);
    }

    termScreen.scrollTop = termScreen.scrollHeight;
  } else if (e.key === "ArrowUp") {
    if (historyIndex > 0) {
      historyIndex--;
      termInput.value = commandHistory[historyIndex];
    }
    e.preventDefault();
  } else if (e.key === "ArrowDown") {
    if (historyIndex < commandHistory.length - 1) {
      historyIndex++;
      termInput.value = commandHistory[historyIndex];
    } else {
      historyIndex = commandHistory.length;
      termInput.value = "";
    }
    e.preventDefault();
  }
});

function appendTerminalLine(text, className = "") {
  const line = document.createElement("div");
  line.className = `term-line ${className}`;
  line.textContent = text;
  termOutput.appendChild(line);
  termScreen.scrollTop = termScreen.scrollHeight;
}

// Flag Submission
flagForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  flagResult.classList.add("hidden");
  flagResult.className = "flag-result";

  const flag = flagInput.value.trim();
  try {
    const res = await fetch("/api/flag/validate", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Session-ID": currentSessionId
      },
      body: JSON.stringify({ flag, session_id: currentSessionId })
    });
    const data = await res.json();
    flagResult.textContent = data.message;
    flagResult.classList.remove("hidden");
    if (data.valid) {
      flagResult.classList.add("success");
      refreshFeedback();
    } else {
      flagResult.classList.add("fail");
    }
  } catch (err) {
    flagResult.textContent = "Error submitting flag to validator.";
    flagResult.classList.remove("hidden");
    flagResult.classList.add("fail");
  }
});

// Initialize
checkSession();
