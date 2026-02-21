import structlog
from platform.workers.celery_app import celery_app

log = structlog.get_logger()


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def sync_connector(self, connector_id: str, org_id: str) -> dict:
    log.info("Syncing connector", connector_id=connector_id)
    try:
        from data.connectors.base import ConnectorRegistry
        connector = ConnectorRegistry.get(connector_id)
        result = connector.sync()
        log.info("Connector sync complete", connector_id=connector_id, records=result.get("records"))
        return result
    except Exception as exc:
        log.error("Connector sync failed", connector_id=connector_id, error=str(exc))
        raise self.retry(exc=exc)


@celery_app.task
def sync_all_connectors() -> dict:
    log.info("Starting scheduled sync for all active connectors")
    from sqlalchemy import create_engine, select
    from platform.api.config import settings
    from platform.api.models import Connector
    results = {"synced": 0, "failed": 0}
    try:
        engine = create_engine(settings.DATABASE_URL_SYNC)
        with engine.connect() as conn:
            rows = conn.execute(select(Connector).where(Connector.is_active == True))
            for row in rows:
                sync_connector.delay(str(row.id), str(row.org_id))
                results["synced"] += 1
    except Exception as e:
        log.error("Failed to schedule connector syncs", error=str(e))
    return results
