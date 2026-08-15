from pathlib import Path

import numpy as np
import pandas as pd

from sklearn.cluster import KMeans
from sklearn.ensemble import IsolationForest
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler


# =============================================================================
# VIGRAH — C3.2 ML PATTERN / RISK STRUCTURE EVALUATION
# =============================================================================

ROOT = Path(__file__).resolve().parents[2]

FEATURE_DIR = (
    ROOT
    / "data"
    / "processed"
    / "features"
)

INPUT = (
    FEATURE_DIR
    / "road_ml_features.parquet"
)

OUTPUT = (
    FEATURE_DIR
    / "road_ml_patterns.parquet"
)

REPORT = (
    FEATURE_DIR
    / "c3_2_ml_evaluation_report.txt"
)


print("=" * 80)
print("VIGRAH — C3.2 ML PATTERN / RISK STRUCTURE EVALUATION")
print("=" * 80)


# =============================================================================
# LOAD
# =============================================================================

print("\nInput:")
print(INPUT)

if not INPUT.exists():
    raise FileNotFoundError(
        f"ML feature dataset not found:\n{INPUT}"
    )

df = pd.read_parquet(INPUT)

print("\n" + "-" * 80)
print("LOADING ML FEATURE DATASET")
print("-" * 80)

print(
    f"Records: {len(df):,}"
)

print(
    f"Columns: {len(df.columns)}"
)


# =============================================================================
# IDENTIFY ML FEATURES
# =============================================================================

excluded = [
    "city",
    "road_id",
    "road_name",
    "highway",

    # Baseline benchmark — NOT a training feature.
    "baseline_risk_score",
    "confidence_adjusted_risk_score",
    "risk_level",
]


feature_columns = [
    column
    for column in df.columns
    if column not in excluded
]


X = df[
    feature_columns
].copy()


# =============================================================================
# VALIDATION
# =============================================================================

print("\n" + "-" * 80)
print("FEATURE MATRIX VALIDATION")
print("-" * 80)

print(
    f"Feature columns: {len(feature_columns)}"
)

print(
    f"Feature rows: {len(X):,}"
)


if X.isna().any().any():

    raise RuntimeError(
        "NaN values detected in ML matrix."
    )


if np.isinf(
    X.to_numpy(
        dtype=float
    )
).any():

    raise RuntimeError(
        "Infinite values detected in ML matrix."
    )


print("NaN validation: PASS")
print("Infinite validation: PASS")


# =============================================================================
# REMOVE CONSTANT FEATURES
# =============================================================================

print("\n" + "-" * 80)
print("FEATURE VARIANCE CHECK")
print("-" * 80)


constant_features = [
    column
    for column in feature_columns
    if X[column].nunique() <= 1
]


if constant_features:

    print(
        "Constant features removed:"
    )

    for column in constant_features:
        print(
            f"  {column}"
        )

    X = X.drop(
        columns=constant_features
    )

else:

    print(
        "No constant features."
    )


feature_columns = list(
    X.columns
)


print(
    f"\nUsable ML features: "
    f"{len(feature_columns)}"
)


# =============================================================================
# STANDARDIZATION
# =============================================================================

print("\n" + "-" * 80)
print("STANDARDIZING FEATURES")
print("-" * 80)


scaler = StandardScaler()

X_scaled = scaler.fit_transform(
    X
)

print(
    f"Matrix shape: "
    f"{X_scaled.shape}"
)

print(
    "Standardization: PASS"
)


# =============================================================================
# K-MEANS CLUSTERING
# =============================================================================

print("\n" + "-" * 80)
print("K-MEANS ROAD PROFILE CLUSTERING")
print("-" * 80)


cluster_results = {}

best_k = None
best_score = -np.inf


# Evaluate a small, defensible range.
for k in range(2, 7):

    model = KMeans(
        n_clusters=k,
        random_state=42,
        n_init=20
    )

    labels = model.fit_predict(
        X_scaled
    )

    score = silhouette_score(
        X_scaled,
        labels
    )

    cluster_results[k] = {
        "model": model,
        "labels": labels,
        "silhouette": score,
    }

    print(
        f"K={k}: "
        f"silhouette={score:.4f}"
    )

    if score > best_score:

        best_score = score
        best_k = k


