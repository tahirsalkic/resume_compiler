from ai.openai_operations import create_chat_completion
from config.settings import load_config
from database.database_operations import update_skill_bullets
from utils.helper_functions import get_user_confirmation, line_fit

VERBS = ["built", "led", "managed", "collaborated", "improved"]

config = load_config()
achievement_length_limit = config["RESUME"]["achievement_length_limit"]

def build_achievements(skills: list):
    """Generate and store achievement bullet points for a list of skills."""
    for skill in skills:
        achievements = generate_achievements(skill)
        verified_achievements = verify_achievements(skill, achievements)
        update_skill_bullets(skill, verified_achievements)

def generate_achievements(skill):
    response = create_chat_completion("build_achievements", skill, temperature=0.8)
    return response.split("^_^")

def verify_achievements(skill, achievements):
    verified_achievements = {}
    for verb, achievement in zip(VERBS, achievements):
        if confirm_achievement(verb, skill, achievement):
            while True:
                if get_user_confirmation(f"Do you want to keep the following achievement? {achievement}"):
                    achievement = ensure_line_fit(achievement)
                    verified_achievements[verb] = achievement
                    break
                else:
                    more_relevant_achievement = create_chat_completion("new_resume_bullet_point", f"**Skill**: {skill}\n**Verb**: {verb}", temperature=0.8)
                    print(f"More relevant example achievement: {more_relevant_achievement}")
                    achievement = input("Enter an achievement: ").strip()
                
    return verified_achievements


def confirm_achievement(verb, skill, achievement):
    print(f"Example achievement: {achievement}")
    return get_user_confirmation(
        f"Use the verb '{verb}' and skill '{skill}' for an achievement point?"
    )

def ensure_line_fit(achievement):
    while not line_fit(achievement, achievement_length_limit):
        print("Achievement is too long.")
        shorter_achievement = create_chat_completion("shorter_achievement", achievement, temperature=0.8)
        print(f"Example of shorter achievement:\n{shorter_achievement}")
        achievement = input("Enter shorter achievement: ").strip()
    return achievement