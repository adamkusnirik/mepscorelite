import { loadTermDataset, createGroupDisplay, createCountryDisplay } from './utilities.js'; // Assuming utilities.js has a suitable loader
import { showScoreBreakdown, hideScoreBreakdown, initializeScoreBreakdownModal } from './score-breakdown.js';

// Profile page now uses MEP Ranking scores from the dataset
// for consistency with the index page

// Get URL parameters
const urlParams = new URLSearchParams(window.location.search);
const mepId = parseInt(urlParams.get('mep_id'));
const term = parseInt(urlParams.get('term')) || 10;

// Update navigation links to preserve the term parameter
const updateNavigationLinks = () => {
    const backLink = document.getElementById('back-to-rankings-link');
    if (backLink && term !== 10) {
        backLink.href = `/?term=${term}`;
    }
    
    // Update breadcrumb home link
    const breadcrumbLinks = document.querySelectorAll('a[href="index.html"]');
    breadcrumbLinks.forEach(link => {
        if (term !== 10) {
            link.href = `/?term=${term}`;
        }
    });
    
    // Update any other ranking links
    const rankingLinks = document.querySelectorAll('a[href="index.html"]');
    rankingLinks.forEach(link => {
        if (term !== 10) {
            link.href = `/?term=${term}`;
        }
    });
};

// Initialize navigation links
updateNavigationLinks();

// DOM elements
const loadingEl = document.getElementById('loading-state');
const errorEl = document.getElementById('error-state');
const errorMessageEl = document.getElementById('error-message');
const profileContentEl = document.getElementById('profile-content');

async function loadMEPProfile() {
    try {
        if (!mepId || isNaN(mepId)) {
            throw new Error('MEP ID is required. Please access this page from the MEP rankings list or use a URL like: profile.html?mep_id=88882&term=10');
        }

        loadingEl.style.display = 'block';
        errorEl.style.display = 'none';
        profileContentEl.style.display = 'none';

        // Load term dataset with fallback
        let termData;
        try {
            termData = await loadTermDataset(term);
        } catch (error) {
            console.warn(`Term ${term} dataset not found, trying term 10 as fallback`);
            try {
                termData = await loadTermDataset(10);
            } catch (fallbackError) {
                throw new Error(`Could not load data for term ${term} or fallback term 10. Available terms: 8, 9, 10`);
            }
        }
        
        // Handle both data formats
        const meps = Array.isArray(termData) ? termData : termData.meps;
        const averages = Array.isArray(termData) ? {} : termData.averages;

        if (!meps || !Array.isArray(meps)) {
            throw new Error(`Could not load MEP data. Available terms: 8, 9, 10`);
        }

        
        // Use MEP Ranking scores from the dataset (already calculated by build_term_dataset.py)
        // This ensures consistency with the index page scoring
        const scoredMeps = meps.map(mep => ({
            ...mep,
            // Use MEP Ranking final_score as the main score for consistency with index page
            score: mep.final_score || mep.score || 0
        }));
        
        // Find the MEP
        const mep = scoredMeps.find(m => m.mep_id === mepId);
        
        if (!mep) {
            throw new Error(`MEP with ID ${mepId} not found in term ${term} data`);
        }

        // Populate profile
        populateProfile(mep, averages, scoredMeps);

        // Show content
        loadingEl.style.display = 'none';
        profileContentEl.style.display = 'block';

    } catch (error) {
        console.error('Error loading MEP profile:', error);
        loadingEl.style.display = 'none';
        errorEl.style.display = 'block';
        errorMessageEl.textContent = error.message;
    }
}

function populateProfile(mep, averages, allMeps) {
    // Basic info
    document.getElementById('mep-name').textContent = mep.full_name || 'Unknown MEP';
    
    // Build subheader and national party
    const country = mep.country || 'Unknown';
    const group = mep.group || 'Unknown';
    const nationalParty = mep.national_party || 'Unknown';
    const countryDisplay = createCountryDisplay(country, { size: 'medium', showText: true });
    const groupDisplay = createGroupDisplay(group, { size: 'medium', showText: true });
    
    document.getElementById('mep-subheader').innerHTML = `${countryDisplay} | ${groupDisplay}`;
    document.getElementById('mep-national-party').textContent = nationalParty;

    // Ranking and score - calculate rank based on scored data
    const sortedMeps = [...allMeps].sort((a, b) => (b.score || 0) - (a.score || 0));
    const rank = sortedMeps.findIndex(m => m.mep_id === mep.mep_id) + 1;
    const score = mep.score || 0;  // This is now the final_score from MEP Ranking system
    document.getElementById('overall-rank').textContent = `Rank ${rank} | Score: ${score.toFixed(1)}`;

    // Show score breakdown button
    const scoreBreakdownBtn = document.getElementById('score-breakdown-btn');
    scoreBreakdownBtn.style.display = 'inline-block';
    scoreBreakdownBtn.onclick = () => showScoreBreakdown(mep);

    // Activity level indicator based on ranking thirds
    const activityLevel = getActivityLevel(mep, averages, allMeps);
    const activityIndicator = document.getElementById('activity-level');
    activityIndicator.className = `performance-indicator ${activityLevel.class}`;

    // Photo - generate URL based on MEP ID
    const photoUrl = mep.photo_url || mep.photo || `https://www.europarl.europa.eu/mepphoto/${mep.mep_id}.jpg`;
    const photoElement = document.getElementById('mep-photo');
    photoElement.src = photoUrl;
    
    // Add error handling for missing photos
    photoElement.onerror = function() {
        this.src = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 150 150'%3E%3Crect width='150' height='150' fill='%23e5e7eb'/%3E%3Ctext x='50%25' y='50%25' text-anchor='middle' dominant-baseline='middle' font-family='Arial' font-size='48' fill='%239ca3af'%3E%3F%3C/text%3E%3C/svg%3E";
    };

    // Performance summary section removed

    // Populate activity statistics
    populateActivityStats(mep, averages, allMeps);

    // Score breakdown is now available via modal button

    // Populate roles
    populateRoles(mep);
}

function getActivityLevel(mep, averages, allMeps) {
    // Calculate rank based on score to determine performance level
    const sortedMeps = [...allMeps].sort((a, b) => (b.score || 0) - (a.score || 0));
    const rank = sortedMeps.findIndex(m => m.mep_id === mep.mep_id) + 1;
    const totalMeps = allMeps.length;
    
    // Determine performance level based on ranking thirds
    const percentile = ((totalMeps - rank + 1) / totalMeps) * 100;
    
    if (percentile > 66.67) {
        // Top third - Green
        return { class: 'performance-high' };
    } else if (percentile > 33.33) {
        // Middle third - Yellow 
        return { class: 'performance-medium' };
    } else {
        // Bottom third - Red
        return { class: 'performance-low' };
    }
}

function calculateGroupRank(mep, allMeps) {
    const groupMeps = allMeps.filter(m => m.group === mep.group);
    if (groupMeps.length === 0) return { rank: 1, total: 1 };
    
    // Sort by score descending
    groupMeps.sort((a, b) => (b.score || 0) - (a.score || 0));
    
    const rank = groupMeps.findIndex(m => m.mep_id === mep.mep_id) + 1;
    return { rank, total: groupMeps.length };
}

function calculateNationalPartyRank(mep, allMeps) {
    const partyMeps = allMeps.filter(m => m.national_party === mep.national_party);
    if (partyMeps.length === 0) return { rank: 1, total: 1 };
    
    // Sort by score descending
    partyMeps.sort((a, b) => (b.score || 0) - (a.score || 0));
    
    const rank = partyMeps.findIndex(m => m.mep_id === mep.mep_id) + 1;
    return { rank, total: partyMeps.length };
}

function calculateCountryRank(mep, allMeps) {
    const countryMeps = allMeps.filter(m => m.country === mep.country);
    if (countryMeps.length === 0) return { rank: 1, total: 1 };
    
    // Sort by score descending
    countryMeps.sort((a, b) => (b.score || 0) - (a.score || 0));
    
    const rank = countryMeps.findIndex(m => m.mep_id === mep.mep_id) + 1;
    return { rank, total: countryMeps.length };
}

function generatePerformanceAnalysis(mep, allMeps, overallRank, groupRank, nationalPartyRank, countryRank) {
    try {
        const totalMeps = allMeps.length;
        const overallPercentile = Math.round(((totalMeps - overallRank + 1) / totalMeps) * 100);
        
        // Calculate strengths and weaknesses
        const strengths = [];
        const weaknesses = [];
        
        // Analyze activities
        const activities = {
            'Speeches': mep.speeches || 0,
            'Amendments': mep.amendments || 0,
            'Reports (Rapporteur)': mep.reports_rapporteur || 0,
            'Reports (Shadow)': mep.reports_shadow || 0,
            'Questions': mep.questions || 0,
            'Motions': mep.motions || 0,
            'Opinions (Rapporteur)': mep.opinions_rapporteur || 0,
            'Opinions (Shadow)': mep.opinions_shadow || 0,
            'Explanations': mep.explanations || 0
        };
        
        // Calculate averages for comparison
        const epAverages = {};
        Object.keys(activities).forEach(key => {
            let field;
            switch(key) {
                case 'Speeches': field = 'speeches'; break;
                case 'Amendments': field = 'amendments'; break;
                case 'Reports (Rapporteur)': field = 'reports_rapporteur'; break;
                case 'Reports (Shadow)': field = 'reports_shadow'; break;
                case 'Questions': field = 'questions'; break;
                case 'Motions': field = 'motions'; break;
                case 'Opinions (Rapporteur)': field = 'opinions_rapporteur'; break;
                case 'Opinions (Shadow)': field = 'opinions_shadow'; break;
                case 'Explanations': field = 'explanations'; break;
                default: field = key.toLowerCase().replace(/[^a-z]/g, '_').replace(/_+/g, '_');
            }
            const values = allMeps.map(m => m[field] || 0).filter(v => v > 0);
            epAverages[key] = values.length > 0 ? values.reduce((a, b) => a + b, 0) / values.length : 0;
        });
        
        // Identify strengths (above 150% of average)
        Object.entries(activities).forEach(([activity, count]) => {
            const avg = epAverages[activity];
            if (count > avg * 1.5 && count > 0) {
                strengths.push(`${activity} (${count} vs ${avg.toFixed(1)} average)`);
            }
        });
        
        // Identify weaknesses (below 50% of average and not zero)
        Object.entries(activities).forEach(([activity, count]) => {
            const avg = epAverages[activity];
            if (count < avg * 0.5 && avg > 0) {
                weaknesses.push(`${activity} (${count} vs ${avg.toFixed(1)} average)`);
            }
        });
        
        // Analyze vote attendance (convert from decimal to percentage)
        const attendance = mep.vote_attendance_percentage || mep.attendance_rate || 0;
        if (attendance > 95) {
            strengths.push(`Excellent vote attendance (${attendance.toFixed(1)}%)`);
        } else if (attendance < 80) {
            weaknesses.push(`Low vote attendance (${attendance.toFixed(1)}%)`);
        }
        
        // Analyze roles
        const roles = {
            'Committee Chair': mep.committee_chair || 0,
            'Committee Vice-Chair': mep.committee_vice_chair || 0,
            'Committee Member': mep.committee_member || 0,
            'Delegation Chair': mep.delegation_chair || 0,
            'EP Leadership': (mep.ep_president || 0) + (mep.ep_vice_president || 0) + (mep.ep_quaestor || 0)
        };
        
        Object.entries(roles).forEach(([role, count]) => {
            if (count > 0) {
                strengths.push(`${role} role${count > 1 ? 's' : ''} (${count})`);
            }
        });
        
        // Generate analysis text
        let analysis = `<strong>${mep.full_name}</strong> ranks <strong>${overallRank} out of ${totalMeps}</strong> MEPs overall (${overallPercentile}th percentile). `;
        
        if (countryRank.total > 1) {
            const countryPercentile = Math.round(((countryRank.total - countryRank.rank + 1) / countryRank.total) * 100);
            analysis += `Among ${mep.country} MEPs, they rank <strong>${countryRank.rank} out of ${countryRank.total}</strong> (${countryPercentile}th percentile). `;
        }
        
        if (groupRank.total > 1) {
            const groupPercentile = Math.round(((groupRank.total - groupRank.rank + 1) / groupRank.total) * 100);
            analysis += `Within the ${mep.group} group, they rank <strong>${groupRank.rank} out of ${groupRank.total}</strong> (${groupPercentile}th percentile). `;
        }
        
        if (nationalPartyRank.total > 1) {
            const partyPercentile = Math.round(((nationalPartyRank.total - nationalPartyRank.rank + 1) / nationalPartyRank.total) * 100);
            analysis += `Among ${mep.national_party} MEPs, they rank <strong>${nationalPartyRank.rank} out of ${nationalPartyRank.total}</strong> (${partyPercentile}th percentile). `;
        }
        
        if (strengths.length > 0) {
            analysis += `<br><br><strong>Strengths:</strong> ${mep.full_name} excels in ${strengths.slice(0, 3).join(', ')}${strengths.length > 3 ? ' and other areas' : ''}. `;
        }
        
        if (weaknesses.length > 0) {
            analysis += `<br><br><strong>Areas for improvement:</strong> ${mep.full_name} could improve in ${weaknesses.slice(0, 3).join(', ')}${weaknesses.length > 3 ? ' and other areas' : ''}. `;
        }
        
        if (strengths.length === 0 && weaknesses.length === 0) {
            analysis += `<br><br>This MEP shows balanced performance across all activity categories, with no significant outliers in either direction.`;
        }
        
        return analysis;
    } catch (error) {
        console.error('Error generating performance analysis:', error);
        return `<strong>${mep.full_name}</strong> ranks <strong>${overallRank} out of ${totalMeps}</strong> MEPs overall. Performance analysis could not be generated due to an error.`;
    }
}

