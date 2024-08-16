from ai.openai_operations import create_chat_completion, skills_analysis
from config.settings import load_config
from database.database_operations import get_documents, update_field
from utils.helper_functions import line_fit, process_string

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

def verify_skills(job_skills):
    for job_id, skills in job_skills.items():
        skills = skills.split("^_^")
        verified_skills = []
        for skill in skills:
            skill = process_string(skill)
            user_input = input(f"Do you have the '{skill}' skills? (yes/no): ").strip().lower()
            while user_input != 'yes':
                replacement_skills = create_chat_completion("replacement_skill", skill, temperature=0.7)
                print(replacement_skills)
                skill = input("Input a replacement skill: ").strip()
                skill = process_string(skill)
                user_input = input(f"Do you have the '{skill}' skills? (yes/no): ").strip().lower()
            while not line_fit(skill, '<skill>lllllllllllllllllllllllllllllllllllllllll'):
                shorter_skills = create_chat_completion("shorter_skill", skill, temperature=0.7)
                print(shorter_skills)
                skill = input(f"'{skill}' skill is too long. Enter shorter skill: ")
                skill = process_string(skill)
                user_input = input(f"Do you have the '{skill}' skills? (yes/no): ").strip().lower()
            verified_skills.append(skill)

        verified_skills = '^_^'.join(verified_skills)
        update_field("job_postings", "job_id", job_id, "skills", verified_skills)

def collect_skills(job_skills):
    for job_id, skills in job_skills.items():
        skills = skills.split("^_^")
        criteria = {}
        fields = ["skill"]
        collection = get_documents('bullet_points', criteria, fields)
        skill_collection = [doc["skill"] for doc in collection if "skill" in doc]
        missing_skills = [skill for skill in job_skills if skill not in skill_collection]
        skill_collection = [skill for skill in skill_collection if skill not in missing_skills]
        prompt = f"Inputted list: {'^_^'.join(missing_skills)}" + "\n" + f"Skill collection: {'^_^'.join(skill_collection)}"
        replacement_skills = create_chat_completion("collect_skills", prompt, temperature=0.4)
        replacement_skills = replacement_skills.split("^_^")
        for i, skill in enumerate(missing_skills):
                index = job_skills.index(skill)
                job_skills[index] = replacement_skills[i]
        updated_job_skills = "^_^".join(job_skills)
        update_field("job_postings", "job_id", job_id, "skills", updated_job_skills)
