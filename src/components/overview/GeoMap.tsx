'use client';

import React, { useEffect, useState, useMemo } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Polyline, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { useGridStore } from '@/store/grid-store';
import { AssetStatus, Bus, Line } from '@/types';
import { renderToString } from 'react-dom/server';
import { Hospital, Zap, Radio, Building2, MapPin } from 'lucide-react';

// ==========================================
// 1. Map Bounds Component
// ==========================================
const MapBoundsFitter = ({ buses }: { buses: Bus[] }) => {
  const map = useMap();

  useEffect(() => {
    const validBuses = buses.filter(b => b.latitude && b.longitude);
    if (validBuses.length > 0) {
      const bounds = L.latLngBounds(
        validBuses.map(b => [b.latitude!, b.longitude!])
      );
      // Pad bounds slightly so edges aren't cut off
      map.fitBounds(bounds, { padding: [50, 50], maxZoom: 15 });
    }
  }, [map, buses]);

  return null;
};

// ==========================================
// 2. Icon Generators
// ==========================================
const getStatusColors = (status: AssetStatus) => {
  switch (status) {
    case 'failed': return { bg: '#ef4444', border: '#b91c1c' }; // Red
    case 'uncertain': return { bg: '#f59e0b', border: '#b45309' }; // Orange
    case 'healthy': return { bg: '#22c55e', border: '#15803d' }; // Green
    case 'selected': return { bg: '#3b82f6', border: '#1d4ed8' }; // Blue
    default: return { bg: '#64748b', border: '#334155' };
  }
};

const createCustomIcon = (bus: Bus, isSelected: boolean) => {
  const status = isSelected ? 'selected' : bus.status;
  const colors = getStatusColors(status);
  
  let iconHtml = '';
  let size = 16;
  const isSubstation = bus.number === 1;

  if (isSubstation) {
    size = 28;
    iconHtml = renderToString(<MapPin size={18} color="white" />);
  } else if (bus.is_critical && bus.critical_facility) {
    size = 24;
    const name = bus.critical_facility.toLowerCase();
    if (name.includes('hospital')) iconHtml = renderToString(<Hospital size={14} color="white" />);
    else if (name.includes('telecom') || name.includes('exchange')) iconHtml = renderToString(<Radio size={14} color="white" />);
    else iconHtml = renderToString(<Building2 size={14} color="white" />);
  } else if (bus.has_der) {
    size = 20;
    iconHtml = renderToString(<Zap size={12} color="white" />);
  }

  const pulseClass = status === 'failed' ? 'animate-pulse ring-4 ring-red-400/50' : '';
  const shapeClass = isSubstation ? 'rounded-md' : 'rounded-full';

  const htmlString = `
    <div 
      class="${shapeClass} ${pulseClass} flex items-center justify-center shadow-lg"
      style="
        background-color: ${colors.bg};
        border: 2px solid white;
        width: ${size}px;
        height: ${size}px;
      "
    >
      ${iconHtml}
    </div>
  `;

  return L.divIcon({
    html: htmlString,
    className: 'custom-leaflet-icon',
    iconSize: [size, size],
    iconAnchor: [size / 2, size / 2],
    popupAnchor: [0, -size / 2],
  });
};

