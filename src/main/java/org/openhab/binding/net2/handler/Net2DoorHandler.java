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
import org.openhab.core.types.State;
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

        // Subscribe to door-specific SignalR events
        Net2SignalRClient signalRClient = bridgeHandler.getSignalRClient();
        if (signalRClient != null && signalRClient.isConnected()) {
            signalRClient.subscribeToDoorEvents(doorId);
            logger.info("Subscribed to door events for door ID: {}", doorId);
        } else {
            logger.debug("SignalR client not available yet, will subscribe later");
        }
    }

    /**
     * Called by server handler when SignalR connection is established
     */
    public void subscribeToSignalREvents() {
        logger.info("subscribeToSignalREvents() called for door {}", doorId);
        Net2ServerHandler bridge = bridgeHandler;
        if (bridge == null) {
            logger.warn("Bridge is null, cannot subscribe for door {}", doorId);
            return;
        }
        
        Net2SignalRClient signalRClient = bridge.getSignalRClient();
        logger.info("SignalR client for door {}: {}, connected: {}", doorId, 
            (signalRClient != null ? "exists" : "null"),
            (signalRClient != null ? signalRClient.isConnected() : "N/A"));
        
        if (signalRClient != null && signalRClient.isConnected()) {
            logger.info("Subscribing to door events for door ID: {}", doorId);
            signalRClient.subscribeToDoorEvents(doorId);
            logger.info("Door-specific subscription completed for door ID: {}", doorId);
        } else {
            logger.warn("SignalR client not available or not connected for door {}", doorId);
        }
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
                case Net2BindingConstants.CHANNEL_DOOR_CONTROL_TIMED:
                    handleDoorControlTimed(command);
                    break;
                default:
                    logger.debug("Unsupported channel: {}", channelUID.getId());
            }
        } catch (Exception e) {
            logger.error("Error handling command for channel {}", channelUID.getId(), e);
            updateStatus(ThingStatus.OFFLINE, ThingStatusDetail.COMMUNICATION_ERROR, "Error: " + e.getMessage());
        }
    }

    private void handleDoorControlTimed(Command command) throws Exception {
        logger.error("TEST LOG Net2DoorHandler: handleDoorControlTimed triggered with command: {}", command);
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
        String payload;
        try {
            // If command is a JSON string, use it directly
            String cmdStr = command.toString();
            if (cmdStr.trim().startsWith("{")) {
                payload = cmdStr;
            } else {
                // Otherwise, use defaults (customize as needed)
                JsonObject relayFunction = new JsonObject();
                relayFunction.addProperty("RelayId", "Relay1");
                relayFunction.addProperty("RelayAction", "TimedOpen");
                relayFunction.addProperty("RelayOpenTime", 500);
                JsonObject body = new JsonObject();
                body.addProperty("DoorId", doorId);
                body.add("RelayFunction", relayFunction);
                body.addProperty("LedFlash", 3);
                payload = body.toString();
            }
        } catch (Exception e) {
            logger.error("Failed to build JSON payload for controlTimed: {}", e.getMessage());
            return;
        }
        logger.debug("Sending advanced door control payload: {}", payload);
        if (apiClient.controlDoorFireAndForget(payload)) {
            // Command was accepted - update state to reflect the action
            if (command instanceof State) {
                updateState(Net2BindingConstants.CHANNEL_DOOR_CONTROL_TIMED, (State) command);
            }
        } else {
            logger.error("Failed to trigger fire-and-forget control for door {}", doorId);
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
            // Update last access time
            if (payload.has("eventTime") && !payload.get("eventTime").isJsonNull()) {
                updateState(Net2BindingConstants.CHANNEL_LAST_ACCESS_TIME,
                        new DateTimeType(payload.get("eventTime").getAsString()));
            }
            
            // Update last access user
            if (payload.has("userName") && !payload.get("userName").isJsonNull()) {
                updateState(Net2BindingConstants.CHANNEL_LAST_ACCESS_USER,
                        new StringType(payload.get("userName").getAsString()));
            }

            // Handle doorStatusEvents - These provide real door lock status
            if ("doorStatusEvents".equalsIgnoreCase(target) || "doorStatusEvent".equalsIgnoreCase(target)) {
                if (payload.has("status") && !payload.get("status").isJsonNull()) {
                    String status = payload.get("status").getAsString().toLowerCase();
                    OnOffType doorStatus;
                    
                    // Map door status to ON/OFF (adjust based on actual API values)
                    if ("open".equals(status) || "unlocked".equals(status) || "opened".equals(status)) {
                        doorStatus = OnOffType.ON;
                    } else if ("closed".equals(status) || "locked".equals(status)) {
                        doorStatus = OnOffType.OFF;
                    } else {
                        logger.debug("Unknown door status: {}", status);
                        return;
                    }
                    
                    updateState(Net2BindingConstants.CHANNEL_DOOR_STATUS, doorStatus);
                    logger.info("Door {} status updated to: {}", doorId, doorStatus);
                    
                    // Cancel any pending auto-off since we have real status
                    cancelStatusOff();
                }
            }
            
            // Handle doorEvents - Door open/closed physical events
            else if ("doorEvents".equalsIgnoreCase(target) || "doorEvent".equalsIgnoreCase(target)) {
                if (payload.has("state") && !payload.get("state").isJsonNull()) {
                    String state = payload.get("state").getAsString().toLowerCase();
                    OnOffType doorStatus;
                    
                    if ("open".equals(state) || "opened".equals(state)) {
                        doorStatus = OnOffType.ON;
                    } else if ("closed".equals(state)) {
                        doorStatus = OnOffType.OFF;
                    } else {
                        logger.debug("Unknown door event state: {}", state);
                        return;
                    }
                    
                    updateState(Net2BindingConstants.CHANNEL_DOOR_STATUS, doorStatus);
                    logger.info("Door {} physical state changed to: {}", doorId, doorStatus);
                    
                    // Cancel any pending auto-off since we have real status
                    cancelStatusOff();
                }
            }
            
            // Handle liveEvents - Access events with eventType-based state tracking
            else if ("LiveEvents".equalsIgnoreCase(target) || "liveEvents".equalsIgnoreCase(target)) {
                if (payload.has("eventType") && !payload.get("eventType").isJsonNull()) {
                    int eventType = payload.get("eventType").getAsInt();
                    
                    // eventType 28 = Door relay opened (timed)
                    // eventType 46 = Door forced/held open
                    // eventType 47 = Door closed/secured
                    // eventType 20 = Access granted
                    
                    if (eventType == 47) {
                        // Door closed - update door-action and status to OFF, cancel any timers
                        updateState(Net2BindingConstants.CHANNEL_DOOR_ACTION, OnOffType.OFF);
                        updateState(Net2BindingConstants.CHANNEL_DOOR_STATUS, OnOffType.OFF);
                        cancelStatusOff();
                        logger.info("Door {} closed (eventType 47)", doorId);
                    } else if (eventType == 28 || eventType == 46 || eventType == 20) {
                        // Door opened/accessed
                        // Update status to ON
                        updateState(Net2BindingConstants.CHANNEL_DOOR_STATUS, OnOffType.ON);
                        
                        // For door-action channel, update to ON and keep it there (no timer)
                        // The state will persist until we receive eventType 47 (close)
                        updateState(Net2BindingConstants.CHANNEL_DOOR_ACTION, OnOffType.ON);
                        
                        // For door-control-timed, we still auto-off after 5 seconds
                        // This provides feedback for timed operations
                        scheduleStatusOff();
                        
                        logger.info("Door {} opened (eventType {})", doorId, eventType);
                    }
                }
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
                    // Update door status from API poll
                    if (doorStatus.has("status") && doorStatus.get("status").isJsonObject()) {
                        JsonObject statusObj = doorStatus.get("status").getAsJsonObject();
                        
                        // Check doorRelayOpen field - true means door is open
                        boolean doorRelayOpen = statusObj.has("doorRelayOpen") && statusObj.get("doorRelayOpen").getAsBoolean();
                        OnOffType status = doorRelayOpen ? OnOffType.ON : OnOffType.OFF;
                        
                        logger.info("updateFromApiResponse: Door {} doorRelayOpen={} -> {}", doorId, doorRelayOpen, status);
                        
                        // Update both door-action and door-status channels to sync with actual state
                        updateState(Net2BindingConstants.CHANNEL_DOOR_ACTION, status);
                        updateState(Net2BindingConstants.CHANNEL_DOOR_STATUS, status);
                        
                        if (status == OnOffType.OFF) {
                            // Door is closed, cancel any pending timers
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
