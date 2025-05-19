import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

def traces_sampler(sampling_context):
    """Filter healthcheck endpoint when sending transactions to sentry"""
    if sampling_context.get("request") and '/api/v1/health' in sampling_context["request"].url.path:
        return 0
    return 1

def init_sentry(env, sentry_dsn):
    if env != 'local' and sentry_dsn:
        sentry_sdk.init(
            dsn=sentry_dsn,
            integrations=[
                FastApiIntegration(),
            ],
            environment=env,
            traces_sampler=traces_sampler,
        )