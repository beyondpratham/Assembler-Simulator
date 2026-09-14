const sourceEl = document.getElementById("source");
const runBtn = document.getElementById("run-btn");
const loadExampleBtn = document.getElementById("load-example");
const errorBanner = document.getElementById("error-banner");
const binaryOutput = document.getElementById("binary-output");
const binaryCount = document.getElementById("binary-count");
const traceBody = document.querySelector("#trace-table tbody");
const traceCount = document.getElementById("trace-count");
const memoryOutput = document.getElementById("memory-output");
const chartLegend = document.getElementById("chart-legend");
const chartContainer = document.getElementById("chart-container");

const EXAMPLE_SOURCE = sourceEl.value;
const MAX_TABLE_ROWS = 2000;
const MAX_CHART_POINTS = 2000;

const chartTooltip = document.createElement("div");
chartTooltip.className = "chart-tooltip";
chartTooltip.hidden = true;
document.body.appendChild(chartTooltip);

const FLAG_BITS = [
  { mask: 8, label: "V" },
  { mask: 4, label: "L" },
  { mask: 2, label: "G" },
  { mask: 1, label: "E" },
];

function flagsLabel(flags) {
  const active = FLAG_BITS.filter((f) => flags & f.mask).map((f) => f.label);
  return active.length ? active.join("") : "-";
}

function toBin(value, width) {
  return value.toString(2).padStart(width, "0");
}

function showError(message) {
  errorBanner.textContent = message;
  errorBanner.hidden = false;
}

function clearError() {
  errorBanner.hidden = true;
  errorBanner.textContent = "";
}

function renderBinary(lines) {
  binaryOutput.textContent = lines.join("\n");
  binaryCount.textContent = `(${lines.length} word${lines.length === 1 ? "" : "s"})`;
}

function renderTrace(trace, traceTotal) {
  traceBody.innerHTML = "";
  const shown = trace.slice(0, MAX_TABLE_ROWS);
  for (const snap of shown) {
    const tr = document.createElement("tr");
    const cells = [
      toBin(snap.pc, 8),
      ...["R0", "R1", "R2", "R3", "R4", "R5", "R6"].map((r) => snap.registers[r]),
      `${flagsLabel(snap.flags)} (${snap.flags_binary})`,
    ];
    for (const value of cells) {
      const td = document.createElement("td");
      td.textContent = value;
      tr.appendChild(td);
    }
    traceBody.appendChild(tr);
  }
  const total = traceTotal ?? trace.length;
  const suffix = total > shown.length ? ` — showing first ${shown.length}` : "";
  traceCount.textContent = `(${total} step${total === 1 ? "" : "s"}${suffix})`;
}

function renderMemory(memory) {
  memoryOutput.textContent = memory
    .map((word, addr) => `${String(addr).padStart(3, "0")}: ${word}`)
    .join("\n");
}

const ACCESS_CATEGORIES = {
  fetch: { label: "Instruction fetch", color: "var(--series-1)" },
  read: { label: "Data access (ld/st)", color: "var(--series-2)" },
  write: { label: "Data access (ld/st)", color: "var(--series-2)" },
  "jump-target": { label: "Jump taken", color: "var(--series-3)" },
};

function renderLegend() {
  const seen = new Set();
  chartLegend.innerHTML = "";
  for (const key of ["fetch", "read", "jump-target"]) {
    const cat = ACCESS_CATEGORIES[key];
    if (seen.has(cat.label)) continue;
    seen.add(cat.label);
    const span = document.createElement("span");
    span.innerHTML = `<span class="swatch" style="background:${cat.color}"></span>${cat.label}`;
    chartLegend.appendChild(span);
  }
}

