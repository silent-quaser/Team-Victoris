const fs = require('fs');
const path = require('path');

const mockPath = path.join(__dirname, 'src', 'data', 'mock-data.ts');
let data = fs.readFileSync(mockPath, 'utf8');

// Center: Guindy, Chennai
const CENTER_LAT = 13.0067;
const CENTER_LNG = 80.2206;

// Much smaller step size for a localized neighborhood distribution grid (~150-200m)
const STEP_SIZE = 0.0015; 

const tree = {
  1: { angle: 45, dist: 0 },
  // Main trunk
  2: { parent: 1, angle: 45 },
  3: { parent: 2, angle: 40 },
  4: { parent: 3, angle: 50 },
  5: { parent: 4, angle: 45 },
  6: { parent: 5, angle: 30 },
  7: { parent: 6, angle: 45 },
  8: { parent: 7, angle: 60 },
  9: { parent: 8, angle: 45 },
  10: { parent: 9, angle: 30 },
  11: { parent: 10, angle: 45 },
  12: { parent: 11, angle: 45 },
  13: { parent: 12, angle: 50 },
  14: { parent: 13, angle: 40 },
  15: { parent: 14, angle: 45 },
  16: { parent: 15, angle: 30 },
  17: { parent: 16, angle: 45 },
  18: { parent: 17, angle: 45 },

  // Branch 2 from Node 2
  19: { parent: 2, angle: 135 },
  20: { parent: 19, angle: 140 },
  21: { parent: 20, angle: 120 },
  22: { parent: 21, angle: 135 },

  // Branch 3 from Node 3
  23: { parent: 3, angle: 225 },
  24: { parent: 23, angle: 210 },
  25: { parent: 24, angle: 230 },

  // Branch 4 from Node 6
  26: { parent: 6, angle: 315 },
  27: { parent: 26, angle: 300 },
  28: { parent: 27, angle: 320 },
  29: { parent: 28, angle: 315 },
  30: { parent: 29, angle: 330 },
  31: { parent: 30, angle: 315 },
  32: { parent: 31, angle: 300 },
  33: { parent: 32, angle: 315 },
};

const coords = {};
for (let i = 1; i <= 33; i++) {
  if (i === 1) {
    coords[i] = { lat: CENTER_LAT, lng: CENTER_LNG };
  } else {
    const node = tree[i];
    const parentCoords = coords[node.parent];
    
    // Slight jitter to make it look organic
    const jitterAngle = (Math.random() - 0.5) * 30; 
    const finalAngle = (node.angle + jitterAngle) * (Math.PI / 180); 
    const step = STEP_SIZE * (0.7 + Math.random() * 0.6); // Randomize line length slightly

    coords[i] = {
      lat: parentCoords.lat + (Math.cos(finalAngle) * step),
      lng: parentCoords.lng + (Math.sin(finalAngle) * step)
    };
  }
}

// Map 10 critical facilities in Chennai
const criticalFacilities = {
  3: 'Apollo Hospital Guindy',
  7: 'MIOT International',
  10: 'Fortis Malar Hospital',
  14: 'BSNL Exchange Guindy',
  18: 'Airtel Network Hub',
  21: 'Guindy Water Station',
  24: 'Metro Water Treatment',
  27: 'Guindy Fire Station',
  30: 'Police Headquarters',
  33: 'Guindy Metro Station'
};

// 1. Update buses with new coordinates and critical facilities
data = data.replace(/\{ id: 'bus-(\d+)',[^}]+\}/g, (match, numStr) => {
    const num = parseInt(numStr);
    if (!coords[num]) return match;

    // Remove old latitude/longitude/critical_facility/is_critical to rebuild cleanly
    let newMatch = match
        .replace(/, latitude: [\d\.]+/, '')
        .replace(/, longitude: [\d\.]+/, '')
        .replace(/, is_critical: (true|false)/, '')
        .replace(/, critical_facility: '[^']+'/, '');
    
    // Add new fields
    const isCritical = criticalFacilities[num] ? true : false;
    const critFacStr = isCritical ? `, critical_facility: '${criticalFacilities[num]}'` : '';
    
    // Insert after has_der
    newMatch = newMatch.replace(/(has_der: (true|false))/, `$1, is_critical: ${isCritical}${critFacStr}, latitude: ${coords[num].lat.toFixed(6)}, longitude: ${coords[num].lng.toFixed(6)}`);
    
    return newMatch;
});

// 2. Replace transformers array completely with 8 transformers
const transformersRegex = /export const transformers: Transformer\[\] = \[[\s\S]*?\];/;
const newTransformers = `export const transformers: Transformer[] = [
  { id: 't-1', name: 'Transformer T1', bus_id: 'bus-2', status: 'healthy', rating_mva: 5.0, load_pct: 45, tap_position: 1 },
  { id: 't-2', name: 'Transformer T2', bus_id: 'bus-5', status: 'healthy', rating_mva: 2.5, load_pct: 60, tap_position: 0 },
  { id: 't-3', name: 'Transformer T3', bus_id: 'bus-8', status: 'uncertain', rating_mva: 10.0, load_pct: 88, tap_position: 2 },
  { id: 't-4', name: 'Transformer T4', bus_id: 'bus-12', status: 'failed', rating_mva: 5.0, load_pct: 0, tap_position: -1 },
  { id: 't-5', name: 'Transformer T5', bus_id: 'bus-16', status: 'healthy', rating_mva: 2.5, load_pct: 35, tap_position: 0 },
  { id: 't-6', name: 'Transformer T6', bus_id: 'bus-20', status: 'healthy', rating_mva: 5.0, load_pct: 55, tap_position: 1 },
  { id: 't-7', name: 'Transformer T7', bus_id: 'bus-24', status: 'healthy', rating_mva: 7.5, load_pct: 40, tap_position: 0 },
  { id: 't-8', name: 'Transformer T8', bus_id: 'bus-28', status: 'healthy', rating_mva: 3.0, load_pct: 75, tap_position: 1 }
];`;

data = data.replace(transformersRegex, newTransformers);

fs.writeFileSync(mockPath, data);
console.log('Successfully scattered buses across a localized Chennai area with 8 transformers and 10 critical facilities!');
