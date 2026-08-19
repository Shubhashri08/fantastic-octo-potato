import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import Header from './components/Header';
import Sidebar from './components/Sidebar';
import LiveStreamGrid from './components/LiveStreamGrid';
import CameraMap from './components/CameraMap';
import IdentifyConsole from './components/IdentifyConsole';
import RespondConsole from './components/RespondConsole';
import SystemTelemetry from './components/SystemTelemetry';
import SnapshotModal from './components/SnapshotModal';

const pageVariants = {
  initial: { opacity: 0, y: 8, scale: 0.995 },
  animate: { opacity: 1, y: 0, scale: 1, transition: { duration: 0.22, ease: [0.22, 1, 0.36, 1] } },
  exit: { opacity: 0, y: -6, scale: 0.995, transition: { duration: 0.15, ease: 'easeIn' } }
};

export default function App() {
  const [activeTab, setActiveTab] = useState('sense');
  const [cameras, setCameras] = useState([]);
  const [events, setEvents] = useState([]);
  const [statusData, setStatusData] = useState(null);
  const [selectedCameraId, setSelectedCameraId] = useState(null);
  const [selectedEventForModal, setSelectedEventForModal] = useState(null);

  const fetchData = useCallback(async () => {
    try {
      const [camRes, evRes, statusRes] = await Promise.all([
        fetch('/api/cameras').catch(() => null),
        fetch('/api/events').catch(() => null),
        fetch('/api/status').catch(() => null)
      ]);

      if (camRes && camRes.ok) {
        const camData = await camRes.json();
        setCameras(camData);
      }
      if (evRes && evRes.ok) {
        const evData = await evRes.json();
        setEvents(evData);
      }
      if (statusRes && statusRes.ok) {
        const statData = await statusRes.json();
        setStatusData(statData);
      }
    } catch (err) {
      console.error('Error fetching telemetry:', err);
    }
  }, []);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 3000);
    return () => clearInterval(interval);
  }, [fetchData]);

  const handleStartDetection = async (cameraId, source, sourceType) => {
    try {
      await fetch('/api/start_detection', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          camera_id: cameraId,
          source: source,
          source_type: sourceType
        })
      });
      fetchData();
    } catch (err) {
      console.error('Error starting camera stream:', err);
    }
  };

  const handleStopDetection = async (cameraId) => {
    try {
      await fetch(`/api/stop_detection?camera_id=${cameraId}`, {
        method: 'POST'
      });
      fetchData();
    } catch (err) {
      console.error('Error stopping camera stream:', err);
    }
  };

  const handleNavigateToLive = (cameraId) => {
    if (cameraId) setSelectedCameraId(cameraId);
    setActiveTab('sense');
  };

  return (
    <div className="h-screen w-screen flex flex-col overflow-hidden bg-[#0A0A0A] text-[#e5e2e1]">
      {/* Top Command Bar */}
      <Header
        statusData={statusData}
        onRefresh={fetchData}
        activeTab={activeTab}
        eventCount={events.length}
      />

      {/* Main Body */}
      <div className="flex flex-1 h-[calc(100vh-56px)] overflow-hidden">
        {/* Sidebar */}
        <Sidebar
          activeTab={activeTab}
          onSelectTab={setActiveTab}
          incidentCount={events.length}
        />

        {/* Dynamic Layer with Framer Motion AnimatePresence */}
        <main className="flex-1 h-full overflow-hidden bg-[#0A0A0A] relative">
          <AnimatePresence mode="wait">
            {activeTab === 'sense' && (
              <motion.div
                key="sense"
                variants={pageVariants}
                initial="initial"
                animate="animate"
                exit="exit"
                className="h-full w-full"
              >
                <LiveStreamGrid
                  cameras={cameras}
                  selectedCameraId={selectedCameraId}
                  onSelectCamera={setSelectedCameraId}
                  onStartDetection={handleStartDetection}
                  onStopDetection={handleStopDetection}
                />
              </motion.div>
            )}

            {activeTab === 'understand' && (
              <motion.div
                key="understand"
                variants={pageVariants}
                initial="initial"
                animate="animate"
                exit="exit"
                className="h-full w-full"
              >
                <CameraMap
                  cameras={cameras}
                  events={events}
                  selectedCameraId={selectedCameraId}
                  onSelectCamera={setSelectedCameraId}
                  onNavigateToLive={handleNavigateToLive}
                />
              </motion.div>
            )}

            {activeTab === 'identify' && (
              <motion.div
                key="identify"
                variants={pageVariants}
                initial="initial"
                animate="animate"
                exit="exit"
                className="h-full w-full"
              >
                <IdentifyConsole
                  events={events}
                  selectedCameraId={selectedCameraId}
                  onSelectCamera={setSelectedCameraId}
                  onSelectEvent={setSelectedEventForModal}
                  onNavigateToMap={() => setActiveTab('understand')}
                />
              </motion.div>
            )}

            {activeTab === 'respond' && (
              <motion.div
                key="respond"
                variants={pageVariants}
                initial="initial"
                animate="animate"
                exit="exit"
                className="h-full w-full"
              >
                <RespondConsole
                  events={events}
                  cameras={cameras}
                  onSelectEvent={setSelectedEventForModal}
                />
              </motion.div>
            )}

            {activeTab === 'connect' && (
              <motion.div
                key="connect"
                variants={pageVariants}
                initial="initial"
                animate="animate"
                exit="exit"
                className="h-full w-full"
              >
                <SystemTelemetry
                  statusData={statusData}
                  cameras={cameras}
                  events={events}
                />
              </motion.div>
            )}
          </AnimatePresence>
        </main>
      </div>

      {/* High-Resolution Verification Snapshot Lightbox Modal */}
      <AnimatePresence>
        {selectedEventForModal && (
          <SnapshotModal
            event={selectedEventForModal}
            onClose={() => setSelectedEventForModal(null)}
          />
        )}
      </AnimatePresence>
    </div>
  );
}
