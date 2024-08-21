import logging
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.opc.constants import RELATIONSHIP_TYPE
from subprocess import Popen, PIPE
from os.path import join
from collections import defaultdict

from config.settings import load_config
from database.database_operations import get_documents
from utils.helper_functions import get_user_confirmation, line_fit, sanitize_filename

logger = logging.getLogger(__name__)

config = load_config()
role_length_limit = config["RESUME"]["role_length_limit"]
skill_length_limit = config["RESUME"]["skill_length_limit"]

def prepare_skills_list(skills):
    logger.debug(f"Preparing skills list from: {skills}")
    skills_list = skills.split('^_^')
    return (skills_list * ((15 // len(skills_list)) + 1))[:15] if len(skills_list) < 15 else skills_list[:15]

def generate_output_filename(role, company, current_date):
    logger.debug(f"Generating output filename for role: {role}, company: {company}, date: {current_date}.")
    safe_role = sanitize_filename(role)
    safe_company = sanitize_filename(company)
    safe_current_date = sanitize_filename(current_date)
    return f'Tahir Salkic Resume - {safe_role} - {safe_company} - {safe_current_date}.docx'

def clear_paragraph_runs(paragraph):
    logger.debug("Clearing paragraph runs.")
    for run in list(paragraph.runs):
        run.clear()

def replace_text_in_paragraph(paragraph, search_text, replace_text):
    logger.debug(f"Replacing text '{search_text}' with '{replace_text}' in paragraph.")
    for run in paragraph.runs:
        run.text = run.text.replace(search_text, replace_text)

def add_column_break(paragraph):
    logger.debug("Adding column break to paragraph.")
    brk = OxmlElement('w:br')
    brk.set(qn('w:type'), 'column')
    paragraph._p.insert(0, brk)

def add_hyperlink(paragraph, text, url):
    logger.debug(f"Adding hyperlink with text '{text}' and URL '{url}' to paragraph.")
    part = paragraph.part
    r_id = part.relate_to(url, RELATIONSHIP_TYPE.HYPERLINK, is_external=True)

    hyperlink = OxmlElement('w:hyperlink')
    hyperlink.set(qn('r:id'), r_id)

    new_run = paragraph.add_run(text)
    r_element = new_run._r
    rPr_element = OxmlElement('w:rPr')

    c_element = OxmlElement('w:color')
    c_element.set(qn('w:val'), '000000')
    u_element = OxmlElement('w:u')
    u_element.set(qn('w:val'), 'none')  # No underline

    rPr_element.append(c_element)
    rPr_element.append(u_element)
    r_element.insert(0, rPr_element)

    hyperlink.append(r_element)
    paragraph._p.append(hyperlink)

def tailor_skill(paragraph, fixed_skills_list, skill_count):
    skill = fixed_skills_list[skill_count]
    logger.debug(f"Handling skill paragraph for skill '{skill}'.")
    while not line_fit(skill, skill_length_limit):
        skill = input(f"'{skill}' skill is too long. Enter shorter skill: ")

    replace_text_in_paragraph(paragraph, '<skill>', skill.strip())

    if skill_count in {5, 10}:
        add_column_break(paragraph)

    return skill_count + 1

def tailor_role(paragraph, role, full_url):
    logger.debug(f"Handling role paragraph for role '{role}' and URL '{full_url}'.")
    clear_paragraph_runs(paragraph)

    while True:
        if not get_user_confirmation(f"Is this role name okay? '{role}'?"):
            while True:
                role = input("Enter new role: ")
                if not line_fit(role, role_length_limit, 'georgia', 14):
                    role = input(f"'{role}' role is too long. Enter shorter role: ")
                break
        elif not line_fit(role, role_length_limit, 'georgia', 14):
            role = input(f"'{role}' role is too long. Enter shorter role: ")
            continue
        else:
            break

    add_hyperlink(paragraph, role, full_url)
    return role

def tailor_achievement(template, selected_bullets):
    logger.debug("Handling achievement paragraphs.")
    bullet_index = 0
    for i in range(26, 32):
        current_paragraph = template.paragraphs[i]
        if "<achievement>" in current_paragraph.text:
            replace_text_in_paragraph(current_paragraph, '<achievement>', selected_bullets[bullet_index].strip())
            bullet_index += 1

def save_resume(template, path):
    logger.debug(f"Saving resume to path '{path}'.")
    template.save(path)

def docx_to_pdf(docx_path, output_dir):
    logger.debug(f"Converting DOCX file '{docx_path}' to PDF in directory '{output_dir}'.")
    p = Popen([
        'libreoffice', '--headless', '--convert-to', 'pdf', '--outdir',
        output_dir, docx_path
    ], stdout=PIPE, stderr=PIPE)
    p.communicate()

def save_pdf(doc_path, role, company, date):
    pdf_path = join(
        '/job_search',
        f'{sanitize_filename(role)} - {sanitize_filename(company)} - {sanitize_filename(date)}'
    )
    logger.debug(f"Saving PDF version to '{pdf_path}'.")
    docx_to_pdf(doc_path, pdf_path)

def fetch_new_jobs():
    logger.info("Fetching new jobs from the database.")
    criteria = {'$and': [{'tailored': False}, {'general': False}]}
    fields = ['job_id', 'company', 'role', 'skills']
    return get_documents('job_postings', criteria, fields)

def extract_job_details(new_job):
    logger.debug(f"Extracting job details from job: {new_job}")
    return new_job['job_id'], new_job['company'], new_job['role'], new_job['skills']

def generate_job_url(job_id):
    logger.debug(f"Generating job URL for job ID: {job_id}")
    return f"https://www.linkedin.com/jobs/view/{job_id}"

def build_output_path(filename):
    logger.debug(f"Building output path for filename: {filename}")
    return join('/job_search', filename)

def format_aggregated_data(agg):
    logger.debug(f"Formatting aggregated data: {agg}")
    result = defaultdict(lambda: defaultdict(list))
    for entry in agg:
        skill = entry['_id']['skill']
        verb = entry['_id']['verb']
        result[verb][skill] = entry['bullets']
    return result
