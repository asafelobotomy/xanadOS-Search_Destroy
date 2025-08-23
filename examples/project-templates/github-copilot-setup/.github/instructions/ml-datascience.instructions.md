---
applyTo: "**/ml/**/*.{py,ipynb,r,scala,jl}"
priority: 90
category: "domain-specific"
---

# ML/Data Science-specific Copilot Instructions

## Data Pipeline Standards

- Use reproducible environments with pinned dependencies (requirements.txt, conda.yml, poetry.lock)
- Implement data validation with Great Expectations or Pandera for schema enforcement
- Use DVC or similar for data versioning; track dataset lineage and transformations
- Implement data quality gates in pipelines (completeness, consistency, accuracy checks)
- Use Apache Airflow or Kubeflow for orchestrating complex data workflows
- Implement data cataloging with metadata for discoverability and governance
- Use partitioning and indexing strategies for large datasets (Parquet, Delta Lake)

## Model Training Standards

- Set random seeds for all stochastic operations (numpy, torch, tensorflow, sklearn, random)
- Use stratified sampling for imbalanced datasets; document class distributions
- Implement proper train/validation/test splits with temporal considerations for time series
- Use cross-validation with appropriate strategies (k-fold, time series split, group k-fold)
- Log all experiments with MLflow, Weights & Biases, or Neptune for reproducibility
- Implement early stopping and model checkpointing to prevent overfitting
- Use automated hyperparameter tuning (Optuna, Ray Tune, Hyperopt) with budget constraints
- Profile GPU/TPU usage and optimize batch sizes for memory efficiency

## Model Evaluation & Monitoring

- Report confidence intervals and statistical significance for all metrics
- Implement model interpretability with SHAP, LIME, or Captum for critical decisions
- Use fairness metrics (demographic parity, equalized odds) to detect bias
- Implement drift detection for features and model performance (Evidently, Alibi Detect)
- Set up automated retraining triggers based on performance degradation thresholds
- Use A/B testing with proper statistical power analysis for model deployment
- Monitor data quality and feature importance changes in production
- Implement model performance benchmarking against baselines and previous versions

## Production & Deployment

- Use feature stores (Feast, Tecton) for consistent online/offline feature serving
- Implement model versioning with semantic versioning and rollback capabilities
- Use containerization with multi-stage builds for efficient model serving
- Implement health checks, load balancing, and auto-scaling for model endpoints
- Use model registries for governance and approval workflows before production
- Implement shadow mode testing before full deployment of new models
- Set up alerts for model performance, latency, and error rate monitoring
- Use blue-green or canary deployments for risk mitigation

## Documentation & Governance

- Create model cards documenting performance, limitations, and ethical considerations
- Document data lineage, feature engineering steps, and model architecture decisions
- Implement code reviews focusing on data leakage prevention and bias detection
- Use notebooks for exploration but productionize code in proper Python modules
- Maintain experiment tracking with clear naming conventions and tags
- Document model assumptions, edge cases, and failure modes
- Implement audit trails for model decisions in regulated environments
- Document model cards with performance characteristics, limitations, and ethical considerations
