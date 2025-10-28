/**
 * Unified Score Breakdown Module
 * Provides consistent score breakdown display for both index and profile pages
 * Uses new 4-category methodology: Legislative Production, Control & Transparency, 
 * Engagement & Presence, and Institutional Roles
 */

/**
 * Generate HTML for the score breakdown modal content
 * @param {Object} mep - MEP data object with scores
 * @returns {string} HTML content for the modal
 */
export function generateScoreBreakdownHTML(mep) {
    const hasScores = mep.final_score !== undefined;
    
    if (!hasScores) {
        return `
            <div class="text-center p-8">
                <i class="fas fa-exclamation-triangle text-gray-500 text-4xl mb-4"></i>
                <h3 class="text-lg font-semibold text-gray-700 mb-2">Score data not available</h3>
                <p class="text-gray-600">Unable to load detailed score breakdown for this MEP.</p>
            </div>
        `;
    }

    return `
        <div class="space-y-6">
            <!-- Score Overview -->
            <div class="bg-gray-50 rounded-lg p-4 border border-gray-200">
                <div class="flex items-center justify-between">
                    <div>
                        <h3 class="text-lg font-semibold text-gray-800">Final Score</h3>
                        <p class="text-sm text-gray-600">Based on 4-category methodology</p>
                    </div>
                    <div class="text-right">
                        <div class="text-3xl font-bold text-gray-800">${mep.final_score?.toFixed(1) || '0.0'}</div>
                        <div class="text-sm text-gray-600">out of ~100</div>
                    </div>
                </div>
            </div>

            <!-- 1. Legislative Production -->
            <div class="score-breakdown-section">
                <h3 class="flex items-center text-lg font-semibold text-gray-800 mb-3">
                    <i class="fas fa-gavel mr-2"></i>
                    1. Legislative Production
                    <span class="ml-auto text-lg font-bold">${mep.legislative_production_score?.toFixed(1) || '0.0'} pts</span>
                </h3>
                <p class="text-sm text-gray-600 mb-3">Measures active participation in European legislation through reports, opinions, and amendments.</p>
                
                <table class="score-breakdown-table">
                    <thead>
                        <tr>
                            <th>Activity</th>
                            <th class="text-center">Count</th>
                            <th class="text-center">Points Each</th>
                            <th class="text-right">Total Points</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td>Reports (Rapporteur)</td>
                            <td class="text-center">${mep.reports_rapporteur || 0}</td>
                            <td class="text-center">4.0</td>
                            <td class="text-right">${mep.reports_rapporteur_score?.toFixed(1) || '0.0'}</td>
                        </tr>
                        <tr>
                            <td>Reports (Shadow)</td>
                            <td class="text-center">${mep.reports_shadow || 0}</td>
                            <td class="text-center">1.0</td>
                            <td class="text-right">${mep.reports_shadow_score?.toFixed(1) || '0.0'}</td>
                        </tr>
                        <tr>
                            <td>Opinions (Rapporteur)</td>
                            <td class="text-center">${mep.opinions_rapporteur || 0}</td>
                            <td class="text-center">1.0</td>
                            <td class="text-right">${mep.opinions_rapporteur_score?.toFixed(1) || '0.0'}</td>
                        </tr>
                        <tr>
                            <td>Opinions (Shadow)</td>
                            <td class="text-center">${mep.opinions_shadow || 0}</td>
                            <td class="text-center">0.5</td>
                            <td class="text-right">${mep.opinions_shadow_score?.toFixed(1) || '0.0'}</td>
                        </tr>
                        <tr>
                            <td>Amendments</td>
                            <td class="text-center">${mep.amendments || 0}</td>
                            <td class="text-center">Outlier-based (0-4)</td>
                            <td class="text-right">${mep.amendments_score?.toFixed(1) || '0.0'}</td>
                        </tr>
                        <tr class="axis-total">
                            <td colspan="3"><strong>Legislative Production Total</strong></td>
                            <td class="text-right"><strong>${mep.legislative_production_score?.toFixed(1) || '0.0'}</strong></td>
                        </tr>
                    </tbody>
                </table>
            </div>

            <!-- 2. Control & Transparency -->
            <div class="score-breakdown-section">
                <h3 class="flex items-center text-lg font-semibold text-gray-800 mb-3">
                    <i class="fas fa-search mr-2"></i>
                    2. Control & Transparency
                    <span class="ml-auto text-lg font-bold">${mep.control_transparency_score?.toFixed(1) || '0.0'} pts</span>
                </h3>
                <p class="text-sm text-gray-600 mb-3">Measures oversight activities and transparency through questions and explanations of votes.</p>
                
                <table class="score-breakdown-table">
                    <thead>
                        <tr>
                            <th>Activity</th>
                            <th class="text-center">Count</th>
                            <th class="text-center">Scoring Method</th>
                            <th class="text-right">Total Points</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td>Oral Questions</td>
                            <td class="text-center">${mep.questions_oral || 0}</td>
                            <td class="text-center">Outlier-based (0-4)</td>
                            <td class="text-right">${mep.oral_questions_score?.toFixed(1) || '0.0'}</td>
                        </tr>
                        <tr>
                            <td>Written Questions</td>
                            <td class="text-center">${mep.questions_written || 0}</td>
                            <td class="text-center">Outlier-based (0-4)</td>
                            <td class="text-right">${mep.written_questions_score?.toFixed(1) || '0.0'}</td>
                        </tr>
                        <tr>
                            <td>Explanations of Vote</td>
                            <td class="text-center">${mep.explanations || 0}</td>
                            <td class="text-center">Outlier-based (0-4)</td>
                            <td class="text-right">${mep.explanations_score?.toFixed(1) || '0.0'}</td>
                        </tr>
                        <tr class="axis-total">
                            <td colspan="3"><strong>Control & Transparency Total</strong></td>
                            <td class="text-right"><strong>${mep.control_transparency_score?.toFixed(1) || '0.0'}</strong></td>
                        </tr>
                    </tbody>
                </table>
            </div>

            <!-- 3. Engagement & Presence -->
            <div class="score-breakdown-section">
                <h3 class="flex items-center text-lg font-semibold text-gray-800 mb-3">
                    <i class="fas fa-users mr-2"></i>
                    3. Engagement & Presence
                    <span class="ml-auto text-lg font-bold">${mep.engagement_presence_score?.toFixed(1) || '0.0'} pts</span>
                </h3>
                <p class="text-sm text-gray-600 mb-3">Measures active participation in parliamentary sessions through speeches, motions for resolutions, and voting attendance.</p>
                
                <table class="score-breakdown-table">
                    <thead>
                        <tr>
                            <th>Activity</th>
                            <th class="text-center">Count</th>
                            <th class="text-center">Scoring Method</th>
                            <th class="text-right">Total Points</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td>Plenary Speeches</td>
                            <td class="text-center">${mep.speeches || 0}</td>
                            <td class="text-center">Outlier-based (0-4)</td>
                            <td class="text-right">${mep.speeches_score?.toFixed(1) || '0.0'}</td>
                        </tr>
                        <tr>
                            <td>Motions for Resolutions</td>
                            <td class="text-center">${mep.motions || 0}</td>
                            <td class="text-center">${(mep.motions || 0) === 0 ? 'No motions' : 'Outlier-based (0-4)'}</td>
                            <td class="text-right">${(mep.motions || 0) === 0 ? '—' : (((mep.engagement_presence_score || 0) - (mep.speeches_score || 0)).toFixed(1))}</td>
                        </tr>
                        <tr class="axis-total">
                            <td colspan="3"><strong>Engagement & Presence Total</strong></td>
                            <td class="text-right"><strong>${mep.engagement_presence_score?.toFixed(1) || '0.0'}</strong></td>
                        </tr>
                    </tbody>
                </table>
            </div>


            <!-- 4. Institutional Roles -->
            <div class="score-breakdown-section">
                <h3 class="flex items-center text-lg font-semibold text-gray-800 mb-3">
                    <i class="fas fa-crown mr-2"></i>
                    4. Institutional Roles
                    <span class="ml-auto text-lg font-bold">×${mep.institutional_roles_multiplier?.toFixed(2) || '1.00'}</span>
                </h3>
                <p class="text-sm text-gray-600 mb-3">Leadership positions receive percentage bonuses using Power × Scarcity heuristic.</p>
                
                <div class="bg-gray-50 border border-gray-200 rounded-lg p-4 mb-4">
                    <h4 class="font-semibold text-gray-800 mb-2">Power × Scarcity Heuristic</h4>
                    <p class="text-sm text-gray-700 mb-2">
                        <strong>bonus ≈ relative authority / share of MEPs in role</strong>
                    </p>
                    <p class="text-xs text-gray-700">
                        The rarer and more powerful the office, the bigger the premium. Roles that can alter legislation 
                        (President, Committee Chair) are weighted highest. Administrative roles (Quaestor) or diplomatic 
                        roles (delegations) receive discounts.
                    </p>
                </div>
                
                <table class="score-breakdown-table">
                    <thead>
                        <tr>
                            <th>Position</th>
                            <th class="text-center">Held</th>
                            <th class="text-center">Bonus</th>
                            <th class="text-right">Applied</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td>EP President</td>
                            <td class="text-center">${mep.ep_president ? '✓' : '✗'}</td>
                            <td class="text-center">+100%</td>
                            <td class="text-right">${mep.ep_president ? '+100%' : '—'}</td>
                        </tr>
                        <tr>
                            <td>EP Vice-President</td>
                            <td class="text-center">${mep.ep_vice_president ? '✓' : '✗'}</td>
                            <td class="text-center">+25%</td>
                            <td class="text-right">${mep.ep_vice_president ? '+25%' : '—'}</td>
                        </tr>
                        <tr>
                            <td>Committee Chair</td>
                            <td class="text-center">${mep.committee_chair ? '✓' : '✗'}</td>
                            <td class="text-center">+15%</td>
                            <td class="text-right">${mep.committee_chair ? '+15%' : '—'}</td>
                        </tr>
                        <tr>
                            <td>Quaestor</td>
                            <td class="text-center">${mep.ep_quaestor ? '✓' : '✗'}</td>
                            <td class="text-center">+25%</td>
                            <td class="text-right">${mep.ep_quaestor ? '+25%' : '—'}</td>
                        </tr>
                        <tr>
                            <td>Committee Vice-Chair</td>
                            <td class="text-center">${mep.committee_vice_chair ? '✓' : '✗'}</td>
                            <td class="text-center">+15%</td>
                            <td class="text-right">${mep.committee_vice_chair ? '+15%' : '—'}</td>
                        </tr>
                        <tr>
                            <td>Delegation Chair</td>
                            <td class="text-center">${mep.delegation_chair ? '✓' : '✗'}</td>
                            <td class="text-center">+10%</td>
                            <td class="text-right">${mep.delegation_chair ? '+10%' : '—'}</td>
                        </tr>
                        <tr>
                            <td>Delegation Vice-Chair</td>
                            <td class="text-center">${mep.delegation_vice_chair ? '✓' : '✗'}</td>
                            <td class="text-center">+7.5%</td>
                            <td class="text-right">${mep.delegation_vice_chair ? '+7.5%' : '—'}</td>
                        </tr>
                        <tr class="axis-total">
                            <td colspan="3"><strong>Highest Role Multiplier</strong></td>
                            <td class="text-right"><strong>×${mep.institutional_roles_multiplier?.toFixed(2) || '1.00'}</strong></td>
                        </tr>
                    </tbody>
                </table>
            </div>

            <!-- Final Calculation -->
            <div class="score-breakdown-section">
                <h3 class="text-lg font-semibold text-gray-900 mb-3">
                    <i class="fas fa-calculator mr-2"></i>
                    Final Score Calculation
                </h3>
                
                <table class="score-breakdown-table">
                    <tbody>
                        <tr>
                            <td>Base Score (Categories 1-3)</td>
                            <td class="text-right">${mep.base_score?.toFixed(1) || '0.0'}</td>
                        </tr>
                        <tr>
                            <td>× Institutional Roles Multiplier</td>
                            <td class="text-right">×${mep.institutional_roles_multiplier?.toFixed(2) || '1.00'}</td>
                        </tr>
                        <tr>
                            <td>Score with Roles</td>
                            <td class="text-right">${mep.score_with_roles?.toFixed(1) || '0.0'}</td>
                        </tr>
                        <tr>
                            <td>× Attendance Penalty</td>
                            <td class="text-right">×${mep.attendance_penalty?.toFixed(2) || '1.00'} ${mep.attendance_penalty < 1.0 ? `(${((1 - mep.attendance_penalty) * 100).toFixed(0)}% reduction)` : '(no penalty)'}</td>
                        </tr>
                        ${(mep.committee_chair > 0 || mep.committee_vice_chair > 0 || mep.ep_president > 0 || mep.ep_vice_president > 0) ? `
                        <tr class="text-xs">
                            <td colspan="2" class="text-center text-gray-600 italic">
                                <i class="fas fa-info-circle mr-1"></i>
                                Presiding officer: exempt from attendance penalties
                            </td>
                        </tr>
                        ` : ''}
                        <tr class="final-score-row">
                            <td><strong>Final Score</strong></td>
                            <td class="text-right"><strong>${mep.final_score?.toFixed(1) || '0.0'}</strong></td>
                        </tr>
                    </tbody>
                </table>
            </div>

            <!-- Voting Attendance Penalty -->
            <div class="score-breakdown-section">
                <h3 class="flex items-center text-lg font-semibold text-gray-800 mb-3">
                    <i class="fas fa-calendar-check mr-2"></i>
                    Voting Attendance Penalty
                    <span class="ml-auto text-lg font-bold">${((mep.vote_attendance_percentage || mep.attendance_rate || 0) * 100).toFixed(1)}%</span>
                </h3>
                <p class="text-sm text-gray-600 mb-3">Democratic representation requires presence. Attendance penalties are applied to final scores based on voting participation.</p>
                
                <div class="bg-gray-50 border border-gray-200 rounded-lg p-4 mb-4">
                    <div class="grid grid-cols-3 gap-4 text-sm">
                        <div class="text-center">
                            <div class="font-semibold text-gray-800">${mep.votes_attended || 0}</div>
                            <div class="text-gray-600">Votes Attended</div>
                        </div>
                        <div class="text-center">
                            <div class="font-semibold text-gray-800">${mep.votes_total || 0}</div>
                            <div class="text-gray-600">Total Votes</div>
                        </div>
                        <div class="text-center">
                            <div class="font-semibold ${((mep.vote_attendance_percentage || mep.attendance_rate || 0) * 100) >= 75 ? 'text-green-600' : ((mep.vote_attendance_percentage || mep.attendance_rate || 0) * 100) >= 55 ? 'text-orange-600' : 'text-red-600'}">
                                ${((mep.vote_attendance_percentage || mep.attendance_rate || 0) * 100).toFixed(1)}%
                            </div>
                            <div class="text-gray-600">Attendance Rate</div>
                        </div>
                    </div>
                </div>

                <table class="score-breakdown-table">
                    <thead>
                        <tr>
                            <th>Attendance Level</th>
                            <th class="text-center">Threshold</th>
                            <th class="text-center">Penalty Applied</th>
                            <th class="text-right">Status</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr class="${((mep.vote_attendance_percentage || mep.attendance_rate || 0) * 100) >= 75 ? 'bg-green-50' : ''}">
                            <td>Good Attendance</td>
                            <td class="text-center">≥75%</td>
                            <td class="text-center">No penalty</td>
                            <td class="text-right">${((mep.vote_attendance_percentage || mep.attendance_rate || 0) * 100) >= 75 ? '✓ Current' : '—'}</td>
                        </tr>
                        <tr class="${(((mep.vote_attendance_percentage || mep.attendance_rate || 0) * 100) < 75 && ((mep.vote_attendance_percentage || mep.attendance_rate || 0) * 100) >= 55) ? 'bg-orange-50' : ''}">
                            <td>Poor Attendance</td>
                            <td class="text-center">&lt;75%</td>
                            <td class="text-center">25% score reduction</td>
                            <td class="text-right">${(((mep.vote_attendance_percentage || mep.attendance_rate || 0) * 100) < 75 && ((mep.vote_attendance_percentage || mep.attendance_rate || 0) * 100) >= 55) ? '⚠ Current' : '—'}</td>
                        </tr>
                        <tr class="${((mep.vote_attendance_percentage || mep.attendance_rate || 0) * 100) < 55 ? 'bg-red-50' : ''}">
                            <td>Very Poor Attendance</td>
                            <td class="text-center">&lt;55%</td>
                            <td class="text-center">50% score reduction</td>
                            <td class="text-right">${((mep.vote_attendance_percentage || mep.attendance_rate || 0) * 100) < 55 ? '🚨 Current' : '—'}</td>
                        </tr>
                    </tbody>
                </table>
                
                ${(mep.committee_chair > 0 || mep.committee_vice_chair > 0 || mep.ep_president > 0 || mep.ep_vice_president > 0) ? `
                <div class="bg-blue-50 border border-blue-200 rounded-lg p-3 mt-4">
                    <div class="flex items-center text-sm text-blue-800">
                        <i class="fas fa-info-circle mr-2"></i>
                        <strong>Exemption: EP Chair and Vice Chair are exempt from attendance penalties as they usually do not participate in votes when presiding over plenary sessions.</strong>
                    </div>
                </div>
                ` : ''}
            </div>

            <!-- Methodology Link -->
            <div class="text-center pt-4">
                <a href="methodology.html" target="_blank" class="inline-flex items-center px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 transition-colors">
                    <i class="fas fa-book mr-2"></i>
                    View Full Methodology
                </a>
            </div>
        </div>
    `;
}