// Note: MEP scoring is now handled by the MEP Ranking system
// Scores are pre-calculated in the dataset by build_term_dataset.py
// This ensures consistency between index page and profile page scoring

// Performance summary function removed

function populateActivityStats(mep, averages, allMeps) {
    const statsEl = document.getElementById('stats-grid');
    
    const activities = [
        { name: 'Speeches', key: 'speeches', icon: 'fa-microphone' },
        { name: 'Amendments', key: 'amendments', icon: 'fa-edit' },
        { name: 'Reports (Rapporteur)', key: 'reports_rapporteur', icon: 'fa-file-alt' },
        { name: 'Reports (Shadow)', key: 'reports_shadow', icon: 'fa-file' },
        { name: 'Written Questions', key: 'questions_written', icon: 'fa-question-circle' },
        { name: 'Oral Questions', key: 'questions_oral', icon: 'fa-microphone-alt' },
        { name: 'Motions', key: 'motions', icon: 'fa-balance-scale' },
        { name: 'Opinions (Rapporteur)', key: 'opinions_rapporteur', icon: 'fa-comment' },
        { name: 'Opinions (Shadow)', key: 'opinions_shadow', icon: 'fa-comments' },
        { name: 'Explanations of Vote', key: 'explanations', icon: 'fa-info-circle' },
        { name: 'Voting Attendance', key: 'voting_combined', icon: 'fa-vote-yea', isCombinedVoting: true }
    ];

    statsEl.innerHTML = '';

    activities.forEach(activity => {
        let value, epAvg, groupAvg, countryAvg, rank, percentageFill, performanceClass;
        
        if (activity.isCombinedVoting) {
            // Handle combined voting data
            const votesAttended = mep.votes_attended || 0;
            // Convert attendance_rate (0-1 decimal) to percentage (0-100)
            const attendanceRateDecimal = mep.attendance_rate || 0;
            const attendanceRate = attendanceRateDecimal * 100; // Convert to percentage
            
            // Use attendance rate for ranking/performance calculation
            value = attendanceRate;
            // For voting attendance, use attendance rate averages
            epAvg = (averages?.ep?.attendance_rate || 0) * 100; // Convert to percentage
            groupAvg = (averages?.groups?.[mep.group]?.attendance_rate || 0) * 100;
            countryAvg = (averages?.countries?.[mep.country]?.attendance_rate || 0) * 100;
            
            // Calculate rank based on attendance rate
            const sortedValues = allMeps.map(m => (m.attendance_rate || 0) * 100).sort((a, b) => b - a);
            rank = sortedValues.findIndex(v => v <= attendanceRate) + 1;
        } else {
            // Handle regular activities
            value = mep[activity.key] || 0;
            
            // Use averages for all activities including written questions
            epAvg = averages?.ep?.[activity.key] || 0;
            groupAvg = averages?.groups?.[mep.group]?.[activity.key] || 0;
            countryAvg = averages?.countries?.[mep.country]?.[activity.key] || 0;
            
            // Calculate rank among all MEPs for this activity
            const sortedValues = allMeps.map(m => m[activity.key] || 0).sort((a, b) => b - a);
            rank = sortedValues.findIndex(v => v <= value) + 1;
        }
        
        const totalMeps = allMeps.length;
        
        // Calculate percentage fill for the progress bar (based on rank)
        percentageFill = Math.min(100, Math.max(5, ((totalMeps - rank + 1) / totalMeps) * 100));
        
        // Determine performance level based on percentage fill
        if (percentageFill <= 33) {
            performanceClass = 'performance-low';
        } else if (percentageFill <= 66) {
            performanceClass = 'performance-medium';
        } else {
            performanceClass = 'performance-high';
        }
        
        // For percentages, don't show decimals if they're whole numbers
        const formatValue = (val) => {
            // Handle non-numeric values
            if (val === null || val === undefined || val === 'N/A' || isNaN(val)) {
                return 'N/A';
            }
            
            const numVal = Number(val);
            if (isNaN(numVal)) {
                return 'N/A';
            }
            
            if (activity.isPercentage || activity.isCombinedVoting) {
                return numVal % 1 === 0 ? `${numVal}%` : `${numVal.toFixed(1)}%`;
            }
            return Math.round(numVal).toString();
        };

        // Check if this category has detailed data available (exclude combined voting)
        const hasDetailedData = !activity.isCombinedVoting;
        
        const card = document.createElement('div');
        card.className = 'detail-stats-card';
        
        if (hasDetailedData) {
            card.classList.add('clickable');
            card.style.cursor = 'pointer';
            card.addEventListener('click', () => showCategoryDetails(activity.key, activity.name, mep));
        }

        if (activity.isCombinedVoting) {
            // Special display for combined voting data
            const votesAttended = mep.votes_attended || 0;
            const attendanceRate = (mep.vote_attendance_percentage || mep.attendance_rate || 0) * 100;
            
            // Get averages for votes attended
            const votesEpAvg = averages?.ep?.votes_attended || 0;
            const votesGroupAvg = averages?.groups?.[mep.group]?.votes_attended || 0;
            const votesCountryAvg = averages?.countries?.[mep.country]?.votes_attended || 0;
            
            card.innerHTML = `
                <div class="flex items-center justify-between mb-2">
                    <div class="flex items-center">
                        <i class="fas ${activity.icon} text-blue-600 mr-2"></i>
                        <span class="font-medium text-gray-700">${activity.name}</span>
                    </div>
                    <div class="performance-indicator ${performanceClass}"></div>
                </div>
                <div class="mb-3">
                    <div class="flex items-baseline justify-between mb-1">
                        <div class="stats-value text-lg">${votesAttended} votes</div>
                        <div class="text-sm text-gray-600">${formatValue(attendanceRate)} attendance</div>
                    </div>
                    <div class="rank-info text-right text-xs">Rank ${rank}/${totalMeps}</div>
                </div>
                <div class="grid grid-cols-2 gap-2 text-xs text-gray-600">
                    <div class="border-r pr-2">
                        <div class="font-medium text-gray-700 mb-1">Votes Attended</div>
                        <div>EP Avg: <span class="font-medium">${Math.round(votesEpAvg)}</span></div>
                        <div>Group Avg: <span class="font-medium">${Math.round(votesGroupAvg)}</span></div>
                        <div>Country Avg: <span class="font-medium">${Math.round(votesCountryAvg)}</span></div>
                    </div>
                    <div class="pl-2">
                        <div class="font-medium text-gray-700 mb-1">Attendance Rate</div>
                        <div>EP Avg: <span class="font-medium">${formatValue(epAvg)}</span></div>
                        <div>Group Avg: <span class="font-medium">${formatValue(groupAvg)}</span></div>
                        <div>Country Avg: <span class="font-medium">${formatValue(countryAvg)}</span></div>
                    </div>
                </div>
                <div class="progress-bar mt-3">
                    <div class="progress-fill ${performanceClass}" style="width: ${percentageFill}%"></div>
                </div>
            `;
        } else {
            // Regular display for other activities
            card.innerHTML = `
                <div class="flex items-center justify-between mb-2">
                    <div class="flex items-center">
                        <i class="fas ${activity.icon} text-blue-600 mr-2"></i>
                        <span class="font-medium text-gray-700">${activity.name}</span>
                        ${hasDetailedData ? '<i class="fas fa-external-link-alt text-gray-400 text-xs ml-1"></i>' : ''}
                    </div>
                    <div class="performance-indicator ${performanceClass}"></div>
                </div>
                <div class="flex items-baseline justify-between mb-2">
                    <div class="stats-value">${activity.isPercentage ? formatValue(value) : value}</div>
                    <div class="rank-info">Rank ${rank}/${totalMeps}</div>
                </div>
                <div class="averages-grid text-xs text-gray-600">
                    <div>EP Average: <br><span class="font-medium">${epAvg === 'N/A' ? 'N/A' : (activity.isPercentage ? formatValue(epAvg) : Math.round(epAvg))}</span></div>
                    <div>Group Average: <br><span class="font-medium">${groupAvg === 'N/A' ? 'N/A' : (activity.isPercentage ? formatValue(groupAvg) : Math.round(groupAvg))}</span></div>
                    <div>Country Average: <br><span class="font-medium">${countryAvg === 'N/A' ? 'N/A' : (activity.isPercentage ? formatValue(countryAvg) : Math.round(countryAvg))}</span></div>
                </div>
                <div class="progress-bar mt-3">
                    <div class="progress-fill ${performanceClass}" style="width: ${percentageFill}%"></div>
                </div>
            `;
        }
        
        statsEl.appendChild(card);
    });
}

