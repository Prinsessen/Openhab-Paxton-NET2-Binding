"use strict";

var openHAB = new Object();
var xhrReadyState = Object.freeze({
    "unsent": 0,
    "opened": 1,
    "headersRecieved": 2,
    "loading": 3,
    "done": 4
});

openHAB.baseURL = "https://openhab3.agesen.dk/";
openHAB.getItemValue = (itemName, callback) => {
    var encodedItemName =  encodeURIComponent(itemName);
    var xhr = new XMLHttpRequest();
    var restAPICall = openHAB.baseURL.concat("rest/items/").concat(encodedItemName).concat("/state");

    xhr.open("GET", restAPICall);
    xhr.onreadystatechange = (readyState) => {
        if (xhr.readyState == xhrReadyState.done) {
            callback(xhr.responseText);   
        }
    };
    xhr.send();
};