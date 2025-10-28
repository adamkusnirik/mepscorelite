# **MEP Score Methodology**

Transparent scoring system for European Parliament member activities based on open data, weighted by their importance in performing the European Parliament mandate.

## **Philosophy**

The weighting of individual indicators largely draws from the weights established by MEP Ranking, which was previously widely cited and recognized but is no longer operational, as well as from practical work experience in the European Parliament.

### **Core Principles**

**Reports and Opinions are the most important**, as MEPs have the greatest impact on how legislation will look at the end - the highest possible gains. This forms the foundation of our Legislative Production category, where MEPs can directly shape European Union law through their role as rapporteurs and opinion drafters.

**Activity Indicators Scoring** reflects the day-to-day parliamentary work that demonstrates MEP engagement and accountability. These quantifiable activities show how actively MEPs participate in the democratic process through questions, speeches, and legislative amendments.

**Institutional Roles** recognize that some MEPs carry additional responsibilities beyond regular legislative work. Leadership positions require extra time and effort, and the scoring system acknowledges this through carefully calibrated multipliers based on the Power × Scarcity principle.

**Attendance Penalty** ensures that the fundamental duty of parliamentary participation is reflected in scores. Democratic representation requires physical presence and participation in votes, making attendance a baseline requirement for effective MEP performance.

### **Transparency Commitment**

The methodology is transparent. All data processing and calculation methods are documented and verifiable, ensuring accountability and enabling independent verification of results.

We strive to identify potential errors and correct them after verification.

MEP evaluation is based on four distinct categories of parliamentary activity. Each category measures different aspects of MEP performance to provide a better assessment.

## **4-Category System**

### **1. Legislative Production**

**Philosophy**: Legislative Production represents the core function of any parliamentarian - creating, shaping, and improving laws. In the European Parliament, this happens primarily through the report system, where MEPs serve as rapporteurs (lead authors) or shadow rapporteurs (opposition perspectives) for legislative files. **Reports and Opinions are the most important**, as MEPs have the greatest impact on how legislation will look at the end - the highest possible gains.

Rapporteurs draft the Parliament's position on proposed legislation, conduct negotiations with other institutions, and guide the legislative file through the parliamentary process. Shadow rapporteurs provide alternative viewpoints and ensure political balance. Opinion rapporteurs contribute specialized committee expertise to legislation outside their committee's primary competence.

Amendments represent the detailed work of legislative improvement, where MEPs propose specific textual changes to make laws more effective, clearer, or better aligned with European values. This granular legislative work directly influences the final shape of EU law.

**Measurement**: This category combines reports, opinions, and amendments into a single score reflecting the MEP's contribution to EU lawmaking.

#### **Reports & Opinions**

| Report Role | Points | Description |
| ----- | ----- | ----- |
| Rapporteur | 4.0 | Lead author of report |
| Shadow Rapporteur | 1.0 | Opposition/alternative perspective |
| Opinion Rapporteur | 1.0 | Committee opinion on report |
| Opinion Shadow | 0.5 | Shadow for committee opinion |

#### **Amendments submitted in Committees**

Amendments are legislative proposals to modify existing draft legislation during the committee stage. This is where MEPs can directly influence the final shape of EU laws by proposing specific changes, additions, or deletions to legislative texts.

**Scoring:** Outlier-based (0-4 points)

**Activity Indicators Scoring**

Activity indicators (such as Amendments, Written Questions, Oral Questions, Explanations of Vote, Plenary Speeches, and Motions) are evaluated using an **outlier-based scoring system with logarithmic scaling** (0-4 points). This statistical approach ensures fair comparison within each parliamentary term while automatically adapting to data distribution.

##### **Outlier-Based Scoring Method**

**1. Outlier Detection (IQR Method):**

* Calculate Q1 (25th percentile), Q3 (75th percentile), and IQR = Q3 - Q1  
* Lower bound = Q1 - 1.5 × IQR  
* Upper bound = Q3 + 1.5 × IQR

**2. Scoring Rules:**

* **Below lower bound:** 0 points (outlier low activity)  
* **Above upper bound:** 4 points (outlier high activity)  
* **Within normal range:** Logarithmic scaling from 0 to 4 points

**3. Logarithmic Formula:**  
score = log₂(1 + normalized) × 4

Where normalized = (value - min) / (max - min) using clean data after outlier removal

##### **Benefits of Outlier-Based Scoring**

* **Automatic Adaptation:** No need for manual threshold adjustments between terms  
* **Statistical Robustness:** Uses proven IQR method for outlier detection  
* **Fair Distribution:** Ensures meaningful score differentiation across all activity levels  
* **Smooth Scaling:** Logarithmic function provides natural growth curves  
* **Term Independence:** Each term is analyzed separately for fair historical comparison

