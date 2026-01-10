(function(data) {
    if (!data || data === "NULL") {
        return "No entries yet";
    }
    try {
        var entry = JSON.parse(data);
        var time = entry.timestamp.substring(11, 19);
        return entry.firstName + " " + entry.lastName + " entered " + entry.doorName + " at " + time;
    } catch (e) {
        return "Error parsing entry log";
    }
})(input)
