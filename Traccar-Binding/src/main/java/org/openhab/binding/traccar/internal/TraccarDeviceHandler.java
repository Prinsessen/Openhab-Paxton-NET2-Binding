/*
 * Copyright (c) 2010-2026 Contributors to the openHAB project
 *
 * See the NOTICE file(s) distributed with this work for additional
 * information.
 *
 * This program and the accompanying materials are made available under the
 * terms of the Eclipse Public License 2.0 which is available at
 * http://www.eclipse.org/legal/epl-2.0
 *
 * SPDX-License-Identifier: EPL-2.0
 */
package org.openhab.binding.traccar.internal;

import static org.openhab.binding.traccar.internal.TraccarBindingConstants.*;

import java.time.ZonedDateTime;
import java.util.Map;

import javax.measure.Unit;

import org.eclipse.jdt.annotation.NonNullByDefault;
import org.eclipse.jdt.annotation.Nullable;
import org.openhab.core.library.types.DateTimeType;
import org.openhab.core.library.types.DecimalType;
import org.openhab.core.library.types.OnOffType;
import org.openhab.core.library.types.PointType;
import org.openhab.core.library.types.QuantityType;
import org.openhab.core.library.types.StringType;
import org.openhab.core.library.unit.ImperialUnits;
import org.openhab.core.library.unit.MetricPrefix;
import org.openhab.core.library.unit.SIUnits;
import org.openhab.core.library.unit.Units;
import org.openhab.core.thing.Bridge;
import org.openhab.core.thing.ChannelUID;
import org.openhab.core.thing.Thing;
import org.openhab.core.thing.ThingStatus;
import org.openhab.core.thing.ThingStatusDetail;
import org.openhab.core.thing.binding.BaseThingHandler;
import org.openhab.core.thing.binding.BridgeHandler;
import org.openhab.core.types.Command;
import org.openhab.core.types.RefreshType;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * The {@link TraccarDeviceHandler} handles commands for Traccar tracked devices
 * and updates their position and geofence status.
 *
 * @author Nanna Agesen - Initial contribution
 */
@NonNullByDefault
public class TraccarDeviceHandler extends BaseThingHandler {

    private final Logger logger = LoggerFactory.getLogger(TraccarDeviceHandler.class);

    private @Nullable TraccarDeviceConfiguration config;
    private @Nullable NominatimGeocoder geocoder;

    public TraccarDeviceHandler(Thing thing) {
        super(thing);
    }

    @Override
    public void handleCommand(ChannelUID channelUID, Command command) {
        if (command instanceof RefreshType) {
            updatePosition();
        }
    }

    @Override
    public void initialize() {
        config = getConfigAs(TraccarDeviceConfiguration.class);

        Bridge bridge = getBridge();
        if (bridge == null) {
            updateStatus(ThingStatus.OFFLINE, ThingStatusDetail.CONFIGURATION_ERROR, "No bridge configured");
            return;
        }

        BridgeHandler bridgeHandler = bridge.getHandler();
        if (!(bridgeHandler instanceof TraccarServerHandler)) {
            updateStatus(ThingStatus.OFFLINE, ThingStatusDetail.CONFIGURATION_ERROR, "Invalid bridge handler");
            return;
        }

        updateStatus(ThingStatus.UNKNOWN);
        scheduler.execute(this::connect);
    }

    private void connect() {
        Bridge bridge = getBridge();
        if (bridge != null && bridge.getStatus() == ThingStatus.ONLINE) {
            // Initialize Nominatim geocoder from server configuration
            TraccarServerHandler serverHandler = (TraccarServerHandler) bridge.getHandler();
            if (serverHandler != null) {
                TraccarServerConfiguration serverConfig = serverHandler.getConfiguration();
                if (serverConfig.useNominatim) {
                    geocoder = new NominatimGeocoder(serverConfig.nominatimUrl, serverConfig.nominatimLanguage,
                            serverConfig.geocodingCacheDistance);
                    logger.info("Nominatim geocoding enabled for device {} (server: {}, language: {})", config.deviceId,
                            serverConfig.nominatimUrl, serverConfig.nominatimLanguage);
                }
            }
            updateStatus(ThingStatus.ONLINE);
            updatePosition();
        } else {
            updateStatus(ThingStatus.OFFLINE, ThingStatusDetail.BRIDGE_OFFLINE);
        }
    }

