'use client';

import MetricCards from '@/components/overview/MetricCards';
import CurrentScenario from '@/components/overview/CurrentScenario';
import RecommendedAction from '@/components/overview/RecommendedAction';
import ImpactAnalysis from '@/components/overview/ImpactAnalysis';
import RestorationProgress from '@/components/overview/RestorationProgress';
import GridVisualization from '@/components/overview/GridVisualization';
import AssetDrawer from '@/components/overview/AssetDrawer';

export default function OverviewPage() {
  return (
    <div className="min-h-screen bg-slate-50 p-6">
      {/* Page header */}
      <div className="mb-5">
        <h1 className="text-xl font-semibold text-slate-900">
          Grid Operations Overview
        </h1>
        <p className="text-sm text-slate-500">
          Situational awareness and decision support for distribution-grid
          recovery
        </p>
      </div>

      {/* Metric cards — full width */}
      <div className="mb-4">
        <MetricCards />
      </div>

      {/* Two-column: grid network + scenario */}
      <div className="grid grid-cols-3 gap-4 mb-4">
        {/* Grid Network Visualization */}
        <div className="col-span-2">
          <GridVisualization />
        </div>

        {/* Current scenario */}
        <div className="col-span-1">
          <CurrentScenario />
        </div>
      </div>

      {/* Three-column: recommendation + impact + restoration */}
      <div className="grid grid-cols-3 gap-4">
        <div className="col-span-1">
          <RecommendedAction />
        </div>
        <div className="col-span-1">
          <ImpactAnalysis />
        </div>
        <div className="col-span-1">
          <RestorationProgress />
        </div>
      </div>
      <AssetDrawer />
    </div>
  );
}
