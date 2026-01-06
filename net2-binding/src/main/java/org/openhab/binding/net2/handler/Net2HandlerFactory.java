package org.openhab.binding.net2.handler;

import org.openhab.binding.net2.Net2BindingConstants;
import org.openhab.core.thing.Bridge;
import org.openhab.core.thing.Thing;
import org.openhab.core.thing.ThingTypeUID;
import org.openhab.core.thing.binding.BaseThingHandlerFactory;
import org.openhab.core.thing.binding.ThingHandler;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.Set;

/**
 * The {@link Net2HandlerFactory} is responsible for creating things and thing
 * handlers.
 */
public class Net2HandlerFactory extends BaseThingHandlerFactory {

    private final Logger logger = LoggerFactory.getLogger(Net2HandlerFactory.class);

    private static final Set<ThingTypeUID> SUPPORTED_THING_TYPES = Set.of(
            new ThingTypeUID(Net2BindingConstants.BINDING_ID, Net2BindingConstants.THING_TYPE_NET2SERVER),
            new ThingTypeUID(Net2BindingConstants.BINDING_ID, Net2BindingConstants.THING_TYPE_DOOR));

    @Override
    public boolean supportsThingType(ThingTypeUID thingTypeUID) {
        return SUPPORTED_THING_TYPES.contains(thingTypeUID);
    }

    @Override
    protected ThingHandler createHandler(Thing thing) {
        ThingTypeUID thingTypeUID = thing.getThingTypeUID();

        if (new ThingTypeUID(Net2BindingConstants.BINDING_ID, Net2BindingConstants.THING_TYPE_NET2SERVER)
                .equals(thingTypeUID)) {
            return new Net2ServerHandler((Bridge) thing);
        } else if (new ThingTypeUID(Net2BindingConstants.BINDING_ID, Net2BindingConstants.THING_TYPE_DOOR)
                .equals(thingTypeUID)) {
            return new Net2DoorHandler(thing);
        }

        return null;
    }
}