// ==========================================
// 3. Main Map Component
// ==========================================
export default function GeoMap() {
  const { gridState, selectAsset, selectedAssetId } = useGridStore();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) return <div className="h-full w-full bg-slate-50 animate-pulse flex items-center justify-center">Loading GIS Data...</div>;

  // Fallback center if bounds fail
  const fallbackCenter: [number, number] = [8.5241, 76.9366];

  return (
    <div className="h-full w-full relative z-0">
      <MapContainer 
        center={fallbackCenter} 
        zoom={13} 
        style={{ height: '100%', width: '100%', zIndex: 0 }}
        zoomControl={true}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        
        {/* Auto-fitter for bounds */}
        <MapBoundsFitter buses={gridState.buses} />

        {/* Render Edges (Lines) */}
        {gridState.lines.map((line: Line) => {
          const fromBus = gridState.buses.find(b => b.id === line.from_bus);
          const toBus = gridState.buses.find(b => b.id === line.to_bus);
          
          if (!fromBus?.latitude || !fromBus?.longitude || !toBus?.latitude || !toBus?.longitude) return null;

          const isSelected = selectedAssetId === line.id;
          const status = isSelected ? 'selected' : line.status;
          const colors = getStatusColors(status);
          
          const isDashed = status === 'failed' || status === 'uncertain';

          return (
            <Polyline
              key={line.id}
              positions={[
                [fromBus.latitude, fromBus.longitude],
                [toBus.latitude, toBus.longitude]
              ]}
              color={colors.bg}
              weight={isSelected ? 6 : (line.type === 'feeder' ? 4 : 3)}
              opacity={isSelected ? 1 : 0.7}
              dashArray={isDashed ? '6, 8' : undefined}
              eventHandlers={{
                click: () => selectAsset(line.id),
              }}
              className="cursor-pointer transition-all duration-300"
            />
          );
        })}

        {/* Render Nodes (Buses/Critical Services) */}
        {gridState.buses.map((bus: Bus) => {
          if (!bus.latitude || !bus.longitude) return null;
          const isSelected = selectedAssetId === bus.id;

          return (
            <Marker 
              key={bus.id} 
              position={[bus.latitude, bus.longitude]}
              icon={createCustomIcon(bus, isSelected)}
              eventHandlers={{
                click: () => selectAsset(bus.id),
              }}
            >
              <Popup className="rounded-lg shadow-xl border-0">
                <div className="font-semibold text-slate-800 border-b pb-2 mb-2">{bus.name}</div>
                
                {bus.is_critical && (
                  <div className="text-xs text-blue-700 bg-blue-50 px-2 py-1 rounded font-bold mb-2 inline-block">
                    ★ {bus.critical_facility}
                  </div>
                )}
                
                <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs text-slate-600 mb-3">
                  <span className="font-medium">Type:</span> <span>{bus.number === 1 ? 'Substation' : 'Bus'}</span>
                  <span className="font-medium">Status:</span> 
                  <span className={`font-bold uppercase ${bus.status === 'failed' ? 'text-red-600' : bus.status === 'healthy' ? 'text-green-600' : 'text-orange-600'}`}>
                    {bus.status}
                  </span>
                  <span className="font-medium">Voltage:</span> <span>{bus.voltage_kv} kV</span>
                  <span className="font-medium">Load:</span> <span>{bus.load_mw} MW</span>
                </div>
                
                <button 
                  onClick={(e) => { e.stopPropagation(); selectAsset(bus.id); }}
                  className="w-full bg-slate-900 hover:bg-slate-800 text-white text-xs font-medium py-1.5 rounded transition-colors"
                >
                  View in Asset Drawer
                </button>
              </Popup>
            </Marker>
          );
        })}

        {/* Render Transformers */}
        {gridState.transformers.map((t) => {
          const bus = gridState.buses.find(b => b.id === t.bus_id);
          if (!bus?.latitude || !bus?.longitude) return null;
          
          const isSelected = selectedAssetId === t.id;
          const status = isSelected ? 'selected' : t.status;
          const colors = getStatusColors(status);
          const pulseClass = status === 'failed' ? 'animate-pulse ring-4 ring-red-400/50' : '';
          
          const iconHtml = `
            <div 
              class="flex flex-col items-center justify-center cursor-pointer ${pulseClass} hover:scale-110 transition-transform"
              style="width: 24px; height: 30px; margin-top: -15px; margin-left: 15px;"
            >
              <div class="w-5 h-5 rounded-full border-2 bg-white flex items-center justify-center z-10" style="border-color: ${colors.border}">
                <div class="w-1.5 h-1.5 rounded-full" style="background-color: ${colors.bg}"></div>
              </div>
              <div class="w-5 h-5 rounded-full border-2 bg-white -mt-3 z-0" style="border-color: ${colors.border}"></div>
            </div>
          `;

          const tIcon = L.divIcon({
            html: iconHtml,
            className: 'custom-leaflet-icon bg-transparent',
            iconSize: [24, 30],
            iconAnchor: [12, 15],
            popupAnchor: [12, -10],
          });

          // Offset transformer slightly from its parent bus so they don't perfectly overlap
          const offsetLat = bus.latitude + 0.0003;
          const offsetLng = bus.longitude + 0.0003;

          return (
            <Marker 
              key={t.id} 
              position={[offsetLat, offsetLng]}
              icon={tIcon}
              eventHandlers={{
                click: () => selectAsset(t.id),
              }}
            >
              <Popup className="rounded-lg shadow-xl border-0">
                <div className="font-semibold text-slate-800 border-b pb-2 mb-2">{t.name}</div>
                <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs text-slate-600 mb-3">
                  <span className="font-medium">Status:</span> 
                  <span className={`font-bold uppercase ${t.status === 'failed' ? 'text-red-600' : t.status === 'healthy' ? 'text-green-600' : 'text-orange-600'}`}>
                    {t.status}
                  </span>
                  <span className="font-medium">Rating:</span> <span>{t.rating_mva} MVA</span>
                  <span className="font-medium">Load:</span> <span>{t.load_pct}%</span>
                  <span className="font-medium">Tap Pos:</span> <span>{t.tap_position}</span>
                </div>
                <button 
                  onClick={(e) => { e.stopPropagation(); selectAsset(t.id); }}
                  className="w-full bg-slate-900 hover:bg-slate-800 text-white text-xs font-medium py-1.5 rounded transition-colors"
                >
                  View Details
                </button>
              </Popup>
            </Marker>
          );
        })}
      </MapContainer>
    </div>
  );
}
