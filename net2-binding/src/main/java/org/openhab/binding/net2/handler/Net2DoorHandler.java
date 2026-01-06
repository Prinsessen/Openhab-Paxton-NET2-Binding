package org.openhab.binding.net2.handler;

import org.openhab.binding.net2.Net2BindingConstants;
import org.openhab.core.thing.ChannelUID;
import org.openhab.core.thing.Thing;
import org.openhab.core.thing.ThingStatus;
import org.openhab.core.thing.ThingStatusDetail;
import org.openhab.core.thing.binding.BaseThingHandler;
import org.openhab.core.types.Command;
import org.openhab.core.types.OnOffType;
import org.openhab.core.types.UnDefType;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.google.gson.JsonArray;
import com.google.gson.JsonObject;

/**
 * The {@link Net2DoorHandler} is responsible for handling commands, which are
 * sent to one of the channels.
 */
public class Net2DoorHandler extends BaseThingHandler {

    private final Logger logger = LoggerFactory.getLogger(Net2DoorHandler.class);

    private Net2ServerHandler bridgeHandler;
    private int doorId;

    public Net2DoorHandler(Thing thing) {
        super(thing);
    }

    @Override
    public void initialize() {
        logger.debug("Initializing Net2 Door handler for door {}", getThing().getUID());

        // Get bridge handler
        bridgeHandler = (Net2ServerHandler) getBridge().getHandler();
        if (bridgeHandler == null) {
            updateStatus(ThingStatus.OFFLINE, ThingStatusDetail.BRIDGE_OFFLINE,
                    "Bridge handler not available");
            return;
        }

        // Get configuration
        Net2DoorConfiguration config = getConfigAs(Net2DoorConfiguration.class);
        
        if (config.doorId == null || config.doorId <= 0) {
            updateStatus(ThingStatus.OFFLINE, ThingStatusDetail.CONFIGURATION_ERROR,
                    "Valid Door ID is required");
            return;
        }

        this.doorId = config.doorId;
        updateStatus(ThingStatus.ONLINE);
    }

    @Override
    public void handleCommand(ChannelUID channelUID, Command command) {
        if (command == null || !bridgeHandler.isOnline()) {
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
            updateStatus(ThingStatus.OFFLINE, ThingStatusDetail.COMMUNICATION_ERROR,
                    "Error: " + e.getMessage());
        }
    }

    private void handleDoorAction(Command command) throws Exception {
        Net2ApiClient apiClient = bridgeHandler.getApiClient();
        
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
                    }

                    // Update last access user
                    if (doorStatus.has("lastAccessUser") && !doorStatus.get("lastAccessUser").isJsonNull()) {
                        updateState(Net2BindingConstants.CHANNEL_LAST_ACCESS_USER,
                                new org.openhab.core.types.StringType(doorStatus.get("lastAccessUser").getAsString()));
                    } else {
                        updateState(Net2BindingConstants.CHANNEL_LAST_ACCESS_USER, UnDefType.UNDEF);
                    }

                    // Update last access time
                    if (doorStatus.has("lastAccessTime") && !doorStatus.get("lastAccessTime").isJsonNull()) {
                        try {
                            String timeStr = doorStatus.get("lastAccessTime").getAsString();
                            org.openhab.core.types.DateTimeType dateTime =
                                    new org.openhab.core.types.DateTimeType(timeStr);
                            updateState(Net2BindingConstants.CHANNEL_LAST_ACCESS_TIME, dateTime);
                        } catch (Exception e) {
                            logger.debug("Failed to parse last access time: {}", e.getMessage());
                        }
                    } else {
                        updateState(Net2BindingConstants.CHANNEL_LAST_ACCESS_TIME, UnDefType.UNDEF);
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
}
