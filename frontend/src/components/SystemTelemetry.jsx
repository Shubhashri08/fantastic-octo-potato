import React from 'react';
import { Cpu, HardDrive, Activity, CheckCircle2, ShieldCheck, Database, Layers } from 'lucide-react';

export default function SystemTelemetry({ statusData, cameras, events }) {
  return (
    <div className="p-5 h-full overflow-y-auto bg-[#0A0A0A] space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3 pb-3 border-b border-[#2A2A2A]">
        <span className="material-symbols-outlined text-[#f5dfc0]">share_reviews</span>
        <div>
          <h2 className="text-sm font-bold text-[#f5dfc0] uppercase tracking-wider font-sans">
            Connect Layer — System Telemetry & AI Pipeline Health
          </h2>
          <p className="text-[11px] text-[#988f85] font-mono">
            RTX 2050 Hardware Metrics, Model Checkpoints, and Multi-Worker Topology
          </p>
        </div>
      </div>

      {/* Top 4 Metrics Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 font-mono">
        <div className="solid-card p-4 space-y-1">
          <div className="flex items-center justify-between text-[#988f85] text-xs">
            <span>COMPUTE ENGINE</span>
            <Cpu className="w-4 h-4 text-[#9ed1c1]" />
          </div>
          <div className="text-base font-bold text-[#f5dfc0]">
            {statusData?.device === 'cuda' ? 'NVIDIA CUDA' : 'CPU FALLBACK'}
          </div>
          <div className="text-[10px] text-[#9ed1c1]">
            {statusData?.gpu_name || 'Host CPU Engine'}
          </div>
        </div>

        <div className="solid-card p-4 space-y-1">
          <div className="flex items-center justify-between text-[#988f85] text-xs">
            <span>ACTIVE WORKERS</span>
            <Activity className="w-4 h-4 text-[#f5dfc0]" />
          </div>
          <div className="text-base font-bold text-[#f5dfc0]">
            {statusData?.active_camera_workers || cameras.length} THREADS
          </div>
          <div className="text-[10px] text-[#cfc5b9]">
            Dedicated MJPEG Pipelines
          </div>
        </div>

        <div className="solid-card p-4 space-y-1">
          <div className="flex items-center justify-between text-[#988f85] text-xs">
            <span>DATABASE RECORDS</span>
            <Database className="w-4 h-4 text-[#d8c3a5]" />
          </div>
          <div className="text-base font-bold text-[#f5dfc0]">
            {events.length} INCIDENTS
          </div>
          <div className="text-[10px] text-[#cfc5b9]">
            SQLite Persistence (vigrah.db)
          </div>
        </div>

        <div className="solid-card p-4 space-y-1">
          <div className="flex items-center justify-between text-[#988f85] text-xs">
            <span>INFERENCE CADENCE</span>
            <Layers className="w-4 h-4 text-[#9ed1c1]" />
          </div>
          <div className="text-base font-bold text-[#9ed1c1]">
            1 IN 3 FRAMES
          </div>
          <div className="text-[10px] text-[#988f85]">
            4GB VRAM Optimization
          </div>
        </div>
      </div>

      {/* Model Registry & Weights Stack */}
      <div className="solid-card p-4 space-y-3 font-mono text-xs">
        <div className="flex items-center justify-between border-b border-[#222222] pb-2">
          <span className="font-bold text-[#f5dfc0] uppercase">Active Neural Model Architecture</span>
          <span className="text-[10px] text-[#9ed1c1] bg-[#1C1B1B] px-2 py-0.5 border border-[#2A2A2A]">
            ZERO PAID SERVICES
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          <div className="p-3 bg-[#141414] border border-[#222222] space-y-1">
            <div className="text-[#9ed1c1] font-bold">1. Base Detector</div>
            <div className="text-[#cfc5b9]">Ultralytics YOLO11 Nano (yolo11n.pt)</div>
            <div className="text-[10px] text-[#988f85]">Vehicles, Pedestrians, Bounding Boxes</div>
          </div>

          <div className="p-3 bg-[#141414] border border-[#222222] space-y-1">
            <div className="text-[#ffd9d7] font-bold">2. Fire / Smoke Engine</div>
            <div className="text-[#cfc5b9]">HSV Flame Spectral + YOLO Multi-Scale</div>
            <div className="text-[10px] text-[#988f85]">Flicker analysis, Flame hue segmentation</div>
          </div>

          <div className="p-3 bg-[#141414] border border-[#222222] space-y-1">
            <div className="text-[#f5dfc0] font-bold">3. Accident & Collision</div>
            <div className="text-[#cfc5b9]">Spatial IoU Polygon Intersection</div>
            <div className="text-[10px] text-[#988f85]">Temporal cluster overlap (&gt;0.05 IoU)</div>
          </div>
        </div>
      </div>

      {/* Connected Camera Node Health Table */}
      <div className="solid-card p-4 space-y-3 font-mono text-xs">
        <div className="font-bold text-[#f5dfc0] uppercase border-b border-[#222222] pb-2">
          Surveillance Node Stream Workers
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-[11px]">
            <thead className="text-[#988f85] border-b border-[#222222]">
              <tr>
                <th className="py-2">Node ID</th>
                <th className="py-2">Designation</th>
                <th className="py-2">Source Type</th>
                <th className="py-2">Location Coordinates</th>
                <th className="py-2">Stream Protocol</th>
                <th className="py-2 text-right">Worker Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#1D1D1D] text-[#cfc5b9]">
              {cameras.map((c) => (
                <tr key={c.id}>
                  <td className="py-2 font-bold text-[#f5dfc0]">CAM-0{c.id}</td>
                  <td className="py-2">{c.name}</td>
                  <td className="py-2 uppercase text-[#988f85]">{c.source_type}</td>
                  <td className="py-2 text-[10px]">{c.lat.toFixed(4)}°N, {c.lon.toFixed(4)}°E</td>
                  <td className="py-2">MJPEG /stream/{c.id}</td>
                  <td className="py-2 text-right">
                    <span className="px-2 py-0.5 text-[10px] bg-[#1d4f43] text-[#9ed1c1]">
                      {c.is_active ? 'RUNNING' : 'STOPPED'}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
