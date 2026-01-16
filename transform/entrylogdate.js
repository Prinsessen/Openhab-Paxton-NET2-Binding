(function(data) {
    if (!data || data === "NULL") {
        return "No entries yet";
    }
    try {
        var entry = JSON.parse(data);
        var year = entry.timestamp.substring(0, 4);   // Extracts 2026
        var month = entry.timestamp.substring(5, 7);  // Extracts 01
        var day = entry.timestamp.substring(8, 10);   // Extracts 16
        var time = entry.timestamp.substring(11, 19); // Extracts 14:35:22
        var date = day + "-" + month + "-" + year;    // Format as 16-01-2026
        return entry.firstName + " " + entry.lastName + " entered " + entry.doorName + " on " + date + " at " + time;
    } catch (e) {
        return "Error parsing entry log";
    }
})(input)
