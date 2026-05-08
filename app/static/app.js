const questionInput = document.getElementById("question");
const modeInput = document.getElementById("mode");
const topKInput = document.getElementById("topK");
const askButton = document.getElementById("askButton");
const statusBox = document.getElementById("status");

const answerCard = document.getElementById("answerCard");
const answerBox = document.getElementById("answer");

const sourcesCard = document.getElementById("sourcesCard");
const sourcesList = document.getElementById("sources");

async function askQuestion() {
  const question = questionInput.value.trim();
  const mode = modeInput.value;
  const topK = Number(topKInput.value);

  if (!question) {
    statusBox.textContent = "Skriv et spørgsmål først.";
    return;
  }

  askButton.disabled = true;
  statusBox.textContent = "Henter kilder og genererer svar...";
  answerCard.classList.add("hidden");
  sourcesCard.classList.add("hidden");
  answerBox.textContent = "";
  sourcesList.innerHTML = "";

  try {
    const response = await fetch("/v1/ask", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        question: question,
        top_k: topK,
        mode: mode,
      }),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || "Ukendt fejl");
    }

    const data = await response.json();

    answerBox.textContent = data.answer || "Intet svar returneret.";
    answerCard.classList.remove("hidden");

    const sources = data.sources || [];

    if (sources.length > 0) {
      for (const source of sources) {
        const li = document.createElement("li");

        const link = document.createElement("a");
        link.href = source.url;
        link.target = "_blank";
        link.rel = "noopener noreferrer";
        link.textContent = source.title || source.url;

        li.appendChild(link);
        sourcesList.appendChild(li);
      }

      sourcesCard.classList.remove("hidden");
    }

    statusBox.textContent = `Færdig. Retrieval query: ${data.retrieval_query || "ikke angivet"}`;
  } catch (error) {
    statusBox.textContent = `Fejl: ${error.message}`;
  } finally {
    askButton.disabled = false;
  }
}

askButton.addEventListener("click", askQuestion);

questionInput.addEventListener("keydown", (event) => {
  if (event.ctrlKey && event.key === "Enter") {
    askQuestion();
  }
});

document.querySelectorAll(".example").forEach((button) => {
  button.addEventListener("click", () => {
    questionInput.value = button.textContent;
    questionInput.focus();
  });
});

const evalButton = document.getElementById("evalButton");
const evalStatus = document.getElementById("evalStatus");
const evalModeInput = document.getElementById("evalMode");
const evalTopKInput = document.getElementById("evalTopK");
const evalLimitInput = document.getElementById("evalLimit");

const evalSummaryCard = document.getElementById("evalSummaryCard");
const evalResultsCard = document.getElementById("evalResultsCard");
const evalResultsBody = document.getElementById("evalResultsBody");

const metricQuestions = document.getElementById("metricQuestions");
const metricRetrieval = document.getElementById("metricRetrieval");
const metricCoverage = document.getElementById("metricCoverage");
const metricUnknown = document.getElementById("metricUnknown");

function formatPercent(value) {
  if (value === null || value === undefined) {
    return "-";
  }
  return `${(value * 100).toFixed(1)}%`;
}

function badge(value) {
  if (value === true) {
    return `<span class="badge badge-ok">OK</span>`;
  }
  if (value === false) {
    return `<span class="badge badge-fail">Fail</span>`;
  }
  return `<span class="badge badge-neutral">N/A</span>`;
}

async function runEvaluation() {
  const mode = evalModeInput.value;
  const topK = Number(evalTopKInput.value);
  const limitRaw = evalLimitInput.value.trim();

  const payload = {
    mode: mode,
    top_k: topK,
  };

  if (limitRaw) {
    payload.limit = Number(limitRaw);
  }

  evalButton.disabled = true;
  evalStatus.textContent = "Kører evaluation. Det kan tage lidt tid...";
  evalSummaryCard.classList.add("hidden");
  evalResultsCard.classList.add("hidden");
  evalResultsBody.innerHTML = "";

  try {
    const response = await fetch("/v1/evaluate", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || "Ukendt fejl");
    }

    const data = await response.json();

    metricQuestions.textContent = data.num_questions;
    metricRetrieval.textContent = formatPercent(data.retrieval_hit_rate);
    metricCoverage.textContent = formatPercent(data.avg_keyword_coverage);
    metricUnknown.textContent = formatPercent(data.unknown_accuracy);

    for (const result of data.results) {
      const tr = document.createElement("tr");
      tr.classList.add("clickable-row");

      const detailsTr = document.createElement("tr");
      detailsTr.classList.add("details-row", "hidden");

      tr.innerHTML = `
        <td>${result.id}</td>
        <td>${result.category}</td>
        <td>${result.question}</td>
        <td>${badge(result.retrieval_hit)}</td>
        <td>${formatPercent(result.keyword_coverage)}</td>
        <td>${badge(result.unknown_correct)}</td>
      `;

      detailsTr.innerHTML = `
        <td colspan="6">
          <div class="details-box">
            <p><strong>Expected behavior:</strong> ${result.expected_behavior}</p>
            <p><strong>Expected unknown:</strong> ${result.expected_unknown}</p>
            <p><strong>Predicted unknown:</strong> ${result.predicted_unknown}</p>

            <p><strong>Retrieval query:</strong> ${result.retrieval_query || "-"}</p>
            <p><strong>Rewritten query:</strong> ${result.rewritten_query || "-"}</p>

            <p><strong>Answer:</strong></p>
            <div class="eval-answer">${escapeHtml(result.answer || "")}</div>

            <p><strong>Keywords:</strong></p>
            <div class="keywords">
              ${renderKeywords(result.matched_keywords || [], result.missed_keywords || [])}
            </div>

            <p><strong>Sources:</strong></p>
            <ul>
              ${(result.sources || []).map(source => `
                <li>
                  <a href="${source.url}" target="_blank" rel="noopener noreferrer">
                    ${escapeHtml(source.title || source.url)}
                  </a>
                </li>
              `).join("")}
            </ul>
          </div>
        </td>
      `;

      tr.addEventListener("click", () => {
        detailsTr.classList.toggle("hidden");
      });

      evalResultsBody.appendChild(tr);
      evalResultsBody.appendChild(detailsTr);
    }

    evalSummaryCard.classList.remove("hidden");
    evalResultsCard.classList.remove("hidden");

    evalStatus.textContent = "Evaluation færdig.";
  } catch (error) {
    evalStatus.textContent = `Fejl: ${error.message}`;
  } finally {
    evalButton.disabled = false;
  }
}

function escapeHtml(text) {
  return text
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function renderKeywords(matched, missed) {
  const matchedHtml = matched.map(keyword =>
    `<span class="keyword keyword-hit">${escapeHtml(keyword)}</span>`
  ).join("");

  const missedHtml = missed.map(keyword =>
    `<span class="keyword keyword-miss">${escapeHtml(keyword)}</span>`
  ).join("");

  if (!matchedHtml && !missedHtml) {
    return `<span class="muted">No keywords</span>`;
  }

  return matchedHtml + missedHtml;
}


evalButton.addEventListener("click", runEvaluation);