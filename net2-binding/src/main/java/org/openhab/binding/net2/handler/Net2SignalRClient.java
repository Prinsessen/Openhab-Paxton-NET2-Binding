package org.openhab.binding.net2.handler;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.google.gson.JsonObject;
import com.google.gson.JsonParser;

import java.io.IOException;
import java.net.URI;
import java.net.URISyntaxException;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.net.http.WebSocket;
import java.net.http.WebSocket.Listener;
import java.nio.ByteBuffer;
import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.util.Base64;
import java.util.HashMap;
import java.util.Map;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.function.Consumer;

/**
 * WebSocket client for Net2 SignalR real-time events
 * Enables live door open/close status updates without polling
 */
public class Net2SignalRClient implements Listener {

    private final Logger logger = LoggerFactory.getLogger(Net2SignalRClient.class);

    private final String host;
    private final int port;
    private final String accessToken;
    private final boolean tlsVerification;
    private final HttpClient httpClient;
    private final Map<String, Consumer<String>> eventHandlers = new HashMap<>();
    
    private WebSocket webSocket;
    private volatile boolean connected = false;
    private String connectionToken;
    private String connectionId;
    private final AtomicInteger invokeId = new AtomicInteger(1);

    public Net2SignalRClient(String hostname, int port, String accessToken, boolean tlsVerification) {
        this.host = hostname;
        this.port = port;
        this.accessToken = accessToken;
        this.tlsVerification = tlsVerification;
        HttpClient.Builder b = HttpClient.newBuilder().connectTimeout(Duration.ofSeconds(10));
        if (!tlsVerification) {
            try {
                javax.net.ssl.SSLContext sslContext = javax.net.ssl.SSLContext.getInstance("TLS");
                sslContext.init(null, new javax.net.ssl.TrustManager[]{new NoopTrustManager()}, new java.security.SecureRandom());
                b.sslContext(sslContext);
            } catch (Exception e) {
                logger.warn("Failed to configure permissive SSL context", e);
            }
        }
        this.httpClient = b.build();
    }

    /**
     * Connect to SignalR hub
     */
    public void connect() throws URISyntaxException, IOException, InterruptedException {
        // Classic SignalR 2 flow under /webapi/signalr
        String negotiateUrl = String.format("https://%s:%d/webapi/signalr/negotiate?clientProtocol=1.5&connectionData=%s&_=%d",
                host, port, urlEncode("[{\"name\":\"eventHubLocal\"}]"), System.currentTimeMillis());
        logger.debug("Classic negotiate URI: {}", negotiateUrl);

        HttpRequest negotiate = HttpRequest.newBuilder()
                .uri(URI.create(negotiateUrl))
                .header("Authorization", "Bearer " + accessToken)
                .GET()
                .build();

        HttpResponse<String> negResp = httpClient.send(negotiate, HttpResponse.BodyHandlers.ofString());
        if (negResp.statusCode() != 200) {
            logger.warn("SignalR negotiate failed: status {}", negResp.statusCode());
            connected = false;
            return;
        }

        JsonObject negJson = JsonParser.parseString(negResp.body()).getAsJsonObject();
        this.connectionToken = negJson.has("ConnectionToken") ? negJson.get("ConnectionToken").getAsString() : null;
        this.connectionId = negJson.has("ConnectionId") ? negJson.get("ConnectionId").getAsString() : null;

        if (connectionToken == null) {
            logger.warn("SignalR negotiate missing ConnectionToken");
            connected = false;
            return;
        }

        String wsUrl = String.format(
                "wss://%s:%d/webapi/signalr/connect?transport=webSockets&clientProtocol=1.5&connectionToken=%s&connectionData=%s",
                host, port, urlEncode(connectionToken), urlEncode("[{\"name\":\"eventHubLocal\"}]"));

        java.net.http.WebSocket.Builder builder = httpClient.newWebSocketBuilder()
                .header("Authorization", "Bearer " + accessToken)
                .connectTimeout(Duration.ofSeconds(10));

        try {
            this.webSocket = builder.buildAsync(URI.create(wsUrl), this).join();
        } catch (Exception e) {
            logger.error("Failed to open SignalR WebSocket", e);
            connected = false;
            return;
        }

        // Start step
        String startUrl = String.format(
                "https://%s:%d/webapi/signalr/start?transport=webSockets&clientProtocol=1.5&connectionToken=%s&connectionData=%s",
                host, port, urlEncode(connectionToken), urlEncode("[{\"name\":\"eventHubLocal\"}]"));
        HttpRequest startReq = HttpRequest.newBuilder()
                .uri(URI.create(startUrl))
                .header("Authorization", "Bearer " + accessToken)
                .GET()
                .build();
        HttpResponse<String> startResp = httpClient.send(startReq, HttpResponse.BodyHandlers.ofString());
        if (startResp.statusCode() != 200) {
            logger.warn("SignalR start failed: status {}", startResp.statusCode());
            connected = false;
            return;
        }

        connected = true;
        logger.info("Connected to Net2 SignalR server (classic)");

        // Initial subscription to live events
        subscribeToLiveEvents();
    }

