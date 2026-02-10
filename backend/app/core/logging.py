import logging
from app.core.context import request_id_var

def setup_logging(level: str = "INFO") -> None:
    # Injetar request_id em todo LogRecord
    old_factory = logging.getLogRecordFactory()

    def record_factory(*args, **kwargs):
        record = old_factory(*args, **kwargs)
        record.request_id = request_id_var.get("-")
        return record

    logging.setLogRecordFactory(record_factory)

    # Formato padrão (simples e útil em prod)
    fmt = "%(asctime)s %(levelname)s %(name)s request_id=%(request_id)s %(message)s"
    logging.basicConfig(level=level.upper(), format=fmt)
