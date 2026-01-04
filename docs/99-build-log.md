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

---

## 2025-12-30 – Testing and bug fix: duplicate search endpoint

### Goal
- Test PDF text extraction and content search functionality
- Verify all endpoints work correctly end-to-end

### What worked
- Database schema verified - extracted_text column exists
- FastAPI application starts successfully
- PDF upload with text extraction works correctly
- Uploaded 083205518681.pdf (161KB, 9148 chars extracted)
- Extracted text includes: name, address, billing info, dates
- Recent items endpoint works correctly
- Search by filename works

### What failed
- Search by PDF content initially returned empty results
- Root cause: duplicate search endpoint definitions in app/main.py
  - Line 157: Old endpoint - only searched filenames
  - Line 220: New endpoint - searches filenames AND extracted_text
  - First definition was being used, so content search didn't work

### Resolution
- Removed duplicate search endpoint (lines 154-183)
- Kept the correct implementation with extracted_text search
- Fixed unused variable warning in ui_upload endpoint
- Verified searches work correctly:
  - Search "Swords" → found (from address)
  - Search "Cranfield" → found (from name)
  - Search "electricity" → found (case-insensitive)
  - Search "nonexistent" → no results (correct)

### Notes
- PDF text extraction is fully functional and deterministic
- Content search works with case-insensitive ILIKE in SQLite
- All MVP requirements for content indexing are met:
  - extracted_text column added ✓
  - extract_pdf_text() implemented ✓
  - Upload flow extracts PDF text ✓
  - Search endpoint searches both filename and content ✓
- Server auto-reload feature helped during testing
- The duplicate endpoint was likely from an earlier implementation attempt
---

## 2026-01-03 – OCR for Image Attachments

### Goal
- Add OCR capability for image attachments (JPG/PNG) in Gmail ingestion
- Make image attachments searchable via text extraction
- Keep implementation minimal and robust

### What worked
- System dependencies installed successfully:
  - `brew install tesseract` (macOS) - Tesseract 5.5.2
- Python dependencies added to requirements.txt:
  - pytesseract==0.3.13
  - pillow==11.2.0
  - opencv-python==4.10.0.84
- Created extract_text_from_image() function in scripts/gmail_ingest.py
- Image detection by MIME type (image/png, image/jpeg) and file extension (.jpg, .jpeg, .png)
- Optional OpenCV preprocessing (grayscale + thresholding) improves accuracy
- Graceful degradation if OpenCV not available
- Temp file handling with proper cleanup
- Image attachments now searchable via /items/search endpoint
- Logging: "OCR extracted X characters from <filename>"
- Updated README.md with Tesseract installation instructions

### Testing
- Tested with iPhone camera photo (IMG_0193.jpeg - medical receipt)
- OCR successfully extracted 337 characters:
  - Clinic name, address, patient name, date, amount
- Search verification passed:
  - Search "Plaza" → Found image
  - Search "Clinic" → Found image
  - Search "RECEIPT" → Found image (plus PDFs)
  - Search "Cranfield" → Found image (plus emails)

### What failed
- Nothing

### Resolution
- N/A

### Notes
- System requirement: Tesseract OCR must be installed (brew install tesseract on macOS)
- OCR only applies to attachments (source_type="attachment"), not uploaded files
- Extracted text stored in items.extracted_text (same field as PDF text)
- No database schema changes required
- Preprocessing with OpenCV optional but recommended for better accuracy
- Import guards ensure script works even if pytesseract/opencv missing
- PYTESSERACT_AVAILABLE and CV2_AVAILABLE flags control feature availability

---

## 2026-01-03 – OCR Quality Markers and Guardrails

### Goal
- Add quality markers to identify extraction source (EMAIL/PDF/OCR)
- Add guardrails to prevent OCR slowdowns and duplicate processing
- Improve debugging and performance

### What worked
- Quality markers implemented:
  - EMAIL: prefix for email body text
  - PDF: prefix for PDF extracted text
  - OCR: prefix for image OCR text
