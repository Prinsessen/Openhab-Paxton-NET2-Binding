// function to invert Modbus binary states
// variable "input" contains data passed by openHAB
(function(inputData) {
    var out = inputData ;      // allow UNDEF to pass through
    if (inputData == '1' || inputData == 'ON' || inputData == 'OPEN') {
        out = '0' ;  // change to OFF or OPEN depending on your Item type
    } else if (inputData == '0' || inputData == 'OFF' || inputData == 'CLOSED') {
        out = '1' ;
    }
    return out ;      // return a string
})(input)
