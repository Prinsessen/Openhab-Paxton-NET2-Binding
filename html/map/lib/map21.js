/*** 
 * JavaScript classes to display openHAB user locations 
 * and histories.
 *
 * Version 2.1.0
 * Date: 2019-02-22
 * Author: Patrik Gfeller
 * 
 * History:
 * - 2.1.0: Cleaned up of 2.0.0 prototype; initial 
 *          version to be shared.
 */
"use strict";

var locationTypes = Object.freeze({
    "home": "1",
    "user": "2"
});
/* *****************************************************************
 * !!! Configure your openHAB items here (home location, users). !!! 
 * ***************************************************************** */
function initialize() {
    /* Add your location and history items here. If the 
    historyItem is not set (undefined), no history will be shown
    for the respective item. 

    The openHAB items need to have the following format:
        - locationItem: <latitudate>, <longitude>
        - historyItem: <latitude>, <longitude>; <latitude>, <longitude>; ...

    Possible values for locationMarkerAnimation:
        - null
        - google.maps.Animation.BOUNCE
        - google.maps.Animation.DROP */
    var openHABLocations = {
        "Home": {
            locationItem: "Squaw_Position",
            locationIcon: "./img/patrik.png",
            locationType: locationTypes.home,
            animation: google.maps.Animation.DROP,
            historyItem: "null",
            historyIcon: "null",
            zIndex: 10
        },
        "Patrik": {
            locationItem: "NannaPhone_Position",
            locationIcon: "./img/patrik.png",
            locationType: locationTypes.user,
            animation: google.maps.Animation.DROP,
            historyItem:  null,
            historyIcon:  null,
            zIndex: 9
        },
        "Karin": {
            locationItem: "KennethBil_Position",
            locationIcon: "./img/karin.png",
            locationType: locationTypes.user,
            animation: google.maps.Animation.DROP,
            historyItem:  null,
            historyIcon:  null,
            zIndex: 8
        },
	"Roadmaster": {
            locationItem: "Roadmaster_Position",
            locationIcon: "./img/karin.png",
            locationType: locationTypes.user,
            animation: google.maps.Animation.DROP,
            historyItem:  null,
            historyIcon:  null,
            zIndex: 8
 	   }
    };
    var domElementId = "map";
    var domElement = document.getElementById(domElementId);

    if (domElement === null)
        domElement = document.createElement("div");

    var configuration = new Configuration(domElement, openHABLocations);
    configuration.updateTime = 60000;
    configuration.historyAnimationTime = 250;

    new MapObject(openHAB, configuration).initialize();
};
/* ***************************************************************** */
var javascriptTypes = Object.freeze({
    "undefined": "undefined",
    "boolean": "boolean",
    "number": "number", 
    "string": "string",
    "symbol": "symbol", // ECMAScript 2015
    "function": "function",
    "object": "object"
});
var util = {
    throwExceptionIfParameterIsNotDefined: (obj, expectedType, exceptionMessage) => {
        switch (typeof obj) {
            case javascriptTypes.object: 
                if (obj === null) 
                    throw new Error(exceptionMessage);
            case javascriptTypes.string:
                if(obj == "") 
                    throw new Error(exceptionMessage);
            default:
                if (typeof obj != expectedType)
                    throw new Error(exceptionMessage);
        };
    },
    replaceAll: (str, pattern) => {
        if (str == undefined || str == "") 
            return "";

        while (str.indexOf(pattern) != -1) { 
            str = str.replace(pattern, "");
        }

        return str;
    }
};

function Configuration(domContainer, openHABLocations) {
    // Basic parameter sanity checks ...
    util.throwExceptionIfParameterIsNotDefined(domContainer, javascriptTypes.object, "Invalid Argument");
    util.throwExceptionIfParameterIsNotDefined(openHABLocations, javascriptTypes.object, "Invalid Argument");

    // Create and initialize properties ...
    this.domContainer = domContainer;
    this.openHABLocations = openHABLocations;
}

