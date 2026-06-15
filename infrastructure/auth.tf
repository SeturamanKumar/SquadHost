# auth.tf
# ------------------------------------------------------------------------------
# Cognito + Lambda@Edge Authentication
# Added in 1.3. Will hold:
# - Cognito User Pool
# - Cognito User Pool Client (for Next.js frontend)
# - Cognito hosted UI domain
# - Lambda@Edge function for JWT validation at CloudFront viewer-request
# - First admin user (or post-deploy script reference)
# ------------------------------------------------------------------------------
