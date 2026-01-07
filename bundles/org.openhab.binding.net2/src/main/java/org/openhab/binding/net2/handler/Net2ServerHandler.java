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
import org.openhab.core.thing.Bridge;
import org.openhab.core.thing.ChannelUID;
import org.openhab.core.thing.ThingStatus;
import org.openhab.core.thing.ThingStatusDetail;
import org.openhab.core.thing.binding.BaseBridgeHandler;
import org.openhab.core.types.Command;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;

/**
 * The {@link Net2ServerHandler} is responsible for handling communication
 * with the Paxton Net2 API server.
 *
 * @author openHAB Community - Initial contribution
 */
@NonNullByDefault
public class Net2ServerHandler extends BaseBridgeHandler {

    private final Logger logger = LoggerFactory.getLogger(Net2ServerHandler.class);

    private @Nullable ScheduledFuture<?> refreshJob;
    private @Nullable Net2ApiClient apiClient;
    private @Nullable Net2SignalRClient signalRClient;

    public Net2ServerHandler(Bridge bridge) {
        super(bridge);
    }

    @Override
    public void handleCommand(ChannelUID channelUID, Command command) {
        // Bridge has no channels to command
    }

    @Override
    public void initialize() {
        logger.debug("Initializing Net2 Server handler");

        Net2ServerConfiguration config = getConfigAs(Net2ServerConfiguration.class);

        // Validate configuration
        if (config.hostname == null || config.hostname.isEmpty()) {
            updateStatus(ThingStatus.OFFLINE, ThingStatusDetail.CONFIGURATION_ERROR, "Hostname is required");
            return;
        }
        if (config.username == null || config.username.isEmpty()) {
            updateStatus(ThingStatus.OFFLINE, ThingStatusDetail.CONFIGURATION_ERROR, "Username is required");
            return;
        }
        if (config.password == null || config.password.isEmpty()) {
            updateStatus(ThingStatus.OFFLINE, ThingStatusDetail.CONFIGURATION_ERROR, "Password is required");
            return;
        }
        if (config.clientId == null || config.clientId.isEmpty()) {
            updateStatus(ThingStatus.OFFLINE, ThingStatusDetail.CONFIGURATION_ERROR, "Client ID is required");
            return;
        }

        // Create API client
        try {
            apiClient = new Net2ApiClient(config);

            // Test authentication
            if (!apiClient.authenticate()) {
                updateStatus(ThingStatus.OFFLINE, ThingStatusDetail.COMMUNICATION_ERROR,
                        "Failed to authenticate with Net2 server");
                return;
            }

            updateStatus(ThingStatus.ONLINE);

            Net2ApiClient client = apiClient;
            if (client != null) {
                startSignalR(client, config);
            }

            // Schedule periodic refresh
            int refreshInterval = config.refreshInterval > 0 ? config.refreshInterval : 30;
            refreshJob = scheduler.scheduleWithFixedDelay(this::refreshDoorStatus, 0, refreshInterval,
                    TimeUnit.SECONDS);
        } catch (Exception e) {
            logger.error("Failed to initialize Net2 API client", e);
            updateStatus(ThingStatus.OFFLINE, ThingStatusDetail.COMMUNICATION_ERROR,
                    "Error initializing API: " + e.getMessage());
        }
    }

    @Override
    public void dispose() {
        logger.debug("Disposing Net2 Server handler");

        if (refreshJob != null) {
            refreshJob.cancel(true);
            refreshJob = null;
        }

        if (apiClient != null) {
            apiClient.close();
        }

        if (signalRClient != null) {
            signalRClient.disconnect();
            signalRClient = null;
        }
    }

    private void startSignalR(Net2ApiClient client, Net2ServerConfiguration config) {
        if (signalRClient != null && signalRClient.isConnected()) {
            return;
        }

        try {
            String token = client.getValidAccessToken();
            boolean verify = config.tlsVerification != null ? config.tlsVerification : true;
            Net2SignalRClient newClient = new Net2SignalRClient(client.getServerRootUri(), token, verify);
            newClient.setEventConsumer(this::handleSignalREvent);
            newClient.connect();
            newClient.subscribeToEvents();
            signalRClient = newClient;
        } catch (Exception e) {
            logger.debug("SignalR startup failed", e);
        }
    }

    private void handleSignalREvent(String target, JsonObject payload) {
        if (!payload.has("deviceId")) {
            return;
        }

        int deviceId = payload.get("deviceId").getAsInt();
        getThing().getThings().forEach(childThing -> {
            if (childThing.getHandler() instanceof Net2DoorHandler handler && handler.getDoorId() == deviceId) {
                handler.applyEvent(payload, target);
            }
        });
    }

    /**
     * Refresh door status for all child things
     */
    private void refreshDoorStatus() {
        Net2ApiClient client = apiClient;
        if (client == null || !client.isAuthenticated()) {
            try {
                if (client == null) {
                    logger.error("API client not initialized");
                    return;
                }
                if (!client.authenticate()) {
                    updateStatus(ThingStatus.OFFLINE, ThingStatusDetail.COMMUNICATION_ERROR,
                            "Failed to re-authenticate");
                    return;
                }
            } catch (Exception e) {
                logger.error("Authentication error during refresh", e);
                return;
            }
        }

        try {
            String statusResponse = client.getDoorStatus();
            // Note: SignalR is started once during initialization, not on every refresh
            JsonElement element = JsonParser.parseString(statusResponse);

            if (element.isJsonArray()) {
                // Notify child handlers of status update
                getThing().getThings().forEach(childThing -> {
                    Net2DoorHandler handler = (Net2DoorHandler) childThing.getHandler();
                    if (handler != null) {
                        handler.updateFromApiResponse(element.getAsJsonArray());
                    }
                });
            }

            if (getThing().getStatus() != ThingStatus.ONLINE) {
                updateStatus(ThingStatus.ONLINE);
            }
        } catch (Exception e) {
            logger.debug("Error refreshing door status", e);
            updateStatus(ThingStatus.OFFLINE, ThingStatusDetail.COMMUNICATION_ERROR,
                    "Error refreshing: " + e.getMessage());
        }
    }

    /**
     * Get the API client for child door handlers
     */
    public @Nullable Net2ApiClient getApiClient() {
        return apiClient;
    }

    /**
     * Check if bridge is online
     */
    public boolean isOnline() {
        Net2ApiClient client = apiClient;
        return getThing().getStatus() == ThingStatus.ONLINE && client != null && client.isAuthenticated();
    }
}