    public void updatePosition() {
        TraccarDeviceConfiguration configuration = config;
        if (configuration == null) {
            return;
        }

        Bridge bridge = getBridge();
        if (bridge == null) {
            return;
        }

        BridgeHandler bridgeHandler = bridge.getHandler();
        if (!(bridgeHandler instanceof TraccarServerHandler serverHandler)) {
            return;
        }

        TraccarApiClient apiClient = serverHandler.getApiClient();
        if (apiClient == null) {
            return;
        }

        try {
            // Get device info for status
            Map<String, Object> device = apiClient.getDevice(configuration.deviceId);
            if (device != null) {
                Object statusObj = device.get("status");
                if (statusObj instanceof String status) {
                    updateState(CHANNEL_STATUS, new StringType(status));
                }
            }

            // Get position data
            Map<String, Object> position = apiClient.getLatestPosition(configuration.deviceId);
            if (position != null) {
                updatePositionChannels(position);
            }
        } catch (Exception e) {
            logger.debug("Failed to update position for device {}: {}", configuration.deviceId, e.getMessage());
        }
    }

    private void updatePositionChannels(Map<String, Object> position) {
        // Update position (latitude, longitude, altitude)
        Object latObj = position.get("latitude");
        Object lonObj = position.get("longitude");
        if (latObj instanceof Number && lonObj instanceof Number) {
            double latitude = ((Number) latObj).doubleValue();
            double longitude = ((Number) lonObj).doubleValue();
            Object altObj = position.get("altitude");
            double altitude = altObj instanceof Number ? ((Number) altObj).doubleValue() : 0.0;

            PointType point = new PointType(new DecimalType(latitude), new DecimalType(longitude),
                    new DecimalType(altitude));
            updateState(CHANNEL_POSITION, point);
        }

        // Update speed (Traccar reports in knots, convert to configured unit)
        Object speedObj = position.get("speed");
        if (speedObj instanceof Number) {
            double speedKnots = ((Number) speedObj).doubleValue();
            double convertedSpeed;
            Unit<?> speedUnit;

            TraccarServerHandler bridge = (TraccarServerHandler) getBridge().getHandler();
            String speedUnitConfig = bridge != null ? bridge.getSpeedUnit() : "kmh";

            switch (speedUnitConfig) {
                case "mph":
                    convertedSpeed = speedKnots * 1.15078; // knots to mph
                    speedUnit = ImperialUnits.MILES_PER_HOUR;
                    break;
                case "knots":
                    convertedSpeed = speedKnots; // no conversion
                    speedUnit = Units.KNOT;
                    break;
                case "kmh":
                default:
                    convertedSpeed = speedKnots * 1.852; // knots to km/h
                    speedUnit = SIUnits.KILOMETRE_PER_HOUR;
                    break;
            }

            // Filter GPS noise: speeds below threshold are considered stationary
            // This prevents false motion detection from GPS signal drift and small movements
            TraccarServerConfiguration serverConfig = bridge != null ? bridge.getConfiguration() : null;
            double thresholdKmh = serverConfig != null ? serverConfig.speedThreshold : 2.0;
            double thresholdKnots = thresholdKmh / 1.852; // Convert km/h threshold to knots
            if (speedKnots < thresholdKnots) {
                convertedSpeed = 0;
            }

            updateState(CHANNEL_SPEED, new QuantityType<>(convertedSpeed, speedUnit));
        }

        // Update altitude (elevation)
        Object altObj = position.get("altitude");
        if (altObj instanceof Number) {
            double altitude = ((Number) altObj).doubleValue();
            updateState(CHANNEL_ALTITUDE, new QuantityType<>(altitude, SIUnits.METRE));
        }

        // Update GPS validity
        Object validObj = position.get("valid");
        if (validObj instanceof Boolean valid) {
            updateState(CHANNEL_VALID, OnOffType.from(valid));
        }

        // Update protocol
        Object protocolObj = position.get("protocol");
        String protocol = null;
        if (protocolObj != null) {
            protocol = protocolObj.toString();
            updateState(CHANNEL_PROTOCOL, new StringType(protocol));
        }

        // Update course (direction/heading)
        Object courseObj = position.get("course");
        if (courseObj instanceof Number) {
            double course = ((Number) courseObj).doubleValue();
            updateState(CHANNEL_COURSE, new QuantityType<>(course, Units.DEGREE_ANGLE));
        }

        // Update accuracy
        Object accuracyObj = position.get("accuracy");
        if (accuracyObj instanceof Number) {
            double accuracy = ((Number) accuracyObj).doubleValue();
            updateState(CHANNEL_ACCURACY, new QuantityType<>(accuracy, SIUnits.METRE));
        }

        // Update address (use Nominatim if enabled, otherwise use Traccar's address)
        String address = null;
        NominatimGeocoder currentGeocoder = geocoder;
        if (currentGeocoder != null && latObj instanceof Number && lonObj instanceof Number) {
            // Use Nominatim for reverse geocoding
            double latitude = ((Number) latObj).doubleValue();
            double longitude = ((Number) lonObj).doubleValue();
            address = currentGeocoder.getAddress(latitude, longitude);
            if (address != null) {
                logger.debug("Using Nominatim address for device {}: {}", config.deviceId, address);
            }
        }

        // Fall back to Traccar's address if Nominatim is disabled or failed
        if (address == null) {
            Object addressObj = position.get("address");
            if (addressObj instanceof String traccarAddress) {
                address = traccarAddress;
                logger.debug("Using Traccar address for device {}: {}", config.deviceId, address);
            }
        }

        // Update address channel
        if (address != null) {
            updateState(CHANNEL_ADDRESS, new StringType(address));
        }

        // Update attributes (batteryLevel, odometer, motion)
        Object attributesObj = position.get("attributes");
        if (attributesObj instanceof Map<?, ?>) {
            @SuppressWarnings("unchecked")
            Map<String, Object> attributes = (Map<String, Object>) attributesObj;

            // Battery level
            Object batteryObj = attributes.get("batteryLevel");
            if (batteryObj instanceof Number) {
                double battery = ((Number) batteryObj).doubleValue();
                updateState(CHANNEL_BATTERY_LEVEL, new QuantityType<>(battery, Units.PERCENT));
            }

            // Odometer (device-reported, mainly for OSMand)
            Object odometerObj = attributes.get("odometer");
            if (odometerObj instanceof Number) {
                double odometerMeters = ((Number) odometerObj).doubleValue();
                updateState(CHANNEL_ODOMETER, new QuantityType<>(odometerMeters, SIUnits.METRE));
            }

            // Total Distance (Traccar server cumulative distance, all protocols)
            Object totalDistanceObj = attributes.get("totalDistance");
            if (totalDistanceObj instanceof Number) {
                double totalDistanceMeters = ((Number) totalDistanceObj).doubleValue();
                updateState(CHANNEL_TOTAL_DISTANCE, new QuantityType<>(totalDistanceMeters, SIUnits.METRE));
            }

            // Motion detection
            Object motionObj = attributes.get("motion");
            if (motionObj instanceof Boolean motion) {
                updateState(CHANNEL_MOTION, OnOffType.from(motion));
            }

            // Engine hours (in milliseconds from Traccar)
            Object hoursObj = attributes.get("hours");
            if (hoursObj instanceof Number) {
                double hoursMs = ((Number) hoursObj).doubleValue();
                double hoursValue = hoursMs / 3600000.0; // Convert milliseconds to hours
                logger.debug("Engine hours: {} ms = {} hours", hoursMs, hoursValue);
                updateState(CHANNEL_HOURS, new QuantityType<>(hoursValue, Units.HOUR));
            }

            // Event code (device-specific)
            Object eventObj = attributes.get("event");
            if (eventObj instanceof Number) {
                int eventCode = ((Number) eventObj).intValue();
                updateState(CHANNEL_EVENT, new DecimalType(eventCode));
            }

            // Distance (incremental distance since last update)
            Object distanceObj = attributes.get("distance");
            if (distanceObj instanceof Number) {
                double distanceMeters = ((Number) distanceObj).doubleValue();
                updateState(CHANNEL_DISTANCE, new QuantityType<>(distanceMeters, SIUnits.METRE));
            }

            // Activity (OSMand-specific activity detection)
            Object activityObj = attributes.get("activity");
            if (activityObj != null) {
                updateState(CHANNEL_ACTIVITY, new StringType(activityObj.toString()));
            }

            // Ignition status
            Object ignitionObj = attributes.get("ignition");
            if (ignitionObj instanceof Boolean) {
                updateState(CHANNEL_IGNITION, OnOffType.from((Boolean) ignitionObj));
            }

            // GPS Satellites
            Object satObj = attributes.get("sat");
            if (satObj instanceof Number) {
                int satellites = ((Number) satObj).intValue();
                updateState(CHANNEL_GPS_SAT, new DecimalType(satellites));
            }

            // GSM Signal Strength (RSSI)
            Object rssiObj = attributes.get("rssi");
            if (rssiObj instanceof Number) {
                double rssi = ((Number) rssiObj).doubleValue();
                double signalPercent;
                if (rssi >= 0 && rssi <= 5) {
                    // Teltonika bar scale: 0-5 bars, convert to percentage
                    signalPercent = (rssi / 5.0) * 100.0;
                } else if (rssi < 0) {
                    // dBm scale: -113 to -51 dBm
                    signalPercent = Math.max(0, Math.min(100, 2 * (rssi + 113)));
                } else {
                    signalPercent = rssi; // Already percentage
                }
                updateState(CHANNEL_GSM_SIGNAL, new QuantityType<>(signalPercent, Units.PERCENT));
            } else {
                // Try alternative attribute name "gsm"
                Object gsmObj = attributes.get("gsm");
                if (gsmObj instanceof Number) {
                    double gsm = ((Number) gsmObj).doubleValue();
                    updateState(CHANNEL_GSM_SIGNAL, new QuantityType<>(gsm, Units.PERCENT));
                }
            }

            // GPS Dilution of Precision (DOP) metrics
            Object pdopObj = attributes.get("pdop");
            if (pdopObj instanceof Number) {
                double pdop = ((Number) pdopObj).doubleValue();
                updateState(CHANNEL_PDOP, new DecimalType(pdop));
            }

            Object hdopObj = attributes.get("hdop");
            if (hdopObj instanceof Number) {
                double hdop = ((Number) hdopObj).doubleValue();
                updateState(CHANNEL_HDOP, new DecimalType(hdop));
            }

            // Power and Battery voltages
            Object powerObj = attributes.get("power");
            if (powerObj instanceof Number) {
                double powerVolts = ((Number) powerObj).doubleValue();
                updateState(CHANNEL_POWER, new QuantityType<>(powerVolts, Units.VOLT));
            }

            Object batteryObjVolt = attributes.get("battery");
            if (batteryObjVolt instanceof Number) {
                double batteryVolts = ((Number) batteryObjVolt).doubleValue();
                updateState(CHANNEL_BATTERY, new QuantityType<>(batteryVolts, Units.VOLT));
            }

            // Mobile operator code
            Object operatorObj = attributes.get("operator");
            if (operatorObj != null) {
                String operatorCode;
                if (operatorObj instanceof Number) {
                    // Convert to integer to remove decimal point (23801.0 -> 23801)
                    operatorCode = String.valueOf(((Number) operatorObj).intValue());
                } else {
                    operatorCode = operatorObj.toString();
                }
                updateState(CHANNEL_OPERATOR, new StringType(operatorCode));
            }

            // Vehicle Identification Number (VIN)
            Object vinObj = attributes.get("vin");
            if (vinObj != null) {
                updateState(CHANNEL_VIN, new StringType(vinObj.toString()));
            }

            // Additional Teltonika IO Channels (experimental/unknown purpose)
            // io42: Varies 84-94 (possibly intake air temperature or another sensor)
            Object io42Obj = attributes.get("io42");
            if (io42Obj instanceof Number) {
                int io42 = ((Number) io42Obj).intValue();
                updateState(CHANNEL_IO42, new DecimalType(io42));
            }

            // io49: Typically constant ~5816 (possibly battery voltage in mV)
            Object io49Obj = attributes.get("io49");
            if (io49Obj instanceof Number) {
                int io49 = ((Number) io49Obj).intValue();
                updateState(CHANNEL_IO49, new DecimalType(io49));
            }

            // io51: Varies 14000-14200 (possibly alternator voltage in mV)
            Object io51Obj = attributes.get("io51");
            if (io51Obj instanceof Number) {
                int io51 = ((Number) io51Obj).intValue();
                updateState(CHANNEL_IO51, new DecimalType(io51));
            }

            // Trip distance (resets)
            Object tripDistanceObj = attributes.get("distance");
            if (tripDistanceObj instanceof Number) {
                double tripDist = ((Number) tripDistanceObj).doubleValue();
                updateState(CHANNEL_TRIP_DISTANCE, new QuantityType<>(tripDist, SIUnits.METRE));
            }

            // Teltonika event code (e.g., 36 = OBD-II data update)
            Object eventCodeObj = attributes.get("event");
            if (eventCodeObj instanceof Number) {
                int eventCode = ((Number) eventCodeObj).intValue();
                updateState(CHANNEL_EVENT_CODE, new DecimalType(eventCode));
            }

            // OBD-II Trip Meters from ECU
            // io199: Trip odometer 1 (in meters, convert to km)
            Object io199Obj = attributes.get("io199");
            if (io199Obj instanceof Number) {
                double trip1Meters = ((Number) io199Obj).doubleValue();
                updateState(CHANNEL_IO199, new QuantityType<>(trip1Meters / 1000.0, MetricPrefix.KILO(SIUnits.METRE)));
            }

            // io205: Trip odometer 2 (in meters, convert to km)
            Object io205Obj = attributes.get("io205");
            if (io205Obj instanceof Number) {
                double trip2Meters = ((Number) io205Obj).doubleValue();
                updateState(CHANNEL_IO205, new QuantityType<>(trip2Meters / 1000.0, MetricPrefix.KILO(SIUnits.METRE)));
            }

            // io389: Total vehicle mileage from ECU (in meters, convert to km)
            Object io389Obj = attributes.get("io389");
            if (io389Obj instanceof Number) {
                double ecuOdometerMeters = ((Number) io389Obj).doubleValue();
                updateState(CHANNEL_IO389,
                        new QuantityType<>(ecuOdometerMeters / 1000.0, MetricPrefix.KILO(SIUnits.METRE)));
            }

            // OBD-II Data (Teltonika FMM920 with Bluetooth OBD-II dongle)
            // These channels are only populated when an OBD-II dongle is paired and ignition is ON

            // io30: Number of Diagnostic Trouble Codes (DTCs)
            Object io30Obj = attributes.get("io30");
            if (io30Obj instanceof Number) {
                int dtcCount = ((Number) io30Obj).intValue();
                updateState(CHANNEL_OBD_DTC_COUNT, new DecimalType(dtcCount));
            }

            // io31: Engine Load [%]
            Object io31Obj = attributes.get("io31");
            if (io31Obj instanceof Number) {
                double engineLoad = ((Number) io31Obj).doubleValue();
                updateState(CHANNEL_OBD_ENGINE_LOAD, new QuantityType<>(engineLoad, Units.PERCENT));
            }

            // io32: Coolant Temperature [°C]
            Object io32Obj = attributes.get("io32");
            if (io32Obj instanceof Number) {
                double coolantTemp = ((Number) io32Obj).doubleValue();
                updateState(CHANNEL_OBD_COOLANT_TEMP, new QuantityType<>(coolantTemp, SIUnits.CELSIUS));
            }

            // io33: Short Fuel Trim [%]
            Object io33Obj = attributes.get("io33");
            if (io33Obj instanceof Number) {
                double shortFuelTrim = ((Number) io33Obj).doubleValue();
                updateState(CHANNEL_OBD_SHORT_FUEL_TRIM, new QuantityType<>(shortFuelTrim, Units.PERCENT));
            }

            // io35: Fuel Pressure [kPa]
            Object io35Obj = attributes.get("io35");
            if (io35Obj instanceof Number) {
                double fuelPressureKpa = ((Number) io35Obj).doubleValue();
                // Convert kPa to Pa for OpenHAB (1 kPa = 1000 Pa)
                double fuelPressurePa = fuelPressureKpa * 1000;
                updateState(CHANNEL_OBD_FUEL_PRESSURE, new QuantityType<>(fuelPressurePa, SIUnits.PASCAL));
            }

            // io36: Engine RPM (actual RPM from OBD-II)
            // This appears to be the real RPM value that varies with engine speed
            Object io36Obj = attributes.get("io36");
            if (io36Obj instanceof Number) {
                int rpm = ((Number) io36Obj).intValue();
                updateState(CHANNEL_OBD_RPM, new DecimalType(rpm));
            }

            // io37: Engine RPM Reported (standard OBD-II PID, often shows 0)
            Object io37Obj = attributes.get("io37");
            if (io37Obj instanceof Number) {
                int rpmReported = ((Number) io37Obj).intValue();
                updateState(CHANNEL_OBD_RPM_REPORTED, new DecimalType(rpmReported));
            }

            // io38: Vehicle Speed from OBD-II [km/h]
            Object io38Obj = attributes.get("io38");
            if (io38Obj instanceof Number) {
                double obdSpeed = ((Number) io38Obj).doubleValue();
                updateState(CHANNEL_OBD_SPEED, new QuantityType<>(obdSpeed, SIUnits.KILOMETRE_PER_HOUR));
            }

            // io48: Fuel Level [%] - Inverted (100 - value) because bike reports fuel used, not remaining
            Object io48Obj = attributes.get("io48");
            if (io48Obj instanceof Number) {
                double fuelUsed = ((Number) io48Obj).doubleValue();
                double fuelRemaining = 100.0 - fuelUsed;
                updateState(CHANNEL_OBD_FUEL_LEVEL, new QuantityType<>(fuelRemaining, Units.PERCENT));
            }

            // OEM Odometer (actual vehicle odometer from CAN bus via OBD-II)
            // This is different from the generic "odometer" field - when OBD-II is active,
            // the odometer field contains the real vehicle odometer reading from CAN bus
            // Check if OBD-II data is present (indicated by io30+ attributes)
            if (io30Obj != null || io31Obj != null) {
                Object oemOdometerObj = attributes.get("odometer");
                if (oemOdometerObj instanceof Number) {
                    double oemOdometerMeters = ((Number) oemOdometerObj).doubleValue();
                    updateState(CHANNEL_OBD_OEM_ODOMETER, new QuantityType<>(oemOdometerMeters, SIUnits.METRE));
                }
            }
        }

        // Update last update time
        Object deviceTimeObj = position.get("deviceTime");
        if (deviceTimeObj instanceof String deviceTime) {
            try {
                ZonedDateTime dateTime = ZonedDateTime.parse(deviceTime);
                updateState(CHANNEL_LAST_UPDATE, new DateTimeType(dateTime));
            } catch (Exception e) {
                logger.debug("Failed to parse device time: {}", e.getMessage());
            }
        }
    }

