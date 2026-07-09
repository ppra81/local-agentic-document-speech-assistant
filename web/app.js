const samples = {
  invoice: `Vendor: Example Medical Store
Invoice Number: INV-2026-0709
Date: 2026-07-09

Items:
- Digital thermometer: ₹450
- First aid kit: ₹600
- Sanitizer: ₹200

Total Amount: ₹1,250
Payment Method: UPI

Thank you for your purchase.`,
  receipt: `Store: Local Grocery Mart
Receipt No: R-10042
Date: 2026-07-09
Rice: ₹700
Milk: ₹120
Vegetables: ₹430
Total Amount: ₹1,250`,
  transcript: `This is a mock audio transcript. The speaker asks the assistant to summarize an invoice and identify the total amount due.`
};

let inputMode = "upload";
let lastResult = {};

function byId(id) {
  return document.getElementById(id);
}

function apiBase() {
  return window.location.origin;
}

function setInputMode(next) {
  inputMode = next;
  byId("uploadPanel").classList.toggle("hidden", next !== "upload");
  byId("pathPanel").classList.toggle("hidden", next !== "path");
  byId("samplePanel").classList.toggle("hidden", next !== "sample");
  byId("uploadTab").classList.toggle("secondary", next !== "upload");
  byId("pathTab").classList.toggle("secondary", next !== "path");
  byId("sampleTab").classList.toggle("secondary", next !== "sample");
}

function loadSample(name) {
  byId("sampleText").value = samples[name] || "";
  renderPreview(byId("sampleText").value || "No sample loaded.");
}