    /**
     * Subscribe to door events
     */
    public void subscribeToDoorEvents(int doorId) {
        if (!connected || webSocket == null) {
            logger.warn("Not connected to SignalR, cannot subscribe to events");
            return;
        }
        JsonObject invoke = new JsonObject();
        invoke.addProperty("H", "eventHubLocal");
        invoke.addProperty("M", "subscribeToDoorEvents");
        com.google.gson.JsonArray args = new com.google.gson.JsonArray();
        args.add(doorId);
        invoke.add("A", args);
        invoke.addProperty("I", invokeId.getAndIncrement());
        String payload = invoke.toString();
        webSocket.sendText(payload, true);
        logger.debug("Sent subscribeToDoorEvents({})", doorId);
    }

    public void subscribeToLiveEvents() {
        if (!connected || webSocket == null) {
            return;
        }
        JsonObject invoke = new JsonObject();
        invoke.addProperty("H", "eventHubLocal");
        invoke.addProperty("M", "subscribeToLiveEvents");
        invoke.add("A", new com.google.gson.JsonArray());
        invoke.addProperty("I", invokeId.getAndIncrement());
        webSocket.sendText(invoke.toString(), true);
        logger.debug("Sent subscribeToLiveEvents()");
    }

    /**
     * Register event handler callback
     */
    public void onDoorStatusChanged(Consumer<String> handler) {
        eventHandlers.put("doorStatusChanged", handler);
    }

    /**
     * Handle incoming messages
     */
    @Override
    public void onText(WebSocket webSocket, CharSequence data, boolean last) {
        try {
            String message = data.toString();
            logger.debug("Received SignalR message: {}", message);
            
            // Parse and dispatch events
            JsonObject json = JsonParser.parseString(message).getAsJsonObject();
            
            // Classic SignalR server-to-client invocation uses 'M' (method) and 'A' (args)
            if (json.has("M")) {
                String method = json.get("M").getAsString();
                Consumer<String> handler = eventHandlers.get(method);
                if (handler != null) {
                    handler.accept(message);
                }
            } else if (json.has("C")) {
                // Keep-alive/batch marker - ignore
            } else {
                logger.debug("Unhandled SignalR message: {}", message);
            }
        } catch (Exception e) {
            logger.debug("Error processing SignalR message", e);
        }
        Listener.super.onText(webSocket, data, last);
    }

    @Override
    public void onClose(WebSocket webSocket, int statusCode, String reason) {
        connected = false;
        logger.info("SignalR connection closed: {} - {}", statusCode, reason);
        Listener.super.onClose(webSocket, statusCode, reason);
    }

    @Override
    public void onError(WebSocket webSocket, Throwable error) {
        logger.error("SignalR connection error", error);
        connected = false;
        Listener.super.onError(webSocket, error);
    }

    public void disconnect() {
        if (webSocket != null) {
            webSocket.sendClose(1000, "Normal close");
            connected = false;
        }
    }

    public boolean isConnected() {
        return connected;
    }

    private static String urlEncode(String s) {
        return java.net.URLEncoder.encode(s, java.nio.charset.StandardCharsets.UTF_8);
    }

    private static class NoopTrustManager implements javax.net.ssl.X509TrustManager {
        @Override public void checkClientTrusted(java.security.cert.X509Certificate[] xcs, String s) {}
        @Override public void checkServerTrusted(java.security.cert.X509Certificate[] xcs, String s) {}
        @Override public java.security.cert.X509Certificate[] getAcceptedIssuers() { return new java.security.cert.X509Certificate[0]; }
    }
}
