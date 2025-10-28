
// Function to load averages from database API
async function loadDatabaseAverages(term) {
    try {
        const response = await fetch(`http://localhost:8001/api/averages?term=${term}`);
        if (!response.ok) {
            throw new Error(`Failed to load averages: ${response.status}`);
        }
        const result = await response.json();
        if (result.success) {
            console.log("Loaded averages from database API");
            return result.data;
        } else {
            throw new Error(result.error || "Failed to load averages");
        }
    } catch (error) {
        console.warn("Could not load database averages:", error);
        return { ep: {}, groups: {}, countries: {} };
    }
}
