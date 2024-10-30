from datetime import datetime
import logging
from docx import Document
from os.path import exists

from config.settings import load_config
from database.database_operations import get_aggregated_data, update_field, update_many_fields
from resume.resume_helper_functions import (
    build_output_path, extract_job_details, fetch_new_jobs, 
    format_aggregated_data, generate_job_url, generate_output_filename,
    prepare_skills_list, save_pdf, save_resume, tailor_achievement, tailor_city, tailor_role, tailor_skill
)
from ai.openai_operations import pick_a_hat
from utils.helper_functions import config_exists, get_current_date

logger = logging.getLogger(__name__)

config = load_config()

def display_dict(d):
    logger.debug("Displaying dictionary.")
    for verb, skills in d.items():
        print(f"Verb: {verb}")
        for skill, bullet in skills.items():
            print(f"  Skill: {skill}")
            print(f"    {bullet[0]}")

def select_bullets(aggregated_data):
    logger.debug("Selecting bullets from aggregated data.")
    selected_bullets = []
    selected_verb_skill = {}
    display_dict(aggregated_data)

    while len(selected_bullets) < 5 and any(len(skills) > 0 for skills in aggregated_data.values()):
        try:
            verb = input("Enter verb: ")
            if verb not in aggregated_data:
                print("Invalid verb. Please try again.")
                continue

            skill = input("Enter skill: ")
            if skill not in aggregated_data[verb]:
                print("Invalid skill. Please try again.")
                continue

            bullet = aggregated_data[verb][skill]
            selected_bullets.append(bullet[0])
            selected_verb_skill.setdefault(verb, []).append(skill)
            for v in aggregated_data:
                aggregated_data[v].pop(skill, None)
            logger.debug(f"Selected bullets: {selected_bullets}, Total selected bullets: {len(selected_bullets)}")
            display_dict(aggregated_data)
            logger.debug(f"Selected verb-skill pairs: {selected_verb_skill}")

        except (ValueError, KeyError) as e:
            logger.error(f"Error: {e}. Please try again.")

    while len(selected_bullets) < 5:
        logger.debug(f"Selected bullets so far: {selected_bullets}")
        extra_point = input("Enter extra point: ")
        selected_bullets.append(extra_point)
    
    return selected_bullets

def aggregate_skill_bullets(skills):
    top_skills = skills[:5]
    logger.debug(f"Aggregating skill bullets for skills: {top_skills}")
    pipeline = [
        {'$match': {'skill': {'$in': top_skills}}},
        {'$unwind': '$bullets'},
        {'$group': {
            '_id': {
                'skill': '$skill',
                'verb': '$bullets.verb'
            },
            'bullets': {'$push': '$bullets.bullet'}
        }},
        {'$sort': {'_id.skill': 1, '_id.verb': 1}}
    ]
    agg = get_aggregated_data("bullet_points", pipeline)
    aggregated_data = format_aggregated_data(agg)
    logger.debug(f"Aggregated data: {aggregated_data}")
    return aggregated_data

def update_resume(template, role, city, full_url, fixed_skills_list, selected_bullets):
    logger.debug(f"Updating resume for role: {role}, URL: {full_url}, Skills: {fixed_skills_list}.")
    skill_count = 0
    for p in template.paragraphs:
        if '<Role>' in p.text:
            tailor_role(p, role, full_url)
        elif '<skill>' in p.text:
            skill_count = tailor_skill(p, fixed_skills_list, skill_count)
        elif '<City>' in p.text:
            tailor_city(p, city)
    
    tailor_achievement(template, selected_bullets)
    logger.debug("Resume updated with selected bullets and skills.")

def tailor_resume():
    logger.info("Fetching new jobs to tailor resumes.")
    new_jobs = fetch_new_jobs()
    
    for new_job in new_jobs:
        job_id, company, role, city, skills = extract_job_details(new_job)
        
        full_url = generate_job_url(job_id)
        current_date = get_current_date()
        
        output_filename = generate_output_filename(role, company, current_date)
        output_path = build_output_path(output_filename)
        
        if exists(output_path):
            logger.warning(f"Resume '{output_filename}' already exists.")
            continue
        
        while True:
            profile = pick_a_hat(role)
            if config_exists(config, "RESUME", f"{profile}_template"):
                break
            logger.warning(f"Could not find profile: '{profile}' in config.")

        template_path = config["RESUME"][f"{profile}_template"]
        template = Document(template_path)
        logger.debug(f"Using template path: {template_path}")
        
        skills_list = prepare_skills_list(skills)
        search_skills = [skill.lower() for skill in skills_list]
        aggregated_data = aggregate_skill_bullets(search_skills)
        summary_of_achievements = select_bullets(aggregated_data)
        
        update_resume(template, role, city, full_url, skills_list, summary_of_achievements)
        save_resume(template, output_path)
        save_pdf(output_path, role, company, current_date)
        update_many_fields("bullet_points", "bullets.bullet", {"$in": summary_of_achievements}, "bullets.$[elem].resume_reference", datetime.now(), [{ "elem.bullet": {"$in": summary_of_achievements} }])
        update_field("job_postings", "job_id", job_id, "tailored", True)
        logger.info(f"Tailored resume created and saved as '{output_path}' and PDF version.")
