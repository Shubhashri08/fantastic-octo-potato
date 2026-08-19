import React, { useState } from 'react';
import { Eye, ShieldAlert, Filter, Search } from 'lucide-react';

export default function EventTable({ events, onSelectEvent, onSelectCamera, selectedCameraId }) {
 const [filterType, setFilterType] = useState('All');
 const [filterSeverity, setFilterSeverity] = useState('All');
 const [searchTerm, setSearchTerm] = useState('');

 const filteredEvents = events.filter((ev) => {
 const matchesType = filterType === 'All' || ev.event_type.toLowerCase().includes(filterType.toLowerCase());
 const matchesSeverity = filterSeverity === 'All' || ev.severity === filterSeverity;
 const matchesCam = !selectedCameraId || ev.camera_id === selectedCameraId;
 const matchesSearch = !searchTerm || ev.event_type.toLowerCase().includes(searchTerm.toLowerCase()) || String(ev.camera_id).includes(searchTerm);
 return matchesType && matchesSeverity && matchesCam && matchesSearch;
 });

 const getSeverityChip = (severity) => {
 switch (severity) {
 case 'High':
 return <span className="px-2 py-0.5 text-[10px] font-mono font-bold bg-[#8e3335] text-[#ffd9d7] border border-[#ffb4ab]/30">HIGH</span>;
 case 'Medium':
 default:
 return <span className="px-2 py-0.5 text-[10px] font-mono font-bold bg-[#5f5038] text-[#f6dfc0] border border-[#d8c3a5]/30">MED</span>;
 }
 };

 const getEventTypeTag = (type) => {
 switch (type) {
 case 'Fighting':
 case 'Violence':
 return <span className="text-[#ffb4ab] font-mono font-bold"> FIGHTING / VIOLENCE</span>;
 case 'Fire':
 return <span className="text-[#ffd9d7] font-mono font-bold"> FIRE OUTBREAK</span>;
 case 'Smoke':
 return <span className="text-[#cfc5b9] font-mono font-bold"> SMOKE PLUME</span>;
 default:
 return <span className="text-[#f5dfc0] font-mono font-bold"> {type.toUpperCase()}</span>;
 }
 };

 return (
 <div className="flex flex-col h-full overflow-hidden p-4 bg-[#0A0A0A]">
 {/* Top Filter and Controls Bar */}
 <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-3 pb-3 mb-3 border-b border-[#2A2A2A] flex-shrink-0">
 <div className="flex items-center gap-3">
 <span className="material-symbols-outlined text-[#f5dfc0]">fingerprint</span>
 <div>
 <h2 className="text-sm font-bold text-[#f5dfc0] uppercase tracking-wider font-sans">
 Identify Layer — Violence & Fire Incident Log
 </h2>
 <p className="text-[11px] text-[#988f85] font-mono">
 Event-Driven Triggers • Verified via Temporal Confirmation (≥3 Consecutive Frames)
 </p>
 </div>
 </div>

 {/* Filters */}
 <div className="flex flex-wrap items-center gap-2 text-xs">
 {/* Search Box */}
 <div className="flex items-center bg-[#141414] border border-[#2A2A2A] px-2 py-1">
 <Search className="w-3.5 h-3.5 text-[#988f85] mr-1.5" />
 <input
 type="text"
 placeholder="Search incidents..."
 value={searchTerm}
 onChange={(e) => setSearchTerm(e.target.value)}
 className="bg-transparent text-xs font-mono text-[#e5e2e1] focus:outline-none placeholder-[#555555] w-[130px]"
 />
 </div>

 {/* Type Filter */}
 <select
 value={filterType}
 onChange={(e) => setFilterType(e.target.value)}
 className="px-2.5 py-1 bg-[#141414] border border-[#2A2A2A] text-[#cfc5b9] font-mono text-xs focus:outline-none"
 >
 <option value="All">All Categories</option>
 <option value="Fighting">Fighting / Violence</option>
 <option value="Fire">Fire</option>
 <option value="Smoke">Smoke</option>
 </select>

 {/* Severity Filter */}
 <select
 value={filterSeverity}
 onChange={(e) => setFilterSeverity(e.target.value)}
 className="px-2.5 py-1 bg-[#141414] border border-[#2A2A2A] text-[#cfc5b9] font-mono text-xs focus:outline-none"
 >
 <option value="All">All Severities</option>
 <option value="High">High Severity</option>
 <option value="Medium">Medium Severity</option>
 </select>

 {selectedCameraId && (
 <button
 onClick={() => onSelectCamera(null)}
 className="px-2 py-1 bg-[#241113] text-[#ffd9d7] border border-[#8e3335] text-[11px] font-mono"
 >
 Clear CAM-0{selectedCameraId} Filter x
 </button>
 )}
 </div>
 </div>

 {/* High Density Table */}
 <div className="flex-1 overflow-auto border border-[#222222] bg-[#111111]">
 <table className="w-full text-left text-xs">
 <thead className="sticky top-0 bg-[#161616] border-b border-[#2A2A2A] z-10">
 <tr className="text-[#988f85] uppercase font-mono text-[10px] tracking-wider">
 <th className="py-2 px-3">Event ID</th>
 <th className="py-2 px-3">Incident Classification</th>
 <th className="py-2 px-3">Camera Node</th>
 <th className="py-2 px-3">Confidence Score</th>
 <th className="py-2 px-3">Severity</th>
 <th className="py-2 px-3">Timestamp</th>
 <th className="py-2 px-3 text-right">Verification</th>
 </tr>
 </thead>
 <tbody className="divide-y divide-[#1D1D1D] font-medium font-mono text-[11px]">
 {filteredEvents.length === 0 ? (
 <tr>
 <td colSpan="7" className="py-12 text-center text-[#555555]">
 No active violence or fire incidents recorded.
 </td>
 </tr>
 ) : (
 filteredEvents.map((ev) => (
 <tr
 key={ev.id}
 onClick={() => onSelectEvent(ev)}
 className="hover:bg-[#1A1A1A] cursor-pointer transition-colors"
 >
 <td className="py-2.5 px-3 text-[#988f85]">#EV-{String(ev.id).padStart(4, '0')}</td>
 <td className="py-2.5 px-3">{getEventTypeTag(ev.event_type)}</td>
 <td className="py-2.5 px-3">
 <button
 onClick={(e) => {
 e.stopPropagation();
 onSelectCamera(ev.camera_id);
 }}
 className="px-2 py-0.5 bg-[#161616] hover:bg-[#222222] text-[#f5dfc0] border border-[#2E2E2E] text-[10px] transition"
 >
 CAM-0{ev.camera_id}
 </button>
 </td>
 <td className="py-2.5 px-3 font-bold text-[#9ed1c1]">
 {(ev.confidence * 100).toFixed(1)}%
 </td>
 <td className="py-2.5 px-3">{getSeverityChip(ev.severity)}</td>
 <td className="py-2.5 px-3 text-[#988f85]">
 {new Date(ev.timestamp).toLocaleTimeString()}
 </td>
 <td className="py-2.5 px-3 text-right">
 <button
 onClick={(e) => {
 e.stopPropagation();
 onSelectEvent(ev);
 }}
 className="inline-flex items-center gap-1 px-2.5 py-1 bg-[#1C1B1B] hover:bg-[#2A2A2A] text-[#f5dfc0] border border-[#353534] text-[10px] uppercase font-bold transition"
 >
 <Eye className="w-3 h-3" /> Snapshot
 </button>
 </td>
 </tr>
 ))
 )}
 </tbody>
 </table>
 </div>
 </div>
 );
}
