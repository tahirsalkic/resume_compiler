import sys

from config.logging_config import setup_logging
from firefox.profile_operations import get_bookmarks
from database.backup_operations import check_and_import, clean_backups, export_backups
from database.database_operations import (
    collect_new_job_postings,
    find_documents_missing_field,
    propagate_skills_field_across_docs,
)
from resume.achievements_builder import build_achievements
from resume.tailor_resume import tailor_resume
from resume.tailor_skills import tailor_skills
from scraper.scrapy_helper_functions import run_job_scraper

def main():

    logger = setup_logging()

    check_and_import()

    bookmark_urls = get_bookmarks()
    if not bookmark_urls:
        logger.info("No bookmarks found in Firefox profile. Aborting compiler.")
        sys.exit(0)

    collect_new_job_postings(bookmark_urls)

    postings_to_scrape = find_documents_missing_field('job_postings', 'job_id', 'description')
    run_job_scraper(postings_to_scrape)

    propagate_skills_field_across_docs()

    postings_missing_skills = find_documents_missing_field('job_postings', 'job_id', 'skills')
    tailor_skills(postings_missing_skills)

    skills_missing_achievements = find_documents_missing_field('bullet_points', 'skill', 'bullets')
    build_achievements(skills_missing_achievements)

    tailor_resume()

    export_backups()
    clean_backups()

    logger.info("Done")

if __name__ == "__main__":
    main()