**Note:** Term-specific ranges ensure fair comparison within each parliamentary term while accounting for significant activity variations between terms (e.g., amendment activity in Term 8 averaged 906 vs. 268 in Term 10).

##### **Why Term-Specific Ranges?**

* **Dramatic variations:** Activity levels vary by over 1000% between some terms  
* **Term completion:** Current Term 10 shows lower activity due to incomplete duration  
* **Fair comparison:** MEPs should be evaluated against their contemporaries, not across different parliamentary contexts  
* **Data-driven ranges:** Ranges based on quartile analysis of actual parliamentary activity data

### **2. Control & Transparency**

**Philosophy**: Parliamentary democracy requires robust oversight of executive power. MEPs exercise democratic control through various questioning mechanisms that hold the European Commission, Council, and other EU institutions accountable to citizens. This category measures the watchdog function of parliament.

Written questions allow MEPs to seek detailed information on EU policies, spending, and decision-making processes. They create a permanent record of institutional accountability and often reveal important information about EU operations that might otherwise remain opaque.

Oral questions during plenary sessions and committee meetings provide real-time scrutiny of EU executives, forcing public responses to important issues and concerns raised by elected representatives.

Explanations of vote demonstrate transparency in the democratic process, showing citizens why their representatives voted in specific ways on important legislation. This builds democratic accountability between MEPs and their constituents.

**Measurement**: All indicators use outlier-based scoring for fair cross-term comparison, recognizing that oversight intensity varies across different parliamentary terms.

##### **Written Questions**

Written questions submitted by MEPs to EU institutions for official written responses. These allow MEPs to seek detailed information and hold institutions accountable through documented exchanges.

**Scoring:** Outlier-based (0-4 points)

##### **Oral Questions**

Formal questions for oral answer with debate, addressed to EU institutions. These can be tabled by committees, political groups, or groups of MEPs to bring important issues to parliamentary debate.

**Scoring:** Outlier-based (0-4 points)

##### **Explanations of Vote**

Written or oral statements explaining voting positions on specific measures

**Scoring:** Outlier-based (0-4 points)

### **3. Engagement & Presence**

**Philosophy**: Democracy requires active debate and public discourse. This category measures how actively MEPs participate in parliamentary discussions and contribute to the European political conversation. Speaking in plenary sessions demonstrates engagement with EU-wide issues and helps shape public understanding of European policies.

Plenary speeches allow MEPs to articulate positions, challenge proposals, and represent their constituents' views in the broader European debate. These contributions to parliamentary discourse help form public opinion and influence the direction of European integration.

Motions for resolutions enable MEPs to raise important issues that might not otherwise receive parliamentary attention. These initiatives demonstrate proactive engagement with emerging challenges and help set the European political agenda.

**Measurement**: All indicators use outlier-based scoring for consistent evaluation across different parliamentary terms and political contexts.

##### **Plenary Speeches**

Speeches delivered during plenary sessions of the European Parliament

**Scoring:** Outlier-based (0-4 points)

##### **Motions for Resolutions**

Proposals for Parliament resolutions on various topics and issues

**Scoring:** Outlier-based (0-4 points)

### **4. Institutional Roles**

**Philosophy**: Democratic institutions require leadership and specialized expertise. MEPs who accept institutional roles take on additional responsibilities that extend beyond regular legislative duties. These positions involve chairing meetings, coordinating between political groups, managing parliamentary business, and representing the Parliament in external relations. The scoring system recognizes this additional workload while maintaining proportionality.

Institutional roles are applied as percentage multipliers using the Power × Scarcity heuristic, which balances the authority level of a position against how few MEPs can hold it.

#### **Power × Scarcity Heuristic**

**bonus ≈ relative authority / share of MEPs in role**

The rarer and more powerful the office, the bigger the premium. Roles that can alter legislation (President, Committee Chair) are weighted highest. Administrative roles (Quaestor) or diplomatic roles (delegations) receive discounts reflecting their more limited legislative impact.

| Position | Bonus Multiplier | Rationale |
| ----- | ----- | ----- |
| EP President | +100% | Highest authority, unique position (1/720 MEPs)* |
| EP Vice-President | +60% | High authority, very rare (~14/720 MEPs)* |
| Committee Chair | +60% | High legislative power, rare (~20/720 MEPs)* |
| Quaestor | +35% | Administrative role, limited legislative impact |
| Committee Vice-Chair | +30% | Moderate authority in committees |
| Delegation Chair | +20% | Diplomatic role, lower legislative impact |
| Delegation Vice-Chair | +10% | Minor diplomatic responsibilities |

**Role multiplier calculation:**  
institutional_roles_multiplier = 1 + highest_role_percentage  
*(Only the highest role bonus is applied to avoid double-counting)*

*Maximum number of MEPs has changed over the years: 751 (8th term), 705 (9th term post-Brexit), 720 (10th term).

