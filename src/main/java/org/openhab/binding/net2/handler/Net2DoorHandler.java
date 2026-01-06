/*
 * Copyright (c) 2010-2025 Contributors to the openHAB project
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
package org.openhab.binding.net2.handler;

import java.util.concurrent.ScheduledFuture;
import java.util.concurrent.TimeUnit;

import org.eclipse.jdt.annotation.NonNullByDefault;
import org.eclipse.jdt.annotation.Nullable;
import org.openhab.binding.net2.Net2BindingConstants;
import org.openhab.core.library.types.DateTimeType;
import org.openhab.core.library.types.OnOffType;
import org.openhab.core.library.types.StringType;
import org.openhab.core.thing.ChannelUID;
import org.openhab.core.thing.Thing;
import org.openhab.core.thing.ThingStatus;
import org.openhab.core.thing.ThingStatusDetail;
import org.openhab.core.thing.binding.BaseThingHandler;
import org.openhab.core.types.Command;
import org.openhab.core.types.UnDefType;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.google.gson.JsonArray;
import com.google.gson.JsonObject;

/**
 * The {@link Net2DoorHandler} is responsible for handling commands, which are
 * sent to one of the channels.
 *
 * @author openHAB Community - Initial contribution
 */
@NonNullByDefault
public class Net2DoorHandler extends BaseThingHandler {

    private final Logger logger = LoggerFactory.getLogger(Net2DoorHandler.class);

    private @Nullable Net2ServerHandler bridgeHandler;
    private int doorId;
    private @Nullable ScheduledFuture<?> statusReset;

    public Net2DoorHandler(Thing thing) {
        super(thing);
    }

    @Override
    public void initialize() {
        logger.debug("Initializing Net2 Door handler for door {}", getThing().getUID());

        // Get bridge handler
        var bridge = getBridge();
        if (bridge == null) {
            updateStatus(ThingStatus.OFFLINE, ThingStatusDetail.BRIDGE_OFFLINE, "No bridge configured");
            return;
        }
        var handler = bridge.getHandler();
        if (!(handler instanceof Net2ServerHandler)) {
            updateStatus(ThingStatus.OFFLINE, ThingStatusDetail.BRIDGE_OFFLINE, "Bridge handler not available");
            return;
        }
        bridgeHandler = (Net2ServerHandler) handler;
        if (bridgeHandler == null) {
            updateStatus(ThingStatus.OFFLINE, ThingStatusDetail.BRIDGE_OFFLINE, "Bridge handler not available");
            return;
        }

        // Get configuration
        Net2DoorConfiguration config = getConfigAs(Net2DoorConfiguration.class);

        if (config.doorId == null || config.doorId <= 0) {
            updateStatus(ThingStatus.OFFLINE, ThingStatusDetail.CONFIGURATION_ERROR, "Valid Door ID is required");
            return;
        }

        this.doorId = config.doorId;
        updateStatus(ThingStatus.ONLINE);
    }

    @Override
    public void handleCommand(ChannelUID channelUID, Command command) {
        Net2ServerHandler bridge = bridgeHandler;
        if (command == null || bridge == null || !bridge.isOnline()) {
            return;
        }

        try {
            switch (channelUID.getId()) {
                case Net2BindingConstants.CHANNEL_DOOR_ACTION:
                    handleDoorAction(command);
                    break;
                default:
                    logger.debug("Unsupported channel: {}", channelUID.getId());
            }
        } catch (Exception e) {
            logger.error("Error handling command for channel {}", channelUID.getId(), e);
            updateStatus(ThingStatus.OFFLINE, ThingStatusDetail.COMMUNICATION_ERROR, "Error: " + e.getMessage());
        }
    }