    public void updatePositionFromWebhook(Map<String, Object> position) {
        logger.debug("Updating position from webhook for device {}", config != null ? config.deviceId : "unknown");
        updatePositionChannels(position);
    }

    public void updateStatus(String status) {
        logger.debug("Updating status from webhook for device {}: {}", config != null ? config.deviceId : "unknown",
                status);
        updateState(CHANNEL_STATUS, new StringType(status));
    }

    public void handleGeofenceEvent(Map<String, Object> eventData) {
        // Extract the event object - Traccar sends nested structure
        Object eventObj = eventData.get("event");
        if (!(eventObj instanceof Map<?, ?>)) {
            logger.debug("No event object in webhook data");
            return;
        }

        @SuppressWarnings("unchecked")
        Map<String, Object> event = (Map<String, Object>) eventObj;

        // Handle geofence entry/exit events from webhook
        Object eventTypeObj = event.get("type");
        if (eventTypeObj instanceof String eventType) {
            updateState(CHANNEL_GEOFENCE_EVENT, new StringType(eventType));

            // Update geofence name if available
            Object geofenceObj = eventData.get("geofence");
            if (geofenceObj instanceof Map<?, ?>) {
                @SuppressWarnings("unchecked")
                Map<String, Object> geofence = (Map<String, Object>) geofenceObj;

                // Update geofence ID
                Object idObj = geofence.get("id");
                if (idObj instanceof Number geofenceId) {
                    updateState(CHANNEL_GEOFENCE_ID, new DecimalType(geofenceId.longValue()));
                }

                // Update geofence name
                Object nameObj = geofence.get("name");
                if (nameObj instanceof String geofenceName) {
                    updateState(CHANNEL_GEOFENCE_NAME, new StringType(geofenceName));
                    TraccarDeviceConfiguration configuration = config;
                    logger.info("Device {} {} geofence: {} (ID: {})",
                            configuration != null ? Integer.valueOf(configuration.deviceId) : "unknown", eventType,
                            geofenceName, idObj);
                }
            }

            // Also update position if included in the event
            Object positionObj = eventData.get("position");
            if (positionObj instanceof Map<?, ?>) {
                @SuppressWarnings("unchecked")
                Map<String, Object> position = (Map<String, Object>) positionObj;
                logger.debug("Updating position from geofence event");
                updatePositionChannels(position);
            }
        }
    }

    public @Nullable TraccarDeviceConfiguration getConfiguration() {
        return config;
    }
}
