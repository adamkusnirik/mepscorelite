import { loadTermDataset, createGroupDisplay, createCountryDisplay } from "./utilities.js";
import { showScoreBreakdown, hideScoreBreakdown, initializeScoreBreakdownModal } from "./score-breakdown.js";

// DOM Elements
const termSelect = document.getElementById("term-select");
const generalSearch = document.getElementById("general-search");
const countryFilter = document.getElementById("country-filter");
const groupFilter = document.getElementById("group-filter");
const partyFilter = document.getElementById("party-filter");
const resetFiltersBtn = document.getElementById("reset-filters");
const selectAllActivitiesBtn = document.getElementById("select-all-activities");
const clearAllActivitiesBtn = document.getElementById("clear-all-activities");
const activityButtons = document.getElementById("activity-buttons");
const tbody = document.getElementById("explorer-table-body");
const resultsCount = document.getElementById("results-count");
const activeFilters = document.getElementById("active-filters");
const tableHead = document.getElementById("explorer-table-head");

// Keep track of all data for the current term
let currentTermData = [];
// Sorting state
let currentSortColumn = 'score'; // Default sort: score
let currentSortDirection = 'desc';

// Global current term for mobile interface
window.currentTerm = 10;

// Scoring mode state
let currentScoringMode = 'mep-ranking'; // 'mep-ranking' or 'custom-weights'
let customWeights = {
  legislative_production: 0,      // Legislative Production (-100% to +100%)
  control_transparency: 0,        // Control & Transparency (-100% to +100%)
  engagement_presence: 0,         // Engagement & Presence (-100% to +100%)
  institutional_roles: 0          // Institutional Roles (-100% to +100%)
};
let attendancePenaltyEnabled = true; // Track whether attendance penalty is enabled

// New 4-category methodology - scores are calculated by backend
// Custom weights allow user to adjust the 4 category weightings with -100% to +100% range

// Activity columns definition
const activityColumns = [
  // Legislative Activities
  { id: "speeches", label: "Speeches", tooltip: "Plenary speeches delivered", weight: 0.5 },
  { 
    id: "reports_opinions", 
    label: "Reports & Opinions", 
    tooltip: "Combined reports and opinions as rapporteur and shadow",
    breakdown: {
      reports_rapporteur: { label: "Reports (Rapporteur)", weight: 10 },
      reports_shadow: { label: "Reports (Shadow)", weight: 3 },
      opinions_rapporteur: { label: "Opinions (Rapporteur)", weight: 6 },
      opinions_shadow: { label: "Opinions (Shadow)", weight: 2 }
    }
  },
  { id: "amendments", label: "Amendments", tooltip: "Amendments tabled by the MEP", weight: 1 },
  { id: "questions", label: "Questions", tooltip: "Questions for written answers", weight: 1 },
  { id: "motions", label: "Motions", tooltip: "Motions for resolutions", weight: 2 },
  { id: "explanations", label: "Vote Explanations", tooltip: "Explanations of votes", weight: 1 },
  { id: "votes_attended", label: "Votes Attended", tooltip: "Votes attended by the MEP", weight: 0.1 },
  
  // Committee Roles
  { id: "committee_chair", label: "Committee Chair", tooltip: "Chair position in parliamentary committee", weight: 10 },
  { id: "committee_vice_chair", label: "Committee Vice Chair", tooltip: "Vice-chair position in parliamentary committee", weight: 7 },
  { id: "committee_member", label: "Committee Member", tooltip: "Regular membership in parliamentary committee", weight: 5 },
  { id: "committee_substitute", label: "Committee Substitute", tooltip: "Substitute membership in parliamentary committee", weight: 2 },
  
  // Delegation Roles
  { id: "delegation_chair", label: "Delegation Chair", tooltip: "Chair position in parliamentary delegation", weight: 8 },
  { id: "delegation_vice_chair", label: "Delegation Vice Chair", tooltip: "Vice-chair position in parliamentary delegation", weight: 5 },
  { id: "delegation_member", label: "Delegation Member", tooltip: "Regular membership in parliamentary delegation", weight: 3 },
  { id: "delegation_substitute", label: "Delegation Substitute", tooltip: "Substitute membership in parliamentary delegation", weight: 1.5 },
  
  // EP Leadership
  { id: "ep_president", label: "EP President", tooltip: "President of the European Parliament", weight: 10 },
  { id: "ep_vice_president", label: "EP Vice President", tooltip: "Vice-President of the European Parliament", weight: 7 },
  { id: "ep_quaestor", label: "EP Quaestor", tooltip: "Quaestor of the European Parliament", weight: 6 }
];

// Political group information
const groupInfo = {
  "EPP": {
    name: "Group of the European People's Party (Christian Democrats)",
    ideology: "Centre-right, Christian democratic, conservative, and liberal-conservative orientation. Largest group since 1999."
  },
  "S&D": {
    name: "Group of the Progressive Alliance of Socialists and Democrats in the European Parliament",
    ideology: "Centre-left, social democratic."
  },
  "ECR": {
    name: "European Conservatives and Reformists Group",
    ideology: "Right-wing, conservative, and Eurosceptic."
  },
  "ALDE": {
    name: "Group of the Alliance of Liberals and Democrats for Europe",
    ideology: "Centrist, liberal."
  },
  "RE": {
    name: "Renew Europe Group",
    ideology: "Centrist, pro-European liberal group."
  },
  "Greens/EFA": {
    name: "Group of the Greens/European Free Alliance",
    ideology: "Green, regionalist, and progressive."
  },
  "GUE/NGL": {
    name: "Confederal Group of the European United Left/Nordic Green Left",
    ideology: "Left-wing, socialist, and communist."
  },
  "EFDD": {
    name: "Europe of Freedom and Direct Democracy Group",
    ideology: "Eurosceptic, populist."
  },
  "ID": {
    name: "Identity and Democracy Group",
    ideology: "Far-right, nationalist, Eurosceptic."
  },
  "ENF": {
    name: "Europe of Nations and Freedom Group",
    ideology: "Far-right, Eurosceptic."
  },
  "PfE": {
    name: "Patriots for Europe",
    ideology: "Far-right, nationalist, Eurosceptic."
  },
  "ESN": {
    name: "Europe of Sovereign Nations",
    ideology: "Far-right, nationalist."
  },
  "NI": {
    name: "Non-Inscrits (Non-Attached Members)",
    ideology: "Not a formal group but a category for MEPs not affiliated with any political group."
  }
};

/**
 * Create table cell for political group with logo and info popup
 */
function createGroupCell(group, index) {
  const info = groupInfo[group] || { name: group };
  
  const cell = document.createElement('td');
  cell.className = 'group-cell'; // Add class to the TD itself
  cell.innerHTML = createGroupDisplay(group, { size: 'small' });
  return cell; // Return the DOM element
}

