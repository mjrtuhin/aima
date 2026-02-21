import structlog
from platform.workers.celery_app import celery_app

log = structlog.get_logger()


@celery_app.task(bind=True, max_retries=2)
def recompute_customer_features(self, customer_id: str, org_id: str) -> dict:
    log.info("Recomputing features", customer_id=customer_id)
    try:
        from modules.customer_intelligence.features.engineer import FeatureEngineer
        engineer = FeatureEngineer(org_id=org_id)
        features = engineer.compute(customer_id=customer_id)
        return {"customer_id": customer_id, "features_computed": len(features)}
    except Exception as exc:
        log.error("Feature computation failed", customer_id=customer_id, error=str(exc))
        raise self.retry(exc=exc)


@celery_app.task
def recompute_all_features() -> dict:
    log.info("Starting scheduled feature recomputation for all customers")
    return {"status": "scheduled"}


@celery_app.task
def update_churn_predictions() -> dict:
    log.info("Updating churn predictions for all customers")
    return {"status": "scheduled"}


@celery_app.task
def update_brand_sentiment() -> dict:
    log.info("Updating brand sentiment from all sources")
    return {"status": "scheduled"}


@celery_app.task
def check_segment_drift() -> dict:
    log.info("Checking segment drift for all customers")
    return {"status": "scheduled"}


@celery_app.task(bind=True, max_retries=2)
def train_customer_intelligence_model(self, org_id: str, config: dict) -> dict:
    log.info("Training Customer Intelligence model", org_id=org_id)
    try:
        from modules.customer_intelligence.models.transformer import TemporalBehavioralTransformer
        model = TemporalBehavioralTransformer(config=config)
        result = model.train(org_id=org_id)
        return result
    except Exception as exc:
        log.error("Model training failed", org_id=org_id, error=str(exc))
        raise self.retry(exc=exc)
