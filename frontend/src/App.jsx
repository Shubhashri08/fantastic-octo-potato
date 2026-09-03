import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import Header from './components/Header';
import Sidebar from './components/Sidebar';
import LiveStreamGrid from './components/LiveStreamGrid';
import UnderstandConsole from './components/UnderstandConsole';
import IdentifyConsole from './components/IdentifyConsole';
import RespondConsole from './components/RespondConsole';
import SnapshotModal from './components/SnapshotModal';
import ErrorBoundary from './components/ErrorBoundary';
import { getCameras, startDetection, stopDetection } from './api/cameras';
import { getEvents } from './api/events';
import { getSystemStatus } from './api/status';

const pageVariants = {
  initial: { opacity: 0, y: 6, scale: 0.998 },
  animate: { opacity: 1, y: 0, scale: 1, transition: { duration: 0.18, ease: [0.22, 1, 0.36, 1] } },
  exit: { opacity: 0, y: -4, scale: 0.998, transition: { duration: 0.12, ease: 'easeIn' } }
};

const getInitialRouteState = () => {
  const path = window.location.pathname.toLowerCase();
  if (path.startsWith('/understand') || path.startsWith('/dashboard') || path.startsWith('/map') || path.startsWith('/reconstruction')) {
    return { tab: 'understand', subTab: path.includes('reconstruction') ? 'reconstruction' : 'map' };
  }
  if (path.startsWith('/identify/vehicle')) {
    return { tab: 'identify', subTab: 'vehicle' };
  }
  if (path.startsWith('/identify/person')) {
    return { tab: 'identify', subTab: 'person' };
  }
  if (path.startsWith('/identify')) {
    return { tab: 'identify', subTab: 'vehicle' };
  }
  if (path.startsWith('/respond')) {
    return { tab: 'respond', subTab: null };
  }
  return { tab: 'sense', subTab: null };
};

const DEFAULT_CAMERAS = [
  { id: 1, name: "CAM-01: Mumbai CSMT Concourse Altercation", source: "samples/fight_1.mp4", source_type: "video", lat: 18.9401, lon: 72.8351, is_active: true },
  { id: 2, name: "CAM-02: Bengaluru MG Road Commercial Corridor", source: "samples/fire_1.mp4", source_type: "video", lat: 12.9756, lon: 77.6067, is_active: true },
  { id: 3, name: "CAM-03: Mumbai Marine Drive Coastal Unit", source: "http://10.49.119.32:8080/video", source_type: "rtsp", lat: 18.9438, lon: 72.8233, is_active: true },
  { id: 4, name: "CAM-04: Bengaluru Trinity Circle Transit Node", source: "samples/fire_1.mp4", source_type: "video", lat: 12.9725, lon: 77.6200, is_active: true },
  { id: 5, name: "CAM-05: Bengaluru Outer Ring Road Hub", source: "samples/fight_1.mp4", source_type: "video", lat: 12.9820, lon: 77.6200, is_active: true },
  { id: 6, name: "CAM-06: Mumbai Worli Sea Face Intercept", source: "samples/fight_1.mp4", source_type: "video", lat: 18.9650, lon: 72.8180, is_active: true }
];

