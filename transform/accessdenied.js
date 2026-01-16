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
        
        // Format timestamp in same format as entrylogdate.js: DD-MM-YYYY at HH:mm:ss
        var dateTimeStr = "Unknown time";
        if (timestamp) {
            try {
                // Extract date and time from ISO format: 2026-01-16T17:26:50
                var year = timestamp.substring(0, 4);   // Extracts 2026
                var month = timestamp.substring(5, 7);  // Extracts 01
                var day = timestamp.substring(8, 10);   // Extracts 16
                var time = timestamp.substring(11, 19); // Extracts 17:26:50
                var date = day + "-" + month + "-" + year;  // Format as 16-01-2026
                dateTimeStr = date + " at " + time;
            } catch (e) {
                dateTimeStr = timestamp;
            }
        }
        
        // Return formatted string: Token 1234567 denied at 16-01-2026 at 17:26:50
        return "⚠️ Token " + tokenNumber + " denied at " + dateTimeStr;
        
    } catch (e) {
        return "Error parsing data: " + e.message;
    }
})(input)
