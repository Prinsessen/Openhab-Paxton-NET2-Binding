# Contributing to Traccar Binding

Thank you for your interest in contributing to the Traccar binding for openHAB!

## Author & Maintainer

**Nanna Agesen**  
- Email: Nanna@agesen.dk  
- GitHub: [@Prinsessen](https://github.com/Prinsessen)

## How to Contribute

### Reporting Issues

If you encounter bugs or have feature requests:

1. Check existing issues to avoid duplicates
2. Provide detailed information:
   - openHAB version
   - Traccar version
   - Device/tracker model
   - Binding version
   - Relevant log output
   - Steps to reproduce

### Submitting Changes

1. **Fork the repository** (if contributing to openHAB add-ons repo)

2. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make your changes**
   - Follow openHAB coding guidelines
   - Add/update tests if applicable
   - Update documentation (README.md, CHANGELOG.md)

4. **Test thoroughly**
   - Build the binding: `mvn clean package`
   - Test with real Traccar server
   - Verify all channels work correctly
   - Check webhook functionality

5. **Format code**
   ```bash
   mvn spotless:apply
   ```

6. **Commit with clear messages**
   ```bash
   git commit -m "Add feature: description of change"
   ```

7. **Submit pull request**
   - Describe what changes were made
   - Reference any related issues
   - Include testing details

## Development Setup

### Prerequisites
- Java 21 or later
- Maven 3.x
- openHAB development environment
- Access to Traccar server (demo.traccar.org for testing)

### Building the Binding

```bash
cd bundles/org.openhab.binding.traccar
mvn clean package -DskipTests
```

The compiled JAR will be in `target/org.openhab.binding.traccar-5.2.0-SNAPSHOT.jar`

### Installing for Testing

```bash
cp target/org.openhab.binding.traccar-*.jar /usr/share/openhab/addons/
```

### Code Style

- Follow openHAB Java coding conventions
- Use meaningful variable names
- Add JavaDoc comments for public methods/classes
- Keep methods focused and concise
- Run `mvn spotless:apply` before committing

### Testing Checklist

- [ ] Bridge connects successfully to Traccar server
- [ ] Devices auto-discover correctly
- [ ] Position updates via polling
- [ ] Webhooks receive geofence events
- [ ] All channels update with correct values
- [ ] Speed unit conversion works (km/h, mph, knots)
- [ ] Battery level displays correctly
- [ ] Odometer accumulates distance
- [ ] NULL/UNDEF states handled gracefully
- [ ] No errors in openhab.log
- [ ] Documentation updated

## Project Structure

```
org.openhab.binding.traccar/
├── src/main/java/org/openhab/binding/traccar/internal/
│   ├── TraccarBindingConstants.java      # Channel and thing type constants
│   ├── TraccarHandlerFactory.java        # Thing handler factory
│   ├── TraccarServerHandler.java         # Bridge handler (API client, polling)
│   ├── TraccarDeviceHandler.java         # Device handler (channels, updates)
│   ├── TraccarDiscoveryService.java      # Auto-discovery service
│   ├── TraccarApiClient.java             # Traccar REST API wrapper
│   ├── TraccarWebhookServer.java         # Jetty webhook server
│   ├── TraccarServerConfiguration.java   # Bridge configuration
│   └── TraccarDeviceConfiguration.java   # Device configuration
├── src/main/resources/OH-INF/
│   ├── thing/thing-types.xml             # Thing and channel definitions
│   └── i18n/                             # Internationalization
├── pom.xml                               # Maven build configuration
└── README.md                             # User documentation
```

## Architecture Notes

### Update Mechanisms

**Polling (TraccarServerHandler)**
- Scheduled job runs every `refreshInterval` seconds
- Fetches positions for all devices via `/api/positions` endpoint
- Updates device handlers with new position data
- Minimum interval: 10 seconds (API rate limiting)

**Webhooks (TraccarWebhookServer)**
- Jetty server listens on configured `webhookPort`
- Accepts POST requests from Traccar notifications
- Parses JSON event data
- Routes to appropriate device handler
- Provides instant updates for geofence events

### Channel Updates

Position channels are updated in `TraccarDeviceHandler.updatePositionChannels()`:
- Extracts data from Traccar position JSON
- Converts units (speed from knots, etc.)
- Updates channel states via `updateState()`
- Handles NULL/missing attributes gracefully

### Speed Conversion Logic

Traccar reports speed in **knots** (nautical miles per hour):
- `kmh`: speed_knots × 1.852
- `mph`: speed_knots × 1.15078
- `knots`: no conversion (raw value)

Conversion factor selected based on `speedUnit` bridge parameter.

## Adding New Features

### Adding a New Channel

1. **Define constant** in `TraccarBindingConstants.java`:
   ```java
   public static final String CHANNEL_NEW_FEATURE = "newFeature";
   ```

2. **Add channel type** in `thing-types.xml`:
   ```xml
   <channel-type id="new-feature">
       <item-type>String</item-type>
       <label>New Feature</label>
       <description>Description of new feature</description>
       <state readOnly="true"/>
   </channel-type>
   ```

3. **Add to device channels** in `thing-types.xml`:
   ```xml
   <channel id="newFeature" typeId="new-feature"/>
   ```

4. **Extract and update** in `TraccarDeviceHandler.java`:
   ```java
   Object newFeatureObj = position.get("newFeature");
   if (newFeatureObj instanceof String newFeature) {
       updateState(CHANNEL_NEW_FEATURE, new StringType(newFeature));
   }
   ```

5. **Document** in README.md and update CHANGELOG.md

### Adding Configuration Parameters

1. Add field to `TraccarServerConfiguration.java`
2. Add parameter definition in `thing-types.xml`
3. Use parameter in handler logic
4. Document in README.md

## Contact

For questions or discussions:
- **Email**: Nanna@agesen.dk
- **GitHub**: [@Prinsessen](https://github.com/Prinsessen)

## License

By contributing, you agree that your contributions will be licensed under the Eclipse Public License 2.0 (EPL-2.0).
