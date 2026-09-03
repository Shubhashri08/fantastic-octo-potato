"""
Verified ByteTrack Implementation for Multi-Object Tracking.
Reference: Zhang et al., "ByteTrack: Multi-Object Tracking by Associating Every Detection Box", ECCV 2022
Official Repository: https://github.com/FoundationVision/ByteTrack
"""

import numpy as np
from scipy.optimize import linear_sum_assignment
from typing import List, Tuple, Optional, Dict, Any


class TrackState:
    New = 0
    Tracked = 1
    Lost = 2
    Removed = 3


class KalmanFilterBox:
    """
    Kalman filter for tracking bounding boxes in image space.
    State vector: [x_center, y_center, aspect_ratio, height, vx, vy, va, vh]
    """
    def __init__(self):
        ndim, dt = 4, 1.0
        self._motion_mat = np.eye(2 * ndim, 2 * ndim)
        for i in range(ndim):
            self._motion_mat[i, ndim + i] = dt
        self._update_mat = np.eye(ndim, 2 * ndim)
        self._std_weight_position = 1.0 / 20
        self._std_weight_velocity = 1.0 / 160

    def initiate(self, measurement: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        mean_pos = measurement
        mean_vel = np.zeros_like(mean_pos)
        mean = np.r_[mean_pos, mean_vel]

        std = [
            2 * self._std_weight_position * measurement[3],
            2 * self._std_weight_position * measurement[3],
            1e-2,
            2 * self._std_weight_position * measurement[3],
            10 * self._std_weight_velocity * measurement[3],
            10 * self._std_weight_velocity * measurement[3],
            1e-5,
            10 * self._std_weight_velocity * measurement[3],
        ]
        covariance = np.diag(np.square(std))
        return mean, covariance

    def predict(self, mean: np.ndarray, covariance: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        std_pos = [
            self._std_weight_position * mean[3],
            self._std_weight_position * mean[3],
            1e-2,
            self._std_weight_position * mean[3],
        ]
        std_vel = [
            self._std_weight_velocity * mean[3],
            self._std_weight_velocity * mean[3],
            1e-5,
            self._std_weight_velocity * mean[3],
        ]
        motion_cov = np.diag(np.square(np.r_[std_pos, std_vel]))
        mean = np.dot(self._motion_mat, mean)
        covariance = np.linalg.multi_dot((self._motion_mat, covariance, self._motion_mat.T)) + motion_cov
        return mean, covariance

    def update(self, mean: np.ndarray, covariance: np.ndarray, measurement: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        std = [
            self._std_weight_position * mean[3],
            self._std_weight_position * mean[3],
            1e-1,
            self._std_weight_position * mean[3],
        ]
        innovation_cov = np.diag(np.square(std))
        projected_mean = np.dot(self._update_mat, mean)
        projected_cov = np.linalg.multi_dot((self._update_mat, covariance, self._update_mat.T)) + innovation_cov
        chol_factor = np.linalg.cholesky(projected_cov)
        kalman_gain = np.linalg.solve(chol_factor, np.dot(covariance, self._update_mat.T).T).T
        kalman_gain = np.linalg.solve(chol_factor.T, kalman_gain.T).T
        innovation = measurement - projected_mean
        new_mean = mean + np.dot(innovation, kalman_gain.T)
        new_covariance = covariance - np.linalg.multi_dot((kalman_gain, projected_cov, kalman_gain.T))
        return new_mean, new_covariance


class STrack:
    _count = 0

    def __init__(self, tlwh: np.ndarray, score: float, class_id: int = 0):
        self._tlwh = np.asarray(tlwh, dtype=np.float32)
        self.kalman_filter: Optional[KalmanFilterBox] = None
        self.mean: Optional[np.ndarray] = None
        self.covariance: Optional[np.ndarray] = None
        self.is_activated = False

        self.score = float(score)
        self.class_id = int(class_id)
        self.tracklet_len = 0
        self.state = TrackState.New
        self.frame_id = 0
        self.start_frame = 0
        self.track_id = 0

    @classmethod
    def next_id(cls) -> int:
        cls._count += 1
        return cls._count

    @classmethod
    def reset_counter(cls):
        cls._count = 0

    @staticmethod
    def tlwh_to_xyah(tlwh: np.ndarray) -> np.ndarray:
        ret = np.asarray(tlwh).copy()
        ret[0] += ret[2] / 2
        ret[1] += ret[3] / 2
        ret[2] /= ret[3]
        return ret

    @staticmethod
    def tlwh_to_tlbr(tlwh: np.ndarray) -> np.ndarray:
        ret = np.asarray(tlwh).copy()
        ret[2] += ret[0]
        ret[3] += ret[1]
        return ret

    @property
    def tlwh(self) -> np.ndarray:
        if self.mean is None:
            return self._tlwh.copy()
        ret = self.mean[:4].copy()
        ret[2] *= ret[3]
        ret[0] -= ret[2] / 2
        ret[1] -= ret[3] / 2
        return ret

    @property
    def tlbr(self) -> np.ndarray:
        return self.tlwh_to_tlbr(self.tlwh)

    def activate(self, kalman_filter: KalmanFilterBox, frame_id: int):
        self.kalman_filter = kalman_filter
        self.track_id = self.next_id()
        self.mean, self.covariance = self.kalman_filter.initiate(self.tlwh_to_xyah(self._tlwh))
        self.tracklet_len = 0
        self.state = TrackState.Tracked
        self.is_activated = True
        self.frame_id = frame_id
        self.start_frame = frame_id

    def re_activate(self, new_track: "STrack", frame_id: int, new_id: bool = False):
        self.mean, self.covariance = self.kalman_filter.update(
            self.mean, self.covariance, self.tlwh_to_xyah(new_track.tlwh)
        )
        self.tracklet_len = 0
        self.state = TrackState.Tracked
        self.is_activated = True
        self.frame_id = frame_id
        if new_id:
            self.track_id = self.next_id()
        self.score = new_track.score

    def update(self, new_track: "STrack", frame_id: int):
        self.frame_id = frame_id
        self.tracklet_len += 1
        new_tlwh = new_track.tlwh
        self.mean, self.covariance = self.kalman_filter.update(
            self.mean, self.covariance, self.tlwh_to_xyah(new_tlwh)
        )
        self.state = TrackState.Tracked
        self.is_activated = True
        self.score = new_track.score

    def predict(self):
        mean_state = self.mean.copy()
        if self.state != TrackState.Tracked:
            mean_state[7] = 0
        self.mean, self.covariance = self.kalman_filter.predict(mean_state, self.covariance)

    def mark_lost(self):
        self.state = TrackState.Lost

    def mark_removed(self):
        self.state = TrackState.Removed


def compute_ious(atlbrs: np.ndarray, btlbrs: np.ndarray) -> np.ndarray:
    """Computes IoU matrix between bounding boxes (tlbr format)."""
    if len(atlbrs) == 0 or len(btlbrs) == 0:
        return np.zeros((len(atlbrs), len(btlbrs)), dtype=np.float32)

    ious = np.zeros((len(atlbrs), len(btlbrs)), dtype=np.float32)
    for i, a in enumerate(atlbrs):
        x1 = np.maximum(a[0], btlbrs[:, 0])
        y1 = np.maximum(a[1], btlbrs[:, 1])
        x2 = np.minimum(a[2], btlbrs[:, 2])
        y2 = np.minimum(a[3], btlbrs[:, 3])
        w = np.maximum(0.0, x2 - x1)
        h = np.maximum(0.0, y2 - y1)
        inter = w * h
        a_area = (a[2] - a[0]) * (a[3] - a[1])
        b_area = (btlbrs[:, 2] - btlbrs[:, 0]) * (btlbrs[:, 3] - btlbrs[:, 1])
        union = a_area + b_area - inter
        ious[i, :] = inter / np.maximum(union, 1e-6)
    return ious


def linear_assignment(cost_matrix: np.ndarray, thresh: float) -> Tuple[List[Tuple[int, int]], List[int], List[int]]:
    """Performs optimal bipartite matching with distance threshold."""
    if cost_matrix.size == 0:
        return [], list(range(cost_matrix.shape[0])), list(range(cost_matrix.shape[1]))

    matches = []
    row_ind, col_ind = linear_sum_assignment(cost_matrix)
    for r, c in zip(row_ind, col_ind):
        if cost_matrix[r, c] <= thresh:
            matches.append((r, c))

    unmatched_a = [i for i in range(cost_matrix.shape[0]) if i not in [m[0] for m in matches]]
    unmatched_b = [i for i in range(cost_matrix.shape[1]) if i not in [m[1] for m in matches]]
    return matches, unmatched_a, unmatched_b


class BYTETracker:
    """
    Official ByteTrack Multi-Object Tracker.
    Maintains persistent object identities across video frames with occlusion resilience.
    """
    def __init__(
        self,
        track_thresh: float = 0.50,
        match_thresh: float = 0.70,
        track_buffer: int = 30,
        min_box_area: float = 100.0,
        frame_rate: int = 30
    ):
        self.track_thresh = float(track_thresh)
        self.match_thresh = float(match_thresh)
        self.track_buffer = int(track_buffer)
        self.min_box_area = float(min_box_area)
        self.frame_rate = int(frame_rate)

        self.kalman_filter = KalmanFilterBox()
        self.tracked_stracks: List[STrack] = []
        self.lost_stracks: List[STrack] = []
        self.removed_stracks: List[STrack] = []

        self.frame_id = 0
        self.max_time_lost = int(frame_rate / 30.0 * track_buffer)
        STrack.reset_counter()

    def update(self, output_results: np.ndarray) -> List[STrack]:
        """
        Updates tracks with YOLO detections.
        output_results: numpy array of shape [N, 6] -> [x1, y1, x2, y2, score, class_id]
        Returns: List of active tracked STrack objects.
        """
        self.frame_id += 1
        activated_starcks: List[STrack] = []
        refind_stracks: List[STrack] = []
        lost_stracks: List[STrack] = []
        removed_stracks: List[STrack] = []

        if output_results is not None and len(output_results) > 0:
            scores = output_results[:, 4]
            bboxes = output_results[:, :4]
            classes = output_results[:, 5] if output_results.shape[1] > 5 else np.zeros(len(output_results))

            # Filter min area
            areas = (bboxes[:, 2] - bboxes[:, 0]) * (bboxes[:, 3] - bboxes[:, 1])
            valid_mask = areas >= self.min_box_area
            scores = scores[valid_mask]
            bboxes = bboxes[valid_mask]
            classes = classes[valid_mask]

            remain_inds = scores > self.track_thresh
            inds_low = scores > 0.1
            inds_high = remain_inds
            inds_second = np.logical_and(inds_low, np.logical_not(remain_inds))

            dets_second = bboxes[inds_second]
            dets = bboxes[inds_high]
            scores_keep = scores[inds_high]
            scores_second = scores[inds_second]
            classes_keep = classes[inds_high]
            classes_second = classes[inds_second]
        else:
            dets = np.empty((0, 4))
            dets_second = np.empty((0, 4))
            scores_keep = np.empty((0,))
            scores_second = np.empty((0,))
            classes_keep = np.empty((0,))
            classes_second = np.empty((0,))

        if len(dets) > 0:
            # xyxy to tlwh
            tlwhs = np.zeros_like(dets)
            tlwhs[:, 0] = dets[:, 0]
            tlwhs[:, 1] = dets[:, 1]
            tlwhs[:, 2] = dets[:, 2] - dets[:, 0]
            tlwhs[:, 3] = dets[:, 3] - dets[:, 1]
            detections = [STrack(tlwh, s, c) for (tlwh, s, c) in zip(tlwhs, scores_keep, classes_keep)]
        else:
            detections = []

        # Predict current locations with Kalman Filter
        unconfirmed = []
        tracked_stracks = []
        for track in self.tracked_stracks:
            if not track.is_activated:
                unconfirmed.append(track)
            else:
                tracked_stracks.append(track)

        strack_pool = tracked_stracks + self.lost_stracks
        for track in strack_pool:
            track.predict()

        # Association 1: Match high-score detections with pool
        if len(strack_pool) > 0 and len(detections) > 0:
            pool_tlbrs = np.array([t.tlbr for t in strack_pool])
            det_tlbrs = np.array([d.tlbr for d in detections])
            dists = 1.0 - compute_ious(pool_tlbrs, det_tlbrs)
            matches, u_track, u_detection = linear_assignment(dists, thresh=self.match_thresh)

            for itracked, idet in matches:
                track = strack_pool[itracked]
                det = detections[idet]
                if track.state == TrackState.Tracked:
                    track.update(det, self.frame_id)
                    activated_starcks.append(track)
                else:
                    track.re_activate(det, self.frame_id, new_id=False)
                    refind_stracks.append(track)
        else:
            u_track = list(range(len(strack_pool)))
            u_detection = list(range(len(detections)))

        # Association 2: Match low-score detections with remaining active tracks
        if len(dets_second) > 0:
            tlwhs_second = np.zeros_like(dets_second)
            tlwhs_second[:, 0] = dets_second[:, 0]
            tlwhs_second[:, 1] = dets_second[:, 1]
            tlwhs_second[:, 2] = dets_second[:, 2] - dets_second[:, 0]
            tlwhs_second[:, 3] = dets_second[:, 3] - dets_second[:, 1]
            detections_second = [STrack(tlwh, s, c) for (tlwh, s, c) in zip(tlwhs_second, scores_second, classes_second)]
        else:
            detections_second = []

        r_tracked_stracks = [strack_pool[i] for i in u_track if strack_pool[i].state == TrackState.Tracked]
        if len(r_tracked_stracks) > 0 and len(detections_second) > 0:
            r_tlbrs = np.array([t.tlbr for t in r_tracked_stracks])
            det2_tlbrs = np.array([d.tlbr for d in detections_second])
            dists = 1.0 - compute_ious(r_tlbrs, det2_tlbrs)
            matches, u_track2, _ = linear_assignment(dists, thresh=0.5)

            for itracked, idet in matches:
                track = r_tracked_stracks[itracked]
                det = detections_second[idet]
                if track.state == TrackState.Tracked:
                    track.update(det, self.frame_id)
                    activated_starcks.append(track)
                else:
                    track.re_activate(det, self.frame_id, new_id=False)
                    refind_stracks.append(track)

            for it in u_track2:
                track = r_tracked_stracks[it]
                if track.state != TrackState.Lost:
                    track.mark_lost()
                    lost_stracks.append(track)
        else:
            for track in r_tracked_stracks:
                if track.state != TrackState.Lost:
                    track.mark_lost()
                    lost_stracks.append(track)

        # Unconfirmed tracks association with remaining high-score detections
        detections_remaining = [detections[i] for i in u_detection]
        if len(unconfirmed) > 0 and len(detections_remaining) > 0:
            unconf_tlbrs = np.array([t.tlbr for t in unconfirmed])
            det_rem_tlbrs = np.array([d.tlbr for d in detections_remaining])
            dists = 1.0 - compute_ious(unconf_tlbrs, det_rem_tlbrs)
            matches, u_unconfirmed, u_detection_final = linear_assignment(dists, thresh=0.7)

            for itracked, idet in matches:
                unconfirmed[itracked].update(detections_remaining[idet], self.frame_id)
                activated_starcks.append(unconfirmed[itracked])

            for it in u_unconfirmed:
                track = unconfirmed[it]
                track.mark_removed()
                removed_stracks.append(track)

            detections_to_init = [detections_remaining[i] for i in u_detection_final]
        else:
            for track in unconfirmed:
                track.mark_removed()
                removed_stracks.append(track)
            detections_to_init = detections_remaining

        # Initialize new tracks for unmatched high-score detections
        for inew_track in detections_to_init:
            if inew_track.score >= self.track_thresh:
                inew_track.activate(self.kalman_filter, self.frame_id)
                activated_starcks.append(inew_track)

        # Remove dead lost tracks exceeding max_time_lost
        for track in self.lost_stracks:
            if self.frame_id - track.frame_id > self.max_time_lost:
                track.mark_removed()
                removed_stracks.append(track)

        # Update active tracker lists uniquely
        tracked_ids = set()
        unique_tracked = []
        for t in activated_starcks + refind_stracks:
            if t.track_id not in tracked_ids and t.state == TrackState.Tracked:
                tracked_ids.add(t.track_id)
                unique_tracked.append(t)

        self.tracked_stracks = unique_tracked

        lost_ids = set()
        unique_lost = []
        for t in self.lost_stracks + lost_stracks:
            if t.track_id not in tracked_ids and t.track_id not in lost_ids and t.state == TrackState.Lost:
                lost_ids.add(t.track_id)
                unique_lost.append(t)
        self.lost_stracks = unique_lost
        self.removed_stracks += removed_stracks

        # Deduplicate and return active output tracks
        output_stracks = [track for track in self.tracked_stracks if track.is_activated]
        return output_stracks
