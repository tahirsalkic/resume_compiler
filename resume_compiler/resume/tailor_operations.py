from ai.openai_operations import create_chat_completion, skills_analysis
from config.settings import load_config
from database.database_operations import get_documents, insert_skill, update_field
from utils.helper_functions import line_fit

config = load_config()
robo_tailor = eval(config["DEFAULT"]["ROBO_TAILOR"])

def tailor_skills(job_ids: list) -> dict:
    """Perform skills analysis on a list of job IDs and return a dictionary of job_id to analyzed description."""
    criteria = {"job_id": {"$in": job_ids}}
    fields = ["job_id", "description"]
    
    try:
        job_listings = get_documents('job_postings', criteria, fields)
        job_descriptions = {doc["job_id"]: doc["description"] for doc in job_listings if "description" in doc}
        skills = skills_analysis(job_descriptions)
        job_skills = dict(zip(job_descriptions.keys(), skills))

        if robo_tailor:
            collect_skills(job_skills)
        else:
            verify_skills(job_skills)

    except Exception as e:
        print("Error during skills analysis:", e)
        raise

def get_user_confirmation(skill):
    user_input = input(f"Do you have the '{skill}' skills? (yes/no): ").strip().lower()
    while user_input not in ['yes', 'no']:
        user_input = input("Please answer with 'yes' or 'no': ").strip().lower()
    return user_input == 'yes'

def get_replacement_skill(skill):
    replacement_skills = create_chat_completion("replacement_skill", skill, temperature=0.7)
    print(replacement_skills)
    return input("Input a replacement skill: ").strip()

def ensure_skill_fits_length(skill):
    while not line_fit(skill, '<skill>lllllllllllllllllllllllllllllllllllllllll'):
        shorter_skills = create_chat_completion("shorter_skill", skill, temperature=0.7)
        print(shorter_skills)
        skill = input(f"'{skill}' skill is too long. Enter shorter skill: ").strip()
    return skill

def verify_single_skill(skill):
    while not get_user_confirmation(skill):
        skill = get_replacement_skill(skill)
    skill = ensure_skill_fits_length(skill)
    insert_skill(skill)
    return skill

def verify_skills(job_skills):
    for job_id, skills in job_skills.items():
        skills_list = skills.split("^_^")
        verified_skills = [verify_single_skill(skill) for skill in skills_list]
        verified_skills_str = '^_^'.join(verified_skills)
        update_field("job_postings", "job_id", job_id, "skills", verified_skills_str)

def collect_skills(job_skills):
    fields = ["skill"]
    skill_collection = {
        doc["skill"]
        for doc in get_documents('bullet_points', {}, fields)
        if "skill" in doc
    }

    for job_id, skills_str in job_skills.items():
        skills = skills_str.split("^_^")
        missing_skills = [skill for skill in skills if skill not in skill_collection]

        if missing_skills:
            prompt = (
                f"Inputted list: {'^_^'.join(missing_skills)}\n"
                f"Skill collection: {'^_^'.join(skill_collection)}"
            )
            replacement_skills = create_chat_completion("collect_skills", prompt, temperature=0.4)
            replacement_skills_list = replacement_skills.split("^_^")

            for i, skill in enumerate(missing_skills):
                index = skills.index(skill)
                skills[index] = replacement_skills_list[i]
            
            updated_job_skills = "^_^".join(skills)
            update_field("job_postings", "job_id", job_id, "skills", updated_job_skills)