function populateRoles(mep) {
    const rolesEl = document.getElementById('mep-roles-container');
    
    // Check for any leadership roles first
    const epRoles = [];
    if (mep.ep_president > 0) epRoles.push({ type: 'EP President', count: mep.ep_president, icon: 'fa-crown' });
    if (mep.ep_vice_president > 0) epRoles.push({ type: 'EP Vice-President', count: mep.ep_vice_president, icon: 'fa-star' });
    if (mep.ep_quaestor > 0) epRoles.push({ type: 'EP Quaestor', count: mep.ep_quaestor, icon: 'fa-coins' });
    
    // Role hierarchy for deduplication (higher number = higher priority)
    const roleHierarchy = {
        'Chair': 4,
        'Vice-Chair': 3,
        'Member': 2,
        'Substitute': 1
    };
    
    // Function to deduplicate roles by committee/delegation and keep only the highest role
    function deduplicateRoles(roles) {
        const roleMap = new Map();
        
        roles.forEach(role => {
            const key = `${role.type}-${role.acronym}`;
            const currentPriority = roleHierarchy[role.role] || 0;
            
            if (!roleMap.has(key) || currentPriority > (roleHierarchy[roleMap.get(key).role] || 0)) {
                roleMap.set(key, role);
            }
        });
        
        return Array.from(roleMap.values());
    }
    
    // Check for detailed roles
    const hasDetailedRoles = mep.detailed_roles && mep.detailed_roles.length > 0;
    let committeeRoles = hasDetailedRoles ? mep.detailed_roles.filter(role => role.type === 'committee') : [];
    let delegationRoles = hasDetailedRoles ? mep.detailed_roles.filter(role => role.type === 'delegation') : [];
    
    // Deduplicate detailed roles
    if (committeeRoles.length > 0) {
        committeeRoles = deduplicateRoles(committeeRoles);
    }
    if (delegationRoles.length > 0) {
        delegationRoles = deduplicateRoles(delegationRoles);
    }
    
    // Check for generic role counts (fallback)
    const genericRoles = [];
    if (mep.committee_chair > 0) genericRoles.push({ type: 'Committee Chair', count: mep.committee_chair, icon: 'fa-gavel' });
    if (mep.committee_vice_chair > 0) genericRoles.push({ type: 'Committee Vice-Chair', count: mep.committee_vice_chair, icon: 'fa-user-tie' });
    if (mep.committee_member > 0) genericRoles.push({ type: 'Committee Member', count: mep.committee_member, icon: 'fa-users' });
    if (mep.committee_substitute > 0) genericRoles.push({ type: 'Committee Substitute', count: mep.committee_substitute, icon: 'fa-user-plus' });
    if (mep.delegation_chair > 0) genericRoles.push({ type: 'Delegation Chair', count: mep.delegation_chair, icon: 'fa-flag' });
    if (mep.delegation_vice_chair > 0) genericRoles.push({ type: 'Delegation Vice-Chair', count: mep.delegation_vice_chair, icon: 'fa-flag' });
    if (mep.delegation_member > 0) genericRoles.push({ type: 'Delegation Member', count: mep.delegation_member, icon: 'fa-globe' });
    if (mep.delegation_substitute > 0) genericRoles.push({ type: 'Delegation Substitute', count: mep.delegation_substitute, icon: 'fa-globe' });
    
    // If there are no roles of any kind, hide the entire section
    if (epRoles.length === 0 && committeeRoles.length === 0 && delegationRoles.length === 0 && genericRoles.length === 0) {
        const rolesCard = document.querySelector('.card:has(#mep-roles-container)');
        if (rolesCard) {
            rolesCard.style.display = 'none';
        }
        return;
    }
    
    // Make sure the card is visible
    const rolesCard = document.querySelector('.card:has(#mep-roles-container)');
    if (rolesCard) {
        rolesCard.style.display = 'block';
    }
    
    let content = '';
    
    // EP Leadership Roles
    if (epRoles.length > 0) {
        content += `
            <div class="mb-6">
                <h3 class="text-lg font-semibold text-gray-800 mb-3">
                    <i class="fas fa-crown text-blue-600 mr-2"></i>EP Leadership
                </h3>
                <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                    ${epRoles.map(role => `
                        <div class="role-chip">
                            <div class="flex items-center justify-between">
                                <div class="flex items-center">
                                    <i class="fas ${role.icon} text-blue-600 mr-2"></i>
                                    <span class="font-medium text-gray-700">${role.type}</span>
                                </div>
                                ${role.count > 1 ? `<span class="text-sm bg-blue-100 text-blue-800 px-2 py-1 rounded-full">${role.count}</span>` : ''}
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }
    
    // Committee Roles (detailed if available, otherwise generic)
    if (committeeRoles.length > 0) {
        // Calculate committee role summary
        const committeeRoleCounts = {};
        committeeRoles.forEach(role => {
            const roleType = `Committee ${role.role}`;
            committeeRoleCounts[roleType] = (committeeRoleCounts[roleType] || 0) + 1;
        });
        
        const committeeSummary = Object.entries(committeeRoleCounts)
            .map(([role, count]) => `${role}: ${count}`)
            .join(', ');
        
        content += `
            <div class="mb-6">
                <h3 class="text-lg font-semibold text-gray-800 mb-3">
                    <i class="fas fa-users text-blue-600 mr-2"></i>Committee Roles
                </h3>
                <div class="bg-blue-50 border border-blue-200 rounded-lg p-3 mb-4">
                    <div class="text-sm font-medium text-blue-800">${committeeSummary}</div>
                </div>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
                    ${committeeRoles.map(role => `
                        <div class="role-chip">
                            <div class="font-medium text-gray-800">${role.role}</div>
                            <div class="text-sm text-gray-600">${role.name}</div>
                            <div class="text-xs text-blue-600 mt-1">(${role.acronym})</div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    } else {
        // Show generic committee roles if no detailed ones
        const committeeGenericRoles = genericRoles.filter(role => role.type.includes('Committee'));
        if (committeeGenericRoles.length > 0) {
            content += `
                <div class="mb-6">
                    <h3 class="text-lg font-semibold text-gray-800 mb-3">
                        <i class="fas fa-users text-blue-600 mr-2"></i>Committee Roles
                    </h3>
                    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                        ${committeeGenericRoles.map(role => `
                            <div class="role-chip">
                                <div class="flex items-center justify-between">
                                    <div class="flex items-center">
                                        <i class="fas ${role.icon} text-blue-600 mr-2"></i>
                                        <span class="font-medium text-gray-700">${role.type}</span>
                                    </div>
                                    ${role.count > 1 ? `<span class="text-sm bg-blue-100 text-blue-800 px-2 py-1 rounded-full">${role.count}</span>` : ''}
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>
            `;
        }
    }
    
    // Delegation Roles (detailed if available, otherwise generic)
    if (delegationRoles.length > 0) {
        // Calculate delegation role summary
        const delegationRoleCounts = {};
        delegationRoles.forEach(role => {
            const roleType = `Delegation ${role.role}`;
            delegationRoleCounts[roleType] = (delegationRoleCounts[roleType] || 0) + 1;
        });
        
        const delegationSummary = Object.entries(delegationRoleCounts)
            .map(([role, count]) => `${role}: ${count}`)
            .join(', ');
        
        content += `
            <div class="mb-6">
                <h3 class="text-lg font-semibold text-gray-800 mb-3">
                    <i class="fas fa-globe text-blue-600 mr-2"></i>Delegation Roles
                </h3>
                <div class="bg-green-50 border border-green-200 rounded-lg p-3 mb-4">
                    <div class="text-sm font-medium text-green-800">${delegationSummary}</div>
                </div>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
                    ${delegationRoles.map(role => `
                        <div class="role-chip">
                            <div class="font-medium text-gray-800">${role.role}</div>
                            <div class="text-sm text-gray-600">${role.name}</div>
                            <div class="text-xs text-blue-600 mt-1">(${role.acronym})</div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    } else {
        // Show generic delegation roles if no detailed ones
        const delegationGenericRoles = genericRoles.filter(role => role.type.includes('Delegation'));
        if (delegationGenericRoles.length > 0) {
            content += `
                <div class="mb-6">
                    <h3 class="text-lg font-semibold text-gray-800 mb-3">
                        <i class="fas fa-globe text-blue-600 mr-2"></i>Delegation Roles
                    </h3>
                    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                        ${delegationGenericRoles.map(role => `
                            <div class="role-chip">
                                <div class="flex items-center justify-between">
                                    <div class="flex items-center">
                                        <i class="fas ${role.icon} text-blue-600 mr-2"></i>
                                        <span class="font-medium text-gray-700">${role.type}</span>
                                    </div>
                                    ${role.count > 1 ? `<span class="text-sm bg-blue-100 text-blue-800 px-2 py-1 rounded-full">${role.count}</span>` : ''}
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>
            `;
        }
    }
    
    rolesEl.innerHTML = content;
}

async function populateScoreBreakdown(mep, term) {
    const breakdownEl = document.getElementById('score-breakdown-container');
    if (!breakdownEl) return;

    // Hide score breakdown section as requested - score breakdown is shown on index page under score column
    breakdownEl.style.display = 'none';
    return;

    // Unreachable code removed - score breakdown is disabled
    /*
    try {
        // Fetch scoring configuration for the term
        const baseUrl = window.location.protocol + '//' + window.location.host;
        const response = await fetch(`${baseUrl}/api/scoring-config?term=${term}`);
        const configData = await response.json();
        
        if (!configData.success) {
            console.error('Failed to load scoring config:', configData.error);
            return;
        }
        
        const config = configData.categories;
        
        // Helper function to format ranges
        function formatRange(ranges) {
            return ranges.map(range => {
                const [min, max, points] = range;
                if (max === Infinity || max === Number.MAX_VALUE) {
                    return `${min}+ (${points} pts)`;
                } else {
                    return `${min}-${max} (${points} pts)`;
                }
            }).join(', ');
        }
        
        // Helper function to get the range and score for a specific count
        function getRangeInfo(count, ranges) {
            for (const [min, max, points] of ranges) {
                if (count >= min && count <= max) {
                    let rangeText;
                    if (max === Infinity || max === Number.MAX_VALUE) {
                        rangeText = `${min}+`;
                    } else {
                        rangeText = `${min}-${max}`;
                    }
                    return { range: rangeText, points: points };
                }
            }
            return { range: '0', points: 0 };
        }
        
        // Calculate detailed breakdown
        const speeches = mep.speeches || 0;
        const explanations = mep.explanations || 0;
        const amendments = mep.amendments || 0;
        const questions = mep.questions || 0;
        
        // Get oral and written questions breakdown (if available, otherwise estimate)
        const oralQuestions = Math.floor(questions * 0.1); // Rough estimate
        const writtenQuestions = questions - oralQuestions;
        
        const speechesInfo = getRangeInfo(speeches, config.statements.speeches_ranges);
        const explanationsInfo = getRangeInfo(explanations, config.statements.explanations_ranges);
        const oralQuestionsInfo = getRangeInfo(oralQuestions, config.statements.oral_questions_ranges);
        const amendmentsInfo = getRangeInfo(amendments, config.statements.amendment_ranges);
        
        const writtenQuestionsScore = Math.min(writtenQuestions * config.statements.written_questions_rate, config.statements.written_questions_max);
        
        const statementsTotal = (mep.speeches_score || 0) + (mep.explanations_score || 0) + 
                               (mep.oral_questions_score || 0) + (mep.written_questions_score || 0);
        
        breakdownEl.innerHTML = `
            <div class="bg-white border border-gray-200 rounded-lg p-6">
                <h3 class="text-lg font-semibold text-gray-800 mb-4">
                    <i class="fas fa-calculator text-blue-600 mr-2"></i>
                    MEP Score Breakdown (Term ${term})
                </h3>
                
                <div class="mb-6">
                    <h4 class="text-md font-semibold text-gray-700 mb-3">Statements Category</h4>
                    <div class="overflow-x-auto">
                        <table class="min-w-full text-sm">
                            <thead class="bg-gray-50">
                                <tr>
                                    <th class="px-3 py-2 text-left font-medium text-gray-700">Type</th>
                                    <th class="px-3 py-2 text-center font-medium text-gray-700">Count</th>
                                    <th class="px-3 py-2 text-center font-medium text-gray-700">Range</th>
                                    <th class="px-3 py-2 text-center font-medium text-gray-700">Score</th>
                                </tr>
                            </thead>
                            <tbody class="divide-y divide-gray-200">
                                <tr>
                                    <td class="px-3 py-2 font-medium">Speeches</td>
                                    <td class="px-3 py-2 text-center">${speeches}</td>
                                    <td class="px-3 py-2 text-center text-sm text-gray-600">
                                        <span class="font-medium text-blue-600">${speechesInfo.range}</span><br>
                                        <span class="text-xs">Dynamic ranges (term-based)</span>
                                    </td>
                                    <td class="px-3 py-2 text-center font-medium">${(mep.speeches_score || 0).toFixed(1)}</td>
                                </tr>
                                <tr class="bg-gray-50">
                                    <td class="px-3 py-2 font-medium">Explanations of Vote</td>
                                    <td class="px-3 py-2 text-center">${explanations}</td>
                                    <td class="px-3 py-2 text-center text-sm text-gray-600">
                                        <span class="font-medium text-blue-600">${explanationsInfo.range}</span><br>
                                        <span class="text-xs">Dynamic ranges (term-based)</span>
                                    </td>
                                    <td class="px-3 py-2 text-center font-medium">${(mep.explanations_score || 0).toFixed(1)}</td>
                                </tr>
                                <tr>
                                    <td class="px-3 py-2 font-medium">Oral Questions</td>
                                    <td class="px-3 py-2 text-center">${oralQuestions}</td>
                                    <td class="px-3 py-2 text-center text-sm text-gray-600">
                                        <span class="font-medium text-blue-600">${oralQuestionsInfo.range}</span><br>
                                        <span class="text-xs">Dynamic ranges (term-based)</span>
                                    </td>
                                    <td class="px-3 py-2 text-center font-medium">${(mep.oral_questions_score || 0).toFixed(1)}</td>
                                </tr>
                                <tr class="bg-gray-50">
                                    <td class="px-3 py-2 font-medium">Written Questions</td>
                                    <td class="px-3 py-2 text-center">${writtenQuestions}</td>
                                    <td class="px-3 py-2 text-center text-sm text-gray-600">
                                        <span class="font-medium text-blue-600">${config.statements.written_questions_rate} each</span><br>
                                        <span class="text-xs">(max ${config.statements.written_questions_max} pts)</span>
                                    </td>
                                    <td class="px-3 py-2 text-center font-medium">${(mep.written_questions_score || 0).toFixed(1)}</td>
                                </tr>
                                <tr class="border-t-2 border-gray-300">
                                    <td class="px-3 py-2 font-medium">Amendments</td>
                                    <td class="px-3 py-2 text-center">${amendments}</td>
                                    <td class="px-3 py-2 text-center text-sm text-gray-600">
                                        <span class="font-medium text-blue-600">${amendmentsInfo.range}</span><br>
                                        <span class="text-xs">Dynamic ranges (term-based)</span>
                                    </td>
                                    <td class="px-3 py-2 text-center font-medium">${(mep.amendments_score || 0).toFixed(1)}</td>
                                </tr>
                                <tr class="bg-blue-50 font-bold">
                                    <td class="px-3 py-2">Statements Total</td>
                                    <td class="px-3 py-2 text-center">-</td>
                                    <td class="px-3 py-2 text-center text-sm text-gray-600">Score (term-based)</td>
                                    <td class="px-3 py-2 text-center">${(mep.statements_score || 0).toFixed(1)}</td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>
                
                <div class="text-xs text-gray-500 mt-4">
                    <div class="flex items-center gap-2">
                        <i class="fas fa-info-circle"></i>
                        <span>Scoring uses the MEP Score methodology (October 2017) with dynamic ranges calculated for Term ${term}. 
                        Transparent calculation shows exactly how each activity contributes to the final score.</span>
                    </div>
                </div>
                
                <div class="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded">
                    <div class="text-sm text-yellow-800">
                        <strong>Range Information for Term ${term}:</strong><br>
                        <span class="text-xs">
                            • Speeches: ${formatRange(config.statements.speeches_ranges)}<br>
                            • Explanations: ${formatRange(config.statements.explanations_ranges)}<br>
                            • Oral Questions: ${formatRange(config.statements.oral_questions_ranges)}<br>
                            • Amendments: ${formatRange(config.statements.amendment_ranges)}
                        </span>
                    </div>
                </div>
            </div>
        `;
        
    } catch (error) {
        console.error('Error loading score breakdown:', error);
        breakdownEl.innerHTML = `
            <div class="bg-red-50 border border-red-200 rounded-lg p-4">
                <div class="text-red-700">
                    <i class="fas fa-exclamation-triangle mr-2"></i>
                    Unable to load score breakdown. Please try again later.
                </div>
            </div>
        `;
    }
    */
}

document.addEventListener('DOMContentLoaded', async () => {
    // Initialize
    loadMEPProfile();
    
    // Initialize unified score breakdown modal
    initializeScoreBreakdownModal();
});

// Add event delegation for Load More buttons
document.addEventListener('click', function(e) {
    if (e.target.classList.contains('load-more-btn') || e.target.closest('.load-more-btn')) {
        e.preventDefault();
        const button = e.target.classList.contains('load-more-btn') ? e.target : e.target.closest('.load-more-btn');
        loadMoreRecords(button);
    }
});

async function showCategoryDetails(categoryKey, categoryLabel, mep) {
    const urlParams = new URLSearchParams(window.location.search);
    const term = parseInt(urlParams.get('term')) || 10;

    const modal = document.createElement('div');
    modal.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50';
    modal.style.display = 'flex';

    modal.innerHTML = `
        <div class="bg-white rounded-lg max-w-4xl w-full mx-4 max-h-[90vh] overflow-hidden flex flex-col">
            <div class="flex items-center justify-between p-6 border-b">
                <h2 class="text-2xl font-bold text-gray-800">${categoryLabel} - ${mep.full_name}</h2>
                <button class="text-gray-400 hover:text-gray-600 text-2xl" onclick="this.closest('.fixed').remove()">
                    <i class="fas fa-times"></i>
                </button>
            </div>
            <div class="p-6 overflow-y-auto flex-1">
                <div class="flex flex-col items-center justify-center py-8">
                    <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mb-4"></div>
                    <span class="text-lg text-gray-600 mb-4" id="loading-text">${term === 10 ? 'Initializing data load...' : 'Loading archived parliamentary records...'}</span>
                    <div class="w-64 bg-gray-200 rounded-full h-2.5 mb-2">
                        <div class="bg-blue-600 h-2.5 rounded-full transition-all duration-300" id="progress-bar" style="width: 0%"></div>
                    </div>
                    <span class="text-sm text-gray-500" id="progress-text">0%</span>
                </div>
            </div>
        </div>
    `;

    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.remove();
        }
    });

    document.body.appendChild(modal);

// Load detailed data with progress tracking
    try {
        const progressBar = modal.querySelector('#progress-bar');
        const progressText = modal.querySelector('#progress-text');
        const loadingText = modal.querySelector('#loading-text');
        
        // Smooth progress stages with realistic timing
        const updateProgress = (percent, message) => {
            if (progressBar) progressBar.style.width = `${percent}%`;
            if (progressText) progressText.textContent = `${percent}%`;
            if (loadingText) loadingText.textContent = message;
        };
        
        updateProgress(10, 'Connecting to server...');
        await new Promise(resolve => setTimeout(resolve, 100));
        
        updateProgress(25, 'Loading MEP data...');
        await new Promise(resolve => setTimeout(resolve, 150));
        
        // Different timing for different categories
        let detailsContent;
        if (categoryKey === 'amendments') {
            // Get current term from URL
            const urlParams = new URLSearchParams(window.location.search);
            const term = parseInt(urlParams.get('term')) || 10;
            
            // Get term date range for display
            let termRange = '';
            if (term === 8) {
                termRange = '(2014-2019)';
            } else if (term === 9) {
                termRange = '(2019-2024)';
            } else if (term === 10) {
                termRange = '(2024-present)';
            } else {
                termRange = `(term ${term})`;
            }
            
            updateProgress(20, 'Checking amendment count in database...');
            await new Promise(resolve => setTimeout(resolve, 200));
            
            updateProgress(35, 'Streaming through 1.4GB amendments file...');
            await new Promise(resolve => setTimeout(resolve, 500));
            
            updateProgress(50, 'Finding amendments for this MEP...');
            await new Promise(resolve => setTimeout(resolve, 1000));
            
            updateProgress(70, `Filtering by parliamentary term ${termRange}...`);
            detailsContent = await getDetailedDataForCategory(categoryKey, categoryLabel, mep);
            
            updateProgress(90, 'Sorting by date (newest first)...');
            await new Promise(resolve => setTimeout(resolve, 200));
        } else if (categoryKey === 'speeches') {
            updateProgress(45, 'Loading speech records...');
            await new Promise(resolve => setTimeout(resolve, 120));
            
            updateProgress(65, 'Filtering speeches...');
            detailsContent = await getDetailedDataForCategory(categoryKey, categoryLabel, mep);
            
            updateProgress(85, 'Processing content...');
            await new Promise(resolve => setTimeout(resolve, 80));
        } else {
            updateProgress(50, 'Processing parliamentary activities...');
            await new Promise(resolve => setTimeout(resolve, 120));
            
            updateProgress(70, 'Filtering records...');
            detailsContent = await getDetailedDataForCategory(categoryKey, categoryLabel, mep);
            
            updateProgress(85, 'Organizing data...');
            await new Promise(resolve => setTimeout(resolve, 80));
        }
        
        updateProgress(95, 'Formatting display...');
        await new Promise(resolve => setTimeout(resolve, 60));
        
        updateProgress(100, 'Complete!');
        await new Promise(resolve => setTimeout(resolve, 150));
        
        // Update modal content
        const contentDiv = modal.querySelector('.overflow-y-auto');
        contentDiv.innerHTML = detailsContent;
    } catch (error) {
        console.error('Error in showCategoryDetails:', error);
        const contentDiv = modal.querySelector('.overflow-y-auto');
        contentDiv.innerHTML = `
            <div class="bg-red-50 rounded-lg p-4 border border-red-200">
                <h3 class="text-lg font-semibold text-red-800 mb-2">Error Loading Details</h3>
                <p class="text-red-700">Failed to load category details: ${error.message}</p>
                <p class="text-sm text-red-600 mt-2">
                    Please ensure the API server is running on port 8000 and try again.
                </p>
            </div>
        `;
    }
}

async function loadActivityDataFromTermFiles(mepId, categoryKey, term, offset, limit) {
    
    // Determine the correct file path based on term
    let filePath;
    if (term === 8) {
        filePath = '/data/parltrack/8th%20term/ep_mep_activities-2019-07-03.json%282%29';
    } else if (term === 9) {
        filePath = '/data/parltrack/9th%20term/ep_mep_activities-2024-07-02.json';
    } else {
        throw new Error(`Term ${term} not supported for direct file loading`);
    }
    
    
    try {
        // Load the activities data
        const response = await fetch(filePath);
        
        if (!response.ok) {
            throw new Error(`Failed to load activities file: ${response.statusText}`);
        }
        
        const allActivities = await response.json();
        
        // Find MEP's activities
        const mepData = allActivities.find(mep => mep.mep_id === mepId);
        if (!mepData) {
            return {
                success: false,
                error: `MEP ${mepId} not found in term ${term} data`
            };
        }
        
        // Get data based on category
        let filteredItems = [];
        
        if (categoryKey === 'speeches') {
            const allItems = mepData.CRE || [];
            // Filter out explanations and one-minute speeches
            filteredItems = allItems.filter(item => 
                !item.title?.includes('Explanations of vote') && 
                !item.title?.includes('One-minute speeches')
            );
        } else if (categoryKey === 'questions' || categoryKey === 'questions_written') {
            filteredItems = mepData.WQ || [];
        } else if (categoryKey === 'questions_oral') {
            filteredItems = mepData.OQ || [];
        } else if (categoryKey === 'motions') {
            filteredItems = mepData.MOTION || [];
        } else if (categoryKey === 'explanations') {
            // Get written explanations
            const wexp = mepData.WEXP || [];
            // Get spoken explanations from CRE
            const creExp = (mepData.CRE || []).filter(item => 
                item.title?.includes('Explanations of vote')
            );
            filteredItems = [...wexp, ...creExp];
        } else if (categoryKey === 'reports_rapporteur') {
            filteredItems = mepData.REPORT || [];
        } else if (categoryKey === 'reports_shadow') {
            filteredItems = mepData['REPORT-SHADOW'] || [];
        } else if (categoryKey === 'opinions_rapporteur') {
            filteredItems = mepData.COMPARL || [];
        } else if (categoryKey === 'opinions_shadow') {
            filteredItems = mepData['COMPARL-SHADOW'] || [];
        }
        
        // Sort by date (newest first)
        filteredItems.sort((a, b) => (b.date || '').localeCompare(a.date || ''));
        
        // Apply pagination
        const totalCount = filteredItems.length;
        const paginatedData = filteredItems.slice(offset, offset + limit);
        const hasMore = offset + limit < totalCount;
        
        return {
            success: true,
            data: paginatedData,
            total_count: totalCount,
            category: categoryKey,
            offset: offset,
            limit: limit,
            has_more: hasMore,
            mep_id: mepId,
            term: term
        };
        
    } catch (error) {
        console.error('Error loading activity data from term files:', error);
        return {
            success: false,
            error: `Failed to load activity data: ${error.message}`
        };
    }
}

// Check if API server is available
async function isAPIServerAvailable() {
    try {
        const baseUrl = window.location.protocol + '//' + window.location.host;
        const response = await fetch(`${baseUrl}/api/health`, { 
            method: 'GET',
            mode: 'cors',
            cache: 'no-cache'
        });
        return response.ok;
    } catch (error) {
        return false;
    }
}

async function getDetailedDataForCategory(categoryKey, categoryLabel, mep, offset = 0) {
    // Get URL parameters
    const urlParams = new URLSearchParams(window.location.search);
    const term = parseInt(urlParams.get('term')) || 10;
    
    // For terms 8-9, immediately show the temporary unavailable message without any data loading
    if (term === 8 || term === 9) {
        return `
            <div class="space-y-6">
                <div class="bg-blue-50 rounded-lg p-4 border border-blue-200 text-center">
                    <h3 class="text-lg font-semibold text-blue-800 mb-2">mepscore.eu says</h3>
                    <p class="text-blue-700">
                        Activity details are temporarily unavailable for MEPs from 2014-2024 (Terms 8-9) due to large database optimization in progress on server. This feature is fully available for current MEPs (Term 10: 2024-2029). We apologize for the inconvenience and are working to restore full functionality soon.
                    </p>
                </div>
            </div>
        `;
    }
    
    const mepId = parseInt(urlParams.get('mep_id'));
    const value = mep[categoryKey] || 0;
    
    try {
        // Check if we're running in static mode (no API server available)
        const isStaticMode = !await isAPIServerAvailable();
        
        if (isStaticMode) {
            // In static mode, show message that detailed data requires API server
            return `
                <div class="space-y-6">
                    <div class="bg-blue-50 rounded-lg p-4 border border-blue-200">
                        <h3 class="text-lg font-semibold text-blue-800 mb-2">Detailed Data Not Available</h3>
                        <p class="text-blue-700">
                            Detailed ${categoryLabel.toLowerCase()} data requires the API server to be running.
                        </p>
                        <p class="text-sm text-blue-600 mt-2">
                            To view detailed parliamentary activities, please start the complete server with:
                            <code class="bg-blue-100 px-2 py-1 rounded text-xs">python working_api_server.py</code>
                        </p>
                    </div>
                </div>
            `;
        }
        
        // Use the API server for all terms and categories (API handles correct file routing)
        let response;
        if (categoryKey === 'amendments') {
            // Use fetch with extended timeout and one retry fallback (Windows file IO can be slow)
            const doFetchWithTimeout = async (ms, useSignal = true) => {
                if (!useSignal) {
                    const baseUrl = window.location.protocol + '//' + window.location.host;
                    return fetch(`${baseUrl}/api/mep/${mepId}/category/${categoryKey}?term=${term}&offset=${offset}&limit=15`, {
                        cache: 'no-store'
                    });
                }
                const controller = new AbortController();
                const timeoutId = setTimeout(() => controller.abort(), ms);
                try {
                    const baseUrl = window.location.protocol + '//' + window.location.host;
                    const res = await fetch(`${baseUrl}/api/mep/${mepId}/category/${categoryKey}?term=${term}&offset=${offset}&limit=15`, {
                        signal: controller.signal,
                        cache: 'no-store'
                    });
                    clearTimeout(timeoutId);
                    return res;
                } catch (err) {
                    clearTimeout(timeoutId);
                    throw err;
                }
            };

            try {
                // First attempt with 120s timeout
                response = await doFetchWithTimeout(120000, true);
            } catch (err) {
                if (err.name === 'AbortError') {
                    // Retry once without a timeout
                    response = await doFetchWithTimeout(0, false);
                } else {
                    throw err;
                }
            }
        } else {
            // Standard fetch for other categories
            const baseUrl = window.location.protocol + '//' + window.location.host;
            response = await fetch(`${baseUrl}/api/mep/${mepId}/category/${categoryKey}?term=${term}&offset=${offset}&limit=15`);
        }
        
        const result = await response.json();
        
        if (!result.success) {
            throw new Error(result.error || 'Failed to load data');
        }
        
        const detailsHtml = formatCategoryData(result, categoryLabel, mep.full_name, offset, mep, categoryKey);
        return detailsHtml;
        
    } catch (error) {
        console.error('Error loading category details:', error);
        return `
            <div class="space-y-6">
                <div class="bg-red-50 rounded-lg p-4 border border-red-200">
                    <h3 class="text-lg font-semibold text-red-800 mb-2">Error Loading Details</h3>
                    <p class="text-red-700">
                        Unable to load detailed data: ${error.message}
                    </p>
                    <p class="text-sm text-red-600 mt-2">
                        Please ensure the API server is running on port 8000 and try again.
                    </p>
                </div>
                
                <div class="bg-red-50 rounded-lg p-4 border border-red-200">
                    <h3 class="text-lg font-semibold text-red-800 mb-2">Error Loading Details</h3>
                    <p class="text-red-700">
                        Unable to load detailed data: ${error.message}
                    </p>
                    <p class="text-sm text-red-600 mt-2">
                        Please ensure the API server is running on port 8000 and try again.
                    </p>
                </div>
            </div>
        `;
    }
}

function formatCategoryData(result, categoryLabel, mepName, currentOffset = 0, mep = null, categoryKey = null) {
    const { data, total_count, category, offset, limit, has_more } = result;
    
    if (!data || data.length === 0) {
        return `
            <div class="space-y-6">
                <div class="bg-blue-50 rounded-lg p-4 border border-blue-200">
                    <h3 class="text-lg font-semibold text-blue-800 mb-2">Overview</h3>
                    <p class="text-gray-700">
                        <span class="font-medium">${mepName}</span> has no recorded ${categoryLabel.toLowerCase()} 
                        in the current parliamentary term.
                    </p>
                </div>
            </div>
        `;
    }
    
    let itemsHtml = '';
    
    if (category === 'speeches') {
        itemsHtml = data.map((speech, index) => `
            <div class="border-l-4 border-blue-500 pl-4 mb-4 hover:bg-gray-50 p-3 rounded-r">
                <div class="flex justify-between items-start mb-2">
                    <h4 class="font-semibold text-gray-800 flex-1">${speech.title || 'Untitled Speech'}</h4>
                    <span class="text-xs text-gray-500 ml-2">${formatDate(speech.date)}</span>
                </div>
                <p class="text-sm text-gray-600 mb-2">Reference: ${speech.reference || 'N/A'}</p>
                ${speech.dossiers && speech.dossiers.length > 0 ? 
                    `<div class="text-xs text-blue-600">Dossiers: ${speech.dossiers.join(', ')}</div>` : ''
                }
                ${speech.url ? 
                    `<a href="${speech.url}" target="_blank" class="text-xs text-blue-500 hover:underline inline-flex items-center mt-2">
                        <i class="fas fa-external-link-alt mr-1"></i>View Original
                    </a>` : ''
                }
            </div>
        `).join('');
    } else if (category === 'amendments') {
        itemsHtml = data.map((amendment, index) => {
            const amendmentNumber = amendment.seq || currentOffset + index + 1;
            
            return `
                <div class="border-l-4 border-green-500 pl-4 mb-4 hover:bg-gray-50 p-3 rounded-r">
                    <div class="flex justify-between items-start mb-2">
                        <h4 class="font-semibold text-gray-800">Amendment ${amendmentNumber}</h4>
                        <span class="text-xs text-gray-500">${formatDate(amendment.date)}</span>
                    </div>
                    <p class="text-sm text-gray-600 mb-2">Reference: ${amendment.reference || 'N/A'}</p>
                    <p class="text-sm text-gray-600 mb-2">Committee: ${amendment.committee ? (Array.isArray(amendment.committee) ? amendment.committee.join(', ') : amendment.committee) : 'N/A'}</p>
                    ${amendment.location && amendment.location.length > 0 ? 
                        `<p class="text-xs text-gray-500 mb-2">Location: ${amendment.location.map(loc => Array.isArray(loc) ? loc.join(' - ') : loc).join('; ')}</p>` : ''
                    }
                    ${amendment.authors ? `<p class="text-xs text-blue-600 mb-2">Authors: ${amendment.authors}</p>` : ''}
                    ${amendment.old && amendment.old.length > 0 ? 
                        `<div class="mt-2 p-2 bg-red-50 rounded text-sm border-l-2 border-red-300">
                            <strong class="text-red-800">Original text:</strong><br>
                            <div class="text-gray-700 italic">${amendment.old.join(' ')}</div>
                        </div>` : ''
                    }
                    ${amendment.new && amendment.new.length > 0 ? 
                        `<div class="mt-2 p-2 bg-green-50 rounded text-sm border-l-2 border-green-300">
                            <strong class="text-green-800">Proposed amendment:</strong><br>
                            <div class="text-gray-700">${amendment.new.join(' ')}</div>
                        </div>` : ''
                    }
                    ${amendment.src ? 
                        `<a href="${amendment.src}" target="_blank" class="text-xs text-blue-500 hover:underline inline-flex items-center mt-2">
                            <i class="fas fa-external-link-alt mr-1"></i>View Original Document
                        </a>` : ''
                    }
                </div>
            `;
        }).join('');
    } else if (category === 'questions' || category === 'questions_written') {
        itemsHtml = data.map((question, index) => `
            <div class="border-l-4 border-yellow-500 pl-4 mb-4 hover:bg-gray-50 p-3 rounded-r">
                <div class="flex justify-between items-start mb-2">
                    <h4 class="font-semibold text-gray-800">${question.title || `Written Question ${index + 1}`}</h4>
                    <span class="text-xs text-gray-500">${formatDate(question.date)}</span>
                </div>
                <p class="text-sm text-gray-600 mb-2">Reference: ${question.reference || 'N/A'}</p>
                ${question.addressee ? `<p class="text-sm text-blue-600 mb-2">To: ${question.addressee}</p>` : ''}
                ${question.subject ? `<p class="text-sm text-gray-700 mb-2"><strong>Subject:</strong> ${question.subject}</p>` : ''}
                ${question.text ? `
                    <div class="mt-2 p-2 bg-yellow-50 rounded text-sm border-l-2 border-yellow-300">
                        <strong>Question:</strong> ${question.text.length > 200 ? question.text.substring(0, 200) + '...' : question.text}
                    </div>
                ` : ''}
                ${question.url ? `<p class="mt-2"><a href="${question.url}" target="_blank" class="text-blue-600 hover:underline text-sm">View Document</a></p>` : ''}
            </div>
        `).join('');
    } else if (category === 'questions_oral') {
        itemsHtml = data.map((question, index) => `
            <div class="border-l-4 border-orange-500 pl-4 mb-4 hover:bg-gray-50 p-3 rounded-r">
                <div class="flex justify-between items-start mb-2">
                    <h4 class="font-semibold text-gray-800">${question.title || `Oral Question ${index + 1}`}</h4>
                    <span class="text-xs text-gray-500">${formatDate(question.date)}</span>
                </div>
                <p class="text-sm text-gray-600 mb-2">Reference: ${question.reference || 'N/A'}</p>
                ${question.subject ? `<p class="text-sm text-gray-700 mb-2"><strong>Subject:</strong> ${question.subject}</p>` : ''}
                ${question.text ? `
                    <div class="mt-2 p-2 bg-orange-50 rounded text-sm border-l-2 border-orange-300">
                        <strong class="text-yellow-800">Question text:</strong><br>
                        <div class="text-gray-700">${Array.isArray(question.text) ? question.text.join(' ') : question.text}</div>
                    </div>
                ` : ''}
                ${question.url ? 
                    `<a href="${question.url}" target="_blank" class="text-xs text-blue-500 hover:underline inline-flex items-center mt-2">
                        <i class="fas fa-external-link-alt mr-1"></i>View Original Question
                    </a>` : ''
                }
            </div>
        `).join('');
    } else if (category === 'motions') {
        itemsHtml = data.map((motion, index) => `
            <div class="border-l-4 border-purple-500 pl-4 mb-4 hover:bg-gray-50 p-3 rounded-r">
                <div class="flex justify-between items-start mb-2">
                    <h4 class="font-semibold text-gray-800">${motion.title || `Motion ${index + 1}`}</h4>
                    <span class="text-xs text-gray-500">${formatDate(motion['Date opened'] || motion.date)}</span>
                </div>
                ${motion.authors ? `<p class="text-sm text-blue-600 mb-2">Authors: ${motion.authors}</p>` : ''}
                ${motion['Number of signatories'] ? 
                    `<p class="text-sm text-green-600 mb-2">Signatories: ${motion['Number of signatories']}</p>` : ''
                }
                ${motion['Lapse date'] ? 
                    `<p class="text-xs text-gray-500 mb-2">Lapse date: ${formatDate(motion['Lapse date'])}</p>` : ''
                }
                ${motion.formats && motion.formats.length > 0 ? 
                    `<div class="mt-2">
                        <p class="text-xs text-gray-600 mb-1">Available formats:</p>
                        ${motion.formats.map(format => 
                            `<a href="${format.url}" target="_blank" class="text-xs text-blue-500 hover:underline mr-3">
                                <i class="fas fa-file-${format.type.toLowerCase()} mr-1"></i>${format.type} ${format.size || ''}
                            </a>`
                        ).join('')}
                    </div>` : ''
                }
            </div>
        `).join('');
    } else if (category === 'explanations') {
        itemsHtml = data.map((explanation, index) => `
            <div class="border-l-4 border-indigo-500 pl-4 mb-4 hover:bg-gray-50 p-3 rounded-r">
                <div class="flex justify-between items-start mb-2">
                    <h4 class="font-semibold text-gray-800">${explanation.title || 'Explanation of Vote'}</h4>
                    <span class="text-xs text-gray-500">${formatDate(explanation.date)}</span>
                </div>
                ${explanation.reference ? 
                    `<p class="text-sm text-gray-600 mb-2">Reference: ${explanation.reference}</p>` : ''
                }
                ${explanation.text ? `
                    <div class="mt-2 p-3 bg-indigo-50 rounded text-sm border-l-2 border-indigo-300">
                        <strong class="text-indigo-800">Explanation:</strong><br>
                        <div class="text-gray-700 mt-1">${explanation.text.length > 300 ? explanation.text.substring(0, 300) + '...' : explanation.text}</div>
                        ${explanation.text.length > 300 ? 
                            `<button class="text-indigo-600 hover:text-indigo-800 text-xs mt-2 underline" onclick="this.previousElementSibling.textContent='${explanation.text.replace(/'/g, "\\'")}'; this.style.display='none';">Show full text</button>` : ''
                        }
                    </div>
                ` : ''}
                ${explanation.dossiers && explanation.dossiers.length > 0 ? 
                    `<div class="text-xs text-blue-600 mb-2 mt-2">Related Dossiers: ${explanation.dossiers.join(', ')}</div>` : ''
                }
                ${explanation.url ? 
                    `<a href="${explanation.url}" target="_blank" class="text-xs text-blue-500 hover:underline inline-flex items-center mt-2">
                        <i class="fas fa-external-link-alt mr-1"></i>View Original Explanation
                    </a>` : ''
                }
            </div>
        `).join('');
    } else if (category === 'reports_rapporteur' || category === 'reports_shadow') {
        itemsHtml = data.map((report, index) => `
            <div class="border-l-4 border-orange-500 pl-4 mb-4 hover:bg-gray-50 p-3 rounded-r">
                <div class="flex justify-between items-start mb-2">
                    <h4 class="font-semibold text-gray-800">${report.title || 'Report'}</h4>
                    <span class="text-xs text-gray-500">${formatDate(report.date)}</span>
                </div>
                <p class="text-sm text-gray-600 mb-2">Reference: ${report.reference || 'N/A'}</p>
                ${report.committee ? `<p class="text-sm text-blue-600 mb-2">Committee: ${Array.isArray(report.committee) ? report.committee.join(', ') : report.committee}</p>` : ''}
                ${report.procedure ? `<p class="text-xs text-gray-500 mb-2">Procedure: ${report.procedure}</p>` : ''}
                ${report.dossiers && report.dossiers.length > 0 ? 
                    `<div class="text-xs text-blue-600 mb-2">Related Dossiers: ${report.dossiers.join(', ')}</div>` : ''
                }
                ${report.url ? 
                    `<a href="${report.url}" target="_blank" class="text-xs text-blue-500 hover:underline inline-flex items-center mt-2">
                        <i class="fas fa-external-link-alt mr-1"></i>View Original Report
                    </a>` : ''
                }
            </div>
        `).join('');
    } else if (category === 'opinions_rapporteur' || category === 'opinions_shadow') {
        itemsHtml = data.map((opinion, index) => `
            <div class="border-l-4 border-green-500 pl-4 mb-4 hover:bg-gray-50 p-3 rounded-r">
                <div class="flex justify-between items-start mb-2">
                    <h4 class="font-semibold text-gray-800">${opinion.title || 'Opinion'}</h4>
                    <span class="text-xs text-gray-500">${formatDate(opinion.date)}</span>
                </div>
                <p class="text-sm text-gray-600 mb-2">Reference: ${opinion.reference || 'N/A'}</p>
                ${opinion.pe ? `<p class="text-sm text-blue-600 mb-2">PE Number: ${opinion.pe}</p>` : ''}
                ${opinion.committee ? `<p class="text-sm text-blue-600 mb-2">Committee: ${Array.isArray(opinion.committee) ? opinion.committee.join(', ') : opinion.committee}</p>` : ''}
                ${opinion.procedure ? `<p class="text-xs text-gray-500 mb-2">Procedure: ${opinion.procedure}</p>` : ''}
                ${opinion.dossiers && opinion.dossiers.length > 0 ? 
                    `<div class="text-xs text-blue-600 mb-2">Related Dossiers: ${opinion.dossiers.join(', ')}</div>` : ''
                }
                ${opinion.formats && opinion.formats.length > 0 ? 
                    `<div class="mt-2">
                        <p class="text-xs text-gray-600 mb-1">Available formats:</p>
                        ${opinion.formats.map(format => 
                            `<a href="${format.url}" target="_blank" class="text-xs text-blue-500 hover:underline mr-3">
                                <i class="fas fa-file-${format.type.toLowerCase()} mr-1"></i>${format.type} ${format.size || ''}
                            </a>`
                        ).join('')}
                    </div>` : ''
                }
            </div>
        `).join('');
    } else {
        // For other categories with limited data
        itemsHtml = data.map((item, index) => `
            <div class="border-l-4 border-gray-500 pl-4 mb-4 hover:bg-gray-50 p-3 rounded-r">
                <h4 class="font-semibold text-gray-800">${item.type || categoryLabel}</h4>
                <p class="text-sm text-gray-600 mb-2">Count: ${item.count || 0}</p>
                ${item.description ? `<p class="text-sm text-gray-700 mb-2">${item.description}</p>` : ''}
                ${item.note ? `<p class="text-xs text-orange-600 mt-2 bg-orange-50 p-2 rounded border-l-2 border-orange-200">${item.note}</p>` : ''}
            </div>
        `).join('');
    }
    
    return `
        <div class="space-y-6">
            <div class="bg-blue-50 rounded-lg p-4 border border-blue-200">
                <h3 class="text-lg font-semibold text-blue-800 mb-2">Overview</h3>
                <p class="text-gray-700">
                    <span class="font-medium">${mepName}</span> 
                    <span class="font-bold text-blue-600">${mep && categoryKey ? (mep[categoryKey] || 0) : total_count}</span> ${categoryLabel.toLowerCase()} 
                    in the current parliamentary term.
                </p>
            </div>
            
            <div class="bg-white rounded-lg border">
                <div class="p-4 border-b bg-gray-50">
                    <h3 class="text-lg font-semibold text-gray-800">Detailed Records</h3>
                    <p class="text-sm text-gray-600">
                        Detailed Records
                    </p>
                </div>
                <div class="p-4 max-h-96 overflow-y-auto" id="records-container">
                    ${itemsHtml}
                </div>
                ${has_more ? `
                    <div class="p-4 border-t bg-gray-50 text-center">
                        <button class="load-more-btn inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                                data-category="${category}" 
                                data-category-label="${categoryLabel}" 
                                data-mep-name="${mepName}" 
                                data-offset="${offset + limit}">
                            <i class="fas fa-plus mr-2"></i>
                            Load More Records
                        </button>
                    </div>
                ` : ''}
            </div>
        </div>
    `;
}

function formatDate(dateString) {
    if (!dateString) return 'N/A';
    try {
        return new Date(dateString).toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short', 
            day: 'numeric'
        });
    } catch {
        return dateString;
    }
}

