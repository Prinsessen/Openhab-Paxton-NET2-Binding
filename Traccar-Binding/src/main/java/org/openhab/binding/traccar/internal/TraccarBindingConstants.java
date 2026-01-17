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
    public static final String CHANNEL_MOTION = "motion";
    public static final String CHANNEL_ADDRESS = "address";
}