- OCR guardrails implemented:
  - 10 MB file size limit (configurable)
  - Attachment idempotency check (source_type + source_id + parent_id)
  - Type checking (images only)
  - Availability checking (pytesseract required)
- Clear logging when skipping OCR:
  - "Skipping OCR for huge.jpg (size 15.2 MB exceeds 10 MB limit)"
  - "Skipping receipt.jpg (already ingested)"

### What failed
- Nothing

### Resolution
- N/A

### Notes
- Quality markers help identify extraction issues in search results
- File size threshold prevents OCR timeouts on large images
- Idempotency prevents duplicate processing on re-runs
- Newly ingested items have quality markers
- Existing items retain their current format (no migration needed)
- Guardrails ensure OCR doesn't slow down the ingestion process

---

## 2026-01-04 – Vault UI Layer 1 (Initial Implementation)

### Goal
- Build human-first document vault UI (pre-AI layer)
- Hide technical details, show only what humans need
- Calm, minimal, scannable interface

### What worked
- Created `app/ui_helpers.py` with title normalization and date formatting
- Title normalization rules:
  - Emails: strip .eml, replace underscores with spaces
  - Images (IMG_xxxx): "Image · 3 January"
  - Uploads: strip extension, replace separators with spaces
  - Attachments: strip extension only
- Date formatting:
  - Today: "Today, 14:32"
  - Yesterday: "Yesterday, 20:46"
  - This week: "Tuesday, 11:20"
  - This year: "15 March"
  - Older: "12 July 2024"
- Redesigned `index.html` with clean minimalist layout
- Separate upload page at `/upload`
- Backend route returns formatted items with parent-child grouping
- Search works across filenames and extracted_text
- All technical metadata hidden (object keys, file sizes, etc.)

### What failed
- Initial minimalist design deemed insufficient for real-world use
- Single-column list doesn't scale to hundreds/thousands of documents
- Hiding all controls on separate pages creates navigation friction
- Theoretical minimalism conflicts with practical usability

### Resolution
- Documented design evolution in `/docs/20-vault-ui-evolution.md`
- Decision: pivot to single-screen interface with sidebar and filters
- Keep core principles (no AI, no tags, calm design)
- Add practical features (filters, table layout, visible controls)
- **Next build:** comprehensive single-screen Vault UI

### Notes
- Initial implementation validated the data flow and helper functions
- Title normalization working correctly for all source types
- Date formatting uses relative times for recent items (better UX)
- Learned: "minimal" doesn't mean "featureless" - it means purposeful
- One well-designed screen > multiple simple screens
- Design evolution: minimalism for its own sake vs minimalism for usability

---

## 2026-01-04 – Single-Screen Vault UI (Complete)

### Goal
- Build comprehensive single-screen document management interface
- Sidebar navigation with filters
- Table layout with file type icons
- Integrated search and upload
- All controls visible at once

### What worked
- **File type detection** (`app/ui_helpers.py`):
  - `get_file_type()`: detects pdf, email, image, word, excel, audio, video, archive
  - `get_file_icon_color()`: color-coded icons (red PDFs, blue emails, green images, etc.)
- **Backend filtering** (`app/main.py`):
  - Updated `ui_home()` route with `source` and `q` parameters
  - Dynamic filtering by source type (email, upload, attachment, all)
  - Combined with search functionality
  - Returns counts for sidebar display
- **Single-screen layout** (`app/templates/index.html`):
  - Left sidebar (240px fixed width):
    - "Document Vault" header
    - Navigation sections (Library, Source)
    - Filter links with document counts
    - Upload button in footer
  - Main content area:
    - Top bar with search (auto-submit after 500ms)
    - Content header showing current view and count
    - Table layout with 3 columns: Name, Date, Source
    - File type icons with colors
    - Row hover effects
  - Upload modal:
    - Triggered by sidebar button
    - Modal overlay with form
    - Cancel or submit