/**
 * Update active filters display
 */
function updateActiveFilters() {
  activeFilters.innerHTML = '';
  
  const filters = [];
  
  // Get active filters
  if (countryFilter.value) filters.push({ type: 'country', value: countryFilter.value });
  if (groupFilter.value) filters.push({ type: 'group', value: groupFilter.value });
  if (partyFilter.value) filters.push({ type: 'party', value: partyFilter.value });
  if (generalSearch.value) filters.push({ type: 'search', value: generalSearch.value });
  
  // Create filter badges
  filters.forEach(filter => {
    const badge = document.createElement('span');
    badge.className = 'filter-badge';
    badge.innerHTML = `
      ${filter.type === 'country' ? '🌍 ' : filter.type === 'group' ? '👥 ' : filter.type === 'party' ? '🏛️ ' : '🔍 '}
      ${filter.value}
      <button class="remove-filter" data-type="${filter.type}">×</button>
    `;
    activeFilters.appendChild(badge);
  });
  
  // Add event listeners to remove buttons
  document.querySelectorAll('.remove-filter').forEach(btn => {
    btn.addEventListener('click', () => {
      const type = btn.dataset.type;
      if (type === 'country') countryFilter.value = '';
      if (type === 'group') groupFilter.value = '';
      if (type === 'party') partyFilter.value = '';
      if (type === 'search') generalSearch.value = '';
      
      updateFilterOptions().then(() => render());
    });
  });
}

/**
 * Reset all filters to default values
 */
function resetFilters() {
  generalSearch.value = '';
  countryFilter.value = '';
  groupFilter.value = '';
  partyFilter.value = '';
  
  updateFilterOptions().then(() => render());
}

/**
 * Get filtered rows based on current selection
 */
function getFilteredRows(rows, selectedCountry = '') {
  if (!selectedCountry) return rows;
  return rows.filter(r => r.country === selectedCountry);
}

/**
 * Validate dataset integrity
 */
function validateDataset(data) {
  
  let validationIssues = {
    missingScores: 0,
    zeroScores: 0,
    missingNames: 0,
    missingIds: 0,
    invalidData: []
  };
  
  data.forEach((mep, index) => {
    // Check for missing required fields
    if (!mep.mep_id) {
      validationIssues.missingIds++;
      validationIssues.invalidData.push(`Row ${index}: Missing mep_id`);
    }
    
    if (!mep.full_name) {
      validationIssues.missingNames++;
      validationIssues.invalidData.push(`Row ${index}: Missing full_name`);
    }
    
    // Check for score issues
    if (!mep.final_score && !mep.score) {
      validationIssues.missingScores++;
    }
    
    if ((mep.final_score || mep.score || 0) === 0) {
      validationIssues.zeroScores++;
    }
  });
  
  // Log summary
  console.log('Dataset validation summary:', {
    totalMEPs: data.length,
    missingIds: validationIssues.missingIds,
    missingNames: validationIssues.missingNames,
    missingScores: validationIssues.missingScores,
    zeroScores: validationIssues.zeroScores
  });
  
  // Log first few detailed issues
  if (validationIssues.invalidData.length > 0) {
    console.warn('Data validation issues:', validationIssues.invalidData.slice(0, 5));
  }
  
  return validationIssues;
}

/**
 * Update filter dropdowns with available options
 */
async function updateFilterOptions(forceReload = false) {
  const term = termSelect.value;
  window.currentTerm = parseInt(term); // Update global term for mobile
  
  // Load new data if term changed or forced reload
  if (forceReload || !currentTermData.length) {
    // Loading dataset for term
    const termDataset = await loadTermDataset(term);
    // Dataset loaded
    
    if (termDataset) {
      // Handle both direct array and object with 'meps' property
      let rawData = Array.isArray(termDataset) ? termDataset : termDataset.meps || [];
      // MEP records processed
      
      // Validate dataset integrity
      validateDataset(rawData);
      
      // Use MEP Ranking scores from the dataset (already calculated by build_term_dataset.py)
      currentTermData = rawData.map(mep => ({
        ...mep,
        // Use original score initially
        score: mep.final_score || mep.score || 0
      }));
      console.log(`Mapped ${currentTermData.length} MEPs to currentTermData`);
    } else {
      console.error("Failed to load MEPs array from dataset", termDataset);
      currentTermData = [];
    }
    updateActivityCounts();
  }
  
  const selectedCountry = countryFilter.value;
  const selectedGroup = groupFilter.value;
  const selectedParty = partyFilter.value;
  
  // Get all unique values
  const countries = [...new Set(currentTermData.map(r => r.country))].sort();
  
  // Get filtered rows based on country selection
  const filteredRows = getFilteredRows(currentTermData, selectedCountry);
  
  // Get groups and parties only from the filtered rows
  const groups = [...new Set(filteredRows.map(r => r.group))].sort();
  const parties = [...new Set(filteredRows.map(r => r.national_party).filter(Boolean))].sort();
  
  // Update country filter
  countryFilter.innerHTML = '<option value="">All Countries</option>' +
    countries.map(c => {
      const count = currentTermData.filter(r => r.country === c).length;
      return `<option value="${c}" ${c === selectedCountry ? 'selected' : ''}>
        ${c} (${count})
      </option>`;
    }).join('');
  
  // Update group filter
  groupFilter.innerHTML = '<option value="">All Groups</option>' +
    groups.map(g => {
      const count = filteredRows.filter(r => r.group === g).length;
      return `<option value="${g}" ${g === selectedGroup && groups.includes(g) ? 'selected' : ''}>
        ${g} (${count})
      </option>`;
    }).join('');
  
  // Update party filter
  partyFilter.innerHTML = '<option value="">All Parties</option>' +
    parties.map(p => {
      const count = filteredRows.filter(r => r.national_party === p).length;
      return `<option value="${p}" ${p === selectedParty && parties.includes(p) ? 'selected' : ''}>
        ${p} (${count})
      </option>`;
    }).join('');
  
  // Clear selections if options no longer available
  if (selectedGroup && !groups.includes(selectedGroup)) groupFilter.value = '';
  if (selectedParty && !parties.includes(selectedParty)) partyFilter.value = '';
  
  updateActiveFilters();
}

/**
 * Update activity counts display
 */