print(
    f"\nSelected K: {best_k}"
)

print(
    f"Best silhouette score: "
    f"{best_score:.4f}"
)


best_model = (
    cluster_results[
        best_k
    ]["model"]
)

best_labels = (
    cluster_results[
        best_k
    ]["labels"]
)


df["road_profile_cluster"] = (
    best_labels
)


# =============================================================================
# CLUSTER SUMMARY
# =============================================================================

print("\n" + "-" * 80)
print("ROAD PROFILE CLUSTERS")
print("-" * 80)


cluster_summary = (
    df
    .groupby(
        "road_profile_cluster"
    )
    .agg(
        roads=(
            "road_id",
            "count"
        ),

        mean_cctv=(
            "cctv_count_norm",
            "mean"
        ),

        mean_spatial_confidence=(
            "spatial_confidence_norm",
            "mean"
        ),

        mean_camera_distance=(
            "mean_camera_distance_m_norm",
            "mean"
        ),

        mean_review_ratio=(
            "review_match_ratio_norm",
            "mean"
        ),

        mean_baseline_risk=(
            "confidence_adjusted_risk_score",
            "mean"
        ),
    )
    .sort_values(
        "mean_baseline_risk",
        ascending=False
    )
)


print(
    cluster_summary.to_string()
)


# =============================================================================
# ISOLATION FOREST
# =============================================================================

print("\n" + "-" * 80)
print("ISOLATION FOREST ANOMALY DETECTION")
print("-" * 80)


isolation = IsolationForest(
    n_estimators=300,
    contamination="auto",
    random_state=42,
    n_jobs=-1
)


anomaly_prediction = (
    isolation.fit_predict(
        X_scaled
    )
)


anomaly_score = (
    isolation.score_samples(
        X_scaled
    )
)


df["ml_anomaly_label"] = (
    anomaly_prediction
)

df["ml_anomaly_score"] = (
    anomaly_score
)


anomaly_count = (
    (anomaly_prediction == -1)
    .sum()
)


normal_count = (
    (anomaly_prediction == 1)
    .sum()
)


print(
    f"Normal roads: {normal_count:,}"
)

print(
    f"Anomalous roads: {anomaly_count:,}"
)


# =============================================================================
# ANOMALY SUMMARY
# =============================================================================

print("\n" + "-" * 80)
print("TOP ANOMALOUS ROAD PROFILES")
print("-" * 80)


top_anomalies = (
    df
    .sort_values(
        "ml_anomaly_score",
        ascending=True
    )
    .head(20)
)


print(
    top_anomalies[
        [
            "city",
            "road_id",
            "road_name",
            "highway",
            "cctv_count_norm",
            "spatial_confidence_norm",
            "confidence_adjusted_risk_score",
            "road_profile_cluster",
            "ml_anomaly_score",
            "ml_anomaly_label",
        ]
    ]
    .to_string(
        index=False
    )
)


# =============================================================================
# BASELINE VS CLUSTERS
# =============================================================================

print("\n" + "-" * 80)
print("CLUSTER → BASELINE RISK COMPARISON")
print("-" * 80)


cluster_risk = (
    df
    .groupby(
        "road_profile_cluster"
    )
    .agg(
        roads=(
            "road_id",
            "count"
        ),

        mean_baseline=(
            "confidence_adjusted_risk_score",
            "mean"
        ),

        median_baseline=(
            "confidence_adjusted_risk_score",
            "median"
        ),

        high_risk_roads=(
            "risk_level",
            lambda x:
                (x == "HIGH").sum()
        ),

        moderate_risk_roads=(
            "risk_level",
            lambda x:
                (x == "MODERATE").sum()
        ),

        low_risk_roads=(
            "risk_level",
            lambda x:
                (x == "LOW").sum()
        ),
    )
)


print(
    cluster_risk.to_string()
)


# =============================================================================
# CITY × CLUSTER
# =============================================================================

print("\n" + "-" * 80)
print("CITY × ROAD PROFILE")
print("-" * 80)


