import { loadTermDataset, createGroupDisplay, createCountryDisplay } from "./utilities.js";

// State
let currentData = [];
let currentSort = { column: 'rank', direction: 'asc' };
let currentFilter = 'all';
let searchTerm = '';

// DOM Elements
const termSelect = document.getElementById("term-select");
const tbody = document.getElementById("mep-table-body");
const searchInput = document.getElementById("search");
const filterSelect = document.getElementById("filter");
const loadingEl = document.getElementById("loading");
const errorEl = document.getElementById("error");
const errorMessage = document.getElementById("error-message");
const showingCount = document.getElementById("showing-count");
const downloadBtn = document.getElementById("download-csv");
const modal = document.getElementById("mep-modal");
const modalContent = document.getElementById("mep-modal-content");

// Utility Functions
function showLoading() {
    loadingEl.classList.remove('hidden');
    tbody.classList.add('opacity-50');
}

function hideLoading() {
    loadingEl.classList.add('hidden');
    tbody.classList.remove('opacity-50');
}

function showError(message) {
    errorMessage.textContent = message;
    errorEl.classList.remove('hidden');
}

function hideError() {
    errorEl.classList.add('hidden');
}

function formatNumber(num) {
    return new Intl.NumberFormat().format(num);
}

// Data Processing Functions
function filterData(data) {
    let filtered = [...data];
    
    // Apply search
    if (searchTerm) {
        const term = searchTerm.toLowerCase();
        filtered = filtered.filter(row => 
            row.full_name.toLowerCase().includes(term) ||
            row.country.toLowerCase().includes(term) ||
            row.group.toLowerCase().includes(term)
        );
    }
    
    // Apply filters
    switch (currentFilter) {
        case 'top100':
            filtered = filtered.slice(0, 100);
            break;
        case 'active':
            filtered.sort((a, b) => b.score - a.score);
            filtered = filtered.slice(0, 50);
            break;
        case 'speeches':
            filtered.sort((a, b) => b.speeches - a.speeches);
            filtered = filtered.slice(0, 50);
            break;
        case 'amendments':
            filtered.sort((a, b) => b.amendments - a.amendments);
            filtered = filtered.slice(0, 50);
            break;
    }
    
    return filtered;
}

function sortData(data) {
    const sorted = [...data];
    const { column, direction } = currentSort;
    
    sorted.sort((a, b) => {
        let comparison = 0;
        
        // Handle numeric vs string comparisons
        if (typeof a[column] === 'number') {
            comparison = a[column] - b[column];
        } else {
            comparison = String(a[column]).localeCompare(String(b[column]));
        }
        
        return direction === 'asc' ? comparison : -comparison;
    });
    
    return sorted;
}


// Rendering Functions
function renderTableRow(row) {
    const tr = document.createElement("tr");
    tr.className = "hover:bg-gray-50 cursor-pointer";
    tr.onclick = () => showMepDetails(row);
    
    tr.innerHTML = `
        <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${row.rank}</td>
        <td class="px-6 py-4 whitespace-nowrap">
            <div class="text-sm font-medium text-gray-900">${row.full_name}</div>
        </td>
        <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
            ${createCountryDisplay(row.country, { size: 'small', showCode: true })}
        </td>
        <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
            ${createGroupDisplay(row.group, { size: 'small' })}
        </td>
        <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${formatNumber(row.speeches || 0)}</td>
        <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${formatNumber(row.reports_rapporteur || 0)}</td>
        <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${formatNumber(row.amendments || 0)}</td>
        <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">${row.score.toFixed(2)}</td>
    `;
    
    return tr;
}

function renderTable(data) {
    tbody.innerHTML = "";
    const fragment = document.createDocumentFragment();
    
    data.forEach(row => {
        fragment.appendChild(renderTableRow(row));
    });
    
    tbody.appendChild(fragment);
    showingCount.textContent = data.length;
}