async function post(path, body) {
  const response = await fetch(`${apiBase()}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body)
  });
  const data = await response.json();
  if (!response.ok) throw new Error(data.detail || `${response.status} request failed`);
  return data;
}

async function checkHealth() {
  try {
    const response = await fetch(`${apiBase()}/health`);
    const data = await response.json();
    byId("health").textContent = `API: ${data.status}`;
  } catch {
    byId("health").textContent = "API: offline";
  }
}

async function collectInput() {
  const docFile = byId("docUpload").files[0];
  const audioFile = byId("audioUpload").files[0];
  if (inputMode === "sample") {
    const text = byId("sampleText").value;
    renderPreview(text || "No sample text.");
    return { text, filePath: "sample_input.txt", audioText: text };
  }
  if (inputMode === "upload") {
    const docText = docFile ? await readDocumentFile(docFile) : null;
    const audioText = byId("audioTranscript").value.trim() || (audioFile && isTextFile(audioFile) ? await audioFile.text() : null);
    if (docText) renderPreview(docText);
    return {
      text: docText,
      filePath: docFile ? docFile.name : byId("docPath").value,
      audioText,
      audioPath: audioFile ? audioFile.name : byId("audioPath").value
    };
  }
  renderPreview(`Path input selected:\n${byId("docPath").value}`);
  return { text: null, filePath: byId("docPath").value, audioText: null, audioPath: byId("audioPath").value };
}

function isTextFile(file) {
  return file.type.startsWith("text") || /\.(txt|text|md|csv|json)$/i.test(file.name);
}

async function readDocumentFile(file) {
  if (file.type === "application/pdf" || /\.pdf$/i.test(file.name)) {
    const buffer = await file.arrayBuffer();
    const raw = new TextDecoder("latin1").decode(buffer);
    const text = extractSimplePdfText(raw);
    if (!text.startsWith("This PDF does not expose")) return text;
    return extractTextViaApi(file);
  }
  return file.text();
}

function extractSimplePdfText(rawPdf) {
  const direct = [...rawPdf.matchAll(/\((.*?)\)\s*Tj/gs)].map((match) => match[1]);
  const arrayMatches = [...rawPdf.matchAll(/\[(.*?)\]\s*TJ/gs)]
    .flatMap((match) => [...match[1].matchAll(/\((.*?)\)/gs)].map((item) => item[1]));
  const matches = direct.concat(arrayMatches);
  if (!matches.length) {
    return "This PDF does not expose embedded plain text in the local browser demo. Use a text file or connect a real OCR/PDF adapter.";
  }
  return matches.map(decodePdfText).join("\n");
}

function decodePdfText(value) {
  return value
    .replace(/\\\(/g, "(")
    .replace(/\\\)/g, ")")
    .replace(/\\\\/g, "\\")
    .replace(/\\n/g, "\n")
    .replace(/\\r/g, "\r")
    .replace(/\\t/g, "\t");
}

async function extractTextViaApi(file) {
  const form = new FormData();
  form.append("file", file);
  const response = await fetch(`${apiBase()}/documents/extract-text`, { method: "POST", body: form });
  const data = await response.json();
  if (!response.ok) throw new Error(data.detail || "PDF text extraction failed.");
  return data.text;
}

function parseReference() {
  const value = byId("referenceJson").value.trim();
  if (!value) return {};
  try {
    return JSON.parse(value);
  } catch {
    throw new Error("Reference JSON is invalid.");
  }
}

async function runWorkflow() {
  byId("runBtn").disabled = true;
  byId("status").textContent = "Running...";
  byId("status").className = "status";
  try {
    const workflow = byId("workflow").value;
    const question = byId("question").value;
    const topK = Number(byId("topK").value || 5);
    const input = await collectInput();
    const reference = parseReference();
    const transcript = workflow === "agent" || workflow === "report" ? await ensureAudioTranscript(input) : "";
    const effectiveTranscript = transcript.trim();
    const enrichedQuestion = effectiveTranscript ? `${question}\n\nRecording transcript: ${effectiveTranscript}` : question;
    const routes = {
      agent: ["/agent/ask", input.text ? { request: enrichedQuestion, text: input.text, file_path: input.filePath, audio_file_path: input.audioPath, audio_text: effectiveTranscript, reference } : { request: enrichedQuestion, file_path: input.filePath, audio_file_path: input.audioPath, audio_text: effectiveTranscript, reference }],
      ingest: ["/documents/ingest", input.text ? { text: input.text, source_file: input.filePath } : { file_path: input.filePath }],
      search: ["/documents/search", { query: question, top_k: topK }],
      asr: ["/audio/transcribe", input.audioText ? { text: input.audioText, file_path: input.audioPath } : { file_path: input.audioPath }],
      report: ["/reports/generate", input.text ? { request: enrichedQuestion, text: input.text, file_path: input.filePath, audio_file_path: input.audioPath, audio_text: effectiveTranscript } : { request: enrichedQuestion, file_path: input.filePath, audio_file_path: input.audioPath, audio_text: effectiveTranscript }]
    };
    const [route, body] = routes[workflow];
    lastResult = await post(route, body);
    renderResult(lastResult, workflow);
    byId("status").textContent = "Completed";
  } catch (error) {
    byId("status").textContent = error.message;
    byId("status").className = "status error";
    lastResult = { error: error.message };
    byId("result").textContent = JSON.stringify(lastResult, null, 2);
  } finally {
    byId("runBtn").disabled = false;
  }
}

async function getRecordingTranscript(input) {
  if (!input.audioPath && !input.audioText) return "";
  const payload = input.audioText ? { text: input.audioText, file_path: input.audioPath } : { file_path: input.audioPath };
  const data = await post("/audio/transcribe", payload);
  return data.transcript || "";
}

async function ensureAudioTranscript(input) {
  const existing = byId("audioTranscript").value.trim();
  if (existing) return existing;
  const transcript = await getRecordingTranscript(input);
  byId("audioTranscript").value = transcript;
  byId("transcriptStatus").textContent = transcript ? "Transcript ready" : "No transcript returned";
  return transcript;
}

async function transcribeSelectedAudio() {
  byId("transcribeBtn").disabled = true;
  byId("transcriptStatus").textContent = "Transcribing...";
  byId("transcriptStatus").className = "status";
  try {
    const audioFile = byId("audioUpload").files[0];
    let data;
    if (audioFile) {
      if (isTextFile(audioFile)) {
        data = await post("/audio/transcribe", { file_path: audioFile.name, text: await audioFile.text() });
      } else {
        const form = new FormData();
        form.append("file", audioFile);
        const response = await fetch(`${apiBase()}/audio/transcribe-upload`, { method: "POST", body: form });
        data = await response.json();
        if (!response.ok) throw new Error(data.detail || "Audio transcription failed.");
      }
    } else {
      data = await post("/audio/transcribe", { file_path: byId("audioPath").value });
    }
    byId("audioTranscript").value = data.transcript || "";
    byId("transcriptStatus").textContent = `${data.adapter || "ASR"} transcript ready`;
  } catch (error) {
    byId("transcriptStatus").textContent = error.message;
    byId("transcriptStatus").className = "status error";
  } finally {
    byId("transcribeBtn").disabled = false;
  }
}

function renderResult(data, workflow) {
  const agentReport = data.report?.report || data.report || {};
  const finalAnswer = data.fields || data.summary || data.answer ? data : agentReport.final_answer || {};
  const planSteps = data.plan?.steps || agentReport.agent_plan?.steps || [];
  const tools = agentReport.tools_used || planSteps.map((step) => step.tool) || [];
  const citations = data.citations || agentReport.retrieved_evidence || data.results || [];
  const metrics = agentReport.evaluation_metrics || data.metrics || data.report?.evaluation_metrics || {};
  const fields = finalAnswer.fields || {};
  const updateOutput = agentReport.intermediate_outputs?.tool_update_resume_from_instruction || {};

  byId("result").textContent = JSON.stringify(data, null, 2);
  byId("toolCount").textContent = tools.length || "-";
  byId("fieldCount").textContent = Object.keys(fields).length || "-";
  byId("evidenceCount").textContent = citations.length || "-";
  byId("qualityScore").textContent = formatMetric(metrics.field_accuracy);
  byId("answer").textContent = finalAnswer.answer || answerFromWorkflow(data, workflow);
  byId("summary").textContent = finalAnswer.summary || "No summary returned for this workflow.";
  byId("planRows").innerHTML = renderPlanRows(planSteps);
  byId("fieldRows").innerHTML = renderFieldRows(fields);
  byId("evidenceRows").innerHTML = renderEvidenceRows(citations);
  byId("metricRows").innerHTML = renderMetricRows(metrics);
  byId("reportId").textContent = data.report?.report_id || agentReport.report_id || "-";
  byId("jsonPath").textContent = data.report?.json_path || data.json_path || "-";
  byId("markdownPath").textContent = data.report?.markdown_path || data.markdown_path || "-";
  byId("updatedResumePath").textContent = finalAnswer.updated_resume_path || updateOutput.updated_resume_path || "-";
  byId("changesApplied").textContent = (finalAnswer.changes || updateOutput.changes || []).join("; ") || "-";
  byId("updatedResume").textContent = updateOutput.updated_resume_markdown || "No updated resume generated for this workflow.";
}

function answerFromWorkflow(data, workflow) {
  if (workflow === "ingest") return `Ingested ${data.chunks?.length || 0} chunks for ${data.document_id || "document"}.`;
  if (workflow === "search") return `${data.results?.length || 0} search results returned.`;
  if (workflow === "asr") return data.transcript || "No transcript returned.";
  if (workflow === "report") return `Generated report ${data.report_id || ""}`.trim();
  return "I could not find enough evidence in the uploaded document.";
}

function renderPlanRows(steps) {
  if (!steps.length) return '<tr><td colspan="3" class="muted">No plan returned for this workflow.</td></tr>';
  return steps.map((step, index) => `<tr><td>${index + 1}</td><td>${escapeHtml(step.tool)}</td><td>${escapeHtml(step.reason || "-")}</td></tr>`).join("");
}

function renderFieldRows(fields) {
  const entries = Object.entries(fields || {});
  if (!entries.length) return '<tr><td colspan="2" class="muted">No structured fields extracted.</td></tr>';
  return entries.map(([key, value]) => `<tr><td>${escapeHtml(key)}</td><td>${escapeHtml(value)}</td></tr>`).join("");
}

function renderEvidenceRows(items) {
  if (!items.length) return '<tr><td colspan="4" class="muted">No evidence retrieved.</td></tr>';
  return items.map((item) => {
    const source = item.source_file || item.source || "-";
    const chunk = item.chunk_id || "-";
    const score = formatMetric(item.confidence ?? item.score);
    const snippet = item.matched_text_snippet || item.snippet || item.text || "-";
    return `<tr><td>${escapeHtml(source)}</td><td>${escapeHtml(chunk)}</td><td>${escapeHtml(score)}</td><td>${escapeHtml(snippet)}</td></tr>`;
  }).join("");
}

function renderMetricRows(metrics) {
  const entries = Object.entries(metrics || {});
  if (!entries.length) return '<tr><td colspan="2" class="muted">No evaluation metrics returned.</td></tr>';
  return entries.map(([key, value]) => `<tr><td>${escapeHtml(key)}</td><td>${escapeHtml(formatValue(value))}</td></tr>`).join("");
}

function renderPreview(text) {
  byId("preview").innerHTML = `<pre>${escapeHtml(text || "")}</pre>`;
}

function clearUi() {
  lastResult = {};
  byId("result").textContent = "{}";
  byId("answer").textContent = "No answer yet.";
  byId("summary").textContent = "Run the workflow to generate a grounded summary.";
  byId("planRows").innerHTML = '<tr><td colspan="3" class="muted">No plan yet.</td></tr>';
  byId("fieldRows").innerHTML = '<tr><td colspan="2" class="muted">No fields yet.</td></tr>';
  byId("evidenceRows").innerHTML = '<tr><td colspan="4" class="muted">No evidence retrieved yet.</td></tr>';
  byId("metricRows").innerHTML = '<tr><td colspan="2" class="muted">No metrics yet.</td></tr>';
  byId("toolCount").textContent = "-";
  byId("fieldCount").textContent = "-";
  byId("evidenceCount").textContent = "-";
  byId("qualityScore").textContent = "-";
  byId("reportId").textContent = "-";
  byId("jsonPath").textContent = "-";
  byId("markdownPath").textContent = "-";
  byId("updatedResumePath").textContent = "-";
  byId("changesApplied").textContent = "-";
  byId("updatedResume").textContent = "No updated resume generated yet.";
  byId("audioTranscript").value = "";
  byId("transcriptStatus").textContent = "No transcript yet";
  byId("transcriptStatus").className = "status";
}

function download(name, content, type) {
  const blob = new Blob([content], { type });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = name;
  link.click();
  URL.revokeObjectURL(url);
}

function formatMetric(value) {
  if (value === undefined || value === null || value === "") return "-";
  if (typeof value === "number") return Number.isInteger(value) ? String(value) : value.toFixed(2);
  return String(value);
}

function formatValue(value) {
  if (typeof value === "object" && value !== null) return JSON.stringify(value);
  return formatMetric(value);
}

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, (char) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[char]));
}

byId("runBtn").addEventListener("click", runWorkflow);
byId("clearBtn").addEventListener("click", clearUi);
byId("transcribeBtn").addEventListener("click", transcribeSelectedAudio);
byId("downloadJson").addEventListener("click", () => download("assistant-result.json", JSON.stringify(lastResult, null, 2), "application/json"));
byId("downloadMd").addEventListener("click", () => {
  const md = lastResult.report?.markdown_path || lastResult.markdown_path || "Run a report workflow first.";
  download("assistant-report-link.md", md, "text/markdown");
});
byId("docUpload").addEventListener("change", async () => {
  const file = byId("docUpload").files[0];
  if (file) renderPreview(await readDocumentFile(file));
});
byId("sampleText").addEventListener("input", () => renderPreview(byId("sampleText").value));

setInputMode("sample");
loadSample("invoice");
checkHealth();
