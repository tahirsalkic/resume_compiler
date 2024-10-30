import logging
from typing import List
from ai.openai_operations import create_chat_completion, skills_analysis
from config.settings import load_config
from database.database_operations import get_documents, insert_skill, update_field
from utils.helper_functions import get_user_confirmation, line_fit

logger = logging.getLogger(__name__)

config = load_config()
robo_tailor = eval(config["AUTOMATION"]["automate_skills"])
skill_length_limit = config["RESUME"]["skill_length_limit"]

def tailor_skills(job_ids: list):
    """Perform skills analysis on a list of job IDs."""
    logger.info("Starting skill tailoring for job ids: %s", job_ids)
    all_job_descriptions = {}
    valid_skills = {}

    try:
        while job_ids:
            criteria = {"job_id": {"$in": job_ids}}
            fields = ["job_id", "description"]
            job_listings = get_documents('job_postings', criteria, fields)
            logger.debug("Fetched job listings: %s", job_listings)

            job_descriptions = {doc["job_id"]: doc["description"] for doc in job_listings if "description" in doc}
            all_job_descriptions.update(job_descriptions)
            logger.debug("Extracted job descriptions: %s", job_descriptions)

            job_skills = skills_analysis(job_descriptions)

            invalid_skills_job_ids = [
                job_id for job_id, skills in job_skills.items()
                if len(skills.split('^_^')[:15]) != 15
            ]

            for job_id, skills in job_skills.items():
                if job_id not in invalid_skills_job_ids:
                    skills = skills.split('^_^')[:15]
                    valid_skills[job_id] = ('^_^').join(skills)

            if invalid_skills_job_ids:
                logger.warning("Some skills did not meet the criteria, re-running analysis for job ids: %s", invalid_skills_job_ids)
                job_ids = invalid_skills_job_ids
            else:       
                logger.info("Mapped job descriptions to skills: %s", valid_skills)
                if robo_tailor:
                    collect_skills(valid_skills)
                else:
                    verify_skills(valid_skills)
                break

    except Exception as e:
        logger.error("Error during skills analysis: %s", e)
        raise

def get_replacement_skill(skill):
    try:
        replacement_skills = create_chat_completion("replacement_skill", skill, temperature=0.8)
        print(f"Generated replacement skills: {replacement_skills}")
        
        user_input = input("Input a replacement skill: ").strip()
        return user_input
    except Exception as e:
        logger.error("Error generating replacement skill: %s", e)
        raise

def ensure_skill_fits_length(skill):
    while not line_fit(skill, skill_length_limit):
        logger.warning("Skill '%s' exceeds length limit.", skill)
        
        shorter_skills = create_chat_completion("shorter_skill", skill, temperature=0.7)
        print(f"Generated shorter skills: {shorter_skills}")
        
        skill = input(f"'{skill}' skill is too long. Enter shorter skill: ").strip()
    return skill

def verify_single_skill(skill):
    replacement_flag = False
    try:
        while not get_user_confirmation(f"Do you have '{skill}' skills?"):
            skill = get_replacement_skill(skill)
            replacement_flag = True
        skill = ensure_skill_fits_length(skill)
        insert_skill(skill)
        logger.info("Verified and inserted skill: %s", skill)
    except Exception as e:
        logger.error("Error verifying single skill '%s': %s", skill, e)
        raise

    return skill, replacement_flag

def verify_skills(job_skills):
    for job_id, skills in job_skills.items():
        logger.info("Verifying skills for job id: %s", job_id)
        
        skills_list = skills.split("^_^")
        verified_skills = []
        replacement_skills = []

        for skill in skills_list:
            verified_skill, replacement_flag = verify_single_skill(skill)
            if replacement_flag:
                replacement_skills.append(verified_skill)
            else:
                verified_skills.append(verified_skill)
            chosen_skills = verified_skills + replacement_skills
            print(f"Verified skills so far: {chosen_skills}")

        chosen_skills_str = '^_^'.join(chosen_skills)
        update_field("job_postings", "job_id", job_id, "skills", chosen_skills_str)
        logger.info("Updated job id %s with skills: %s", job_id, chosen_skills_str)

def are_skills_valid(replacement_skills_list):
    unique_skills = list({skill for skill in replacement_skills_list})
    return len(unique_skills) == 15

def collect_skills(job_skills):
    fields = ["skill"]
    try:
        for job_id, skills_str in job_skills.items():
            skill_collection = {
                doc["skill"].lower()
                for doc in get_documents('bullet_points', {}, fields)
                if "skill" in doc
            }
            logger.debug("Collected existing skills: %s", skill_collection)

            verified_skills = []

            skills = skills_str.split("^_^")
            for skill in skills:
                skill = skill.lower()
                if skill in skill_collection:
                    verified_skills.append(skill)
                    skill_collection.remove(skill)
                else:
                    replacement_skill = skill
                    while replacement_skill not in skill_collection:
                        logger.info("Found missing skills for job id %s: %s", job_id, skill)
                        prompt = (
                            f"Inputted skill: {skill}\n\n"
                            f"Skill collection: {'^_^'.join(skill_collection)}"
                        )
                        replacement_skill = create_chat_completion("collect_skills", prompt, temperature=0.7)
                    verified_skills.append(replacement_skill)
                    skill_collection.remove(replacement_skill)

            while len(verified_skills) < 15:
                for skill in verified_skills:
                    logger.info("Not enough skills for job id %s", job_id)
                    prompt = (
                        f"Inputted skill: {skill}\n\n"
                        f"Skill collection: {'^_^'.join(skill_collection)}"
                    )
                    replacement_skill = create_chat_completion("collect_skills", prompt, temperature=0.7)
                    while replacement_skill not in skill_collection:
                        logger.info("Adding additional skill for job id %s", job_id)
                        prompt = (
                            f"Inputted skill: {skill}\n\n"
                            f"Skill collection: {'^_^'.join(skill_collection)}"
                        )
                        replacement_skill = create_chat_completion("collect_skills", prompt, temperature=0.7)
                    verified_skills.append(replacement_skill)
                    skill_collection.remove(replacement_skill)
                    if len(verified_skills) < 15:
                        break

            logger.info("Verified skills for job id %s: %s", job_id, verified_skills)

            updated_job_skills = "^_^".join(verified_skills)
            capitalized_skills = create_chat_completion("capitalize_skills", updated_job_skills, temperature=0.4)
            capitalized_skills_list = capitalized_skills.split("^_^")[:15]
            while len(capitalized_skills_list) != 15:
                logger.warning("AI failed to capitalize skills")
                capitalized_skills = create_chat_completion("capitalize_skills", updated_job_skills, temperature=0.4)
                capitalized_skills_list = capitalized_skills.split("^_^")[:15]
                capitalized_skills = "^_^".join(capitalized_skills_list)

            update_field("job_postings", "job_id", job_id, "skills", capitalized_skills)
            logger.info("Updated job id %s with new skills collection: %s", job_id, capitalized_skills)

    except Exception as e:
        logger.error("Error collecting skills: %s", e)
        raise
