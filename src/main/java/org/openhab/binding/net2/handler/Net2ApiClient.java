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
package org.openhab.binding.net2.handler;

import java.io.IOException;
import java.net.URI;
import java.net.URISyntaxException;
import java.net.URLEncoder;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.ZoneOffset;
import java.time.ZonedDateTime;
import java.util.HashMap;
import java.util.Map;
import java.util.concurrent.locks.ReentrantLock;

import org.eclipse.jdt.annotation.NonNullByDefault;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.google.gson.JsonObject;
import com.google.gson.JsonParser;

/**
 * The {@link Net2ApiClient} handles all HTTP communication with the Paxton Net2 API.
 *
 * @author OpenHAB Community - Initial contribution
 */
@NonNullByDefault
public class Net2ApiClient {

    private final Logger logger = LoggerFactory.getLogger(Net2ApiClient.class);

    private final String baseUrl;
    private final String username;
    private final String password;
    private final String clientId;
    private final boolean tlsVerification;
    private final HttpClient httpClient;
    private final URI serverRootUri;

    private String accessToken = "";
    private String refreshToken = "";
    private ZonedDateTime tokenExpiry = ZonedDateTime.now(ZoneOffset.UTC);
    private final ReentrantLock tokenLock = new ReentrantLock();

    public Net2ApiClient(Net2ServerConfiguration config) {
        String host = config.hostname;
        if (host.startsWith("http://") || host.startsWith("https://")) {
            // Allow full base URL in hostname param (compat with external config)
            this.baseUrl = host.replaceAll("/+$", "");
        } else {
            this.baseUrl = String.format("https://%s:%d/api/%s", host, config.port != null ? config.port : 8443, "v1");
        }
        this.username = config.username;
        this.password = config.password;
        this.clientId = config.clientId;
        this.tlsVerification = config.tlsVerification != null ? config.tlsVerification : true;

        // Create HTTP client
        HttpClient.Builder builder = HttpClient.newBuilder();
        this.httpClient = builder.build();

        try {
            URI apiUri = URI.create(this.baseUrl);
            this.serverRootUri = new URI(apiUri.getScheme(), null, apiUri.getHost(), apiUri.getPort(), null, null, null);
        } catch (URISyntaxException e) {
            throw new IllegalArgumentException("Invalid base URL for Net2 API", e);
        }
    }

    /**
     * Authenticate with Net2 API
     */
    public boolean authenticate() throws IOException, InterruptedException {
        tokenLock.lock();
        try {
            Map<String, String> formData = new HashMap<>();
            formData.put("username", username);
            formData.put("password", password);
            formData.put("grant_type", "password");
            formData.put("client_id", clientId);
            formData.put("scope", "offline_access");

            String body = encodeFormData(formData);

            HttpRequest request = HttpRequest.newBuilder().uri(URI.create(baseUrl + "/authorization/tokens"))
                    .POST(HttpRequest.BodyPublishers.ofString(body))
                    .header("Content-Type", "application/x-www-form-urlencoded; charset=UTF-8").build();

            HttpResponse<String> response = httpClient.send(request, HttpResponse.BodyHandlers.ofString());

            if (response.statusCode() == 200) {
                JsonObject jsonResponse = JsonParser.parseString(response.body()).getAsJsonObject();
                accessToken = jsonResponse.get("access_token").getAsString();
                refreshToken = jsonResponse.get("refresh_token").getAsString();
                int expiresIn = jsonResponse.get("expires_in").getAsInt();
                tokenExpiry = ZonedDateTime.now(ZoneOffset.UTC).plusSeconds(expiresIn);

                logger.debug("Successfully authenticated with Net2 API. Token expires in {} seconds", expiresIn);
                return true;
            } else {
                logger.error("Authentication failed. Status: {}, Response: {}", response.statusCode(), response.body());
                return false;
            }
        } finally {
            tokenLock.unlock();
        }
    }

    /**
     * Refresh access token using refresh token
     */
    private boolean refreshAccessToken() throws IOException, InterruptedException {
        tokenLock.lock();
        try {
            if (refreshToken == null) {
                return authenticate();
            }

            Map<String, String> formData = new HashMap<>();
            formData.put("refresh_token", refreshToken);
            formData.put("grant_type", "refresh_token");
            formData.put("client_id", clientId);
            formData.put("scope", "offline_access");

            String body = encodeFormData(formData);

            HttpRequest request = HttpRequest.newBuilder().uri(URI.create(baseUrl + "/authorization/tokens"))
                    .POST(HttpRequest.BodyPublishers.ofString(body))
                    .header("Content-Type", "application/x-www-form-urlencoded; charset=UTF-8").build();

            HttpResponse<String> response = httpClient.send(request, HttpResponse.BodyHandlers.ofString());

            if (response.statusCode() == 200) {
                JsonObject jsonResponse = JsonParser.parseString(response.body()).getAsJsonObject();
                accessToken = jsonResponse.get("access_token").getAsString();
                if (jsonResponse.has("refresh_token")) {
                    refreshToken = jsonResponse.get("refresh_token").getAsString();
                }
                int expiresIn = jsonResponse.get("expires_in").getAsInt();
                tokenExpiry = ZonedDateTime.now(ZoneOffset.UTC).plusSeconds(expiresIn);

                logger.debug("Token refreshed successfully");
                return true;
            } else {
                logger.error("Token refresh failed. Status: {}", response.statusCode());
                return false;
            }
        } finally {
            tokenLock.unlock();
        }
    }