function updateActivityCounts() {
  // Calculate counts for each activity type
  const counts = {
    speeches: 0,
    reports_opinions: 0,
    amendments: 0,
    questions_written: 0,
    questions_oral: 0,
    motions: 0,
    explanations: 0,
    votes_attended: 0,
    committee_chair: 0,
    committee_vice_chair: 0,
    committee_member: 0,
    committee_substitute: 0,
    delegation_chair: 0,
    delegation_vice_chair: 0,
    delegation_member: 0,
    delegation_substitute: 0,
    ep_president: 0,
    ep_vice_president: 0,
    ep_quaestor: 0
  };

  // Count MEPs with non-zero values for each activity
  currentTermData.forEach(mep => {
    if (mep.speeches > 0) counts.speeches++;
    if (getReportsOpinionsValue(mep).total > 0) counts.reports_opinions++;
    if (mep.amendments > 0) counts.amendments++;
    if (mep.questions_written > 0) counts.questions_written++;
    if (mep.questions_oral > 0) counts.questions_oral++;
    if (mep.motions > 0) counts.motions++;
    if (mep.explanations > 0) counts.explanations++;
    if (mep.votes_attended > 0) counts.votes_attended++;
    if (mep.committee_chair > 0) counts.committee_chair++;
    if (mep.committee_vice_chair > 0) counts.committee_vice_chair++;
    if (mep.committee_member > 0) counts.committee_member++;
    if (mep.committee_substitute > 0) counts.committee_substitute++;
    if (mep.delegation_chair > 0) counts.delegation_chair++;
    if (mep.delegation_vice_chair > 0) counts.delegation_vice_chair++;
    if (mep.delegation_member > 0) counts.delegation_member++;
    if (mep.delegation_substitute > 0) counts.delegation_substitute++;
    if (mep.ep_president > 0) counts.ep_president++;
    if (mep.ep_vice_president > 0) counts.ep_vice_president++;
    if (mep.ep_quaestor > 0) counts.ep_quaestor++;
  });
  
  // Update count displays
  document.querySelectorAll('.activity-pill').forEach(pill => {
    const activity = pill.dataset.activity;
    const countSpan = pill.querySelector('.activity-count');
    if (countSpan) {
      countSpan.textContent = counts[activity] || 0;
    }
  });
}

/**
 * Format large numbers with k suffix
 */
function formatNumber(num) {
  return num > 999 ? (num/1000).toFixed(1) + 'k' : num;
}

/**
 * Normalize text by removing diacritical marks and converting to lowercase
 */
function normalizeText(text) {
  return text
    .normalize('NFD')               // Normalize to decomposed form
    .replace(/[\u0300-\u036f]/g, '') // Remove combining diacritical marks
    .toLowerCase();                 // Convert to lowercase
}

/**
 * Apply all filters to the data
 */
function applyFilters(rows) {
  const searchText = normalizeText(generalSearch.value);
  const country = countryFilter.value;
  const group = groupFilter.value;
  const party = partyFilter.value;
  
  return rows.filter(r => {
    // Apply general search across multiple fields
    if (searchText) {
      const searchFields = [
        r.full_name,
        r.country,
        r.group,
        r.national_party
      ].map(f => normalizeText(String(f || '')));
      
      if (!searchFields.some(f => f.includes(searchText))) {
        return false;
      }
    }
    
    // Apply specific filters
    if (country && r.country !== country) return false;
    if (group && r.group !== group) return false;
    if (party && r.national_party !== party) return false;
    
    return true;
  });
}

/**
 * Update visible columns based on selected activities
 */
function updateVisibleColumns() {
  const selectedActivities = Array.from(document.querySelectorAll('.activity-pill.selected'))
    .map(btn => btn.dataset.activity);
  
  document.querySelectorAll('.activity-col').forEach(col => {
    const activity = col.dataset.activity;
    if (selectedActivities.includes(activity)) {
      col.style.display = '';
      const cells = document.querySelectorAll(`td[data-activity="${activity}"]`);
      cells.forEach(cell => cell.style.display = '');
    } else {
      col.style.display = 'none';
      const cells = document.querySelectorAll(`td[data-activity="${activity}"]`);
      cells.forEach(cell => cell.style.display = 'none');
    }
  });

  // After visibility changes, update the horizontal scroll slider if available
  if (typeof window.updateTableScrollSlider === 'function') {
    // Use a small timeout to allow layout to settle
    setTimeout(() => window.updateTableScrollSlider(), 50);
  }
}

/**
 * Select all activity columns
 */
function selectAllActivities() {
  document.querySelectorAll('.activity-pill').forEach(pill => {
    pill.classList.add('selected');
  });
  updateVisibleColumns();
}

/**
 * Clear all activity column selections
 */
function clearAllActivities() {
  document.querySelectorAll('.activity-pill').forEach(pill => {
    pill.classList.remove('selected');
  });
  updateVisibleColumns();
}

// MEP Ranking scores are calculated by the backend MEPRankingScorer
// No client-side score calculation needed

/**
 * Calculate combined reports & opinions value
 */
function getReportsOpinionsValue(mep) {
  const reports = {
    rapporteur: mep.reports_rapporteur || 0,
    shadow: mep.reports_shadow || 0
  };
  const opinions = {
    rapporteur: mep.opinions_rapporteur || 0,
    shadow: mep.opinions_shadow || 0
  };
  const total = reports.rapporteur + reports.shadow + opinions.rapporteur + opinions.shadow;
  
  // Calculate weighted score using the same weights as the scoring system
  const weightedScore = (reports.rapporteur * 5.0) + 
                       (reports.shadow * 3.0) + 
                       (opinions.rapporteur * 2.0) + 
                       (opinions.shadow * 1.0);
  
  return {
    reports,
    opinions,
    total,
    weightedScore
  };
}

/**
 * Calculate custom weighted score for a MEP using new 4-category methodology
 */
function calculateCustomScore(mep) {
  if (currentScoringMode === 'mep-ranking') {
    return mep.final_score || mep.score || 0;
  }
  
  // Validate MEP data
  if (!mep.mep_id || !mep.full_name) {
    console.warn('Invalid MEP data:', mep);
    return 0;
  }
  
  // Use new 4-category scores from backend
  const legislativeScore = mep.legislative_production_score || 0;
  const controlScore = mep.control_transparency_score || 0;
  const engagementScore = mep.engagement_presence_score || 0;
  const baseScore = legislativeScore + controlScore + engagementScore;
  
  // Institutional roles multiplier (already includes role bonuses)
  const rolesMultiplier = mep.institutional_roles_multiplier || 1.0;
  const scoreWithRoles = baseScore * rolesMultiplier;
  
  // Store attendance penalty for later use (don't apply here)
  const attendancePenalty = mep.attendance_penalty || 1.0;
  
  // Apply custom weights (-100% to +100% range)
  // Weight of 0% = use original score, +100% = double the category, -100% = eliminate the category
  const legislativeWeight = 1 + (customWeights.legislative_production / 100);
  const controlWeight = 1 + (customWeights.control_transparency / 100);
  const engagementWeight = 1 + (customWeights.engagement_presence / 100);
  const rolesWeight = 1 + (customWeights.institutional_roles / 100);
  
  // Calculate weighted components
  const weightedLegislative = legislativeScore * legislativeWeight;
  const weightedControl = controlScore * controlWeight;
  const weightedEngagement = engagementScore * engagementWeight;
  const weightedBase = weightedLegislative + weightedControl + weightedEngagement;
  
  // Apply weighted roles multiplier
  const adjustedRolesMultiplier = Math.max(0.01, rolesMultiplier * rolesWeight); // Minimum 0.01 to avoid zero
  const scoreWithWeightedRoles = weightedBase * adjustedRolesMultiplier;
  
  // Apply attendance penalty only if enabled
  const finalAttendancePenalty = attendancePenaltyEnabled ? attendancePenalty : 1.0;
  const finalScore = scoreWithWeightedRoles * finalAttendancePenalty;
  
  // Ensure non-negative result
  return Math.max(0, finalScore);
}

