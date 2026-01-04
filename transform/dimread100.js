// Wrap everything in a function (no global variable pollution)
// variable "input" contains data string passed by binding
(function(inputData) {
    // here set the 100% equivalent register value
    var MAX_SCALE = 100;
    // convert to percent
    return Math.round( parseFloat(inputData) * 100 / MAX_SCALE );
})(input)