    /**
     * Check and refresh token if needed
     */
    private void ensureTokenValid() throws IOException, InterruptedException {
        tokenLock.lock();
        try {
            if (accessToken == null) {
                throw new IllegalStateException("Not authenticated");
            }

            if (tokenExpiry != null && ZonedDateTime.now(ZoneOffset.UTC).plusSeconds(300).isAfter(tokenExpiry)) {
                logger.debug("Token expiring soon, refreshing...");
                refreshAccessToken();
            }
        } finally {
            tokenLock.unlock();
        }
    }

    /**
     * Get door status
     */
    public String getDoorStatus() throws IOException, InterruptedException {
        ensureTokenValid();

        HttpRequest request = HttpRequest.newBuilder().uri(URI.create(baseUrl + "/doors/status")).GET()
                .header("Authorization", "Bearer " + accessToken).build();

        HttpResponse<String> response = httpClient.send(request, HttpResponse.BodyHandlers.ofString());

        if (response.statusCode() == 200) {
            return response.body();
        } else {
            throw new IOException("Failed to get door status. Status: " + response.statusCode());
        }
    }

    /**
     * Get list of all doors
     */
    public String listDoors() throws IOException, InterruptedException {
        ensureTokenValid();

        HttpRequest request = HttpRequest.newBuilder().uri(URI.create(baseUrl + "/doors")).GET()
                .header("Authorization", "Bearer " + accessToken).build();

        HttpResponse<String> response = httpClient.send(request, HttpResponse.BodyHandlers.ofString());

        if (response.statusCode() == 200) {
            return response.body();
        } else {
            throw new IOException("Failed to list doors. Status: " + response.statusCode());
        }
    }

    /**
     * Hold door open
     */
    public boolean holdDoorOpen(int doorId) throws IOException, InterruptedException {
        ensureTokenValid();

        JsonObject body = new JsonObject();
        body.addProperty("DoorId", doorId);

        HttpRequest request = HttpRequest.newBuilder().uri(URI.create(baseUrl + "/commands/door/holdopen"))
                .POST(HttpRequest.BodyPublishers.ofString(body.toString()))
                .header("Authorization", "Bearer " + accessToken).header("Content-Type", "application/json").build();

        HttpResponse<String> response = httpClient.send(request, HttpResponse.BodyHandlers.ofString());
        return response.statusCode() == 200;
    }

    /**
     * Close door
     */
    public boolean closeDoor(int doorId) throws IOException, InterruptedException {
        ensureTokenValid();

        JsonObject body = new JsonObject();
        body.addProperty("DoorId", doorId);

        HttpRequest request = HttpRequest.newBuilder().uri(URI.create(baseUrl + "/commands/door/close"))
                .POST(HttpRequest.BodyPublishers.ofString(body.toString()))
                .header("Authorization", "Bearer " + accessToken).header("Content-Type", "application/json").build();

        HttpResponse<String> response = httpClient.send(request, HttpResponse.BodyHandlers.ofString());
        return response.statusCode() == 200;
    }

    /**
     * Check if authenticated and token is valid
     */
    public boolean isAuthenticated() {
        tokenLock.lock();
        try {
            return accessToken != null
                    && (tokenExpiry == null || ZonedDateTime.now(ZoneOffset.UTC).isBefore(tokenExpiry));
        } finally {
            tokenLock.unlock();
        }
    }

    /**
     * Returns a valid access token, refreshing if needed.
     */
    public String getValidAccessToken() throws IOException, InterruptedException {
        ensureTokenValid();
        return accessToken;
    }

    /**
     * Returns the root URI (scheme/host/port) for the server, without the API path.
     */
    public URI getServerRootUri() {
        return serverRootUri;
    }

    /**
     * Indicates whether TLS verification is enabled in the configuration.
     */
    public boolean isTlsVerificationEnabled() {
        return tlsVerification;
    }

    /**
     * Close the HTTP client
     */
    public void close() {
        // HTTP client is managed by the JVM, no explicit close needed
    }

    /**
     * Encode form data for URL-encoded POST
     */
    private String encodeFormData(Map<String, String> data) {
        StringBuilder sb = new StringBuilder();
        for (Map.Entry<String, String> entry : data.entrySet()) {
            if (sb.length() > 0) {
                sb.append("&");
            }
            sb.append(URLEncoder.encode(entry.getKey(), java.nio.charset.StandardCharsets.UTF_8)).append("=")
                    .append(URLEncoder.encode(entry.getValue(), java.nio.charset.StandardCharsets.UTF_8));
        }
        return sb.toString();
    }
}
