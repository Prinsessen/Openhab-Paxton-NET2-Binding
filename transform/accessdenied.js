(function(input) {
    // Parse the JSON input
    try {
        if (input === "NULL" || input === "UNDEF" || !input) {
            return "No denied access attempts";
        }
        
        var data = JSON.parse(input);
        
        // Extract values
        var tokenNumber = data.tokenNumber || "Unknown";
        var doorName = data.doorName || "Unknown Door";
        var timestamp = data.timestamp || "";
        
        // Format timestamp to just show time (HH:mm:ss)
        var timeStr = "Unknown time";
        if (timestamp) {
            try {
                // Extract time portion (ISO format: 2026-01-16T17:26:50)
                timeStr = timestamp.substring(11, 19);
            } catch (e) {
                timeStr = timestamp;
            }
        }
        
        // Return formatted string
        return "⚠️ Token " + tokenNumber + " at " + timeStr;
        
    } catch (e) {
        return "Error parsing data: " + e.message;
    }
})(input)