function getIncludesDescription(categoryKey) {
    const descriptions = {
        'speeches': '<li>Plenary speeches during debates</li><li>Official interventions on the floor</li><li>Speaking time and frequency</li>',
        'amendments': '<li>Legislative amendments proposed</li><li>Committee and plenary amendments</li><li>Amendment adoption rates</li>',
        'reports_rapporteur': '<li>Reports as main rapporteur</li><li>Committee reports and recommendations</li><li>Legislative initiatives led</li>',
        'reports_shadow': '<li>Reports as shadow rapporteur</li><li>Opposition or alternative positions</li><li>Cross-party collaboration</li>',
        'questions': '<li>Written questions to Commission</li><li>Parliamentary questions submitted</li><li>Response rates and follow-ups</li>',
        'motions': '<li>Motions for resolution proposed</li><li>Policy initiatives and statements</li><li>Parliamentary procedure motions</li>',
        'opinions_rapporteur': '<li>Committee opinions as rapporteur</li><li>Advisory positions on legislation</li><li>Expert recommendations</li>',
        'opinions_shadow': '<li>Shadow opinions and alternatives</li><li>Minority positions expressed</li><li>Cross-committee input</li>',
        'explanations': '<li>Explanations of voting behavior</li><li>Justifications for vote choices</li><li>Public voting record clarifications</li>'
    };
    
    return descriptions[categoryKey] || '<li>Parliamentary activity data</li><li>Official records and documentation</li>';
}