function showMepDetails(mep) {
    modalContent.innerHTML = `
        <div class="sm:flex sm:items-start">
            <div class="mt-3 text-center sm:mt-0 sm:text-left w-full">
                <h3 class="text-lg leading-6 font-medium text-gray-900 mb-4">
                    ${mep.full_name}
                </h3>
                <div class="grid grid-cols-2 gap-4">
                    <div>
                        <p class="text-sm text-gray-500">Country</p>
                        <div class="text-sm font-medium text-gray-900">${createCountryDisplay(mep.country, { size: 'small', showText: true })}</div>
                    </div>
                    <div>
                        <p class="text-sm text-gray-500">Political Group</p>
                        <div class="text-sm font-medium text-gray-900">${createGroupDisplay(mep.group, { size: 'small' })}</div>
                    </div>
                    <div>
                        <p class="text-sm text-gray-500">Rank</p>
                        <p class="text-sm font-medium text-gray-900">#${mep.rank}</p>
                    </div>
                    <div>
                        <p class="text-sm text-gray-500">Score</p>
                        <p class="text-sm font-medium text-gray-900">${mep.score.toFixed(2)}</p>
                    </div>
                </div>
                <div class="mt-4">
                    <h4 class="text-sm font-medium text-gray-900 mb-2">Activity Breakdown</h4>
                    <div class="bg-gray-50 rounded-lg p-4">
                        <div class="grid grid-cols-2 gap-4">
                            <div>
                                <p class="text-sm text-gray-500">Speeches</p>
                                <p class="text-sm font-medium text-gray-900">${formatNumber(mep.speeches || 0)}</p>
                            </div>
                            <div>
                                <p class="text-sm text-gray-500">Reports</p>
                                <p class="text-sm font-medium text-gray-900">${formatNumber(mep.reports_rapporteur || 0)}</p>
                            </div>
                            <div>
                                <p class="text-sm text-gray-500">Amendments</p>
                                <p class="text-sm font-medium text-gray-900">${formatNumber(mep.amendments || 0)}</p>
                            </div>
                            <div>
                                <p class="text-sm text-gray-500">Written Questions</p>
                                <p class="text-sm font-medium text-gray-900">${formatNumber(mep.questions_written || 0)}</p>
                            </div>
                            <div>
                                <p class="text-sm text-gray-500">Oral Questions</p>
                                <p class="text-sm font-medium text-gray-900">${formatNumber(mep.questions_oral || 0)}</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
    modal.classList.remove('hidden');
}

// Event Handlers
async function loadData(term) {
    showLoading();
    hideError();
    
    try {
        const termData = await loadTermDataset(term);
        
        // Handle new data structure (object with meps array)
        if (Array.isArray(termData)) {
            currentData = termData; // Old format
        } else {
            currentData = termData.meps; // New format
        }
        updateTable();
    } catch (error) {
        console.error('Error loading data:', error);
        showError('Failed to load MEP data. Please try again later.');
    } finally {
        hideLoading();
    }
}

function updateTable() {
    const filtered = filterData(currentData);
    const sorted = sortData(filtered);
    renderTable(sorted);
}

function handleSort(column) {
    if (currentSort.column === column) {
        currentSort.direction = currentSort.direction === 'asc' ? 'desc' : 'asc';
    } else {
        currentSort = { column, direction: 'asc' };
    }
    
    // Update sort icons
    document.querySelectorAll('[data-sort]').forEach(th => {
        const icon = th.querySelector('i');
        if (th.dataset.sort === column) {
            icon.className = `fas fa-sort-${currentSort.direction === 'asc' ? 'up' : 'down'}`;
        } else {
            icon.className = 'fas fa-sort';
        }
    });
    
    updateTable();
}

function downloadCsv() {
    const filtered = filterData(currentData);
    const sorted = sortData(filtered);
    
    const headers = ['Rank', 'Name', 'Country', 'Party', 'Speeches', 'Reports', 'Amendments', 'Score'];
    const rows = sorted.map(row => [
        row.rank,
        row.full_name,
        row.country,
        row.group,
        row.speeches || 0,
        row.reports_rapporteur || 0,
        row.amendments || 0,
        row.score.toFixed(2)
    ]);
    
    const csvContent = [
        headers.join(','),
        ...rows.map(row => row.join(','))
    ].join('\n');
    
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `mep_rankings_term${termSelect.value}.csv`;
    link.click();
}

// Event Listeners
termSelect.addEventListener('change', () => loadData(parseInt(termSelect.value, 10)));
searchInput.addEventListener('input', (e) => {
    searchTerm = e.target.value;
    updateTable();
});
filterSelect.addEventListener('change', (e) => {
    currentFilter = e.target.value;
    updateTable();
});
downloadBtn.addEventListener('click', downloadCsv);

// Sort handlers
document.querySelectorAll('[data-sort]').forEach(th => {
    th.addEventListener('click', () => handleSort(th.dataset.sort));
});

// Close modal when clicking outside
modal.addEventListener('click', (e) => {
    if (e.target === modal) {
        modal.classList.add('hidden');
    }
});

// Initial load
loadData(parseInt(termSelect.value, 10)); 