/**
 * Update scoring mode and recalculate scores
 */
function updateScoringMode(mode) {
  currentScoringMode = mode;
  
  // Update toggle buttons
  document.getElementById('mep-ranking-mode').classList.toggle('active', mode === 'mep-ranking');
  document.getElementById('custom-weights-mode').classList.toggle('active', mode === 'custom-weights');
  
  // Show/hide appropriate content
  document.getElementById('mep-ranking-content').style.display = mode === 'mep-ranking' ? 'block' : 'none';
  document.getElementById('custom-weights-content').style.display = mode === 'custom-weights' ? 'block' : 'none';
  
  // Update scores in current data
  currentTermData.forEach(mep => {
    mep.score = calculateCustomScore(mep);
  });
  
  // Re-render the table
  render();
}

/**
 * Update custom weight values for new 4-category methodology
 */
function updateCustomWeights() {
  // Get values from sliders (-100 to +100 range)
  const legislativeSlider = document.getElementById('weight-legislative-production');
  const controlSlider = document.getElementById('weight-control-transparency');
  const engagementSlider = document.getElementById('weight-engagement-presence');
  const rolesSlider = document.getElementById('weight-institutional-roles');
  
  if (legislativeSlider) customWeights.legislative_production = parseInt(legislativeSlider.value || 0);
  if (controlSlider) customWeights.control_transparency = parseInt(controlSlider.value || 0);
  if (engagementSlider) customWeights.engagement_presence = parseInt(engagementSlider.value || 0);
  if (rolesSlider) customWeights.institutional_roles = parseInt(rolesSlider.value || 0);
  
  // Update display values with proper formatting
  const formatWeight = (weight) => weight >= 0 ? `+${weight}%` : `${weight}%`;
  
  const legislativeValue = document.getElementById('legislative-production-value');
  const controlValue = document.getElementById('control-transparency-value');
  const engagementValue = document.getElementById('engagement-presence-value');
  const rolesValue = document.getElementById('institutional-roles-value');
  
  if (legislativeValue) legislativeValue.textContent = formatWeight(customWeights.legislative_production);
  if (controlValue) controlValue.textContent = formatWeight(customWeights.control_transparency);
  if (engagementValue) engagementValue.textContent = formatWeight(customWeights.engagement_presence);
  if (rolesValue) rolesValue.textContent = formatWeight(customWeights.institutional_roles);
  
}

/**
 * Apply custom weights and update the table
 */
function applyCustomWeights() {
  // Show loading state on button
  const applyBtn = document.getElementById('apply-weights');
  if (applyBtn) {
    applyBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-1"></i>Applying...';
    applyBtn.disabled = true;
  }
  
  // Update weights from sliders
  updateCustomWeights();
  
  // Switch to custom weights mode
  currentScoringMode = 'custom-weights';
  
  // Recalculate scores for all MEPs
  currentTermData.forEach(mep => {
    mep.score = calculateCustomScore(mep);
  });
  
  // Re-render the table with new scores
  render();
  
  // Reset button state
  setTimeout(() => {
    if (applyBtn) {
      applyBtn.innerHTML = '<i class="fas fa-check mr-1"></i>Applied!';
      setTimeout(() => {
        applyBtn.innerHTML = '<i class="fas fa-check mr-1"></i>Apply Weights';
        applyBtn.disabled = false;
      }, 1000);
    }
  }, 100);
}

/**
 * Reset all weights to default (0%)
 */
function resetWeights() {
  // Reset sliders to 0
  const sliders = [
    'weight-legislative-production',
    'weight-control-transparency', 
    'weight-engagement-presence',
    'weight-institutional-roles'
  ];
  
  sliders.forEach(sliderId => {
    const slider = document.getElementById(sliderId);
    if (slider) slider.value = 0;
  });
  
  // Reset weights object
  customWeights = {
    legislative_production: 0,
    control_transparency: 0,
    engagement_presence: 0,
    institutional_roles: 0
  };
  
  // Reset attendance penalty
  attendancePenaltyEnabled = true;
  updateAttendancePenaltyToggle();
  
  // Update display
  updateCustomWeights();
  
  // Switch back to MEP ranking mode
  currentScoringMode = 'mep-ranking';
  
  // Reset scores to original
  currentTermData.forEach(mep => {
    mep.score = mep.final_score || mep.score || 0;
  });
  
  // Re-render
  render();
}

/**
 * Toggle attendance penalty on/off
 */
function toggleAttendancePenalty() {
  attendancePenaltyEnabled = !attendancePenaltyEnabled;
  updateAttendancePenaltyToggle();
  
  // If in custom weights mode, recalculate scores
  if (currentScoringMode === 'custom-weights') {
    currentTermData.forEach(mep => {
      mep.score = calculateCustomScore(mep);
    });
    render();
  }
}

/**
 * Update attendance penalty toggle button appearance
 */
function updateAttendancePenaltyToggle() {
  const toggle = document.getElementById('attendance-penalty-toggle');
  const status = document.getElementById('attendance-penalty-status');
  
  if (toggle && status) {
    if (attendancePenaltyEnabled) {
      toggle.innerHTML = '<i class="fas fa-toggle-on mr-2"></i>Attendance Penalty Enabled';
      toggle.className = 'w-full py-2 px-3 bg-red-100 text-red-800 text-sm rounded hover:bg-red-200 transition-colors border border-red-200';
      status.textContent = 'ON';
    } else {
      toggle.innerHTML = '<i class="fas fa-toggle-off mr-2"></i>Attendance Penalty Disabled';
      toggle.className = 'w-full py-2 px-3 bg-gray-100 text-gray-700 text-sm rounded hover:bg-gray-200 transition-colors border border-gray-200';
      status.textContent = 'OFF';
    }
  }
}

/**
 * Get abbreviated name for a political group
 */

function createTableCell(content, isHeader = false) {
  const cell = document.createElement(isHeader ? 'th' : 'td');
  
  // Add tooltip for long content
  if (typeof content === 'string' && content.length > 20) {
    cell.setAttribute('title', content);
    content = content.substring(0, 20) + '...';
  }
  
  cell.textContent = content;
  return cell;
}

