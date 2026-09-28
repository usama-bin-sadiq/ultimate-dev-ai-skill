<!-- Moved verbatim from gemini-interactions-api/SKILL.md, the
     '1-authentication' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## 1. Authentication

Before running any code, ensure you are authenticated with Application Default Credentials (ADC) and have the necessary API enabled.

1.  **Login**:
    
    ```bash
    gcloud auth application-default login
    ```
2.  **Enable API** (if not already enabled):
    
    ```bash
    gcloud services enable aiplatform.googleapis.com
    ```

---
