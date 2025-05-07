import logging
from logging.handlers import TimedRotatingFileHandler
from metadefender_menlo.log_handlers.log_request_filter import LogRequestFilter
from metadefender_menlo.log_handlers.kafka_log import KafkaLogHandler
from metadefender_menlo.log_handlers.SNS_log import SNSLogHandler

def init_logging(config):
    config_logging = config["logging"]
    if "enabled" not in config_logging or not config_logging["enabled"]:
        return

    logger = logging.getLogger()
    logging.getLogger('uvicorn.access').disabled = True
    logging.getLogger('kafka.conn').disabled = True
    logging.getLogger('kafka.access').disabled = True
    logger.setLevel(config_logging["level"])
    logfile = config_logging["logfile"]
    
    # create log handlers
    log_handler = TimedRotatingFileHandler(
        filename=logfile, when="h", interval=config_logging["interval"], backupCount=config_logging["backup_count"])

    log_format = '%(asctime)s - %(levelname)s - %(filename)s > %(funcName)s:%(lineno)d - %(message)s'
    formatter = logging.Formatter(
        fmt=log_format, datefmt='%m/%d/%Y %I:%M:%S %p')

    log_handler.setFormatter(formatter)

    if config['logging']['kafka']['enabled']:
        log_handler_kafka = KafkaLogHandler(config, config['logging']['kafka'])
        if hasattr(log_handler_kafka, "sender"):
            logger.addHandler(log_handler_kafka)
        else:
            logger.addHandler(log_handler)
    else:
        logger.addHandler(log_handler)

    if config['logging']['sns']['enabled']:
        log_hanfler_sns = SNSLogHandler(config['logging']['sns'])
        logger.addHandler(log_hanfler_sns)

    log_request_filter = LogRequestFilter()

    for handler in logging.getLogger().handlers:
        try:
            handler.addFilter(log_request_filter)
        except Exception as error:
            print(error)