/**
 * Render the table with current data and filters
 */
async function render() {
  const tableBody = document.getElementById("explorer-table-body");
  if (!tableBody) {
    console.error("Table body not found for rendering.");
    return;
  }
  console.log(`Rendering table with ${currentTermData.length} MEPs available`);
  tableBody.innerHTML = ''; // Clear existing rows

  // Ensure currentTermData is the array of MEPs
  const mepsList = Array.isArray(currentTermData) ? currentTermData : [];
  const filteredData = applyFilters(mepsList);
  const visibleColumns = Array.from(document.querySelectorAll('#activity-buttons input[type="checkbox"]:checked')).map(cb => cb.value);

  resultsCount.textContent = `Showing ${filteredData.length} of ${mepsList.length} MEPs`;

  // Update mobile results count if it exists
  const mobileResultsCount = document.getElementById("mobile-results-count");
  if (mobileResultsCount) {
    mobileResultsCount.textContent = `${filteredData.length} MEPs found`;
  }

  // Sort data
  filteredData.sort((a, b) => {
    let valA = a[currentSortColumn];
    let valB = b[currentSortColumn];

    // Special handling for score column - use calculated score based on mode
    if (currentSortColumn === 'score') {
      valA = currentScoringMode === 'custom-weights' ? calculateCustomScore(a) : (a.final_score || a.score || 0);
      valB = currentScoringMode === 'custom-weights' ? calculateCustomScore(b) : (b.final_score || b.score || 0);
    }
    
    // Special handling for combined reports/opinions score
    if (currentSortColumn === 'reports_opinions') {
        const reportsOpinionsA = getReportsOpinionsValue(a);
        const reportsOpinionsB = getReportsOpinionsValue(b);
        valA = reportsOpinionsA.weightedScore;
        valB = reportsOpinionsB.weightedScore;
    }

    if (typeof valA === 'string') valA = valA.toLowerCase();
    if (typeof valB === 'string') valB = valB.toLowerCase();

    if (valA < valB) return currentSortDirection === 'asc' ? -1 : 1;
    if (valA > valB) return currentSortDirection === 'asc' ? 1 : -1;
    return 0;
  });

  // Update header sort indicators
  updateHeaderSortIndicators();

  filteredData.forEach((mep, index) => {
    const row = document.createElement("tr");
    row.className = "border-b border-gray-200 hover:bg-gray-50 transition-colors duration-150 ease-in-out";

    // Rank
    const rankCell = createTableCell(index + 1);
    rankCell.classList.add("rank-cell", "text-center", "font-medium");
    row.appendChild(rankCell);

    // Name with Photo - Updated to link to profile.html
    const nameCell = createTableCell(''); // Content will be HTML
    nameCell.classList.add("name-cell", "font-medium");
    const photoUrl = `https://www.europarl.europa.eu/mepphoto/${mep.mep_id}.jpg`;
    const currentTermValueForLink = termSelect.value; // Get current term for the link
    nameCell.innerHTML = `
      <a href="profile.html?mep_id=${mep.mep_id}&term=${currentTermValueForLink}" class="mep-link">
        <img src="${photoUrl}" alt="Photo of ${mep.full_name}" class="mep-photo" 
             onerror="this.src='data:image/svg+xml,%3Csvg xmlns=\\'http://www.w3.org/2000/svg\\' viewBox=\\'0 0 150 150\\'%3E%3Crect width=\\'150\\' height=\\'150\\' fill=\\'%23e5e7eb\\'/%3E%3Ctext x=\\'50%25\\' y=\\'50%25\\' text-anchor=\\'middle\\' dominant-baseline=\\'middle\\' font-family=\\'Arial\\' font-size=\\'48\\' fill=\\'%239ca3af\\'%3E%3F%3C/text%3E%3C/svg%3E'">
        ${mep.full_name}
      </a>`;
    row.appendChild(nameCell);

    // Country with Flag
    const countryCell = createTableCell('');
    countryCell.classList.add("country-cell");
    countryCell.innerHTML = createCountryDisplay(mep.country, { size: 'small' });
    row.appendChild(countryCell);

    // Group
    const groupCell = createGroupCell(mep.group, index);
    row.appendChild(groupCell);

    // National Party
    const nationalPartyCell = createTableCell(mep.national_party || '');
    nationalPartyCell.classList.add("national-party-cell");
    row.appendChild(nationalPartyCell);

    // Legislative Activities
    const speechesCell = createTableCell(mep.speeches ?? 0);
    speechesCell.setAttribute("data-activity", "speeches");
    row.appendChild(speechesCell);

    const reportsOpinions = getReportsOpinionsValue(mep);
    const reportsOpinionsCell = createTableCell('');
    reportsOpinionsCell.classList.add("tooltip");
    reportsOpinionsCell.setAttribute("data-activity", "reports_opinions");
    reportsOpinionsCell.innerHTML = `
      <div class="text-center w-full">
        <span class="font-medium">${reportsOpinions.total}</span>
        <div class="text-xs text-gray-600 mt-1 breakdown-values">
          ${reportsOpinions.reports.rapporteur}+${reportsOpinions.reports.shadow}+${reportsOpinions.opinions.rapporteur}+${reportsOpinions.opinions.shadow}
        </div>
      </div>
      <div class="tooltip-content text-xs">
        <div class="font-medium mb-2">Value Breakdown:</div>
        <table class="breakdown-table">
          <tr>
            <td class="font-medium pr-2">Reports (Rapporteur):</td>
            <td class="text-right">${reportsOpinions.reports.rapporteur}</td>
            <td class="text-right text-gray-500">×5.0</td>
          </tr>
          <tr>
            <td class="font-medium pr-2">Reports (Shadow):</td>
            <td class="text-right">${reportsOpinions.reports.shadow}</td>
            <td class="text-right text-gray-500">×3.0</td>
          </tr>
          <tr>
            <td class="font-medium pr-2">Opinions (Rapporteur):</td>
            <td class="text-right">${reportsOpinions.opinions.rapporteur}</td>
            <td class="text-right text-gray-500">×2.0</td>
          </tr>
          <tr>
            <td class="font-medium pr-2">Opinions (Shadow):</td>
            <td class="text-right">${reportsOpinions.opinions.shadow}</td>
            <td class="text-right text-gray-500">×1.0</td>
          </tr>
          <tr class="border-t">
            <td class="font-medium pr-2 pt-1">Total Count:</td>
            <td class="text-right pt-1">${reportsOpinions.total}</td>
          </tr>
          <tr class="border-t">
            <td class="font-medium pr-2 pt-1">Weighted Score:</td>
            <td class="text-right pt-1 font-bold">${reportsOpinions.weightedScore.toFixed(1)}</td>
          </tr>
        </table>
      </div>
    `;
    row.appendChild(reportsOpinionsCell);

    const amendmentsCell = createTableCell(mep.amendments ?? 0);
    amendmentsCell.setAttribute("data-activity", "amendments");
    row.appendChild(amendmentsCell);

    const votesAttendedCell = createTableCell(mep.votes_attended ?? 0);
    votesAttendedCell.setAttribute("data-activity", "votes_attended");
    row.appendChild(votesAttendedCell);

    const questionsWrittenCell = createTableCell(mep.questions_written ?? 0);
    questionsWrittenCell.setAttribute("data-activity", "questions_written");
    row.appendChild(questionsWrittenCell);

    const motionsCell = createTableCell(mep.motions ?? 0);
    motionsCell.setAttribute("data-activity", "motions");
    row.appendChild(motionsCell);

    const explanationsCell = createTableCell(mep.explanations ?? 0);
    explanationsCell.setAttribute("data-activity", "explanations");
    row.appendChild(explanationsCell);

    const questionsOralCell = createTableCell(mep.questions_oral ?? 0);
    questionsOralCell.setAttribute("data-activity", "questions_oral");
    row.appendChild(questionsOralCell);

    // Committee Roles
    const committeeChairCell = createTableCell(mep.committee_chair ?? 0);
    committeeChairCell.setAttribute("data-activity", "committee_chair");
    row.appendChild(committeeChairCell);

    const committeeViceChairCell = createTableCell(mep.committee_vice_chair ?? 0);
    committeeViceChairCell.setAttribute("data-activity", "committee_vice_chair");
    row.appendChild(committeeViceChairCell);

    const committeeMemberCell = createTableCell(mep.committee_member ?? 0);
    committeeMemberCell.setAttribute("data-activity", "committee_member");
    row.appendChild(committeeMemberCell);

    const committeeSubstituteCell = createTableCell(mep.committee_substitute ?? 0);
    committeeSubstituteCell.setAttribute("data-activity", "committee_substitute");
    row.appendChild(committeeSubstituteCell);

    // Delegation Roles
    const delegationChairCell = createTableCell(mep.delegation_chair ?? 0);
    delegationChairCell.setAttribute("data-activity", "delegation_chair");
    row.appendChild(delegationChairCell);

    const delegationViceChairCell = createTableCell(mep.delegation_vice_chair ?? 0);
    delegationViceChairCell.setAttribute("data-activity", "delegation_vice_chair");
    row.appendChild(delegationViceChairCell);

    const delegationMemberCell = createTableCell(mep.delegation_member ?? 0);
    delegationMemberCell.setAttribute("data-activity", "delegation_member");
    row.appendChild(delegationMemberCell);

    const delegationSubstituteCell = createTableCell(mep.delegation_substitute ?? 0);
    delegationSubstituteCell.setAttribute("data-activity", "delegation_substitute");
    row.appendChild(delegationSubstituteCell);

    // EP Leadership
    const epPresidentCell = createTableCell(mep.ep_president ?? 0);
    epPresidentCell.setAttribute("data-activity", "ep_president");
    row.appendChild(epPresidentCell);

    const epVicePresidentCell = createTableCell(mep.ep_vice_president ?? 0);
    epVicePresidentCell.setAttribute("data-activity", "ep_vice_president");
    row.appendChild(epVicePresidentCell);

    const epQuaestorCell = createTableCell(mep.ep_quaestor ?? 0);
    epQuaestorCell.setAttribute("data-activity", "ep_quaestor");
    row.appendChild(epQuaestorCell);

    // Score (clickable) - use calculated score based on current mode
    const scoreCell = createTableCell('');
    scoreCell.classList.add("font-semibold");
    scoreCell.setAttribute("data-column-id", "score"); // Essential for sticky positioning CSS
    const displayScore = currentScoringMode === 'custom-weights' ? calculateCustomScore(mep) : (mep.final_score || mep.score || 0);
    
    // Debug logging for Victor NEGRESCU on index page
    if (mep.mep_id === 88882) {
    }
    
    scoreCell.innerHTML = `<span class="clickable-score" data-mep-id="${mep.mep_id}">${displayScore.toFixed(1)}</span>`;
    row.appendChild(scoreCell);

    tableBody.appendChild(row);
  });

  // Update scroll content width (if applicable)
  if (typeof updateScrollContentWidth === 'function') {
    updateScrollContentWidth();
  }

  // Ensure columns visibility is updated after rendering
  updateVisibleColumns();
  
  // Add click event listeners to score cells - use unified score breakdown
  document.querySelectorAll('.clickable-score').forEach(scoreElement => {
    scoreElement.addEventListener('click', (e) => {
      e.preventDefault();
      const mepId = parseInt(e.target.dataset.mepId);
      const mep = currentTermData.find(m => m.mep_id === mepId);
      if (mep) {
        showScoreBreakdown(mep, currentTermData);
      }
    });
  });

  // Render mobile cards if the function exists
  if (typeof window.renderMobileCards === 'function') {
    const processedData = filteredData.map(mep => ({
      ...mep,
      final_score: currentScoringMode === 'custom-weights' ? calculateCustomScore(mep) : (mep.final_score || mep.score || 0)
    }));
    // Store data globally for sorting functionality
    window.currentMEPData = processedData;
    window.renderMobileCards(processedData);
  } else {
    // Fallback: ensure mobile rendering is initialized
    console.warn('Mobile rendering not ready, attempting to initialize...');
    setTimeout(() => {
      if (typeof window.renderMobileCards === 'function') {
        const processedData = filteredData.map(mep => ({
          ...mep,
          final_score: currentScoringMode === 'custom-weights' ? calculateCustomScore(mep) : (mep.final_score || mep.score || 0)
        }));
        window.currentMEPData = processedData;
        window.renderMobileCards(processedData);
      } else {
        console.error('Mobile rendering failed to initialize');
        // Show error message on mobile with retry option
        const mobileContainer = document.getElementById('mobile-mep-cards');
        if (mobileContainer) {
          mobileContainer.innerHTML = `
            <div class="text-center p-4 text-gray-500">
              <i class="fas fa-exclamation-triangle text-2xl mb-2 text-orange-500"></i>
              <p class="mb-3">Unable to load MEP data for mobile view.</p>
              <button onclick="window.location.reload()" class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">
                <i class="fas fa-refresh mr-2"></i>Refresh Page
              </button>
            </div>
          `;
        }
      }
    }, 500);
  }
}

