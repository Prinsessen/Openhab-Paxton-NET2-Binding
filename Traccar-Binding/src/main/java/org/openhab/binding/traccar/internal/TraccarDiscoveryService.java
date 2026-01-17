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

import static org.openhab.binding.traccar.internal.TraccarBindingConstants.*;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

import org.eclipse.jdt.annotation.NonNullByDefault;
import org.openhab.core.config.discovery.AbstractThingHandlerDiscoveryService;
import org.openhab.core.config.discovery.DiscoveryResultBuilder;
import org.openhab.core.thing.ThingUID;
import org.osgi.service.component.annotations.Component;
import org.osgi.service.component.annotations.ServiceScope;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * The {@link TraccarDiscoveryService} discovers Traccar devices.
 *
 * @author Nanna Agesen - Initial contribution
 */
@Component(scope = ServiceScope.PROTOTYPE, service = TraccarDiscoveryService.class)
@NonNullByDefault
public class TraccarDiscoveryService extends AbstractThingHandlerDiscoveryService<TraccarServerHandler> {

    private final Logger logger = LoggerFactory.getLogger(TraccarDiscoveryService.class);

    private static final int DISCOVER_TIMEOUT_SECONDS = 10;

    public TraccarDiscoveryService() {
        super(TraccarServerHandler.class, SUPPORTED_THING_TYPES_UIDS, DISCOVER_TIMEOUT_SECONDS);
    }

    @Override
    protected void startScan() {
        logger.debug("Starting Traccar device discovery");

        TraccarServerHandler handler = thingHandler;
        if (handler == null) {
            logger.warn("Cannot discover devices: handler is null");
            return;
        }

        TraccarApiClient apiClient = handler.getApiClient();
        if (apiClient == null) {
            logger.warn("Cannot discover devices: API client is null");
            return;
        }

        List<Map<String, Object>> devices = apiClient.getDevices();
        if (devices == null) {
            logger.warn("Failed to retrieve devices from Traccar server");
            return;
        }

        ThingUID bridgeUID = handler.getThing().getUID();

        for (Map<String, Object> device : devices) {
            discoverDevice(bridgeUID, device);
        }

        logger.info("Discovered {} Traccar device(s)", devices.size());
    }

    private void discoverDevice(ThingUID bridgeUID, Map<String, Object> device) {
        Object deviceIdObj = device.get("id");
        if (deviceIdObj == null) {
            return;
        }

        int deviceId = ((Number) deviceIdObj).intValue();
        Object nameObj = device.get("name");
        String name = nameObj instanceof String ? (String) nameObj : "Device " + deviceId;
        Object uniqueIdObj = device.get("uniqueId");
        String uniqueId = uniqueIdObj instanceof String ? (String) uniqueIdObj : String.valueOf(deviceId);

        ThingUID thingUID = new ThingUID(THING_TYPE_DEVICE, bridgeUID, uniqueId);

        Map<String, Object> properties = new HashMap<>();
        properties.put("deviceId", Integer.valueOf(deviceId));
        properties.put("uniqueId", uniqueId);
        Object modelObj = device.get("model");
        if (modelObj != null) {
            properties.put("model", modelObj);
        }
        Object contactObj = device.get("contact");
        if (contactObj != null) {
            properties.put("contact", contactObj);
        }

        thingDiscovered(DiscoveryResultBuilder.create(thingUID).withThingType(THING_TYPE_DEVICE).withBridge(bridgeUID)
                .withLabel(name).withProperties(properties).withRepresentationProperty("uniqueId").build());

        logger.debug("Discovered device: {} (ID: {})", name, deviceId);
    }
}