async function loadMoreRecords(button) {
    try {
        const category = button.dataset.category;
        const categoryLabel = button.dataset.categoryLabel;
        const mepName = button.dataset.mepName;
        const newOffset = parseInt(button.dataset.offset);
        
        // Show loading state
        const originalText = button.innerHTML;
        button.innerHTML = `
            <span class="inline-flex items-center">
                <svg class="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Loading more...
            </span>
        `;
        button.disabled = true;
        
        // Get URL parameters
        const urlParams = new URLSearchParams(window.location.search);
        const mepId = parseInt(urlParams.get('mep_id'));
        const term = parseInt(urlParams.get('term')) || 10;
        
        // Fetch more data using API server (handles correct file routing for all terms)
        const baseUrl = window.location.protocol + '//' + window.location.host;
        const response = await fetch(`${baseUrl}/api/mep/${mepId}/category/${category}?term=${term}&offset=${newOffset}&limit=15`);
        const result = await response.json();
        
        if (result.success && result.data.length > 0) {
            // Get the container and current content
            const container = document.getElementById('records-container');
            const buttonContainer = button.closest('.p-4');
            
            // Format new items based on category
            let newItemsHtml = '';
            
            if (category === 'speeches') {
                newItemsHtml = result.data.map((speech, index) => `
                    <div class="border-l-4 border-blue-500 pl-4 mb-4 hover:bg-gray-50 p-3 rounded-r">
                        <div class="flex justify-between items-start mb-2">
                            <h4 class="font-semibold text-gray-800 flex-1">${speech.title || 'Untitled Speech'}</h4>
                            <span class="text-xs text-gray-500 ml-2">${formatDate(speech.date)}</span>
                        </div>
                        <p class="text-sm text-gray-600 mb-2">Reference: ${speech.reference || 'N/A'}</p>
                        ${speech.dossiers && speech.dossiers.length > 0 ? 
                            `<div class="text-xs text-blue-600">Dossiers: ${speech.dossiers.join(', ')}</div>` : ''
                        }
                        ${speech.url ? 
                            `<a href="${speech.url}" target="_blank" class="text-xs text-blue-500 hover:underline inline-flex items-center mt-2">
                                <i class="fas fa-external-link-alt mr-1"></i>View Original
                            </a>` : ''
                        }
                    </div>
                `).join('');
            } else if (category === 'amendments') {
                newItemsHtml = result.data.map((amendment, index) => `
                    <div class="border-l-4 border-green-500 pl-4 mb-4 hover:bg-gray-50 p-3 rounded-r">
                        <div class="flex justify-between items-start mb-2">
                            <h4 class="font-semibold text-gray-800">Amendment ${amendment.seq || newOffset + index + 1}</h4>
                            <span class="text-xs text-gray-500">${formatDate(amendment.date)}</span>
                        </div>
                        <p class="text-sm text-gray-600 mb-2">Reference: ${amendment.reference || 'N/A'}</p>
                        <p class="text-sm text-gray-600 mb-2">Committee: ${amendment.committee ? amendment.committee.join(', ') : 'N/A'}</p>
                        ${amendment.location && amendment.location.length > 0 ? 
                            `<p class="text-xs text-gray-500 mb-2">Location: ${amendment.location.map(loc => Array.isArray(loc) ? loc.join(' - ') : loc).join('; ')}</p>` : ''
                        }
                        ${amendment.authors ? `<p class="text-xs text-blue-600 mb-2">Authors: ${amendment.authors}</p>` : ''}
                        ${amendment.old && amendment.old.length > 0 ? 
                            `<div class="mt-2 p-2 bg-red-50 rounded text-sm border-l-2 border-red-300">
                                <strong class="text-red-800">Original text:</strong><br>
                                <div class="text-gray-700 italic">${amendment.old.join(' ')}</div>
                            </div>` : ''
                        }
                        ${amendment.new && amendment.new.length > 0 ? 
                            `<div class="mt-2 p-2 bg-green-50 rounded text-sm border-l-2 border-green-300">
                                <strong class="text-green-800">Proposed amendment:</strong><br>
                                <div class="text-gray-700">${amendment.new.join(' ')}</div>
                            </div>` : ''
                        }
                        ${amendment.src ? 
                            `<a href="${amendment.src}" target="_blank" class="text-xs text-blue-500 hover:underline inline-flex items-center mt-2">
                                <i class="fas fa-external-link-alt mr-1"></i>View Original Document
                            </a>` : ''
                        }
                    </div>
                `).join('');
            } else if (category === 'questions' || category === 'questions_written') {
                newItemsHtml = result.data.map((question, index) => `
                    <div class="border-l-4 border-yellow-500 pl-4 mb-4 hover:bg-gray-50 p-3 rounded-r">
                        <div class="flex justify-between items-start mb-2">
                            <h4 class="font-semibold text-gray-800">${question.title || `Written Question ${newOffset + index + 1}`}</h4>
                            <span class="text-xs text-gray-500">${formatDate(question.date)}</span>
                        </div>
                        <p class="text-sm text-gray-600 mb-2">Reference: ${question.reference || 'N/A'}</p>
                        ${question.addressee ? `<p class="text-sm text-blue-600 mb-2">To: ${question.addressee}</p>` : ''}
                        ${question.subject ? `<p class="text-sm text-gray-700 mb-2"><strong>Subject:</strong> ${question.subject}</p>` : ''}
                        ${question.text ? `
                            <div class="mt-2 p-2 bg-yellow-50 rounded text-sm border-l-2 border-yellow-300">
                                <strong>Question:</strong> ${question.text.length > 200 ? question.text.substring(0, 200) + '...' : question.text}
                            </div>
                        ` : ''}
                        ${question.url ? `<p class="mt-2"><a href="${question.url}" target="_blank" class="text-blue-600 hover:underline text-sm">View Document</a></p>` : ''}
                    </div>
                `).join('');
            } else if (category === 'questions_oral') {
                newItemsHtml = result.data.map((question, index) => `
                    <div class="border-l-4 border-orange-500 pl-4 mb-4 hover:bg-gray-50 p-3 rounded-r">
                        <div class="flex justify-between items-start mb-2">
                            <h4 class="font-semibold text-gray-800">${question.title || `Oral Question ${newOffset + index + 1}`}</h4>
                            <span class="text-xs text-gray-500">${formatDate(question.date)}</span>
                        </div>
                        <p class="text-sm text-gray-600 mb-2">Reference: ${question.reference || 'N/A'}</p>
                        ${question.subject ? `<p class="text-sm text-gray-700 mb-2"><strong>Subject:</strong> ${question.subject}</p>` : ''}
                        ${question.text ? `
                            <div class="mt-2 p-2 bg-orange-50 rounded text-sm border-l-2 border-orange-300">
                                <strong class="text-yellow-800">Question text:</strong><br>
                                <div class="text-gray-700">${Array.isArray(question.text) ? question.text.join(' ') : question.text}</div>
                            </div>
                        ` : ''}
                        ${question.url ? 
                            `<a href="${question.url}" target="_blank" class="text-xs text-blue-500 hover:underline inline-flex items-center mt-2">
                                <i class="fas fa-external-link-alt mr-1"></i>View Original Question
                            </a>` : ''
                        }
                    </div>
                `).join('');
            } else if (category === 'motions') {
                newItemsHtml = result.data.map((motion, index) => `
                    <div class="border-l-4 border-purple-500 pl-4 mb-4 hover:bg-gray-50 p-3 rounded-r">
                        <div class="flex justify-between items-start mb-2">
                            <h4 class="font-semibold text-gray-800">${motion.title || `Motion ${newOffset + index + 1}`}</h4>
                            <span class="text-xs text-gray-500">${formatDate(motion['Date opened'] || motion.date)}</span>
                        </div>
                        ${motion.authors ? `<p class="text-sm text-blue-600 mb-2">Authors: ${motion.authors}</p>` : ''}
                        ${motion['Number of signatories'] ? 
                            `<p class="text-sm text-green-600 mb-2">Signatories: ${motion['Number of signatories']}</p>` : ''
                        }
                        ${motion['Lapse date'] ? 
                            `<p class="text-xs text-gray-500 mb-2">Lapse date: ${formatDate(motion['Lapse date'])}</p>` : ''
                        }
                        ${motion.formats && motion.formats.length > 0 ? 
                            `<div class="mt-2">
                                <p class="text-xs text-gray-600 mb-1">Available formats:</p>
                                ${motion.formats.map(format => 
                                    `<a href="${format.url}" target="_blank" class="text-xs text-blue-500 hover:underline mr-3">
                                        <i class="fas fa-file-${format.type.toLowerCase()} mr-1"></i>${format.type} ${format.size || ''}
                                    </a>`
                                ).join('')}
                            </div>` : ''
                        }
                    </div>
                `).join('');
            } else if (category === 'explanations') {
                newItemsHtml = result.data.map((explanation, index) => `
                    <div class="border-l-4 border-indigo-500 pl-4 mb-4 hover:bg-gray-50 p-3 rounded-r">
                        <div class="flex justify-between items-start mb-2">
                            <h4 class="font-semibold text-gray-800">${explanation.title || 'Explanation of Vote'}</h4>
                            <span class="text-xs text-gray-500">${formatDate(explanation.date)}</span>
                        </div>
                        ${explanation.reference ? 
                            `<p class="text-sm text-gray-600 mb-2">Reference: ${explanation.reference}</p>` : ''
                        }
                        ${explanation.text ? `
                            <div class="mt-2 p-3 bg-indigo-50 rounded text-sm border-l-2 border-indigo-300">
                                <strong class="text-indigo-800">Explanation:</strong><br>
                                <div class="text-gray-700 mt-1">${explanation.text.length > 300 ? explanation.text.substring(0, 300) + '...' : explanation.text}</div>
                                ${explanation.text.length > 300 ? 
                                    `<button class="text-indigo-600 hover:text-indigo-800 text-xs mt-2 underline" onclick="this.previousElementSibling.textContent='${explanation.text.replace(/'/g, "\\'")}'; this.style.display='none';">Show full text</button>` : ''
                                }
                            </div>
                        ` : ''}
                        ${explanation.dossiers && explanation.dossiers.length > 0 ? 
                            `<div class="text-xs text-blue-600 mb-2 mt-2">Related Dossiers: ${explanation.dossiers.join(', ')}</div>` : ''
                        }
                        ${explanation.url ? 
                            `<a href="${explanation.url}" target="_blank" class="text-xs text-blue-500 hover:underline inline-flex items-center mt-2">
                                <i class="fas fa-external-link-alt mr-1"></i>View Original Explanation
                            </a>` : ''
                        }
                    </div>
                `).join('');
            } else {
                // For other categories, use generic formatting
                newItemsHtml = result.data.map((item, index) => `
                    <div class="border-l-4 border-gray-500 pl-4 mb-4 hover:bg-gray-50 p-3 rounded-r">
                        <h4 class="font-semibold text-gray-800">${item.title || item.type || `Item ${newOffset + index + 1}`}</h4>
                        <p class="text-sm text-gray-600">${formatDate(item.date)}</p>
                        ${item.count ? `<p class="text-sm text-blue-600">Count: ${item.count}</p>` : ''}
                        ${item.note ? `<p class="text-xs text-orange-600">${item.note}</p>` : ''}
                    </div>
                `).join('');
            }
            
            // Append new items to container
            container.insertAdjacentHTML('beforeend', newItemsHtml);
            
            // Keep the display as "Detailed Records" - no count updates needed
            
            // Update or remove the load more button
            if (result.has_more) {
                button.innerHTML = originalText;
                button.disabled = false;
                button.dataset.offset = newOffset + result.limit;
            } else {
                buttonContainer.remove();
            }
        } else {
            // No more data
            button.closest('.p-4').remove();
        }
        
    } catch (error) {
        console.error('Error loading more records:', error);
        button.innerHTML = originalText;
        button.disabled = false;
        
        // Show error message
        const errorDiv = document.createElement('div');
        errorDiv.className = 'bg-red-50 rounded-lg p-4 border border-red-200 mt-4';
        errorDiv.innerHTML = `
            <h3 class="text-lg font-semibold text-red-800 mb-2">Error Loading More Records</h3>
            <p class="text-red-700">Failed to load additional records: ${error.message}</p>
            <p class="text-sm text-red-600 mt-2">Please check your connection and try again.</p>
        `;
        button.parentNode.insertBefore(errorDiv, button);
    }
}

