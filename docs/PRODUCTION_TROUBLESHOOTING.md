# Production Troubleshooting Guide - Google Docs Integration

## Problem
Combined report is not getting appended to Google Doc in production (Render/Vercel), even though base64 environment variable has been added.

## 🔍 Step-by-Step Troubleshooting

### **Step 1: Verify Environment Variables in Production**

#### **Check Render:**
1. Go to your Render dashboard
2. Select your service
3. Go to "Environment" tab
4. Verify these variables are set:
   ```
   GOOGLE_DOC_ID=18QNI1O7hYnT4U8VtO7bfuvIIiD819I2tMVL8D2jL7H0
   GOOGLE_SERVICE_ACCOUNT_BASE64=ewogICJ0eXBlIjogInNlcnZpY2VfYWNjb3VudCIsCiAgInByb2plY3RfaWQiOiAib3B0aW11bS1wbGV4dXMtNDkwNzAzLXA1IiwKICAicHJpdmF0ZV9rZXlfaWQiOiAiNzY4YmE3ZTc3MzRjYzI4MjExZDgzZTQ1ZGE3OWIwYTM2ZWYxMWFmYiIsCiAgInByaXZhdGVfa2V5IjogIi0tLS0tQkVHSU4gUFJJVkFURSBLRVktLS0tLVxuTUlJRXZnSUJBREFOQmdrcWhraUc5dzBCQVFFRkFBU0NCS2d3Z2dTa0FnRUFBb0lCQVFER3JCd1BEcHRWUGwvcVxub01UcVkzdzR4c01EbUZ4SkczdFlXa1FSaHZMZnp1MkNGdUFreGVyU3ZvSGxUOS9EclpSd2hJd2l6Rkh6OTRSRlxuOThOMldLWjNJcS9WMjJZNzU2ejZRWlNNOEhDTXdwTE42ZnJMRWU2R3c4NVpQVjVmYkkxMHJDRjExcjgxeG1iNlxuVUQ1YmRVYkk5dS9wUEswdzd3alFkUDZ4T0p0WkFNMmtLTHBoRXAvbFV3UXNVT2pmWW85WUZtN3BLcXZVblBvMFxuaUVZQk5RTjVOTmVYbjRxZm4rL1B0MGtMVmlYUGRqTDhJc0FWYmZqZGU3MG50QzhCakRrUmpwajlhZzFNck5QVFxuWndPaHdpbVhvMFNEdnp5cUwrUHdmbllUVVBWSFIvYjNReXIzZDhQOEhiSjB0b21WU1FOV1I3SWRqOEZFc2tka1xuR1FqdXBrTC9BZ01CQUFFQ2dnRUFWSWNLb3g5Z1dIcmkzVlZNb3JyME1jWGpXQWE5a1A5SDBmWUp5dmxESVpVTlxuZVZGWlNWd0p4bU4ycWNWN20yb2hZMlFKcVk2TCtjUmdPMUtvajVRMU16QUhadkpqZzI1Vkt0NjNJT1gxeFBYTlxuOXgwcmJyWHc2ZGFxVjA2a2RlNGVHenRYT3lkRWtGRWJKRG42NWZlMlI2L0VzRlA0RGY5Tm5UK0IwNDRWamw1b1xuakg3endXOUFyc0dyeW9WYmlOcldIR3ZhN05ZR1BCNzZiZklnUHd5bVdieHRFYzlqdHpLQUxJaXdNNlBseGxSYVxuaDNBazA1UnZ6WUJMYU1VeWU0UG1pWHZoU0RVYkoxYXFHWFNPand4SHBCdHE2Q3AyelB0L0NMUytadmFhWkRWUlxuT29TSWdRZDRKc3MrcTJBWW5PZWdJZy84dCtIaHd1Wkl4NFZ0aFdYT1FRS0JnUURyUWNRRWtIellxdGdhcFdhTVxuS3lZSG9VNmQyTnBWeHR0Ni95UmlVWEt4UWNUU2gzeC85bHlLSDhGdnYvZFdYUm5OSkdzY1JBY0dRclBLYXN5cFxueDNFMXRyQXRDNFVVcXhQTDZqRnBRVFVNQ2FPWjhtN0R3d05kdG12OE9yaXZCWkorM0xvWkF6Zkw5MTF2VTZLdFxucGhBczB5bFFkUTNHZVZEZGZ4RkRlTzUvUHdLQmdRRFlNSTNVY1o3b1lHWTBNd3BpbUttT05ReEVkcGlKQzBMZ1xuT3VYNExWUlBZRVc2b1VvdUpTb0xmelhQb2dlSk50SVNua2R3dkxOMnM4VmZyTllvSHJOOTJyRmZVeUhNQjdtVlxuT1lZYU44TGpIUnVlTFZIdXIvSjN2eGdOYmY1WGNnSXNRWUNFalMzU0lEeEh3REpWODJEOGdacEtnVHJ4eTJBaFxubWFibi9KOE1RUUtCZ1FDZUh6RHg1RytWYlpjY3FjazRNeFEza3FyMW16aDg2TkRDWmRUOXBFTFRjeUlvWXRwQ1xuWThNbEwxemprSUpjOE95VG5vUERsdEdsMnBWZld0TSsxZ2Q0azlic0g4OE42a0svRHlTdzJ4d2RnQ2tQSXd4aFxuMWFSZ2kya2ZPaFRCeHB3RldyUldkWHcrUW4veGdLUloxTUVRYjhsWUE2VURucXpFZzFDR0tqVWJId0tCZ0dBbVxuMkMzUWl2aVhSMTJZQmRwc1E1MDRBc2pBWm44dFB3VXpyT3lBWEtzaENtSkRNaGJyK0pNOGROWndIaUhzKytuRFxuODhvMFl5MDhMMkNxSW1XZG9mOHJzUS9Rall1Tk5BRW1vSG93cXNFUVJTUkl5OVA0OVVKRS81R1poakdtUjBrZlxucU9WTFZVSExqSVBzKzNZMjFMLzVkSUlHa0F6U2cyTHVUOG1HRmNjQkFvR0JBTkxhQndZUVd4S3BCdW1mTElhS1xueUFzUWRsRXFLQzBZbXBad1RTWjY5WEsyMVB6UDVQRk5KWkY4ZGpGWWVHQXY3L2pTU3QvY2VwMDdTcWhnZ0ZsdlxuY2RkSGNSZVJOLzdlMWJnSVRhclFQRzY0TDFBdmVPczVGbEx3NmxRV244OCt1aHQyNHgyU21odDdlSk5maUtUL1xuRHg2THJBS2dkWjFXbjFFL0NVbXZIYnFuXG4tLS0tLUVORCBQUklWQVRFIEtFWS0tLS0tXG4iLAogICJjbGllbnRfZW1haWwiOiAibWNwLWdvb2dsZS1kb2NzQG9wdGltdW0tcGxleHVzLTQ5MDcwMy1wNS5pYW0uZ3NlcnZpY2VhY2NvdW50LmNvbSIsCiAgImNsaWVudF9pZCI6ICIxMDU5ODgxNTE4ODMyMzkwMjQ2MDMiLAogICJhdXRoX3VyaSI6ICJodHRwczovL2FjY291bnRzLmdvb2dsZS5jb20vby9vYXV0aDIvYXV0aCIsCiAgInRva2VuX3VyaSI6ICJodHRwczovL29hdXRoMi5nb29nbGVhcGlzLmNvbS90b2tlbiIsCiAgImF1dGhfcHJvdmlkZXJfeDUwOV9jZXJ0X3VybCI6ICJodHRwczovL3d3dy5nb29nbGVhcGlzLmNvbS9vYXV0aDIvdjEvY2VydHMiLAogICJjbGllbnRfeDUwOV9jZXJ0X3VybCI6ICJodHRwczovL3d3dy5nb29nbGVhcGlzLmNvbS9yb2JvdC92MS9tZXRhZGF0YS94NTA5L21jcC1nb29nbGUtZG9jcyU0MG9wdGltdW0tcGxleHVzLTQ5MDcwMy1wNS5pYW0uZ3NlcnZpY2VhY2NvdW50LmNvbSIsCiAgInVuaXZlcnNlX2RvbWFpbiI6ICJnb29nbGVhcGlzLmNvbSIKfQo=
   ```

