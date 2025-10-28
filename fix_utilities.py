import re

# Read the original file
with open('public/js/utilities.js', 'r') as f:
    content = f.read()

# Replace the problematic section in loadTermDataset function
old_pattern = r'''    if \(response\.ok\) \{
      const data = await response\.json\(\);
      console\.log\(\);
      return data;
    \}'''

new_pattern = '''    if (response.ok) {
      const data = await response.json();
      if (Array.isArray(data)) {
        // Database API returns just MEPs array, wrap it for consistency
        console.log(`Loaded term ${term} dataset from database API (${data.length} MEPs, no averages)`);
        return { meps: data, averages: {} };
      } else {
        // If it's an object, return as-is
        console.log(`Loaded term ${term} dataset from database API`);
        return data;
      }
    }'''

content = re.sub(old_pattern, new_pattern, content, flags=re.MULTILINE)

# Also fix the JSON file handling
old_json_pattern = r'''    const data = await jsonResponse\.json\(\);
    console\.log\(\);
    return data;'''

new_json_pattern = '''    const data = await jsonResponse.json();
    // Handle both direct array and wrapped object formats
    if (Array.isArray(data)) {
      // If it's just an array, wrap it in an object for consistency
      console.log(`Loaded term ${term} dataset from JSON file (${data.length} MEPs, no averages)`);
      return { meps: data, averages: {} };
    } else {
      // If it's an object, return the full object (includes averages)
      const mepsCount = data.meps ? data.meps.length : 0;
      const hasAverages = data.averages ? 'with averages' : 'no averages';
      console.log(`Loaded term ${term} dataset from JSON file (${mepsCount} MEPs, ${hasAverages})`);
      return data;
    }'''

content = re.sub(old_json_pattern, new_json_pattern, content, flags=re.MULTILINE)

# Write the fixed content
with open('public/js/utilities.js', 'w') as f:
    f.write(content)

print('Fixed utilities.js successfully')
