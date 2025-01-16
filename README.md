# **Application Agent Services**

This project provides a service for managing interactions with Odoo, OTP handling, and other functionalities specific to agents.

---

## **Prerequisites**

### **Enable Required Services in Google Cloud**
1. Create an identity for the Secret Manager service:
```bash
   gcloud beta services identity create --service "secretmanager.googleapis.com" --project steam-outlet-209412
 ```
2. Add an IAM policy binding for the Pub/Sub topic topic_secret_changed:
```bash
gcloud pubsub topics add-iam-policy-binding \
projects/steam-outlet-209412/topics/topic_secret_changed \
--member "serviceAccount:service-262908862000@gcp-sa-secretmanager.iam.gserviceaccount.com" \
--role "roles/pubsub.publisher"
 ```
## Local Configuration
.env File

Create a .env file at the root of the project with the following variables:

```env
ODOO_URL="https://baobab.env.local"
ODOO_DB="prod-db"
ODOO_USERNAME="mail@baobab.com"
ODOO_PASSWORD="********"
ODOO_UUID=12
ODOO_SLOW_PAYER_SEGMENTATION_LIST="4"
OTP_SECRET="v4t3Bs7lhatC9hwHYJPzXffFFFFGFG"
OTP_INTERVAL=30
OTP_VALID_WINDOW=1
ENV="LOCAL"
```
### Running Locally with Docker
Run the application locally using Docker:

```
docker run -e PORT=8080 -p 8080:8080 \
--env-file .env \
--network dev \
-v app:/app testapp

```

## Deploying to Google Cloud Run
Deploy the application to Google Cloud Run with the following commands:

TEST
```bash
gcloud run deploy app-agent-services \
--port 8080 \
--source . \
--region europe-west2 \
--allow-unauthenticated \
--update-env-vars "ODOO_URL=https://odoo-preprod.baobabplus.com,ODOO_DB=preprod-db,ODOO_USERNAME=automations,ODOO_UUID=12,ODOO_SLOW_PAYER_SEGMENTATION_LIST=4,OTP_INTERVAL=30,ENV=PREPROD,OTP_VALID_WINDOW=30,ACCESS_TOKEN_EXPIRE=60,REFRESH_TOKEN_EXPIRE=7" \
--set-secrets "ODOO_PASSWORD=odoo-automations:latest,OTP_SECRET=otp-secret:latest,ACCESS_TOKEN_SECRET=odoo-jwt-secret:latest,ACCESS_TOKEN_SECRET=mobile-mw-access-token-secret:latest,REFRESH_TOKEN_SECRET=mobile-mw-refresh-token-secret:latest" \
--timeout=30
```

PROD
```bash
gcloud run deploy app-agent-services \
--port 8080 \
--source . \
--region europe-west2 \
--allow-unauthenticated \
--update-env-vars "ODOO_URL=https://odoo.baobabplus.com,ODOO_DB=prod-db,ODOO_USERNAME=automations,ODOO_UUID=12,ODOO_SLOW_PAYER_SEGMENTATION_LIST=4,OTP_INTERVAL=30,ENV=LOCAL,OTP_VALID_WINDOW=30,ACCESS_TOKEN_EXPIRE=60,REFRESH_TOKEN_EXPIRE=7" \
--set-secrets "ODOO_PASSWORD=odoo-automations:latest,OTP_SECRET=otp-secret:latest,ACCESS_TOKEN_SECRET=odoo-jwt-secret:latest,ACCESS_TOKEN_SECRET=mobile-mw-access-token-secret:latest,REFRESH_TOKEN_SECRET=mobile-mw-refresh-token-secret:latest" \
--timeout=60
```
## Environment Variable Structure
| Name                           | Description                                     | Example                                |
|--------------------------------|-------------------------------------------------|----------------------------------------|
| `ODOO_URL`                     | URL of the Odoo server                          | `https://odoo-preprod.baobabplus.com`  |
| `ODOO_DB`                      | Name of the Odoo database                       | `prod-db`                              |
| `ODOO_USERNAME`                | Odoo username                                  | `mail@baobab.com`                      |
| `ODOO_PASSWORD`                | Odoo user password                             | `********`                             |
| `ODOO_UUID`                    | Unique UUID associated with Odoo               | `12`                                   |
| `ODOO_SLOW_PAYER_SEGMENTATION_LIST` | List of segmentation IDs for slow payers        | `4`                                    |
| `OTP_SECRET`                   | Secret used for OTP generation                 | `v4t3Bs7lhatC9hwHYJPzXffFFFFGFG`       |
| `OTP_INTERVAL`                 | OTP validity interval in seconds               | `30`                                   |
| `OTP_VALID_WINDOW`             | Validation window for OTP                      | `1`                                    |
| `ENV`                          | Execution environment                          | `LOCAL`, `PREPROD`                     |


## Secrets
- ODOO_PASSWORD: Stored in Google Secret Manager.
- OTP_SECRET: Stored in Google Secret Manager.
## Notes
- Ensure sensitive variables and secrets are protected.
- Adjust configurations according to your environments (LOCAL, PREPROD, PROD).
