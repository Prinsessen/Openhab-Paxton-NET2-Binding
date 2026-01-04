(function(i) {
    if (i === 'NULL' || i === 'UNDEF' || i === '') {
        return "N/A"; // Return "N/A" or whatever you prefer if there's no data
    }
    // Parse the input string as a float, divide by 60, and round down
    return Math.floor(parseFloat(i) / 60);
})(input)
