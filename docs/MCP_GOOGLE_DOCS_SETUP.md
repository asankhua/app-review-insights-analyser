# Phase 8 MCP – Google Doc setup (real values)

Use this to replace the placeholders in `.env` for **MCP_GOOGLE_DOCS_SERVICE_ACCOUNT_PATH** and **MCP_GOOGLE_DOCS_SUBJECT_EMAIL**.

---

## 1. Get the service account JSON file (for `MCP_GOOGLE_DOCS_SERVICE_ACCOUNT_PATH`)

### Step 1.1: Open Google Cloud Console

1. Go to [Google Cloud Console](https://console.cloud.google.com/).
2. Sign in with the Google account that owns (or will own) the Google Doc.

### Step 1.2: Create or select a project

1. In the top bar, click the **project** dropdown.
2. Click **New Project** (or select an existing project).
3. Name it (e.g. `app-review-insights`) and click **Create**.

### Step 1.3: Enable Google Docs API

1. In the left menu go to **APIs & Services** → **Library**.
2. Search for **Google Docs API**.
3. Open it and click **Enable**.

### Step 1.4: Create a service account

1. Go to **APIs & Services** → **Credentials**.
2. Click **+ Create Credentials** → **Service account**.
3. **Service account name:** e.g. `mcp-google-docs`.
4. Click **Create and Continue** (optional: add a role like “Editor” for the project, or skip).
5. Click **Done**.

### Step 1.5: Create and download the JSON key

1. On the **Credentials** page, under **Service accounts**, click the service account you just created.
2. Open the **Keys** tab.
3. Click **Add Key** → **Create new key** → **JSON** → **Create**.
4. A JSON file will download (e.g. `your-project-abc123-xxxx.json`).

### Step 1.6: Save the file and set the path in `.env`

1. Move the downloaded JSON to a fixed location, e.g.:
   - **Mac/Linux:** `~/secrets/google-docs-service-account.json`
   - Or inside the project: `app-review-insights-analyser/secrets/google-docs-service-account.json`  
   (Add `secrets/` to `.gitignore` so the key is never committed.)

2. Use the **full path** in `.env`:

   ```bash
   MCP_GOOGLE_DOCS_SERVICE_ACCOUNT_PATH=/Users/YOUR_USERNAME/secrets/google-docs-service-account.json
   ```

   On Mac, you can get the full path by dragging the file into Terminal, or run:

   ```bash
   realpath ~/secrets/google-docs-service-account.json
   # or on Mac:
   python3 -c "import os; print(os.path.abspath(os.path.expanduser('~/secrets/google-docs-service-account.json')))"
   ```

---

## 2. Set the subject email (for `MCP_GOOGLE_DOCS_SUBJECT_EMAIL`)

The MCP server can run as “this user” when writing to the Doc. Use the **Google account that owns the Doc** (the one you open the Doc with).

- **Personal Gmail:** use that Gmail address.
  ```bash
  MCP_GOOGLE_DOCS_SUBJECT_EMAIL=yourname@gmail.com
  ```
- **Google Workspace:** use the Workspace user who owns or should own the Doc.
  ```bash
  MCP_GOOGLE_DOCS_SUBJECT_EMAIL=you@yourcompany.com
  ```

Use the **same** account you use to create and open the Google Doc.

---

## 3. Share the Google Doc with the service account

The Doc must be shared with the **service account’s email** (not your personal email).

1. Open the JSON file you downloaded.
2. Find the field **`client_email`**. It looks like:
   ```text
   something@your-project-abc123.iam.gserviceaccount.com
   ```
3. Open your Google Doc (the one whose ID you put in `GOOGLE_DOC_ID`).
4. Click **Share**.
5. Add the **`client_email`** address as a user.
6. Give it **Editor** access.
7. Click **Send** (you can uncheck “Notify people” if you prefer).

---

## 4. Update your `.env` file

Edit `.env` and replace the two placeholders with your real values:

```bash
# Phase 8: Google Doc (optional; uncomment and set if needed)
GOOGLE_DOC_ID=18QNI1O7hYnT4U8VtO7bfuvIIiD819I2tMVL8D2jL7H0
MCP_GOOGLE_DOCS_USE_MCP=1
MCP_GOOGLE_DOCS_MCP_COMMAND=uvx
MCP_GOOGLE_DOCS_MCP_ARGS=google-docs-mcp-server
# ↓ Replace with the FULL path to your downloaded JSON file:
MCP_GOOGLE_DOCS_SERVICE_ACCOUNT_PATH=/Users/asankhua/secrets/google-docs-service-account.json
# ↓ Replace with the Google account that owns the Doc (Gmail or Workspace):
MCP_GOOGLE_DOCS_SUBJECT_EMAIL=ashishsankhuapg@gmail.com
```

- **MCP_GOOGLE_DOCS_SERVICE_ACCOUNT_PATH** = full path to the JSON key file.
- **MCP_GOOGLE_DOCS_SUBJECT_EMAIL** = email of the account that owns the Doc (your Gmail or Workspace email).

---

## 5. Test

From the project root:

```bash
python scripts/test_mcp.py
```

If everything is set correctly, you should see something like:

- `Google Doc: appended successfully via MCP.`
- `OK: Append succeeded. Check your Google Doc for the test block.`

If you see an error, check:

- Path in `MCP_GOOGLE_DOCS_SERVICE_ACCOUNT_PATH` (no spaces, correct file).
- Doc shared with the **service account `client_email`** from the JSON.
- `MCP_GOOGLE_DOCS_SUBJECT_EMAIL` = the account that owns the Doc.
- Google Docs API enabled for the project that owns the service account.

