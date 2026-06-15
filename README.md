Starting the server:

uvicorn app.main:app --reload

Feature Flag API examples (base: http://localhost:8000):

Create a feature flag

curl -X POST "http://localhost:8000/api/v1/flags" \
     -H "Content-Type: application/json" \
     -d '{"name": "beta_feature", "description": "Beta", "default_enabled": false}'

List flags

curl -X GET "http://localhost:8000/api/v1/flags"

Set global state

curl -X PUT "http://localhost:8000/api/v1/flags/beta_feature/global" \
     -H "Content-Type: application/json" \
     -d '{"enabled": true}'

Set per-user override

curl -X PUT "http://localhost:8000/api/v1/flags/beta_feature/users/123" \
     -H "Content-Type: application/json" \
     -d '{"enabled": false}'

Evaluate for user

curl -X GET "http://localhost:8000/api/v1/flags/beta_feature/evaluate?user_id=123"