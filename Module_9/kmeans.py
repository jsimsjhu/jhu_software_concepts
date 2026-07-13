"""
Module 9: K-Means Clustering of Grad Café Programs

This script performs:
1. TF-IDF vectorization of program names
2. PCA dimensionality reduction
3. K-Means clustering
4. Elbow method for optimal cluster selection
5. Analysis of CS and Philosophy clusters
"""

import json
import os
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans


def load_data():
    """Load the cleaned Grad Café dataset."""
    # Try to load cleaned data first
    if os.path.exists('cleaned_gradcafe.json'):
        with open('cleaned_gradcafe.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        data_df = pd.DataFrame(data)
        print(f"✅ Loaded cleaned data: {len(data_df)} rows")
        return data_df

    # Fallback to raw data if cleaned data not found
    if os.path.exists('../Module_8/cleaned_gradcafe.json'):
        with open('../Module_8/cleaned_gradcafe.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        data_df = pd.DataFrame(data)
        print(f"✅ Loaded cleaned data from Module_8: {len(data_df)} rows")
        return data_df

    # Final fallback to applicant_data.json
    if os.path.exists('../Module_6/src/data/applicant_data.json'):
        with open('../Module_6/src/data/applicant_data.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        data_df = pd.DataFrame(data['results'])
        print(f"✅ Loaded raw data: {len(data_df)} rows")
        return data_df

    raise FileNotFoundError("No data file found!")


def clean_data(data_df):
    """Clean the program names and split university."""
    # Remove rows where program is None
    clean_df = data_df[data_df['program'].notna()].copy()
    print(f"Rows after removing None programs: {len(clean_df)}")

    # Clean program names: strip whitespace
    clean_df['program'] = clean_df['program'].str.strip()

    # Count unique programs
    n_entries = len(clean_df)
    n_unique_programs = clean_df['program'].nunique()
    print(f"Number of Entries: {n_entries:,}")
    print(f"Number of Program Input Names: {n_unique_programs:,}")

    return clean_df


def vectorize_programs(clean_df):
    """Vectorize program names using TF-IDF."""
    vectorizer = TfidfVectorizer(
        max_features=1000,
        stop_words='english',
        lowercase=True
    )

    tfidf = vectorizer.fit_transform(clean_df['program'])
    print(f"TF-IDF Matrix Shape: {tfidf.shape}")
    print(f"TF-IDF Matrix Type: {type(tfidf)}")

    return vectorizer, tfidf


def apply_pca_2d(tfidf):
    """Reduce TF-IDF matrix to 2 components for initial visualization."""
    pca = PCA(n_components=2, random_state=42)
    pca_features = pca.fit_transform(tfidf.toarray())
    print(f"✅ PCA 2D Shape: {pca_features.shape}")
    print(f"✅ PCA Configuration: {pca}")
    return pca, pca_features


def kmeans_cluster_50(pca_features):
    """Apply K-Means with 50 clusters."""
    kmeans = KMeans(n_clusters=50, max_iter=100, n_init=5, random_state=42)
    cluster_labels = kmeans.fit_predict(pca_features)
    print("✅ K-Means 50 clusters completed")
    print(f"✅ Cluster labels shape: {cluster_labels.shape}")
    return kmeans, cluster_labels


def plot_initial_clusters(pca_features, cluster_labels):
    """Plot the initial clustering with 50 clusters."""
    plt.figure(figsize=(12, 8))
    scatter = plt.scatter(
        pca_features[:, 0], pca_features[:, 1],
        c=cluster_labels, cmap='tab20', alpha=0.6, s=10
    )
    plt.title('K-Means Clustering of Grad Café Programs (50 Clusters)')
    plt.xlabel('Principal Component 1')
    plt.ylabel('Principal Component 2')
    plt.colorbar(scatter, label='Cluster')
    plt.tight_layout()
    plt.savefig('initial_cluster.png', dpi=300, bbox_inches='tight')
    print("✅ Saved initial_cluster.png")
    plt.close()


def create_clustered_dataframe(clean_df, cluster_labels):
    """Create a DataFrame with program, university, and cluster labels."""
    cluster_df = clean_df[['program', 'university']].copy()
    cluster_df['cluster'] = cluster_labels

    print("\n📊 Clustered DataFrame (first 100 rows):")
    print(cluster_df.head(100))

    return cluster_df


def save_clustered_dataframe_image(cluster_df):
    """Save a screenshot of the clustered DataFrame as an image."""
    _, ax = plt.subplots(figsize=(14, 20))
    ax.axis('tight')
    ax.axis('off')

    display_df = cluster_df.head(100)
    table = ax.table(
        cellText=display_df.values,
        colLabels=display_df.columns,
        cellLoc='left',
        loc='center'
    )
    table.auto_set_font_size(False)
    table.set_fontsize(8)
    table.scale(1, 1.5)

    plt.title('Clustered DataFrame (First 100 Rows)', fontsize=14, pad=20)
    plt.tight_layout()
    plt.savefig('clustered_dataFrame.png', dpi=300, bbox_inches='tight')
    print("✅ Saved clustered_dataFrame.png")
    plt.close()


def apply_pca_high_dim(tfidf):
    """Reduce TF-IDF matrix to 50-100 components for elbow analysis."""
    pca = PCA(n_components=50, random_state=42)
    pca_features = pca.fit_transform(tfidf.toarray())
    print(f"✅ PCA High-Dim Shape: {pca_features.shape}")
    print(f"✅ PCA Configuration: {pca}")
    return pca, pca_features


def elbow_method(pca_features, max_clusters=100):
    """Run K-Means for cluster counts 1-100 and compute inertia."""
    inertias = []
    k_range = range(1, max_clusters + 1)

    for k in k_range:
        kmeans = KMeans(n_clusters=k, max_iter=100, n_init=5, random_state=42)
        kmeans.fit(pca_features)
        inertias.append(kmeans.inertia_)
        if k % 10 == 0:
            print(f"  Processed k={k}, inertia={kmeans.inertia_:.0f}")

    return k_range, inertias


def plot_elbow(k_range, inertias):
    """Plot the elbow curve."""
    plt.figure(figsize=(12, 6))
    plt.plot(k_range, inertias, 'bo-', linewidth=2, markersize=4)
    plt.xlabel('Number of Clusters (k)')
    plt.ylabel('Inertia (Sum of Squared Distances)')
    plt.title('Elbow Method for Optimal K-Means Clustering')
    plt.grid(True, alpha=0.3)
    plt.xticks(range(0, 101, 10))
    plt.tight_layout()
    plt.savefig('elbow.png', dpi=300, bbox_inches='tight')
    print("✅ Saved elbow.png")
    plt.close()


def final_kmeans_clustering(pca_features, n_clusters=85):
    """Apply K-Means with the selected number of clusters."""
    kmeans = KMeans(n_clusters=n_clusters, max_iter=100, n_init=5, random_state=42)
    cluster_labels = kmeans.fit_predict(pca_features)
    print(f"✅ Final K-Means with {n_clusters} clusters completed")
    print(f"✅ Cluster labels shape: {cluster_labels.shape}")
    return kmeans, cluster_labels


def identify_clusters(clean_df, cluster_labels):
    """Identify CS and Philosophy clusters."""
    final_df = clean_df[['program', 'university', 'gpa', 'gre_quant',
                         'gre_verbal', 'gre_aw']].copy()
    final_df['cluster'] = cluster_labels

    # Find CS-like cluster
    cs_keywords = ['computer science', 'cs', 'computer', 'computing']
    cluster_cs_count = {}

    for cluster in final_df['cluster'].unique():
        cluster_programs = final_df[final_df['cluster'] == cluster]['program'].str.lower()
        count = sum(cluster_programs.str.contains('|'.join(cs_keywords), na=False))
        cluster_cs_count[cluster] = count

    cs_cluster = max(cluster_cs_count, key=cluster_cs_count.get)
    print(f"✅ Computer Science cluster identified: {cs_cluster}")

    # Find Philosophy-like cluster
    phil_keywords = ['philosophy', 'phil']
    cluster_phil_count = {}

    for cluster in final_df['cluster'].unique():
        cluster_programs = final_df[final_df['cluster'] == cluster]['program'].str.lower()
        count = sum(cluster_programs.str.contains('|'.join(phil_keywords), na=False))
        cluster_phil_count[cluster] = count

    phil_cluster = max(cluster_phil_count, key=cluster_phil_count.get)
    print(f"✅ Philosophy cluster identified: {phil_cluster}")

    return final_df, cs_cluster, phil_cluster


def get_cluster_data(final_df, cluster):
    """Get data for a specific cluster with numeric GRE values."""
    cluster_data = final_df[final_df['cluster'] == cluster]
    gre_values = pd.to_numeric(cluster_data['gre_quant'], errors='coerce').dropna()
    return cluster_data, gre_values


def find_alternative_cluster(final_df, keywords, skip_cluster=None):
    """Find an alternative cluster with data matching keywords."""
    best_cluster = None
    best_score = 0
    best_gre = None

    for cluster in final_df['cluster'].unique():
        if skip_cluster is not None and cluster == skip_cluster:
            continue

        cluster_data = final_df[final_df['cluster'] == cluster]
        gre_values = pd.to_numeric(cluster_data['gre_quant'], errors='coerce').dropna()

        if len(gre_values) > 0:
            cluster_programs = cluster_data['program'].str.lower()
            score = sum(cluster_programs.str.contains('|'.join(keywords), na=False))
            if score > best_score:
                best_score = score
                best_cluster = cluster
                best_gre = gre_values

    return best_cluster, best_gre


def create_box_plot(data, title, filename, ylabel='GRE Quant Score'):
    """Create and save a box plot."""
    plt.figure(figsize=(10, 6))
    plt.boxplot(data, positions=[1])
    plt.xticks([1], [title])
    plt.title(f'GRE Quant Scores - {title}')
    plt.ylabel(ylabel)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    print(f"✅ Saved {filename}")
    plt.close()


def create_placeholder_plot(title, filename):
    """Create and save a placeholder plot for missing data."""
    plt.figure(figsize=(10, 6))
    plt.text(0.5, 0.5, f'No GRE data found for {title}',
             ha='center', va='center', fontsize=14,
             transform=plt.gca().transAxes)
    plt.title(f'GRE Quant Scores - {title} (No Data)')
    plt.ylabel('GRE Quant Score')
    plt.tight_layout()
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    print(f"✅ Saved {filename} (placeholder)")
    plt.close()


def plot_gre_boxplots(final_df, cs_cluster, phil_cluster):
    """Create box plots for CS and Philosophy clusters."""
    # Get CS cluster data
    cs_data, cs_gre = get_cluster_data(final_df, cs_cluster)
    print(f"CS cluster: {cs_cluster}, rows: {len(cs_data)}, "
          f"GRE non-null: {len(cs_gre)}")

    # Get Philosophy cluster data
    phil_data, phil_gre = get_cluster_data(final_df, phil_cluster)
    print(f"Phil cluster: {phil_cluster}, rows: {len(phil_data)}, "
          f"GRE non-null: {len(phil_gre)}")

    # If CS cluster has no data, find alternative
    if len(cs_gre) == 0:
        print("⚠️ Computer Science cluster has no GRE data! Searching...")
        cs_keywords = ['computer science', 'cs', 'computer', 'computing']
        alt_cluster, alt_gre = find_alternative_cluster(
            final_df, cs_keywords, skip_cluster=cs_cluster
        )
        if alt_cluster is not None:
            cs_cluster = alt_cluster
            cs_gre = alt_gre
            print(f"✅ Using alternative CS cluster: {cs_cluster} "
                  f"with {len(cs_gre)} GRE values")

    # If Philosophy cluster has no data, find alternative
    if len(phil_gre) == 0:
        print("⚠️ Philosophy cluster has no GRE data! Searching...")
        phil_keywords = ['philosophy', 'phil']
        alt_cluster, alt_gre = find_alternative_cluster(
            final_df, phil_keywords, skip_cluster=phil_cluster
        )
        if alt_cluster is not None:
            phil_cluster = alt_cluster
            phil_gre = alt_gre
            print(f"✅ Using alternative Philosophy cluster: {phil_cluster} "
                  f"with {len(phil_gre)} GRE values")

    # Handle missing data with placeholders
    if len(cs_gre) == 0 or len(phil_gre) == 0:
        print("⚠️ No GRE data found for one or both clusters.")
        if len(cs_gre) == 0:
            create_placeholder_plot('Computer Science Cluster',
                                    'computer_science.png')
        else:
            create_box_plot(cs_gre, 'Computer Science Cluster',
                            'computer_science.png')

        if len(phil_gre) == 0:
            create_placeholder_plot('Philosophy Cluster',
                                    'philosophy.png')
        else:
            create_box_plot(phil_gre, 'Philosophy Cluster',
                            'philosophy.png')
        return

    # Create CS Box Plot
    create_box_plot(cs_gre, 'Computer Science Cluster', 'computer_science.png')

    # Create Philosophy Box Plot
    create_box_plot(phil_gre, 'Philosophy Cluster', 'philosophy.png')

    # Print summary statistics
    print("\n📊 GRE Quant Summary Statistics:")
    print(f"Computer Science Cluster: n={len(cs_gre)}, "
          f"mean={cs_gre.mean():.2f}, std={cs_gre.std():.2f}")
    print(f"Philosophy Cluster: n={len(phil_gre)}, "
          f"mean={phil_gre.mean():.2f}, std={phil_gre.std():.2f}")

    # Compare clusters
    if cs_gre.mean() > phil_gre.mean() * 1.5:
        print("\n⚠️ CS GRE scores appear suspiciously high compared to Philosophy.")
        print("   This may indicate data quality issues or misclustering.")
    else:
        print("\n✅ GRE scores appear reasonable between clusters.")


def analyze_clusters(final_df, cs_cluster, phil_cluster):
    """Print summary of cluster contents."""
    print("\n" + "=" * 50)
    print("FINAL CLUSTER ANALYSIS")
    print("=" * 50)

    # CS cluster programs
    cs_programs = final_df[final_df['cluster'] == cs_cluster]['program'].value_counts().head(10)
    print(f"\n🔬 Top 10 programs in Computer Science Cluster ({cs_cluster}):")
    print(cs_programs)

    # Philosophy cluster programs
    phil_programs = final_df[final_df['cluster'] == phil_cluster]['program'].value_counts().head(10)
    print(f"\n📚 Top 10 programs in Philosophy Cluster ({phil_cluster}):")
    print(phil_programs)


def main():
    """Main execution function."""
    # Load and clean data
    data_df = load_data()
    clean_df = clean_data(data_df)

    # Vectorize
    _, tfidf = vectorize_programs(clean_df)

    # ===== PART 1: Initial Clustering (50 clusters) =====
    print("\n" + "=" * 50)
    print("PART 1: Initial Clustering with 50 Clusters")
    print("=" * 50)

    _, pca_features_2d = apply_pca_2d(tfidf)
    _, labels_50 = kmeans_cluster_50(pca_features_2d)
    plot_initial_clusters(pca_features_2d, labels_50)

    cluster_df = create_clustered_dataframe(clean_df, labels_50)
    save_clustered_dataframe_image(cluster_df)

    # ===== PART 2: Elbow Method =====
    print("\n" + "=" * 50)
    print("PART 2: Elbow Method for Optimal Cluster Selection")
    print("=" * 50)

    _, pca_features_high = apply_pca_high_dim(tfidf)
    k_range, inertias = elbow_method(pca_features_high)
    plot_elbow(k_range, inertias)

    # ===== PART 3: Final Clustering and Analysis =====
    print("\n" + "=" * 50)
    print("PART 3: Final Clustering and Analysis")
    print("=" * 50)

    # Use 85 clusters based on elbow analysis
    _, labels_final = final_kmeans_clustering(pca_features_high, n_clusters=85)

    # Identify CS and Philosophy clusters
    final_df, cs_cluster, phil_cluster = identify_clusters(clean_df, labels_final)

    # Create box plots
    plot_gre_boxplots(final_df, cs_cluster, phil_cluster)

    # Analyze clusters
    analyze_clusters(final_df, cs_cluster, phil_cluster)

    print("\n✅ All visualizations complete!")
    print("   - initial_cluster.png")
    print("   - clustered_dataFrame.png")
    print("   - elbow.png")
    print("   - computer_science.png")
    print("   - philosophy.png")


if __name__ == "__main__":
    main()
