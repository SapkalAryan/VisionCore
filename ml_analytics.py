import os
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import BaggingClassifier
from sklearn.svm import SVC
from sklearn.cluster import DBSCAN, KMeans
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LinearRegression
from sklearn.metrics import (accuracy_score, silhouette_score,
                             mean_squared_error, r2_score)
import networkx as nx

OCCUPANCY_CSV = "data/occupancy_log.csv"


def load_data():
    if not os.path.exists(OCCUPANCY_CSV):
        return None

    try:
        df = pd.read_csv(OCCUPANCY_CSV)
    except Exception:
        return None

    if df.empty or len(df) < 20:
        return None

    if "timestamp" not in df.columns:
        return None

    try:
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
        df = df.dropna(subset=["timestamp"])
        df["person_count"] = pd.to_numeric(df["person_count"], errors="coerce").fillna(0)
        df["hour"] = df["timestamp"].dt.hour
        df["weekday"] = df["timestamp"].dt.weekday
        df["sin_hour"] = np.sin(2 * np.pi * df["hour"] / 24)
        df["cos_hour"] = np.cos(2 * np.pi * df["hour"] / 24)
    except Exception:
        return None

    return df


def run_bagging_classifier(df):
    X = df[["hour", "weekday", "sin_hour", "cos_hour"]].values
    y = df["occupied"].values
    if len(np.unique(y)) < 2:
        return {"error": "Need both occupied & empty samples. Keep the app running."}
    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.25, random_state=42)
    model = BaggingClassifier(n_estimators=15, random_state=42)
    model.fit(X_tr, y_tr)
    acc = accuracy_score(y_te, model.predict(X_te))
    return {"algorithm": "Bagging Classifier", "accuracy": round(acc, 4), "n_estimators": 15}


def run_svm_classifier(df):
    X = df[["hour", "weekday"]].values
    y = df["occupied"].values
    if len(np.unique(y)) < 2:
        return {"error": "Need both occupied & empty samples. Keep the app running."}
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    X_tr, X_te, y_tr, y_te = train_test_split(X_scaled, y, test_size=0.25, random_state=42)
    model = SVC(kernel="rbf", C=1.0, gamma="scale")
    model.fit(X_tr, y_tr)
    acc = accuracy_score(y_te, model.predict(X_te))
    return {"algorithm": "SVM (RBF Kernel)", "accuracy": round(acc, 4)}


def run_dbscan(df):
    X = df[["hour", "person_count"]].values
    X_scaled = StandardScaler().fit_transform(X)
    model = DBSCAN(eps=0.6, min_samples=3).fit(X_scaled)
    labels = model.labels_
    n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
    noise = list(labels).count(-1)
    result = {"algorithm": "DBSCAN", "n_clusters": n_clusters, "noise_points": noise}
    if n_clusters > 1:
        result["silhouette"] = round(silhouette_score(X_scaled, labels), 4)
    return result


def run_kmeans_graph_clustering(df):
    hourly = df.groupby("hour")["person_count"].mean().reset_index()
    X = hourly[["person_count"]].values
    if len(X) < 3:
        return {"error": "Not enough hourly data."}
    kmeans = KMeans(n_clusters=min(3, len(X)), n_init=10, random_state=42)
    labels = kmeans.fit_predict(X)

    G = nx.Graph()
    for _, row in hourly.iterrows():
        G.add_node(int(row["hour"]), occupancy=float(row["person_count"]))
    hours = hourly["hour"].tolist()
    for i in range(len(hours)):
        for j in range(i + 1, len(hours)):
            diff = abs(hours[i] - hours[j])
            if diff <= 1:
                G.add_edge(int(hours[i]), int(hours[j]), weight=1.0 / (diff + 1))
    communities = list(nx.community.greedy_modularity_communities(G))

    return {
        "algorithm": "KMeans + Graph Clustering",
        "kmeans_clusters": int(kmeans.n_clusters),
        "graph_communities": [sorted(list(c)) for c in communities],
        "hourly_occupancy": hourly.to_dict("records")
    }


def run_pca(df):
    feats = ["hour", "weekday", "person_count", "sin_hour", "cos_hour"]
    X = df[feats].values
    X_scaled = StandardScaler().fit_transform(X)
    pca = PCA(n_components=2)
    components = pca.fit_transform(X_scaled)
    return {
        "algorithm": "PCA",
        "explained_variance": [round(v, 4) for v in pca.explained_variance_ratio_],
        "sample_points": components[:50].round(3).tolist()
    }


def run_regression(df):
    X = df[["hour", "weekday", "sin_hour", "cos_hour"]].values
    y = df["person_count"].values
    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.25, random_state=42)
    model = LinearRegression()
    model.fit(X_tr, y_tr)
    pred = model.predict(X_te)
    return {
        "algorithm": "Linear Regression",
        "r2_score": round(r2_score(y_te, pred), 4),
        "rmse": round(float(np.sqrt(mean_squared_error(y_te, pred))), 4)
    }


def run_all_analytics():
    df = load_data()
    if df is None:
        return {
            "status": "insufficient_data",
            "message": "Not enough data yet. Let the app run for 2-3 minutes, or run `python seed_data.py`.",
            "bagging": {"status": "waiting"},
            "svm": {"status": "waiting"},
            "dbscan": {"status": "waiting"},
            "graph_clustering": {"status": "waiting"},
            "pca": {"status": "waiting"},
            "regression": {"status": "waiting"}
        }

    report = {"status": "ok", "rows": len(df)}
    for name, fn in [
        ("bagging", run_bagging_classifier),
        ("svm", run_svm_classifier),
        ("dbscan", run_dbscan),
        ("graph_clustering", run_kmeans_graph_clustering),
        ("pca", run_pca),
        ("regression", run_regression),
    ]:
        try:
            report[name] = fn(df)
        except Exception as e:
            report[name] = {"error": str(e)}
    return report