- **Visual design**:
  - Apple-inspired color palette (#F5F5F7 background, #1D1D1F text)
  - Clean typography (San Francisco system font)
  - Subtle borders and shadows
  - Consistent spacing and padding
  - Professional, calm appearance
- **All functionality working**:
  - Filter by source type (All: 49, Emails: 13, Uploads: 2, Attachments: 34)
  - Search across filenames and extracted text
  - File type icons render correctly (PDF, email, image, audio, etc.)
  - Upload modal opens/closes
  - Table displays all document metadata
  - Download links work

### What failed
- Nothing

### Resolution
- N/A

### Notes
- Single-screen approach solves scalability issues of initial minimalist design
- All controls accessible without page navigation
- Information density achieved through table layout, not hiding features
- File type icons provide instant visual recognition
- Color-coded icons aid scanning (red=PDF, blue=email, green=image)
- Sidebar counts give immediate overview of document distribution
- Search auto-submit provides real-time filtering
- Upload modal keeps main view clean while making upload accessible
- Design is still "boring and calm" - just more complete
- Ready for real-world use with hundreds of documents
- No AI features, no tags, no manual categorization - stays true to core principles
- This completes Layer 1 (Vault UI) - next is Layer 2 (AI Understanding)

---

## 2026-01-04 – OCR for Uploads, Duplicate Detection, and Delete

### Goal
- Add OCR text extraction for uploaded images (not just email attachments)
- Implement duplicate detection to prevent uploading same file twice
- Add soft delete functionality with UI controls

### What worked
- **OCR for uploads** (`app/extractors.py`, `app/main.py`):
  - Moved `extract_image_text()` from gmail_ingest to shared extractors module
  - Added image detection to upload endpoint
  - Applied same 10 MB file size limit as email attachments
  - Extracts text with Tesseract + OpenCV preprocessing
  - Stores with "OCR:" prefix in extracted_text column
  - Uploaded images now searchable (receipts, screenshots, scans)
- **Duplicate detection** (`app/models.py`, `app/main.py`):
  - Added `file_hash` column (SHA256 hash of file content)
  - Upload endpoint calculates hash before uploading
  - Checks database for existing file with same hash
  - Returns duplicate=true with existing item details if found
  - Prevents duplicate storage in R2 and database
- **Soft delete** (`app/models.py`, `app/main.py`, `app/templates/index.html`):
  - Added `deleted_at` column to items table
  - DELETE `/items/{item_id}` endpoint marks items as deleted (doesn't remove from R2)
  - All queries filter out deleted items (`WHERE deleted_at IS NULL`)
  - UI shows delete button on row hover (appears in 4th column)
  - JavaScript confirmation dialog before delete
  - Page reloads after successful deletion
  - Preserves data integrity - files remain in R2, just hidden from UI
- **Database schema updates**:
  - `ALTER TABLE items ADD COLUMN file_hash TEXT;`
  - `ALTER TABLE items ADD COLUMN deleted_at TEXT;`
  - Applied to existing database without data loss

### What failed
- Nothing

### Resolution
- N/A

### Notes
- OCR now consistent: email attachments AND direct uploads get indexed
- Duplicate detection is content-based (SHA256), not filename-based
  - Uploading same file with different name is still detected as duplicate
  - Prevents accidental re-uploads
- Soft delete preserves "documents as source of truth" principle
  - Items marked as deleted but not removed from storage
  - Can be undeleted if needed (just clear deleted_at timestamp)
  - No data loss, just visibility control
- Delete requires confirmation to prevent accidental removal
- All existing items work with new schema (nullable columns)
- Upload flow now:
  1. Read file content
  2. Calculate SHA256 hash
  3. Check for duplicates → return existing if found
  4. Extract text (PDF or OCR for images)
  5. Upload to R2
  6. Store in database with hash
- Search now works across all document types: emails, PDFs, images
- Delete button only shows on hover to keep UI clean