#### **Check Vercel:**
1. Go to your Vercel dashboard
2. Select your project
3. Go to "Settings" → "Environment Variables"
4. Verify the same variables are set

### **Step 2: Test Production API Endpoints**

#### **Add Debug API to Production:**
1. Deploy the `debug_production_api.py` to your production environment
2. Add it as a new service or endpoint

#### **Test Debug Endpoints:**
```bash
# Check configuration
curl https://your-app.onrender.com/api/debug/google-docs

# Test Google Doc append
curl -X POST https://your-app.onrender.com/api/debug/test-google-docs \
  -H "Content-Type: application/json" \
  -d '{"test_message": "Production Debug Test"}'

# Test Phase 8
curl https://your-app.onrender.com/api/debug/phase8
```

### **Step 3: Check Google Doc Permissions**

#### **Verify Service Account Access:**
1. Open your Google Doc: https://docs.google.com/document/d/18QNI1O7hYnT4U8VtO7bfuvIIiD819I2tMVL8D2jL7H0
2. Click "Share" → "Share with people"
3. Add the service account email: `mcp-google-docs@optimum-plexus-490703-p5.iam.gserviceaccount.com`
4. Give it "Editor" permissions

### **Step 4: Check Production Logs**

#### **Render Logs:**
1. Go to Render dashboard
2. Select your service
3. Click "Logs" tab
4. Look for errors related to Google Docs API

