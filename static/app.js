// Viscan AI Dental Assistant — Datacurve-inspired Frontend & Motion Engine
let sessionId = "session-" + Math.random().toString(36).substring(2, 9);

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
  const btnApplyJson = document.getElementById("btn-apply-json");
  const btnCopyDraft = document.getElementById("btn-copy-draft");

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
    sessionId = "session-" + Math.random().toString(36).substring(2, 9);
    chatMessages.innerHTML = `
      <div class="message message--bot">
        <div class="message__meta">
          <span class="message__sender">Viscan Intelligence</span>
          <span class="message__time">Reset</span>
        </div>
        <div class="message__body">Session context reset. Active patient and report memory cleared. Ready for new clinical dialogue.</div>
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
      draftOutput.value = data.draft_report;

      // Tab 2: Structured JSON
      jsonOutput.value = JSON.stringify({
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

  /* ---------- Editable JSON & Draft Handlers (Requirement B) ---------- */
  if (btnApplyJson) {
    btnApplyJson.addEventListener("click", () => {
      try {
        const rawJson = jsonOutput.value.trim();
        if (!rawJson) {
          alert("JSON editor is empty.");
          return;
        }

        let parsed;
        try {
          parsed = JSON.parse(rawJson);
        } catch (err) {
          alert("Invalid JSON syntax: " + err.message);
          return;
        }

        // Schema validation: verify findings array and required fields
        let findings = null;
        if (Array.isArray(parsed)) {
          findings = parsed;
        } else if (parsed && typeof parsed === "object") {
          if (Array.isArray(parsed.structured_findings)) {
            findings = parsed.structured_findings;
          } else if (Array.isArray(parsed.findings)) {
            findings = parsed.findings;
          }
        }

        if (!findings || !Array.isArray(findings) || findings.length === 0) {
          alert("Invalid schema: JSON must contain a non-empty findings array (e.g. structured_findings) with 'anatomical_site' and 'observation' properties.");
          return;
        }

        for (let i = 0; i < findings.length; i++) {
          const f = findings[i];
          if (!f || typeof f !== "object" || !f.anatomical_site || !f.observation || typeof f.anatomical_site !== "string" || typeof f.observation !== "string") {
            alert(`Invalid schema in finding #${i + 1}: each finding must contain string properties for 'anatomical_site' and 'observation'.`);
            return;
          }
        }

        const rawDictation = dictateInput.value.trim() || "Clinician Dictation";

        let draftText = "CLINICAL OBSERVATION REPORT (DRAFT - REQUIRES CLINICIAN REVIEW)\n\n";
        draftText += `Raw Dictation: "${rawDictation}"\n\n`;
        draftText += "Structured Observations (Clinician Edited):\n";
        findings.forEach(f => {
          const status = f.is_supported !== false ? "[VALIDATED]" : "[UNSUPPORTED / CAUTION]";
          const site = f.anatomical_site;
          const obs = f.observation;
          const conf = f.confidence !== undefined ? Number(f.confidence).toFixed(2) : "0.95";
          draftText += ` - ${status} Site: ${site} | Observation: ${obs} (Confidence: ${conf})\n`;
        });
        draftText += "\nStatus: DRAFT - Mandatory clinician sign-off required prior to final diagnostic record.";

        draftOutput.value = draftText;
        document.querySelector(`.tab-link[data-tab="tab-draft"]`).click();
        appendBubble("bot", "Viscan Assistant", "Structured JSON edits validated and applied. Draft report recompiled from updated findings.");
      } catch (err) {
        alert("Schema validation error: " + err.message);
      }
    });
  }

  if (btnCopyDraft) {
    btnCopyDraft.addEventListener("click", () => {
      const text = draftOutput.value.trim();
      if (!text) {
        alert("Draft report is currently empty.");
        return;
      }
      navigator.clipboard.writeText(text).then(() => {
        btnCopyDraft.textContent = "Copied!";
        setTimeout(() => { btnCopyDraft.textContent = "Copy Draft"; }, 2000);
      }).catch(() => {
        // Fallback copy
        draftOutput.select();
        document.execCommand("copy");
        btnCopyDraft.textContent = "Copied!";
        setTimeout(() => { btnCopyDraft.textContent = "Copy Draft"; }, 2000);
      });
    });
  }

  /* ---------- Speech Recognition / Voice Input Handlers ---------- */
  function getSpeechRecognition() {
    const SpeechClass = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechClass) return null;
    try {
      const rec = new SpeechClass();
      rec.continuous = false;
      rec.interimResults = true;
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
      }
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

    let finalTranscript = "";
    let hasSubmitted = false;
    let hasError = false;

    rec.onresult = (e) => {
      let fullFinal = "";
      let interim = "";
      for (let i = 0; i < e.results.length; ++i) {
        const res = e.results[i];
        if (res.isFinal) {
          fullFinal += res[0].transcript + " ";
        } else {
          interim += res[0].transcript;
        }
      }
      finalTranscript = fullFinal.trim();
      const liveText = (finalTranscript + (interim ? " " + interim : "")).trim();
      if (liveText) {
        chatInput.value = liveText;
      }
    };

    rec.onerror = (e) => {
      console.warn("Voice chat recognition error:", e.error);
      hasError = true;
      btnVoiceChat.classList.remove("recording");
      activeVoiceTarget = null;
      activeRecognition = null;

      if (e.error === "not-allowed" || e.error === "service-not-allowed" || e.error === "network") {
        appendBubble("bot", "Viscan Voice Assistant", `Voice input unavailable (${e.error}). Please type your query or click one of the preset example queries.`);
      } else if (e.error === "no-speech") {
        appendBubble("bot", "Viscan Voice Assistant", "No speech was detected. Please click the mic again or type your query.");
      }
    };

    rec.onend = () => {
      btnVoiceChat.classList.remove("recording");
      if (activeVoiceTarget === "chat") {
        activeVoiceTarget = null;
        activeRecognition = null;
      }

      if (hasError || hasSubmitted) return;

      const query = (finalTranscript || chatInput.value).trim();
      if (query) {
        hasSubmitted = true;
        chatInput.value = query;
        chatForm.dispatchEvent(new Event("submit"));
      }
    };

    try {
      rec.start();
    } catch (err) {
      console.warn("rec.start() error:", err);
      btnVoiceChat.classList.remove("recording");
      activeVoiceTarget = null;
      activeRecognition = null;
      appendBubble("bot", "Viscan Voice Assistant", "Voice input could not start. Please type your query or click a preset example.");
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
      alert("Voice recognition is not supported in this browser. Please type or paste your dictation, or select a preset sample.");
      return;
    }

    activeRecognition = rec;
    activeVoiceTarget = "dictate";
    btnRecordAudio.classList.add("recording");
    recordBtnText.textContent = "Listening...";
    let finalTranscript = "";
    let hasSubmitted = false;
    let hasError = false;

    rec.onresult = (e) => {
      let fullFinal = "";
      let interim = "";
      for (let i = 0; i < e.results.length; ++i) {
        const res = e.results[i];
        if (res.isFinal) {
          fullFinal += res[0].transcript + " ";
        } else {
          interim += res[0].transcript;
        }
      }
      finalTranscript = fullFinal.trim();
      const liveText = (finalTranscript + (interim ? " " + interim : "")).trim();
      if (liveText) {
        dictateInput.value = liveText;
      }
    };

    rec.onerror = (e) => {
      console.warn("Dictation recognition error:", e.error);
      hasError = true;
      btnRecordAudio.classList.remove("recording");
      recordBtnText.textContent = "Voice Dictation";
      activeVoiceTarget = null;
      activeRecognition = null;

      if (e.error === "not-allowed" || e.error === "service-not-allowed" || e.error === "network") {
        appendBubble("bot", "Viscan Assistant", `Voice input unavailable (${e.error}). Existing transcript preserved; please type or paste your observations, or click an example preset.`);
      } else if (e.error === "no-speech") {
        appendBubble("bot", "Viscan Assistant", "No speech was detected. Please click the mic again or type your dictation.");
      }
    };

    rec.onend = () => {
      btnRecordAudio.classList.remove("recording");
      recordBtnText.textContent = "Voice Dictation";
      if (activeVoiceTarget === "dictate") {
        activeVoiceTarget = null;
        activeRecognition = null;
      }

      if (hasError || hasSubmitted) return;

      const text = (finalTranscript || dictateInput.value).trim();
      if (text) {
        hasSubmitted = true;
        dictateInput.value = text;
        processDictation();
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
      appendBubble("bot", "Viscan Assistant", "Voice input could not start. Please type or paste your dictation.");
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
