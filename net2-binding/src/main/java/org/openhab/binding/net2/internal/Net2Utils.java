package org.openhab.binding.net2.internal;

import org.openhab.core.library.types.OnOffType;
import org.openhab.core.library.types.StringType;
import org.openhab.core.thing.ThingStatus;
import org.openhab.core.types.State;
import org.openhab.core.types.UnDefType;

/**
 * Helper class for type conversions and data transformations
 */
public class Net2Utils {

    /**
     * Convert door state string to OpenHAB OnOffType
     */
    public static OnOffType convertDoorState(String state) {
        if (state != null) {
            if ("open".equalsIgnoreCase(state) || "unlocked".equalsIgnoreCase(state)) {
                return OnOffType.ON;
            } else if ("closed".equalsIgnoreCase(state) || "locked".equalsIgnoreCase(state)) {
                return OnOffType.OFF;
            }
        }
        return OnOffType.OFF;
    }

    /**
     * Convert string to State type, handling null/empty values
     */
    public static State toState(String value) {
        if (value == null || value.isEmpty()) {
            return UnDefType.UNDEF;
        }
        return new StringType(value);
    }

    /**
     * Format door control log message
     */
    public static String formatDoorAction(int doorId, String action) {
        return String.format("Door %d action: %s", doorId, action);
    }

    /**
     * Validate door ID
     */
    public static boolean isValidDoorId(int doorId) {
        return doorId > 0;
    }
}