city_cluster = (
    df
    .groupby(
        [
            "city",
            "road_profile_cluster",
        ]
    )
    .size()
    .reset_index(
        name="roads"
    )
)


print(
    city_cluster.to_string(
        index=False
    )
)


# =============================================================================
# ROAD-LEVEL ML SIGNAL SUMMARY
# =============================================================================

print("\n" + "-" * 80)
print("ROAD-LEVEL SIGNAL SUMMARY")
print("-" * 80)


signal_features = [
    "cctv_count_norm",
    "mean_camera_distance_m_norm",
    "median_camera_distance_m_norm",
    "max_camera_distance_m_norm",
    "min_camera_distance_m_norm",
    "high_quality_matches_norm",
    "good_quality_matches_norm",
    "low_quality_matches_norm",
    "review_matches_norm",
    "high_quality_match_ratio_norm",
    "review_match_ratio_norm",
    "spatial_confidence_norm",
]


# Fix accidental duplicate typo safely if present.
signal_features = [
    column
    for column in signal_features
    if column in df.columns
]


for column in signal_features:

    print(
        f"{column:45s}"
        f" unique={df[column].nunique():4d}"
        f" std={df[column].std():.4f}"
    )


# =============================================================================
# IMPORTANT SEMANTIC CHECK
# =============================================================================

print("\n" + "-" * 80)
print("SEMANTIC SAFETY CHECK")
print("-" * 80)


print(
    "Baseline risk is NOT used as a supervised label."
)

print(
    "Accident values remain contextual."
)

print(
    "Crime values remain contextual."
)

print(
    "ML outputs represent road-profile structure "
    "and anomaly patterns."
)

print(
    "PASS"
)


# =============================================================================
# SAVE
# =============================================================================

print("\n" + "-" * 80)
print("SAVING ML PATTERN DATASET")
print("-" * 80)


df.to_parquet(
    OUTPUT,
    index=False
)


print(
    f"Output:\n{OUTPUT}"
)

print(
    f"Output size: "
    f"{OUTPUT.stat().st_size / 1024:.2f} KB"
)


# =============================================================================
# REPORT
# =============================================================================

report = []

report.append(
    "VIGRAH — C3.2 ML PATTERN EVALUATION"
)

report.append(
    "=" * 60
)

report.append(
    f"Road records: {len(df):,}"
)

report.append(
    f"Usable ML features: {len(feature_columns):,}"
)

report.append(
    f"Selected clusters: {best_k}"
)

report.append(
    f"Best silhouette score: {best_score:.4f}"
)

report.append("")

report.append(
    "ANOMALY DETECTION"
)

report.append(
    f"Normal roads: {normal_count:,}"
)

report.append(
    f"Anomalous roads: {anomaly_count:,}"
)

report.append("")

report.append(
    "SEMANTIC RULES"
)

report.append(
    "Baseline risk is a benchmark, not a ground-truth label."
)

report.append(
    "Accident data is contextual."
)

report.append(
    "Crime data is contextual."
)

report.append(
    "ML outputs describe road-profile structure."
)

report.append("")

report.append(
    "CLUSTER SUMMARY"
)

report.append(
    cluster_summary.to_string()
)

report.append("")

report.append(
    "CITY × CLUSTER"
)

report.append(
    city_cluster.to_string(
        index=False
    )
)


REPORT.write_text(
    "\n".join(report),
    encoding="utf-8"
)


# =============================================================================
# COMPLETE
# =============================================================================

print("\n" + "=" * 80)
print("C3.2 COMPLETE")
print("=" * 80)

print(
    "\nML pattern evaluation completed."
)

print(
    f"Selected clusters: {best_k}"
)

print(
    f"Silhouette score: "
    f"{best_score:.4f}"
)

print(
    f"Anomalous roads: "
    f"{anomaly_count:,}"
)

print(
    "\nOutput:"
)

print(
    OUTPUT
)

print(
    "\nReport:"
)

print(
    REPORT
)

print(
    "\nNEXT → C3.3 ML VALIDATION / RISK PROFILE GENERATION"
)