/**
 * Initialize activity pill click handlers
 */
function initializeActivityPills() {
  document.querySelectorAll('.activity-pill').forEach(pill => {
    pill.addEventListener('click', () => {
      pill.classList.toggle('selected');
      updateVisibleColumns();
    });
  });
}

/**
 * Initialize header sorting
 */
function initializeHeaderSorting() {
  // Ensure the table head is selected correctly. If it's not explorer-table-head, adjust the selector.
  // The <thead> tag in index.html should have id="explorer-table-head"
  const tableHeaders = document.querySelectorAll('#explorer-table-head th[data-column-id]');
  tableHeaders.forEach(th => {
    const columnId = th.dataset.columnId;
    if (columnId) {
      th.style.cursor = 'pointer';
      // Remove existing listener to prevent multiple attachments if this function is called multiple times
      // A more robust way would be to use a marker or check if listener already exists.
      // For simplicity, we'll rely on this being called once or ensure th is freshly queried.
      // Or, manage listeners more carefully (e.g. th.replaceWith(th.cloneNode(true)) before adding new one)
      
      th.addEventListener('click', () => {
        if (currentSortColumn === columnId) {
          currentSortDirection = currentSortDirection === 'asc' ? 'desc' : 'asc';
        } else {
          currentSortColumn = columnId;
          // Default to descending for numeric/activity columns, ascending for text like name
          if (['full_name', 'country', 'group', 'national_party'].includes(columnId)) {
            currentSortDirection = 'asc';
          } else {
            currentSortDirection = 'desc';
          }
        }
        render();
      });
    }
  });
}

