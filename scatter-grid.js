const fs = require('fs');
const path = require('path');

const mockPath = path.join(__dirname, 'src', 'data', 'mock-data.ts');
let data = fs.readFileSync(mockPath, 'utf8');

const CENTER_LAT = 8.5241;
const CENTER_LNG = 76.9366;

// IEEE 33 tree structure:
// B1 is substation
// Branch 1: 1-2-3-4-5-6-7-8-9-10-11-12-13-14-15-16-17-18
// Branch 2: 2-19-20-21-22
// Branch 3: 3-23-24-25
// Branch 4: 6-26-27-28-29-30-31-32-33

const tree = {
  1: { angle: 45, dist: 0 },
  // Main trunk (North-East ish)
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

  // Branch 2 from Node 2 (South-East ish)
  19: { parent: 2, angle: 135 },
  20: { parent: 19, angle: 140 },
  21: { parent: 20, angle: 120 },
  22: { parent: 21, angle: 135 },

  // Branch 3 from Node 3 (South-West ish)
  23: { parent: 3, angle: 225 },
  24: { parent: 23, angle: 210 },
  25: { parent: 24, angle: 230 },

  // Branch 4 from Node 6 (North-West ish)
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
const STEP_SIZE = 0.008; // ~800 meters

// Compute coordinates
for (let i = 1; i <= 33; i++) {
  if (i === 1) {
    coords[i] = { lat: CENTER_LAT, lng: CENTER_LNG };
  } else {
    const node = tree[i];
    if (!node) {
       // fallback
       coords[i] = { lat: CENTER_LAT + 0.01, lng: CENTER_LNG + 0.01 };
       continue;
    }
    const parentCoords = coords[node.parent];
    
    // Add jitter (-10 to +10 degrees)
    const jitterAngle = (Math.random() - 0.5) * 20; 
    const finalAngle = (node.angle + jitterAngle) * (Math.PI / 180); // radians
    
    // Step distance variation
    const step = STEP_SIZE * (0.8 + Math.random() * 0.4);

    coords[i] = {
      lat: parentCoords.lat + (Math.cos(finalAngle) * step),
      lng: parentCoords.lng + (Math.sin(finalAngle) * step)
    };
  }
}

// Replace in mock-data.ts
data = data.replace(/number:\s*(\d+),[\s\S]*?y:\s*\d+(?:,\s*lat:\s*[\d\.]+,\s*lng:\s*[\d\.]+)?/g, (match, numStr) => {
    const num = parseInt(numStr);
    if (coords[num]) {
        // Find existing x/y to preserve them
        const xMatch = match.match(/x:\s*(\d+)/);
        const yMatch = match.match(/y:\s*(\d+)/);
        const x = xMatch ? xMatch[1] : 0;
        const y = yMatch ? yMatch[1] : 0;
        
        // Return replaced block
        return match.replace(/x:\s*\d+,\s*y:\s*\d+(?:,\s*lat:\s*[\d\.]+,\s*lng:\s*[\d\.]+)?/, 
          `x: ${x}, y: ${y}, latitude: ${coords[num].lat.toFixed(6)}, longitude: ${coords[num].lng.toFixed(6)}`);
    }
    return match;
});

fs.writeFileSync(mockPath, data);
console.log('Successfully scattered buses across Trivandrum based on network topology!');
