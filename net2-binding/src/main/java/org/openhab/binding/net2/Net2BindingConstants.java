package org.openhab.binding.net2;

/**
 * The {@link Net2BindingConstants} class defines common constants, which are
 * used across the whole binding.
 */
public class Net2BindingConstants {

    public static final String BINDING_ID = "net2";

    // List of all Bridge Thing Type UIDs
    public static final String THING_TYPE_NET2SERVER = "net2server";

    // List of all Thing Type UIDs
    public static final String THING_TYPE_DOOR = "door";

    // List of all Channel ids
    public static final String CHANNEL_DOOR_STATUS = "status";
    public static final String CHANNEL_DOOR_ACTION = "action";
    public static final String CHANNEL_LAST_ACCESS_USER = "lastAccessUser";
    public static final String CHANNEL_LAST_ACCESS_TIME = "lastAccessTime";

    // API Configuration
    public static final String API_VERSION = "v1";
    public static final int DEFAULT_PORT = 8443;
    public static final int DEFAULT_REFRESH_INTERVAL = 30;
    public static final int TOKEN_EXPIRY_BUFFER_SECONDS = 300; // Refresh token 5 mins before expiry
}