function updateHeaderSortIndicators() {
  const tableHeaders = document.querySelectorAll('#explorer-table-head th[data-column-id]');
  tableHeaders.forEach(th => {
    // Clear previous indicators by removing child nodes that are text nodes and match the pattern
    Array.from(th.childNodes).forEach(child => {
        if (child.nodeType === Node.TEXT_NODE && child.textContent.match(/ [▲▼]/)) {
            th.removeChild(child);
        }
    });
    // Or a simpler way to reset if header content is just text:
    // th.textContent = th.textContent.replace(/ [▲▼]$/, ''); // More careful if HTML is inside TH

    if (th.dataset.columnId === currentSortColumn) {
      // Add indicator as a new text node to avoid messing with existing HTML inside TH (if any)
      const indicator = document.createTextNode(currentSortDirection === 'asc' ? ' ▲' : ' ▼');
      th.appendChild(indicator);
    }
  });
}

// Event listeners
termSelect.onchange = async () => {
  currentTermData = []; // Clear cached data
  await updateFilterOptions(true);
  render();
};

countryFilter.onchange = async () => {
  await updateFilterOptions();
  render();
};

groupFilter.onchange = () => {
  updateActiveFilters();
  render();
};

partyFilter.onchange = () => {
  updateActiveFilters();
  render();
};

generalSearch.oninput = () => {
  updateActiveFilters();
  render();
};

resetFiltersBtn.addEventListener('click', resetFilters);
selectAllActivitiesBtn.addEventListener('click', selectAllActivities);
clearAllActivitiesBtn.addEventListener('click', clearAllActivities);

/**
 * Initialize scoring mode controls for new 4-category methodology
 */
function initializeScoringModeControls() {
  // Weight sliders for new 4-category system (-100% to +100%)
  const sliders = [
    'weight-legislative-production',
    'weight-control-transparency', 
    'weight-engagement-presence',
    'weight-institutional-roles'
  ];
  
  sliders.forEach(sliderId => {
    const slider = document.getElementById(sliderId);
    if (slider) {
      slider.addEventListener('input', updateCustomWeights);
    }
  });
  
  // Apply weights button
  const applyBtn = document.getElementById('apply-weights');
  if (applyBtn) {
    applyBtn.addEventListener('click', applyCustomWeights);
  }
  
  // Reset weights button
  const resetBtn = document.getElementById('reset-weights');
  if (resetBtn) {
    resetBtn.addEventListener('click', resetWeights);
  }
  
  // Attendance penalty toggle
  const attendanceToggle = document.getElementById('attendance-penalty-toggle');
  if (attendanceToggle) {
    attendanceToggle.addEventListener('click', toggleAttendancePenalty);
  }
  
  // Initialize display
  updateCustomWeights();
  updateAttendancePenaltyToggle();
}

// Initial setup
document.addEventListener('DOMContentLoaded', () => {
  initializeActivityPills();
  
  // Delay the scoring controls initialization to ensure DOM is fully ready
  setTimeout(() => {
    initializeScoringModeControls();
  }, 100);
  
  initializeScoreBreakdownModal(); // Initialize unified score breakdown modal
  
  // Wait for mobile functions to be ready before initial data load
  const initializeData = () => {
    console.log('Initializing MEP Explorer data...');
    updateFilterOptions().then(() => {
      console.log('Filter options updated, starting initial render...');
      render(); // Initial render
      initializeHeaderSorting(); // Setup sorting after initial render
    }).catch(error => {
      console.error('Failed to initialize data:', error);
    });
  };
  
  // Check if mobile functions are ready (for mobile compatibility)
  if (window.innerWidth < 1024) {
    // On mobile, wait for mobile functions to be ready
    let attempts = 0;
    const waitForMobile = () => {
      if (typeof window.renderMobileCards === 'function' || attempts > 10) {
        initializeData();
      } else {
        attempts++;
        setTimeout(waitForMobile, 100);
      }
    };
    waitForMobile();
  } else {
    // On desktop, initialize immediately
    initializeData();
  }
  
  setupCustomSlider();
  setupScrollSynchronization();
});

// Synchronize top and bottom scrollbars
function setupScrollSynchronization() {
  const tableContainer = document.querySelector('.table-container');
  const scrollControls = document.querySelector('.scroll-controls');
  const scrollContentWidth = document.querySelector('.scroll-content-width');
  
  // Set the width of the scroll content to match the table width
  function updateScrollContentWidth() {
    if (tableContainer && scrollContentWidth) {
      const tableWidth = tableContainer.querySelector('table').offsetWidth;
      scrollContentWidth.style.width = `${tableWidth}px`;
    }
  }
  
  // Synchronize scrolling between the top and bottom scrollbars
  if (tableContainer && scrollControls) {
    // Sync scroll position when top scrollbar is used
    scrollControls.addEventListener('scroll', () => {
      tableContainer.scrollLeft = scrollControls.scrollLeft;
    });
    
    // Sync scroll position when table container is scrolled
    tableContainer.addEventListener('scroll', () => {
      scrollControls.scrollLeft = tableContainer.scrollLeft;
    });
    
    // Update scroll content width after rendering
    const observer = new MutationObserver(() => {
      updateScrollContentWidth();
    });
    
    observer.observe(tableContainer, { childList: true, subtree: true });
  }
  
  // Initial width update
  updateScrollContentWidth();
  
  // Update width when window is resized
  window.addEventListener('resize', updateScrollContentWidth);
}

/**
 * Fix and improve the slider functionality
 */
