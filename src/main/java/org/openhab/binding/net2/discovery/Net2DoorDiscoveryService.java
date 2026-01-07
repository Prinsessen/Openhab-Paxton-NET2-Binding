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
package org.openhab.binding.net2.discovery;

import java.util.Set;

import org.eclipse.jdt.annotation.NonNullByDefault;
import org.eclipse.jdt.annotation.Nullable;
import org.openhab.binding.net2.Net2BindingConstants;
import org.openhab.binding.net2.handler.Net2ApiClient;
import org.openhab.binding.net2.handler.Net2ServerHandler;
import org.openhab.core.config.discovery.AbstractDiscoveryService;
import org.openhab.core.config.discovery.DiscoveryResult;
import org.openhab.core.config.discovery.DiscoveryResultBuilder;
import org.openhab.core.thing.ThingTypeUID;
import org.openhab.core.thing.ThingUID;
import org.openhab.core.thing.binding.ThingHandler;
import org.openhab.core.thing.binding.ThingHandlerService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;

/**
 * Discovery service for Net2 doors
 *
 * @author openHAB Community - Initial contribution
 */
@NonNullByDefault
public class Net2DoorDiscoveryService extends AbstractDiscoveryService implements ThingHandlerService {

    private final Logger logger = LoggerFactory.getLogger(Net2DoorDiscoveryService.class);
    private static final int SEARCH_TIME = 30;

    private @Nullable Net2ServerHandler bridgeHandler;

    public Net2DoorDiscoveryService() {
        super(Set.of(new ThingTypeUID(Net2BindingConstants.BINDING_ID, Net2BindingConstants.THING_TYPE_DOOR)),
                SEARCH_TIME);
    }

    @Override
    protected void startScan() {
        logger.debug("Starting Net2 door discovery");

        Net2ServerHandler handler = bridgeHandler;
        if (handler == null) {
            logger.warn("No bridge handler set; cannot perform discovery");
            return;
        }

        try {
            Net2ApiClient apiClient = handler.getApiClient();
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
                            new ThingTypeUID(Net2BindingConstants.BINDING_ID, Net2BindingConstants.THING_TYPE_DOOR),
                            handler.getThing().getUID(), String.valueOf(doorId));

                    DiscoveryResult result = DiscoveryResultBuilder.create(thingUID)
                            .withBridge(handler.getThing().getUID()).withLabel(doorName).withProperty("doorId", doorId)
                            .withProperty("name", doorName).withRepresentationProperty("doorId").build();

                    thingDiscovered(result);
                    logger.info("Discovered door: {} (ID: {})", doorName, doorId);
                }
            }
            logger.debug("Discovery scan completed");
        } catch (Exception e) {
            logger.error("Error discovering Net2 doors", e);
        }
    }

    @Override
    public void setThingHandler(ThingHandler thingHandler) {
        if (thingHandler instanceof Net2ServerHandler handler) {
            this.bridgeHandler = handler;
        }
    }

    public void unsetThingHandler(ThingHandler thingHandler) {
        if (thingHandler instanceof Net2ServerHandler) {
            this.bridgeHandler = null;
        }
    }

    @Override
    public @Nullable ThingHandler getThingHandler() {
        return bridgeHandler;
    }

    @Override
    public void deactivate() {
        bridgeHandler = null;
        super.deactivate();
    }
}