    private void handleDoorAction(Command command) throws Exception {
        Net2ServerHandler bridge = bridgeHandler;
        if (bridge == null) {
            logger.error("Bridge handler not available");
            return;
        }
        Net2ApiClient apiClient = bridge.getApiClient();
        if (apiClient == null) {
            logger.error("API client not available");
            return;
        }

        if (command == OnOffType.ON) {
            // Hold door open
            logger.debug("Opening door {}", doorId);
            if (apiClient.holdDoorOpen(doorId)) {
                updateState(Net2BindingConstants.CHANNEL_DOOR_ACTION, OnOffType.ON);
                updateState(Net2BindingConstants.CHANNEL_DOOR_STATUS, OnOffType.ON);
            } else {
                logger.error("Failed to open door {}", doorId);
            }
        } else if (command == OnOffType.OFF) {
            // Close door
            logger.debug("Closing door {}", doorId);
            if (apiClient.closeDoor(doorId)) {
                updateState(Net2BindingConstants.CHANNEL_DOOR_ACTION, OnOffType.OFF);
                updateState(Net2BindingConstants.CHANNEL_DOOR_STATUS, OnOffType.OFF);
            } else {
                logger.error("Failed to close door {}", doorId);
            }
        }
    }

    public int getDoorId() {
        return doorId;
    }

    public void applyEvent(JsonObject payload, String target) {
        logger.info("Applying SignalR event: target={}, payload={}", target, payload);
        try {
            if (payload.has("eventTime") && !payload.get("eventTime").isJsonNull()) {
                updateState(Net2BindingConstants.CHANNEL_LAST_ACCESS_TIME,
                        new DateTimeType(payload.get("eventTime").getAsString()));
            }
            if (payload.has("userName") && !payload.get("userName").isJsonNull()) {
                updateState(Net2BindingConstants.CHANNEL_LAST_ACCESS_USER,
                        new StringType(payload.get("userName").getAsString()));
            }

            // Any LiveEvents or doorEvents for this door sets status ON with auto-off after 5 seconds
            if ("LiveEvents".equalsIgnoreCase(target) || "doorEvents".equalsIgnoreCase(target)) {
                updateState(Net2BindingConstants.CHANNEL_DOOR_STATUS, OnOffType.ON);
                scheduleStatusOff();
            }
        } catch (Exception e) {
            logger.debug("Failed to apply SignalR event", e);
        }
    }

    /**
     * Update state from API response
     */
    public void updateFromApiResponse(JsonArray doorStatusArray) {
        try {
            for (int i = 0; i < doorStatusArray.size(); i++) {
                JsonObject doorStatus = doorStatusArray.get(i).getAsJsonObject();

                if (doorStatus.has("id") && doorStatus.get("id").getAsInt() == doorId) {
                    // Update door status
                    if (doorStatus.has("state")) {
                        String state = doorStatus.get("state").getAsString();
                        OnOffType status = "open".equalsIgnoreCase(state) ? OnOffType.ON : OnOffType.OFF;
                        updateState(Net2BindingConstants.CHANNEL_DOOR_STATUS, status);
                        if (status == OnOffType.ON) {
                            scheduleStatusOff();
                        } else {
                            cancelStatusOff();
                        }
                    }

                    // Update last access user
                        if (doorStatus.has("lastAccessUser") && !doorStatus.get("lastAccessUser").isJsonNull()) {
                            updateState(Net2BindingConstants.CHANNEL_LAST_ACCESS_USER,
                                    new StringType(doorStatus.get("lastAccessUser").getAsString()));
                        }

                    // Update last access time
                        if (doorStatus.has("lastAccessTime") && !doorStatus.get("lastAccessTime").isJsonNull()) {
                            updateState(Net2BindingConstants.CHANNEL_LAST_ACCESS_TIME,
                                    new DateTimeType(doorStatus.get("lastAccessTime").getAsString()));
                        }

                    return;
                }
            }
        } catch (Exception e) {
            logger.debug("Error updating from API response", e);
        }
    }

    @Override
    public void bridgeStatusChanged(org.openhab.core.thing.ThingStatusInfo bridgeStatusInfo) {
        if (bridgeStatusInfo.getStatus() == ThingStatus.ONLINE) {
            updateStatus(ThingStatus.ONLINE);
        } else {
            updateStatus(ThingStatus.OFFLINE, ThingStatusDetail.BRIDGE_OFFLINE);
        }
    }
    
    private void scheduleStatusOff() {
        cancelStatusOff();
        statusReset = scheduler.schedule(() -> updateState(Net2BindingConstants.CHANNEL_DOOR_STATUS, OnOffType.OFF), 5,
                TimeUnit.SECONDS);
    }
    
    private void cancelStatusOff() {
        ScheduledFuture<?> future = statusReset;
        if (future != null && !future.isDone()) {
            future.cancel(false);
        }
    }
}