function setupCustomSlider() {
  const tableContainer = document.querySelector('.table-container');
  const scrollThumb = document.getElementById('table-scroll-thumb');
  const scrollTrack = document.querySelector('.scroll-track');
  
  if (!tableContainer || !scrollThumb || !scrollTrack) return;
  
  let isDragging = false;
  let startX, startScrollLeft, maxScrollLeft;
  
  function updateSlider() {
    const table = tableContainer.querySelector('table');
    if (!table) return;
    
    const containerWidth = tableContainer.clientWidth;
    const tableWidth = table.offsetWidth;
    
    // Only show the thumb if table is wider than container
    if (tableWidth <= containerWidth) {
      scrollTrack.style.display = 'none';
      return;
    }
    
    scrollTrack.style.display = 'block';
    maxScrollLeft = tableWidth - containerWidth;
    
    // Calculate thumb width based on visible portion ratio
    const thumbWidthPercentage = (containerWidth / tableWidth) * 100;
    const thumbWidth = Math.max(40, (scrollTrack.clientWidth * thumbWidthPercentage) / 100);
    scrollThumb.style.width = `${thumbWidth}px`;
    
    // Update thumb position based on current scroll
    const scrollRatio = tableContainer.scrollLeft / maxScrollLeft;
    const maxThumbPosition = scrollTrack.clientWidth - thumbWidth;
    const thumbPosition = Math.min(maxThumbPosition, scrollRatio * maxThumbPosition);
    
    scrollThumb.style.transform = `translateX(${thumbPosition}px)`;
  }
  
  // Move the thumb when scrolling the table
  tableContainer.addEventListener('scroll', () => {
    if (!isDragging) {
      updateSlider();
    }
  });
  
  // Handle mousedown on the thumb
  scrollThumb.addEventListener('mousedown', (e) => {
    e.preventDefault();
    isDragging = true;
    startX = e.pageX - scrollThumb.offsetLeft;
    startScrollLeft = tableContainer.scrollLeft;
    scrollThumb.style.cursor = 'grabbing';
    document.body.style.userSelect = 'none';
  });
  
  // Handle mousemove for dragging
  document.addEventListener('mousemove', (e) => {
    if (!isDragging) return;
    e.preventDefault();
    
    const x = e.pageX - scrollTrack.getBoundingClientRect().left;
    const thumbWidth = scrollThumb.offsetWidth;
    const trackWidth = scrollTrack.clientWidth;
    const maxThumbPosition = trackWidth - thumbWidth;
    
    // Calculate new thumb position
    let newThumbPosition = x - startX;
    newThumbPosition = Math.max(0, Math.min(maxThumbPosition, newThumbPosition));
    
    // Update thumb position
    scrollThumb.style.transform = `translateX(${newThumbPosition}px)`;
    
    // Calculate and update table scroll position
    const scrollRatio = newThumbPosition / maxThumbPosition;
    tableContainer.scrollLeft = scrollRatio * maxScrollLeft;
  });
  
  // Handle mouseup to stop dragging
  document.addEventListener('mouseup', () => {
    if (!isDragging) return;
    isDragging = false;
    scrollThumb.style.cursor = 'grab';
    document.body.style.userSelect = '';
  });
  
  // Handle click on the track to jump to that position
  scrollTrack.addEventListener('click', (e) => {
    if (e.target === scrollThumb) return;
    
    const trackRect = scrollTrack.getBoundingClientRect();
    const thumbWidth = scrollThumb.offsetWidth;
    const clickPosition = e.clientX - trackRect.left;
    const trackWidth = trackRect.width;
    
    // Calculate the new thumb position
    let newThumbPosition = clickPosition - (thumbWidth / 2);
    newThumbPosition = Math.max(0, Math.min(trackWidth - thumbWidth, newThumbPosition));
    
    // Update thumb position
    scrollThumb.style.transform = `translateX(${newThumbPosition}px)`;
    
    // Calculate and update table scroll position
    const scrollRatio = newThumbPosition / (trackWidth - thumbWidth);
    const newScrollPosition = scrollRatio * maxScrollLeft;
    
    tableContainer.scrollTo({
      left: newScrollPosition,
      behavior: 'smooth'
    });
  });
  
  // Update on window resize
  window.addEventListener('resize', updateSlider);
  
  // Initialize the slider
  updateSlider();
  
  // Add keyboard navigation
  scrollThumb.setAttribute('tabindex', '0');
  scrollThumb.addEventListener('keydown', (e) => {
    const STEP = 100;
    
    switch(e.key) {
      case 'ArrowLeft':
      case 'Left':
        e.preventDefault();
        tableContainer.scrollLeft = Math.max(0, tableContainer.scrollLeft - STEP);
        break;
      case 'ArrowRight':
      case 'Right':
        e.preventDefault();
        tableContainer.scrollLeft = Math.min(maxScrollLeft, tableContainer.scrollLeft + STEP);
        break;
    }
  });
}

// Score breakdown modal functionality now handled by unified score-breakdown.js module
// Functions are imported at the top of this file

// Score breakdown HTML generation moved to score-breakdown.js module
// This function is now deprecated and will use the unified module

// Score modal initialization now handled by unified score-breakdown.js module

// Initialize category modal event listeners
function initializeCategoryModal() {
  const modal = document.getElementById('category-modal');
  const openBtn = document.getElementById('weights-info-btn');
  const closeBtn = document.getElementById('category-modal-close');
  
  // Open modal when clicking info button
  openBtn.addEventListener('click', () => {
    modal.classList.add('active');
  });
  
  // Close modal when clicking close button
  closeBtn.addEventListener('click', () => {
    modal.classList.remove('active');
  });
  
  // Close modal when clicking outside content
  modal.addEventListener('click', (e) => {
    if (e.target === modal) {
      modal.classList.remove('active');
    }
  });
  
  // Close modal with Escape key
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && modal.classList.contains('active')) {
      modal.classList.remove('active');
    }
  });
}

// Removed duplicate DOMContentLoaded listener - consolidated above

// Add event listener for term changes
termSelect.addEventListener('change', async () => {
  const selectedTerm = termSelect.value;
  
  // Update URL with new term parameter
  const url = new URL(window.location);
  if (selectedTerm === '10') {
    // Remove term parameter for default (10th term)
    url.searchParams.delete('term');
  } else {
    url.searchParams.set('term', selectedTerm);
  }
  window.history.replaceState({}, '', url);
  
  // Reload data for new term
  await updateFilterOptions(true);
  render();
});

// Initial setup
(async () => {
  // Check for term parameter in URL and update selector
  const urlParams = new URLSearchParams(window.location.search);
  const termParam = urlParams.get('term');
  if (termParam && ['8', '9', '10'].includes(termParam)) {
    termSelect.value = termParam;
  }
  
  await updateFilterOptions(true);
  render();
  // Setup slider after render completes
  setTimeout(() => {
    setupCustomSlider();
  }, 100);
})(); 