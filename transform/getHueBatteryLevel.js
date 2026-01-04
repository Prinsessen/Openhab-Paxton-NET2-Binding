(function(i) {
    var json = JSON.parse(i);
    return parseInt(json["config"]["battery"]);
})(input)
