FROM eclipse-temurin:11-jre

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    curl \
    wget \
    unzip \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

WORKDIR /app

ENV GRAPHHOPPER_VERSION=8.0
RUN wget -q https://github.com/graphhopper/graphhopper/releases/download/${GRAPHHOPPER_VERSION}/graphhopper-web-${GRAPHHOPPER_VERSION}.jar

RUN wget -q https://download.geofabrik.de/north-america/us/montana-latest.osm.pbf

RUN mkdir -p /app/config /app/elevation-cache /app/graph-cache

# COPY paths are relative to repo root (build context)
COPY graphhopper/config.gcp.yml /app/config/config.yml
COPY graphhopper/bike.json /app/
COPY graphhopper/gravel.json /app/
COPY graphhopper/mountain.json /app/

RUN groupadd -r graphhopper && useradd -r -g graphhopper graphhopper
RUN chown -R graphhopper:graphhopper /app
USER graphhopper

EXPOSE 8080
ENV PORT=8080

HEALTHCHECK --interval=30s --timeout=10s --start-period=180s --retries=3 \
  CMD curl -f http://localhost:8080/info || exit 1

CMD ["sh", "-c", "java -Xmx1536m -XX:+UseG1GC -XX:+UseStringDeduplication -jar graphhopper-web-${GRAPHHOPPER_VERSION}.jar server config/config.yml"]
