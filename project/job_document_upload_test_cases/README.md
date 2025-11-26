# Job Document Upload Test Cases

## ⚠️ **IMPORTANT DISCLAIMER**

**These documents contain fake and potentially misleading job descriptions created for testing purposes only.**

### **Test Case Categories**

#### **Legitimate Job Postings**
- These represent real, authentic job postings from reputable companies
- Used to test the system's ability to correctly identify genuine opportunities
- May contain actual company information and realistic job requirements

#### **Fake/Scam Job Postings**
- **Obvious scams** (files ending in `_obvious_scam`): Clear red flags like payment requests, urgent language, suspicious contact methods
- **Subtle fakes** (files ending in `_subtle_fake`): More sophisticated fake postings that appear legitimate at first glance
- These are designed to test the AI's ability to detect fraudulent job listings

### **Purpose**

These test cases are used to:
- Validate the document upload and text extraction functionality
- Test the AI-powered authenticity analysis system
- Ensure proper handling of various document formats (PDF, DOCX, TXT)
- Train and evaluate the job scam detection algorithms

### **File Naming Convention**

```
[JobTitle]_[category].[extension]

Examples:
- SeniorFinancialAnalyst_subtle_fake.pdf
- DataComplianceAssistant_obvious_scam.docx
- SoftwareEngineer_legitimate.txt
```

### **Security Notice**

⚠️ **Do not use these documents for any purpose outside of testing this job analysis system.**

- The fake job descriptions may contain:
  - Fabricated company information
  - Fictional contact details
  - Misleading salary information
  - Potentially harmful links or instructions

- **Never apply to jobs based on these test documents**
- **Never share personal information in response to these postings**
- **Never send money or payments to contacts found in these documents**

### **Usage in Testing**

These files are used exclusively for:
- Backend unit tests for document processing
- Integration tests for the upload API endpoint
- AI model validation and accuracy testing
- User interface testing for file upload functionality

### **Contact Information**

If you have questions about these test cases or the job analysis system, please contact the development team.

---

**Remember: Always verify job opportunities through official company websites and never share sensitive information with unverified sources.**

