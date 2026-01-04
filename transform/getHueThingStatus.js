(function(i) {
    var json = JSON.parse(i);
    return (json["config"]["reachable"]) == true ? "ONLINE" : "OFFLINE";
})(input)

