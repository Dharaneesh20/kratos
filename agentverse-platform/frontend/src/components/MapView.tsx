import React, { useEffect, useRef } from 'react';
import L from 'leaflet';
import { CriticalNode, EvacuationRoute } from '../types';

interface MapViewProps {
  roadsGeoJSON?: any;
  roadMaskBase64?: string;
  criticalNodes?: CriticalNode[];
  evacuationRoutes?: EvacuationRoute[];
}

export const MapView: React.FC<MapViewProps> = ({
  roadsGeoJSON,
  roadMaskBase64,
  criticalNodes,
  evacuationRoutes,
}) => {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<L.Map | null>(null);
  const geojsonLayerRef = useRef<L.GeoJSON | null>(null);
  const nodeMarkersRef = useRef<L.LayerGroup | null>(null);
  const routePolylinesRef = useRef<L.LayerGroup | null>(null);

  useEffect(() => {
    if (!mapContainerRef.current) return;

    if (!mapRef.current) {
      // Default initial center (e.g. San Francisco or generic coordinates)
      const map = L.map(mapContainerRef.current, {
        center: [37.7749, -122.4194],
        zoom: 13,
      });

      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; OpenStreetMap contributors',
        maxZoom: 19,
      }).addTo(map);

      mapRef.current = map;
      nodeMarkersRef.current = L.layerGroup().addTo(map);
      routePolylinesRef.current = L.layerGroup().addTo(map);
    }

    return () => {
      // Keep map instance across renders
    };
  }, []);

  // Update GeoJSON Road Layer
  useEffect(() => {
    if (!mapRef.current) return;

    if (geojsonLayerRef.current) {
      mapRef.current.removeLayer(geojsonLayerRef.current);
      geojsonLayerRef.current = null;
    }

    if (roadsGeoJSON && roadsGeoJSON.features && roadsGeoJSON.features.length > 0) {
      const geoLayer = L.geoJSON(roadsGeoJSON, {
        style: () => ({
          color: '#9333ea',
          weight: 3,
          opacity: 0.8,
        }),
      }).addTo(mapRef.current);

      geojsonLayerRef.current = geoLayer;

      try {
        const bounds = geoLayer.getBounds();
        if (bounds.isValid()) {
          mapRef.current.fitBounds(bounds, { padding: [30, 30] });
        }
      } catch (e) {
        console.warn("Invalid bounds for GeoJSON", e);
      }
    }
  }, [roadsGeoJSON]);

  // Update Critical Node Markers
  useEffect(() => {
    if (!mapRef.current || !nodeMarkersRef.current) return;

    nodeMarkersRef.current.clearLayers();

    if (criticalNodes && criticalNodes.length > 0) {
      criticalNodes.forEach((node) => {
        const isBridge = node.is_bridge_adjacent;
        const color = isBridge ? '#ef4444' : '#eab308';
        const radius = Math.max(5, Math.min(12, node.criticality_score * 15));

        const circle = L.circleMarker([node.lat, node.lon], {
          radius: radius,
          fillColor: color,
          color: '#000000',
          weight: 1.5,
          opacity: 1,
          fillOpacity: 0.85,
        });

        circle.bindPopup(`
          <div style="font-family: sans-serif; font-size: 12px; padding: 2px;">
            <b>Node ID:</b> ${node.node_id}<br/>
            <b>Criticality Score:</b> ${node.criticality_score}<br/>
            <b>Bridge Adjacent:</b> ${isBridge ? 'YES' : 'NO'}<br/>
            <b>Betweenness:</b> ${node.betweenness}
          </div>
        `);

        nodeMarkersRef.current?.addLayer(circle);
      });
    }
  }, [criticalNodes]);

  // Update Evacuation Route Polylines
  useEffect(() => {
    if (!mapRef.current || !routePolylinesRef.current) return;

    routePolylinesRef.current.clearLayers();

    if (evacuationRoutes && evacuationRoutes.length > 0) {
      evacuationRoutes.forEach((route, idx) => {
        if (route.path_coords && route.path_coords.length > 1) {
          const latLngs = route.path_coords.map(([lon, lat]) => [lat, lon] as [number, number]);
          const colorsList = ['#10b981', '#06b6d4', '#3b82f6', '#ec4899'];
          const polyColor = colorsList[idx % colorsList.length];

          const polyline = L.polyline(latLngs, {
            color: polyColor,
            weight: 5,
            dashArray: '8, 6',
            opacity: 0.9,
          });

          polyline.bindPopup(`
            <div style="font-family: sans-serif; font-size: 12px;">
              <b>Route:</b> ${route.route_id}<br/>
              <b>Vehicle:</b> ${route.vehicle}<br/>
              <b>ETA:</b> ${route.eta_min} mins
            </div>
          `);

          routePolylinesRef.current?.addLayer(polyline);
        }
      });
    }
  }, [evacuationRoutes]);

  return (
    <div className="bg-card border border-border rounded-xl p-4 shadow-sm flex flex-col h-full min-h-[420px]">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-bold tracking-wide uppercase text-foreground flex items-center gap-2">
          <span className="w-2.5 h-2.5 rounded-full bg-primary inline-block"></span>
          Geospatial Network & Route Map View
        </h3>
        <div className="flex items-center gap-3 text-xs">
          <span className="flex items-center gap-1">
            <span className="w-3 h-1 bg-purple-600 inline-block rounded"></span> Roads
          </span>
          <span className="flex items-center gap-1">
            <span className="w-2.5 h-2.5 bg-amber-500 rounded-full inline-block"></span> Critical Node
          </span>
          <span className="flex items-center gap-1">
            <span className="w-2.5 h-2.5 bg-red-500 rounded-full inline-block"></span> Bridge Bottleneck
          </span>
          <span className="flex items-center gap-1">
            <span className="w-3 h-1 bg-emerald-500 inline-block rounded"></span> Route
          </span>
        </div>
      </div>

      <div className="relative flex-1 rounded-lg overflow-hidden border border-border">
        <div ref={mapContainerRef} className="w-full h-full min-h-[360px] z-10" />

        {/* Road Mask PNG Overlay Preview if available */}
        {roadMaskBase64 && (
          <div className="absolute bottom-2 right-2 z-[1000] bg-card/90 backdrop-blur border border-border p-1.5 rounded-lg shadow">
            <p className="text-[10px] font-bold text-muted-foreground mb-1 text-center">Vision AI Road Mask</p>
            <img
              src={`data:image/png;base64,${roadMaskBase64}`}
              alt="Road Mask"
              className="w-24 h-24 object-cover rounded border border-border"
            />
          </div>
        )}
      </div>
    </div>
  );
};
