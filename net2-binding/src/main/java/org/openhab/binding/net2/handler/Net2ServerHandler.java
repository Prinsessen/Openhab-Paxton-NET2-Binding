package org.openhab.binding.net2.handler;

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

import java.io.IOException;
import java.time.ZonedDateTime;
import java.time.format.DateTimeFormatter;
import java.util.concurrent.ScheduledFuture;
import java.util.concurrent.TimeUnit;

/**
 * The {@link Net2ServerHandler} is responsible for handling communication
 * with the Paxton Net2 API server.
 */
public class Net2ServerHandler extends BaseBridgeHandler {

    private final Logger logger = LoggerFactory.getLogger(Net2ServerHandler.class);

    private ScheduledFuture<?> refreshJob;
    private Net2ApiClient apiClient;

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

        Bridge bridge = getThing();
        Net2ServerConfiguration config = getConfigAs(Net2ServerConfiguration.class);

        // Validate configuration
        if (config.hostname == null || config.hostname.isEmpty()) {
            updateStatus(ThingStatus.OFFLINE, ThingStatusDetail.CONFIGURATION_ERROR,
                    "Hostname is required");
            return;
        }
        if (config.username == null || config.username.isEmpty()) {
            updateStatus(ThingStatus.OFFLINE, ThingStatusDetail.CONFIGURATION_ERROR,
                    "Username is required");
            return;
        }
        if (config.password == null || config.password.isEmpty()) {
            updateStatus(ThingStatus.OFFLINE, ThingStatusDetail.CONFIGURATION_ERROR,
                    "Password is required");
            return;
        }
        if (config.clientId == null || config.clientId.isEmpty()) {
            updateStatus(ThingStatus.OFFLINE, ThingStatusDetail.CONFIGURATION_ERROR,
                    "Client ID is required");
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
            
            // Schedule periodic refresh
            int refreshInterval = config.refreshInterval > 0 ? config.refreshInterval : 30;
            refreshJob = scheduler.scheduleWithFixedDelay(this::refreshDoorStatus, 0, refreshInterval, TimeUnit.SECONDS);
            
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
    }

    /**
     * Refresh door status for all child things
     */
    private void refreshDoorStatus() {
        if (apiClient == null || !apiClient.isAuthenticated()) {
            try {
                if (!apiClient.authenticate()) {
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
            String statusResponse = apiClient.getDoorStatus();
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
    public Net2ApiClient getApiClient() {
        return apiClient;
    }

    /**
     * Check if bridge is online
     */
    public boolean isOnline() {
        return getThing().getStatus() == ThingStatus.ONLINE && apiClient != null && apiClient.isAuthenticated();
    }
}
