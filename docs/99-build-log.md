# Build Log – Life Admin System

This log records what was built, how it was built, and what went wrong.

The purpose is:
- future understanding
- reproducibility
- debugging
- legacy handover

---

## 2025-01-XX – Initial R2 intake wiring

### Goal
Upload life admin documents and store originals safely.

### What worked
- FastAPI service started successfully
- R2 bucket created (`life-admin-documents`)
- S3-compatible upload works
- Object key format: documents/YYYY/MM/uuid.ext

### What failed
- macOS privacy blocked Downloads folder access
- curl could not read files from Downloads

### Resolution
- Moved test files into project directory
- Added Files/ to .gitignore
- Confirmed uploads via curl from project path

### Notes
- R2 chosen for predictable access and no egress fees
- UUID-based object keys avoid naming decisions

---

## 2025-12-30 – Build update (14:52)

### Goal
- 

### What worked
- 

### What failed
- 

### Resolution
- 

### Notes
- 

---

## 2025-12-30 – Build update (16:14)

### Goal
- 

### What worked
- 

### What failed
- 

### Resolution
- 

### Notes
- 

---

## 2025-12-30 – Build update (16:19)

### Goal
- 

### What worked
- 

### What failed
- 

### Resolution
- 

### Notes
- 

---

## 2025-12-30 – Build update (16:33)

### Goal
-

### What worked
-

### What failed
-

### Resolution
-

### Notes
-

---

## 2025-12-30 – Added claude.md and build log protocol

### Goal
- Create AI assistant guidance document to maintain project ethos
- Establish protocol for keeping build log current

### What worked
- Created `/claude.md` with core principles and guardrails
- Documented the 7 core principles (zero decision-making at intake, documents as truth, one-way flow, longevity, simplicity, AI assists/humans decide, no bloat)
- Included "always do" and "never do" lists
- Added explicit instruction to call out principle violations
- Updated claude.md to emphasize build log maintenance requirement

### What failed
- Nothing

### Resolution
- N/A

### Notes
- claude.md serves as the first line of defense against feature creep and principle violations
- Build log format: Goal → What worked → What failed → Resolution → Notes
- Build log is critical for longevity goal (10-20+ years) and legacy handover
- Empty build log entries from earlier in the day remain (14:52, 16:14, 16:19) - to be filled in retrospectively if needed

---

## 2025-12-30 – Git repository cleanup and commit organization

### Goal
- Clean up git repository and properly commit all recent work
- Remove Python bytecode files from tracking
- Organize commits logically by feature/purpose

### What worked
- Updated .gitignore to exclude __pycache__/, *.pyc, *.pyo, *.pyd
- Removed tracked pycache files from repository (3 files)
- Organized work into 3 logical commits:
  1. chore: gitignore cleanup and pycache removal (731f5c5)
  2. feat: PDF text extraction and content search (2c22a0b)
  3. docs: claude.md and build log protocol (6507da3)
- Successfully pushed to origin/main
- All commits include Claude Code attribution

### What failed
- Nothing

### Resolution
- N/A

### Notes
- Python bytecode files were being tracked due to missing .gitignore entries
- PDF extraction feature had been implemented but not yet committed
- Commit messages follow existing pattern: prefix (feat/docs/chore) + description
- Repository now clean with working tree up to date
- Total 3 commits ahead of previous state (60dc137)
