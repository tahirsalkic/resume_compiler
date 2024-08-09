# resume_compiler
This project compiles your skills and career achievements, making it easier to tailor your resume for specific job postings and improving your chances in a competitive job market.

## Functional Requirements

1. **Manage Firefox Bookmarks**
    - Read existing bookmarks
    - Edit and update bookmarks

2. **Scrape Job Postings**
    - Extract job postings from LinkedIn
    - Build scalable workers for scraping

3. **Skill Extraction Using AI**
    - Extract top 15 skills relevant to job postings using AI
    - Confirmation Modes:
        - **Manual Mode:** User manually confirms the extracted skills
        - **Automatic Mode:** Selects the top 15 skills from the existing skills in db

4. **Achievement Bullet Points Generation**
    - Use AI to generate achievement bullet points for new skills
    - Allow users to rewrite and confirm new achievement bullet points

5. **Resume Customization**
    - Allow users to select achievements for inclusion in the resume
    - Read and edit a predefined resume template

6. **Resume Export**
    - Generate tailored resumes in PDF and DOCX formats

## Non-Functional Requirements

1. **User Interaction**
    - Provide a guided CLI process for user interaction or an automated workflow to generate tailored resumes