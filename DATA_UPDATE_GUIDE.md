# Data Update Guide for MEP Ranking System

**For Non-Technical Maintainers**

This guide provides step-by-step instructions for updating the MEP (Member of European Parliament) activity data in the ranking system.

## 🎯 Overview

The MEP Ranking system focuses on **10th parliamentary term (2024-2029)** data. Regular updates ensure the rankings reflect the most current parliamentary activities.

## 📁 Data Update Folder

**Important**: All new data files must be placed in:
```
\data\parltrack\
```

This is the designated folder where the system looks for updated ParlTrack data files.

## 📋 Step-by-Step Update Process

### Step 1: Download Latest ParlTrack Data

1. **Visit ParlTrack**: Go to [parltrack.org](https://parltrack.org)
2. **Download Required Files**: Look for these compressed files (.zst format):
   - `ep_mep_activities.json.zst` ← **Most Important** (MEP activities like speeches, amendments)
   - `ep_amendments.json.zst` (Amendment details)
   - `ep_votes.json.zst` (Voting records) 
   - `ep_meps.json.zst` (MEP biographical information)

3. **Save to Correct Folder**: Place all downloaded files in `\data\parltrack\`

### Step 2: Cross-Check MEP List ⚠️ CRITICAL

This step ensures accuracy of the data:

1. **Get Official MEP List**: Download the current MEP full list XML from European Parliament website
2. **Verify MEP Count**: Confirm the number matches current 10th term MEPs (~720 MEPs)
3. **Check for Changes**: Look for newly elected MEPs or those who have left office

### Step 3: Run the Data Update

#### Option A: Simple Method (Recommended)
- **Windows**: Double-click `run_update.bat`
- **Command Line**: Type `python run_update.py` and press Enter

#### Option B: PowerShell (Windows)
- Right-click PowerShell → "Run as Administrator"
- Navigate to the project folder
- Type `.\run_update.ps1` and press Enter

### Step 4: Monitor the Update Process

The update will show progress messages:
```
✅ Decompressing ParlTrack files...
✅ Ingesting MEP activities...
✅ Processing amendments data...
✅ Building Term 10 dataset...
✅ Calculating scores...
✅ Update complete!
```

**Typical Duration**: 5-15 minutes depending on data size

### Step 5: Verify Update Results

After the update completes, check:

1. **MEP Count**: Verify the number of MEPs matches expectations
2. **Recent Activity**: Check that recent parliamentary activities appear
3. **Profile Pages**: Test a few MEP profiles to ensure data updated
4. **Rankings**: Confirm ranking changes reflect recent activities

## 🔄 What Gets Updated

The data update process refreshes all system components:

### Score Breakdown
- **Legislative Production**: Reports, amendments, opinions
- **Control & Transparency**: Questions (oral/written), explanations
- **Engagement & Presence**: Speeches, motions
- **Institutional Roles**: Leadership position bonuses

### Profile Pages
- Individual MEP activity histories
- Detailed breakdowns by category
- Comparison with averages

### Averages & Benchmarks
- **EP-wide averages**: Parliament-wide activity levels
- **Group averages**: Political group comparisons
- **Country averages**: National delegation comparisons

### Interactive Features
- **Clickable Activity Details**: Drill-down data for specific activities
- **Search and Filtering**: Updated MEP information
- **Custom Rankings**: Refreshed data for weight adjustments

## ⚠️ Important Notes

### Data Scope
- **Primary Focus**: 10th term (2024-2029) - current parliamentary term
- **Historical Data**: Terms 8 and 9 are maintained separately in backup files
- **Update Frequency**: Recommended monthly or after significant parliamentary activity

### Quality Assurance
- Always verify MEP count after updates
- Cross-reference with official EP sources
- Test key functionality after major updates

### File Management
- Keep backup copies of previous data files
- Compressed files (.zst) save significant storage space
- Old files are automatically archived during updates

## 🆘 Troubleshooting

### Common Issues

**"Python not found"**
- Ensure Python is installed and accessible from command line
- Windows: Download from python.org and add to PATH

**"Files missing"**
- Check that all required .zst files are in `\data\parltrack\`
- Re-download missing files from parltrack.org

**"MEP count mismatch"**
- Verify against official European Parliament MEP list
- Check for recent MEP changes or elections

**"Update takes too long"**
- Large data files can take 10-15 minutes to process
- Ensure sufficient disk space is available

### Getting Help

For technical issues:
1. Check the console output for specific error messages
2. Verify all required files are present
3. Ensure Python dependencies are installed (`pip install -r requirements.txt`)

## 📊 Success Indicators

A successful data update should result in:
- ✅ Current MEP count matches official numbers
- ✅ Recent parliamentary activities visible in rankings
- ✅ Profile pages show updated activity data
- ✅ All navigation and search functions work properly
- ✅ Score breakdowns reflect methodology correctly

## 🔄 Regular Maintenance

### Recommended Schedule
- **Weekly**: Check for new ParlTrack data releases
- **Monthly**: Perform full data update
- **After Elections**: Immediate update to reflect MEP changes
- **Before Major Announcements**: Ensure data is current

### Data Quality Monitoring
- Compare MEP counts with official EP sources
- Verify activity totals seem reasonable
- Spot-check individual MEP profiles for accuracy

---

**Remember**: The goal is to maintain accurate, current data that serves citizens seeking transparency in European Parliament activities. Regular updates ensure the system remains a reliable resource for evaluating MEP performance.