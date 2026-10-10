# Synthetic demonstration models

All three models use scikit-learn, fixed seed 42 and disjoint 60/20/20 train/validation/test splits. Hyperparameters are selected using validation data. The final test set is used only for reporting. Labels are generated synthetic rules, not learner outcomes or production accuracy.

- `python -m app.ml.training.train`: Ridge relevance ranker for resources/projects. Reports MAE/RMSE and NDCG@5 on fixed groups of ten held-out synthetic candidates. This ranking evaluation is not a real recommendation benchmark.
- `python -m app.ml.training.advisory`: multinomial logistic evidence-strength classifier and Ridge learning-risk regression. Reports macro precision/recall/F1 and MAE/RMSE respectively.

Models are versioned JSON weight artifacts, with no pickle execution. Training datasets and metrics are saved in data/ and evaluation/. Runtime features come from authenticated canonical student state. GET /api/v1/analytics/intelligence and GET /api/v1/state expose advisory inference. Predictions never grant evidence verification or change mastery/readiness.

Risk is a synthetic advisory score, not a calibrated probability of failure. Engagement uses attempt/completion counts; missing time-tracking is not fabricated. Collect consented real outcome data and perform representative evaluation before using predictions to make learner decisions.
