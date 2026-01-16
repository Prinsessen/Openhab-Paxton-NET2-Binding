(function(data) {
    if (!data || data === "NULL") {
        return "No entries yet";
    }
    try {
        var entry = JSON.parse(data);
        var date = entry.timestamp.substring(0, 10);  // Extracts 2026-01-16
        var time = entry.timestamp.substring(11, 19); // Extracts 14:35:22
        return entry.firstName + " " + entry.lastName + " entered " + entry.doorName + " on " + date + " at " + time;
    } catch (e) {
        return "Error parsing entry log";
    }
})(input)
