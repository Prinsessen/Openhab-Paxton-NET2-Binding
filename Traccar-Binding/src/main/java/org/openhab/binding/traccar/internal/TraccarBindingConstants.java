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

import java.util.Set;

import org.eclipse.jdt.annotation.NonNullByDefault;
import org.openhab.core.thing.ThingTypeUID;

/**
 * The {@link TraccarBindingConstants} class defines common constants, which are
 * used across the whole binding.
 *
 * @author Nanna Agesen - Initial contribution
 */
@NonNullByDefault
public class TraccarBindingConstants {

    private static final String BINDING_ID = "traccar";

    // List of all Thing Type UIDs
    public static final ThingTypeUID THING_TYPE_SERVER = new ThingTypeUID(BINDING_ID, "server");
    public static final ThingTypeUID THING_TYPE_DEVICE = new ThingTypeUID(BINDING_ID, "device");

    public static final Set<ThingTypeUID> SUPPORTED_THING_TYPES_UIDS = Set.of(THING_TYPE_SERVER, THING_TYPE_DEVICE);

    // List of all Channel ids
    public static final String CHANNEL_GEOFENCE_EVENT = "geofenceEvent";
    public static final String CHANNEL_GEOFENCE_ID = "geofenceId";
    public static final String CHANNEL_POSITION = "position";
    public static final String CHANNEL_LAST_UPDATE = "lastUpdate";
    public static final String CHANNEL_STATUS = "status";
    public static final String CHANNEL_SPEED = "speed";
    public static final String CHANNEL_GEOFENCE_NAME = "geofenceName";
    public static final String CHANNEL_COURSE = "course";
    public static final String CHANNEL_ACCURACY = "accuracy";
    public static final String CHANNEL_BATTERY_LEVEL = "batteryLevel";
    public static final String CHANNEL_ODOMETER = "odometer";
    public static final String CHANNEL_TOTAL_DISTANCE = "totalDistance";
    public static final String CHANNEL_MOTION = "motion";
    public static final String CHANNEL_ADDRESS = "address";
    public static final String CHANNEL_GPS_SAT = "gpsSatellites";
    public static final String CHANNEL_GSM_SIGNAL = "gsmSignal";
    public static final String CHANNEL_HOURS = "hours";
    public static final String CHANNEL_EVENT = "event";
    public static final String CHANNEL_ALTITUDE = "altitude";
    public static final String CHANNEL_VALID = "valid";
    public static final String CHANNEL_DISTANCE = "distance";
    public static final String CHANNEL_ACTIVITY = "activity";
    public static final String CHANNEL_PROTOCOL = "protocol";

    // OBD-II Channels (Teltonika FMM920 with Bluetooth OBD-II dongle)
    public static final String CHANNEL_OBD_DTC_COUNT = "obdDtcCount";
    public static final String CHANNEL_OBD_ENGINE_LOAD = "obdEngineLoad";
    public static final String CHANNEL_OBD_COOLANT_TEMP = "obdCoolantTemp";
    public static final String CHANNEL_OBD_SHORT_FUEL_TRIM = "obdShortFuelTrim";
    public static final String CHANNEL_OBD_FUEL_PRESSURE = "obdFuelPressure";
    public static final String CHANNEL_OBD_RPM = "obdRpm";
    public static final String CHANNEL_OBD_RPM_REPORTED = "obdRpmReported";
    public static final String CHANNEL_OBD_SPEED = "obdSpeed";
    public static final String CHANNEL_OBD_FUEL_LEVEL = "obdFuelLevel";
    public static final String CHANNEL_OBD_OEM_ODOMETER = "obdOemOdometer";
    public static final String CHANNEL_IGNITION = "ignition";

    // Additional Teltonika/GPS Channels
    public static final String CHANNEL_PDOP = "pdop";
    public static final String CHANNEL_HDOP = "hdop";
    public static final String CHANNEL_POWER = "power";
    public static final String CHANNEL_BATTERY = "battery";
    public static final String CHANNEL_OPERATOR = "operator";
    public static final String CHANNEL_VIN = "vin";

    // Additional Teltonika IO Channels (experimental/unknown)
    public static final String CHANNEL_IO42 = "io42";
    public static final String CHANNEL_IO49 = "io49";
    public static final String CHANNEL_IO51 = "io51";
    public static final String CHANNEL_TRIP_DISTANCE = "tripDistance";
    public static final String CHANNEL_EVENT_CODE = "eventCode";

    // OBD-II Trip Meters from ECU
    public static final String CHANNEL_IO199 = "io199";
    public static final String CHANNEL_IO205 = "io205";
    public static final String CHANNEL_IO389 = "io389";
}
