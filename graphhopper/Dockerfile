# Optimized Dockerfile for GCP Cloud Run
FROM eclipse-temurin:11-jre

# Set non-interactive frontend for apt
ENV DEBIAN_FRONTEND=noninteractive

# Install dependencies and clean up in one layer to reduce image size
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    unzip \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Set working directory
WORKDIR /app

# Download GraphHopper (use specific version for consistency)
ENV GRAPHHOPPER_VERSION=8.0
RUN wget -q https://github.com/graphhopper/graphhopper/releases/download/${GRAPHHOPPER_VERSION}/graphhopper-web-${GRAPHHOPPER_VERSION}.jar

# Download OSM data for Montana (or your region)
# You can change this to your preferred region
RUN wget -q https://download.geofabrik.de/north-america/us/montana-latest.osm.pbf

# Create necessary directories
RUN mkdir -p /app/config /app/elevation-cache /app/graph-cache

# Copy configuration files
COPY config.gcp.yml /app/config/config.yml
COPY bike.json /app/
COPY gravel.json /app/
COPY mountain.json /app/

# Create a non-root user for security
RUN groupadd -r graphhopper && useradd -r -g graphhopper graphhopper
RUN chown -R graphhopper:graphhopper /app
USER graphhopper

# Expose port (Cloud Run uses PORT environment variable)
EXPOSE 8080

# Health check with Cloud Run compatible endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=180s --retries=3 \
  CMD curl -f http://localhost:8080/info || exit 1

# Use environment variable for port (Cloud Run requirement)
ENV PORT=8080

# Start GraphHopper with optimized JVM settings for Cloud Run
CMD ["sh", "-c", "java -Xmx1536m -XX:+UseG1GC -XX:+UseStringDeduplication -jar graphhopper-web-${GRAPHHOPPER_VERSION}.jar server config/config.yml"]