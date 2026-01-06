package org.openhab.binding.net2.discovery;

import org.openhab.binding.net2.Net2BindingConstants;
import org.openhab.binding.net2.handler.Net2ApiClient;
import org.openhab.binding.net2.handler.Net2ServerHandler;
import org.openhab.core.config.discovery.AbstractDiscoveryService;
import org.openhab.core.config.discovery.DiscoveryResult;
import org.openhab.core.config.discovery.DiscoveryResultBuilder;
import org.openhab.core.thing.ThingTypeUID;
import org.openhab.core.thing.ThingUID;
import org.openhab.core.thing.binding.ThingHandlerService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;

import java.util.Set;
import java.util.concurrent.TimeUnit;

/**
 * Discovery service for Net2 doors
 */
public class Net2DoorDiscoveryService extends AbstractThingHandlerDiscoveryService<Net2ServerHandler>
        implements ThingHandlerService {

    private final Logger logger = LoggerFactory.getLogger(Net2DoorDiscoveryService.class);
    private static final int SEARCH_TIME = 30;

    public Net2DoorDiscoveryService() {
        super(Net2ServerHandler.class, Set.of(new ThingTypeUID(Net2BindingConstants.BINDING_ID,
                Net2BindingConstants.THING_TYPE_DOOR)), SEARCH_TIME);
    }

    @Override
    protected void startScan() {
        logger.debug("Starting Net2 door discovery");
        
        try {
            Net2ApiClient apiClient = thingHandler.getApiClient();
            if (apiClient == null || !apiClient.isAuthenticated()) {
                logger.warn("Net2 server not authenticated, cannot discover doors");
                return;
            }

            String doorsJson = apiClient.listDoors();
            JsonArray doors = JsonParser.parseString(doorsJson).getAsJsonArray();

            for (int i = 0; i < doors.size(); i++) {
                JsonObject door = doors.get(i).getAsJsonObject();
                
                if (door.has("id") && door.has("name")) {
                    int doorId = door.get("id").getAsInt();
                    String doorName = door.get("name").getAsString();

                    ThingUID thingUID = new ThingUID(
                            new ThingTypeUID(Net2BindingConstants.BINDING_ID,
                                    Net2BindingConstants.THING_TYPE_DOOR),
                            thingHandler.getThing().getUID(),
                            String.valueOf(doorId));

                    DiscoveryResult result = DiscoveryResultBuilder.create(thingUID)
                            .withBridge(thingHandler.getThing().getUID())
                            .withLabel(doorName)
                            .withProperty("doorId", doorId)
                            .withProperty("name", doorName)
                            .withRepresentationProperty("doorId")
                            .build();

                    thingDiscovered(result);
                    logger.debug("Discovered door: {} (ID: {})", doorName, doorId);
                }
            }
        } catch (Exception e) {
            logger.error("Error discovering Net2 doors", e);
        }
    }

    @Override
    public void initialize() {
        super.initialize();
    }

    @Override
    public void dispose() {
        super.dispose();
    }
}
