package org.openhab.binding.net2.handler;

import org.openhab.core.thing.Bridge;
import org.openhab.core.thing.ChannelUID;
import org.openhab.core.thing.ThingStatus;
import org.openhab.core.thing.ThingStatusDetail;
import org.openhab.core.thing.binding.BaseBridgeHandler;
import org.openhab.core.types.Command;
import org.openhab.core.library.types.StringType;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;

import java.io.IOException;
import java.time.ZonedDateTime;
import java.time.format.DateTimeFormatter;
import java.util.Map;
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
    private Net2SignalRClient signalRClient;

    public Net2ServerHandler(Bridge bridge) {
        super(bridge);
    }

    @Override
    public void handleCommand(ChannelUID channelUID, Command command) {
        String channelId = channelUID.getId();
        try {
            switch (channelId) {
                case org.openhab.binding.net2.Net2BindingConstants.CHANNEL_CREATE_USER:
                    handleCreateUser(command);
                    break;
                case org.openhab.binding.net2.Net2BindingConstants.CHANNEL_DELETE_USER:
                    handleDeleteUser(command);
                    break;
                case org.openhab.binding.net2.Net2BindingConstants.CHANNEL_LIST_ACCESS_LEVELS:
                    handleListAccessLevels(command);
                    break;
                default:
                    // No-op for unknown bridge channel
                    break;
            }
        } catch (Exception e) {
            logger.error("Error handling command for channel {}: {}", channelId, e.getMessage());
        }
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

        // Set status to UNKNOWN during initialization
        updateStatus(ThingStatus.UNKNOWN, ThingStatusDetail.CONFIGURATION_PENDING, "Connecting to Net2 server...");

        // Create API client and authenticate in background to avoid blocking openHAB startup
        scheduler.execute(() -> {
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
                
                // Start SignalR for live events (best-effort)
                try {
                    String token = apiClient.getAccessToken();
                    if (token != null && !token.isEmpty()) {
                        signalRClient = new Net2SignalRClient(apiClient.getHostname(), apiClient.getPort(), token,
                                apiClient.isTlsVerification());
                        signalRClient.onDoorStatusChanged(msg -> logger.debug("SignalR event: {}", msg));
                        signalRClient.connect();
                    } else {
                        logger.debug("No access token available for SignalR startup");
                    }
                } catch (Exception se) {
                    logger.debug("SignalR startup failed", se);
                }
                
            } catch (Exception e) {
                logger.error("Failed to initialize Net2 API client", e);
                updateStatus(ThingStatus.OFFLINE, ThingStatusDetail.COMMUNICATION_ERROR,
                        "Error initializing API: " + e.getMessage());
            }
        });
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
            try { signalRClient.disconnect(); } catch (Exception ignore) {}
            signalRClient = null;
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

    private void handleCreateUser(Command command) throws Exception {
        Net2ApiClient client = apiClient;
        if (client == null) {
            logger.error("API client not available");
            return;
        }

        if (command instanceof StringType) {
            String userData = command.toString();
            // Expected format: firstName,lastName,accessLevel,pin
            String[] parts = userData.split(",");
            if (parts.length >= 4) {
                String firstName = parts[0].trim();
                String lastName = parts[1].trim();
                String accessLevelStr = parts[2].trim();
                String pin = parts[3].trim();

                logger.info("Creating user: {} {}, accessLevel: {}, pin: {}", firstName, lastName, accessLevelStr, pin);

                Integer accessLevelId = null;
                try {
                    accessLevelId = client.resolveAccessLevelId(accessLevelStr);
                } catch (Exception ex) {
                    logger.warn("Unable to resolve access level '{}': {}", accessLevelStr, ex.getMessage());
                }
                if (accessLevelId == null) {
                    logger.warn("Access level '{}' not found among system access levels; proceeding without assignment.", accessLevelStr);
                } else {
                    logger.info("Resolved access level '{}' to ID {}", accessLevelStr, accessLevelId);
                }

                int userId = client.addUser(firstName, lastName, "", pin, "");
                if (userId > 0) {
                    logger.info("User created successfully with ID: {}", userId);

                    if (accessLevelId == null) {
                        logger.warn("User {} created without assigning access level (no valid ID resolved)", userId);
                    } else {
                        try {
                            boolean assigned = client.assignAccessLevels(userId, accessLevelId);
                            if (assigned) {
                                logger.info("Access level {} assigned successfully to user {}", accessLevelId, userId);
                            } else {
                                logger.error("Failed to assign access level {} to user {}", accessLevelId, userId);
                            }
                        } catch (Exception ex) {
                            logger.error("Error assigning access level {} to user {}: {}", accessLevelId, userId, ex.getMessage());
                        }
                    }
                } else {
                    logger.error("Failed to create user");
                }
            } else {
                logger.error("Invalid user data format. Expected: firstName,lastName,accessLevel,pin");
            }
        }
    }

    private void handleDeleteUser(Command command) throws Exception {
        Net2ApiClient client = apiClient;
        if (client == null) {
            logger.error("API client not available");
            return;
        }

        if (command instanceof StringType) {
            String userIdentifier = command.toString();
            logger.info("Deleting user: {}", userIdentifier);
            if (client.deleteUser(userIdentifier)) {
                logger.info("User deleted successfully");
            } else {
                logger.error("Failed to delete user");
            }
        }
    }

    private void handleListAccessLevels(Command command) throws Exception {
        Net2ApiClient client = apiClient;
        if (client == null) {
            logger.error("API client not available");
            return;
        }
        Map<Integer, String> levels = client.listAccessLevels();
        if (levels.isEmpty()) {
            logger.warn("No access levels returned by API");
            return;
        }
        StringBuilder sb = new StringBuilder("Access levels: ");
        levels.forEach((id, name) -> sb.append("[" + id + ":" + name + "] "));
        logger.info(sb.toString());
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
