import React, { useEffect, useRef } from 'react';
import L from 'leaflet';
import { CriticalNode, EvacuationRoute } from '../types';
import { MapPin, Navigation2, Layers } from 'lucide-react';

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
      const map = L.map(mapContainerRef.current, {
        center: [0.02, 0.02],
        zoom: 12,
        zoomControl: true,
        attributionControl: false,
      });

      // Dark Matter tiles from CARTO
      L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
        attribution: '&copy; OSM &copy; CARTO',
        subdomains: 'abcd',
        maxZoom: 20,
      }).addTo(map);

      // Custom attribution control (bottom-right, minimal)
      L.control.attribution({ position: 'bottomright', prefix: false }).addTo(map);

      mapRef.current = map;
      nodeMarkersRef.current = L.layerGroup().addTo(map);
      routePolylinesRef.current = L.layerGroup().addTo(map);
    }
  }, []);

  useEffect(() => {
    if (!mapRef.current) return;
    if (geojsonLayerRef.current) {
      mapRef.current.removeLayer(geojsonLayerRef.current);
      geojsonLayerRef.current = null;
    }
    if (roadsGeoJSON?.features?.length > 0) {
      const geoLayer = L.geoJSON(roadsGeoJSON, {
        style: () => ({
          color: '#a855f7',
          weight: 2.5,
          opacity: 0.85,
        }),
      }).addTo(mapRef.current);
      geojsonLayerRef.current = geoLayer;
      try {
        const bounds = geoLayer.getBounds();
        if (bounds.isValid()) mapRef.current.fitBounds(bounds, { padding: [40, 40] });
      } catch (e) {}
    }
  }, [roadsGeoJSON]);

  useEffect(() => {
    if (!mapRef.current || !nodeMarkersRef.current) return;
    nodeMarkersRef.current.clearLayers();
    if (criticalNodes?.length) {
      criticalNodes.forEach((node) => {
        const isBridge = node.is_bridge_adjacent;
        const color = isBridge ? '#f43f5e' : '#f59e0b';
        const glowColor = isBridge ? 'rgba(244,63,94,0.6)' : 'rgba(245,158,11,0.6)';
        const radius = Math.max(6, Math.min(14, node.criticality_score * 18));

        const circle = L.circleMarker([node.lat, node.lon], {
          radius,
          fillColor: color,
          color: 'rgba(0,0,0,0.5)',
          weight: 2,
          opacity: 1,
          fillOpacity: 0.9,
        });

        circle.bindPopup(`
          <div style="font-family:'Inter',sans-serif;font-size:12px;padding:6px;background:#0a0e1e;color:#f0f4ff;border-radius:8px;min-width:160px">
            <div style="font-weight:700;color:#a855f7;margin-bottom:4px">Node: ${node.node_id}</div>
            <div style="color:#8892b0">Criticality: <span style="color:#f0f4ff;font-weight:600">${node.criticality_score.toFixed(3)}</span></div>
            <div style="color:#8892b0">Bridge Adj: <span style="color:${isBridge ? '#f43f5e' : '#10b981'};font-weight:600">${isBridge ? 'YES ⚠️' : 'NO'}</span></div>
            <div style="color:#8892b0">Betweenness: <span style="color:#f0f4ff">${node.betweenness.toFixed(4)}</span></div>
          </div>
        `);

        nodeMarkersRef.current?.addLayer(circle);
      });
    }
  }, [criticalNodes]);

  useEffect(() => {
    if (!mapRef.current || !routePolylinesRef.current) return;
    routePolylinesRef.current.clearLayers();
    if (evacuationRoutes?.length) {
      const ROUTE_COLORS = ['#10b981', '#06b6d4', '#3b82f6', '#f43f5e', '#a855f7'];
      evacuationRoutes.forEach((route, idx) => {
        if (route.path_coords?.length > 1) {
          const latLngs = route.path_coords.map(([lon, lat]) => [lat, lon] as [number, number]);
          const color = ROUTE_COLORS[idx % ROUTE_COLORS.length];

          const polyline = L.polyline(latLngs, {
            color,
            weight: 4,
            dashArray: '10, 6',
            opacity: 0.9,
          });

          polyline.bindPopup(`
            <div style="font-family:'Inter',sans-serif;font-size:12px;padding:6px;background:#0a0e1e;color:#f0f4ff;border-radius:8px">
              <div style="font-weight:700;color:${color};margin-bottom:4px">${route.route_id.toUpperCase()}</div>
              <div style="color:#8892b0">Vehicle: <span style="color:#f0f4ff">${route.vehicle}</span></div>
              <div style="color:#8892b0">ETA: <span style="color:#10b981;font-weight:600">${route.eta_min} min</span></div>
            </div>
          `);

          routePolylinesRef.current?.addLayer(polyline);
        }
      });
    }
  }, [evacuationRoutes]);

  const hasData = roadsGeoJSON?.features?.length || criticalNodes?.length || evacuationRoutes?.length;

  return (
    <div className="glass-card overflow-hidden" style={{ height: '500px', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <div className="flex items-center justify-between px-5 py-3 border-b border-white/[0.06] bg-white/[0.02]">
        <h3 className="text-sm font-bold text-white flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-violet-500 animate-pulse-glow" />
          Geospatial Network & Route Map
        </h3>
        <div className="flex items-center gap-4 text-[10px] font-medium">
          <span className="flex items-center gap-1.5 text-purple-400">
            <span className="w-4 h-0.5 bg-purple-400 inline-block rounded" /> Roads
          </span>
          <span className="flex items-center gap-1.5 text-amber-400">
            <span className="w-2 h-2 bg-amber-400 rounded-full inline-block" /> Critical
          </span>
          <span className="flex items-center gap-1.5 text-rose-400">
            <span className="w-2 h-2 bg-rose-400 rounded-full inline-block" /> Bridge
          </span>
          <span className="flex items-center gap-1.5 text-emerald-400">
            <span className="w-4 h-0.5 bg-emerald-400 inline-block rounded border-dashed" style={{ borderTop: '2px dashed' }} /> Route
          </span>
        </div>
      </div>

      {/* Map Container */}
      <div className="relative flex-1">
        <div ref={mapContainerRef} className="w-full h-full z-10" />

        {/* Empty state overlay */}
        {!hasData && (
          <div className="absolute inset-0 z-[500] flex flex-col items-center justify-center pointer-events-none">
            <div className="glass-card px-6 py-4 text-center max-w-xs">
              <Layers className="w-8 h-8 text-violet-400 mx-auto mb-2 opacity-60" />
              <p className="text-xs text-muted-foreground">Upload a satellite image and run the workflow to see road network extraction and evacuation routes</p>
            </div>
          </div>
        )}

        {/* Road Mask Preview */}
        {roadMaskBase64 && (
          <div className="absolute bottom-3 right-3 z-[1000] glass-card p-2">
            <p className="text-[9px] font-bold text-muted-foreground mb-1 text-center tracking-wider uppercase">AI Road Mask</p>
            <img
              src={`data:image/png;base64,${roadMaskBase64}`}
              alt="Road Mask"
              className="w-20 h-20 object-cover rounded-lg border border-white/[0.1]"
            />
          </div>
        )}
      </div>
    </div>
  );
};
