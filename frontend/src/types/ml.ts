export interface MLFeatureSchema {
  feature_names: string[];
  dtypes?: Record<string, string>;
  target_column?: string;
}

export interface MLModelMetrics {
  accuracy?: number;
  precision?: number;
  recall?: number;
  f1_score?: number;
  f1?: number;
  auc_roc?: number;
  log_loss?: number;
  [key: string]: any;
}

export interface MLModel {
  model_name: string;
  version: string;
  artifact_location: string;
  artifact_sha256: string;
  task_type?: string;
  framework?: Record<string, string>;
  input_schema: MLFeatureSchema;
  training_dataset?: string;
  metrics?: MLModelMetrics;
  import_timestamp?: string;
  active: boolean;
}

export interface MLModelRegistryResponse {
  models: MLModel[];
}

export interface MLPredictionResult {
  prediction: string;
  probability: number | null;
  features_validated: boolean;
  model: string;
  model_version: string;
  artifact_hash: string;
  analyst_verification_required: boolean;
  prediction_timestamp: string;
}

export interface MLImportResponse extends MLModel {
  status: string;
  validation: string;
}