/**
 * Show the score breakdown modal
 * @param {number|Object} mepData - Either MEP ID or MEP data object
 * @param {Array} allMeps - Array of all MEPs (needed if mepData is ID)
 */
export function showScoreBreakdown(mepData, allMeps = null) {
    let mep;
    
    if (typeof mepData === 'number') {
        // mepData is an ID, find the MEP in allMeps
        mep = allMeps?.find(m => m.mep_id === mepData);
        if (!mep) {
            console.error('MEP not found:', mepData);
            return;
        }
    } else {
        // mepData is the MEP object
        mep = mepData;
    }
    
    const modal = document.getElementById('score-modal');
    const modalMepName = document.getElementById('modal-mep-name');
    const modalContent = document.getElementById('modal-content');
    
    if (!modal || !modalMepName || !modalContent) {
        console.error('Modal elements not found');
        return;
    }
    
    modalMepName.textContent = `Score Breakdown - ${mep.full_name}`;
    modalContent.innerHTML = generateScoreBreakdownHTML(mep);
    
    // Handle different modal implementations
    if (modal.classList.contains('hidden')) {
        // Profile page uses Tailwind classes
        modal.classList.remove('hidden');
        modal.classList.add('flex');
    } else {
        // Index page uses custom CSS classes
        modal.classList.add('active');
    }
}

/**
 * Hide the score breakdown modal
 */
export function hideScoreBreakdown() {
    const modal = document.getElementById('score-modal');
    if (modal) {
        // Handle different modal implementations
        if (modal.classList.contains('flex')) {
            // Profile page uses Tailwind classes
            modal.classList.remove('flex');
            modal.classList.add('hidden');
        } else {
            // Index page uses custom CSS classes
            modal.classList.remove('active');
        }
    }
}

/**
 * Initialize score breakdown modal functionality
 * Should be called once when the page loads
 */
export function initializeScoreBreakdownModal() {
    const modal = document.getElementById('score-modal');
    const closeBtn = document.getElementById('modal-close');
    
    if (!modal || !closeBtn) {
        console.error('Score breakdown modal elements not found');
        return;
    }
    
    // Close button click
    closeBtn.addEventListener('click', hideScoreBreakdown);
    
    // Click outside modal to close
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            hideScoreBreakdown();
        }
    });
    
    // Escape key to close
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && (modal.classList.contains('active') || modal.classList.contains('flex'))) {
            hideScoreBreakdown();
        }
    });
}