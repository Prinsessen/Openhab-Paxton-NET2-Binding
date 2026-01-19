(function(i) {
    var val = parseFloat(i);
    if (isNaN(val)) return "Unknown";
    
    var abs = Math.abs(val);
    
    if (abs <= 2) return "Perfect";
    if (abs <= 5) return "Excellent";
    if (abs <= 10) return "Good";
    if (abs <= 15) return "Monitor";
    return "Check Engine";
})(input)
