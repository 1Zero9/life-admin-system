# Family User Guide - Life Admin System

## What is This?

A simple system for storing and finding family documents. Think of it as a digital filing cabinet that automatically captures important emails and lets you upload documents.

**Access**: Open your web browser and go to: `http://YOUR_HOME_SERVER:8000`
(Bookmark this for easy access!)

## Main Screen - The Vault

When you open the system, you'll see a list of all your documents.

### Finding Documents

**Search box** (top right):
- Type anything: "insurance", "doctor", "receipt"
- Searches both filenames and document text
- Works as you type (no need to press Enter)

**Filters** (left sidebar):
- **All** - Everything
- **Emails** - Just emails from Gmail
- **Uploads** - Documents you uploaded
- **Attachments** - Files attached to emails

### Understanding the List

Each document shows:
- **Name** - What the document is called
- **Date** - When it was captured
- **Source** - Where it came from (Email/Upload/Attachment)
- **Icon** - Type of file (PDF, email, image, etc.)

**► button** (if shown): Click to see AI summary without opening the document

## AI Summaries (Optional)

The system can read documents and extract useful information:
- **Type** - Receipt, invoice, letter, etc.
- **Vendor** - Who sent it (company/organization)
- **Date** - Date mentioned in the document
- **Amount** - Money amount (if any)
- **Description** - One sentence about what it is

### How to Use AI Summaries

1. Click **►** on any document row
2. You'll see either:
   - **AI Summary** - If already generated
   - **Generate Summary** button - Click to create one

**Note**: Generating summaries costs a tiny amount (less than a penny per document). Only generate for important documents.

## Viewing a Document

Click on any document name to see its full details:
- Original filename
- Date captured
- File size
- Where it came from
- AI summary (if generated)
- Extracted text (if it's a PDF or image)

**Buttons**:
- **Download** - Save a copy to your computer
- **Generate Summary** - Create AI summary (if not already done)
- **Regenerate** - Create a new AI summary
- **Delete** - Hide the document (doesn't actually remove it)

## Adding Documents

### Method 1: Gmail (Automatic)

1. In Gmail, apply the label **LifeAdmin** to any email
2. Within 15 minutes, it appears in the vault automatically
3. Email attachments are included

**How to add the label**:
- Open the email
- Click the label icon (looks like a tag)
- Select "LifeAdmin"
- Done!

### Method 2: Upload (Manual)

1. Click **Upload** button (left sidebar)
2. Choose file from your computer
3. Click **Upload File**
4. File appears in vault immediately

**Supported files**:
- PDFs
- Images (JPG, PNG)
- Word documents
- Excel sheets
- Audio/video files
- Archives (ZIP, RAR)

## Finding Documents Later

### By Keyword
Search for anything mentioned in the document:
- Company names: "Electric Ireland", "Bupa"
- Document types: "invoice", "receipt", "statement"
- Text inside: "€50", "December", your address

### By Source
Use filters in sidebar:
- All Gmail documents: Click "Emails"
- All uploaded files: Click "Uploads"
- All attachments: Click "Attachments"

### By AI Summary
If you've generated AI summaries:
1. Click **►** to expand the summary
2. See Type, Vendor, Date, Amount at a glance
3. Click "View Details" to see full document

## Tips for Families

**Label everything in Gmail**:
- Bills (electricity, gas, internet)
- Insurance documents
- Medical receipts and records
- School communications
- Bank statements
- Important receipts

**Upload important documents**:
- Scan paper receipts (use phone camera)
- Download PDFs from websites
- Save confirmation emails as PDFs

**Use AI summaries for**:
- Receipts (to extract amounts)
- Bills (to see vendor and date)
- Medical documents (to organize by provider)
- Insurance letters (to identify type and dates)

**Don't worry about**:
- Organizing into folders (not needed - use search)
- Renaming files (system makes readable titles)
- Duplicate files (system detects and prevents them)
- Deleting by mistake (delete just hides, doesn't remove)

## Common Questions

**Q: How do I organize documents?**
A: You don't! Just capture everything. Use search and filters to find what you need.

**Q: What if I upload the same file twice?**
A: The system detects duplicates and won't store it twice.

**Q: Can I delete documents?**
A: Yes, but "delete" just hides them. The original stays in storage (good for accidents).

**Q: How much does AI cost?**
A: About €0.003 per document (less than a penny). A €5 credit lasts for 1000+ summaries.

**Q: Is my data secure?**
A: Documents are stored in your private cloud storage (R2). Only accessible from your home network.

**Q: What if the system is down?**
A: All documents are safely in cloud storage. Nothing is lost. Just restart the system.

**Q: Can I access from my phone?**
A: Yes! Connect to your home WiFi and use the same web address in your phone browser.

**Q: How do I find all medical receipts?**
A: Search for "receipt" or "clinic" or "doctor". Or generate AI summaries and filter by Type: "Receipt".

**Q: What happens to emails I don't label?**
A: They stay in Gmail. Only emails with "LifeAdmin" label are captured.

## Troubleshooting

**Document not appearing after labeling in Gmail:**
- Wait 15 minutes (Gmail sync runs every 15 minutes)
- Check the label is exactly "LifeAdmin"
- Check logs (ask admin)

**Can't upload file:**
- Check file size (very large files may fail)
- Check file type is supported
- Try again in a few minutes

**AI summary shows wrong information:**
- Click "Regenerate" to try again
- AI isn't perfect - always check the original document

**Search not finding document:**
- Try different keywords
- Check if document has text (images without OCR won't be searchable)
- Try browsing by source type instead

## Need Help?

Ask the person who set up the system. They can:
- Check logs (tells what went wrong)
- Restart services (if system is slow)
- Add more storage (if running out of space)
- Update the system (new features)

---

**Remember**: This system is designed to be boring and reliable. Just label emails and upload documents. The system handles the rest. Don't overthink it!
