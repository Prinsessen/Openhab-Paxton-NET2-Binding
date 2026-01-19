(function(i) {
    var val = parseFloat(i);
    if (val <= 2) return "Excellent";
    if (val <= 5) return "Good";
    if (val <= 10) return "Fair";
    return "Poor";
})(input)
