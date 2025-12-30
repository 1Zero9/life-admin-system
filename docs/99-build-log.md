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
