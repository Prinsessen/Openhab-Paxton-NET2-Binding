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

            // Odometer - Teltonika uses totalDistance, OSMand uses odometer
            Object odometerObj = null;
            if ("teltonika".equalsIgnoreCase(protocol)) {
                // Teltonika: Always use totalDistance, ignore odometer
                odometerObj = attributes.get("totalDistance");
                logger.debug("Teltonika protocol: Using totalDistance for odometer: {}", odometerObj);
            } else {
                // Other protocols (OSMand): Try odometer first, fallback to totalDistance
                odometerObj = attributes.get("odometer");
                if (odometerObj == null) {
                    odometerObj = attributes.get("totalDistance");
                    logger.debug("Using totalDistance for odometer: {}", odometerObj);
                } else {
                    logger.debug("Using odometer attribute: {}", odometerObj);
                }
            }
            if (odometerObj instanceof Number) {
                double odometerMeters = ((Number) odometerObj).doubleValue();
                logger.debug("Odometer: {} meters", odometerMeters);
                updateState(CHANNEL_ODOMETER, new QuantityType<>(odometerMeters, SIUnits.METRE));
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
                // Convert RSSI to percentage (typical range: -113 to -51 dBm)
                // Using formula: percentage = 2 * (rssi + 113)
                double signalPercent = Math.max(0, Math.min(100, 2 * (rssi + 113)));
                updateState(CHANNEL_GSM_SIGNAL, new QuantityType<>(signalPercent, Units.PERCENT));
            } else {
                // Try alternative attribute name "gsm"
                Object gsmObj = attributes.get("gsm");
                if (gsmObj instanceof Number) {
                    double gsm = ((Number) gsmObj).doubleValue();
                    updateState(CHANNEL_GSM_SIGNAL, new QuantityType<>(gsm, Units.PERCENT));
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
