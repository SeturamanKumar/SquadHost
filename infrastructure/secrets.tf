# secrets.tf
# ------------------------------------------------------------------------------
# Secrets Manager + SSM Parameter Store
# Added in 1.2. Will hold:
# - playit.gg secret token
# - Webhook shared secret (replacing random_password.webhook_secret in compute.tf)
# - Any other runtime secrets needed by Lambda functions
# ------------------------------------------------------------------------------
