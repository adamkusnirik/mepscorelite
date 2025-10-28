import { loadTermDataset, createGroupDisplay, createCountryDisplay } from "./utilities.js";

const inputs = document.querySelectorAll("input[data-key]");
const tbody = document.getElementById("custom-table-body");
const termSelect = document.getElementById("term-select");

let dataset = [];

// Load initial dataset
loadTermDataset(termSelect.value).then(data => {
  dataset = data.meps;
  const term = termSelect.value;
  recompute();
});

// Handle term changes
termSelect.addEventListener("change", async () => {
  const term = termSelect.value;
  const data = await loadTermDataset(term);
  dataset = data.meps;
  recompute();
});


function recompute() {
  // Gather weights from input fields
  const weights = {};
  inputs.forEach(input => {
    weights[input.dataset.key] = parseFloat(input.value) || 0;
  });
  
  // Calculate custom scores for each MEP
  const rows = dataset.map(mep => {
    let customScore = 0;
    
    // Apply weights to each activity/role count
    for (const key in weights) {
      customScore += (mep[key] || 0) * weights[key];
    }
    
    return { ...mep, customScore };
  });
  
  // Sort by custom score (descending)
  rows.sort((a, b) => b.customScore - a.customScore);
  
  // Render table - show all rows
  tbody.innerHTML = "";
  rows.forEach((row, index) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${index + 1}</td>
      <td>${row.full_name}</td>
      <td>${createCountryDisplay(row.country, { size: 'small', showCode: true })}</td>
      <td>${createGroupDisplay(row.group, { size: 'small' })}</td>
      <td>${row.customScore.toFixed(2)}</td>`;
    tbody.appendChild(tr);
  });
}

// Apply button click handler
document.getElementById("apply-btn").onclick = recompute;

// Optional: Live updates as inputs change
inputs.forEach(input => {
  input.addEventListener("input", () => {
    // Uncomment the next line for live updates
    // recompute();
  });
}); 