// Score breakdown modal functionality now handled by unified score-breakdown.js module

// Score breakdown HTML generation now handled by unified score-breakdown.js module
function generateScoreBreakdownHTML(mep) {
    // This function is deprecated - use unified score-breakdown.js module instead
    return '';
    
    /* Unreachable code commented out
    // MEP Score Methodology breakdown
    html += `
        <div class="score-breakdown-section">
            <h3><i class="fas fa-info-circle mr-2"></i>MEP Score Methodology</h3>
            <p class="text-sm text-gray-600 mb-4">
                Score calculated using MEP Score methodology with dynamic ranges (October 2017) adapted to each term's activity levels. Includes 
                4 categories: Reports, Statements, Roles, and Attendance.
            </p>
        </div>
    `;
    
    // Reports Category
    html += `
        <div class="score-breakdown-section">
            <h3><i class="fas fa-file-alt mr-2"></i>Reports Category</h3>
            <table class="score-breakdown-table">
                <thead>
                    <tr>
                        <th>Type</th>
                        <th>Count</th>
                        <th>Points Each</th>
                        <th>Score</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>Reports (Rapporteur)</td>
                        <td>${mep.reports_rapporteur || 0}</td>
                        <td>4.0</td>
                        <td>${(mep.score_reports_rap || 0).toFixed(1)}</td>
                    </tr>
                    <tr>
                        <td>Reports (Shadow)</td>
                        <td>${mep.reports_shadow || 0}</td>
                        <td>1.0</td>
                        <td>${(mep.score_reports_shadow || 0).toFixed(1)}</td>
                    </tr>
                    <tr>
                        <td>Opinions (Rapporteur)</td>
                        <td>${mep.opinions_rapporteur || 0}</td>
                        <td>1.0</td>
                        <td>${(mep.score_opinions_rap || 0).toFixed(1)}</td>
                    </tr>
                    <tr>
                        <td>Opinions (Shadow)</td>
                        <td>${mep.opinions_shadow || 0}</td>
                        <td>0.5</td>
                        <td>${(mep.score_opinions_shadow || 0).toFixed(1)}</td>
                    </tr>
                    <tr class="category-total">
                        <td><strong>Reports Total</strong></td>
                        <td colspan="2"></td>
                        <td><strong>${((mep.score_reports_rap || 0) + (mep.score_reports_shadow || 0) + (mep.score_opinions_rap || 0) + (mep.score_opinions_shadow || 0)).toFixed(1)}</strong></td>
                    </tr>
                </tbody>
            </table>
        </div>
    `;
    
    // Statements Category
    html += `
        <div class="score-breakdown-section">
            <h3><i class="fas fa-comments mr-2"></i>Statements Category</h3>
            <table class="score-breakdown-table">
                <thead>
                    <tr>
                        <th>Type</th>
                        <th>Count</th>
                        <th>Range Score</th>
                        <th>Score</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>Speeches</td>
                        <td>${mep.speeches || 0}</td>
                        <td>Dynamic ranges (term-based)</td>
                        <td>${(mep.score_speeches || 0).toFixed(1)}</td>
                    </tr>
                    <tr>
                        <td>Explanations of Vote</td>
                        <td>${mep.explanations || 0}</td>
                        <td>Dynamic ranges (term-based)</td>
                        <td>${(mep.score_explanations || 0).toFixed(1)}</td>
                    </tr>
                    <tr>
                        <td>Questions</td>
                        <td>${mep.questions || 0}</td>
                        <td>0.1 each (max 3 pts)</td>
                        <td>${(mep.score_questions || 0).toFixed(1)}</td>
                    </tr>
                    <tr>
                        <td>Motions</td>
                        <td>${mep.motions || 0}</td>
                        <td>0.1 each (max 3 pts)</td>
                        <td>${(mep.score_motions || 0).toFixed(1)}</td>
                    </tr>
                    <tr>
                        <td>Amendments</td>
                        <td>${mep.amendments || 0}</td>
                        <td>Logarithmic scaling (max 6 pts)</td>
                        <td>${(mep.score_amend || 0).toFixed(1)}</td>
                    </tr>
                    <tr class="category-total">
                        <td><strong>Control & Transparency Total</strong></td>
                        <td colspan="2"></td>
                        <td><strong>${((mep.score_questions || 0) + (mep.score_motions || 0) + (mep.score_explanations || 0)).toFixed(1)}</strong></td>
                    </tr>
                </tbody>
            </table>
        </div>
    `;
    
    // Engagement & Presence Category
    html += `
        <div class="score-breakdown-section">
            <h3><i class="fas fa-users mr-2"></i>Engagement & Presence</h3>
            <table class="score-breakdown-table">
                <tbody>
                    <tr>
                        <td>Speeches Score</td>
                        <td>${(mep.score_speeches || 0).toFixed(1)}</td>
                    </tr>
                    <tr>
                        <td>Voting Attendance (${((mep.vote_attendance_percentage || mep.attendance_rate || 0) * 100).toFixed(1)}%)</td>
                        <td>${(mep.score_votes || 0).toFixed(1)}</td>
                    </tr>
                    <tr class="category-total">
                        <td><strong>Engagement & Presence Total</strong></td>
                        <td><strong>${((mep.score_speeches || 0) + (mep.score_votes || 0)).toFixed(1)}</strong></td>
                    </tr>
                </tbody>
            </table>
        </div>
    `;
    
    // Institutional Roles
    html += `
        <div class="score-breakdown-section">
            <h3><i class="fas fa-crown mr-2"></i>Institutional Roles</h3>
            <table class="score-breakdown-table">
                <tbody>
                    <tr>
                        <td>Top Role</td>
                        <td>${mep.top_role || 'none'}</td>
                    </tr>
                    <tr>
                        <td>Role Multiplier</td>
                        <td>${(mep.institutional_roles_multiplier || 1.0).toFixed(3)}</td>
                    </tr>
                    <tr>
                        <td>Role Percentage Bonus</td>
                        <td>${(mep.roles_percentage || 0).toFixed(1)}%</td>
                    </tr>
                    <tr class="category-total">
                        <td><strong>Score with Roles</strong></td>
                        <td><strong>${(mep.score_with_roles || 0).toFixed(1)}</strong></td>
                    </tr>
                </tbody>
            </table>
        </div>
    `;
    
    // Final Score Summary using new outlier-based scoring fields
    const legislativeScore = mep.legislative_production_score || 0;
    const controlScore = mep.control_transparency_score || 0;
    const engagementScore = mep.engagement_presence_score || 0;
    const baseScore = mep.base_score || 0;
    const rolesMultiplier = mep.institutional_roles_multiplier || 1.0;
    
    html += `
        <div class="score-breakdown-section">
            <h3><i class="fas fa-calculator mr-2"></i>Final Score Calculation</h3>
            <table class="score-breakdown-table">
                <tbody>
                    <tr>
                        <td>Legislative Production</td>
                        <td>${legislativeScore.toFixed(1)} pts</td>
                    </tr>
                    <tr>
                        <td>Control & Transparency</td>
                        <td>${controlScore.toFixed(1)} pts</td>
                    </tr>
                    <tr>
                        <td>Engagement & Presence</td>
                        <td>${engagementScore.toFixed(1)} pts</td>
                    </tr>
                    <tr>
                        <td>Base Score (Categories 1-3)</td>
                        <td>${baseScore.toFixed(1)} pts</td>
                    </tr>
                    <tr>
                        <td>× Institutional Roles Multiplier</td>
                        <td>×${rolesMultiplier.toFixed(2)}</td>
                    </tr>
                    <tr>
                        <td>Score with Roles</td>
                        <td>${(mep.score_with_roles || 0).toFixed(1)} pts</td>
                    </tr>
                    <tr>
                        <td>× Attendance Penalty</td>
                        <td>×${(mep.attendance_penalty || 1.0).toFixed(2)}</td>
                    </tr>
                    <tr class="category-total">
                        <td><strong>Final Score</strong></td>
                        <td><strong>${(mep.final_score || 0).toFixed(1)} pts</strong></td>
                    </tr>
                </tbody>
            </table>
        </div>
    `;
    
    // Final Score Summary
    html += `
        <div class="score-breakdown-section">
            <h3><i class="fas fa-trophy mr-2"></i>Score Summary</h3>
            <div class="bg-blue-50 p-4 rounded-lg">
                <div class="text-lg font-semibold text-center mb-2">
                    Final MEP Score: <span class="text-blue-600">${(mep.score || 0).toFixed(1)}</span>
                </div>
                <div class="text-center text-sm text-gray-600">
                    Rank: #${mep.rank || 'N/A'} in Term ${term}
                </div>
            </div>
        </div>
    `;
    
    return html;
    */
}

// Score modal initialization now handled by unified score-breakdown.js module