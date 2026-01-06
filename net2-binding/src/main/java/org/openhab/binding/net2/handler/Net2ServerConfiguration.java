package org.openhab.binding.net2.handler;

/**
 * Configuration class for Net2 Server bridge
 */
public class Net2ServerConfiguration {
    public String hostname;
    public Integer port = 8443;
    public String username;
    public String password;
    public String clientId;
    public Boolean tlsVerification = true;
    public Integer refreshInterval = 30;
}
