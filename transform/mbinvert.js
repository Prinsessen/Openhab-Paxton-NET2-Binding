// function to invert Modbus binary states
// input variable i contains data passed by OpenHAB binding
(function(i) {
    var t = i ;      // allow Undefined to pass through
    if (i == '1') {
    	t = 'CLOSED' ;
    } else if (i == '0') {
    	t = 'OPEN' ;
    }
    return t ;      // return a string 
})(input)
