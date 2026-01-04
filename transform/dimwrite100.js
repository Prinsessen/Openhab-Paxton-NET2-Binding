// variable "input" contains command string passed by openhab
(function(inputData) {
    // here set the 100% equivalent register value
    var MAX_SCALE = 100;
    var out = 0
    if (inputData == 'ON') {
          // set max
         out = MAX_SCALE
    } else if (inputData == 'OFF') {
         out = 0
    } else {
         // scale from percent
         out = Math.round( parseFloat(inputData) * MAX_SCALE / 100 )
    }
    return out
})(input)