function MapObject(communicationLayer, configuration) {
    // Basic parameter sanity checks ...
    util.throwExceptionIfParameterIsNotDefined(communicationLayer, javascriptTypes.object, "Invalid Argument");
    util.throwExceptionIfParameterIsNotDefined(configuration, javascriptTypes.object, "Invalid Argument");

    // Create and initialize properties ...
    this.communicationLayer= communicationLayer;
    this.configuration = configuration;

    MapObject.prototype.parseLocation = (value) => {
        value = util.replaceAll(value, ";");
        if (value == "") {
            return [];
        }

        return [
            parseFloat(value.split(",")[0]),
            parseFloat(value.split(",")[1])
        ];
    };
    MapObject.prototype.createGoogleMap = (value) => {
        return new google.maps.Map(this.configuration.domContainer, {
            center: value,
            mapTypeId: google.maps.MapTypeId.TERRAIN,
            zoom: 10
        });
    }
    MapObject.prototype.extendBounds = () => {
        for (var elementName in this.configuration.openHABLocations) {
            var item = this.configuration.openHABLocations[elementName];

            if (item.position != undefined) {
                this.bounds == undefined 
                    ? this.bounds = new google.maps.LatLngBounds(item.position, item.position) 
                : this.bounds.extend(item.position);
            };

            if (item.locationHistory != undefined) {
                for (var index in item.locationHistory) {
                    this.bounds.extend(item.locationHistory[index].position);
                }
            };
        };
    };
    MapObject.prototype.initialize = () => {
        this.customBound = false;
        this.setup = (item) => {
            (() => {   
                this.load = (item, callback) => {
                    (() => {
                        openHAB.getItemValue(item.locationItem, (value) => {
                            var locationArray = this.parseLocation(value);

                            if (locationArray.length >= 2){
                                item.position = new google.maps.LatLng(
                                    parseFloat(locationArray[0]),
                                    parseFloat(locationArray[1]));
                            } else {
                                item.position = undefined;
                            };

                            if (item.historyItem != undefined) {
                                openHAB.getItemValue(item.historyItem, (value) => {
                                    var positionValueArray = value.split(";");
                                    var positionArray = this.parseLocation();

                                    var i = 0;
                                    var j = 0;
                                    for (i; i < positionValueArray.length; i++) {
                                        var position = this.parseLocation(positionValueArray[i]);

                                        if (position.length >= 2) {
                                            positionArray[j++] = position;
                                        };
                                    };
                                    i = 0;
                                    for (i; i < positionArray.length; i++) {
                                        if (positionArray[i] == undefined) 
                                            return;

                                        if (item.locationHistory == undefined)
                                            item.locationHistory = [];

                                        item.locationHistory[i] = {};
                                        item.locationHistory[i].position = new google.maps.LatLng(
                                            parseFloat(positionArray[i][0]),
                                            parseFloat(positionArray[i][1]))  
                                    };

                                    callback(item);
                                });
                            }; 
                        });
                    })();
                };
                this.load(item, (item) => {
                    this.display = () => {
                        this.extendBounds();
                        if (!this.customBound) {
                            this.googleMap.fitBounds(this.bounds);
                        };

                        for (var index in this.configuration.openHABLocations) {
                            var item = this.configuration.openHABLocations[index];
                            (() => {
                                if (item.position != undefined) {
                                    if (item.marker == undefined) {
                                        item.marker = new google.maps.Marker({
                                            position: item.position,
                                            icon: { url: item.locationIcon },
                                            animation: item.animation,
                                            map: this.googleMap,
                                            zIndex: item.zIndex
                                        });
                                    } else {
                                        item.marker.setPosition(item.position);
                                    };
                                };
                                if (item.locationHistory != undefined) {
                                    var i = 0;
                                    for(var index in item.locationHistory) {
                                        if (item.locationHistory[index].marker == undefined) {
                                            var animate = (item, position) => { 
                                                position.marker = new google.maps.Marker({
                                                    position: position,
                                                    icon: { url: item.historyIcon },
                                                    map: this.googleMap,
                                                    zIndex: item.zIndex - 1 
                                                });
                                            };

                                            window.setTimeout(animate, this.configuration.historyAnimationTime * index, item, item.locationHistory[index].position)
                                        } else {
                                            item.locationHistory[index].marker.setPosition(item.locationHistory[index].position);
                                        }
                                    };
                                };
                            })();
                        };
                    };

                    if (this.googleMap == undefined) {
                        this.googleMap = this.createGoogleMap(item.position);

                        var eventListener = this.googleMap.addListener("tilesloaded", () => {
                            google.maps.event.removeListener(eventListener);

                            this.display();

                            eventListener = this.googleMap.addListener("titlesloaded", () => {
                                google.maps.event.removeListener(eventListener);

                                /* Disable automatic bounds (zoom) if the user did 
                                change the area visible. */
                                this.customBound = true;
                            });
                        });
                    };

                    window.setInterval(this.load, this.configuration.updateTime, item, () => {
                        this.display();
                    });
                });
            }) ();
        };

        for (var locationItemName in this.configuration.openHABLocations) {
            (() => {
                var item = this.configuration.openHABLocations[locationItemName];

                this.setup(item);
            })();
        };
    };
};
