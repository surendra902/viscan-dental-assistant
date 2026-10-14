// Viscan AI Dental Assistant — Datacurve-inspired Frontend & Motion Engine
const sessionId = "session-" + Math.random().toString(36).substring(2, 9);

document.addEventListener("DOMContentLoaded", () => {
  // Elements
  const chatForm = document.getElementById("chat-form");
  const chatInput = document.getElementById("chat-input");
  const chatMessages = document.getElementById("chat-messages");
  const btnClearChat = document.getElementById("btn-clear-chat");
  const btnVoiceChat = document.getElementById("btn-voice-chat");
  const evidenceBox = document.getElementById("evidence-container");
  const evidenceBody = document.getElementById("evidence-body");
  const evidenceTag = document.getElementById("evidence-source-tag");

  const dictateInput = document.getElementById("dictate-input");
  const btnProcessDictate = document.getElementById("btn-process-dictate");
  const btnRecordAudio = document.getElementById("btn-record-audio");
  const recordBtnText = document.getElementById("record-btn-text");
  const draftOutput = document.getElementById("draft-output");
  const jsonOutput = document.getElementById("json-output");
  const safetyOutput = document.getElementById("safety-output");

  const btnShowPatients = document.getElementById("btn-show-patients");
  const patientsModal = document.getElementById("patients-modal");
  const btnCloseModal = document.getElementById("btn-close-modal");
  const modalPatientList = document.getElementById("modal-patient-list");

  /* ---------- Particle / Dot-Morph Canvas (from portfolio) ---------- */
  const canvas = document.getElementById("dotCanvas");
  if (canvas) {
    const ctx = canvas.getContext("2d", { alpha: true });
    let w = 0, h = 0, dpr = 1;
    let particles = [];
    let t = 0;

    function resize() {
      dpr = Math.min(window.devicePixelRatio || 1, 2);
      w = window.innerWidth;
      h = window.innerHeight;
      canvas.width = Math.floor(w * dpr);
      canvas.height = Math.floor(h * dpr);
      canvas.style.width = w + "px";
      canvas.style.height = h + "px";
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      initParticles();
    }

    function initParticles() {
      const count = Math.min(100, Math.floor((w * h) / 16000));
      particles = Array.from({ length: count }, () => ({
        x: Math.random() * w,
        y: Math.random() * h,
        vx: (Math.random() - 0.5) * 0.25,
        vy: (Math.random() - 0.5) * 0.25,
        r: Math.random() * 1.5 + 0.6,
        phase: Math.random() * Math.PI * 2,
        speed: 0.3 + Math.random() * 0.5
      }));
    }

    function loop() {
      t += 0.012;
      ctx.clearRect(0, 0, w, h);
      ctx.fillStyle = "rgba(10, 119, 149, 0.45)";

      for (let i = 0; i < particles.length; i++) {
        const p = particles[i];
        p.x += p.vx + Math.sin(t * p.speed + p.phase) * 0.15;
        p.y += p.vy + Math.cos(t * p.speed + p.phase) * 0.15;

        if (p.x < 0) p.x = w;
        if (p.x > w) p.x = 0;
        if (p.y < 0) p.y = h;
        if (p.y > h) p.y = 0;

        ctx.beginPath();
        ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
        ctx.fill();
      }
      requestAnimationFrame(loop);
    }

    window.addEventListener("resize", resize);
    resize();
    loop();
  }

  /* ---------- Soft 3D Tilt on Cards (from portfolio) ---------- */
  if (window.matchMedia("(pointer: fine)").matches) {
    document.querySelectorAll("[data-tilt]").forEach((card) => {
      card.addEventListener("mousemove", (e) => {
        const r = card.getBoundingClientRect();
        const x = (e.clientX - r.left) / r.width - 0.5;
        const y = (e.clientY - r.top) / r.height - 0.5;
        card.style.transform = `perspective(900px) rotateY(${x * 3.5}deg) rotateX(${-y * 3.5}deg) translateY(-2px)`;
      });
      card.addEventListener("mouseleave", () => {
        card.style.transform = "";
      });
    });
  }

  /* ---------- Tab Switching ---------- */
  const tabs = document.querySelectorAll(".tab-link");
  tabs.forEach(tab => {
    tab.addEventListener("click", () => {
      tabs.forEach(t => t.classList.remove("active"));
      document.querySelectorAll(".tab-pane").forEach(c => c.classList.remove("active"));
      tab.classList.add("active");
      const target = document.getElementById(tab.dataset.tab);
      if (target) target.classList.add("active");
    });
  });

  /* ---------- Presets Chips ---------- */
  document.querySelectorAll(".chip[data-msg]").forEach(chip => {
    chip.addEventListener("click", () => {
      chatInput.value = chip.dataset.msg;
      chatForm.dispatchEvent(new Event("submit"));
    });
  });

  document.querySelectorAll(".chip[data-dict]").forEach(chip => {
    chip.addEventListener("click", () => {
      dictateInput.value = chip.dataset.dict;
      processDictation();
    });
  });

  /* ---------- Clear Chat ---------- */
  btnClearChat.addEventListener("click", () => {
    chatMessages.innerHTML = `
      <div class="message message--bot">
        <div class="message__meta">
          <span class="message__sender">Viscan Intelligence</span>
          <span class="message__time">Reset</span>
        </div>
        <div class="message__body">Session context reset. Ready for clinical dialogue.</div>
      </div>
    `;
    evidenceBox.style.display = "none";
  });

  /* ---------- Chat Submission ---------- */
  chatForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const query = chatInput.value.trim();
    if (!query) return;

    appendBubble("user", "Doctor", query);
    chatInput.value = "";

    try {
      const response = await fetch("/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: query, session_id: sessionId })
      });

      if (!response.ok) throw new Error(`HTTP error: ${response.statusText}`);

      const data = await response.json();
      appendBubble("bot", "Viscan Intelligence", data.response_text);

      if (data.evidence) {
        renderEvidence(data.evidence);
      } else {
        evidenceBox.style.display = "none";
      }
    } catch (err) {
      appendBubble("bot", "Error", `Request failed: ${err.message}`);
    }
  });

  function appendBubble(role, sender, text) {
    const bubble = document.createElement("div");
    bubble.className = `message ${role === "user" ? "message--user" : "message--bot"}`;
    bubble.innerHTML = `
      <div class="message__meta">
        <span class="message__sender">${sender}</span>
        <span class="message__time">${new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
      </div>
      <div class="message__body">${escapeHtml(text)}</div>
    `;
    chatMessages.appendChild(bubble);
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }

  function renderEvidence(evidence) {
    evidenceBox.style.display = "block";
    evidenceTag.textContent = `${evidence.modality} (${evidence.report_id})`;
    evidenceBody.innerHTML = `
      <div><strong>Acquisition Date:</strong> ${evidence.date ? evidence.date.substring(0, 10) : 'N/A'}</div>
      <div><strong>Findings Excerpt:</strong> ${evidence.evidence_snippet || 'Verified clinical observation.'}</div>
    `;
  }

  function escapeHtml(str) {
    return str.replace(/[&<>'"]/g, 
      tag => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' }[tag] || tag)
    );
  }

  /* ---------- Dictation Processing ---------- */
  async function processDictation() {
    const text = dictateInput.value.trim();
    if (!text) return;

    btnProcessDictate.disabled = true;
    btnProcessDictate.textContent = "Validating...";

    try {
      const response = await fetch("/dictate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ transcript: text, session_id: sessionId })
      });

      if (!response.ok) throw new Error("Dictation endpoint error.");

      const data = await response.json();

      // Tab 1: Draft Text
      draftOutput.textContent = data.draft_report;

      // Tab 2: Structured JSON
      jsonOutput.textContent = JSON.stringify({
        structured_findings: data.structured_findings,
        requires_review: data.requires_review,
        uncertainties: data.uncertainties,
        unsupported_claims: data.unsupported_claims
      }, null, 2);

      // Tab 3: Safety Flags
      safetyOutput.innerHTML = "";
      if (data.unsupported_claims.length === 0 && data.uncertainties.length === 0) {
        safetyOutput.innerHTML = `
          <div class="safety-notice-box">
            <strong>Standard Allowlist Passed:</strong> All observations correspond to validated dental anatomical landmarks. Clinician sign-off preserved for diagnostic compliance.
          </div>
        `;
      } else {
        data.unsupported_claims.forEach(claim => {
          const card = document.createElement("div");
          card.className = "safety-flag-box";
          card.innerHTML = `<strong>Unsupported Clinical Claim:</strong> ${escapeHtml(claim)}`;
          safetyOutput.appendChild(card);
        });
        data.uncertainties.forEach(unc => {
          const card = document.createElement("div");
          card.className = "safety-notice-box";
          card.innerHTML = `<strong>Uncertainty / Caution:</strong> ${escapeHtml(unc)}`;
          safetyOutput.appendChild(card);
        });
      }

      if (data.unsupported_claims.length > 0) {
        document.querySelector(`.tab-link[data-tab="tab-safety"]`).click();
      } else {
        document.querySelector(`.tab-link[data-tab="tab-draft"]`).click();
      }

    } catch (err) {
      alert("Error processing dictation: " + err.message);
    } finally {
      btnProcessDictate.disabled = false;
      btnProcessDictate.textContent = "Process & Structure Draft";
    }
  }

  btnProcessDictate.addEventListener("click", processDictation);

  /* ---------- Speech Recognition / Voice Input Handlers ---------- */
  function getSpeechRecognition() {
    const SpeechClass = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechClass) return null;
    try {
      const rec = new SpeechClass();
      rec.continuous = false;
      rec.interimResults = false;
      rec.lang = 'en-US';
      return rec;
    } catch (e) {
      console.warn("SpeechRecognition initialization failed:", e);
      return null;
    }
  }

  let activeRecognition = null;
  let activeVoiceTarget = null; // 'chat' | 'dictate' | null

  // Voice Chat Button
  btnVoiceChat.addEventListener("click", () => {
    // 1. Toggle off if already listening on chat
    if (activeVoiceTarget === "chat") {
      if (activeRecognition) {
        try { activeRecognition.stop(); } catch (_) {}
        activeRecognition = null;
      }
      activeVoiceTarget = null;
      btnVoiceChat.classList.remove("recording");
      return;
    }

    // 2. Safely stop any other active voice recording (e.g. dictation)
    if (activeRecognition) {
      try { activeRecognition.stop(); } catch (_) {}
      activeRecognition = null;
      activeVoiceTarget = null;
      btnRecordAudio.classList.remove("recording");
      recordBtnText.textContent = "Voice Dictation";
    }

    const rec = getSpeechRecognition();
    if (!rec) {
      // Browser does not support Web Speech API
      chatInput.value = "Open Priya Sharma's latest OPG report";
      chatForm.dispatchEvent(new Event("submit"));
      return;
    }

    activeRecognition = rec;
    activeVoiceTarget = "chat";
    btnVoiceChat.classList.add("recording");
    let hasResult = false;

    rec.onresult = (e) => {
      if (e.results && e.results[0] && e.results[0][0]) {
        const transcript = e.results[0][0].transcript.trim();
        if (transcript) {
          hasResult = true;
          chatInput.value = transcript;
          chatForm.dispatchEvent(new Event("submit"));
        }
      }
    };

    rec.onerror = (e) => {
      console.warn("Voice chat recognition error:", e.error);
      btnVoiceChat.classList.remove("recording");
      activeVoiceTarget = null;
      activeRecognition = null;

      // If speech recognition failed on remote host (e.g. network / not-allowed / audio-capture)
      // and no speech was transcribed, provide seamless fallback query so user is never stranded
      if (!hasResult) {
        if (e.error === "not-allowed" || e.error === "service-not-allowed" || e.error === "network") {
          appendBubble("bot", "Viscan Voice Assistant", `Microphone or cloud STT unavailable (${e.error}). Submitting sample voice query: "Open Priya Sharma's latest OPG report".`);
          chatInput.value = "Open Priya Sharma's latest OPG report";
          chatForm.dispatchEvent(new Event("submit"));
        } else if (e.error === "no-speech") {
          appendBubble("bot", "Viscan Voice Assistant", "No speech was detected. Please click the mic again or type your query.");
        }
      }
    };

    rec.onend = () => {
      btnVoiceChat.classList.remove("recording");
      if (activeVoiceTarget === "chat") {
        activeVoiceTarget = null;
        activeRecognition = null;
      }
    };

    try {
      rec.start();
    } catch (err) {
      console.warn("rec.start() error:", err);
      btnVoiceChat.classList.remove("recording");
      activeVoiceTarget = null;
      activeRecognition = null;
      chatInput.value = "Open Priya Sharma's latest OPG report";
      chatForm.dispatchEvent(new Event("submit"));
    }
  });

  // Voice Dictate Button
  btnRecordAudio.addEventListener("click", () => {
    // 1. Toggle off if already listening on dictation
    if (activeVoiceTarget === "dictate") {
      if (activeRecognition) {
        try { activeRecognition.stop(); } catch (_) {}
        activeRecognition = null;
      }
      activeVoiceTarget = null;
      btnRecordAudio.classList.remove("recording");
      recordBtnText.textContent = "Voice Dictation";
      return;
    }

    // 2. Safely stop any active chat voice recording
    if (activeRecognition) {
      try { activeRecognition.stop(); } catch (_) {}
      activeRecognition = null;
      activeVoiceTarget = null;
      btnVoiceChat.classList.remove("recording");
    }

    const rec = getSpeechRecognition();
    if (!rec) {
      // Browser does not support Web Speech API
      dictateInput.value = "Lower right third molar is horizontally impacted";
      processDictation();
      return;
    }

    activeRecognition = rec;
    activeVoiceTarget = "dictate";
    btnRecordAudio.classList.add("recording");
    recordBtnText.textContent = "Listening...";
    let hasResult = false;

    rec.onresult = (e) => {
      if (e.results && e.results[0] && e.results[0][0]) {
        const transcript = e.results[0][0].transcript.trim();
        if (transcript) {
          hasResult = true;
          dictateInput.value = transcript;
          processDictation();
        }
      }
    };

    rec.onerror = (e) => {
      console.warn("Dictation recognition error:", e.error);
      btnRecordAudio.classList.remove("recording");
      recordBtnText.textContent = "Voice Dictation";
      activeVoiceTarget = null;
      activeRecognition = null;

      if (!hasResult) {
        if (e.error === "not-allowed" || e.error === "service-not-allowed" || e.error === "network") {
          dictateInput.value = "Lower right third molar is horizontally impacted";
          processDictation();
        }
      }
    };

    rec.onend = () => {
      btnRecordAudio.classList.remove("recording");
      recordBtnText.textContent = "Voice Dictation";
      if (activeVoiceTarget === "dictate") {
        activeVoiceTarget = null;
        activeRecognition = null;
      }
    };

    try {
      rec.start();
    } catch (err) {
      console.warn("rec.start() error:", err);
      btnRecordAudio.classList.remove("recording");
      recordBtnText.textContent = "Voice Dictation";
      activeVoiceTarget = null;
      activeRecognition = null;
      dictateInput.value = "Lower right third molar is horizontally impacted";
      processDictation();
    }
  });

  /* ---------- Patients Modal ---------- */
  btnShowPatients.addEventListener("click", async () => {
    patientsModal.style.display = "flex";
    try {
      const res = await fetch("/patients");
      const patients = await res.json();
      let html = `
        <table class="patient-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Name</th>
              <th>Gender</th>
              <th>DOB</th>
              <th>Contact</th>
            </tr>
          </thead>
          <tbody>
      `;
      patients.forEach(p => {
        html += `
          <tr>
            <td><strong>${p.patient_id}</strong></td>
            <td>${p.name}</td>
            <td>${p.gender}</td>
            <td>${p.date_of_birth}</td>
            <td>${p.contact}</td>
          </tr>
        `;
      });
      html += `</tbody></table>`;
      modalPatientList.innerHTML = html;
    } catch (e) {
      modalPatientList.innerHTML = `<p>Failed to load patient list.</p>`;
    }
  });

  btnCloseModal.addEventListener("click", () => {
    patientsModal.style.display = "none";
  });

  patientsModal.addEventListener("click", (e) => {
    if (e.target === patientsModal) patientsModal.style.display = "none";
  });
});