function renderAccessChart(accesses, accessesTotal) {
  chartContainer.innerHTML = "";
  chartTooltip.hidden = true;
  if (!accesses.length) {
    chartContainer.innerHTML = '<p class="empty-state">No memory accesses recorded.</p>';
    return;
  }

  const points = accesses.slice(0, MAX_CHART_POINTS);
  const maxCycle = Math.max(1, ...points.map((p) => p.cycle));

  const pad = { left: 44, right: 16, top: 12, bottom: 30 };
  const viewW = Math.max(420, Math.min(1100, pad.left + pad.right + maxCycle * 5));
  const viewH = 260;
  const plotW = viewW - pad.left - pad.right;
  const plotH = viewH - pad.top - pad.bottom;

  const xScale = (cycle) => pad.left + (maxCycle === 0 ? 0 : (cycle / maxCycle) * plotW);
  const yScale = (addr) => pad.top + (addr / 255) * plotH;

  const svgns = "http://www.w3.org/2000/svg";
  const svg = document.createElementNS(svgns, "svg");
  svg.setAttribute("viewBox", `0 0 ${viewW} ${viewH}`);
  svg.setAttribute("width", "100%");
  svg.setAttribute("height", viewH);

  const yTicks = [0, 64, 128, 192, 255];
  for (const addr of yTicks) {
    const y = yScale(addr);
    const line = document.createElementNS(svgns, "line");
    line.setAttribute("x1", pad.left);
    line.setAttribute("x2", viewW - pad.right);
    line.setAttribute("y1", y);
    line.setAttribute("y2", y);
    line.setAttribute("stroke", "var(--gridline)");
    line.setAttribute("stroke-width", "1");
    svg.appendChild(line);

    const label = document.createElementNS(svgns, "text");
    label.setAttribute("x", pad.left - 8);
    label.setAttribute("y", y + 3);
    label.setAttribute("text-anchor", "end");
    label.setAttribute("fill", "var(--text-muted)");
    label.setAttribute("font-size", "9");
    label.textContent = addr;
    svg.appendChild(label);
  }

  const xTickCount = Math.min(6, maxCycle + 1);
  for (let i = 0; i <= xTickCount; i++) {
    const cycle = Math.round((maxCycle / xTickCount) * i);
    const x = xScale(cycle);
    const label = document.createElementNS(svgns, "text");
    label.setAttribute("x", x);
    label.setAttribute("y", viewH - pad.bottom + 16);
    label.setAttribute("text-anchor", "middle");
    label.setAttribute("fill", "var(--text-muted)");
    label.setAttribute("font-size", "9");
    label.textContent = cycle;
    svg.appendChild(label);
  }

  const axisLabelX = document.createElementNS(svgns, "text");
  axisLabelX.setAttribute("x", viewW / 2);
  axisLabelX.setAttribute("y", viewH - 4);
  axisLabelX.setAttribute("text-anchor", "middle");
  axisLabelX.setAttribute("fill", "var(--text-muted)");
  axisLabelX.setAttribute("font-size", "9");
  axisLabelX.textContent = "cycle";
  svg.appendChild(axisLabelX);

  const axisLabelY = document.createElementNS(svgns, "text");
  axisLabelY.setAttribute("x", -viewH / 2);
  axisLabelY.setAttribute("y", 12);
  axisLabelY.setAttribute("text-anchor", "middle");
  axisLabelY.setAttribute("fill", "var(--text-muted)");
  axisLabelY.setAttribute("font-size", "9");
  axisLabelY.setAttribute("transform", "rotate(-90)");
  axisLabelY.textContent = "memory address";
  svg.appendChild(axisLabelY);

  for (const point of points) {
    const cat = ACCESS_CATEGORIES[point.kind] || ACCESS_CATEGORIES.fetch;
    const circle = document.createElementNS(svgns, "circle");
    circle.setAttribute("cx", xScale(point.cycle));
    circle.setAttribute("cy", yScale(point.address));
    circle.setAttribute("r", 3);
    circle.setAttribute("fill", cat.color);
    circle.setAttribute("fill-opacity", "0.8");
    circle.addEventListener("mousemove", (evt) => {
      chartTooltip.hidden = false;
      chartTooltip.style.left = `${evt.clientX + 12}px`;
      chartTooltip.style.top = `${evt.clientY + 12}px`;
      chartTooltip.textContent = `cycle ${point.cycle} · addr ${point.address} · ${point.kind}`;
    });
    circle.addEventListener("mouseleave", () => {
      chartTooltip.hidden = true;
    });
    svg.appendChild(circle);
  }

  chartContainer.appendChild(svg);
  const totalAccesses = accessesTotal ?? accesses.length;
  if (totalAccesses > points.length) {
    const note = document.createElement("p");
    note.className = "empty-state";
    note.textContent = `Showing first ${points.length} of ${totalAccesses} accesses.`;
    chartContainer.appendChild(note);
  }
}

async function runProgram() {
  clearError();
  runBtn.disabled = true;
  runBtn.textContent = "Running…";
  try {
    const response = await fetch("/api/run", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ source: sourceEl.value }),
    });
    const data = await response.json();

    if (data.stage === "assemble") {
      showError(`Assembler error${data.line ? ` (line ${data.line})` : ""}: ${data.error}`);
      renderBinary([]);
      renderTrace([]);
      renderMemory([]);
      renderAccessChart([]);
      return;
    }

    if (data.stage === "simulate") {
      showError(`Simulator error: ${data.error}`);
      renderBinary(data.binary || []);
      renderTrace([]);
      renderMemory([]);
      renderAccessChart([]);
      return;
    }

    renderBinary(data.binary);
    renderTrace(data.trace, data.trace_total);
    renderMemory(data.memory);
    renderLegend();
    renderAccessChart(data.accesses, data.accesses_total);
  } catch (err) {
    showError(`Request failed: ${err}`);
  } finally {
    runBtn.disabled = false;
    runBtn.textContent = "Run";
  }
}

runBtn.addEventListener("click", runProgram);
loadExampleBtn.addEventListener("click", () => {
  sourceEl.value = EXAMPLE_SOURCE;
});
sourceEl.addEventListener("keydown", (evt) => {
  if ((evt.ctrlKey || evt.metaKey) && evt.key === "Enter") {
    evt.preventDefault();
    runProgram();
  }
});

runProgram();
