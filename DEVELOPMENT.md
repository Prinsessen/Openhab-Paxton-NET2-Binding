# Net2 Binding - Build & Development Guide

## Prerequisites

- **Java Development Kit (JDK) 21** - [Download](https://adoptium.net/temurin/)
- **Apache Maven 3.6+** - [Download](https://maven.apache.org/download.cgi)
- **Git** - For cloning the OpenHAB repository

### Installation

**Ubuntu/Debian:**
```bash
sudo apt-get install openjdk-21-jdk maven git
```

**macOS (Homebrew):**
```bash
brew install openjdk@21 maven git
```

**Verify installation:**
```bash
java --version
mvn --version
```

## Project Structure

```
net2-binding/
├── pom.xml                          # Maven configuration
├── README.md                        # Binding documentation
├── EXAMPLES.md                      # Usage examples
├── DEVELOPMENT.md                   # This file
├── src/
│   ├── main/
│   │   ├── java/org/openhab/binding/net2/
│   │   │   ├── Net2BindingConstants.java
│   │   │   ├── discovery/
│   │   │   │   └── Net2DoorDiscoveryService.java
│   │   │   ├── handler/
│   │   │   │   ├── Net2HandlerFactory.java
│   │   │   │   ├── Net2ServerHandler.java
│   │   │   │   ├── Net2ServerConfiguration.java
│   │   │   │   ├── Net2DoorHandler.java
│   │   │   │   ├── Net2DoorConfiguration.java
│   │   │   │   ├── Net2ApiClient.java
│   │   │   │   └── Net2SignalRClient.java
│   │   │   └── internal/
│   │   │       └── Net2Utils.java
│   │   └── resources/
│   │       ├── OH-INF/thing/
│   │       │   └── thing-types.xml
│   │       ├── OSGI-INF/
│   │       │   ├── org.openhab.binding.net2.handler.Net2HandlerFactory.xml
│   │       │   └── org.openhab.binding.net2.discovery.Net2DoorDiscoveryService.xml
│   │       └── feature.xml
│   └── test/
│       └── java/org/openhab/binding/net2/
│           └── handler/
│               └── Net2DoorHandlerTest.java
└── target/                          # Build output
    └── org.openhab.binding.net2-5.1.0.jar
```

## Building the Binding

### Full Build

```bash
cd /etc/openhab/net2-binding

# Clean and build
mvn clean install

# Output
# [INFO] BUILD SUCCESS
# [INFO] Total time: XX.XXX s
# [INFO] Finished at: 2026-01-06T...
```

### Build with Tests

```bash
mvn clean install
# Tests run automatically
```

### Skip Tests

```bash
mvn clean install -DskipTests
```

### Build Specific Module

```bash
mvn clean install -pl :org.openhab.binding.net2
```

## Development Workflow

### 1. Set Up IDE

#### Eclipse IDE

```bash
# Generate Eclipse project files
mvn eclipse:eclipse

# In Eclipse: File → Import → Existing Projects into Workspace
# Select net2-binding directory
```

#### VS Code

```bash
# Install extensions:
# - Extension Pack for Java
# - Maven for Java
# - Debugger for Java

# Open folder
code /etc/openhab/net2-binding
```

#### IntelliJ IDEA

```bash
# IntelliJ will auto-detect Maven project
# File → Open → Select net2-binding directory
```

### 2. Code Style & Quality

```bash
# Check code style (SpotBugs)
mvn clean spotbugs:spotbugs

# Format code (Spotless)
mvn spotless:apply

# Full static analysis
mvn clean verify
```

### 3. Running Tests

```bash
# Run all tests
mvn test

# Run specific test
mvn test -Dtest=Net2DoorHandlerTest

# Run with coverage report
mvn clean test jacoco:report
# Report: target/site/jacoco/index.html
```

### 4. Debugging

#### Remote Debug from Eclipse

1. Start Maven with debug flag:
```bash
mvn -Xmx1024m -Xms1024m -agentlib:jdwp=transport=dt_socket,server=y,suspend=y,address=5005 install
```

2. In Eclipse: Debug → Debug Configurations
3. Create "Remote Java Application"
4. Set Host: localhost, Port: 5005

#### Logger Configuration

Add debug logging to `src/main/resources/logback.xml`:
```xml
<logger name="org.openhab.binding.net2" level="DEBUG"/>
```

## Common Development Tasks

### Adding a New Channel

1. Update `thing-types.xml`:
```xml
<channel id="newChannel" typeId="newChannelType"/>
```

2. Define channel type:
```xml
<channel-type id="newChannelType">
    <item-type>String</item-type>
    <label>New Channel</label>
</channel-type>
```

3. Update handler:
```java
case "newChannel":
    // Handle command
    break;
```

### Bridge Channels (User Management)

Implemented bridge-level channels in `thing-types.xml` and `Net2ServerHandler`:

- `createUser` → parses `firstName,lastName,accessLevel,pin`, calls `Net2ApiClient.addUser()` then `assignAccessLevels()`
- `deleteUser` → calls `Net2ApiClient.deleteUser(id)`
- `listAccessLevels` → calls `Net2ApiClient.listAccessLevels()` and logs results

API client helpers:
- `addUser`, `deleteUser`
- `listAccessLevels`, `resolveAccessLevelId`
- `replaceUserDoorPermissionSet`, `assignAccessLevels`

### Adding Configuration Parameter

1. Update `thing-types.xml` config-description
2. Create/update Configuration class
3. Use in handler: `config = getConfigAs(ConfigClass.class)`

### Adding a New Handler

1. Create `MyNewHandler extends BaseThingHandler`
2. Register in `Net2HandlerFactory`
3. Register OSGi service in `OSGI-INF/` XML
4. Add to `pom.xml` if needed

## Testing Best Practices

### Unit Tests

```java
@Test
public void testSomething() {
    // Arrange
    MockitoAnnotations.openMocks(this);
    
    // Act
    handler.someMethod();
    
    // Assert
    verify(callback).somethingHappened();
}
```

### Integration Tests

Test with actual OpenHAB framework (more complex setup):
```java
@RunWith(OSGiRunner.class)
public class Net2IntegrationTest { ... }
```

## Performance Optimization

### API Client Improvements

- Connection pooling for HTTP client
- Request timeout configuration
- Batch API calls where possible

### Handler Optimization

- Cache frequently accessed data
- Use efficient JSON parsing
- Avoid blocking operations in event handlers

## Common Issues

### Build Fails with "Cannot find symbol"

```bash
# Clear Maven cache
rm -rf ~/.m2/repository/org/openhab

# Rebuild with offline check
mvn clean install -U
```

### Tests Timeout

Increase timeout in `pom.xml`:
```xml
<maven.compiler.timeout>300</maven.compiler.timeout>
```

### Bundle Not Loading

Check MANIFEST.MF:
```bash
jar tf target/org.openhab.binding.net2-*.jar | grep MANIFEST
```

Verify imports in OSGi XML are correct.

## Debugging Checklist

- [ ] Check OpenHAB logs: `tail -f /var/log/openhab/openhab.log`
- [ ] Verify thing configuration
- [ ] Check channel bindings
- [ ] Confirm API credentials
- [ ] Verify network connectivity
- [ ] Check Java version (must be 21+)
- [ ] Review handler status updates

## Deployment

### Local Testing

```bash
# Build
mvn clean install

# Copy to OpenHAB
cp target/org.openhab.binding.net2-*.jar ~/openhab-dev/addons/

# Restart
systemctl restart openhab-dev
```

### Production Deployment

```bash
# Build with all checks
mvn clean verify spotbugs:spotbugs

# Copy signed JAR
cp target/org.openhab.binding.net2-*.jar /opt/openhab/addons/

# Backup previous version
cp /opt/openhab/addons/org.openhab.binding.net2-*.jar /backup/

# Restart OpenHAB
systemctl restart openhab

# Verify
systemctl status openhab
tail -f /var/log/openhab/openhab.log | grep net2
```

## Contributing

1. Fork repository
2. Create feature branch: `git checkout -b feature/my-feature`
3. Make changes
4. Run tests: `mvn clean test`
5. Commit with message: `git commit -m "Add feature: ..."`
6. Push: `git push origin feature/my-feature`
7. Create Pull Request

## License

This binding is part of the openHAB project and follows EPL-2.0 license.

## Support & Resources

- **OpenHAB Docs**: https://www.openhab.org/docs/
- **OpenHAB Community**: https://community.openhab.org/
- **Net2 API Docs**: https://prinsessen.agesen.dk:8443/webapihelp/
- **Maven Guide**: https://maven.apache.org/guides/