## **Attendance Penalty**

**Philosophy**: Democratic representation fundamentally requires presence. Citizens elect MEPs to represent their interests in the European Parliament, which means physically attending sessions and participating in votes. While the quality of participation matters, quantity of attendance serves as a baseline indicator of democratic commitment.

Attendance penalties reflect the principle that consistent absence undermines the democratic mandate. MEPs who regularly miss plenary sessions cannot effectively represent their constituents' interests, regardless of their other activities. The penalty system is designed with reasonable thresholds that account for legitimate absences while penalizing systematic non-participation.

**Implementation**: Parliamentary attendance is measured through participation in plenary votes. Attendance rates below certain thresholds result in score penalties applied to the final score after all other calculations.

| Attendance Level | Score Penalty | Description |
| ----- | ----- | ----- |
| 75% and above | No penalty | Good attendance - no score reduction |
| Lower than 75% | Score × 0.75 | 25% score reduction for poor attendance |
| Lower than 55% | Score × 0.5 | 50% score reduction for very poor attendance |

##### **Attendance Penalty Exemptions**

**Only EP Chair and Vice Chair are exempt** from attendance penalties as they usually do not participate in votes when presiding over plenary sessions.

## Final Score Calculation

The final score calculation follows a sequential process:

### Step 1: Category Score Calculation
```
legislative_production = reports_score + amendments_score  
control_transparency = oral_questions_score + written_questions_score + explanations_score  
engagement_presence = speeches_score + motions_score
```

### Step 2: Base Score Calculation
```
base_score = legislative_production + control_transparency + engagement_presence
```

### Step 3: Apply Role Multiplier
```
score_with_roles = base_score × institutional_roles_multiplier
```
where `institutional_roles_multiplier = 1 + highest_role_percentage`

### Step 4: Apply Attendance Penalty
```
final_score = score_with_roles × attendance_penalty
```
where `attendance_penalty = 1.0 (≥75%), 0.75 (<75%), or 0.5 (<55%)`

## **Custom Weights**

### **Personalized Rankings**

The weighting of individual indicators is largely subjective; therefore, the interface includes the ability to adjust the weighting of individual indicator groups according to your preferences. This allows users to create personalized rankings based on what they consider most important in MEP performance.

### **How It Works**

* Adjust weights for each of the four main categories  
* Real-time recalculation of scores and rankings  
* Save and share your custom methodology  
* Compare different weighting approaches

### **Use Cases**

* Emphasize legislative productivity over speeches  
* Prioritize attendance and participation  
* Focus on leadership roles and responsibilities  
* Create balanced or specialized evaluations

## **Data Sources & Limitations**

### **Primary Data Source: ParlTrack.eu**

All data is sourced from ParlTrack.eu, which provides comprehensive, officially sourced European Parliament data including votes, amendments, reports, speeches, and MEP activities across parliamentary terms.

### **Coverage Period**

**8th Term:** 2014-2019  
**9th Term:** 2019-2024  
**10th Term:** 2024-current  
*Last update: July 23rd 2025*

### **Important Notes**

* **New 4-Category System:** This updated methodology replaces previous approaches  
* **Quantitative Focus:** Current method considers quantitative aspects of parliamentary activity  
* **Transparency:** All calculations are based on publicly available data  
* **Power × Scarcity:** Role bonuses reflect both authority and rarity of positions  
* **Data-Driven:** Scoring parameters calibrated based on current EP data patterns

Each final score calculation can be verified in the MEP's profile or by clicking on their score in the table on the homepage

## **Limitations & Disclaimer**

### **Important Notice**

This evaluation represents only a quantitative view of MEP activity and **cannot replace comprehensive assessment of work quality**. Higher scores do not automatically mean better politicians.

### **What the system does not consider:**

* **Quality of legislative proposals** - we evaluate quantity, not quality  
* **Political background and contexts** - the system is politically neutral  
* **Work outside EP** - activity in home countries or other organizations  
* **Unofficial activities** - lobbying, informal negotiations, media appearances  
* **Strategic voting** - reasons and contexts of voting decisions  
* **Specializations** - some areas require less but higher quality work

### **Recommended Usage**

* As one of several tools for evaluating MEPs  
* To identify particularly active or inactive members  
* To compare activity within countries or political groups  
* As a complement to qualitative assessment of political content

#### **Beta Disclaimer**

This is a beta version of our scoring methodology. Parameters and calculations may be adjusted based on ongoing analysis, feedback, and methodological improvements. We welcome constructive feedback to help refine the system.

### **MEP Score**

Transparent overview of the activity of members of the European Parliament. Empowering citizens with objective information for democratic accountability.

### **Contact**

If you notice any inaccuracies or have suggestions for improvement, please contact us at mepscore@gmail.com

© 2025 MEP Score. All rights reserved.