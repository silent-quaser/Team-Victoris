'use client';

import dynamic from 'next/dynamic';

const DynamicGeoMap = dynamic(() => import('./GeoMap'), {
  ssr: false,
  loading: () => (
    <div className="h-full w-full bg-slate-100 animate-pulse flex items-center justify-center text-slate-500 font-medium">
      Loading Real-World Map GIS Data...
    </div>
  ),
});

export default DynamicGeoMap;