#### **Vercel Logs:**
1. Go to Vercel dashboard
2. Select your project
3. Click "Logs" tab
4. Look for Google Docs API errors

### **Step 5: Common Issues & Solutions**

#### **Issue 1: Base64 Encoding Problems**
**Symptoms:** Environment variable set but API returns "credentials not configured"
**Solution:** 
- Re-encode the service account JSON: `base64 -i secrets/optimum-plexus-490703-p5-768ba7e7734c.json`
- Ensure no line breaks in the base64 string

#### **Issue 2: Google Doc Permissions**
**Symptoms:** "Permission denied" or "403 Forbidden" errors
**Solution:**
- Share the Google Doc with the service account email
- Give "Editor" permissions (not just "Viewer")

#### **Issue 3: Missing Dependencies**
**Symptoms:** "ImportError" or "Module not found" errors
**Solution:**
- Ensure `google-api-python-client` and `google-auth` are installed
- Check `requirements.txt` includes these packages

#### **Issue 4: API Quota Exceeded**
**Symptoms:** "Quota exceeded" or "Rate limit" errors
**Solution:**
- Check Google Cloud Console API quotas
- Enable billing if necessary for Google Docs API

### **Step 6: Quick Fix Commands**

#### **Deploy Debug API:**
```bash
# Add debug API to your main app
# Copy debug_production_api.py content to your main app
# Deploy to production
```

#### **Test Locally with Production Env:**
```bash
# Run local debug to simulate production
python3 debug_production.py
```

#### **Force Deploy Latest Code:**
```bash
# Ensure latest code is deployed
git push origin main
# Trigger new deployment on Render/Vercel
```

## Expected Results

### **✅ Working Configuration:**
```json
{
  "checks": {
    "google_doc_id": {"set": true},
    "base64_creds": {"set": true, "length": 3196},
    "base64_decode": {"success": true, "project_id": "optimum-plexus-490703-p5"},
    "import_client": {"success": true},
    "credentials": {"success": true, "has_content": true}
  }
}
```

### **✅ Successful Test:**
```json
{
  "success": true,
  "message": "Appended to Google Doc: 18QNI1O7hYnT4U8VtO7bfuvIIiD819I2tMVL8D2jL7H0"
}
```

## Next Steps

1. **Run the debug script locally** to confirm setup works
2. **Deploy debug API** to production
3. **Test debug endpoints** to identify the specific issue
4. **Fix the identified issue** (environment variables, permissions, etc.)
5. **Test combined report** again in production

---

## 🚀 Emergency Fix

If you need a quick solution, you can:

1. **Use the force append script** directly in production:
   ```bash
   # In production terminal
   python3 force_append_to_doc.py
   ```

2. **Check the Google Doc directly** to see if content appears:
   - Open: https://docs.google.com/document/d/18QNI1O7hYnT4U8VtO7bfuvIIiD819I2tMVL8D2jL7H0
   - Look for recent appended content

3. **Contact support** if the issue persists after following all steps

---

**🔍 Follow this troubleshooting guide step by step to identify and fix the production issue!**