export default function App() {
  const initialRoute = getInitialRouteState();
  const [activeTab, setActiveTab] = useState(initialRoute.tab);
  const [identifySubTab, setIdentifySubTab] = useState(initialRoute.subTab || 'vehicle');
  const [understandSubTab, setUnderstandSubTab] = useState(initialRoute.subTab || 'map');
  const [cameras, setCameras] = useState(DEFAULT_CAMERAS);
  const [events, setEvents] = useState([]);
  const [statusData, setStatusData] = useState(null);
  const [selectedCameraId, setSelectedCameraId] = useState(null);
  const [selectedEventForModal, setSelectedEventForModal] = useState(null);

  // Client-side URL History Navigation
  const navigateTo = useCallback((tab, subTab = null) => {
    let path = '/surveillance';
    if (tab === 'understand') {
      const u = subTab || understandSubTab || 'map';
      path = u === 'reconstruction' ? '/understand/reconstruction' : '/dashboard';
    }
    else if (tab === 'identify') {
      const s = subTab || identifySubTab || 'vehicle';
      path = `/identify/${s}`;
    }
    else if (tab === 'respond') {
      path = '/respond';
    }

    if (window.location.pathname !== path) {
      window.history.pushState({}, '', path);
    }
    setActiveTab(tab);
    if (tab === 'identify' && subTab) setIdentifySubTab(subTab);
    if (tab === 'understand' && subTab) setUnderstandSubTab(subTab);
  }, [identifySubTab, understandSubTab]);

  useEffect(() => {
    const handlePopState = () => {
      const route = getInitialRouteState();
      setActiveTab(route.tab);
      if (route.tab === 'identify' && route.subTab) setIdentifySubTab(route.subTab);
      if (route.tab === 'understand' && route.subTab) setUnderstandSubTab(route.subTab);
    };
    window.addEventListener('popstate', handlePopState);
    return () => window.removeEventListener('popstate', handlePopState);
  }, []);

  const fetchData = useCallback(async () => {
    try {
      const [camData, evData, statData] = await Promise.all([
        getCameras().catch(() => []),
        getEvents().catch(() => []),
        getSystemStatus().catch(() => null)
      ]);

      if (Array.isArray(camData) && camData.length > 0) {
        setCameras(camData);
      }
      if (Array.isArray(evData)) setEvents(evData);
      if (statData) setStatusData(statData);
    } catch (err) {
      console.error('Error fetching telemetry:', err);
    }
  }, []);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 4000);
    return () => clearInterval(interval);
  }, [fetchData]);

  const handleStartDetection = async (cameraId, source, sourceType) => {
    try {
      await startDetection(cameraId, source, sourceType);
      fetchData();
    } catch (err) {
      console.error('Error starting camera stream:', err);
    }
  };

  const handleStopDetection = async (cameraId) => {
    try {
      await stopDetection(cameraId);
      fetchData();
    } catch (err) {
      console.error('Error stopping camera stream:', err);
    }
  };

  const handleNavigateToLive = (cameraId) => {
    if (cameraId) setSelectedCameraId(cameraId);
    navigateTo('sense');
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
        {/* Sidebar (Sense, Understand, Identify, Respond) */}
        <Sidebar
          activeTab={activeTab}
          onSelectTab={(tabId) => navigateTo(tabId)}
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
                <ErrorBoundary name="Sense Layer">
                  <LiveStreamGrid
                    cameras={cameras}
                    selectedCameraId={selectedCameraId}
                    onSelectCamera={setSelectedCameraId}
                    onStartDetection={handleStartDetection}
                    onStopDetection={handleStopDetection}
                  />
                </ErrorBoundary>
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
                <ErrorBoundary name="Understand Layer">
                  <UnderstandConsole
                    cameras={cameras}
                    events={events}
                    selectedCameraId={selectedCameraId}
                    onSelectCamera={setSelectedCameraId}
                    onNavigateToLive={handleNavigateToLive}
                    initialMode={understandSubTab}
                  />
                </ErrorBoundary>
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
                <ErrorBoundary name="Identify Layer">
                  <IdentifyConsole
                    events={events}
                    selectedCameraId={selectedCameraId}
                    onSelectCamera={setSelectedCameraId}
                    onSelectEvent={setSelectedEventForModal}
                    onNavigateToMap={() => navigateTo('understand')}
                    activeSubTab={identifySubTab}
                    onChangeSubTab={(newSubTab) => navigateTo('identify', newSubTab)}
                  />
                </ErrorBoundary>
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
                <ErrorBoundary name="Respond Layer">
                  <RespondConsole
                    events={events}
                    cameras={cameras}
                    onSelectEvent={setSelectedEventForModal}
                  />
                </ErrorBoundary>
              </motion.div>
            )}
          </AnimatePresence>

        </main>
      </div>

      {/* Lightbox Modal */}
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
